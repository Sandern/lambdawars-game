from srcbase import *
from vmath import Vector, QAngle, AngleVectors
from .basezombie import BaseZombieInfo, UnitBaseZombie as BaseClass
from entities import entity, Activity
from gameinterface import ConVarRef
import random
import math

if isserver:
    from unit_helper import EmitSoundAnimEventHandler, BaseAnimEventHandler
    from utils import UTIL_SetOrigin
    
sv_gravity = ConVarRef('sv_gravity')
    
@entity('unit_fastzombie', networked=True)
class UnitFastZombie(BaseClass):    
    """ ZOMBIE  """
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 2048.0
        self.testroutestartheight = 2048.0
        
    if isserver:
        def Precache(self):
            super().Precache() 
            
            self.PrecacheModel("models/zombie/Fast_torso.mdl")
            self.PrecacheScriptSound( "NPC_FastZombie.CarEnter1" )
            self.PrecacheScriptSound( "NPC_FastZombie.CarEnter2" )
            self.PrecacheScriptSound( "NPC_FastZombie.CarEnter3" )
            self.PrecacheScriptSound( "NPC_FastZombie.CarEnter4" )
            self.PrecacheScriptSound( "NPC_FastZombie.CarScream" )

            self.PrecacheModel( "models/gibs/fast_zombie_torso.mdl" )
            self.PrecacheModel( "models/gibs/fast_zombie_legs.mdl" )
            
            self.PrecacheScriptSound( "NPC_FastZombie.LeapAttack" )
            self.PrecacheScriptSound( "NPC_FastZombie.FootstepRight" )
            self.PrecacheScriptSound( "NPC_FastZombie.FootstepLeft" )
            self.PrecacheScriptSound( "NPC_FastZombie.AttackHit" )
            self.PrecacheScriptSound( "NPC_FastZombie.AttackMiss" )
            self.PrecacheScriptSound( "NPC_FastZombie.LeapAttack" )
            self.PrecacheScriptSound( "NPC_FastZombie.Attack" )
            self.PrecacheScriptSound( "NPC_FastZombie.Idle" )
            self.PrecacheScriptSound( "NPC_FastZombie.AlertFar" )
            self.PrecacheScriptSound( "NPC_FastZombie.AlertNear" )
            self.PrecacheScriptSound( "NPC_FastZombie.GallopLeft" )
            self.PrecacheScriptSound( "NPC_FastZombie.GallopRight" )
            self.PrecacheScriptSound( "NPC_FastZombie.Scream" )
            self.PrecacheScriptSound( "NPC_FastZombie.RangeAttack" )
            self.PrecacheScriptSound( "NPC_FastZombie.Frenzy" )
            self.PrecacheScriptSound( "NPC_FastZombie.NoSound" )
            self.PrecacheScriptSound( "NPC_FastZombie.Die" )

            self.PrecacheScriptSound( "NPC_FastZombie.Gurgle" )

            self.PrecacheScriptSound( "NPC_FastZombie.Moan1" )
            
    def Spawn(self):
        super().Spawn()
        
        self.SetBloodColor(BLOOD_COLOR_ZOMBIE)
            
    '''def SetZombieModel(self):
        if self.istorso:
            self.SetModel("models/zombie/fast_torso.mdl")
        else:
            self.SetModel("models/zombie/fast.mdl")

        self.SetBodygroup(self.ZOMBIE_BODYGROUP_HEADCRAB, not self.isheadless)'''
        
    def AttackHitSound(self):
        """ Play a random attack hit sound """
        self.EmitSound( "NPC_FastZombie.AttackHit" )

    def AttackMissSound(self):
        """ Play a random attack miss sound """
        self.EmitSound("NPC_FastZombie.AttackMiss")
        
    def AttackRight(self, event):
        right = Vector()
        AngleVectors(self.GetLocalAngles(), None, right, None)
        right = right * -50
        attackinfo = self.unitinfo.AttackMelee
        self.ClawAttack(attackinfo.maxrange, attackinfo.damage, QAngle(-3, -5, -3), right, self.ZOMBIE_BLOOD_RIGHT_HAND)
        
    def AttackLeft(self, event):
        right = Vector()
        AngleVectors(self.GetLocalAngles(), None, right, None)
        right = right * 50
        attackinfo = self.unitinfo.AttackMelee
        self.ClawAttack(attackinfo.maxrange, attackinfo.damage, QAngle(-3, 5, -3), right, self.ZOMBIE_BLOOD_LEFT_HAND)
        
    def LeapAttackTouch(self, other):
        if not other.IsSolid():
            # Touching a trigger or something.
            return
            
        # Stop the zombie and knock the player back
        vecNewVelocity = Vector(0, 0, self.GetAbsVelocity().z)
        self.SetAbsVelocity(vecNewVelocity)

        forward = Vector()
        AngleVectors(self.GetLocalAngles(), forward)
        #qaPunch = QAngle(15, random.randint(-5,5), random.randint(-5,5))
        qaPunch = QAngle(-3, 5, -3)
        
        attackinfo = self.unitinfo.AttackRange
        self.ClawAttack(100.0, attackinfo.damage, qaPunch, forward * 500, self.ZOMBIE_BLOOD_BOTH_HANDS)

        self.SetTouch(None)
        
    def StartRangeAttack(self, enemy):
        self.SetTouch(self.LeapAttackTouch)
        return super().StartRangeAttack(enemy)
        
    def BeginAttackJump(self):
        # Set this to true. A little bit later if we fail to pathfind, we check
        #this value to see if we just jumped. If so, we assume we've jumped 
        # to someplace that's not pathing friendly, and so must jump again to get out.
        self.justjumped = True

        self.jumpstartaltitude = self.GetLocalOrigin().z

    CLAMP = 1200.0
    def LeapAttack(self, event=None):
        self.SetGroundEntity(None)

        self.BeginAttackJump()

        self.LeapAttackSound()

        #
        # Take him off ground so engine doesn't instantly reset FL_ONGROUND.
        #
        UTIL_SetOrigin(self, self.GetLocalOrigin() + Vector(0 , 0 , 1))

        pEnemy = self.enemy

        if pEnemy:
            vecEnemyPos = pEnemy.WorldSpaceCenter()

            gravity = sv_gravity.GetFloat()
            if gravity <= 1:
                gravity = 1

            #
            # How fast does the zombie need to travel to reach my enemy's eyes given gravity?
            #
            height = (vecEnemyPos.z - self.GetAbsOrigin().z)

            if height < 16:
                height = 16
            elif height > 120:
                height = 120
            
            speed = math.sqrt(2 * gravity * height)
            time = speed / gravity

            #
            # Scale the sideways velocity to get there at the right time
            #
            vecJumpDir = vecEnemyPos - self.GetAbsOrigin()
            vecJumpDir = vecJumpDir / time

            #
            # Speed to offset gravity at the desired height.
            #
            vecJumpDir.z = speed

            #
            # Don't jump too far/fast.
            #
            distance = vecJumpDir.Length()
            if distance > self.CLAMP:
                vecJumpDir = vecJumpDir * (self.CLAMP / distance)

            # try speeding up a bit.
            self.SetAbsVelocity( vecJumpDir )
            self.nextattack = gpGlobals.curtime + 2
    
    def LeapAttackSound(self):
        self.EmitSound("NPC_FastZombie.LeapAttack")
        
    def ShouldBecomeTorso(self, info, damagethreshold):
        if self.istorso:
            # Already split.
            return False

        # Break in half IF:
        if self.health <= 0:
            return True

        return False
        
    def BecomeTorso(self, vecTorsoForce, vecLegsForce):
        # TODO: Remove range attack

        self.ReleaseHeadcrab(self.EyePosition(), vecLegsForce * 0.5, True, True, True)

        super(FastZombie, self).BecomeTorso(vecTorsoForce, vecLegsForce)
        
    if isserver:
        # Anim events
        aetable = {
            'AE_ZOMBIE_ATTACK_RIGHT' : AttackRight,
            'AE_ZOMBIE_ATTACK_LEFT' : AttackLeft,
            'AE_FASTZOMBIE_LEAP' : LeapAttack,
            'AE_FASTZOMBIE_GALLOP_LEFT' : EmitSoundAnimEventHandler('NPC_FastZombie.GallopLeft'),
            'AE_FASTZOMBIE_GALLOP_RIGHT' : EmitSoundAnimEventHandler('NPC_FastZombie.GallopRight'),
            'AE_ZOMBIE_STEP_LEFT' : EmitSoundAnimEventHandler('NPC_FastZombie.FootstepLeft'),
            'AE_ZOMBIE_STEP_RIGHT' : EmitSoundAnimEventHandler('NPC_FastZombie.FootstepRight'),
            'AE_FASTZOMBIE_CLIMB_LEFT' : BaseAnimEventHandler(),
            'AE_FASTZOMBIE_CLIMB_RIGHT' : BaseAnimEventHandler(),
        }
    
    climbdismountz = 133.0
    dismounttolerancez = 16.0
    
    headcrabclassname = 'unit_headcrab_fast'
    
    istorso = False
    isheadless = False
        
class FastZombieInfo(BaseZombieInfo):
    name = 'unit_fastzombie'
    displayname = '#ZomFastZombie_Name'
    description = '#ZomFastZombie_Description'
    cls_name = 'unit_fastzombie'
    image_name = 'vgui/units/unit_shotgun.vmt'
    health = 150
    maxspeed = 224.0
    scrapdropchance = 0.0
    viewdistance = 896
    modelname = 'models/zombie/fast.mdl'
    torsomodel = 'models/zombie/fast_torso.mdl'
    torsogibmodel = 'models/gibs/fast_zombie_torso.mdl'
    legmodel = 'models/gibs/fast_zombie_legs.mdl'
    
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'patrol',
    }
    
    class AttackMelee(BaseZombieInfo.AttackMelee):
        maxrange = 50.0
        damage = 25
        damagetype = DMG_SLASH
        attackspeed = 0.5
    class AttackRange(BaseZombieInfo.AttackRange):
        minrange = 256.0
        maxrange = 720.0
        damage = 15
        damagetype = DMG_SLASH
        attackspeed = 2.0
        requiresmovement = True
    attacks = ['AttackMelee', 'AttackRange']
    