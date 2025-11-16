"""Abilities tied to unit animations.

Provides a base class for abilities that trigger unit animations
when executed. The ability waits for the animation to complete
before finishing, allowing for abilities that are purely visual
or tied to specific unit actions.
"""
from .instant import AbilityInstant
if isserver:
    from core.units import BehaviorGeneric

class AbilityAsAnimation(AbilityInstant):
    """Base class for abilities that trigger unit animations.
    
    The ability waits for the animation to complete before finishing.
    Units execute the animation and the ability completes when all
    units finish their animations.
    """
    def DoAbility(self):
        """Execute the animation ability.
        
        Selects group units and queues animation orders for each unit.
        The ability completes when all units finish their animations.
        """
        self.SelectGroupUnits()
        for unit in self.units:
            unit.AbilityOrder(ability=self)

    def TryStartAnimation(self, unit):
        """Attempt to start the animation for a unit.
        
        Validates ability requirements and energy, then plays the animation.
        
        Args:
            unit: Unit to play the animation on.
            
        Returns:
            bool: True if animation was started, False if requirements not met.
        """
        if not self.CanDoAbility(self.player, unit):
            return False
        if not self.TakeEnergy(unit):
            return False
        self.DoAnimation(unit)
        return True

    def DoAnimation(self, unit):
        """ Called when the unit is starting the action for this ability. Should play the animation. """
        pass

    def OnUnitOrderEnded(self, unit):
        """Called when a unit finishes its animation order.
        
        Applies recharge time to the unit and calls the parent handler.
        
        Args:
            unit: Unit that finished its order.
        """
        self.SetRecharge(unit)

        super().OnUnitOrderEnded(unit)

    def OnAllUnitsCleared(self):
        """Called when all units have finished their animations.
        
        Completes the ability once all units are done.
        """
        self.Completed()

    if isserver:
        behaviorgeneric_action = BehaviorGeneric.ActionAbilityWaitForAnimation

    # This ability object won't be created on the executing client
    serveronly = True
