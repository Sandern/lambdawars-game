from srcbase import *
from vmath import Vector, QAngle, AngleVectors
import random
from .basezombie import BaseZombieInfo, UnitBaseZombie as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t, TranslateActivityMap
from entities import entity, Activity
from animation import EventList_RegisterPrivateEvent
if isserver:
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    
ZOMBIE_MELEE1_RANGE = 100.0

@entity('unit_zombie', networked=True)
class UnitZombie(BaseClass):    
    """ ZOMBIE  """
    if isserver:
        def Precache(self):
            super().Precache() 
            
            #self.PrecacheModel( "models/zombie/classic.mdl" )
            self.PrecacheModel( "models/zombie/classic_torso.mdl" )
            self.PrecacheModel( "models/zombie/classic_legs.mdl" )

            self.PrecacheScriptSound( "Zombie.FootstepRight" )
            self.PrecacheScriptSound( "Zombie.FootstepLeft" )
            self.PrecacheScriptSound( "Zombie.FootstepLeft" )
            self.PrecacheScriptSound( "Zombie.ScuffRight" )
            self.PrecacheScriptSound( "Zombie.ScuffLeft" )
            self.PrecacheScriptSound( "Zombie.AttackHit" )
            self.PrecacheScriptSound( "Zombie.AttackMiss" )
            self.PrecacheScriptSound( "Zombie.Pain" )
            self.PrecacheScriptSound( "Zombie.Die" )
            self.PrecacheScriptSound( "Zombie.Alert" )
            self.PrecacheScriptSound( "Zombie.Idle" )
            self.PrecacheScriptSound( "Zombie.Attack" )

            self.PrecacheScriptSound( "NPC_BaseZombie.Moan1" )
            self.PrecacheScriptSound( "NPC_BaseZombie.Moan2" )
            self.PrecacheScriptSound( "NPC_BaseZombie.Moan3" )
            self.PrecacheScriptSound( "NPC_BaseZombie.Moan4" )
            
        def Spawn(self):
            super().Spawn()
            
            self.SetBloodColor(BLOOD_COLOR_ZOMBIE)
            
    def AttackHitSound(self):
        """ Play a random attack hit sound """
        self.EmitSound( "Zombie.AttackHit" )

    def AttackMissSound(self):
        """ Play a random attack miss sound """
        self.EmitSound("Zombie.AttackMiss")
            
    # Activity translation table
    acttables = {
        Activity.ACT_RUN : Activity.ACT_WALK,
    }
    
    if isserver:
        # Anim events
        aetable = dict(BaseClass.aetable)
        aetable.update({
            'AE_ZOMBIE_SWATITEM': None,
            'AE_ZOMBIE_STARTSWAT': EmitSoundAnimEventHandler('Zombie.Attack'),
            'AE_ZOMBIE_STEP_LEFT': EmitSoundAnimEventHandler('Zombie.FootstepLeft'),
            'AE_ZOMBIE_STEP_RIGHT': EmitSoundAnimEventHandler('Zombie.FootstepRight'),
            'AE_ZOMBIE_SCUFF_LEFT': EmitSoundAnimEventHandler('Zombie.ScuffRight'),#BaseAnimEventHandler(),
            'AE_ZOMBIE_SCUFF_RIGHT': EmitSoundAnimEventHandler('Zombie.ScuffLeft'),#BaseAnimEventHandler(),
            'AE_ZOMBIE_ATTACK_SCREAM': EmitSoundAnimEventHandler('Zombie.Attack'),
            'AE_ZOMBIE_GET_UP': None,
            'AE_ZOMBIE_POUND': None,
            'AE_ZOMBIE_ALERTSOUND': None,
            'AE_ZOMBIE_POPHEADCRAB': None,
        })
    
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=20.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )


class ZombieInfo(BaseZombieInfo):
    name = 'unit_zombie'
    displayname = '#ZomZombie_Name'
    description = '#ZomZombie_Description'
    cls_name = 'unit_zombie'
    image_name = 'vgui/units/unit_shotgun.vmt'
    health = 250
    maxspeed = 48.0
    attributes = ['creature']
    turnspeed = 120.0
    scrapdropchance = 0.0
    viewdistance = 896
    modelname = 'models/Zombie/classic.mdl'
    legmodel = 'models/zombie/classic_legs.mdl'
    torsomodel = 'models/zombie/classic_torso.mdl'
    torsogibmodel = 'models/zombie/classic_torso.mdl'
    sound_death = 'Zombie.Die'
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    
    class AttackMelee(BaseZombieInfo.AttackMelee):
        maxrange = 55.0
        damage = 60
        damagetype = DMG_SLASH
        attackspeed = 1.9
    attacks = 'AttackMelee'

class ZombieBossInfo(ZombieInfo):
    name = 'unit_zombieboss'
    displayname = '#ZomZombieBoss_Name'
    description = '#ZomZombieBoss_Description'
    attributes = ['heavy', 'creature']
    health = 1200
    scrapdropchance = 0.0
    scale = 1.2
    maxspeed = 88.0
    
    class AttackMelee(ZombieInfo.AttackMelee):
        maxrange = 62.0
        damage = 200
        damagetype = DMG_SLASH
        attackspeed = 1.1
    attacks = 'AttackMelee'