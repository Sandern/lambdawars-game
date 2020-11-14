from core.abilities import AbilityInstant

if isserver:
    from core.units import BehaviorGeneric

class AbilityPlayAnimation(AbilityInstant):
    """ Play an activity, to which some action may be linked. """
    animation_event = None

    def DoAbility(self):
        """ Default implementation. Can override and then just call PlayAnimation with the selected units. """
        self.SelectGroupUnits()
        units = self.TakeEnergy(self.units)
        for unit in units:
            unit.AbilityOrder(ability=self)
        self.SetRecharge(units)
        self.Completed()

    def PlayAnimation(self, units):
        for unit in units:
            unit.AbilityOrder(ability=self)

    if isserver:
        behaviorgeneric_action = BehaviorGeneric.ActionAbilityPlayActivity

    # This ability object won't be created on the executing client
    serveronly = True