from cef import viewport, CefPanel
from gamerules import gamerules
from gameui import GetMainMenu
from steam import CSteamID, steamapicontext

class CefWaitingForPlayers(CefPanel):
    name = 'waitingforplayers'
    htmlfile = 'ui/viewport/wars/waitingforplayers.html'
    classidentifier = 'viewport/hud/wars/WaitingForPlayersPanel'
    cssfiles = CefPanel.cssfiles + ['wars/waitingforplayers.css']
    wfptimeout = 0
    
    def OnLoaded(self):
        super().OnLoaded()
        
    def BuildPlayerStatuses(self, gameplayers):
        statuses = []
        
        for gp in gameplayers:
            gp['steamid'] = str(gp['steamid'])
            statuses.append(gp)
            
        return statuses
        
    def UpdatePanel(self, wfptimeout, gameplayers):
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
                
        title = 'Waiting for Players...'
                
        mainmenu = GetMainMenu()
        if mainmenu and mainmenu.gamelobby and mainmenu.gamelobby.steamidlobby:
            gamelobby = mainmenu.gamelobby
            datamodel = gamelobby.datamodel
            title = datamodel.name
        
        self.Invoke("updatePanel", [round(self.wfptimeout - gpGlobals.curtime), title, self.BuildPlayerStatuses(gameplayers)])