from srcbase import DMG_SLASH, DMG_ACID
from vmath import QAngle, Vector
from .basekeeper import UnitBaseCreature as BaseClass, UnitKeeperInfo
from entities import entity, Activity
import random
if isserver:
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from entities import CTakeDamageInfo, CalculateMeleeDamageForce
    from te import CEffectData, DispatchEffect
    from entities import SpawnBlood
    
@entity('unit_parasite', networked=True)
class UnitParasite(BaseClass):
    if isserver:
        def Precache(self):
            super(UnitParasite, self).Precache()
            
            self.PrecacheScriptSound("ASW_Parasite.Death")
            self.PrecacheScriptSound("ASW_Parasite.Attack")
            self.PrecacheScriptSound("ASW_Parasite.Idle")
            self.PrecacheScriptSound("ASW_Parasite.Pain")
            
        def Spawn(self):
            super(UnitParasite, self).Spawn()
            
            self.skin = random.randint(0, 2)
            
    def ShouldGib(self, info):
        return False
        
    def CalcDamageInfo(self, info):
        info.Set(self, self, 5, DMG_ACID)
        CalculateMeleeDamageForce(info, self.GetAbsVelocity(), self.GetAbsOrigin())
        return pInfo.GetDamage()
        
    def TouchDamage(self, other):
        info = CTakeDamageInfo()
        self.CalcDamageInfo(info)
        damage = 5
        info.SetDamage(damage)
        other.TakeDamage(info)
        self.EmitSound("ASWFire.AcidBurn")
        data = CEffectData()
        data.origin = self.GetAbsOrigin()
        data.otherentindex = other.entindex()
        DispatchEffect("ASWAcidBurn", data)
            
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        attackinfo = self.unitinfo.AttackMelee
        enthurt = self.CheckTraceHullAttack(distance, -Vector(16,16,32), Vector(16,16,32), damage, attackinfo.damagetype, 1.2, False)
        if enthurt:
            # Play a random attack hit sound
            self.EmitSound("ASW_Parasite.Attack")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), self.BloodColor(), damage)
        else:
            pass #self.EmitSound("ASW_Drone.Swipe")
            
    # Anim event handlers
    def ParasiteAttack(self, event):
        attackinfo = self.unitinfo.AttackMelee
        self.MeleeAttack(attackinfo.maxrange, attackinfo.damage, QAngle(20.0, 0.0, -12.0), Vector(-250.0, 1.0, 1.0)) 
            
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_ASW_EGG_IDLE',
    ] )
    
    # Animation translation table
    acttables = {
        #Activity.ACT_RANGE_ATTACK1 : Activity.ACT_MELEE_ATTACK1,
        Activity.ACT_MELEE_ATTACK1 : Activity.ACT_RANGE_ATTACK1,
        Activity.ACT_MP_JUMP_FLOAT : 'ACT_ASW_EGG_IDLE',
    }
    
    if isserver:
        # Anim events
        aetable = {
            'AE_HEADCRAB_JUMPATTACK' : ParasiteAttack,
        }
        
    maxspeed = 220
    
class ParasiteInfo(UnitKeeperInfo):
    cls_name = 'unit_parasite'
    hulltype = 'HULL_TINY'
    name = 'unit_parasite'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    costs = []
    health = 200
    viewdistance = 400
    displayname = 'Parasite'
    description = 'A parasite'
    modelname = 'models/swarm/parasite/parasite.mdl'
    sound_death = 'ASW_Parasite.Death'

    class AttackMelee(UnitKeeperInfo.AttackMelee):
        maxrange = 32.0
        damage = 10
        damagetype = DMG_SLASH
    attacks = 'AttackMelee'
    