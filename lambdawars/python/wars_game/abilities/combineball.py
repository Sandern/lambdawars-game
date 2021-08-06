from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget, AbilityUpgrade, AbilityUpgradeValue
from entities import FClassnameIs
from gamerules import gamerules

if isserver:
    from utils import UTIL_PrecacheOther
    from wars_game.ents.prop_combine_ball import CreateCombineBall
    
    from core.units import BehaviorGeneric
    
    # Actions
    class ActionDoShootCombineBall(BehaviorGeneric.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionShootCombineBall, 'Shooting ball', self.order, self)
            
        def OnResume(self):
            self.changetoidleonlostorder = True
            if self.outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.order.ability.stopped:
                self.order.ability.Cancel()

    class ActionShootCombineBall(BehaviorGeneric.ActionMoveInRangeAndFace):
        def Init(self, order, parent_action):
            target = order.target if order.target else order.position
            
            super().Init(target, 1024.0)

            self.parent_action = parent_action
            self.ability = order.ability
            
        def Update(self):
            ability = self.ability
            if not self.target:
                ability.Cancel()
                return self.Done('Lost target')
            if not ability.CanDoAbility(ability.player, self.outer):
                ability.Cancel()
                return self.Done('Can no longer do ability')
            return super().Update()
            
        def OnInRangeAndFacing(self):
            outer = self.outer
            ability = self.ability

            if not ability.CanDoAbility(ability.player, outer):
                ability.Cancel()
                return self.Done('Can no longer do ability')

            ability.SetNotInterruptible()

            outer.activeweapon.SecondaryAttack()
            outer.DoAnimation(outer.ANIM_ATTACK_SECONDARY)
            ability.SetRecharge(outer)
            ability.Completed()
            self.parent_action.changetoidleonlostorder = False
            return self.ChangeTo(self.behavior.ActionLockAim, 'Fired energy ball', self.target, duration=outer.activeweapon.secondaryfiredelay + 0.1)

# Spawns a combine ball
class AbilityCombineBall(AbilityTarget):
    # Info
    name = "combineball"
    displayname = '#CombBall_Name'
    description = '#CombBall_Description'
    image_name = 'vgui/abilities/ability_ar2orb.vmt'
    image_dis_name = 'vgui/abilities/ability_ar2orb.vmt'
    #costs = [('power', 10)]
    rechargetime = 15
    #techrequirements = ['combineball_unlock']
    activatesoundscript = '#energyball'
    sai_hint = AbilityTarget.sai_hint | set(['sai_combine_ball'])

    # Ability
    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()
            
            UTIL_PrecacheOther('prop_combine_ball')
            
        def DoAbility(self):
            data = self.mousedata
            
            if self.ischeat:
                playerpos = self.player.GetAbsOrigin() + self.player.GetCameraOffset() 
                vecShootDir = data.endpos - playerpos
                VectorNormalize( vecShootDir )
                
                CreateCombineBall( playerpos, vecShootDir * 10000.0, 10, 250, 4, self.player )
                self.Completed()
                return
                
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            target = data.ent if (data.ent and not data.ent.IsWorld()) else None
            self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)

        behaviorgeneric_action = ActionDoShootCombineBall
        
    @classmethod    
    def GetRequirements(info, player, unit):
        requirements = set()
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_ar2'):
            requirements.add('requirear2')
        return requirements | super().GetRequirements(player, unit)
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_ar2'):
            return False
        return super().ShouldShowAbility(unit)
     
class AbilityCombineBallUnlock(AbilityUpgrade):
    name = 'combineball_unlock'
    displayname = '#CombBallUnlock_DisplayName'
    description = '#CombBallUnlock_Description'
    image_name = "vgui/abilities/ability_ar2orb_upgrade"
    techrequirements = ['build_comb_specialops']
    buildtime = 30.0
    costs = [[('kills', 5)], [('requisition', 25), ('power', 25)]]
class AbilityCombineBallUpgrade(AbilityUpgradeValue):
    name = 'combineball_upgrade'
    displayname = '#CombBallUpgrade_DisplayName'
    description = '#CombBallUpgrade_Description'
    image_name = "vgui/abilities/ability_ar2orb_upgrade"
    techrequirements = ['build_comb_specialops']
    buildtime = 72.0
    upgradevalue = True
    costs = [[('kills', 15)], [('requisition', 25), ('power', 25)]]
    @classmethod    
    def GetRequirements(info, player, unit):
        requirements = set()
        if gamerules.info.name == 'overrun':
            requirements.discard('available')
        return requirements | super().GetRequirements(player, unit)

class AbilityCombineBallOverrun(AbilityCombineBall):
	name = 'combineball_overrun'
	costs = []
	techrequirements = []
class AbilityCombineBallChar(AbilityCombineBall):
    name = 'combineball_char'
    costs = []
    techrequirements = []
    rechargetime = 15.0