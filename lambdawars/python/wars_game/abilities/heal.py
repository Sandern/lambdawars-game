from core.abilities import AbilityTargetGroup, AbilityBase
from entities import MouseTraceData, D_LI
from fields import FloatField
import random

if isserver:
    from core.units import BehaviorGeneric
    
    class ActionHeal(BehaviorGeneric.ActionAbility):
        def Update(self):
            outer = self.outer
            
            order = self.order
            target = order.target
            
            needs_heal, reason = NeedsHealing(outer, target)
            if not needs_heal:
                order.Remove(dispatchevent=False)
                return self.ChangeToIdle('No target')
                
            # Move to target
            path = outer.navigator.path
            if path.pathcontext != self or not path.success:
                return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to heal target", target, 
                        tolerance=96.0, pathcontext=self)
                
            # Facing (this will usually be the case already when moved to the target)?
            if not outer.FInAimCone(target, self.facingminimum):
                return self.SuspendFor(self.behavior.ActionFaceTarget, 'Not facing target', target, self.facingminimum)

            outer.healtarget = target
            self.healedtarget = True
            outer.DoAnimation(outer.ANIM_HEAL, data=round(self.order.ability.heal_anim_speed * 255))
            return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Playing heal animation',
                                   self.outer.animstate.specificmainactivity)
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.healedtarget:
                self.order.ability.Cancel()

        def OnResume(self):
            if self.healedtarget:
                self.order.ability.SetRecharge(self.outer)
                self.order.ability.Completed()
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        healedtarget = False
        facingminimum = 0.7
        
def NeedsHealing(unit, target):
    if not target or not target.IsAlive() or not target.IsUnit() or target.isbuilding or unit == target:
        return False, '#Ability_InvalidTarget'
        
    # Only heal allies
    if unit.IRelationType(target) != D_LI:
        return False, '#Ability_InvalidTarget'
        
    # Must have less health than max
    if target.health >= target.maxhealth:
        return False, '#RebHeal_TargetFullHP'
        
    # Can't heal mechanic units (e.g. manhacks)
    if 'mechanic' in target.attributes:
        return False, '#RebHeal_TargetMechanic'
    # Can't heal synth units (e.g. Striders, Hunter)
    if 'synth' in target.attributes:
        return False, '#Ability_InvalidTarget'
    if 'metal' in target.attributes:
        return False, '#RebHeal_TargetMechanic'
        
    return True, None
    
class AbilityHeal(AbilityTargetGroup):
    # Info
    name = "heal"
    rechargetime = 2.0
    energy = 10.0
    displayname = "#RebHeal_Name"
    description = "#RebHeal_Description"
    image_name = 'vgui/rebels/abilities/heal'
    heal_anim_speed = FloatField(value=2.0)
    
    defaultautocast = True
    autocastcheckonidle = True
    
    # Ability
    if isserver:
        def DoAbility(self):
            target = self.mousedata.ent
            units = list(filter(lambda unit: unit != target, self.units))
            self.DoHeal(units[0] if units else self.unit)

        def DoHeal(self, selected_unit):
            data = self.mousedata

            if self.ischeat:
                self.Completed()
                return

            pos = data.endpos
            target = data.ent

            if not selected_unit:
                self.Cancel()
                return

            needsheal, reason = NeedsHealing(selected_unit, target)
            if not needsheal:
                self.Cancel(cancelmsg=reason)
                return

            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            self.AbilityOrderUnits(
                selected_unit,
                position=pos,
                target=target,
                ability=self
            )
            self.SetNotInterruptible()

        behaviorgeneric_action = ActionHeal
        
    @classmethod
    def SetupOnUnit(info, unit):
        super(AbilityHeal, info).SetupOnUnit(unit)
        
        unit.abiheal_nextchecktime = gpGlobals.curtime + 0.5
        
    @classmethod
    def OnUnitThink(info, unit):
        if not unit.AllowAutoCast() or not unit.abilitycheckautocast[info.uid]:
            return
            
        info.CheckAutoCast(unit)
        
    @classmethod
    def CheckAutoCast(info, unit):
        if unit.abiheal_nextchecktime > gpGlobals.curtime:
            return
            
        unit.abiheal_nextchecktime = gpGlobals.curtime + 0.5
            
        others = list(filter(bool, unit.senses.GetOthers()))
        #if len(others) > 10:
        #    units = random.sample(others, 10)
        #else:
        #    units = others
        units = others
            
        bestunit = None
        highesthplost = 0
        
        for other in units:
            needsheal, reason = NeedsHealing(unit, other)
            if not needsheal:
                continue
                
            hplost = other.maxhealth - other.health
            if not bestunit or hplost > highesthplost:
                bestunit = other
                highesthplost = hplost
            
        if bestunit and highesthplost > 0:
            leftpressed = MouseTraceData()
            leftpressed.groundendpos = bestunit.GetAbsOrigin()
            leftpressed.ent = bestunit
            unit.DoAbility(info.name, [('leftpressed', leftpressed)], autocasted=True)
            return True
            
        return False

    #allowmultipleability = True

class MissionAbilityHeal(AbilityHeal):
    name = "mission_heal"
    rechargetime = 2.0
    energy = 10.0

class AbilityHealChar(AbilityHeal):
    name = 'heal_char'
    energy = 10.0
    rechargetime = 1.2

class PassiveHealChar(AbilityBase):
    name = 'passivehealing_indicator'
    displayname = "#CharPassiveHealing_Name"
    description = "#CharPassiveHealing_Description"
    image_name = 'vgui/rebels/abilities/heal_passive'
    hidden = True # Hidden from abilitypanel