from .base import AbilityBase


class AbilityMouseOverride(AbilityBase):
    """ Defines an ability that overrides the mouse of the player completely.
        The ability is completed on mouse lost."""

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