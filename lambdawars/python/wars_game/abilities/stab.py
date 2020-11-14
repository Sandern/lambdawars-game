from core.abilities import AbilityTarget
from entities import MouseTraceData

if isserver:
    from unit_helper import GF_REQTARGETALIVE as I_DONTKNOWWHATTHISDOES
    from core.units import BaseBehavior


    class ActionStab(BaseBehavior.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into target range',
                                   self.order.target, self.outer.SCOUT_STAB_RANGE - self.stabadddist,
                                   goalflags=I_DONTKNOWWHATTHISDOES, pathcontext=self)

        def OnEnd(self):
            self.order.ability.Cancel()
            if self.outer.curorder == self.order:
                self.outer.ClearOrder(dispatchevent=False)

        def OnResume(self):
            target = self.order.target
            outer = self.outer
            path = outer.navigator.path
            if target and path.pathcontext == self and path.success:
                outer.stomptarget = target
                outer.DoAnimation(outer.ANIM_THROWGRENADE)
                self.order.ability.SetRecharge(outer)
                self.order.ability.Completed()
                return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Waiting for stab act',
                                    self.outer.animstate.specificmainactivity, self.behavior.ActionIdle)
            return self.ChangeTo(self.behavior.ActionIdle, 'Failed to stab')

        stabadddist = 0.0

class AbilityStab(AbilityTarget):
    # Info
    name = 'stab'
    displayname = "#ScoutBackstab_Name"
    description = '#ScoutBackstab_Description'
    image_name = 'vgui/combine/abilities/impale'
    cloakallowed = True
    hidden = False
    rechargetime = 15.0
    maxrange = 55.0
    damage = 400
    attackspeed = 2.0
    
    def DoAbility(self):
        data = self.mousedata

        target = data.ent if (data.ent and not data.ent.IsWorld()) else None
        if not target or target == self.unit:
            if isserver: 
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
            return

        self.AbilityOrderUnits(self.unit, ability=self, target=target)

    if isserver:
        behaviorgeneric_action = ActionStab