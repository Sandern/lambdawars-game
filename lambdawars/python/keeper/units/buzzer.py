from srcbase import DMG_SLASH, MASK_SOLID, COLLISION_GROUP_NONE
from vmath import Vector, QAngle
from .basekeeper import UnitBaseCreature as BaseClass, UnitKeeperInfo
from entities import entity, Activity
from core.units import UnitBaseAirLocomotion
import random
if isserver:
    from particles import PrecacheParticleSystem
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from core.units import UnitCombatAirNavigator
    from entities import SpawnBlood
    from utils import UTIL_TraceLine, UTIL_DecalTrace, trace_t
    
@entity('unit_buzzer', networked=True)
class UnitBuzzer(BaseClass):
    aiclimb = False
    LocomotionClass = UnitBaseAirLocomotion
    if isserver:
        NavigatorClass = UnitCombatAirNavigator
        
    def __init__(self):
        super(UnitBuzzer, self).__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 2048.0
        self.testroutestartheight = 2048.0
        
    if isserver:
        def Precache(self):
            super(UnitBuzzer, self).Precache()
            
            #PropBreakablePrecacheAll( MAKE_STRING(ASW_BUZZER_MODEL) )
                
            self.PrecacheScriptSound( "ASW_Buzzer.Attack" )
            self.PrecacheScriptSound( "ASW_Buzzer.Death" )
            self.PrecacheScriptSound( "ASW_Buzzer.Pain" )
            self.PrecacheScriptSound( "ASW_Buzzer.Idle" )
            self.PrecacheScriptSound( "ASW_Buzzer.OnFire" )

            PrecacheParticleSystem( "buzzer_trail" )
            PrecacheParticleSystem( "buzzer_death" )
            
    def Spawn(self):
        super(UnitBuzzer, self).Spawn()
        
        self.locomotion.desiredheight = 52.0
        self.locomotion.flynoiserate = 48.0
        self.locomotion.flynoisez = 24.0
        if isserver:
            self.navigator.testroutemask = MASK_SOLID
            self.navigator.usesimplifiedroutebuilding = False
            self.navigator.testrouteworldonly = False
            
    def StartMeleeAttack(self, enemy):
        attackinfo = self.unitinfo.AttackMelee
        self.MeleeAttack(attackinfo.maxrange, attackinfo.damage, QAngle( 20.0, 0.0, -12.0 ), Vector( -250.0, 1.0, 1.0 )) 
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackMelee.attackspeed
        return False
        
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        attackinfo = self.unitinfo.AttackMelee
        enthurt = self.CheckTraceHullAttack(distance, -Vector(16,16,32), Vector(16,16,32), damage, attackinfo.damagetype, 1.2, False)
        if enthurt:
            # Play a random attack hit sound
            self.EmitSound("ASW_Buzzer.Attack")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), self.BloodColor(), damage)
        else:
            self.EmitSound("ASW_Drone.Swipe")

    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [

    ] )
    
    # Animation translation table
    acttables = {
        Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_GLIDE,
    }
    
    if isserver:
        # Anim events
        aetable = {

        }
    
    maxspeed = 350
    
class BuzzerInfo(UnitKeeperInfo):
    name = 'unit_buzzer'
    cls_name = 'unit_buzzer'
    hulltype = 'HULL_TINY_CENTERED'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    costs = []
    health = 100
    viewdistance = 500
    displayname = 'Buzzer'
    description = 'Buzzer'
    modelname = 'models/aliens/buzzer/buzzer.mdl'
    sound_death = 'ASW_Buzzer.Death'
    attacks = 'AttackMelee'
    
    class AttackMelee(UnitKeeperInfo.AttackMelee):
        maxrange = 32.0
        damage = 5
        damagetype = DMG_SLASH
        attackspeed = 1.0
    attacks = 'AttackMelee'