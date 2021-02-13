from .base import AbilityBase

class AbilityInstant(AbilityBase):  
    """ Provides default start methods, but can be ignored by overriding Init
        Provides the default visuals for on the client (projecting a texture on the ground or showing a model) """
    def Init(self): 
        super().Init()
        
        requirements = self.GetRequirementsUnits(self.player)
        #if not requirements:
        #    self.PlayActivateSound()
        self.DoAbility()
  
    def DoAbility(self): 
        """ Start/do the ability directly when the player activates the ability.
            Override this with your implementation."""
        pass

