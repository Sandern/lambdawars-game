"""Abilities that override player mouse input.

Provides a base class for abilities that need complete control over mouse
input, intercepting all mouse button events and suppressing normal player
behavior.
"""
from .base import AbilityBase


class AbilityMouseOverride(AbilityBase):
    """Base class for abilities that override player mouse input completely.
    
    The ability intercepts all mouse button events and suppresses normal
    player behavior. The ability is completed when mouse focus is lost.
    """

    def Init(self):
        """ Initializes the ability. Adds this ability to the players 
            active ability list for mouse input."""
        self.player.AddActiveAbility(self)
        super().Init()
        
    def OnLeftMouseButtonPressed(self):
        """ Called when the player presses the left mouse button. 
            Returns True so the normal player mouse button behavior is suppressed."""
        return True 
    def OnLeftMouseButtonReleased(self):
        """ Called when the player releases the left mouse button. 
            Returns True so the normal player mouse button behavior is suppressed."""
        return True
    def OnRightMouseButtonPressed(self): 
        """ Called when the player presses the right mouse button. 
            Returns True so the normal player mouse button behavior is suppressed."""
        return True
    def OnRightMouseButtonReleased(self):
        """ Called when the player releases the right mouse button. 
            Returns True so the normal player mouse button behavior is suppressed."""
        return True
    
    def OnMouseLost(self):
        """ Called when the ability lost the players mouse focus.
            By default completes the ability. Override for other behavior."""
        if isserver:
            self.Completed() 