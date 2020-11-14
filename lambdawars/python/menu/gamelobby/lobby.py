""" Provides the game lobby webview component.

Based on the WebLobby component.

The game lobby has the following states:
- creating: the lobby is being created on the Steam back-end
- joining: a player is joining an existing lobby on the Steam back-end
- lobbying: players are in an active lobby and deciding about the game to be played
- searching: the game is being started and searching for a suitable server
- gamestarted: found a server, signals the players can connect
- gameended: post game, indicates players can leave the lobby
"""

from ..lobby import WebLobby
from .lobbydatamodel import LobbyGameDataModel
from .settingsinfo import SettingsInfo
from .lobbymatchmaking import LobbyMatchmaking

import srcmgr
import kvdict

from srcbuiltins import Color, KeyValues, KeyValuesToDict
import os
import random
import filesystem
from cef import jsbind
from steam import steamapicontext, CSteamID, servernetadr, ELobbyComparison, LobbyMatchListCallResult, k_uAPICallInvalid
from gameinterface import engine, Plat_FloatTime, ConVarRef
import matchmaking
from core.signals import lobby_gameended, steam_p2p_connectfail, lobby_received_pong, lobby_match_uuid
from core.gamerules.info import dbgamerules

mm_password = ConVarRef('mm_password')


class WebNumGamesMatchListCallResult(LobbyMatchListCallResult):
    """ Callback object for getting the number of games.
    """
    def OnLobbyMatchList(self, lobbymatchlist, iofailure):
        self.webview.AngularJsBroadcast('menu:numgames', [lobbymatchlist.lobbiesmatching])


class WebGameLobby(WebLobby):
    defaultobjectname = 'gamelobby'
    
    settingsinfo = None
    lobbymatchmaking = None
    lobbyownerid = None
    #: Autojoin game when started. Set to true during lobbying state.
    autojoin = False 
    
    defaultlobbytype = 'public'
    
    _lastlobbystate = None
    _nexttryconnect = 0

    max_members = 32

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.kicked_from_lobbies = []
        
        lobby_gameended.connect(self.OnLobbyGameEnded)
        lobby_match_uuid.connect(self.OnLobbyMatchUUID)
        lobby_received_pong.connect(self.OnReceivedPong)
        steam_p2p_connectfail.connect(self.OnSteamP2PConnectFail)
        
    def OnDestroy(self):
        super().OnDestroy()
        
        lobby_gameended.disconnect(self.OnLobbyGameEnded)
        lobby_match_uuid.disconnect(self.OnLobbyMatchUUID)
        lobby_received_pong.disconnect(self.OnReceivedPong)
        steam_p2p_connectfail.disconnect(self.OnSteamP2PConnectFail)
        
        if self.lobbymatchmaking:
            self.lobbymatchmaking.OnDestroy()
            self.lobbymatchmaking = None
    
    @jsbind()
    def setPlayerData(self, methodargs):
        """ Sets a player specific setting.
        
            This is broadcast to all players in the lobby through chat.
            The lobby owner will pick this up, validate the setting and apply
            it to the lobby data.
        """
        key = methodargs[0]
        value = methodargs[1]
        slotid = methodargs[2]
        self.SendLobbyChatMsg('player', '%s=%s %s' % (key, value, slotid))
    
    @jsbind()
    def requestSlot(self, methodargs):
        """ Request for taking a slot.
        
            This is broadcast to all players in the lobby through chat.
            The lobby owner will pick this up, validate the setting and apply
            it to the lobby data.
        """
        slot = methodargs[0]
        self.SendLobbyChatMsg('slot', slot)
        
    @jsbind()
    def addCPU(self, methodargs):
        if not self.islobbyowner:
            return
        slot = methodargs[0]
        self.settingsinfo.AddCPUToSlot(slot)
        
    @jsbind()
    def removeCPU(self, methodargs):
        if not self.islobbyowner:
            return
        slot = methodargs[0]
        self.settingsinfo.RemoveCPUFromSlot(slot)
        
    @jsbind()
    def kickPlayer(self, methodargs):
        if not self.islobbyowner:
            return
        slotid = methodargs[0]
        datamodel = self.datamodel
        slots = datamodel.slots
        slot = slots[slotid]
        
        playerdata = slot.get('player', None)
        if playerdata is not None:
            self.kickPlayerBySteamID([playerdata['steamid']])
        
    @jsbind()
    def kickPlayerBySteamID(self, methodargs):
        """ Kicks a player from the lobby.

            Args:
                methodargs (list): contains one argument, the steam id (str).
        """
        if not self.islobbyowner:
            return
            
        datamodel = self.datamodel
        playersteamid = CSteamID(int(methodargs[0]))
        
        lobbyownerid = self.GetLobbyOwner()
        if playersteamid == lobbyownerid:
            # Can't kick yourself. Well, you could, but you know...
            return
        # Mark as kicked, so everybody ignores the player (since you can't truly kick).
        datamodel.MarkPlayerKicked(playersteamid)
        # Make sure the player is no longer in a slot
        self.settingsinfo.FindAndRemovePlayerFromSlot(playersteamid)
        
    @jsbind()
    def goSpectate(self, methodargs):
        self.SendLobbyChatMsg('spectate')
        
    @jsbind()
    def invite(self, methodargs):

        steamapicontext.SteamFriends().ActivateGameOverlay("LobbyInvite")
        
    @jsbind()
    def setSetting(self, methodargs):
        """ Sets a lobby settings.
        
            Always executed by the lobby owner. No-op in case of other players.
        """
        key = methodargs[0]
        value = methodargs[1]
        self.SetSetting(key, value)
        
    @jsbind()
    def setCustomField(self, methodargs):
        """ Sets a game mode custom field. """
        key = methodargs[0]
        value = methodargs[1]
        datamodel = self.datamodel
        datamodel.SetCustomLobbyData(key, value)
        
    @jsbind(hascallback=True)
    def getMapList(self, methodargs):
        return [list(self.settingsinfo.availablemaps.keys())]
    
    @jsbind(hascallback=True)
    def getModeList(self, methodargs):
        return [list(self.settingsinfo.availablemodes.keys())]
    
    @jsbind()
    def launch(self, methodargs):
        """ Tries to launch the game."""
        if not self.islobbyowner or not self.islobbying:
            return
            
        # state of lobby should be correct
        datamodel = self.datamodel
        if datamodel.lobbystate != 'lobbying':
            PrintWarning('launch: lobby is not lobbying. Cannot launch game.\n')
            return
            
        # Make sure slots are valid at this point
        self.settingsinfo.ValidateSlots()
            
        gamedata = self.BuildGameData()
        
        # Selected game mode should exist
        info = dbgamerules.get(datamodel.mode, None)
        if not info:
            self.SendLobbyChatMsg('globalmsg', 'Found an invalid game mode')
            return
            
        # Custom validation by the game mode
        success, errorMsg = info.ValidateGameSettings(KeyValuesToDict(gamedata))
        if not success:
            self.SendLobbyChatMsg('globalmsg', errorMsg)
            return
            
        # Everybody should be ready
        if not self.isofflinelobby and not self.settingsinfo.IsEverybodyReady():
            self.SendLobbyChatMsg('globalmsg', 'Some players are not ready yet.')
            return
            
        self.lobbymatchmaking.StartSearch(steamidlobby=self.steamidlobby, gamedata=gamedata)

    @jsbind()
    def cancel_launch(self, methodargs):
        """ Cancel launch if no server is found yet. """
        print('Canceled launch')
        self.lobbymatchmaking.StopSearch()
        
    @jsbind()
    def joingame(self, methodargs):
        """ Join the game when in a lobby.
            This method is intended for rejoining a game after a disconnect (for whatever reason). """
        self.JoinGame()
        
    def AddNumGamesFilters(self):
        """ Adds lobby match filters based to get the number of lobbies with games in progress. """
        self.AddLobbyTypeFilters(limitversion=False)
        
        steammatchmaking = steamapicontext.SteamMatchmaking()
        steammatchmaking.AddRequestLobbyListStringFilter('lobbystate', 'gamestarted', ELobbyComparison.k_ELobbyComparisonEqual)
        
    @jsbind()
    def refreshnumgames(self, methodargs):
        """ Counts number of games in progress based on the number of lobbies marked as such. """
        matchmaking = steamapicontext.SteamMatchmaking()
        if not matchmaking:
            return
        
        self.AddNumGamesFilters()
        
        steamapicall = matchmaking.RequestLobbyList()
        if steamapicall != k_uAPICallInvalid:
            callback = WebNumGamesMatchListCallResult(steamapicall)
            callback.webview = self.webview
            self.numgamescallback = callback
        else:
            PrintWarning('refreshnumgames: Failed to make lobby list request\n')

    @jsbind()
    def setMMPassword(self, methodargs):
        """ Sets mm password for dedicated server matching. """
        mm_password.SetValue(methodargs[0])

    def FilterLobbyFromList(self, steamid):
        """ Filter method for not showing lobbies in lobby list.

            Args:
                steamid (CSteamID): lobby steam id

            Returns:
                bool: False for not filtering the lobby
        """
        return steamid in self.kicked_from_lobbies

    def IsOnlyPlayer(self):
        if self.isofflinelobby:
            return True
        steammatchmaking = steamapicontext.SteamMatchmaking()
        return steammatchmaking.GetNumLobbyMembers(self.steamidlobby) == 1

    @property
    def islobbying(self):
        """ Tests if lobby is in lobbying mode. """
        datamodel = self.datamodel
        return datamodel and datamodel.lobbystate == 'lobbying'

    def BuildGameData(self):
        datamodel = self.datamodel

        steamfriends = steamapicontext.SteamFriends()
        
        gamedata = KeyValues('GameData')
        
        # Required settings
        system = KeyValues('system')
        #system.SetString('netflag', '')
        system.SetString('network', 'LIVE' if (not self.isofflinelobby and (not self.IsOnlyPlayer() or self.lobbytype != 'private')) else 'OFFLINE')
        system.SetString('access', 'public')
        gamedata.AddSubKey(system)
        
        members = KeyValues('members')
        members.SetInt('numSlots', 16)
        gamedata.AddSubKey(members)
        
        game = KeyValues('game')
        game.SetString('mode', datamodel.mode)
        game.SetString('mission', datamodel.map)
        game.SetString('type', datamodel.teamsetup)
        
        # Add custom fields
        kvcustomfields = KeyValues('customfields')
        customfields = self.settingsinfo.customfields
        for id, cf in customfields.items():
            kvcustomfields.SetString(id, cf['selectedvalue'])
        game.AddSubKey(kvcustomfields)

        # Add players
        numplayers = 0
        slots = datamodel.slots
        for idx, slot in enumerate(slots):
            type = slot['type']
            if type not in ['player']:
                continue
        
            player = KeyValues('player')
            player.SetInt('team', slot['team'])
            player.SetString('availablepositions', ','.join(map(str,slot['availablepositions'])))
            
            player.SetBool('iscpu', slot['iscpu'])
            player.SetString('cputype', slot['cputype'])
            player.SetString('difficulty', slot['difficulty'])
                
            if type == 'player':
                playerdata = slot['player']
                if not slot['iscpu']:
                    user_steamid = CSteamID(int(playerdata['steamid']))
                    player.SetString('steamid', playerdata['steamid'])
                    player.SetString('playername', steamfriends.GetFriendPersonaName(user_steamid))
                else:
                    player.SetString('steamid', playerdata['steamid'])
                    player.SetString('playername', 'CPU #%d' % idx)

                faction = playerdata['faction']
                if faction == '__random__':
                    settings_factions = set(self.settingsinfo.availablefactions.keys())
                    settings_factions.discard('__random__')
                    faction = random.sample(settings_factions, 1)[0]

                player.SetString('faction', faction)
                player.SetColor('color', self.settingsinfo.allcolors.get(playerdata['color'], {'color' : Color(0, 255, 0, 255)})['color'])
            
            game.AddSubKey(player)
            numplayers += 1
        
        game.SetInt('numplayers', numplayers)
        
        gamedata.AddSubKey(game)
        
        if self.isofflinelobby:
            server = KeyValues('server')
            server.SetString('mode', 'listen')
            server.SetString('server', 'listen')
            gamedata.AddSubKey(server)
        
            options = KeyValues('options')
            options.SetString('server', 'listen')
            gamedata.AddSubKey(options)
        
        return gamedata
        
    def OnLobbyGameEnded(self, lobbysteamid, *args, **kwargs):
        if self.steamidlobby != lobbysteamid:
            return
            
        if not self.islobbyowner:
            return

        # Lock lobby by setting to gameended:
        #self.datamodel.lobbystate = 'gameended'
        # Open again for new game:
        self.datamodel.lobbystate = 'lobbying'

    def OnLobbyMatchUUID(self, match_uuid, *args, **kwargs):
        if not self.islobbyowner:
            return

        self.datamodel.match_uuid = match_uuid

    def OnReceivedPong(self, steamidremote, *args, **kwargs):
        """ Callback from a WarsSendPingMessage action on success.
            Used for testing Steam p2p connection to other players in the lobby.
        """
        if not self.islobbyowner:
            return
            
        datamodel = self.datamodel
        if not datamodel:
            return
            
        usersteamid = steamapicontext.SteamUser().GetSteamID()
        datamodel.SetPlayerConnectState(usersteamid, steamidremote, True)
        print('Lobby: Received pong from test connection to user with steam id %s' % (str(steamidremote)))
            
    def OnSteamP2PConnectFail(self, steamidremote, *args, **kwargs):
        """ Notifies if steam p2p connection to other player failed.
        
            Used for indicating a connection is bad to other players.
        """
        if not self.islobbyowner:
            return
            
        datamodel = self.datamodel
        if not datamodel:
            return

        if not self.HasLobbyMemberWithSteamID(steamidremote):
            return
            
        usersteamid = steamapicontext.SteamUser().GetSteamID()
        datamodel.SetPlayerConnectState(usersteamid, steamidremote, False)
        PrintWarning('Lobby: failed to test connection to user with steam id %s\n' % (str(steamidremote)))
        
    def TestGameServerGameInProgress(self):
        """ Tests if the game server is still running and
            if the game is still in progress. Changes state
            to "gameended" if this is not the case.
            This is called periodically when in the visible
            lobby.
        """
        if not self.islobbyowner:
            return
        datamodel = self.datamodel
        if not datamodel:
            return
          
        if datamodel.lobbystate != 'gamestarted':
            return
        
        # Case 1: reservation ticket is set and we are the lobby owner
        # Case 2: offline lobby
        # In these cases we are always hosting the server
        # Case 3: lobby game server is set, so we play on a dedicated server
        # In this case we need to request the game server status
        if self.isofflinelobby or datamodel.reservationticket:
            if not engine.IsClientLocalToActiveServer():
                #datamodel.lobbystate = 'gameended'
                self.OnLobbyGameEnded(self.steamidlobby)
        else:
            # TODO: ask status from dedicated server
            pass
            
    def AddLobbyListFilters(self):
        """ Adds filters for list lobbies Steam call. """
        super().AddLobbyListFilters()
        
        steammatchmaking = steamapicontext.SteamMatchmaking()
        steammatchmaking.AddRequestLobbyListStringFilter('lobbystate', 'lobbying', ELobbyComparison.k_ELobbyComparisonEqual)
        
    def OnLeftLobby(self, steamidlobby):
        super().OnLeftLobby(steamidlobby)
        
        rememberedsteamidlobby = self.GetRememberedActiveLobby()
        if rememberedsteamidlobby.IsValid() and rememberedsteamidlobby == steamidlobby:
            self.ClearRememberActiveLobby()
        
        # Set state to None in js, so the gamelobby UI gets cleaned up
        self.webview.CallServiceMethod('gamelobbymanager', 'setStateWithApply', ['none'])
        
        self._lastlobbystate = None
        if self.lobbymatchmaking:
            self.lobbymatchmaking.OnDestroy()
        self.lobbymatchmaking = None
        self.settingsinfo = None

    def OnLobbyOwnerChanged(self, oldownerid):
        if self.islobbyowner:
            # Make sure we have the latest copy of the data
            # Afterwards won't be reading anymore, since the lobby owner contains the true data (no need to read back)
            self.ReadData()

            # Probably doesn't happens, but make sure we are not marked as kicked
            lobbyownerid = self.GetLobbyOwner()
            datamodel = self.datamodel
            if datamodel and datamodel.IsPlayerKicked(lobbyownerid):
                datamodel.ClearPlayerKicked(lobbyownerid)
            
    def JoinGame(self):
        """ Joins the game server if started. """
        if engine.IsConnected():
            return False
            
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if not steammatchmaking:
            return False
            
        # By reservation ticket
        if self.datamodel.reservationticket:
            if not engine.IsClientLocalToActiveServer():
                publicip = self.datamodel.publicip
                gameport = self.datamodel.gameport
                if publicip and gameport:
                    addr = servernetadr()
                    addr.Init(publicip, 0, gameport)
                    print('Public address of reserved game server: %s' % addr.GetConnectionAddressString())

                print('Connecting to game server with reservation ticket %s' % self.datamodel.reservationticket)
                matchmaking.MatchSession(KeyValues.FromString(
                    'settings',
                    '''system {
                        network LIVE
                    }
                    options {
                        action joinsession
                        sessionid %s
                    } ''' % self.datamodel.reservationticket))
            return True
            
        # By server ip
        success, ip, port, serversteamid = steammatchmaking.GetLobbyGameServer(self.steamidlobby)
        if not success:
            PrintWarning('Launch game specified, but no game server set\n')
            return False

        # TODO: Refine this check. Need to test if this player is already connected to the server
        if not engine.IsClientLocalToActiveServer():
            addr = servernetadr()
            addr.Init(ip, 0, port)
            print('Connecting to game server at %s with steamid %s' % (addr.GetConnectionAddressString(),
                                                                       str(serversteamid)))
            engine.ClientCommand('connect %s' % (addr.GetConnectionAddressString()))
        else:
            print('Already connected since hosting')
                        
        return True
        
    def UpdateAutoJoin(self):
        """ Tests if player should autojoin if game is started/in progress. """
        lobbystate = self.datamodel.lobbystate
        if not self.autojoin or lobbystate != 'gamestarted' or self.isofflinelobby:
            return
            
        if not engine.IsConnected() and self._nexttryconnect < Plat_FloatTime():
            if self.JoinGame():
                self.autojoin = False
            else:
                self._nexttryconnect = Plat_FloatTime() + 2.0
                
    def SetGameStarted(self):
        """ Called by lobbymatchmaking once a server is found.
            changes the state of the lobby to started. 
        """
        # May connect too soon, so have a very short delay...
        self._nexttryconnect = Plat_FloatTime() + 2.5
            
        self.datamodel.lobbystate = 'gamestarted'
                
    def UpdateLobbyState(self):
        datamodel = self.datamodel
        lobbystate = datamodel.lobbystate
            
        if self._lastlobbystate == lobbystate:
            return
        self._lastlobbystate = lobbystate
        
        self.webview.CallServiceMethod('gamelobbymanager', 'setStateWithApply', [lobbystate])
            
        if lobbystate == 'gamestarted':
            # For easy rejoining: remember the steamid lobby
            self.SetRememberActiveLobby(self.steamidlobby)
        elif lobbystate == 'lobbying':
            # Joins the server. Not needed in case of the lobby owner
            self.autojoin = True
        if lobbystate != 'gamestarted':
            # This data shouldn't be set in other states
            if self.islobbyowner:
                datamodel.reservationticket = ''
                datamodel.publicip = ''
                datamodel.gameport = ''
            self.ClearRememberActiveLobby()
            
    _old_map = None
    
    def ShouldFilterLobbyChatMsg(self, data):
        if self.isofflinelobby:
            return False
        datamodel = self.datamodel
        if datamodel and datamodel.IsPlayerKicked(data.steamiduser):
            DevMsg(1, 'Ignoring chat msg from kicked user\n')
            return True
        return False

    def TestPlayerKickedAndShouldLeave(self):
        datamodel = self.datamodel
        if datamodel and datamodel.IsPlayerKicked(steamapicontext.SteamUser().GetSteamID()):
            DevMsg(1, 'I got kicked, so I am leaving this lobby\n')
            # Remember to not show the lobby in the online list again
            self.kicked_from_lobbies.append(self.steamidlobby)
            # Be a good boy and leave the lobby
            self.leavelobby([])
            # Show a dialog we were kicked
            self.webview.AngularJsBroadcast('user:kicked', [])
            return True
        return False

    def OnLobbyDataUpdate(self, data):
        """ Steam callback when lobby data changes. """
        steamidlobby = CSteamID(data.steamidlobby)
        #steamidmember = CSteamID(data.steamidmember)
        if not data.success or steamidlobby != self.steamidlobby:
            self.TestActiveLobbyResult(data)
            return

        super().OnLobbyDataUpdate(data)

    def PostReadData(self, read_data_changed_keys):
        if self.TestPlayerKickedAndShouldLeave():
            return

        datamodel = self.datamodel
        if not datamodel:
            return

        self.UpdateLobbyState()
        self.UpdateLobby()

        if self.jshandler:
            for key in read_data_changed_keys:
                if key.startswith('kicked_'):
                    steamid_kicked_player = CSteamID(int(key.split('kicked_')[1]))
                    userinfo = self.BuildUserInfo(steamid_kicked_player)
                    DevMsg(1, 'User %s was kicked\n' % (userinfo['username']))
                    if self.jshandler:
                        self.Invoke(self.jshandler, 'OnLobbyUserKicked', [userinfo])
        
    def UpdateLobby(self):
        if not self.steamidlobby:
            return
           
        islobbyowner = self.islobbyowner
        
        # Check for changes in lobby owner (caused by old owner leaving for example)
        lobbyownerid = self.GetLobbyOwner()
        if self.lobbyownerid != lobbyownerid:
            self.lobbyownerid = lobbyownerid
            self.OnLobbyOwnerChanged(self.lobbyownerid)
            
        if not islobbyowner:
            # Check for map changes for non lobby owners
            # They need the map information for displaying the minimap
            if self._old_map != self.datamodel.map:
                self.settingsinfo.OnModeChanged()
            self.settingsinfo.RebuildAvailableFactions()
            
        # Always update lists for slot specific dropdowns
        self.settingsinfo.RebuildAvailableColors()
        self.settingsinfo.RebuildCustomFields()
            
        # Update settingsinfo to reflect potential changes
        self.settingsinfo.islobbyowner = islobbyowner
        
        if self.jshandler:
            settings = self.BuildSettingsInfo(self.steamidlobby)

            # Do not update if there is no valid mode yet.
            # Indicates not all data is received yet and causes unneeded UI render/updates
            if settings.get('mode', None):
                lobby_members = self.BuildLobbyMembersInfoList()
                self.Invoke(self.jshandler, 'OnLobbyDataChanged', [settings, lobby_members, self.datamodel.slots])
            
    def BuildSpectatorList(self):
        spectators = []
        steamfriends = steamapicontext.SteamFriends()
        if self.isofflinelobby:
            usersteamid = steamapicontext.SteamUser().GetSteamID()
            if not self.datamodel.FindPlayerSlot(usersteamid):
                spectators.append({
                    'name': steamfriends.GetFriendPersonaName(usersteamid),
                    'steamid': str(usersteamid),
                    'islocaluser': True,
                })
        else:
            steammatchmaking = steamapicontext.SteamMatchmaking()
            for i in range(0, steammatchmaking.GetNumLobbyMembers(self.steamidlobby)):
                usersteamid = steammatchmaking.GetLobbyMemberByIndex(self.steamidlobby, i)
                if not self.datamodel.FindPlayerSlot(usersteamid):
                    spectators.append({
                        'name': steamfriends.GetFriendPersonaName(usersteamid),
                        'steamid': str(usersteamid),
                        'islocaluser': usersteamid == steamapicontext.SteamUser().GetSteamID()
                    })
        return spectators

    def HasLobbyMemberWithSteamID(self, steamid):
        steammatchmaking = steamapicontext.SteamMatchmaking()
        for i in range(0, steammatchmaking.GetNumLobbyMembers(self.steamidlobby)):
            usersteamid = steammatchmaking.GetLobbyMemberByIndex(self.steamidlobby, i)
            if steamid == usersteamid:
                return True
        return False

    def FindSlotWithSteamID(self, steamid):
        datamodel = self.datamodel
        if not datamodel:
            return None
            
        slots = datamodel.slots
        for slot in slots:
            playerdata = slot['player']
            if playerdata and playerdata['steamid'] == str(steamid):
                return slot
                
        return None
                    
    def BuildUserInfo(self, steamid):
        """ Builds info entry for a given user steam id. """
        userdata = super().BuildUserInfo(steamid)
        datamodel = self.datamodel
        if datamodel:   
            lobbyowner = self.GetLobbyOwner()
            if datamodel.lobbytype != 'offline':
                userdata['connectstate'] = datamodel.GetPlayerConnectState(lobbyowner, steamid)

            foundslot = self.FindSlotWithSteamID(steamid)
            if foundslot:
                userdata.update({
                    'faction': foundslot['player']['faction'],
                    'color': foundslot['player']['color'],
                    'ready': foundslot['player']['ready'],
                    'islocaluser': foundslot['player']['islocaluser'],
                    'localslotid': foundslot['slotid'],
                })
        return userdata
        
    def BuildSettingsInfo(self, steamidlobby):
        settingsinfo = super().BuildSettingsInfo(steamidlobby)
        
        if self.steamidlobby == steamidlobby:
            foundslot = self.FindSlotWithSteamID(steamapicontext.SteamUser().GetSteamID())
            
            # Building info for lobby in which is player
            datamodel = self.datamodel
            settingsinfo.update({
                'mode': datamodel.mode,
                'map': datamodel.map,
                'teamsetup': datamodel.teamsetup,
                'islobbyowner': self.islobbyowner,
                'spectators': self.BuildSpectatorList(),
                'numslots': datamodel.numslots,
                'numtakenslots': datamodel.numtakenslots,
                'localslotid': foundslot['slotid'] if foundslot else None,
                'mm_password': mm_password.GetString(),
                'match_uuid': datamodel.match_uuid,
            })
            
            if self.settingsinfo:
                settingsinfo.update({
                    'availablemodes': self.settingsinfo.availablemodes,
                    'availablemaps': self.settingsinfo.availablemaps,
                    'availablefactions': self.settingsinfo.availablefactions,
                    'availablecolors': self.settingsinfo.availablecolors,
                    'availabledifficulties': self.settingsinfo.availabledifficulties,
                    'customfields': self.settingsinfo.customfields,
                })
        else:
            # Getting information for a lobby listing
            steammatchmaking = steamapicontext.SteamMatchmaking()
            settingsinfo.update({
                'mode': steammatchmaking.GetLobbyData(steamidlobby, 'mode'),
                'map': steammatchmaking.GetLobbyData(steamidlobby, 'map'),
                'teamsetup': steammatchmaking.GetLobbyData(steamidlobby, 'teamsetup'),
                'numslots': steammatchmaking.GetLobbyData(steamidlobby, 'numslots'),
                'numtakenslots': steammatchmaking.GetLobbyData(steamidlobby, 'numtakenslots'),
            })
            
            maprespath = os.path.join('maps', settingsinfo['map']) + '.res'
            if filesystem.FileExists(maprespath):
                kvres = kvdict.LoadFileIntoDictionaries(maprespath)
                overview_path = kvres.get('material', '')
                settingsinfo['overviewsrc'] = 'vtf://%s' % overview_path
                
        return settingsinfo
        
    def OnLobbyUserEntered(self, steamiduser):
        """ Steam callback when user enters lobby. """
        # Don't find slot and don't display message for kicked user
        datamodel = self.datamodel
        if datamodel and datamodel.IsPlayerKicked(steamiduser):
            return

        super().OnLobbyUserEntered(steamiduser)
        
        if self.islobbyowner:
            foundslot = self.FindSlotWithSteamID(steamiduser)
            if not foundslot:
                self.settingsinfo.FindSlotForPlayer(steamiduser)
                
            usersteamid = steamapicontext.SteamUser().GetSteamID()
            if usersteamid != steamiduser:
                matchmaking.WarsSendPingMessage(steamiduser)
        
    def OnLobbyUserLeft(self, steamiduser):
        if self.islobbyowner:
            # Remove from slots
            self.settingsinfo.FindAndRemovePlayerFromSlot(steamiduser)

            # Could clear the kicked status, but then the player just rejoins
            #datamodel = self.datamodel
            #if datamodel and datamodel.IsPlayerKicked(steamiduser):
            #    datamodel.ClearPlayerKicked(steamiduser)

        # Don't call super so it does not display the user left message
        datamodel = self.datamodel
        if datamodel and datamodel.IsPlayerKicked(steamiduser):
            return
        super().OnLobbyUserLeft(steamiduser)
        
    def OnLobbyCreated(self, lobbycreated, iofailure):
        """ Steam callback when lobby is created. """
        if not super().OnLobbyCreated(lobbycreated, iofailure):
            return False
        
        lobbyowner = self.GetLobbyOwner()
        self.settingsinfo.FindSlotForPlayer(lobbyowner)
        return True
        
    def CreateLobbyDataModel(self, steamidlobby):
        return LobbyGameDataModel(steamidlobby, offline=bool(self.lobbytype == 'offline'))
        
    def OnJoinOrCreateLobby(self, lobbymembers):
        self._lastlobbystate = None
        self._nexttryconnect = 0
        self.lobbymatchmaking = LobbyMatchmaking(self, gamedir=srcmgr.GetModDirectory())
        self.settingsinfo = SettingsInfo(self)
        self.datamodel.InitSettingsInfoCallbacks(self, self.islobbyowner)

        if not super().OnJoinOrCreateLobby(lobbymembers):
            return False

        if self.TestPlayerKickedAndShouldLeave():
            return False

        # Version may already be received upon joining
        if not self.islobbyowner and self.datamodel.version is not None:
            self.OnVersionReceived()
        
        return True

    def OnVersionReceived(self):
        """ Verifies other user is running the same version.
            This can happen when the user invites a friend into the lobby from a different version.
        """
        version = self.datamodel.version
        if version != engine.GetProductVersionString():
            DevMsg(1, 'Version does not match. Leaving lobby %s != %s\n' % (version, engine.GetProductVersionString()))
            # Different version and leave the lobby
            self.leavelobby([])
            # Show a dialog warning user about version
            self.webview.AngularJsBroadcast('user:versionmismatch', [])

    def SetSetting(self, key, value):
        if not hasattr(self.datamodel, key):
            PrintWarning('SetSetting: invalid key %s\n' % (key))
            return
            
        if not self.islobbyowner:
            return
            
        setattr(self.datamodel, key, value)
        self.settingsinfo.InvalidateReady() #remove ready if game settings change
            
    def GetSetting(self, key, noconvert=False):
        return getattr(self.datamodel, key, None)
            
    def BuildLobbyChatMsgHandlers(self):
        handlers = super().BuildLobbyChatMsgHandlers()
        handlers.update({
            'globalmsg': self.HandleLobbyGlobalMsg,
            'player': self.HandleLobbyPlayerDataMsg,
            'slot': self.HandleLobbySlotMsg,
            'spectate': self.HandleLobbySpectateMsg,
        })
        return handlers
        
    def HandleLobbyGlobalMsg(self, steamiduser, type, msg):
        if steamiduser != self.GetLobbyOwner():
            return
            
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnLobbyChatMsg', ['', msg])
        
    def HandleLobbyPlayerDataMsg(self, steamiduser, type, data):
        #print('HandleLobbyPlayerDataMsg %s' % (data))
        if not self.islobbyowner or not self.islobbying:
            return
        lobbyowner = self.GetLobbyOwner()
        
        # By default sets data for a user in the lobby
        # If a slot id is found, then the data is being set for a cpu
        key, value = data.strip().split('=', 1)
        try:
            value, slotid = value.split(' ', 1)
            slotid = int(slotid)
            # Since we found a slotid, the message should come from the lobby owner
            if lobbyowner != steamiduser:
                return
        except ValueError:
            slotid = None 
        
        print('Setting player data %s to value %s (slotid: %s)' % (key, value, slotid))
        datamodel = self.datamodel
        if key == 'faction':
            if value not in self.settingsinfo.availablefactions:
                PrintWarning('Trying to set invalid faction %s for player %s\n' % (value, str(steamiduser)))
                return
            if slotid != None:
                datamodel.SetSlotLobbyData(slotid, 'faction', value)
            else:
                datamodel.SetPlayerLobbyData(steamiduser, 'faction', value)
            #self.settingsinfo.InvalidateReady() #if player selects ready then he is ready! 
        elif key == 'color':
            if not self.settingsinfo.IsColorAvailable(value):
                PrintWarning('Trying to set invalid or unavailable color %s for player %s\n' % (value, str(steamiduser)))
                return
            if slotid is not None:
                datamodel.SetSlotLobbyData(slotid, 'color', value)
            else:
                datamodel.SetPlayerLobbyData(steamiduser, 'color', value)
            self.settingsinfo.RebuildAvailableColors()
        elif key == 'difficulty': # CPU Only
            founddiff = False
            for x in self.settingsinfo.availabledifficulties:
                if x['id'] == value:
                    founddiff = True
                    break
            if not founddiff:
                PrintWarning('Trying to set invalid difficulty %s for player %s\n' % (value, str(steamiduser)))
                return
            datamodel.SetSlotLobbyData(slotid, 'difficulty', value)
        elif key == 'ready':
            #if lobbyowner == steamiduser:
            #    value = True
        
            datamodel.SetPlayerLobbyData(steamiduser, 'ready', str(int(value)))
        else:
            PrintWarning('Trying to set unknown player data %s for player %s\n' % (key, str(steamiduser)))
        
    def HandleLobbySlotMsg(self, steamiduser, type, data):
        if not self.islobbyowner or not self.islobbying:
            return
            
        try: 
            slotid = int(data)
        except ValueError:
            PrintWarning('HandleLobbySlotMsg -> Invalid slot id: %s\n' % (slotid))
            return
            
        self.settingsinfo.TryTakeSlot(steamiduser, slotid)
            
    def HandleLobbySpectateMsg(self, steamiduser, type, data):
        if not self.islobbyowner or not self.islobbying:
            return
            
        self.settingsinfo.FindAndRemovePlayerFromSlot(steamiduser)
        
    __nexttestgameserver = 0

    def OnThink(self):
        """ Called each frame to update the webview when visible. """
        if not self.steamidlobby:
            return

        super().OnThink()

        curtime = Plat_FloatTime()

        datamodel = self.datamodel

        # Auto joining a server after found
        if datamodel:
            self.UpdateAutoJoin()

        # Updating matchmaking/server searching
        if self.lobbymatchmaking:
            self.lobbymatchmaking.Update()

        # When the game is in progress, test if the game server is still valid
        if self.__nexttestgameserver < curtime:
            self.__nexttestgameserver = curtime + 1.0
            self.TestGameServerGameInProgress()
            
    def OnNAError(self):
        """ Received n/a error from matchmaking...
        
            Could mean the autojoin failed....
        """
        datamodel = self.datamodel
        if not datamodel:
            return
            
        lobbystate = self.datamodel.lobbystate
        if engine.IsConnected() or lobbystate != 'gamestarted':
            return
            
        # Try auto joining again
        print('Retrying auto join after failing to join the first time...')
        self.autojoin = True
            
    __pathrememberedactivelobby = 'activelobby'

    def GetRememberedActiveLobby(self):
        if not filesystem.FileExists(self.__pathrememberedactivelobby):
            return CSteamID()
        strlobbysteamid = filesystem.ReadFile(self.__pathrememberedactivelobby, 'MOD').strip()
        if not strlobbysteamid:
            return CSteamID()
        try:
            return CSteamID(int(strlobbysteamid))
        except ValueError:
            return CSteamID()
        
    def SetRememberActiveLobby(self, lobbysteamid):
        filesystem.WriteFile(self.__pathrememberedactivelobby, 'MOD', str(lobbysteamid))

    def ClearRememberActiveLobby(self):
        filesystem.WriteFile(self.__pathrememberedactivelobby, 'MOD', '0')
        
    def StartTestActiveLobby(self):
        """ Starts a test for the active gamelobby.
            This allows a crashed player to rejoin after starting the game.
        """
        rememberedsteamidlobby = self.GetRememberedActiveLobby()
        if not rememberedsteamidlobby.IsValid():
            return
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if not steammatchmaking:
            return
        # RequestLobbyData results in a callback to UpdateLobbyData
        steammatchmaking.RequestLobbyData(rememberedsteamidlobby)
            
    def TestActiveLobbyResult(self, data):
        datasteamidlobby = CSteamID(data.steamidlobby)
        rememberedsteamidlobby = self.GetRememberedActiveLobby()
        if not rememberedsteamidlobby.IsValid() or datasteamidlobby != rememberedsteamidlobby:
            return
        if not data.success:
            self.ClearRememberActiveLobby()
            return
        
        # Join the lobby, this will allow the player to join the game again if still active. 
        # TODO: we could opt for also testing the lobby state, however I think it's also fine to join 
        # the lobby again if the game ended (since it means there are still other players in the lobby)
        self.webview.CallServiceMethod('gamelobbymanager', 'setStateWithApply', ['joining'])
        self.joinlobby([str(rememberedsteamidlobby)])
