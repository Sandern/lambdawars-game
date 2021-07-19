from srcbase import *
from vmath import Vector, QAngle, AngleVectors, vec3_angle
import random
from .basezombie import BaseZombieInfo, UnitBaseZombie as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t, TranslateActivityMap
from entities import entity, Activity
from animation import EventList_RegisterPrivateEvent

from core.units import CreateUnitNoSpawn
    
if isserver:
    from utils import UTIL_Remove
    from unit_helper import EmitSoundAnimEventHandler
    
@entity('unit_poisonzombie', networked=True)
class UnitPoisonZombie(BaseClass):
    if isserver:
        def Precache(self):
            self.PrecacheScriptSound( "NPC_PoisonZombie.Die" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.ThrowWarn" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.Throw" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.Idle" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.Pain" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.Alert" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.FootstepRight" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.FootstepLeft" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.Attack" )

            self.PrecacheScriptSound( "NPC_PoisonZombie.FastBreath" )
            self.PrecacheScriptSound( "NPC_PoisonZombie.Moan1" )

            self.PrecacheScriptSound( "Zombie.AttackHit" )
            self.PrecacheScriptSound( "Zombie.AttackMiss" )
    
            super().Precache() 
            
        def Spawn(self):
            super().Spawn()
            
            self.SetBloodColor(BLOOD_COLOR_ZOMBIE)
            
            self.istorso = False
            self.isheadless = False
            
            # Enable crabs
            self.crabs = [False] * self.MAX_CRABS
            
            nCrabs = self.crabcount
            if not nCrabs:
                nCrabs = self.MAX_CRABS
            self.crabcount = 0

            #
            # Generate a random set of crabs based on the crab count
            # specified by the level designer.
            #
            nBits = [
                # One bit
                0x01,
                0x02,
                0x04,

                # Two bits
                0x03,
                0x05,
                0x06,
            ]

            nBitMask = 7
            if nCrabs == 1:
                nBitMask = nBits[random.randint(0, 2)]
            elif nCrabs == 2:
                nBitMask = nBits[random.randint(3, 5)]

            for i in range(0, self.MAX_CRABS):
                self.EnableCrab(i, (nBitMask & ( 1 << i )) != 0)
            
    def AttackHitSound(self):
        """ Play a random attack hit sound """
        self.EmitSound( "Zombie.AttackHit" )

    def AttackMissSound(self):
        """ Play a random attack miss sound """
        self.EmitSound("Zombie.AttackMiss")
            
    def Event_Killed(self, info):
        if not (info.GetDamageType() & (DMG_BLAST | DMG_ALWAYSGIB)):
            self.EmitSound("NPC_PoisonZombie.Die")

        if not self.istorso and not self.IsOnFire() and not (info.GetDamageType() & DMG_BLAST):
            self.EvacuateNest(info.GetDamageType() == DMG_BLAST, info.GetDamage(), info.GetAttacker())

        super().Event_Killed(info)
            
    def PickupHeadCrab(self, event):
        self.EnableCrab(self.throwcrab, False)
        self.SetBodygroup(self.ZOMBIE_BODYGROUP_THROW, 1)
            
    def ThrowHeadCrab(self, event):
        self.SetBodygroup(self.ZOMBIE_BODYGROUP_THROW, 0)

        pCrab = CreateUnitNoSpawn(self.headcrabclassname, self.GetOwnerNumber())
        pCrab.SetAbsOrigin(self.EyePosition())
        pCrab.SetOwnerEntity(self)
        #pCrab.AddSpawnFlags(SF_NPC_FALL_TO_GROUND)
        
        # Fade if our parent is supposed to
        #if self.HasSpawnFlags(SF_NPC_FADE_CORPSE):
        #    pCrab.AddSpawnFlags(SF_NPC_FADE_CORPSE)

        # make me the crab's owner to avoid collision issues
        pCrab.SetOwnerEntity(self)

        pCrab.Spawn()

        pCrab.SetLocalAngles( self.GetLocalAngles() )
        pCrab.DoAnimation(pCrab.ANIM_RANGE_ATTACK1)
        pCrab.SetNextThink( gpGlobals.curtime )
        pCrab.PhysicsSimulate()

        #pCrab.GetMotor().SetIdealYaw( GetAbsAngles().y )

        if self.IsOnFire():
            pCrab.Ignite(100.0)

        pEnemy = self.enemy
        if pEnemy:
            vecEnemyEyePos = pEnemy.EyePosition()
            pCrab.ThrowAt(vecEnemyEyePos)

        #if self.crabcount == 0:
        #    CapabilitiesRemove( bits_CAP_INNATE_RANGE_ATTACK1 | bits_CAP_INNATE_RANGE_ATTACK2 )

        self.nextcrabthrowtime = gpGlobals.curtime + random.randint(self.ZOMBIE_THROW_MIN_DELAY, self.ZOMBIE_THROW_MAX_DELAY)
        
    #-----------------------------------------------------------------------------
    # Purpose: Turns the given crab on or off.
    #-----------------------------------------------------------------------------
    def EnableCrab(self, nCrab, bEnable):
        assert((nCrab >= 0) and (nCrab < self.MAX_CRABS))

        if (nCrab >= 0) and (nCrab < self.MAX_CRABS):
            if self.crabs[nCrab] != bEnable:
                self.crabcount += 1 if bEnable else -1

            self.crabs[nCrab] = bEnable
            self.SetBodygroup(self.ZOMBIE_BODYGROUP_NEST_BASE + nCrab, bEnable)

    #-----------------------------------------------------------------------------
    # Purpose: Returns the index of a randomly chosen crab to throw.
    #-----------------------------------------------------------------------------
    def RandomThrowCrab(self):
        # FIXME: this could take a long time, theoretically
        nCrab = -1
        while nCrab == -1:
            nTest = random.randint(0, 2)
            if self.crabs[nTest]:
                nCrab = nTest
        return nCrab

    #-----------------------------------------------------------------------------
    # Purpose: The nest is dead! Evacuate the nest!
    # Input  : bExplosion - We were evicted by an explosion so we should go a-flying.
    #			flDamage - The damage that was done to cause the evacuation.
    #-----------------------------------------------------------------------------
    def EvacuateNest(self, bExplosion, flDamage, pAttacker):
        # HACK: if we were in mid-throw, drop the throwing crab also.
        if self.GetBodygroup(self.ZOMBIE_BODYGROUP_THROW):
            self.SetBodygroup(self.ZOMBIE_BODYGROUP_THROW, 0)
            self.crabcount += 1
        

        for i in range(0, self.MAX_CRABS):
            if self.crabs[i]:
                vecPosition = Vector()
                vecAngles = QAngle()

                szAttachment = 'headcrab%d' % (i)
                self.GetAttachment( szAttachment, vecPosition, vecAngles )

                # Now slam the angles because the attachment point will have pitch and roll, which we can't use.
                vecAngles = QAngle(0, random.uniform( 0, 360 ), 0)

                pCrab = CreateUnitNoSpawn(self.headcrabclassname, self.GetOwnerNumber())
                pCrab.SetAbsOrigin(vecPosition)
                pCrab.SetAbsAngles(vecAngles)
                pCrab.SetOwnerEntity(self)
                pCrab.Spawn()

                if not self.HeadcrabFits(pCrab):
                    UTIL_Remove(pCrab)
                    continue
                
                flVelocityScale = 2.0
                if bExplosion and (flDamage > 10):
                    flVelocityScale = 0.1 * flDamage

                if self.IsOnFire():
                    pCrab.Ignite(100.0)

                pCrab.Eject(vecAngles, flVelocityScale, pAttacker)
                self.EnableCrab(i, False)
                
    def PoisonSpit(self, event):
        forward = Vector()
        qaPunch = QAngle(45, random.randint(-5, 5), random.randint(-5, 5))
        AngleVectors(self.GetLocalAngles(), forward)
        forward = forward * 200
        ClawAttack( GetClawAttackRange(), sk_zombie_poison_dmg_spit.GetFloat(), qaPunch, forward, ZOMBIE_BLOOD_BITE )
        attackinfo = self.unitinfo.AttackMelee
        self.ClawAttack(attackinfo.maxrange, attackinfo.damage, qaPunch, right + forward, self.ZOMBIE_BLOOD_BITE)
        
    # Activity translation table
    acttables = {
        Activity.ACT_RUN : Activity.ACT_WALK,
    }
    
    if isserver:
        # Anim events
        aetable = dict(BaseClass.aetable)
        aetable.update({
            'AE_ZOMBIE_POISON_THROW_WARN_SOUND' : EmitSoundAnimEventHandler('NPC_PoisonZombie.ThrowWarn'),
            'AE_ZOMBIE_POISON_PICKUP_CRAB' : 'PickupHeadCrab',
            'AE_ZOMBIE_POISON_THROW_SOUND' : EmitSoundAnimEventHandler('NPC_PoisonZombie.Throw'),
            'AE_ZOMBIE_POISON_THROW_CRAB' : 'ThrowHeadCrab',
            'AE_ZOMBIE_POISON_SPIT' : 'PoisonSpit',
            'AE_ZOMBIE_STEP_LEFT' : EmitSoundAnimEventHandler('NPC_PoisonZombie.FootstepLeft'),
            'AE_ZOMBIE_STEP_RIGHT' : EmitSoundAnimEventHandler('NPC_PoisonZombie.FootstepRight'),
            'AE_ZOMBIE_ATTACK_SCREAM' : EmitSoundAnimEventHandler('NPC_PoisonZombie.Attack'),
        })
                
    crabcount = 0
    throwcrab = 0
    nextcrabthrowtime = 0.0
    headcrabclassname = 'unit_headcrab_poison'
        
    ZOMBIE_BODYGROUP_NEST_BASE = 2 # First nest crab, +2 more
    ZOMBIE_BODYGROUP_THROW = 5 # The crab in our hand for throwing

    ZOMBIE_ENEMY_BREATHE_DIST = 300 # How close we must be to our enemy before we start breathing hard.
    
    # Controls how soon he throws the first headcrab after seeing his enemy (also when the first headcrab leaps off)
    ZOMBIE_THROW_FIRST_MIN_DELAY = 1 # min seconds before first crab throw
    ZOMBIE_THROW_FIRST_MAX_DELAY = 2 # max seconds before first crab throw

    # Controls how often he throws headcrabs (also how often headcrabs leap off)
    ZOMBIE_THROW_MIN_DELAY = 4 # min seconds between crab throws
    ZOMBIE_THROW_MAX_DELAY = 10 # max seconds between crab throws
    
    MAX_CRABS = 3
    
@entity('unit_poisonzombieboss')
class UnitPoisonZombieBoss(UnitPoisonZombie):
    def ThrowHeadCrab(self, event):
        for i in range(0, 6):
            super(UnitPoisonZombieBoss, self).ThrowHeadCrab(event)
            
class PoisonZombieInfo(BaseZombieInfo):
    name = 'unit_poisonzombie'
    displayname = '#ZomPoisonZombie_Name'
    description = '#ZomPoisonZombie_Description'
    cls_name = 'unit_poisonzombie'
    image_name = 'vgui/units/unit_shotgun.vmt'
    health = 600
    maxspeed = 50.0
    scrapdropchance = 0.0
    modelname = 'models/Zombie/poison.mdl'
    legmodel = 'models/zombie/classic_legs.mdl'
    torsomodel = 'models/zombie/classic_torso.mdl'
    torsogibmodel = 'models/zombie/classic_torso.mdl'
    attributes = ['heavy', 'slash']
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'patrol',
    }
    
    class AttackMelee(BaseZombieInfo.AttackMelee):
        maxrange = 55.0
        damage = 150
        damagetype = DMG_SLASH
        attackspeed = 1.9
        
    class AttackRange(BaseZombieInfo.AttackRange):
        maxrange = 620.0
        
        nextattacktime = 0.0
        
        def ShouldUpdateAttackInfo(self, unit): 
            return self.nextattacktime < gpGlobals.curtime and self.unit.MAX_CRABS > 1

        def CanAttack(self, enemy):
            if self.nextattacktime > gpGlobals.curtime:
                return False
            if self.unit.IsOnFire():
                return False
            if self.unit.stunned:
                return False
            if self.unit.MAX_CRABS < 2:
                return False
            return self.unit.CanRangeAttack(enemy)

        def Attack(self, enemy, action):
            self.nextattacktime = gpGlobals.curtime + 6.0
            self.unit.MAX_CRABS = self.unit.MAX_CRABS - 1
            return super().Attack(enemy, action)

    attacks = ['AttackMelee', 'AttackRange']

class PoisonZombieBossInfo(PoisonZombieInfo):
    name = 'unit_poisonzombieboss'
    cls_name = 'unit_poisonzombieboss'
    displayname = '#ZomPoisonZombieBoss_Name'
    description = '#ZomPoisonZombieBoss_Description'
    health = 2200
    scrapdropchance = 0.0
    scale = 1.5
    maxspeed = 80.0
    turnspeed = 120
    
    class AttackRange(PoisonZombieInfo.AttackRange):
        def Attack(self, enemy, action):
            self.nextattacktime = gpGlobals.curtime + 3.0
            self.unit.MAX_CRABS = self.unit.MAX_CRABS - 1
            return super().Attack(enemy, action)
