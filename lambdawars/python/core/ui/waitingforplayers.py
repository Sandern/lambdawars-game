"""Waiting-for-players CEF panel showing lobby status, host banner, and MOTD.

Handles updating the HTML view with current lobby information while players
connect or load into the match.
"""
from cef import viewport, CefPanel
from gamerules import gamerules
from gameui import GetMainMenu
from steam import CSteamID, steamapicontext

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
        """Return a list of player status dicts compatible with the HTML UI."""
        statuses = []
        
        for gp in gameplayers:
            gp['steamid'] = str(gp['steamid'])
            statuses.append(gp)
            
        return statuses
        
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
    
        hostcontent = gamerules.GetTableInfoString('hostfile')
        if hostcontent:
            if hostcontent.startswith('http://'):
                self.Invoke("updateBanner", [hostcontent])
            else:
                self.Invoke("updateBannerFromContent", [hostcontent])
            
        motdcontent = gamerules.GetTableInfoString('motd')
        if motdcontent:
            if motdcontent.startswith('http://'):
                self.Invoke("updateMOTD", [motdcontent])
            else:
                self.Invoke("updateMOTDFromContent", [motdcontent])
                
        title = 'Waiting for Players...'
                
        mainmenu = GetMainMenu()
        if mainmenu and mainmenu.gamelobby and mainmenu.gamelobby.steamidlobby:
            gamelobby = mainmenu.gamelobby
            datamodel = gamelobby.datamodel
            title = datamodel.name
        
        self.Invoke("updatePanel", [round(self.wfptimeout - gpGlobals.curtime), title, self.BuildPlayerStatuses(gameplayers)])