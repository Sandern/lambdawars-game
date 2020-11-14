from steam import steamapicontext, SteamMatchmakingServerListResponse, SteamMatchmakingRulesResponse, SteamAPI_RunCallbacks
from gameinterface import engine, ConVar, ConVarRef, Plat_FloatTime
import matchmaking

from core.signals import lobby_gameserver_accept, lobby_gameserver_denied

mm_nolocal_hosting = ConVar('mm_nolocal_hosting', '0', 0,
                            'Prevents from falling back to local server hosting. '
                            'May fail to start the game if no server is available.')
mm_debug_findserver = ConVar('mm_debug_findserver', '0', 0,
                             'Provides debug information when finding a server.')
mm_debug_no_request_server = ConVar('mm_debug_no_request_server', '0', 0,
                                    'Test server finding, but do not actually request and join a server')
mm_force_findserver = ConVar('mm_force_findserver', '0', 0, 'Forces to find a server.')
mm_dedicated_server_max_ping = ConVar('mm_dedicated_server_max_ping', '110', 0,
                                      'Discards dedicated servers with ping higher than specified.')

mm_password = ConVarRef('mm_password')

class LobbyMatchmaking(SteamMatchmakingServerListResponse, SteamMatchmakingRulesResponse):
    """ Responsible for finding a server. """
    issearching = False
    steamidlobby = None
    activelistrequest = None
    activeserverrequestdetails = None
    #: Indicates a server is being requested, which will respond through the lobby_gameserver_accept or
    #: lobby_gameserver_denied signals.
    requestingserver_start_time = None
    resultlist = None
    gamedata = None
    
    gametags = None
    gamedir = None

    gametagsfilter = ''

    def __init__(self, lobby, gamedir):
        # Boost python bug: does not chain correctly
        SteamMatchmakingServerListResponse.__init__(self)
        SteamMatchmakingRulesResponse.__init__(self)
    
        self.lobby = lobby
        self.gamedir = gamedir
        
        lobby_gameserver_accept.connect(self.OnGameServerAccepts)
        lobby_gameserver_denied.connect(self.OnGameServerDenies)
        
    def OnDestroy(self):
        lobby_gameserver_accept.disconnect(self.OnGameServerAccepts)
        lobby_gameserver_denied.disconnect(self.OnGameServerDenies)

    def Update(self):
        """  Updates matchmaking when searching for server. """
        if not self.issearching or self.lobby.isofflinelobby:
            return

        if self.requestingserver_start_time and Plat_FloatTime() - self.requestingserver_start_time > 30.0:
            print('Server request timed out. Skipping...')
            self.TryNextGameServerResult()

    def ShouldLocalHost(self, gamedata):
        # Offline games are always local.
        network = gamedata.GetString('system/network', 'live').lower()
        if network == 'offline':
            return True
            
        # Force finding a server, for debugging
        if mm_force_findserver.GetBool() or mm_nolocal_hosting.GetBool():
            return False

        # Never when mm_password is set, we want our server.
        if mm_password.GetString():
            return False
            
        # No need to find a server if only one player is in the lobby
        if self.lobby.IsOnlyPlayer():
            return True
            
        # Sandbox can right now easily crash the server (e.g. spawning too much), so
        # always force local since it's a playbox anyway, unless we have code/password
        # for a reserved dedicated server.
        gamemode = gamedata.GetString('game/mode', '').lower()
        if gamemode == 'sandbox':
            return True
        
        return False
        
    def StartSearch(self, steamidlobby, gamedata):
        # Make sure no other search is active
        self.StopSearch() 

        print('Searching available server')
        
        self.issearching = True
        self.steamidlobby = steamidlobby
        self.gamedata = gamedata

        # Enrich with password if set. Game server will validate this upon requesting the server.
        if mm_password.GetString():
            gamedata.SetString('server/password', mm_password.GetString())

        self.lobby.datamodel.reservationticket = ''
        self.lobby.datamodel.lobbystate = 'searchingserver'
        
        if self.ShouldLocalHost(gamedata):
            # Maybe single player, or only player or sandbox
            self.RequestLocalGameServer()
        else:
            matchmakingservers = steamapicontext.SteamMatchmakingServers()
            if not matchmakingservers:
                return

            gamedataand_value = 'g:lw'
            if mm_password.GetString():
                gamedataand_value += ',password:%s' % mm_password.GetString()

            self.gametagsfilter = 'Available'

            # Start a new list call
            # TO CHECK: not sure if gamedata can be publicly queried, in which can the password/code could be
            # intercepted. If that's the case, it would need to filtered in a different way.
            filters = [
                ('gamedir', self.gamedir),
                ('gamedataand', gamedataand_value),
                ('gametagsand', self.gametagsfilter),
                ('secure', '1'),
            ]

            n = len(filters)
            filters = [('and', str(n))] + filters

            if mm_debug_findserver.GetBool():
                print('\tSearch filters: %s' % str(filters))
            
            self.resultlist = []
            self.activelistrequest = matchmakingservers.RequestInternetServerList(
                steamapicontext.SteamUtils().GetAppID(), filters, self)
        
    def StopSearch(self):
        # Stop any list call
        matchmakingservers = steamapicontext.SteamMatchmakingServers()
        if matchmakingservers and self.activelistrequest:
            matchmakingservers.ReleaseRequest(self.activelistrequest)
            self.activelistrequest = None
            
        self.steamidlobby = None
        self.resultlist = []
        self.issearching = False
        self.requestingserver_start_time = None
        
        if self.lobby.datamodel.lobbystate == 'searchingserver':
            self.lobby.datamodel.lobbystate = 'lobbying'
        
    def ServerResponded(self, request, server):
        if request != self.activelistrequest:
            return
            
        matchmakingservers = steamapicontext.SteamMatchmakingServers()
        
        details = matchmakingservers.GetServerDetails(request, server)

        if mm_debug_findserver.GetBool():
            print('ServerResponded: IP: %s, Steam ID: %s, Ping: %d' % (details.netadr.GetConnectionAddressString(),
                                                                       details.steamid, details.ping))

        if details.ping > mm_dedicated_server_max_ping.GetInt():
            if mm_debug_findserver.GetBool():
                print('ServerResponded: Skipping server due ping being higher than %d' %
                      mm_dedicated_server_max_ping.GetInt())
            return
        
        # Manually check some filters (TODO: move to filters passed to RequestInternetServerList if possible)
        # Game directory should match
        moddir = self.gamedir
        servermoddir = details.gamedir
        if moddir != servermoddir:
            if mm_debug_findserver.GetBool():
                print('Ignoring server (mod directory does not match %s != %s' % (moddir, servermoddir))
            return
            
        # Server version should match
        clientversion = int(engine.GetProductVersionString().replace('.', ''))
        serverversion = details.serverversion
        if serverversion != clientversion:
            if mm_debug_findserver.GetBool():
                print('Server version of responded server does not match client version (%s != %s)' % (serverversion,
                                                                                                       clientversion))
            return

        # Tags should match
        gametags = details.gametags
        hasgametags = set(self.gametagsfilter.split(',')) <= set(gametags.split(','))
        if not hasgametags:
            if mm_debug_findserver.GetBool():
                print('Gametags of responded server does not match (%s > %s). Ignoring...' % (self.gametagsfilter, gametags))
            return
        
        self.resultlist.append(details)
        
        if not self.activeserverrequestdetails:
            self.RequestGameServer(details)
        
    def RequestGameServer(self, details):
        if mm_debug_no_request_server.GetBool():
            print('Debug Find Server: Wanted to request server with ip %s' %
                  details.netadr.GetConnectionAddressString())
            return
        self.requestingserver_start_time = Plat_FloatTime()
        matchmaking.WarsRequestGameServer(details.steamid, self.steamidlobby, self.gamedata)
        self.activeserverrequestdetails = details
        
    def RequestLocalGameServer(self):
        if mm_debug_no_request_server.GetBool():
            print('Debug Find Server: Wanted to request local server')
            return
        self.lobby.datamodel.lobbystate = 'startinglocalserver'
        self.requestingserver_start_time = Plat_FloatTime()
        steamuser = steamapicontext.SteamUser()
        matchmaking.WarsRequestGameServer(steamuser.GetSteamID(), self.steamidlobby, self.gamedata)
            
    def ServerFailedToRespond(self, request, server):
        if request != self.activelistrequest:
            return
        # Just ignore, won't be added to list
        #print('ServerFailedToRespond: %s %s' % (request, server))
        
    def RefreshComplete(self, request, response):
        if request != self.activelistrequest:
            return

        matchmakingservers = steamapicontext.SteamMatchmakingServers()
        if mm_debug_findserver.GetBool():
            print('RefreshComplete: %s %s' % (request, response))
        matchmakingservers.ReleaseRequest(self.activelistrequest)
        self.activelistrequest = None
        
        if not self.issearching:
            return
        
        # Fallback to lobby owner to host the game if needed
        if not self.resultlist and not self.activelistrequest:
            self.OnEndResultList()
            
    def OnGameServerAccepts(self, publicip, gameport, serversteamid, **kwargs):
        """ Called when the server we requested accepted the game. """
        if not self.issearching:
            return
        
        if self.activeserverrequestdetails:
            details = self.activeserverrequestdetails
            if details.netadr.GetIP() != 0:
                publicip = details.netadr.GetIP()
            if details.netadr.GetConnectionPort() != 0:
                gameport = details.netadr.GetConnectionPort()
            serversteamid = details.steamid

            self.requestingserver_start_time = None
            self.activeserverrequestdetails = None
            
        print('Game server accepted game with public ip %d and game port %d. Players can connect now' % (publicip, gameport))
        
        steammatchmaking = steamapicontext.SteamMatchmaking()

        self.lobby.datamodel.publicip = publicip
        self.lobby.datamodel.gameport = gameport
        
        if not self.lobby.isofflinelobby and matchmaking.IsSessionActive():
            settings = matchmaking.matchsession.GetSessionSettings()
            if settings:
                # If there is a session, the local player is hosting the server
                # Other players should connect by the reservationid, since it provides some mechanics for when the player is hosting 
                # from behind a firewall.
                self.lobby.datamodel.reservationticket = settings.GetString('server/reservationid')
                if not self.lobby.datamodel.reservationticket:
                    PrintWarning('Match session active active, but no reservation ticket found!\n')
            else:
                PrintWarning('Match session active, but no settings found!\n')
        else:
            # All members in the lobby will receive a data update and should respond by connecting to the game server
            steammatchmaking.SetLobbyGameServer(self.steamidlobby, publicip, gameport, serversteamid)
        self.lobby.SetGameStarted()

        self.StopSearch()
        
    def OnGameServerDenies(self, **kwargs):
        print('Game server denied game. Should find another server')
        self.TryNextGameServerResult()

    def TryNextGameServerResult(self):
        # Remove our current try from the list
        if self.activeserverrequestdetails:
            try:
                self.resultlist.remove(self.activeserverrequestdetails)
            except ValueError:
                pass

            self.requestingserver_start_time = None
            self.activeserverrequestdetails = None
            
        if not self.issearching:
            return
            
        # Try next in list
        if self.resultlist:
            self.RequestGameServer(self.resultlist[0])
        else:
            self.OnEndResultList()

    def ClearGameServerRequest(self):
        self.requestingserver_start_time = None
        self.activeserverrequestdetails = None
            
    def OnEndResultList(self):
        """ Called when all possible options are tried from server result list.

            Will fallback to local hosting if:
            - mm_nolocal_hosting allows it
            - and no mm_password is set, which indicates the player explicitly wants to play on the matching server.
        """
        if not mm_nolocal_hosting.GetBool() and not mm_password.GetString():
            print('Falling back to lobby owner to host game')
            self.RequestLocalGameServer()
            return

        # Set message
        if mm_password.GetString():
            self.lobby.webview.AngularJsBroadcast('lobbying:msg', ['GL_StatusFailedFindReservedServer'])
        else:
            self.lobby.webview.AngularJsBroadcast('lobbying:msg', ['GL_StatusFailedFindServer'])
        print('No remote wars game servers found. Local hosting is disallowed, so stopping search.')
        self.StopSearch()


