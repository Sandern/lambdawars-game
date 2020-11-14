""" Provides boilerplate ability to use an ability tied to an animation.
"""
from .instant import AbilityInstant
if isserver:
    from core.units import BehaviorGeneric

class AbilityAsAnimation(AbilityInstant):
    def DoAbility(self):
        self.SelectGroupUnits()
        for unit in self.units:
            unit.AbilityOrder(ability=self)

    def TryStartAnimation(self, unit):
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
        self.SetRecharge(unit)

        super().OnUnitOrderEnded(unit)

    def OnAllUnitsCleared(self):
        self.Completed()

    if isserver:
        behaviorgeneric_action = BehaviorGeneric.ActionAbilityWaitForAnimation

    # This ability object won't be created on the executing client
    serveronly = True
