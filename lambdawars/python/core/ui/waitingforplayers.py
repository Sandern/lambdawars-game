"""Waiting-for-players CEF panel showing lobby status, host banner, and MOTD.

Handles updating the HTML view with current lobby information while players
connect or load into the match.
"""
from cef import viewport, CefPanel
from gamerules import gamerules
from gameui import GetMainMenu
from playermgr import dbplayers
from steam import CSteamID, steamapicontext
import srcmgr

class CefWaitingForPlayers(CefPanel):
    """Displays lobby information while waiting for players to connect.

    Updates banner/MOTD content, resolves player names via Steam, and feeds
    timeout plus player status data into the HTML UI until the match starts.
    """
    name = 'waitingforplayers'
    htmlfile = 'ui/viewport/wars/waitingforplayers.html'
    classidentifier = 'viewport/hud/wars/WaitingForPlayersPanel'
    cssfiles = CefPanel.cssfiles + ['wars/waitingforplayers.css']
    wfptimeout = 0
    
    def OnLoaded(self):
        """Placeholder hook; panel shows once an update arrives."""
        super().OnLoaded()
        
    def BuildPlayerStatuses(self, gameplayers):
        """Return a list of player status dicts compatible with the HTML UI.

        Adds the color of each player and whether it's the local player.
        """
        statuses = []
        steamuser = steamapicontext.SteamUser()
        localsteamid = steamuser.GetSteamID() if steamuser else None

        for gp in gameplayers:
            steamid = gp.get('steamid', None)
            gp['isyou'] = bool(steamid and localsteamid and steamid == localsteamid)
            gp['steamid'] = str(steamid) if steamid else ''
            color = dbplayers[gp.get('ownernumber', 0)].color
            gp['color'] = 'rgb(%d, %d, %d)' % (color.r(), color.g(), color.b()) if hasattr(color, 'r') else ''
            statuses.append(gp)

        return statuses

    def BuildGameInfo(self):
        """Return the game mode and map shown below the lobby name."""
        info = getattr(gamerules, 'info', None)
        return {
            'mode' : info.displayname if info else '',
            'map' : srcmgr.levelname,
        }
        
    def UpdatePanel(self, wfptimeout, gameplayers):
        """Refresh banner/MOTD/player list information in the HTML panel.
        
        Args:
            wfptimeout (float): Server timeout value used to compute remaining time.
            gameplayers (list): Player dictionaries from the gamerules lobby.
        """
        self.wfptimeout = wfptimeout
        
        # Fill in playername from steamid if no playername is present
        steamfriends = steamapicontext.SteamFriends()
        if steamfriends:
            for gp in gameplayers:
                steamid = gp.get('steamid', None)
                if steamid and 'playername' not in gp:
                    gp['playername'] = steamfriends.GetFriendPersonaName(steamid)
    
            
        motdcontent = gamerules.GetTableInfoString('motd')
        if motdcontent:
            if motdcontent.startswith('http://'):
                self.Invoke("updateMOTD", [motdcontent])
            else:
                self.Invoke("updateMOTDFromContent", [motdcontent])
                
        # The lobby name, the panel shows "Waiting for players" without a lobby
        title = ''

        mainmenu = GetMainMenu()
        if mainmenu and mainmenu.gamelobby and mainmenu.gamelobby.steamidlobby:
            gamelobby = mainmenu.gamelobby
            datamodel = gamelobby.datamodel
            title = datamodel.name

        self.Invoke("updatePanel", [round(self.wfptimeout - gpGlobals.curtime), title,
                                    self.BuildPlayerStatuses(gameplayers), self.BuildGameInfo()])