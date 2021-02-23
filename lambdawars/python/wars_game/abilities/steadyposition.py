""" Steady position ability. Puts the unit in a crouch position on the spot. """
from core.abilities import AbilityInstant
from fields import FloatField

if isserver:
    from core.units import BehaviorGeneric, BaseAction

class AbilitySteadyPosition(AbilityInstant):
    name = 'steadyposition'
    displayname = '#CombSteadyPosition_Name'
    description = '#CombSteadyPosition_Description'
    image_name = 'vgui/combine/abilities/combine_sniper_steady_position'
    hidden = True
    rechargetime = 1.0
    steadytime = FloatField(value=4.67)
    defaultautocast = True
    serveronly = True
    #  sai_hint = AbilityInstant.sai_hint | set(['sai_deploy'])
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()
            alwaysqueue = True if self.autocasted else False
            idx = 0 if alwaysqueue else None
            for unit in self.units:
                if unit.in_cover or unit.insteadyposition:
                    continue
                # From the attack code we stack the action on top of the current attack action, so it does not get
                # ended.
                if not self.kwarguments.get('direct_from_attack', False):
                    unit.AbilityOrder(position=unit.GetAbsOrigin(),
                                      ability=self, alwaysqueue=alwaysqueue, idx=idx)
                self.SetNotInterruptible()

        class ActionInSteadyPosition(BehaviorGeneric.ActionCrouchHoldSpot):
            def Init(self, autocasted=False):
                super().Init()

                self.autocasted = autocasted

            def OnStart(self):
                self.outer.insteadyposition = True
                return super().OnStart()

            def OnEnd(self):
                self.outer.insteadyposition = False
                super().OnEnd()

            # Don't break cover when targeting an enemy
            def OnNewOrder(self, order):
                if order.type == order.ORDER_ENEMY:
                    return self.SuspendFor(self.behavior.ActionHideSpotAttack,
                                           'Attacking enemy on order from cover/hold spot', order.target)

            autocasted = False
            last_had_valid_enemy_time = 0

        class ActionDoSteadyPosition(BaseAction):
            def Init(self, ability, order=None):
                super().Init()

                self.ability = ability
                self.order = order

            # TODO: Don't interrupt steadying position when a new enemy is targeted while the unit is steadying for the previous attack
            # (e.g. a manhack flies in while the unit is steadying to shoot a more distant target)

            def Update(self):
                outer = self.outer

                abi = self.ability
                outer.crouching = True
                outer.aimoving = True
                trans = self.SuspendFor(self.behavior.ActionChanneling, 'Steadying position', abi.steadytime,
                                        channel_animation=self.channel_animation)
                self.steadyaction = self.nextaction
                return trans

            def OnEnd(self):
                super().OnEnd()

                outer = self.outer
                outer.aimoving = False
                if not self.steadiedposition:
                    outer.crouching = False
                    self.ability.Cancel()

            def OnResume(self):
                outer = self.outer
                abi = self.ability
                order = self.order
                steadyaction = self.steadyaction
                if steadyaction:
                    self.steadyaction = None
                    if order:
                        order.Remove(dispatchevent=False)

                    if steadyaction.channelsuccess:
                        self.steadiedposition = True
                        abi.SetRecharge(outer)
                        abi.Completed()
                        return self.ChangeTo(abi.ActionInSteadyPosition, 'In steady position', autocasted=abi.autocasted)

                return super().OnResume()

            steadyaction = None
            steadiedposition = False
            channel_animation = None
            ability = None
            order = None
            #changetoidleonlostorder = False

        class ActionSteadyPosition(BehaviorGeneric.ActionAbility):
            def OnStart(self):
                return self.SuspendFor(self.order.ability.ActionDoSteadyPosition, 'Do steady position',
                                       self.order.ability, self.order)




        behaviorgeneric_action = ActionSteadyPosition

class AbilitySteadyCharPosition(AbilitySteadyPosition):
    name = 'steadyposition_char'
    displayname = '#CombSteadyPosition_Name'
    description = '#CombSteadyPosition_Description'
    image_name = 'vgui/combine/abilities/combine_sniper_steady_position'
    rechargetime = 1.0
    steadytime = FloatField(value=1.0)

class RebelAbilitySteadyPosition(AbilitySteadyPosition):
    name = 'rebel_steadyposition'
    displayname = '#CombSteadyPosition_Name'
    description = '#CombSteadyPosition_Description'
    image_name = 'vgui/combine/abilities/combine_sniper_steady_position'
    rechargetime = 1.99
    steadytime = FloatField(value=2.24)

class RebelAbilitySteadyCharPosition(AbilitySteadyPosition):
    name = 'rebel_steadyposition_char'
    displayname = '#RebSteadyPosition_Name'
    description = '#RebSteadyPosition_Description'
    image_name = 'vgui/rebels/abilities/rebel_veteran_steady_position'
    rechargetime = 1.0
    steadytime = FloatField(value=1.0)

