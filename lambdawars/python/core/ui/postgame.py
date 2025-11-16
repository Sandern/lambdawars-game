"""CEF post-game summary panel displayed after matches complete.

Shows winners/losers and exposes a disconnect button so players can leave
or review match results once the game has ended.
"""
from cef import viewport, CefPanel
from gamerules import gamerules

class CefPostGamePlayers(CefPanel):
    """Screen shown to all players after a game ends.
    
    Contains the disconnect button and displays the final winners/losers list.
    """
    name = 'postgame'
    htmlfile = 'ui/viewport/wars/postgame.html'
    classidentifier = 'viewport/hud/wars/PostGamePanel'
    cssfiles = CefPanel.cssfiles + ['wars/postgame.css']
    
    #def OnLoaded(self):
    #    super().OnLoaded()
        
    def ShowPanel(self, winners, losers, iswinner):
        """Display the post-game panel populated with winners/losers."""
        self.visible = True
        self.Invoke("updatePanel", [winners, losers, iswinner])
        
    def HidePanel(self):
        """Hide the post-game panel."""
        self.visible = False
