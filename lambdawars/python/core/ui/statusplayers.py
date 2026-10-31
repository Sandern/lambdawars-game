"""CEF panel listing players, lobby info, and connection status for matches.

Aggregates data from the main menu lobby, Steam friends, and in-game
resources to display current player states and statistics.
"""
from srcbuiltins import Color
from cef import viewport, CefPanel
from gameinterface import PlayerInfo, concommand, engine
from playermgr import dbplayers
from entities import PlayerResource
from steam import CSteamID, steamapicontext, k_EAccountTypeIndividual

from gameui import GetMainMenu

class CefStatusPlayers(CefPanel):
    """Displays player and lobby status information using a CEF UI.

    Collects lobby slot data, steam persona names, and in-game stats, then
    forwards the combined information to the HTML UI for rendering.
    """
    htmlfile = 'ui/viewport/wars/playerstatuspanel.html'
    classidentifier = 'viewport/hud/wars/PlayerStatusPanel'
    cssfiles = CefPanel.cssfiles + ['wars/playerstatuspanel.css']
    
    def SetupFunctions(self):
        """Placeholder for future CEF function bindings (none yet)."""
        super().SetupFunctions()
        
    def OnLoaded(self):
        """Populate player data as soon as the HTML UI is ready."""
        super().OnLoaded()

        self.UpdateAllPlayers()
        self.RegisterTickSignal(0.5)
        
    def OnRemove(self):
        super().OnRemove()
        
    def UpdateAllPlayers(self):
        """Collect lobby/ingame player data and send it to the HTML UI."""
        gameplayers, players = self.CollectPlayers()
        self.Invoke("updatePlayers", [gameplayers, players])
        
    def CollectPlayers(self):
        """Gather lobby slots and connected player data for display."""
        gameplayers = []
        players = []
        
        steamfriends = steamapicontext.SteamFriends()
        
        mainmenu = GetMainMenu()
        if mainmenu and mainmenu.gamelobby and mainmenu.gamelobby.steamidlobby:
            gamelobby = mainmenu.gamelobby
            datamodel = gamelobby.datamodel
            
            for slot in datamodel.slots:
                playerdata = slot.get('player', None)
                if not playerdata:
                    continue
                steamid = CSteamID(int(playerdata['steamid'])) if playerdata['steamid'] else None
                color = gamelobby.settingsinfo.allcolors.get(playerdata['color'], {'color' : Color(0, 255, 0, 255)})['color']
                iscpu = slot['iscpu']
                gameplayers.append({
                    'index' : slot['slotid'],
                    'name' : steamfriends.GetFriendPersonaName(steamid) if steamid else playerdata['name'],
                    'steamid' : str(steamid) if steamid else None,
                    'color' : 'rgb(%d, %d, %d)' % (color.r(), color.g(), color.b()),
                    'ping' : 0,
                    'team' : slot['team'],
                    'state' : 'disconnected' if not iscpu else 'connected',
                })
                
        # Add pings and colors
        if PlayerResource():
            for index in range(1, gpGlobals.maxClients+1):
                info = PlayerInfo()
                if not engine.GetPlayerInfo(index, info):
                    continue
                steamid = CSteamID(info.friendsID, 1, steamapicontext.SteamUtils().GetConnectedUniverse(), k_EAccountTypeIndividual)
                
                owner = PlayerResource().GetOwnerNumber(index)
                color = dbplayers[owner].color
                ping = PlayerResource().GetPing(index)
                
                foundplayer = False
                for player in gameplayers:
                    if player['steamid'] == str(steamid):
                        player['color'] = 'rgb(%d, %d, %d)' % (color.r(), color.g(), color.b())
                        player['ping'] = ping
                        player['state'] = 'connected'
                        foundplayer = True
                        break
                        
                if not foundplayer:
                    players.append({
                        'index' : index,
                        'name' : info.name,
                        'steamid' : str(steamid),
                        'color' : 'rgb(%d, %d, %d)' % (color.r(), color.g(), color.b()),
                        'ping' : ping,
                        'team' : PlayerResource().GetTeam(index),
                        'state' : 'connected',
                    })
        
        return gameplayers, players
                
    def OnTick(self):
        """Refresh the player list on a timer while the panel is visible."""
        if not self.visible:
            return
        self.UpdateAllPlayers()
        
statusplayers = CefStatusPlayers(viewport, 'statusplayerspanel')
        
@concommand('status_players_toggle', '', 0)
def show_statusplayers_toggle(args):
    statusplayers.visible = not statusplayers.visible
    if statusplayers.visible:
        statusplayers.OnTick()
        
@concommand('+status_players', '', 0)
def show_statusplayers_down(args):
    statusplayers.visible = True
    statusplayers.OnTick()
    
@concommand('-status_players', '', 0)
def show_statusplayers_up(args):
    statusplayers.visible = False