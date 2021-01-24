from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget, AbilityUpgrade, AbilityUpgradeValue
from fields import FloatField, StringField, UpgradeField
from entities import entity

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_PrecacheOther
    from core.units import BaseBehavior
        
if isserver:
    class ActionThrowGrenade(BaseBehavior.ActionAbility):
        def Update(self):
            outer = self.outer
            abi = self.order.ability
            throwrange = abi.throwrange if abi else 768.0
            
            target = abi.throwtarget if abi.throwtarget else abi.throwtargetpos
            
            # In range?
            if abi.throwtarget:
                dist = outer.EnemyDistance(abi.throwtarget)
            else:
                dist = (outer.GetAbsOrigin() - abi.throwtargetpos).Length2D()
            fnloscheck = outer.GrenadeInRangeLOSCheck if hasattr(outer, 'GrenadeInRangeLOSCheck') else None
            if fnloscheck:
                if dist > throwrange or not fnloscheck(self.order.position, abi.throwtarget):
                    return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into grenade throw range', target, maxrange=throwrange, fncustomloscheck=fnloscheck) 
            else:
                if dist > throwrange:
                    return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into grenade throw range', target, maxrange=throwrange) 
                    
            # Facing?
            if not outer.FInAimCone(target, self.facingminimum):
                return self.SuspendFor(self.behavior.ActionFaceTarget, 'Not facing target', target, self.facingminimum)

            outer.grenadeability = abi
            self.throwedgrenade = True
            self.changetoidleonlostorder = False
            outer.DoAnimation(outer.ANIM_THROWGRENADE, data=round(abi.throw_anim_speed * 255))
            abi.SetNotInterruptible()
            return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Executing attack', self.outer.animstate.specificmainactivity)
            
        def OnEnd(self):
            super().OnEnd()
            
            self.outer.grenadeability = None
            
            # Noop in case already canceled or completed, so just call to be sure
            self.order.ability.Cancel()

        def OnResume(self):
            self.changetoidleonlostorder = True
            if self.throwedgrenade:
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        throwedgrenade = False
        facingminimum = 0.7

    class ActionThrowStunGrenade(ActionThrowGrenade):
        def Update(self):
            outer = self.outer
            abi = self.order.ability
            throwrange = abi.throwrange if abi else 1024.0

            target = abi.throwtarget if abi.throwtarget else abi.throwtargetpos

            # In range?
            if abi.throwtarget:
                dist = outer.EnemyDistance(abi.throwtarget)
            else:
                dist = (outer.GetAbsOrigin() - abi.throwtargetpos).Length2D()
            fnloscheck = outer.GrenadeInRangeLOSCheck if hasattr(outer, 'GrenadeInRangeLOSCheck') else None
            if fnloscheck:
                if dist > throwrange or not fnloscheck(self.order.position, abi.throwtarget):
                    return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into grenade throw range', target,
                                           maxrange=throwrange, fncustomloscheck=fnloscheck)
            else:
                if dist > throwrange:
                    return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into grenade throw range', target,
                                           maxrange=throwrange)

                    # Facing?
            if not outer.FInAimCone(target, self.facingminimum):
                return self.SuspendFor(self.behavior.ActionFaceTarget, 'Not facing target', target, self.facingminimum)

            outer.grenadeability = abi
            self.throwedgrenade = True
            self.changetoidleonlostorder = False
            outer.DoAnimation(outer.ANIM_TOSS_GRENADE, data=round(abi.throw_anim_speed * 255))
            abi.SetNotInterruptible()
            return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Executing attack',
                                   self.outer.animstate.specificmainactivity)

class AbilityGrenade(AbilityTarget):
    # Info
    name = "grenade"
    image_name = 'vgui/abilities/ability_grenade.vmt'
    rechargetime = 40.0
    costs = [[('requisition', 0)], [('kills', 1)]]
    displayname = "#AbilityGrenade_Name"
    description = "#AbilityGrenade_Description"
    techrequirements = ['grenade_unlock']
    activatesoundscript = '#grenade'
    damageradius = FloatField(value=256.0)
    damage = FloatField(value=100)
    throwrange = FloatField(value=768.0)
    throw_anim_speed = FloatField(value=1.50)
    grenadeclsname = StringField(value='grenade_frag')
    sai_hint = AbilityTarget.sai_hint | set(['sai_grenade'])
    
    # Ability
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(self.damageradius, 1, 0))
        
    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()
            
            UTIL_PrecacheOther(info.grenadeclsname)
    
        def DoAbility(self):
            data = self.mousedata
            units = self.TakeEnergy(self.units)
            
            if self.ischeat:
                playerpos = self.player.GetAbsOrigin() + self.player.GetCameraOffset() 
                vecShootDir = data.endpos - playerpos
                VectorNormalize( vecShootDir )
                grenade = CreateEntityByName(self.grenadeclsname)
                grenade.SetAbsOrigin(playerpos)
                DispatchSpawn(grenade)
                self.SetupGrenade(grenade)
                grenade.SetVelocity( vecShootDir * 10000.0, Vector(0, 0, 0) )
                grenade.SetTimer( 2.0, 2.0 - grenade.FRAG_GRENADE_WARN_TIME )
                self.Completed()
                return

            pos = data.groundendpos
            target = data.ent
            self.throwtargetpos = pos
            if target and not target.IsWorld():
                self.throwtarget = target
            
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            self.unit.AbilityOrder(position=pos,
                        target=target,
                        ability=self)
            
        def SetupGrenade(self, grenade):
            """ Applies settings from ability to grenade.
                This allows customization per different ability.
            """
            grenade.damageradius = self.damageradius
            grenade.damage = self.damage
            
        def OnGrenadeThrowed(self, unit, grenade):
            self.grenade = grenade
            self.SetupGrenade(grenade)
            self.SetRecharge(unit)
            self.Completed()
        
        behaviorgeneric_action = ActionThrowGrenade
        #damage = UpgradeField(cppimplemented=True, abilityname='army_tier2')
        
    '''
    # Silly test
    defaultautocast = True
    autocastcheckonenemy = True
    @classmethod
    def CheckAutoCast(info, unit):
        print 'checking grenade autocast'
        if info.CanDoAbility(None, unit=unit):
            enemy = unit.enemy
            from entities import MouseTraceData
            leftpressed = MouseTraceData()
            leftpressed.endpos = enemy.GetAbsOrigin()
            leftpressed.groundendpos = enemy.GetAbsOrigin()
            leftpressed.ent = enemy
            unit.DoAbility(info.name, mouse_inputs=[('leftpressed', leftpressed)])
            return True
        return False
    '''
        
    infoparticles = ['pg_grenade_radius']
    
    grenade = None # Set after the unit throwed the grenade
    throwtargetpos = None
    throwtarget = None

'''@entity('grenade', networked=True)
class GrenadeRebels(AbilityTarget):
    damage = UpgradeField(cppimplemented=True, abilityname='army_tier2')

@entity('grenade_combine', networked=True)
class GrenadeCombine(AbilityTarget):
    damage = UpgradeField(abilityname='army_tier2', cppimplemented=True)'''

class AbilityGrenadeCombine(AbilityGrenade):
    name = "grenade_combine"
    techrequirements = ['grenade_unlock_combine']

class OverrunAbilityGrenade(AbilityGrenade):
    name = "overrun_grenade"
    techrequirements = ['or_tier2_research']
    hidden = True
    
# Unlock for grenade
class AbilityGrenadeUnlock(AbilityUpgrade):
    name = 'grenade_unlock'
    displayname = '#AbilityGrenadeUnlock_Name'
    description = '#AbilityGrenadeUnlock_Description'
    image_name = "vgui/abilities/unlock_grenade.vmt"
    buildtime = 40.0
    costs = [[('kills', 4)], [('scrap', 30)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_grenade_upgrade'])

class AbilityGrenadeUnlockCombine(AbilityGrenadeUnlock):
    name = 'grenade_unlock_combine'
    costs = [('power', 30)]
    
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_grenade_upgrade'])

class AbilitySmokeGrenade(AbilityGrenade):
    name = 'smokegrenade'
    grenadeclsname = 'grenade_smoke'
    #energy = 40.0
    #costs = []
    #costs = [[('requisition', 3)], [('kills', 1)]]
    image_name = 'vgui/rebels/abilities/rebel_smoke_grenade.vmt'
    displayname = "#AbilitySmokeGrenade_Name"
    description = "#AbilitySmokeGrenade_Description"
    techrequirements = []
    rechargetime = 20.0
    smokeduration = 10.0
    throwrange = 768.0
    throw_anim_speed = FloatField(value=1.75)
    
    def SetupGrenade(self, grenade):
        """ Applies settings from ability to grenade.
            This allows customization per different ability.
        """
        grenade.smokeduration = self.smokeduration

# Mission Versions
class MissionAbilityGrenade(AbilityGrenade):
    name = "mission_grenade"
    rechargetime = 1.5
    damageradius = FloatField(value=200.0)
    damage = FloatField(value=120)
    throwrange = FloatField(value=700.0)
    techrequirements = []
    costs = [[('requisition', 0)], [('kills', 1)]]
    hidden = True

class MissionAbilitySmokeGrenade(AbilitySmokeGrenade):
    name = 'mission_smokegrenade'
    rechargetime = 1.5
    smokeduration = 5.0
    throwrange = FloatField(value=700.0)
    techrequirements = []
    costs = [[('requisition', 0)], [('kills', 1)]]
    hidden = True

class ArmyTier2(AbilityUpgradeValue):
    name = 'army_tier2'
    displayname = '#ArmyTier2_Name'
    description = '#ArmyTier2_Description'
    upgradevalue = FloatField(value=270)

# ======================================================================================================================
# ============================================= Squad Wars Grenades ====================================================
# ======================================================================================================================

class AbilityGrenadeChar(AbilityGrenade):
    name = "grenade_soldier"
    rechargetime = 30.0
    techrequirements = []
    costs = []

class AbilitySmokeGrenadeChar(AbilitySmokeGrenade):
    name = "smokegrenade_char"
    rechargetime = 20.0
    costs = []

class AbilityStunGrenadeCharSoldier(AbilityGrenade):
    name = 'stun_frag'
    grenadeclsname = 'grenade_stun'
    rechargetime = 30.0
    techrequirements = []
    costs = []

class AbilityStunGrenadeChar(AbilityGrenade):
    name = 'stun_frag_police'
    grenadeclsname = 'grenade_stun'
    rechargetime = 30.0
    techrequirements = []
    costs = []

    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()

            UTIL_PrecacheOther(info.grenadeclsname)

        def DoAbility(self):
            data = self.mousedata
            units = self.TakeEnergy(self.units)

            if self.ischeat:
                playerpos = self.player.GetAbsOrigin() + self.player.GetCameraOffset()
                vecShootDir = data.endpos - playerpos
                VectorNormalize(vecShootDir)
                grenade = CreateEntityByName(self.grenadeclsname)
                grenade.SetAbsOrigin(playerpos)
                DispatchSpawn(grenade)
                self.SetupGrenade(grenade)
                grenade.SetVelocity(vecShootDir * 10000.0, Vector(0, 0, 0))
                grenade.SetTimer(2.0, 2.0 - grenade.FRAG_GRENADE_WARN_TIME)
                self.Completed()
                return

            pos = data.groundendpos
            target = data.ent
            self.throwtargetpos = pos
            if target and not target.IsWorld():
                self.throwtarget = target

            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            self.unit.AbilityOrder(position=pos,
                                   target=target,
                                   ability=self)

        def SetupGrenade(self, grenade):
            """ Applies settings from ability to grenade.
                This allows customization per different ability.
            """
            grenade.damageradius = self.damageradius
            grenade.damage = self.damage

        def OnGrenadeThrowed(self, unit, grenade):
            self.grenade = grenade
            self.SetupGrenade(grenade)
            self.SetRecharge(unit)
            self.Completed()

        behaviorgeneric_action = ActionThrowStunGrenade

class AbilityGrenadeHeal(AbilityGrenade):
    name = 'med_frag'
    rechargetime = 30.0
    damageradius = FloatField(value=200.0)
    damage = FloatField(value=-300.0)
    techrequirements = []
    costs = []