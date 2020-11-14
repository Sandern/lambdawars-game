#from srcbase import COLLISION_GROUP_NONE, MASK_SHOT, DMG_SHOCK, SURF_SKY, MAX_TRACE_LENGTH, DAMAGE_NO, MASK_WATER, DMG_GENERIC, MOVETYPE_VPHYSICS, FSOLID_NOT_SOLID, SOLID_VPHYSICS, DONT_BLEED
from srcbase import *
from vmath import (vec3_origin, Vector, QAngle, matrix3x4_t, AngleVectors, VectorAngles, VectorITransform, Approach,
                   AngleDiff, AngularImpulse, RandomAngularImpulse, clamp)
from entities import entity, CreateEntityByName
from core.units import BaseVehicleInfo, UnitBaseVehicle as BaseClass, UnitVehicleAnimState
from core.weapons import VECTOR_CONE_1DEGREES

from gameinterface import CPASAttenuationFilter, CPVSFilter, CPASFilter
from utils import trace_t, UTIL_TraceLine, UTIL_ImpactTrace, TRACER_DONT_USE_ATTACHMENT, UTIL_Tracer, UTIL_DecalTrace, UTIL_PointContents
from te import te
from entities import CBeam, FireBulletsInfo_t, FIRE_BULLETS_ALLOW_WATER_SURFACE_IMPACTS
from gamerules import GetAmmoDef
import ndebugoverlay

if isserver:
    from entities import CTakeDamageInfo, CalculateBulletDamageForce, ClearMultiDamage, ApplyMultiDamage, CLASS_NONE, CEntityFlame, SmokeTrail
    from core.units import BaseAction
    from utils import ExplosionCreate

import random

class UnitJeepAnimState(UnitVehicleAnimState):
    def OnNewModel(self):
        """ Setup pose parameters and other model related stuff """
        outer = self.outer
        studiohdr = outer.GetModelPtr()
        
        self.vehiclesteer = outer.LookupPoseParameter(studiohdr, "vehicle_steer")
        if self.vehiclesteer >= 0:
            outer.SetPoseParameter(studiohdr, self.vehiclesteer, 0.0)
        
        self.vehicleflspin = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_fl_spin")
        self.vehiclefrspin = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_fr_spin")
        self.vehiclerlspin = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_rl_spin")
        self.vehiclerrspin = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_rr_spin")
        
        self.vehicleflheight = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_fl_height")
        self.vehiclefrheight = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_fr_height")
        self.vehiclerlheight = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_rl_height")
        self.vehiclerrheight = outer.LookupPoseParameter(studiohdr, "vehicle_wheel_rr_height")
        
        self.jeepgunyaw = outer.LookupPoseParameter(studiohdr, "vehicle_weapon_yaw")
        self.jeepgunpitch = outer.LookupPoseParameter(studiohdr, "vehicle_weapon_pitch")
        self.jeepgunspin = outer.LookupPoseParameter(studiohdr, "gun_spin")
        
        outer.SetPoseParameter(self.jeepgunyaw, 0)
        outer.SetPoseParameter(self.jeepgunpitch, 0)
        outer.SetPoseParameter(self.jeepgunspin, 0)
        
    def Update(self, eyeYaw, eyePitch):
        super().Update(eyeYaw, eyePitch)
        
        outer = self.outer
        if outer.enemy:
            targetpos = outer.enemy.BodyTarget(outer.GetAbsOrigin())
            outer.AimGunAt(targetpos, self.GetAnimTimeInterval())
        
@entity('unit_jeep', networked=True)
class UnitJeep(BaseClass):
    hasgun = True
    
    enginelocked = False
    unabletofire = False
    cannoncharging = False
    cannontime = 0
    gunorigin = vec3_origin
    cannonchargestarttime = 0
    bullettype = 0
    ammotype = 0
    
    player = None
    aimyaw = 0
    aimpitch = 0
    spinpos = 0
    vecguncrosshair = None
    sndcannoncharge = None
    
    MAX_GAUSS_CHARGE_TIME = 3
    GAUSS_BEAM_SPRITE = "sprites/laserbeam.vmt"
    
    CANNON_MAX_UP_PITCH = 20
    CANNON_MAX_DOWN_PITCH = 20
    CANNON_MAX_LEFT_YAW = 90
    CANNON_MAX_RIGHT_YAW = 90
    JEEP_GUN_SPIN_RATE = 20
    
    def __init__(self):
        super().__init__()
        
        # Calls DoImpactEffect on server too from FireBullets (for beam drawing)
        self.serverdoimpactandtracer = True
        
        # Jeep model has a rotation of 90 degrees. Fix it here in code (but would prefer to have the model rotated).
        # This rotation will render the jeep model at this angle and correct the bone setup for this rotation.
        self.modelyawrotation = 90.0
    
    def Precache(self):
        super().Precache()
        
        self.PrecacheScriptSound('ATV_engine_idle')
        
        self.PrecacheScriptSound("PropJeep.AmmoClose")
        self.PrecacheScriptSound("PropJeep.FireCannon")
        self.PrecacheScriptSound("PropJeep.FireChargedCannon")
        self.PrecacheScriptSound("PropJeep.AmmoOpen")

        self.PrecacheScriptSound("Jeep.GaussCharge")
        
        self.PrecacheModel(self.GAUSS_BEAM_SPRITE)

        for chunkmodelname in self.chunkmodelnames:
            self.PrecacheModel(chunkmodelname)
        
    def Spawn(self):
        super().Spawn()
        
        ammodef = GetAmmoDef()
        self.bullettype = ammodef.Index("GaussEnergy")
        self.ammotype = ammodef.Index("GaussEnergy")
        
        if self.hasgun:
            self.SetBodygroup(1, True)
            
    def CreateComponents(self):
        super().CreateComponents()
        
        self.locomotion.stopspeed = 50
        self.locomotion.worldfriction = 2.2
        self.locomotion.acceleration = 2.5
            
    def UnitThink(self):
        super().UnitThink()
        
        weight = self.GetAbsVelocity().Length2D() / self.unitinfo.maxspeed
        self.mv.yawspeed = min(self.unitinfo.turnspeed * weight, self.unitinfo.turnspeed)
        
        enemy = self.enemy
        if enemy:
            #self.FireCannon()
            self.DoAnimation(self.ANIM_FIRE_GAUSS_CANNON)
        
    def AimGunAt(self, endPos, interval):
        ''' Aim Gun at a target. '''
        # Update gun origin
        dummy = QAngle()
        self.GetAttachment( "Muzzle", self.gunorigin, dummy)
        #ndebugoverlay.Box(self.gunorigin, -Vector(8,8,8), Vector(8,8,8), 255 if isclient else 0, 255 if isserver else 0, 0, 255, 0.2)
            
        self.unabletofire = False
        
        aimPos = Vector(endPos)

        jeepgunyaw = self.animstate.jeepgunyaw
        jeepgunpitch = self.animstate.jeepgunpitch
        jeepgunspin = self.animstate.jeepgunspin
        
        # See if the gun should be allowed to aim
        if self.IsOverturned() or self.enginelocked or self.hasgun == False:
            self.SetPoseParameter(jeepgunyaw, 0)
            self.SetPoseParameter(jeepgunpitch, 0)
            self.SetPoseParameter(jeepgunspin, 0)
            return

            # Make the gun go limp and look "down"
            v_forward = Vector(); v_up = Vector()
            AngleVectors(self.GetLocalAngles(), None, v_forward, v_up)
            aimPos = self.WorldSpaceCenter() + (v_forward * -32.0) - Vector(0, 0, 128.0)

        gunMatrix = matrix3x4_t()
        self.GetAttachment(self.LookupAttachment("gun_ref"), gunMatrix)

        # transform the enemy into gun space
        localEnemyPosition = Vector()
        VectorITransform(aimPos, gunMatrix, localEnemyPosition)

        # do a look at in gun space (essentially a delta-lookat)
        localEnemyAngles = QAngle()
        VectorAngles(localEnemyPosition, localEnemyAngles)
        
        # convert to +/- 180 degrees
        localEnemyAngles.x = AngleDiff( localEnemyAngles.x, 0 )
        localEnemyAngles.y = AngleDiff( localEnemyAngles.y, 0 )

        targetYaw = self.aimyaw + localEnemyAngles.y
        targetPitch = self.aimpitch + localEnemyAngles.x
        
        # Constrain our angles
        newTargetYaw = clamp( targetYaw, -self.CANNON_MAX_LEFT_YAW, self.CANNON_MAX_RIGHT_YAW )
        newTargetPitch = clamp( targetPitch, -self.CANNON_MAX_DOWN_PITCH, self.CANNON_MAX_UP_PITCH )

        # If the angles have been clamped, we're looking outside of our valid range
        if abs(newTargetYaw-targetYaw) > 1e-4 or abs(newTargetPitch-targetPitch) > 1e-4:
            self.unabletofire = True

        targetYaw = newTargetYaw
        targetPitch = newTargetPitch

        # Exponentially approach the target
        yawSpeed = 8
        pitchSpeed = 8

        self.aimyaw = Approach(targetYaw, self.aimyaw, yawSpeed)
        self.aimpitch = Approach(targetPitch, self.aimpitch, pitchSpeed)

        self.SetPoseParameter(jeepgunyaw, -self.aimyaw)
        self.SetPoseParameter(jeepgunpitch, -self.aimpitch )

        self.InvalidateBoneCache()

        # read back to avoid drift when hitting limits
        # as long as the velocity is less than the delta between the limit and 180, self is fine.
        self.aimpitch = -self.GetPoseParameter(jeepgunpitch)
        self.aimyaw = -self.GetPoseParameter(jeepgunyaw)

        # Now draw crosshair for actual aiming point
        vecMuzzle = Vector(); vecMuzzleDir = Vector()
        vecMuzzleAng = QAngle()

        self.GetAttachment("Muzzle", vecMuzzle, vecMuzzleAng)
        
        AngleVectors(vecMuzzleAng, vecMuzzleDir)

        tr = trace_t()
        UTIL_TraceLine(vecMuzzle, vecMuzzle + (vecMuzzleDir * MAX_TRACE_LENGTH), MASK_SHOT, self, COLLISION_GROUP_NONE, tr)
        
        # see if we hit something, if so, adjust endPos to hit location
        if tr.fraction < 1.0:
            self.vecguncrosshair = vecMuzzle + (vecMuzzleDir * MAX_TRACE_LENGTH * tr.fraction)
            
    def DoImpactEffect(self, tr, nDamageType):
        # Draw our beam
        self.DrawBeam(tr.startpos, tr.endpos, 2.4)
        
        if (tr.surface.flags & SURF_SKY) == False:
            filter = CPVSFilter(tr.endpos)
            te.GaussExplosion(filter, 0.0, tr.endpos, tr.plane.normal, 0)

            UTIL_ImpactTrace(tr, self.bullettype)
        
    def DrawBeam(self, startPos, endPos, width):
        if isclient:
            # Tracer down the middle
            UTIL_Tracer(startPos, endPos, 0, TRACER_DONT_USE_ATTACHMENT, 6500, False, "GaussTracer")
        else:
            #Draw the main beam shaft
            beam = CBeam.BeamCreate(self.GAUSS_BEAM_SPRITE, 0.5)
            
            beam.SetStartPos( startPos )
            beam.PointEntInit( endPos, self )
            beam.SetEndAttachment(self.LookupAttachment("Muzzle"))
            beam.SetWidth( width )
            beam.SetEndWidth( 0.05 )
            beam.SetBrightness( 255 )
            beam.SetColor( 255, 185+random.randint( -16, 16 ), 40 )
            beam.RelinkBeam()
            beam.LiveForTime( 0.1 )

            #Draw electric bolts along shaft
            beam = CBeam.BeamCreate(self.GAUSS_BEAM_SPRITE, 3.0)
            
            beam.SetStartPos( startPos )
            beam.PointEntInit( endPos, self )
            beam.SetEndAttachment(self.LookupAttachment("Muzzle") )

            beam.SetBrightness( random.randint( 64, 255 ) )
            beam.SetColor( 255, 255, 150+random.randint( 0, 64 ) )
            beam.RelinkBeam()
            beam.LiveForTime( 0.1 )
            beam.SetNoise( 1.6 )
            beam.SetEndWidth( 0.1 )

    # NVNT Convar for jeep cannon magnitude
    #hap_jeep_cannon_mag = ConVar("hap_jeep_cannon_mag", "10", 0)
    
    def EventHandlerFireGaussCannon(self, data):
        self.FireCannon()

    def FireCannon(self):
        #Don't fire again if it's been too soon
        if self.cannontime > gpGlobals.curtime:
            return
            
        if self.unabletofire:
            return

        self.cannontime = gpGlobals.curtime + 0.2
        self.cannoncharging = False

        #Find the direction the gun is pointing in
        aimDir = Vector()
        self.GetCannonAim(aimDir)

    #if defined( WIN32 ) and !defined( _X360 ) 
        # NVNT apply a punch on fire
        #HapticPunch(self.player,0,0,hap_jeep_cannon_mag.GetFloat())
    #endif
        info = FireBulletsInfo_t(1, self.gunorigin, aimDir, VECTOR_CONE_1DEGREES, MAX_TRACE_LENGTH, self.ammotype)

        info.flags = FIRE_BULLETS_ALLOW_WATER_SURFACE_IMPACTS
        info.attacker = self.player

        self.FireBullets(info)

        # Register a muzzleflash for the AI
        #if self.player:
        #    self.player.SetMuzzleFlashTime(gpGlobals.curtime + 0.5)
        #    self.player.RumbleEffect(RUMBLE_PISTOL, 0, RUMBLE_FLAG_RESTART)

        sndFilter = CPASAttenuationFilter(self, "PropJeep.FireCannon")
        self.EmitSoundFilter(sndFilter, self.entindex(), "PropJeep.FireCannon")
        
        # make cylinders of gun spin a bit
        self.spinpos = self.spinpos + self.JEEP_GUN_SPIN_RATE
        #SetPoseParameter( JEEP_GUN_SPIN, self.spinpos )	#FIXME: Don't bother with this for E3, won't look right
        
    def FireChargedCannon(self):
        penetrated = False

        self.cannoncharging = False
        self.cannontime = gpGlobals.curtime + 0.5

        self.StopChargeSound()

        sndFilter = CPASAttenuationFilter( self, "PropJeep.FireChargedCannon" )
        self.EmitSoundFilter(sndFilter, self.entindex(), "PropJeep.FireChargedCannon")

        #if self.player:
        #    self.player.RumbleEffect(RUMBLE_357, 0, RUMBLE_FLAG_RESTART)

        #Find the direction the gun is pointing in
        aimDir = Vector()
        self.GetCannonAim(aimDir)

        endPos = self.gunorigin + (aimDir * MAX_TRACE_LENGTH)
        
        #Shoot a shot straight out
        tr = trace_t()
        UTIL_TraceLine(self.gunorigin, endPos, MASK_SHOT, self, COLLISION_GROUP_NONE, tr)
        
        ClearMultiDamage()

        #Find how much damage to do
        flChargeAmount = (gpGlobals.curtime - self.cannonchargestarttime) / self.MAX_GAUSS_CHARGE_TIME

        #Clamp self
        if flChargeAmount > 1.0:
            flChargeAmount = 1.0

        #Determine the damage amount
        #FIXME: Use ConVars!
        flDamage = 15 + ( ( 250 - 15 ) * flChargeAmount )

        pHit = tr.m_pEnt
        
        #Look for wall penetration
        if tr.DidHitWorld() and not (tr.surface.flags & SURF_SKY):
            #Try wall penetration
            UTIL_ImpactTrace(tr, self.bullettype, "ImpactJeep")
            UTIL_DecalTrace(tr, "RedGlowFade")

            filter = CPVSFilter( tr.endpos )
            te.GaussExplosion( filter, 0.0, tr.endpos, tr.plane.normal, 0 )
            
            testPos = tr.endpos + (aimDir * 48.0)
            
            UTIL_TraceLine(testPos, tr.endpos, MASK_SHOT, self.GetDriver(), COLLISION_GROUP_NONE, tr)
                
            if tr.allsolid == False:
                UTIL_DecalTrace(tr, "RedGlowFade")

                penetrated = True
        elif pHit != None:
            dmgInfo = CTakeDamageInfo(self, self.GetDriver(), flDamage, DMG_SHOCK)
            CalculateBulletDamageForce(dmgInfo, GetAmmoDef().Index("GaussEnergy"), aimDir, tr.endpos, 1.0 + flChargeAmount * 4.0)

            #Do direct damage to anything in our path
            pHit.DispatchTraceAttack(dmgInfo, aimDir, tr)

        ApplyMultiDamage()

        #Kick up an effect
        if not (tr.surface.flags & SURF_SKY):
            UTIL_ImpactTrace(tr, self.bullettype, "ImpactJeep")

            #Do a gauss explosion
            filter = CPVSFilter(tr.endpos)
            te.GaussExplosion(filter, 0.0, tr.endpos, tr.plane.normal, 0)
            
        #Show the effect
        self.DrawBeam(self.gunorigin, tr.endpos, 9.6)

        # Register a muzzleflash for the AI
        if self.player:
            self.player.SetMuzzleFlashTime(gpGlobals.curtime + 0.5)

        #Rock the car
        pObj = self.VPhysicsGetObject()

        if pObj != None:
            shoveDir = aimDir * -(flDamage * 500.0)

            pObj.ApplyForceOffset(shoveDir, self.gunorigin)

        #Do radius damage if we didn't penetrate the wall
        if penetrated == True:
            RadiusDamage(CTakeDamageInfo(self, self, flDamage, DMG_SHOCK), tr.endpos, 200.0, CLASS_NONE, None)

    def ChargeCannon(self):
        #Don't fire again if it's been too soon
        if self.cannontime > gpGlobals.curtime:
            return

        #See if we're starting a charge
        if self.cannoncharging == False:
            self.cannonchargestarttime = gpGlobals.curtime
            self.cannoncharging = True

            #Start charging sound
            filter = CPASAttenuationFilter(self)
            self.sndcannoncharge = (CSoundEnvelopeController.GetController()).SoundCreate(filter, self.entindex(), CHAN_STATIC, "Jeep.GaussCharge", ATTN_NORM)

            #if self.player:
            #    self.player.RumbleEffect(RUMBLE_FLAT_LEFT, int(0.1 * 100), RUMBLE_FLAG_RESTART | RUMBLE_FLAG_LOOP | RUMBLE_FLAG_INITIAL_SCALE)

            assert(self.sndcannoncharge!=None)
            if self.sndcannoncharge != None:
                (CSoundEnvelopeController.GetController()).Play(self.sndcannoncharge, 1.0, 50)
                (CSoundEnvelopeController.GetController()).SoundChangePitch(self.sndcannoncharge, 250, 3.0)
            return
        else:
            flChargeAmount = ( gpGlobals.curtime - self.cannonchargestarttime ) / self.MAX_GAUSS_CHARGE_TIME
            if flChargeAmount > 1.0:
                flChargeAmount = 1.0

            rumble = flChargeAmount * 0.5

            #if self.player:
            #    self.player.RumbleEffect( RUMBLE_FLAT_LEFT, int(rumble * 100), RUMBLE_FLAG_UPDATE_SCALE )

        #TODO: Add muzzle effect?

        #TODO: Check for overcharge and have the weapon simply fire or instead "decharge"?
        
    def StopChargeSound(self):
        if self.sndcannoncharge != None:
            (CSoundEnvelopeController.GetController()).SoundFadeOut(self.sndcannoncharge, 0.1)

        #if self.player:
        #    self.player.RumbleEffect( RUMBLE_FLAT_LEFT, 0, RUMBLE_FLAG_STOP )
    
    def GetCannonAim(self, resultDir):
        ''' Finds the True aiming position of the gun (looks at what player 
            is looking at and adjusts)
            
            Args:
                resultDir(Vector): direction to be calculated
        '''
        muzzleOrigin = Vector()
        muzzleAngles = QAngle()

        self.GetAttachment(self.LookupAttachment("gun_ref"), muzzleOrigin, muzzleAngles)
        
        AngleVectors(muzzleAngles, resultDir)

    def BecomePhysical(self):
        self.VPhysicsDestroyObject()

        self.RemoveSolidFlags(FSOLID_NOT_SOLID)

        # Setup the physics controller on the roller
        phys_obj = self.VPhysicsInitNormal(SOLID_VPHYSICS, self.GetSolidFlags(), False)

        if phys_obj is None:
            return False

        # Lomotion component acts as controller for VPhysics
        #self.locomotion.CreateMotionController()

        self.SetMoveType(MOVETYPE_VPHYSICS)

        phys_obj.Wake()

        return True

    def Hop(self, height):
        if self.nexthop > gpGlobals.curtime:
            return

        if self.GetMoveType() == MOVETYPE_VPHYSICS:
            pPhysObj = self.VPhysicsGetObject()
            pPhysObj.ApplyForceCenter(Vector(random.uniform(-1, 1), random.uniform(1, -1), 1) * height * pPhysObj.GetMass())

            angVel = AngularImpulse()
            angVel.Random(-400.0, 400.0)
            pPhysObj.AddVelocity(None, angVel)

            self.nexthop = gpGlobals.curtime + self.ROLLERMINE_HOP_DELAY
            ExplosionCreate(self.WorldSpaceCenter(), self.GetLocalAngles(), self, 0, 0, True)

    def PreDetonate(self):
        """ Makes warning noise before actual explosion occurs """
        self.BecomePhysical()
        self.Hop(500)

        self.SetTouch(None)
        self.SetThink(self.Explode)
        self.SetNextThink(gpGlobals.curtime + 0.5)

        self.EmitSound("NPC_RollerMine.Hurt")

    def Explode(self):
        self.takedamage = DAMAGE_NO

        # FIXME: Hack to make thrown mines more deadly and fun
        expDamage = 0 if self.isprimed else 25

        # If we've been hacked and we're blowing up cause we've been shut down then do moderate damage.
        if self.powerdown == True:
            expDamage = 0

        # Underwater explosion?
        if UTIL_PointContents(self.GetAbsOrigin(), MASK_WATER):
            data = CEffectData()
            data.origin = self.WorldSpaceCenter()
            data.magnitude = expDamage
            data.scale = 128
            data.flags = (SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSMOKE)
            DispatchEffect("WaterSurfaceExplosion", data)
        else:
            ExplosionCreate(self.WorldSpaceCenter(), self.GetLocalAngles(), self, expDamage, 0, True)

        info = CTakeDamageInfo(self, self, 1, DMG_GENERIC)
        self.Event_Killed(info)

        # Remove myself a frame from now to avoid doing it in the middle of running AI
        self.SetThink(self.SUB_Remove)
        self.SetNextThink(gpGlobals.curtime)
        self.ThrowFlamingGib()
        self.ThrowFlamingGib()
        self.ThrowFlamingGib()
        self.ThrowFlamingGib()

    def ThrowFlamingGib(self):
        ''' Character killed (only fired once) '''
        vecAbsMins = Vector();
        vecAbsMaxs = Vector()
        self.CollisionProp().WorldSpaceAABB(vecAbsMins, vecAbsMaxs)

        vecNormalizedMins = Vector();
        vecNormalizedMaxs = Vector()
        self.CollisionProp().WorldToNormalizedSpace(vecAbsMins, vecNormalizedMins)
        self.CollisionProp().WorldToNormalizedSpace(vecAbsMaxs, vecNormalizedMaxs)

        vecAbsPoint = Vector()
        filter = CPASFilter(self.GetAbsOrigin())
        self.CollisionProp().RandomPointInBounds(vecNormalizedMins, vecNormalizedMaxs, vecAbsPoint)

        # Throw a flaming, smoking chunk.
        pChunk = CreateEntityByName("gib")
        pChunk.Spawn("models/gibs/hgibs.mdl")
        pChunk.SetBloodColor(DONT_BLEED)

        vecSpawnAngles = QAngle()
        vecSpawnAngles.Random(-90, 90)
        pChunk.SetAbsOrigin(vecAbsPoint)
        pChunk.SetAbsAngles(vecSpawnAngles)

        nGib = random.randint(0, len(self.chunkmodelnames) - 1)
        pChunk.Spawn(self.chunkmodelnames[nGib])
        pChunk.SetOwnerEntity(self)
        pChunk.lifetime = random.uniform(6.0, 8.0)
        pChunk.SetCollisionGroup(COLLISION_GROUP_DEBRIS)
        pPhysicsObject = pChunk.VPhysicsInitNormal(SOLID_VPHYSICS, pChunk.GetSolidFlags(), False)

        # Set the velocity
        if pPhysicsObject:
            pPhysicsObject.EnableMotion(True)
            vecVelocity = Vector()

            angles = QAngle()
            angles.x = random.uniform(-20, 20)
            angles.y = random.uniform(0, 360)
            angles.z = 0.0
            AngleVectors(angles, vecVelocity)

            vecVelocity *= random.uniform(300, 900)
            vecVelocity += self.GetAbsVelocity()

            angImpulse = AngularImpulse()
            angImpulse = RandomAngularImpulse(-180, 180)

            pChunk.SetAbsVelocity(vecVelocity)
            pPhysicsObject.SetVelocity(vecVelocity, angImpulse)

        pFlame = CEntityFlame.Create(pChunk, False)
        if pFlame != None:
            pFlame.SetLifetime(pChunk.lifetime)

        pSmokeTrail = SmokeTrail.CreateSmokeTrail()
        if pSmokeTrail:
            pSmokeTrail.spawnrate = 80
            pSmokeTrail.particlelifetime = 0.8
            pSmokeTrail.startcolor = Vector(0.3, 0.3, 0.3)
            pSmokeTrail.endcolor = Vector(0.5, 0.5, 0.5)
            pSmokeTrail.startsize = 10
            pSmokeTrail.endsize = 40
            pSmokeTrail.spawnradius = 5
            pSmokeTrail.opacity = 0.4
            pSmokeTrail.minspeed = 15
            pSmokeTrail.maxspeed = 25
            pSmokeTrail.SetLifetime(pChunk.lifetime)
            pSmokeTrail.SetParent(pChunk, 0)
            pSmokeTrail.SetLocalOrigin(vec3_origin)
            pSmokeTrail.SetMoveType(MOVETYPE_NONE)

    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionDie(BaseAction):
                def OnStart(self):
                    # Will remove the unit after explode:
                    self.outer.PreDetonate()
    
    AnimStateClass = UnitJeepAnimState
    nexthop = 0.0
    ROLLERMINE_HOP_DELAY = 2
    isprimed = False
    powerdown = False
    
    events = dict(BaseClass.events)
    events.update({
        'ANIM_FIRE_GAUSS_CANNON' : EventHandlerFireGaussCannon,
    })

    chunkmodelnames = [
        'models\props_vehicles\carparts_wheel01a.mdl',
        'models\props_vehicles\carparts_wheel01a.mdl',
        'models\props_vehicles\carparts_wheel01a.mdl',
    ]
    
    scaleprojectedtexture = 1.7
    
class JeepInfo(BaseVehicleInfo):
    name = 'unit_jeep'
    cls_name = 'unit_jeep'
    modelname = 'models/buggy.mdl'
    hulltype = 'HULL_LARGE'
    health = 500
    maxspeed = 500
    turnspeed = 6.0

    """class AttackMelee(UnitInfo.AttackMelee):
        damage = 200
        damagetype = DMG_SLASH
        attackspeed = 0.3"""
    