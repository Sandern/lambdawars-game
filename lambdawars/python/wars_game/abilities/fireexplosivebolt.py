from vmath import VectorNormalize, Vector, QAngle, VectorAngles
from core.abilities import AbilityTarget, AbilityUpgrade
from entities import FClassnameIs

if isserver:
    from wars_game.weapons.crossbow import ExplosiveCrossbowBolt, WeaponCrossbow
    
    from core.units import BehaviorGeneric
    
    # Actions
    class ActionDoShootBolt(BehaviorGeneric.ActionAbility):
        def OnStart(self):
            return self.SuspendFor(ActionShootBolt, 'Shooting explosive bolt', self.order, self)
            
        def OnResume(self):
            self.changetoidleonlostorder = True
            if self.outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.order.ability.stopped:
                self.order.ability.Cancel()
                
        def OnOutOfClip(self):
            ''' Called when the active weapon clip has runned out of ammo. '''
            return self.SuspendFor(self.behavior.ActionReload, 'Waiting for reload animation')

    class ActionShootBolt(BehaviorGeneric.ActionMoveInRangeAndFace):
        def Init(self, order, parent_action):
            target = order.target if order.target else order.position
            
            super().Init(target, 896.0)

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
            return self.ChangeTo(self.behavior.ActionLockAim, 'Fired explosive bolt', self.target, duration=outer.activeweapon.secondaryfiredelay + 0.1)

class AbilityFireExplosiveBolt(AbilityTarget):
    # Info
    name = "fireexplosivebolt"
    displayname = '#RebExplosiveBolt_Name'
    description = '#RebExplosiveBolt_Description'
    image_name = 'vgui/rebels/abilities/rebel_fire_explosive_bolt.vmt'
    image_dis_name = 'vgui/rebels/abilities/rebel_fire_explosive_bolt.vmt'
    #costs = [[('scrap', 5)], [('kills', 1)]]
    rechargetime = 18
    #techrequirements = ['build_reb_munitiondepot']
    techrequirements = ['fireexplosivebolt_unlock']
    #activatesoundscript = '#energyball'
    sai_hint = AbilityTarget.sai_hint | set(['sai_combine_ball'])
    
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata
            
            if self.ischeat:
                playerpos = self.player.GetAbsOrigin() + self.player.GetCameraOffset() 
                shootdir = data.endpos - playerpos
                VectorNormalize(shootdir)
                boltangles = QAngle()
                VectorAngles(shootdir, boltangles)
                bolt = ExplosiveCrossbowBolt.BoltCreate(playerpos, boltangles, 100, self.player)
                bolt.SetAbsVelocity(shootdir * WeaponCrossbow.BOLT_AIR_VELOCITY)
                self.Completed()
                return
                
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            target = data.ent if (data.ent and not data.ent.IsWorld()) else None
            self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)

        behaviorgeneric_action = ActionDoShootBolt
        
    @classmethod    
    def GetRequirements(info, player, unit):
        requirements = set()
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_crossbow') and not unit.garrisoned:
            requirements.add('requirecrossbow')
        return requirements | super().GetRequirements(player, unit)
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        activeweapon = unit.activeweapon
        if not activeweapon or not FClassnameIs(activeweapon, 'weapon_crossbow'):
            return False
        return super().ShouldShowAbility(unit)

class AbilityFireExplosiveBoltDestroyHQ(AbilityFireExplosiveBolt):
    name = 'fireexplosivebolt_destroyhq'
    #techrequirements = ['build_reb_munitiondepot_destroyhq']
    techrequirements = ['fireexplosivebolt_unlock']

class AbilityFireExplosiveBoltOverrun(AbilityFireExplosiveBolt):
    name = 'fireexplosivebolt_overrun'
    techrequirements = []
    costs = []

class AbilityFireExplosiveBoltChar(AbilityFireExplosiveBolt):
    name = 'fireexplosivebolt_char'
    costs = []
    techrequirements = []
    rechargetime = 15.0

class FireExplosiveBoltUnlock(AbilityUpgrade):
    name = 'fireexplosivebolt_unlock'
    displayname = '#RebExplosiveBoltUnlock_Name'
    description = '#RebExplosiveBoltUnlock_Description'
    image_name = "VGUI/rebels/abilities/rebel_explosivebolt_unlock"
    #techrequirements = ['build_reb_specialops']
    buildtime = 60.0
    costs = [[('kills', 1)], [('requisition', 40), ('scrap', 20)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])
class FireExplosiveBoltUnlockDHQ(FireExplosiveBoltUnlock):
    name = 'fireexplosivebolt_unlock_destroyhq'
    #techrequirements = ['build_reb_munitiondepot_destroyhq']