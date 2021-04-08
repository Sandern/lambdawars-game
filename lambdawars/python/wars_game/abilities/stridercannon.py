from core.abilities import AbilityTarget, AbilityUpgrade
from core.decorators import serveronly
from fields import FloatField

if isclient:
    from te import C_StriderFX
else:
    from core.units import BaseBehavior, BehaviorGeneric
    from unit_helper import GF_REQUIREVISION, GF_REQTARGETALIVE, GF_USETARGETDIST
    
if isserver:
    class ActionExecuteFireCannon(BehaviorGeneric.ActionMoveInRangeAndFace):
        def Init(self, order, parentaction):
            target = order.target if order.target else order.position
            
            super().Init(target, 896.0, goalflags=GF_REQTARGETALIVE|GF_USETARGETDIST|GF_REQUIREVISION)
            
            self.order = order
            self.ability = order.ability
            self.parentaction = parentaction
        
        def Update(self):
            if self.chargingcannon and not self.firedcannon:
                order = self.order
                self.outer.AimCannonAt(self.firepos, 0.1)
                if self.firecannontime < gpGlobals.curtime:
                    self.parentaction.changetoidleonlostorder = True
                    self.firedcannon = True
                    
                    abi = self.ability
                    self.outer.FireCannon(self.firepos, abi.damage, abi.damageradius)

                    abi.SetRecharge(self.outer)
                    abi.Completed()
                    order.Remove(dispatchevent=True)
                return self.Continue()
            # Only execute base if not charging
            return super().Update()
            
        def OnEnd(self):
            super().OnEnd()
            
            outer = self.outer
            #if self.originalbodyheight:
            #    outer.body_height = self.originalbodyheight
            
            if not self.firedcannon:
                outer.CancelFireCannon()
                self.order.ability.Cancel()
            
        def OnInRangeAndFacing(self):
            outer = self.outer
            if self.outer.curorder != self.order:
                self.order.ability.Cancel()
                return self.Done('Ignore facing event due changed order')

            if not self.ability.TakeEnergy(outer):
                self.ability.Cancel(cancelmsg='#Ability_NotEnoughEnergy')
                return self.Done('Canceled ability due lack of energy')
        
            order = self.order
            self.parentaction.changetoidleonlostorder = False
            self.chargingcannon = True
            self.ability.SetNotInterruptible()
            self.firepos = order.target.GetAbsOrigin() if (order.target and not order.target.IsWorld()) else order.position
            outer.ChargeCannon(self.firepos)
            self.firecannontime = gpGlobals.curtime + 1.25
            
            #self.originalbodyheight = outer.bodyheight
            #outer.body_height = outer.bodyheight * 0.5

        chargingcannon = False
        firedcannon = False
        firecannontime = 0
        firepos = None
        
        #originalbodyheight = None

    class ActionFireCannonAbility(BaseBehavior.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionExecuteFireCannon, 'Doing fire cannon action', self.order, self)

        def OnStunned(self):
            self.order.ability.Cancel()
            return self.ChangeTo(self.behavior.ActionStunned, 'Stunned')
            
class AbilityStriderCannon(AbilityTarget):
    # Info
    name = 'stridercannon'
    displayname = '#CombStriderCannon_Name'
    description = '#CombStriderCannon_Description'
    image_name = 'vgui/combine/abilities/strider_cannon'
    rechargetime = 3.0
    damage = FloatField(value=400.0)
    damageradius = FloatField(value=256.0)
    #techrequirements = ['stridercannon_unlock']
    #costs = [[('power', 100)], [('kills', 10)]]
    energy = 50
    sai_hint = AbilityTarget.sai_hint | set(['sai_grenade'])
    
    @serveronly
    def DoAbility(self):
        data = self.mousedata
        
        #if isserver:
        #    self.unit.AimCannonAt(data.endpos, 0.1)
        #    self.unit.FireCannon(data.endpos)
            
        #    self.Completed()
        
        target = data.ent if (data.ent and not data.ent.IsWorld()) else None
        if target == self.unit:
            if isserver: 
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
            return
            
        self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)
        
    if isserver:
        behaviorgeneric_action = ActionFireCannonAbility
        
class AbilityStriderCannonUnlock(AbilityUpgrade):
    name = 'stridercannon_unlock'
    displayname = '#AbilityStriderCannonUnlock_Name'
    description = '#AbilityStriderCannonUnlock_Description'
    image_name = "vgui/combine/abilities/combine_strider_cannon_unlock.vmt"
    buildtime = 45.0
    costs = [[('kills', 4)], [('requisition', 250), ('power', 400)]]