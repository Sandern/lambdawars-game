from core.abilities import AbilityTarget
from entities import MouseTraceData

if isserver:
    from unit_helper import GF_REQTARGETALIVE
    from core.units import BaseBehavior
    
    class ActionImpale(BaseBehavior.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into target range', 
                    self.order.target, self.outer.STRIDER_STOMP_RANGE-self.stompadddist, goalflags=GF_REQTARGETALIVE, pathcontext=self)
                    
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
                outer.DoAnimation(outer.ANIM_STOMPL)
                self.order.ability.SetRecharge(outer)
                self.order.ability.Completed()
                return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Waiting for impale act',
                    self.outer.animstate.specificmainactivity, self.behavior.ActionIdle)
            return self.ChangeTo(self.behavior.ActionIdle, 'Failed to impale')
            
        stompadddist = 64.0
                
class AbilityImpale(AbilityTarget):
    # Info
    name = 'impale'
    displayname = '#CombImpale_Name'
    description = '#CombImpale_Description'
    image_name = 'vgui/combine/abilities/impale'
    hidden = True
    rechargetime = 5.0
    
    supportsautocast = True
    defaultautocast = False
    autocastcheckonenemy = True
    checkautocastinenemyrange = 100.0
    
    def DoAbility(self):
        data = self.mousedata

        target = data.ent if (data.ent and not data.ent.IsWorld()) else None
        if not target or target == self.unit:
            if isserver: 
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
            return

        self.AbilityOrderUnits(self.unit, ability=self, target=target)
        
    @classmethod
    def CheckAutoCast(info, unit):
        if not info.CanDoAbility(None, unit=unit):
            return False
        if unit.senses.CountEnemiesInRange(112.0) >= 1:
            enemy = unit.senses.GetNearestEnemy()
            leftpressed = MouseTraceData()
            leftpressed.groundendpos = enemy.GetAbsOrigin()
            leftpressed.ent = enemy
            unit.DoAbility(info.name, [('leftpressed', leftpressed)], autocasted=True)
            return True
        return False
        
    if isserver:
        behaviorgeneric_action = ActionImpale
