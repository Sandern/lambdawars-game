from core.abilities.instant import AbilityInstant
if isserver:
    from core.units.behavior_generic import BaseAction, BehaviorGeneric


class AbilitySwitchWeapon(AbilityInstant):
    """ Switches all units in the selection with this ability
        to the specified weapon. """
    def DoAbility(self):
        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()

        for unit in self.units:
            unit.AbilityOrder(position=unit.GetAbsOrigin(),
                              target=unit,
                              ability=self)

    def OnAllUnitsCleared(self):
        self.Completed()

    def SwitchWeapon(self, unit):
        """ Switches the weapon and completes the ability. """
        self.SetRecharge(unit)
        unit.Weapon_Switch(unit.Weapon_OwnsThisType(self.weapon))
        
    #: The weapon the unit(s) will switch to. This is the entity class name of the weapon.
    #: The unit must have the weapon already, otherwise the switching will fail.
    weapon = None

    #: Time it takes to switch weapon
    switch_weapon_time = 0
    #: Animation played during switching weapon
    switch_weapon_animation = None
    
    # This ability object won't be created on the executing client
    serveronly = True

    if isserver:
        class ActionDoSwitchWeapon(BaseAction):
            switch_weapon_action = None

            def Init(self, ability, order=None):
                super().Init()

                self.ability = ability
                self.order = order

            def Update(self):
                outer = self.outer

                abi = self.ability
                outer.aimoving = True
                trans = self.SuspendFor(self.behavior.ActionChanneling, 'Switch weapon', abi.switch_weapon_time,
                                        channel_animation=abi.switch_weapon_animation)
                self.switch_weapon_action = self.nextaction
                return trans

            def OnEnd(self):
                super().OnEnd()

                self.outer.aimoving = False

            def OnResume(self):
                outer = self.outer
                abi = self.ability
                order = self.order
                switch_weapon_action = self.switch_weapon_action
                if switch_weapon_action:
                    self.switch_weapon_action = None
                    if order:
                        order.Remove(dispatchevent=False)

                    if switch_weapon_action.channelsuccess:
                        abi.SwitchWeapon(outer)
                        return self.ChangeTo(self.behavior.ActionIdle, 'Done switching weapon')

                return super().OnResume()

        class ActionSwitchWeaponAbility(BehaviorGeneric.ActionAbility):
            def OnStart(self):
                return self.SuspendFor(self.order.ability.ActionDoSwitchWeapon, 'Switching weapon',
                                       self.order.ability, self.order)

        behaviorgeneric_action = ActionSwitchWeaponAbility
