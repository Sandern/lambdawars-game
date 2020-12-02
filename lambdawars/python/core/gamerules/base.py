from srcbase import FL_FROZEN, MAX_PLAYERS, Color, MOVETYPE_STRATEGIC, MOVETYPE_OBSERVER, TEAM_SPECTATOR, TEAM_UNASSIGNED
from vmath import Vector, QAngle, vec3_origin, AngleVectors
import sys
import traceback
import random

from core.factions import GetFactionInfo
from core.resources import HasEnoughResources, TakeResources, GiveResources
from playermgr import dbplayers, OWNER_LAST, PlayerInfo as PMGRPlayerInfo, relationships
from entities import D_LI, OBS_MODE_ROAMING, OBS_MODE_NONE
import srcmgr
from navmesh import RandomNavAreaPosition
from fow import FogOfWarMgr
from steam import CSteamID, steamapicontext

from .statistics_uploader import StatisticsUploader
from core.abilities import DoAbility, GetAbilityInfo, GetAbilityByID
from core.units import PrecacheUnit, CreateUnitFancy
from core.signals import FireSignalRobust, endgame, map_endgame, startgame
from core.usermessages import usermessage
from core.ui import ShowWinLoseDialog

from gamerules import CHL2WarsGameRules, gamerules, GameRules
from gameinterface import ConVarRef, engine, ConVar, concommand, FCVAR_CHEAT, PrecacheEffect
import matchmaking
import filesystem
if isserver:
    from .statistics_collector import StatisticsCollector
    from utils import (UTIL_EntityByIndex, UTIL_PlayerByIndex, UTIL_SayTextAll, UTIL_GetLocalPlayer,
                       UTIL_GetPlayers, UTIL_ListPlayersForOwnerNumber, UTIL_GetCommandClient, UTIL_ClientPrintAll,
                       HUD_PRINTTALK)
    from entities import entlist, DispatchSpawn, CreateEntityByName
    from playermgr import FindFirstFreeOwnerNumber, InfoStartWars
    from core.strategicai import CreateAIForFaction
    from gameinterface import CRecipientFilter
    from core.signals import playerdefeated
    from core.units import unitlist
else:
    from vgui import CHudElementHelper
    from core.signals import firedping, lobby_gameended, lobby_match_uuid
    from vgui.musicplayer import musicmanager
    from cef import viewport, CefPanel
    from achievements import WarsSteamStats

if __debug__:
    import mem_debug
    
mp_chattime = ConVarRef('mp_chattime')
mp_timelimit = ConVarRef('mp_timelimit')

if isserver:
    sv_crate_minfreq = ConVar('sv_crate_minfreq', '5', FCVAR_CHEAT)
    sv_crate_maxfreq = ConVar('sv_crate_maxfreq', '60', FCVAR_CHEAT)
    
PANEL_SCOREBOARD = "scores"

@usermessage()
def FirePing(pos, color, **kwargs):
    FireSignalRobust(firedping, pos=pos, color=color)

@usermessage()
def ClientFOWResetExplored(**kwargs):
    DevMsg(1, 'Resetting Fog of War explored state\n')
    FogOfWarMgr().ResetExplored()

@usermessage()
def ClientShowWaitingForPlayers(**kwargs):
    panel = gamerules.GetHudPanel('CefWaitingForPlayers')
    if not panel:
        return
        
    panel.visible = True

@usermessage()
def ClientUpdateWaitingForPlayers(wfptimeout, gameplayers, **kwargs):
    panel = gamerules.GetHudPanel('CefWaitingForPlayers')
    if not panel:
        return
        
    panel.visible = True
    panel.UpdatePanel(wfptimeout, gameplayers)

@usermessage()
def ClientHideWaitingForPlayers(**kwargs):
    panel = gamerules.GetHudPanel('CefWaitingForPlayers')
    if not panel:
        return
        
    panel.visible = False
@usermessage()
def ClientShowTimer(**kwargs):
    panel = gamerules.GetHudPanel('HudTimer')
    if not panel:
        return
        
    panel.visible = True
@usermessage()
def ClientHideTimer(**kwargs):
    panel = gamerules.GetHudPanel('HudTimer')
    if not panel:
        return
        
    panel.visible = False
@usermessage()
def ClientChangeTimer(time, **kwargs):
    panel = GameRules().hudrefs['HudTimer'].Get()
    panel.gametime = True
    panel.time = time

@usermessage(usesteamp2p=True)
def ClientEndGameMessage(lobbysteamid, winners, losers, *args, **kwargs):
    # Fire signal so lobby can cleaned up by the owner
    FireSignalRobust(lobby_gameended, lobbysteamid=lobbysteamid)
    
    gamerules.ClientEndGame(winners, losers)

@usermessage()
def ClientSetMatchUUID(match_uuid, **kwargs):
    gamerules.match_uuid = match_uuid
    gamerules.stats_uploader.VerifyPlayer(match_uuid)

    FireSignalRobust(lobby_match_uuid, match_uuid=match_uuid)


class WarsBaseGameRules(CHL2WarsGameRules):
    """ Base gamerules for Lambda Wars games. """
    def __init__(self):
        super().__init__()

        self.stats_uploader = StatisticsUploader()
        if isserver:
            # Collects match events and statistics and publish them to the match server
            self.stats_collector = StatisticsCollector()

        # List of valid game players (usually build from the gamelobby data)
        self.gameplayers = []
        # List of defeated players
        self.defeatedplayers = []
        
    def Precache(self):
        """ Precaches the game rules.
            Any game settings have been applied to gamerules at this point.
            Usually this should precache all the units.
        """
        # TODO: Move these precaches to a specific wars_game gamerules class
        PrecacheEffect('ManhackSparks')
        PrecacheEffect('StriderMuzzleFlash')
        PrecacheEffect('VortDispel')
        PrecacheEffect('HelicopterMegaBomb')
        PrecacheEffect('BoltImpact')
        PrecacheEffect('StunstickImpact')
        PrecacheEffect('WaterSurfaceExplosion')

        super().Precache()

        # For each player precache the start building. 
        # This building should precache all other stuff.
        for data in self.gameplayers:
            faction = GetFactionInfo(data['faction'])
            if faction:
                faction.Precache()
                if faction.startbuilding:
                    PrecacheUnit(faction.startbuilding)

        # Precache crate if crates are on
        if self.crates:
            PrecacheUnit('crate')

    def InitGamerules(self):
        """ Initializes the gamerules.
        
            Sets the default colors for the different players 
            (in case not launched from the gamelobby).
            Initializes the gamerules specific hud elements.
        """
        super().InitGamerules()

        self.statehandlers = self.BuildStateHandlers()
        self.state = self.defaultstate

        if isserver:
            # Ensure game server state is made ingame if started from matchmaking
            if matchmaking.GetWarsGameServerState() == matchmaking.k_EGameServer_StartingGame:
                matchmaking.SetWarsGameServerState(matchmaking.k_EGameServer_InGame)

            # Init the first 12 ownernumbers after the defaults
            dbplayers[OWNER_LAST] = PMGRPlayerInfo(color=Color(251, 126, 20, 255))
            dbplayers[OWNER_LAST+1] = PMGRPlayerInfo(color=Color(20, 100, 200, 255))
            dbplayers[OWNER_LAST+2] = PMGRPlayerInfo(color=Color(255, 0, 255, 255))
            dbplayers[OWNER_LAST+3] = PMGRPlayerInfo(color=Color(0, 128, 128, 255))
            dbplayers[OWNER_LAST+4] = PMGRPlayerInfo(color=Color(0, 255, 0, 255))
            dbplayers[OWNER_LAST+5] = PMGRPlayerInfo(color=Color(128, 0, 0, 255))
            dbplayers[OWNER_LAST+6] = PMGRPlayerInfo(color=Color(221, 204, 0, 255))
            dbplayers[OWNER_LAST+7] = PMGRPlayerInfo(color=Color(128, 75, 0, 255))
            dbplayers[OWNER_LAST+8] = PMGRPlayerInfo(color=Color(136, 102, 204, 255))
            dbplayers[OWNER_LAST+9] = PMGRPlayerInfo(color=Color(0, 255, 255, 255))
            dbplayers[OWNER_LAST+10] = PMGRPlayerInfo(color=Color(153, 204, 153, 255))
            dbplayers[OWNER_LAST+11] = PMGRPlayerInfo(color=Color(255, 128, 128, 255))
            
            
            self.ReadServerInfo()
        else:
            self.hudrefs = {}
            for hud in self.info.huds:
                modname, hudclsname = hud.rsplit('.', 1)
                __import__(modname)
                try:
                    hudcls = getattr(sys.modules[modname], hudclsname)
                except (KeyError, AttributeError):
                    PrintWarning('Invalid hud element %s in %s gamerules\n' % (hud, str(self)))
                    continue
                    
                try:
                    if issubclass(hudcls, CefPanel):
                        self.hudrefs[hudclsname] = hudcls(viewport)
                    else:
                        self.hudrefs[hudclsname] = CHudElementHelper(hudcls())
                except:
                    PrintWarning('Could not initialize hud panel %s:\n' % (hudclsname))
                    traceback.print_exc()
                
            # Changes playlist if specified by the new gamerules
            musicmanager.LoadPlayList(self.musicplaylist)
    
    def ShutdownGamerules(self):
        """ Shutdown gamerules.
        
            Clears the gamerules specific hud elements.
        """
        self._state = None
        self.stateinfo = None
        self.statehandlers.clear()

        super().ShutdownGamerules()
        
        if isclient:
            # Cleanup hud
            for name, hudhelper in self.hudrefs.items():
                if isinstance(hudhelper, CefPanel):
                    hudhelper.Remove()
                else:
                    if hudhelper and hudhelper.Get():
                        try: 
                            hudhelper.Get().DeletePanel()
                        except AttributeError: 
                            pass # Already dead
            self.hudrefs = {}
        else:
            # End game. No winners/losers. Indicate end is forced.
            # This will be a noop if the game is already properly ended.
            self.EndGame([], [], force_end=True)
            # Make sure game server is released
            self.GameServerGameEnded()

        if __debug__:
            mem_debug.CheckRefDebug(self)
            
    def ReadServerInfo(self):
        """ Reads and stores server information, such as the banner and motd. """
        hostfile = ConVarRef('hostfile')
        motdfile = ConVarRef('motdfile')
        
        # Read the host file
        pathid = 'MOD'
        self.serverhost = None
        if filesystem.FileExists(hostfile.GetString(), pathid):
            try:
                self.serverhost = filesystem.ReadFile(hostfile.GetString(), pathid, textmode=True).strip()
            except IOError as e:
                PrintWarning('ReadServerInfo: failed to read %s (%s)'% (hostfile.GetString(), e))
            
        # Read the motd file
        self.servermotd = None
        if filesystem.FileExists(motdfile.GetString(), pathid):
            try:
                self.servermotd = filesystem.ReadFile(motdfile.GetString(), pathid, textmode=True).strip()
            except IOError as e:
                PrintWarning('ReadServerInfo: failed to read %s (%s)'% (motdfile.GetString(), e))
            
    # Gamerules state handling
    _state = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, newstate):
        if self._state == newstate:
            return
        stateinfo = self.statehandlers.get(newstate, None)
        if not stateinfo:
            PrintWarning('gamerules.state: trying to set invalid state %s\n' % (newstate))
            return
            
        # Call left state handler for old state
        try:
            leftstate = self.stateinfo.get('leftstate', None)
            if leftstate:
                leftstate()
        except:
            traceback.print_exc()
            
        # Change to the new state
        self._state = newstate
        self.stateinfo = stateinfo
        
        # Call enter state handler
        try:
            enterstate = self.stateinfo.get('enterstate', None)
            if enterstate:
                enterstate()
        except:
            traceback.print_exc()
        
    def BuildStateHandlers(self):
        return {
            'main' : {'think' : self.MainThink, 'enterstate' : self.MainStart },
            'waitingforplayers' : {'think' : self.WaitingForPlayersThink, 'leftstate' : self.WaitingForPlayersEnd, 'enterstate' : self.WaitingForPlayersStart},
        }
            
    def Think(self):
        """ Updates the gamerules. """
        self.CheckMatchUUID()

        think = self.stateinfo.get('think', None)
        if think:
            try:
                think()
            except Exception:
                # Don't want to fallback to CMultiplayRules::think on exception, so just print the stack trace.
                traceback.print_exc()
            
    def MainStart(self):
        if self.gamestartpending:
            self.gamestartpending = False
            self.StartGame()
            
    def MainThink(self):
        """ Main think during the match.
            Usually tests for win/lost conditions.
        """
        self.UpdateGamePlayers()
        self.UpdateVoiceManager()
        time = gpGlobals.curtime - self.gametime 
        ClientChangeTimer(time)
    
        if self.CheckGameOver():
            return
                
        timelimit = mp_timelimit.GetFloat() * 60
        
        self.UpdateRandomCrate()
        
        if timelimit != 0 and gpGlobals.curtime >= timelimit:
            self.GoToIntermission()
            return

    def CheckMatchUUID(self):
        """ Checks if the match server returned a uuid for the running match yet.
            When that's the case, broadcast the uuid to all game players, so they
            can verify themself with the match server.
        """
        if not self.stats_collector or self.match_uuid:
            return
        if 'uuid' not in self.stats_collector.match_info:
            return

        self.match_uuid = self.stats_collector.match_info['uuid']

        msg_filter = CRecipientFilter()
        msg_filter.MakeReliable()
        [msg_filter.AddRecipient(w) for w in self.GetGamePlayers()]
        ClientSetMatchUUID(self.match_uuid, filter=msg_filter)

    def ClientConnected(self, client_index, name, address):
        """
            Args:
                client_index (int): Entity index of player
                name (str): Name of player
                address (str): Address of player

            Returns:
                None or str with reject reason
        """
        msg_filter = CRecipientFilter()
        msg_filter.MakeReliable()
        msg_filter.AddRecipient(client_index)
        ClientSetMatchUUID(self.match_uuid, filter=msg_filter)

        return None
            
    def BuildClientPlayerData(self, gameplayers):
        """ Builds simplified list for sending to client.
            Should be small and only contain what's needed.

            Args:
                gameplayers (list): contains dictionary per player with info.

            Returns: list containing essential info per player.
        """
        clientgameplayers = []
        for gp in gameplayers:
            # Note: don't include playername if there is already a steamid
            # In other words, only send playername for CPUs. Use steam api to
            # get name on client when needed.
            steamid = gp.get('steamid', None)
            playerdata = {
                'steamid' : steamid,
                'state' : gp.get('state', ''),
            }
            if not steamid:
                playerdata['playername'] = gp.get('playername', '')
            clientgameplayers.append(playerdata)
        return clientgameplayers
    
    _nextupdatewaitingforplayers = 0
    _wfpgotomaintime = 0
    _wfptimeout = 0

    def WaitingForPlayersThink(self):
        """ Main think function for when waiting for players to load pre-match. """
        # Send updated information to every player 
        self.UpdateGamePlayers()
        
        playersloading = False
        for gp in self.gameplayers:
            if gp['state'] == 'loading':
                playersloading = True
                break
        
        if self._nextupdatewaitingforplayers < gpGlobals.curtime:
            self._nextupdatewaitingforplayers = gpGlobals.curtime + 1.0
            ClientShowWaitingForPlayers()
            wfpgameplayers = self.BuildClientPlayerData(self.gameplayers)
            
            # First loaded player will trigger the time-out for other players
            if self._wfptimeout == 0:
                for gp in wfpgameplayers:
                    if gp['state'] != 'loading':
                        self._wfptimeout = gpGlobals.curtime + (60.0 * 1.5)
                        break
            ClientUpdateWaitingForPlayers(self._wfptimeout if playersloading else self._wfpgotomaintime, wfpgameplayers)
            
        # Change state to main if everybody is no longer loading
        if not playersloading or (self._wfptimeout != 0 and self._wfptimeout < gpGlobals.curtime):
            if self._wfpgotomaintime == 0:
                self._wfpgotomaintime = gpGlobals.curtime + 5.0
                
            if self._wfpgotomaintime < gpGlobals.curtime:
                if not playersloading:
                    print('All players are loaded. Changing to main gamerules state.')
                else:
                    print('Not all players are loaded, but starting anyway (taking too long). Changing to main gamerules state.')
                self.state = 'main'
                return
            
    def WaitingForPlayersStart(self):
        self._wfpgotomaintime = 0
        self._wfptimeout = 0
            
    def WaitingForPlayersEnd(self):
        ClientHideWaitingForPlayers()
            
    def GoToIntermission(self, showscoreboard=True):
        """ Set gameover to True and start intermission (show scoreboard). """
        if self.gameover:
            return False

        self.gameover = True

        self.intermissionendtime = gpGlobals.curtime + mp_chattime.GetInt()

        if showscoreboard:
            for i in range(0, MAX_PLAYERS):
                player = UTIL_PlayerByIndex(i)

                if not player:
                    continue

                player.ShowViewPortPanel(PANEL_SCOREBOARD)
                player.AddFlag(FL_FROZEN)
                
        return True

    def DoEndStatsRecord(self):
        """ Ends recording statistics, writes it to file and uploads to match server. """
        self.stats_collector.EndRecord()
        path = self.stats_collector.WriteToFile()
        if self.stats_uploader and 'uuid' in self.stats_collector.match_info:
            self.stats_uploader.UploadMatchFile(self.stats_collector.match_info['uuid'], path)
            
    def EndGame(self, winners, losers, observers=[], force_end=False):
        """ Goes in intermission and shows appropriate 
            messages to winners and losers.
            
            Args:
                winners (list): List of winners. Each entry is a dictionary (see BuildGamePlayerFromKV).
                losers (list): List of losers. Each entry is a dictionary (see BuildGamePlayerFromKV).
                
            Kwargs:
                observers (list): List of observers.
                force_end (bool): If end was forced. Winners and losers will be empty.
                                  This is called so it cleanup the game and still record the game as played.
                                  For example, this is the case if the host disconnects.
        """
        self.GameServerGameEnded()
        
        if force_end:
            # Force end is not a proper ending. Still try to write away the stats + upload to server.
            # The match won't be marked as ended.
            self.DoEndStatsRecord()
            return
        
        # Returns False if game is already over, so no other things are processed.
        if not self.GoToIntermission(showscoreboard=False):
            return
        
        # Ensure the defeated players message is printed
        for data in losers:
            self.PlayerDefeated(data)
        
        # Show appropriate dialogs
        winnernames = []
        losernames = []
        for data in winners:
            winnernames.append(data['playername'])
        for data in losers:
            losernames.append(data['playername'])
            
        DevMsg(1, 'EndGame: Winners: %s, Losers: %s\n' % (winnernames, losernames))
            
        # Tell winners they are winners
        msg_filter = CRecipientFilter()
        msg_filter.MakeReliable()
        [msg_filter.AddRecipient(w) for w in self.GetGamePlayers(winners)]
        ShowWinLoseDialog(winnernames, losernames, 'won', filter=msg_filter)
        
        # Tell losers they are losers
        msg_filter = CRecipientFilter()
        msg_filter.MakeReliable()
        [msg_filter.AddRecipient(l) for l in self.GetGamePlayers(losers)]
        ShowWinLoseDialog(winnernames, losernames, 'lost', filter=msg_filter)

        # Tell spectators/others game ended
        msg_filter = CRecipientFilter()
        msg_filter.MakeReliable()
        [msg_filter.AddRecipient(l) for l in self.GetSpectators()]
        ShowWinLoseDialog(winnernames, losernames, '', filter=msg_filter)
        
        # End notification (TODO: merge ShowWinLoseDialog into one call to ClientGameEnd)
        ClientEndGameMessage(matchmaking.GetActiveGameLobbySteamID(), self.BuildClientPlayerData(winners), self.BuildClientPlayerData(losers))
        
        FireSignalRobust(endgame, gamerules=self, winners=winners, losers=losers)
        FireSignalRobust(map_endgame[srcmgr.levelname], gamerules=self, winners=winners, losers=losers)

        # Finalize Stats
        self.DoEndStatsRecord()
        
    def ClientUpdateEndGameStats(self, playersteamid, stats, winners, losers):
        """ Updates stats after a end game.
            Allows gamerules implementations to fill in specific stats.
            Note these stats are defined on the Steamworks partner website, so you can't just
            add random stats.
        
            Args:
                playersteamid (CSteamID): SteamID of local player.
                stats (WarsUserStats_t): Stats object
                winners (list): list of winners. Dictionary entry for each player.
                losers (list): list of losers. Dictionary entry for each player.
        """
        # Update games total
        stats.games_total += 1
        
    def ClientEndGame(self, winners, losers):
        """ Handler for end game on client.
        
            Args:
                winners (list): list of winners. Dictionary entry for each player.
                losers (list): list of losers. Dictionary entry for each player.
        """
        # Update stats from active gamerules
        playersteamid = steamapicontext.SteamUser().GetSteamID()
        stats = WarsSteamStats().GetUserStats(playersteamid)
        self.ClientUpdateEndGameStats(playersteamid, stats, winners, losers)
        
        # Fire signals on client to update stats/for achievements
        FireSignalRobust(endgame, gamerules=self, winners=winners, losers=losers)
        FireSignalRobust(map_endgame[srcmgr.levelname], gamerules=self, winners=winners, losers=losers)
        
        # Likely modified stats, so a good moment to push back stats to Steam (and possible unlock some achievements)
        WarsSteamStats().StoreStats()

    def GetSteamIDSConnectedPlayers(self):
        """ Returns a set of steamids of connected players.
        """
        foundplayers = set()
        for i in range(0, MAX_PLAYERS):
            player = UTIL_PlayerByIndex(i)
            if not player or not player.IsConnected():
                continue
            foundplayers.add(engine.GetClientSteamID(player))
        return foundplayers

    def UpdateDisconnectedPlayer(self, gp):
        """ Prints warnings for players disconnected and forfeits them after 5 minutes. """
        if (self.gameover or
                not self.forfeit_disconnected_too_long or
                gp['state'] != 'disconnected' or
                not gp['lastconnectedtime'] or
                self.IsPlayerDefeated(gp)):
            return

        reconnect_time = 5  # In minutes
        seconds_unconnected = gpGlobals.curtime - gp['lastconnectedtime']
        if seconds_unconnected / 60 > 5:
            UTIL_ClientPrintAll(HUD_PRINTTALK, "#Wars_Chat_PlayerLeftDisconnectedTooLong",
                                gp['playername'])
            self.PlayerDefeated(gp)
        else:
            minutes_unconnected = round(seconds_unconnected / 60.0)
            minutes_left = reconnect_time - minutes_unconnected

            unconnected_last_minute_warning = gp['unconnected_last_minute_warning']
            if unconnected_last_minute_warning is None:
                unconnected_last_minute_warning = 100

            if 0 < minutes_left < unconnected_last_minute_warning:
                msg = "#Wars_Chat_DisconnectTimeRemaining" if minutes_left == 1 \
                    else '#Wars_Chat_DisconnectTimeRemainingPlural'
                UTIL_ClientPrintAll(HUD_PRINTTALK, msg,
                                    gp['playername'], str(minutes_left))
                gp['unconnected_last_minute_warning'] = minutes_left

    def UpdateGamePlayers(self):
        """ Updates state of game player (connected, disconnected, loading). """
        foundplayers = self.GetSteamIDSConnectedPlayers()

        for gp in self.gameplayers:
            new_state = None
            old_state = gp.get('state', 'loading')
            if gp['iscpu']:
                new_state = 'connected'
            else:
                if gp['steamid'] in foundplayers:
                    new_state = 'connected'
                    gp['lastconnectedtime'] = gpGlobals.curtime
                    gp['unconnected_last_minute_warning'] = None
                elif old_state == 'connected':
                    new_state = 'disconnected'

                    # Only print message if game is not over
                    if not self.gameover:
                        # Notify player disconnected
                        UTIL_ClientPrintAll(HUD_PRINTTALK, "#Wars_Chat_DisconnectWaitForReconnect",
                                            gp['playername'])
                elif not gp['lastconnectedtime']:
                    new_state = 'loading'

            if new_state:
                gp['state'] = new_state

            self.UpdateDisconnectedPlayer(gp)


    def ClientDisconnected(self, client):
        """ Handler when a player disconnects.

            Args:
                client (entity): Handle to player entity
        """
        super().ClientDisconnected(client)
        
        playername = client.GetPlayerName()
        UTIL_ClientPrintAll(HUD_PRINTTALK, "#Game_disconnected", playername if playername else '<unconnected>')
        
        print('Dispatched disconnect message %s' % (playername))
        
    def PlayerDefeated(self, data):
        """ Marks the specified gamelobby player entry as defeated.

            Args:
                data (dict): Entry from self.gameplayers.
        """
        if data in self.defeatedplayers:
            return
            
        UTIL_SayTextAll('Player %s was defeated' % (data['playername']))
        self.defeatedplayers.append(data)
        
        ownernumber = data['ownernumber']
        
        FireSignalRobust(playerdefeated, ownernumber=ownernumber)

        for unit in unitlist[ownernumber]:
            unit.OnPlayerDefeated()
        
        if self.spectateondefeat:
            # Move to spectators
            for player in UTIL_ListPlayersForOwnerNumber(ownernumber):
                player.SetOwnerNumber(0)
                player.ChangeTeam(TEAM_SPECTATOR)
                #player.SetObserverMode(OBS_MODE_ROAMING)
            
    def IsPlayerDefeated(self, data):
        """ Returns True if the specified gamelobby player entry is marked as defeated. """
        return data in self.defeatedplayers
        
    def GetPlayerID(self, player):
        steamIDForPlayer = engine.GetClientSteamID(player)
        if steamIDForPlayer:
            return steamIDForPlayer
        return player.GetPlayerName()
        
    def CalculateWinnersAndLosers(self, winnerteamordata):
        """ Returns two lists of game player entries with winners and losers. """
        winners = []
        losers = []
        
        if type(winnerteamordata) == int:
            for data in self.gameplayers:
                if data['team'] == winnerteamordata:
                    winners.append(data)
                else:
                    losers.append(data)
        else:
            for data in self.gameplayers:
                if data == winnerteamordata:
                    winners.append(data)
                else:
                    losers.append(data)
                    
        return winners, losers
        
    def GetRealPlayers(self):
        """ Gets all real players, that is without spectators. """
        players = UTIL_GetPlayers()
        realplayers = []
        for player in players:
            if player.GetTeamNumber() == TEAM_SPECTATOR:
                continue
            realplayers.append(player)
        return realplayers
        
    def GetObservers(self):
        """ Get list of observers. """
        players = UTIL_GetPlayers()
        observers = []
        for player in players:
            if player.GetTeamNumber() != TEAM_SPECTATOR:
                continue
            observers.append(player)
        return observers

    def CheckGameOver(self):
        """ If the game is over (self.gameover == True), change to
            the next map after the intermission time. """
        if self.gameover:   # someone else quit the game already
            # check to see if we should change levels now
            if self.intermissionendtime < gpGlobals.curtime:
                self.ChangeLevel()  # intermission is over
            return True
        return False
        
    def ChangeLevel(self):
        """ Called after intermission is over. """
        pass
        
    def ChangeToGamelobby(self):
        if self.offlinegame:
            # Simply go back to main menu for now
            player = UTIL_GetLocalPlayer()
            if player:
                engine.ClientCommand(player, 'disconnect\n')
                return
    
        lobbysteamid = matchmaking.GetActiveGameLobbySteamID()
        if lobbysteamid.IsValid():
            self.GameServerGameEnded()
            
    def GameServerGameEnded(self):
        """ New lobby system, where Steam hosts the lobbies
            Players should just disconnect at this point """
        if matchmaking.GetWarsGameServerState() in [matchmaking.k_EGameServer_InGame, matchmaking.k_EGameServer_InGameFreeStyle]:
            matchmaking.SetWarsGameServerState(matchmaking.k_EGameServer_GameEnded)
        
    def ClientCommand(self, player, args):
        """ Process hud commands """
        command = args[0]
        
        if command == 'player_ability':
            abiname = args[1]
            if len(args) > 3:
                unittype = args[2]
                predictedid = int(args[3])
            elif len(args) > 2:
                unittype = args[2]
                predictedid = -1
            else:
                unittype = None
                predictedid = -1

            DoAbility(player, abiname, unittype, predictedid)
            return True
        elif command == 'player_abilityalt':
            try:
                abiname = args[1]
            except IndexError:
                PrintWarning("player_abilityalt: not enough arguments\n") 
                return True
            info = GetAbilityInfo(abiname)
            if not info:
                return True # GetAbilityInfo will warn
            info.DoAbilityAlt(player)
            return True
        elif command == 'player_abilityclearmouse':
            try:
                id = int(args[1])
            except (IndexError, ValueError):
                PrintWarning("player_abilityclearmouse: not enough arguments or arguments are invalid\n") 
                return True
                
            abi = GetAbilityByID(id)
            if not abi:
                DevMsg(2, "player_abilityclearmouse: invalid ability id %d specified. Ability already cleared?\n" % (id)) 
                return True
                
            abi.ClearMouse()
        
            return True
        elif command == 'player_queue':
            unit = player.GetUnit(0)
            if not unit or unit.GetOwnerNumber() != player.GetOwnerNumber():
                return True
            unit.CancelAbility(int(args[1]))
            return True
        elif command == 'player_ungarrison_unit':
            building = player.GetUnit(0)
            if not building or building.GetOwnerNumber() != player.GetOwnerNumber():
                return True
            unit = UTIL_EntityByIndex(int(args[1]))
            building.UnGarrisonUnit(unit)
            return True
        elif command == 'player_sendres':
            # Send resources to another player
            try:
                type = args[1]
                amount = int(args[2])
                ownernumber = int(args[3])
            except IndexError:
                PrintWarning("player_sendres: not enough arguments\n") 
                return True
            except ValueError:
                PrintWarning("player_sendres: invalid arguments\n") 
                return True
            
            costs = [(type, amount)]
            if not HasEnoughResources(costs, player.GetOwnerNumber()):
                PrintWarning("player_sendres: not enough resources (%s, player %d)\n" % (str(costs), player.GetOwnerNumber()))
                return True
            TakeResources(player.GetOwnerNumber(), costs)
            GiveResources(ownernumber, costs) 
            
            return True
        elif command == 'player_forfeit':
            data = self.GetPlayerGameData(player=player)
            if data:
                self.PlayerDefeated(data)
            return True
        elif command == 'wars_ping':
            if len(args) < 4:
                return True
            filter = CRecipientFilter()
            filter.MakeReliable()
            for otherplayer in UTIL_GetPlayers():
                if not otherplayer or not otherplayer.IsConnected():
                    continue
                if relationships[(player.GetOwnerNumber(), otherplayer.GetOwnerNumber())] != D_LI:
                    continue
                filter.AddRecipient(otherplayer)
            pos = Vector(float(args[1]), float(args[2]), float(args[3]))
            c = dbplayers[player.GetOwnerNumber()].color
            color = (c[0], c[1], c[2])
            FirePing(pos, color, filter=filter)
            return True
        elif command == 'wars_close_msgbox':
            if len(args) < 2:
                PrintWarning('wars_close_msgbox: not enough arguments\n')
                return True
            entname = args[1]
            msgbox = entlist.FindEntityByName(None, entname)
            if msgbox:
                msgbox.PlayerClose()
            else:
                PrintWarning('wars_close_msgbox: Could not find message box entity %s\n' % (entname))
                
            return True
            
        return super().ClientCommand(player, args)
        
    def HasMapBoundary(self):
        return bool(entlist.FindEntityByClassname(None, 'func_map_boundary'))
        
    def FindEntityWithOwnerNumber(self, entity_name, ownernumber):
        """ Finds an entity with the specified class name and ownernumber.
        
            Returns None if there is no such entity.
        """
        current = entlist.FindEntityByClassname( None, entity_name )
        while current:
            if current.GetOwnerNumber() == ownernumber:
                return current
            current = entlist.FindEntityByClassname( current, entity_name )
        return None
    
    def FindPlayerSpawnSpot(self, player):
        """ Finds a start spot for the player.
        
            By default looks for info_player_wars with the matching ownernumber.
            If there is no such spot look for info_start_wars and then create
            a start spot.
        """
        if self.HasMapBoundary():
            # Find start spot
            startspot = self.FindEntityWithOwnerNumber('info_start_wars', player.GetOwnerNumber())
            if not startspot:
                # Get mappers placed spawn spot
                spawnspot = self.FindEntityWithOwnerNumber('info_player_wars', player.GetOwnerNumber())
                if spawnspot:
                    return spawnspot
                    
            return startspot
        else:
            # Get mappers placed spawn spot
            spawnspot = self.FindEntityWithOwnerNumber('info_player_wars', player.GetOwnerNumber())
            if spawnspot:
                return spawnspot
                
            # No spawnspot: try startspot and spawn a spawnspot dynamically
            startspot = self.FindEntityWithOwnerNumber('info_start_wars', player.GetOwnerNumber())
            if startspot:
                angles = QAngle(-115, 135, 0)
                forward = Vector()
                AngleVectors(angles, forward, None, None)
                
                spawnspot = CreateEntityByName('info_player_wars')
                spawnspot.SetOwnerNumber(player.GetOwnerNumber())
                spawnspot.SetAbsOrigin(startspot.GetAbsOrigin() + forward * 800.0)
                DispatchSpawn(spawnspot)
                spawnspot.Activate()
                return spawnspot
                
        return player.EntSelectSpawnPoint()
                       
    def GetPlayerSpawnSpot(self, player):
        """ Tries to pick a start point according to the ownernumber of the player """  
        # Because the ownernumber is required, we need to setup the player here.
        self.SetupPlayer(player)
        
        spawnspot = self.FindPlayerSpawnSpot(player)
        
        if spawnspot:
            #player.SetLocalOrigin(spawnspot.GetAbsOrigin() + Vector(0,0,1))
            player.SnapCameraTo(spawnspot.GetAbsOrigin() + Vector(0,0,1))
            player.SetAbsVelocity(vec3_origin)
            player.SetLocalAngles(QAngle(65, 135, 0))
            player.SnapEyeAngles(QAngle(65, 135, 0))
            #player.SetLocalAngles(spawnspot.GetLocalAngles())
            #player.SnapEyeAngles(spawnspot.GetLocalAngles())

        return spawnspot
        
    def SetupPlayer(self, player):
        # First try to apply gamelobby data
        # Otherwise use the first free owner number
        if player.GetOwnerNumber() == 0:
            if not self.ApplyDataToPlayer(player):
                if self.info.allowplayerjoiningame:
                    self.CreateDataForExistingPlayer(player, FindFirstFreeOwnerNumber())
                    self.ApplyDataToPlayer(player)
                else:
                    player.SetOwnerNumber(0)
                    player.ChangeTeam(TEAM_SPECTATOR)

    def InitRandomCrates(self):
        """ Initializes spawning crates randomly on the map, containing bonuses. """
        if not self.crates:
            return
        DevMsg(1, 'Random crates enabled\n')
        self.nextrandomcratetime = gpGlobals.curtime + random.uniform(90, 150)

    def ForceSpawnNextCrate(self):
        self.nextrandomcratetime = 0
        self.UpdateRandomCrate()
        
    def UpdateRandomCrate(self):
        if not self.crates:
            return
        if self.nextrandomcratetime < gpGlobals.curtime:
            pos = RandomNavAreaPosition()
            if pos != vec3_origin:
                crate = CreateUnitFancy('crate', pos)
                if crate:
                    crate.lifetime = 25.0
                    DevMsg(1, 'Spawned random crate\n')
                self.nextrandomcratetime = gpGlobals.curtime + random.uniform(sv_crate_minfreq.GetFloat(), sv_crate_maxfreq.GetFloat())
                self.cratesspawnretries = 0
            else:
                self.cratesspawnretries += 1
                self.nextrandomcratetime = gpGlobals.curtime + 1.0 # Try again soon, but not too soon
                
        if self.cratesspawnretries > 10:
            PrintWarning('Disabling random bonus crates due being unable to find a spot after 10 retries!\n')
            self.crates = False
            
    def GetMainResource(self):
        return 'requisition'
    
    # Data
    defaultstate = 'main'
    statehandlers = {}
    stateinfo = {}
    
    gametimeout = 0.0
    hasplayers = True
    activeplayers = 0
    
    spectateondefeat = True
    
    crates = False
    nextrandomcratetime = 0
    cratesspawnretries = 0
    
    #
    # Hud manipulation
    #
    def GetHudPanel(self, name):
        return self.hudrefs.get(name, None)
        
    def GetDefaultButtons(self):
        """ Returns the default buttons for the CefTopBar hud element. """
        return {
        
        }
        
    def SetupTopBar(self):
        topbar = self.GetHudPanel('CefTopBar')
        if not topbar:
            return
            
        defaultbuttons = self.GetDefaultButtons()
        for name, buttondef in defaultbuttons.items():
            topbar.InsertButton(
                name, 
                text=buttondef.get('text', ''),
                imagepath=buttondef.get('image', ''), 
                order=buttondef.get('order', 0), 
                handler=buttondef.get('handler', None),
                floatright=buttondef.get('floatright', False),
            )
            
    def ApplyGameSettings(self, kv):
        """ Main entry called by matchmaking, allowing the game server to setup
            a game based on the lobby data. 
        """
        self.state = 'waitingforplayers'
        self.gamestartpending = True
        
        self.offlinegame = kv.get('system', {}).get('network', 'live').lower() == 'offline'
        
        game = kv.get('game', None)
        if game:
            self.game_type = game.get('type', 'ffa')

            # Build players
            playerdata = game.get('player', None)
            if playerdata:
                if type(playerdata) != list:
                    self.BuildGamePlayerFromKV(playerdata)
                else:
                    for player in game.get('player', []):
                        self.BuildGamePlayerFromKV(player)
                    
            # Apply custom fields
            customfieldsdata = game.get('customfields', None)
            if customfieldsdata:
                for name, value in customfieldsdata.items():
                    try:
                        if not self.ApplyCustomField(name, value):
                            PrintWarning('ApplyGameSettings: unable to apply custom field %s with value %s\n' % (name, value))
                    except:
                        PrintWarning('ApplyGameSettings: An error occurred while trying to apply custom field %s with value %s:\n' % (name, value))
                        traceback.print_exc()
        
        # ApplyGameSettings should be called at level loading, so at this point the gamerules should precache the game
        self.Precache()
                
    def StartGame(self):
        for data in self.gameplayers:
            ownernumber = data['ownernumber']
            dbplayers[ownernumber] = PMGRPlayerInfo(faction=data['faction'], color=data['color']) 
                
        self.SetupRelationships()
        
        if self.spawnstartbuildings:
            # Create buildings at start spots
            self.activeplayers = 0
            for data in self.gameplayers:
                ownernumber = data['ownernumber']
                startspot = self.FindStartSpot(ownernumber)
                if startspot:
                    if not startspot.HasSpawnFlags(InfoStartWars.SF_NO_POPULATE):
                        # Let the new made gamerules populate the startpoint
                        try:
                            self.PopulateStartSpot(startspot, data['faction'], ownernumber, data['steamid'])
                        except:
                            traceback.print_exc()
                else:
                    PrintWarning('No start spot for owner number %d\n' % (ownernumber))
                self.activeplayers += 1
                
        # Apply player data to players already ingame
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if player is None or not player.IsConnected():
                continue     
            self.ApplyDataToPlayer(player)    
            player.Spawn()  # Respawn player
            
        # Crates
        self.InitRandomCrates()

        self.stats_collector.StartRecord()
        if self.stats_uploader:
            self.stats_uploader.RecordMatchStart(self.stats_collector.match_info)

        # Create CPU players (and immediately start their logic, so call after recording initial stats)
        for data in self.gameplayers:
            if not data['iscpu']:
                continue
            CreateAIForFaction(data['ownernumber'], cputype=data['cputype'], difficulty=data['difficulty'])

        self.gametime = gpGlobals.curtime
        FireSignalRobust(startgame, gamerules=self)
    
    def BuildPreferredPositions(self, team, availablepositions):
        # Which team groups would we like to avoid?
        teamhintstaken = set()
        for otherpd in self.gameplayers:
            otherteam = otherpd['team']
            if team != TEAM_UNASSIGNED and otherteam == team:
                continue
            otherowner = otherpd['ownernumber']
            startspot = self.FindStartSpot(otherowner)
            if not startspot:
                continue
            teamhintstaken.add(startspot.groupname if startspot.groupname else '_free_start_spot_%d' % (otherowner))
        
        # Walk through available positions
        preferredpositions = set()
        for ap in availablepositions:
            startspot = self.FindStartSpot(ap)
            if not startspot:
                continue
            groupname = startspot.groupname if startspot.groupname else '_free_start_spot_%d' % (ap)
            if groupname in teamhintstaken:
                continue
            preferredpositions.add(ap)
            
        if not preferredpositions:
            return availablepositions # preferred is empty, so just use all (no good setup available)
        #print('Calculated the following preferred positions: %s' % (str(preferredpositions)))
        return preferredpositions
    
    def BuildGamePlayerFromKV(self, kvplayerdata):
        playerdata = self.PlayerData()
        
        strsteamid = kvplayerdata.get('steamid', '')
        playerdata['steamid'] = None
        playerdata['faction'] = kvplayerdata.get('faction', 'rebels')
        playerdata['team'] = kvplayerdata.get('team', TEAM_UNASSIGNED)
        if strsteamid:
            try:
                playerdata['steamid'] = CSteamID(int(strsteamid))
            except ValueError:
                PrintWarning('BuildGamePlayerFromKV: found invalid steamid %s\n' % (strsteamid))
        
        try:
            playerdata['playername'] = kvplayerdata.get('playername', 'Unknown')
        except UnicodeDecodeError:
            playerdata['playername']  = 'Unknown'
            PrintWarning('BuildGamePlayerFromKV: could not read player name for user with steamid %s\n' % (strsteamid))
            traceback.print_exc()

        if 'availablepositions' in kvplayerdata:
            # Figure out which positions are available
            availablepositions = set(map(int, kvplayerdata['availablepositions'].split(',')))
            for otherpd in self.gameplayers:
                availablepositions.discard(otherpd.get('ownernumber', None))
                
            # Pick a random position from the available set
            playerdata['ownernumber'] = random.sample(self.BuildPreferredPositions(playerdata['team'], availablepositions), 1)[0]
        else:
            playerdata['ownernumber'] = kvplayerdata.get('ownernumber', 2)

        playerdata['iscpu'] = kvplayerdata.get('iscpu', False)
        playerdata['cputype'] = kvplayerdata.get('cputype', 'cpu_wars_default')
        playerdata['difficulty'] = kvplayerdata.get('difficulty', 'easy')
        playerdata['color'] = kvplayerdata.get('color', Color(0, 255, 0, 255))
        playerdata['state'] = 'loading' if not playerdata['iscpu'] else 'connected'
        playerdata['lastconnectedtime'] = 0
        playerdata['unconnected_last_minute_warning'] = None

        self.gameplayers.append(playerdata)
    
    #
    # Game Player management methods
    #
    class PlayerData(dict):
        def __hash__(self): 
            return id(self)

    def CreateDataForExistingPlayer(self, player, ownernumber):
        """ Creates a new entry on the fly for a new player.
            Mainly intended for usage in Sandbox (or when we don't know which players will participate yet)
            In other cases it is preferred to set it up beforehand, like in BuildGamePlayersFromGLData.
            
            Args:
                player (entity): Entity handle to player being added.
                ownernumber (int): Owner identification number in this game.
        """
        playerdata = self.PlayerData()
        self.gameplayers.append(playerdata)
                
        steamid = engine.GetClientSteamID(player)
        
        try:
            playerdata['playername'] = player.GetPlayerName()
        except UnicodeDecodeError:
            playerdata['playername']  = 'Unknown'
            traceback.print_exc()
        playerdata['steamid'] = steamid
        playerdata['ownernumber'] = ownernumber
        playerdata['faction'] = 'rebels'
        playerdata['team'] = TEAM_UNASSIGNED
        playerdata['iscpu'] = False
        playerdata['cputype'] = None
        playerdata['difficulty'] = None # Difficulty of CPU player, None for not set/default
        playerdata['color'] = Color(255, 255, 255)
            
    def GetPlayerGameData(self, player=None, steamid=None, name=None, gameplayers=None):
        """ Get the player data from the gameplayers list based on either the name/steamid or
            or the player entity.
    
            Kwargs:
               player (entity): The player entity handle. Overrides steamid and name.
               steamid (CSteamID): The player steam id to be matched
               name (str): The player name to be matched
               gameplayers (list): optional list of player data to be searched.
                                   By default the full gamerules player data list is used.
                                   This option can be used to only search a sub selection.
        """
        assert player or steamid or name, 'Must at least specify a player handle, steamid or player name'
        
        if gameplayers is None:
            gameplayers = self.gameplayers
        
        if player:
            steamid = engine.GetClientSteamID(player)
            # This code is probably not needed anymore (already handled), but the way source engine stores the player names
            # is in a 32 char buf and cuts of for unicode names, resulting in invalid utf-8 encoding.
            # In the C++ code, this just resulting in garbage for the last char, while Python throws an exception.
            try:
                name = player.GetPlayerName()
            except UnicodeDecodeError:
                name = 'Unknown'
                traceback.print_exc()
                
        for data in gameplayers:
            if data.get('steamid', None) is not None:
                if steamid and data['steamid'] == steamid:
                    return data
            elif data.get('playername', None):
                if name and data['playername'] == name:
                    return data
        return None

    def GetGamePlayersAndSpectators(self, game_players=None):
        """ Returns two lists of entity handles to valid game players and spectators.

            Kwargs:
                game_players (list|None):
        """
        ent_game_players = []
        ent_spectators = []
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if player is None or not player.IsConnected():
                continue

            data = self.GetPlayerGameData(player=player, gameplayers=game_players)
            if data:
                ent_game_players.append(player)
            else:
                ent_spectators.append(player)
        return ent_game_players, ent_spectators
        
    def GetGamePlayers(self, gameplayers=None):
        """ Returns the list of entity handles from valid game players. """
        players, spectators = self.GetGamePlayersAndSpectators(game_players=gameplayers)
        return players

    def GetSpectators(self):
        """ Returns the list of entity handles from valid game players. """
        players, spectators = self.GetGamePlayersAndSpectators()
        return spectators

    def ApplyDataToPlayer(self, player):
        """ Applies the player data to the player entity.

            Args:
                player (entity): Player for which to apply data.

            Returns: False if no data exists or when player is already defeated, otherwise True.
        """
        data = self.GetPlayerGameData(player=player)
        if not data or self.IsPlayerDefeated(data):
            return False
            
        player.SetOwnerNumber(data['ownernumber'])
            
        player.ChangeFaction(data['faction'])
        if data['team'] != 0:
            player.ChangeTeam(data['team'])
            
        # Reset Fog of War explored state, otherwise it might be showing whatever was it showing before
        # setting up the game (i.e. control points, because the player is neutral between level init and game init)
        filter = CRecipientFilter()
        filter.MakeReliable()
        filter.AddRecipient(player)
        ClientFOWResetExplored(filter=filter)

        return True
            
    def SetupRelationships(self):
        """ Setups default relationships between players when a game is started from the game lobby. """
        for data1 in self.gameplayers:
            if data1['team'] == 0:
                continue
            for data2 in self.gameplayers:
                if data1['team'] == data2['team']:
                    relationships[(data1['ownernumber'], data2['ownernumber'])] = D_LI

    def FindStartSpot(self, owner_number):
        """ Finds start spot for player.

            Args:
                owner_number (int): Owner for which to find a start spot

            Returns: spot entity
        """
        first_spot = entlist.FindEntityByClassname(None, "info_start_wars")
        current_spot = first_spot
        while True:
            if current_spot:
                # check if this is our spot
                if current_spot.GetOwnerNumber() == owner_number:
                    return current_spot.Get()
            current_spot = entlist.FindEntityByClassname(current_spot, "info_start_wars")
            if current_spot is first_spot:
                break   
        return None
    
    def PopulateStartSpot(self, startspot, faction, ownernumber, playerSteamID):
        """ Called by the gamelobby when a game is scheduled (Post Init map)

            Args:
                startspot (entity):
                faction (str): name of faction
                ownernumber (int): owner
                playerSteamID (CSteamID):
        """
        # Get faction info
        info = GetFactionInfo(faction)
        if not info:
            return  # Player is screwed
            
        info.PopulateStartSpot(self, startspot, ownernumber, playerSteamID)
        
    @classmethod    
    def GetCustomFields(cls):
        """ Returns a list of custom settings to be displayed in the game lobby settings. """
        fields = {
            'crates': {'name': '#Crates_Name', 'type': 'choices', 'values': ['no', 'yes'], 'default': 'no'},
        }
        return fields
        
    def ApplyCustomField(self, fieldname, value):
        """ Tries to apply a custom field value send by the game lobby.
            Returns True on success.

            Args:
                fieldname (str): name of field being applied
                value (str): value of field to be applied
        """
        if fieldname == 'crates':
            self.crates = value == 'yes'
            return True
        return False
        
    def ParseCustomFields(self, fields):
        """ Receives custom settings from game lobby to be appied in the game.

            Args:
                fields (list): fields to parse
        """
        for name, values in fields.items():
            self.ApplyCustomField(name, values['default'])
                
    gamestartpending = False
    spawnstartbuildings = True
    hudrefs = {}
    musicplaylist = None
    offlinegame = False
    gametime = 0

    forfeit_disconnected_too_long = True

    #: This is set during games for which match history is recorded. At the start of the match, it creates a new
    #: match entry at api.lambdawars.com. At end of of match, it commits the file data.
    #: match_uuid is synced to players, so they can confirm/verify they are in the match and request the result
    #: afterwards.
    match_uuid = None

    #: Type as set by the game lobby (ffa, 2vs2, etc)
    #: Mostly just here for the match history/recording
    game_type = ''
    
if isserver:
    @concommand('wars_crates_force_spawn', flags=FCVAR_CHEAT)
    def CCForceSpawnCrate(args):
        if not gamerules.crates:
            PrintWarning('Crates are not enabled (use wars_crates_toggle to force it)\n')
            return
        gamerules.ForceSpawnNextCrate()
        
    @concommand('wars_crates_toggle', flags=FCVAR_CHEAT)
    def CCToggleEnableCrates(args):
        gamerules.crates = not gamerules.crates
        gamerules.ForceSpawnNextCrate()
        print('Random crates are %s with min freq %f and max freq %f!' % ('Enabled' if gamerules.crates else 'Disabled', 
                sv_crate_minfreq.GetFloat(), sv_crate_maxfreq.GetFloat()) )
                
    # Temporary commands for spectators, until we make something nicer
    @concommand('spectator_freeroam', flags=0)
    def CCSpectatorFreeRoam(args):
        player = UTIL_GetCommandClient()
        if player.GetTeamNumber() != TEAM_SPECTATOR:
            return
        player.SetObserverMode(OBS_MODE_ROAMING)
        player.SetMoveType(MOVETYPE_OBSERVER)
            
    @concommand('spectator_strategicmode', flags=0)
    def CCSpectatorStrategicMode(args):
        player = UTIL_GetCommandClient()
        if player.GetTeamNumber() != TEAM_SPECTATOR:
            return
        player.SetObserverMode(OBS_MODE_ROAMING)
        player.SetMoveType(MOVETYPE_STRATEGIC) # SetObserverMode also changes move type, so apply after
