from cef import viewport, CefPanel
from gamerules import gamerules

class CefPostGamePlayers(CefPanel):
    ''' Screen shown to all players after game ended. 
    
        Contains disconnect button to leave game.
    '''
    name = 'postgame'
    htmlfile = 'ui/viewport/wars/postgame.html'
    classidentifier = 'viewport/hud/wars/PostGamePanel'
    cssfiles = CefPanel.cssfiles + ['wars/postgame.css']
    
    #def OnLoaded(self):
    #    super().OnLoaded()
        
    def ShowPanel(self, winners, losers, iswinner):
        self.visible = True
        self.Invoke("updatePanel", [winners, losers, iswinner])
        
    def HidePanel(self):
        self.visible = False
