from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget, GetTechNode
from entities import FClassnameIs, MouseTraceData
from fow import FogOfWarMgr

if isserver:
    from utils import UTIL_PrecacheOther
    from wars_game.ents.prop_combine_ball import CreateCombineBall
    
    from core.units import BehaviorGeneric
    from gamerules import gamerules
    
    # Actions
    class ActionDoShootGrenade(BehaviorGeneric.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionShootGrenade, 'Shooting grenade', self.order)
            
        def OnResume(self):
            self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.order.ability.stopped:
                self.order.ability.Cancel()

    class ActionShootGrenade(BehaviorGeneric.ActionMoveInRangeAndFace):
        def Init(self, order):
            #target = order.target if order.ability.target else order.position
            target = order.position
            
            super().Init(target, self.outer.unitinfo.AttackRange.maxrange)
            
            self.order = order
            self.ability = order.ability
            
        def Update(self):
            if not self.target:
                self.ability.Cancel()
                return self.Done('Lost target')
            return super().Update()
        def OnInRangeAndFacing(self):
            ability = self.ability
            ability.SetNotInterruptible()
            
            outer = self.outer
            outer.DoAnimation(outer.ANIM_RANGE_ATTACK1)
            #self.firecannontime = gpGlobals.curtime + 2
            outer.ThrowEnergyGrenade(self.target)
            technode = GetTechNode('mortarsynth_upgrade', outer.GetOwnerNumber())
            if technode.techenabled:
                outer.nextattacktime += outer.unitinfo.AttackRange.attackspeed + outer.attackspeedboost
                outer.nextshoottime = outer.unitinfo.AttackRange.attackspeed + gpGlobals.curtime + outer.attackspeedboost
                ability.SetRecharge(outer, t=outer.attackspeedboost)
            else:
                outer.nextattacktime += outer.unitinfo.AttackRange.attackspeed
                outer.nextshoottime = outer.unitinfo.AttackRange.attackspeed + gpGlobals.curtime
                ability.SetRecharge(outer)
            self.ability.Completed()
            self.order.Remove(dispatchevent=True)
            return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Executing attack', outer.animstate.specificmainactivity)
        firecannontime = 0

class AbilityMortarAttack(AbilityTarget):
    # Info
    name = "mortarattack"
    displayname = '#CombBall_Name'
    description = '#CombBall_Description'
    image_name = 'VGUI/combine/abilities/mortar_synth_attack_icon.vmt'
    costs = [] 
    rechargetime = 7
    target = None
    supportsautocast = True
    defaultautocast = True
    # Ability
    if isserver:
            
        def DoAbility(self):
            data = self.mousedata
            if FogOfWarMgr().PointInFOW(data.endpos, self.ownernumber):
                self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
                return
                
            target = data.ent
            if target and not target.IsWorld():
                self.target = target.GetAbsOrigin()
            self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)

        behaviorgeneric_action = ActionDoShootGrenade
        