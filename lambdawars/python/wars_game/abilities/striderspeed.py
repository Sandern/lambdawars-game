from core.abilities import AbilityInstant
from fields import FloatField
if isserver:
    from core.units import BaseBehavior

if isserver:
    class ActionCrouching(BaseBehavior.ActionAbility):
        def Init(self, ability, order=None):
            super().Init()

            self.ability = ability
            self.order = order

        def Update(self):
            outer = self.outer
            units = self.outer.units

            abi = self.ability
            outer.aimoving = True
            # if
            trans = self.SuspendFor(self.behavior.ActionWaitForActivity, 'Playing Crouch Animation', abi.transitiontime, self.order.ability, self.order)
            return trans

        def OnEnd(self):
            super().OnEnd()
            self.order.ability.Cancel()
            if self.outer.curorder == self.order:
                self.outer.ClearOrder(dispatchevent=False)
            self.outer.aimoving = False

class AbilityStriderSpeed(AbilityInstant):
    name = 'striderspeed'
    displayname = '#CombStriderSpeed_Name'
    description = '#CombStriderSpeed_Description'
    image_name = 'vgui/combine/abilities/combine_strider_crouch'
    rechargetime = 3.0
    #energy = 10
    serveronly = True # Do not instantiate on the client
    transitiontime = 4.0
    transitionspeed = 1.4


    def DoAbility(self):
        self.SelectGroupUnits()

        enablespeed = False
        for unit in self.units:
            if not unit.speedenabled:
                enablespeed = True
                break

        units = [unit for unit in self.units if unit.speedenabled != enablespeed]

        if not enablespeed:
            units = self.TakeEnergy(units)

        for unit in units:
            if enablespeed:
                unit.DoAnimation(unit.ANIM_CROUCH, data=round(self.transitionspeed*255))
                self.AbilityOrderUnits(unit, ability=self)
                unit.EnableSpeed()
            else:
                unit.DisableSpeed()
                unit.DoAnimation(unit.ANIM_STAND, data=round(self.transitionspeed*255))
                self.AbilityOrderUnits(unit, ability=self)

            self.SetRecharge(units)
            self.Completed()

    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbility



