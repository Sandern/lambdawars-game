from core.abilities.instant import AbilityInstant
if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from core.units.behavior_generic import BaseAction, BehaviorGeneric


class AbilityTransformUnit(AbilityInstant):
    """ Transforms an unit into another unit type 
        Note: Does not change the instance data of the unit.
              It mainly changes what is displayed in the hud.
    """
    interruptible = False

    def OnAllUnitsCleared(self):
        self.Completed()

    def DoAbility(self):
        self.SelectGroupUnits()

        if isserver:
            count = self.TakeResources(count=len(self.units))
            if not count:
                self.Cancel()
                return
        else:
            # TODO: compute units taking the order
            count = len(self.units)

        for unit in self.units[0:count]:
            unit.AbilityOrder(position=unit.GetAbsOrigin(),
                              target=unit,
                              ability=self)

    if isserver:
        def Transform(self, unit):
            self.PreTransform(unit)
            unit.SetUnitType(self.transform_type)
            self.PostTransform(unit)

        def PreTransform(self, unit):
            pass

        def ReplaceWeapons(self, unit):
            unit.RemoveAllWeapons()
            for weapon in unit.unitinfo.weapons:
                w = CreateEntityByName(weapon)
                if not w:
                    continue
                DispatchSpawn(w)
                w.Activate()
                unit.Weapon_Equip(w)

        def PostTransform(self, unit):
            if self.replaceweapons:
                self.ReplaceWeapons(unit)
        
        #: Type the unit should transform into
        transform_type = None
        #: Time it takes to transform into new unit
        transform_time = 0
        #: Animation played during transformation time
        transform_unit_animation = None
        
        #: If True, the weapon of the unit is replaced by the weapons of the new unit type
        replaceweapons = False

        class ActionDoTransformUnit(BaseAction):
            transform_unit_action = None

            def Init(self, ability, order=None):
                super().Init()

                self.ability = ability
                self.order = order

            def Update(self):
                outer = self.outer

                abi = self.ability
                outer.aimoving = True
                trans = self.SuspendFor(self.behavior.ActionChanneling, 'Transform unit', abi.transform_time,
                                        channel_animation=abi.transform_unit_animation)
                self.transform_unit_action = self.nextaction
                return trans

            def OnEnd(self):
                super().OnEnd()

                self.outer.aimoving = False

            def OnResume(self):
                outer = self.outer
                abi = self.ability
                order = self.order
                transform_unit_action = self.transform_unit_action
                if transform_unit_action:
                    self.transform_unit_action = None
                    if order:
                        order.Remove(dispatchevent=False)

                    if transform_unit_action.channelsuccess:
                        abi.Transform(outer)
                        return self.ChangeTo(self.behavior.ActionIdle, 'Done transforming unit')

                return super().OnResume()

        class ActionTransformUnitAbility(BehaviorGeneric.ActionAbility):
            def OnStart(self):
                return self.SuspendFor(self.order.ability.ActionDoTransformUnit, 'Transforming unit',
                                       self.order.ability, self.order)

            changetoidleonlostorder = False

        behaviorgeneric_action = ActionTransformUnitAbility
