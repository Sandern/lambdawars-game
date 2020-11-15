from srcbase import *
from vmath import Vector, QAngle, AngularImpulse, AngleVectors, vec3_angle, vec3_origin
import random
from core.units import EventHandlerAnimation
from .basezombie import BaseZombieInfo, UnitBaseZombie as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t, TranslateActivityMap
from entities import entity, Activity
from animation import EventList_RegisterPrivateEvent
if isserver:
    from entities import SpawnBlood
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from wars_game.ents.grenade_frag import GrenadeFrag
    from animation import Animevent
    
ZOMBIE_MELEE1_RANGE = 100.0

@entity('unit_zombine', networked=True)
class UnitZombine(BaseClass):   
    if isserver:
        def Precache(self):
            super().Precache() 
            
            self.PrecacheModel( "models/zombie/zombie_soldier_legs.mdl" )
            self.PrecacheModel( "models/zombie/zombie_soldier_torso.mdl" )
            
            self.PrecacheScriptSound( "Zombie.FootstepRight" )
            self.PrecacheScriptSound( "Zombie.FootstepLeft" )
            self.PrecacheScriptSound( "Zombine.ScuffRight" )
            self.PrecacheScriptSound( "Zombine.ScuffLeft" )
            self.PrecacheScriptSound( "Zombie.AttackHit" )
            self.PrecacheScriptSound( "Zombie.AttackMiss" )
            self.PrecacheScriptSound( "Zombine.Pain" )
            self.PrecacheScriptSound( "Zombine.Die" )
            self.PrecacheScriptSound( "Zombine.Alert" )
            self.PrecacheScriptSound( "Zombine.Idle" )
            self.PrecacheScriptSound( "Zombine.ReadyGrenade" )

            self.PrecacheScriptSound( "ATV_engine_null" )
            self.PrecacheScriptSound( "Zombine.Charge" )
            self.PrecacheScriptSound( "Zombie.Attack" )
            
        def Spawn(self):
            super().Spawn()
            
            self.SetBloodColor(BLOOD_COLOR_ZOMBIE)
            
            UnitZombine.g_flZombineGrenadeTimes = gpGlobals.curtime
            self.grenadepulltime = gpGlobals.curtime
            
            self.grenadecount = self.ZOMBINE_MAX_GRENADES
            
        def Event_Killed(self, info):
            super().Event_Killed(info)
            
            # Drop grenade
            if self.grenade:
                self.grenade.SetParent(None)
            
    def AttackHitSound(self):
        """ Play a random attack hit sound """
        self.EmitSound( "Zombie.AttackHit" )

    def AttackMissSound(self):
        """ Play a random attack miss sound """
        self.EmitSound("Zombie.AttackMiss")
        
    def PullPin(self, event):
        vecStart = Vector()
        angles = QAngle()
        self.GetAttachment( "grenade_attachment", vecStart, angles )

        grenade = GrenadeFrag.Fraggrenade_Create( vecStart, vec3_angle, vec3_origin, AngularImpulse( 0, 0, 0 ), None, 3.5 )

        if grenade:
            # Move physobject to shadow
            physicsobject = grenade.VPhysicsGetObject()

            if physicsobject:
                grenade.VPhysicsDestroyObject()

                iAttachment = self.LookupAttachment("grenade_attachment")

                grenade.SetMoveType(MOVETYPE_NONE)
                grenade.SetSolid(SOLID_NONE)
                grenade.SetCollisionGroup(COLLISION_GROUP_DEBRIS)

                grenade.SetAbsOrigin(vecStart)
                grenade.SetAbsAngles(angles)

                grenade.SetParent(self, iAttachment)

                grenade.damage = 250
                grenade.damageradius = 350
                self.grenade = grenade
                
                self.EmitSound( "Zombine.ReadyGrenade" )

            self.grenadecount -= 1
    if isserver:
        def StartMeleeAttack(self, enemy):    
            # Do melee damage
            attackinfo = self.unitinfo.AttackMelee
            self.MeleeAttack(attackinfo.maxrange, attackinfo.damage)
                
            return super().StartMeleeAttack(enemy)

    def MeleeAttack(self, distance, damage):
        vecMins = self.WorldAlignMins()
        vecMaxs = self.WorldAlignMaxs()
        vecMins.z = vecMins.x
        vecMaxs.z = vecMaxs.x
        enthurt = self.CheckTraceHullAttack( distance, vecMins, vecMaxs, damage, self.unitinfo.AttackMelee.damagetype)
        if enthurt != None:     # hitted something
            # Play a random attack hit sound
            self.EmitSound( "Zombie.AttackHit" )
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), enthurt.BloodColor(), damage)
        else:
            self.EmitSound( "Zombie.AttackMiss" )
    def AttackRight(self, event): pass #можно сделать рандомный выбор или поведение и типа по разному атакует но как по мне такое себе
    def AttackLeft(self, event): pass
    def AttackBoth(self, event): pass
    def ClawAttack(self, flDist, iDamage, qaViewPunch, vecVelocityPunch, BloodOrigin): pass
    # Events
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_ZOMBINE_PULLGRENADE' : EventHandlerAnimation('ACT_ZOMBINE_GRENADE_PULL'),
    } )

    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_ZOMBINE_GRENADE_PULL',
        'ACT_ZOMBINE_GRENADE_WALK',
        'ACT_ZOMBINE_GRENADE_RUN',
        'ACT_ZOMBINE_GRENADE_IDLE',
        'ACT_ZOMBINE_ATTACK_FAST',
        'ACT_ZOMBINE_GRENADE_FLINCH_BACK',
        'ACT_ZOMBINE_GRENADE_FLINCH_FRONT',
        'ACT_ZOMBINE_GRENADE_FLINCH_WEST',
        'ACT_ZOMBINE_GRENADE_FLINCH_EAST',
    ])
    
    if isserver:
        # Anim events
        aetable = dict(BaseClass.aetable)
        aetable.update({
            'AE_ZOMBINE_PULLPIN' : PullPin,
            'AE_ZOMBIE_STEP_LEFT' : EmitSoundAnimEventHandler('Zombie.FootstepLeft'),
            'AE_ZOMBIE_STEP_RIGHT' : EmitSoundAnimEventHandler('Zombie.FootstepRight'),
            #'AE_ZOMBIE_ATTACK_SCREAM' : EmitSoundAnimEventHandler('Zombie.Attack'),
            Animevent.AE_NPC_ATTACK_BROADCAST : BaseAnimEventHandler(),
        })
    attackmelee1act = 'ACT_ZOMBINE_ATTACK_FAST'

    grenade = None
    
    g_flZombineGrenadeTimes = 0
    ZOMBINE_MAX_GRENADES = 1

class ZombineInfo(BaseZombieInfo):
    name = 'unit_zombine'
    displayname = '#ZomZombine_Name'
    description = '#ZomZombine_Description'
    cls_name = 'unit_zombine'
    image_name = 'vgui/units/unit_shotgun.vmt'
    health = 220
    maxspeed = 200.0
    scrapdropchance = 0.0
    viewdistance = 896
    modelname = 'models/Zombie/zombie_soldier.mdl'
    legmodel = 'models/zombie/zombie_soldier_legs.mdl'
    torsomodel = 'models/zombie/zombie_soldier_torso.mdl'
    torsogibmodel = 'models/zombie/zombie_soldier_torso.mdl'
    attributes = ['medium', 'creature']
    
    sound_death = 'Zombine.Die'
    
    abilities = {
        0 : 'pullgrenade',
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'patrol',
    }
    
    class AttackMelee(BaseZombieInfo.AttackMelee):
        maxrange = 55.0
        damage = 60
        damagetype = DMG_SLASH
        attackspeed = 1.9
    attacks = 'AttackMelee'