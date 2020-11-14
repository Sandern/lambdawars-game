from srcbase import *
from vmath import *
from .basehelicopter import BaseHelicopter as BaseClass, UnitBaseHelicopterAnimState
from core.units import UnitInfo, EventHandlerAnimation
from core.weapons import VECTOR_CONE_5DEGREES
from entities import entity, FireBulletsInfo_t, CalculateBulletDamageForce, TRACER_LINE
from utils import UTIL_VecToYaw, UTIL_VecToPitch, trace_t, UTIL_Tracer, TRACER_DONT_USE_ATTACHMENT
from sound import CSoundEnvelopeController
from gameinterface import CPASAttenuationFilter, PrecacheMaterial, ConVar
from unit_helper import UnitAnimConfig, LegAnimType_t
from gamerules import GetAmmoDef
import random
from te import CEffectData, DispatchEffect

if isserver:
    from utils import UTIL_PrecacheOther
    from entities import PropBreakablePrecacheAll
    from utils import UTIL_PredictedPosition
    
# FIXME
PITCH = 0 # up / down
YAW = 1 #left / right
ROLL = 2 # fall over

class UnitBaseGunshipAnimState(UnitBaseHelicopterAnimState):
    def __init__(self, outer, *args, **kwargs):
        super().__init__(outer)
        
        self.anggun = QAngle(0,0,0)
    
    def Update(self, eyeyaw, eyepitch):
        super().Update(eyeyaw, eyepitch)
    
        outer = self.outer
        enemy = outer.enemy
        
        # GetAnimTimeInterval returns gpGlobals.frametime on client, and interval between main think (non context) on server
        interval = self.GetAnimTimeInterval()

        self.MoveHead(interval)
        
        if outer.enemy:
            outer.attackposition = outer.enemy.EyePosition()

            vGunPosition = Vector()
            outer.GetAttachment( "gun", vGunPosition )
            vecToAttackPos = (outer.attackposition - vGunPosition)
            self.PoseGunTowardTargetDirection(vecToAttackPos)
        
    def SetActivityMap(self, *args, **kwargs): pass
            
    def OnNewModel(self):
        studiohdr = self.outer.GetModelPtr()
 
        # Init the pose parameters
        self.outer.SetPoseParameter( "flex_horz", 0 )
        self.outer.SetPoseParameter( "flex_vert", 0 )
        self.outer.SetPoseParameter( "fin_accel", 0 )
        self.outer.SetPoseParameter( "fin_sway", 0 )
        
        self.poseflexhorz = self.outer.LookupPoseParameter( "flex_horz")
        self.poseflexvert = self.outer.LookupPoseParameter( "flex_vert" )
        self.posepitch = self.outer.LookupPoseParameter( "pitch" )
        self.poseyaw = self.outer.LookupPoseParameter( "yaw" )
        self.posefinaccel = self.outer.LookupPoseParameter( "fin_accel" )
        self.posefinsway = self.outer.LookupPoseParameter( "fin_sway" )

        self.poseweapon_pitch = self.outer.LookupPoseParameter( "weapon_pitch" )
        self.poseweapon_yaw = self.outer.LookupPoseParameter( "weapon_yaw" )
        
    def MoveHead(self, interval):
        outer = self.outer
        
        flYaw = outer.GetPoseParameter( self.poseflexhorz )
        flPitch = outer.GetPoseParameter( self.poseflexvert )

        while True:
            if self.outer.enemy:
                vecToEnemy = Vector()
                vecAimDir = Vector()
                
                vGunPosition = Vector()
                vecTargetOffset = Vector()
                vGunAngles = QAngle()

                self.outer.GetAttachment( "muzzle", vGunPosition, vGunAngles )

                vTargetPos = self.outer.GetEnemyTarget()

                VectorSubtract( vTargetPos, vGunPosition, vecToEnemy )
                VectorNormalize( vecToEnemy )
                
                # get angles relative to body position
                AngleVectors( self.GetAbsAngles(), vecAimDir )
                flDot = DotProduct( vecAimDir, vecToEnemy )

                # Look at Enemy!!
                if flDot > 0.3:
                    flDesiredYaw = UTIL_VecToYaw(vTargetPos - vGunPosition)
                    flDiff = AngleDiff( flDesiredYaw, vGunAngles.y ) * 0.90
                    flYaw = Approach( flYaw + flDiff, flYaw, 5.0 )

                    flDesiredPitch = UTIL_VecToPitch(vTargetPos - vGunPosition)
                    flDiff = AngleDiff( flDesiredPitch, vGunAngles.x ) * 0.90
                    flPitch = Approach( flPitch + flDiff, flPitch, 5.0 )

                    break

     
            # Look where going!
            flYaw = Approach( outer.GetLocalAngularVelocity().y, flYaw, 2.0 * 10 * interval )
            flPitch = Approach( outer.GetLocalAngularVelocity().x, flPitch, 2.0 * 10 * interval )
            break

        # Set the body flexes
        outer.SetPoseParameter( self.poseflexvert, flPitch )
        outer.SetPoseParameter( self.poseflexhorz, flYaw )

    def PoseGunTowardTargetDirection(self, vTargetDir):
        ''' Utility function to aim the helicopter gun at the direction '''
        outer = self.outer
        
        vecOut = Vector()
        VectorIRotate( vTargetDir, self.outer.EntityToWorldTransform(), vecOut )

        angles = QAngle()
        VectorAngles(vecOut, angles)
        angles.y = AngleNormalize( angles.y )
        angles.x = AngleNormalize( angles.x )

        if angles.x > self.anggun.x:
            self.anggun.x = min( angles.x, self.anggun.x + 12 )
        if angles.x < self.anggun.x:
            self.anggun.x = max( angles.x, self.anggun.x - 12 )
        if angles.y > self.anggun.y:
            self.anggun.y = min( angles.y, self.anggun.y + 12 )
        if angles.y < self.anggun.y:
            self.anggun.y = max( angles.y, self.anggun.y - 12 )


        outer.SetPoseParameter( self.poseweapon_pitch, -self.anggun.x )
        outer.SetPoseParameter( self.poseweapon_yaw, self.anggun.y )

        return True

@entity('unit_combinegunship', networked=True)
class UnitCombineGunship(BaseClass):    
    """ Combine Gunship """
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 435.0
        self.testroutestartheight = 1024.0
        
    AnimStateClass = UnitBaseGunshipAnimState
        
    if isserver:
        def Precache(self):
            super().Precache()
            
            self.PrecacheModel("sprites/lgtning.vmt")

            PrecacheMaterial( "effects/ar2ground2" )
            PrecacheMaterial( "effects/blueblackflash" )
            
            self.PrecacheScriptSound( "NPC_CombineGunship.SearchPing" )
            self.PrecacheScriptSound( "NPC_CombineGunship.PatrolPing" )
            self.PrecacheScriptSound( "NPC_Strider.Charge" )
            self.PrecacheScriptSound( "NPC_Strider.Shoot" )
            self.PrecacheScriptSound( "NPC_CombineGunship.SeeEnemy" )
            self.PrecacheScriptSound( "NPC_CombineGunship.CannonStartSound" )
            self.PrecacheScriptSound( "NPC_CombineGunship.Explode")
            self.PrecacheScriptSound( "NPC_CombineGunship.Pain" )
            self.PrecacheScriptSound( "NPC_CombineGunship.CannonStopSound" )

            self.PrecacheScriptSound( "NPC_CombineGunship.DyingSound" )
            self.PrecacheScriptSound( "NPC_CombineGunship.CannonSound" )
            self.PrecacheScriptSound( "NPC_CombineGunship.RotorSound" )
            self.PrecacheScriptSound( "NPC_CombineGunship.ExhaustSound" )
            self.PrecacheScriptSound( "NPC_CombineGunship.RotorBlastSound" )

            #UTIL_PrecacheOther( "env_citadel_energy_core" )
            UnitCombineGunship.g_iGunshipEffectIndex = self.PrecacheModel( "sprites/physbeam.vmt" )

            PropBreakablePrecacheAll("models/gunship.mdl")
        
    def Spawn(self):
        super().Spawn()
        
        self.ammotype = GetAmmoDef().Index("CombineCannon")
        
        if isclient:
            self.InitializeRotorSound()
        
    def UnitThink(self):
        super().UnitThink()
        
        self.DoCombat()
        self.Ping()
        
    def StartRangeAttack(self, enemy):
        self.FireGun()
        self.DoAnimation(self.ANIM_RANGE_ATTACK1) 
        return False
            
    def PlayPatrolLoop(self):
        self.patrolloopplaying = True
        '''
        controller = CSoundEnvelopeController.GetController()
        controller.SoundChangeVolume( m_pPatrolSound, 1.0, 1.0 )
        controller.SoundChangeVolume( m_pAngrySound, 0.0, 1.0 )
        '''
        
    def PlayAngryLoop(self):
        self.patrolloopplaying = False
        '''
        CSoundEnvelopeController &controller = CSoundEnvelopeController::GetController()
        controller.SoundChangeVolume( m_pPatrolSound, 0.0, 1.0 )
        controller.SoundChangeVolume( m_pAngrySound, 1.0, 1.0 )
        '''
        
    def Ping(self):
        if self.iscrashing:
            return

        if self.enemy:
            if gpGlobals.curtime > self.timenextping:
                self.EmitSound( "NPC_CombineGunship.SearchPing" )
                self.timenextping = gpGlobals.curtime + 3
        else:
            if gpGlobals.curtime > self.timenextping:
                self.EmitSound( "NPC_CombineGunship.PatrolPing" )
                self.timenextping = gpGlobals.curtime + 3

    def InitializeRotorSound(self):
        ''' Fire up the Gunships 'second' rotor sound. The Search sound. '''
        controller = CSoundEnvelopeController.GetController()
        
        filter = CPASAttenuationFilter(self)

        self.cannonsound = controller.SoundCreate( filter, self.entindex(), "NPC_CombineGunship.CannonSound" )
        self.rotorsound = controller.SoundCreate( filter, self.entindex(), "NPC_CombineGunship.RotorSound" )
        self.airexhaustsound = controller.SoundCreate( filter, self.entindex(), "NPC_CombineGunship.ExhaustSound" )
        self.airblastsound = controller.SoundCreate( filter, self.entindex(), "NPC_CombineGunship.RotorBlastSound" )
        
        controller.Play( self.cannonsound, 0.0, 100 )
        controller.Play( self.airexhaustsound, 0.0, 100 )
        controller.Play( self.airblastsound, 0.0, 100 )

        super().InitializeRotorSound()
        
    def StopLoopingSounds(self):
        controller = CSoundEnvelopeController.GetController()

        if self.cannonsound:
            controller.SoundDestroy( self.cannonsound )
            self.cannonsound = None

        if self.rotorsound:
            controller.SoundDestroy( self.rotorsound )
            self.rotorsound = None

        if self.airexhaustsound:
            controller.SoundDestroy( self.airexhaustsound )
            self.airexhaustsound = None

        if self.airblastsound:
            controller.SoundDestroy( self.airblastsound )
            self.airblastsound = None

        super().StopLoopingSounds()
        

    def IsTargettingMissile(self):
        ''' Tells us whether or not we're targetting an incoming missile '''
        if not self.enemy:
            return False
        return False
        #if FClassnameIs( self.enemy, "rpg_missile" ) == False:
        #    return False
        #return True
        
    def GetMissileTarget(self):
        return self.enemy.GetAbsOrigin()

    def GetEnemyTarget(self):
        ''' Get the target position for the enemy- the position we fire upon.
            this is often modified by m_flAttackOffset to provide the 'stitching'
            behavior that's so popular with the kids these days (sjb)'''
        # Make sure we have an enemy
        if not self.enemy:
            return self.attackposition

        # If we're locked onto a missile, use special code to try and destroy it
        if self.IsTargettingMissile():
            return self.GetMissileTarget()

        return self.attackposition
        
    def GroundDistToPosition(self, pos):
        vecDiff = Vector()
        VectorSubtract(self.GetAbsOrigin(), pos, vecDiff)

        # Only interested in the 2d dist
        vecDiff.z = 0

        return vecDiff.Length()
        
    def FireGun(self):
        ''' If the enemy is in front of the gun, load up a burst. 
            Actual gunfire is handled in UnitThink. '''
        if self.lifestate != LIFE_ALIVE:
            return False

        #if ( self.isgroundattacking )
        #    return False

        if self.enemy and not self.isfiring and gpGlobals.curtime > self.nextfireguntime:
            # We want to decelerate to attack
            #if m_flGoalSpeed > GetMaxSpeedFiring():
            #    m_flGoalSpeed = GetMaxSpeedFiring()

            bTargetingMissile = self.IsTargettingMissile()
            '''if not bTargetingMissile and not m_bPreFire:
                m_bPreFire = True
                self.nextfireguntime = gpGlobals.curtime + 0.5
                
                self.EmitSound( "NPC_CombineGunship.CannonStartSound" )
                return False'''

            #TODO: Emit the danger noise and wait until it's finished

            # Don't fire at an occluded enemy unless blindfire is on.
            #if ( HasCondition( COND_ENEMY_OCCLUDED ) and ( m_fBlindfire == False ) )
            #    return False

            # Don't shoot if the enemy is too close
            if not bTargetingMissile and self.GroundDistToPosition(self.enemy.GetAbsOrigin()) < self.GUNSHIP_STITCH_MIN:
                return False

            vecAimDir = Vector()
            vecToEnemy = Vector()
            vecMuzzle = Vector()

            self.GetAttachment( "muzzle", vecMuzzle, vecAimDir, None, None )
            vecEnemyTarget = self.GetEnemyTarget()

            # Aim with the muzzle's attachment point.
            VectorSubtract( vecEnemyTarget, vecMuzzle, vecToEnemy )

            VectorNormalize(vecToEnemy)
            VectorNormalize(vecAimDir)

            attackinfo = self.unitinfo.AttackRange
            if DotProduct(vecToEnemy, vecAimDir) > attackinfo.cone:
                self.StartCannonBurst( self.gunshipburstsize )
                return True
            return False
        return False

    def StartCannonBurst(self, iBurstSize):
        ''' The proper way to begin the gunship cannon firing at the enemy. '''
        self.burstsize = iBurstSize
        self.bursthits = 0

        self.nextfireguntime = gpGlobals.curtime

        # Start up the cannon sound.
        if self.cannonsound:
            controller = CSoundEnvelopeController.GetController()
            controller.SoundChangeVolume( self.cannonsound, 1.0, 0 )

        self.isfiring = True

        # Setup the initial position of the burst
        if self.enemy:
            # Follow mode
            enemyPos = Vector()
            UTIL_PredictedPosition(self.enemy, 2.0, enemyPos)

            offsetAngles = QAngle()
            offsetDir = ( self.WorldSpaceCenter() - enemyPos )
            VectorNormalize( offsetDir )
            VectorAngles( offsetDir, offsetAngles )

            angleOffset = random.randint(15, 30)
            if random.randint(0, 1):
                angleOffset *= -1
            
            offsetAngles[YAW] += angleOffset
            offsetAngles[PITCH] = 0
            offsetAngles[ROLL] = 0

            AngleVectors(offsetAngles, offsetDir)

            enemyDist = self.GroundDistToPosition(self.enemy.GetAbsOrigin())
            if enemyDist < ( float(self.gunshipburstdist) + self.GUNSHIP_STITCH_MIN ):
                stitchOffset = self.GUNSHIP_STITCH_MIN
            else:
                stitchOffset = float(self.gunshipburstdist)

            # Move out to the start of our stitch run
            self.attackposition = enemyPos + ( offsetDir * stitchOffset )
            self.attackposition.z = enemyPos.z

            # Point at our target
            self.attackvelocity = -offsetDir * self.BASE_STITCH_VELOCITY

            #CSoundEnt.InsertSound( SOUND_DANGER | SOUND_CONTEXT_REACT_TO_SOURCE, enemyPos, 512, 0.2f, this )

    def StopCannonBurst(self):
        ''' The proper way to cease the gunship cannon firing.  '''
        self.bursthits = 0
        self.isfiring = False
        self.prefire = False

        # Reduce the burst time when we get lower in health
        flPerc = self.health / float(self.maxhealth)
        flDelay = clamp( flPerc * self.burstdelay, 0.5, self.burstdelay )

        # If we didn't finish the burst, don't wait so long
        flPerc = 1.0 - (self.burstsize / float(self.gunshipburstsize))
        flDelay *= flPerc

        self.nextfireguntime = gpGlobals.curtime + flDelay
        self.burstsize = 0

        # Stop the cannon sound.
        if self.cannonsound:
            CSoundEnvelopeController.GetController().SoundChangeVolume(self.cannonsound, 0.0, 0.05)
        self.EmitSound( "NPC_CombineGunship.CannonStopSound" )
    
    oldenemy = None
    nextseeenemysound = 0.0
    def DoCombat(self):
        ''' do all of the stuff related to having an enemy, attacking, etc. '''
        # Check for enemy change-overs
        if self.enemy:
            if self.oldenemy != self.enemy:
                self.oldenemy = self.enemy
                if self.enemy.IsUnit() and self.nextseeenemysound < gpGlobals.curtime:
                    self.nextseeenemysound = gpGlobals.curtime + 5.0

                    if not self.HasSpawnFlags( self.SF_GUNSHIP_USE_CHOPPER_MODEL ):
                        self.EmitSound( "NPC_CombineGunship.SeeEnemy" )

                # If we're shooting at a missile, do it immediately!
                if self.IsTargettingMissile():
                    EmitSound( "NPC_CombineGunship.SeeMissile" )

                    # Allow the gunship to attack again immediately
                    if ( self.nextfireguntime > gpGlobals.curtime ) and ( ( self.nextfireguntime - gpGlobals.curtime ) > self.GUNSHIP_MISSILE_MAX_RESPONSE_TIME ):
                        self.nextfireguntime = gpGlobals.curtime + self.GUNSHIP_MISSILE_MAX_RESPONSE_TIME
                        self.burstsize = self.gunshipburstsize

                # Fade in angry sound, fade out patrol sound.
                self.PlayAngryLoop()

        # Do we have a belly blast target?
        if self.groundattacktarget and not self.isgroundattacking:
            # If we're over it, blast. Can't use GetDesiredPosition() because it's not updated yet.
            vecTarget = self.groundattacktarget.GetAbsOrigin() + Vector(0,0,self.GUNSHIP_BELLYBLAST_TARGET_HEIGHT)
            vecToTarget = (vecTarget - self.GetAbsOrigin())
            flDistance = vecToTarget.Length()

            # Get the difference between our velocity & the target's velocity
            vec2DVelocity = self.GetAbsVelocity()
            vec2DTargetVelocity = self.groundattacktarget.GetAbsVelocity()
            vec2DVelocity.z = vec2DTargetVelocity.z = 0
            flVelocityDiff = (vec2DVelocity - vec2DTargetVelocity).Length()
            if flDistance < 100 and flVelocityDiff < 200:
                self.StartGroundAttack()

        # Update our firing
        if self.isfiring:
            # Fire if we have rounds remaining in this burst
            if ( self.burstsize > 0 ) and (gpGlobals.curtime > self.nextfireguntime):
                self.UpdateEnemyTarget()
                self.FireCannonRound()
            elif self.burstsize < 1:
                # We're done firing
                self.StopCannonBurst()
                
                if self.IsTargettingMissile():
                    self.nextfireguntime = gpGlobals.curtime + 0.5
        else:
            # If we're not firing, look at the enemy
            if self.enemy:
                self.attackposition = self.enemy.EyePosition()

            '''
            #ifdef BELLYBLAST
            # Check for a ground attack
            if ( CheckGroundAttack() )
            {
                StartGroundAttack()
            }
            #endif
            '''
            # See if we're attacking
            if self.isgroundattacking:
                self.hitpos = self.GetGroundAttackHitPosition()

                self.ManageWarningBeam()

                # If our time is up, fire the blast and be done
                if self.groundattacktime < gpGlobals.curtime:
                    # Fire!
                    self.StopGroundAttack( True )

        # If we're using the chopper model, align the gun towards the target
        if self.HasSpawnFlags( self.SF_GUNSHIP_USE_CHOPPER_MODEL ):
            vGunPosition = Vector()
            self.GetAttachment( "gun", vGunPosition )
            vecToAttackPos = (self.attackposition - vGunPosition)
            self.animstate.PoseGunTowardTargetDirection(vecToAttackPos)

        '''
        # Forget flares once I've seen them for a while
        flDeltaSeen = m_flLastSeen - m_flPrevSeen
        if self.enemy != None and GetEnemy().Classify() == CLASS_FLARE and flDeltaSeen > GUNSHIP_FLARE_IGNORE_TIME )
            AddEntityRelationship( GetEnemy(), D_NU, 5 )

            self.PlayPatrolLoop()

            # Forget the flare now.
            self.enemy = None
        '''
        
    def UpdateEnemyTarget(self):
        vGunPosition = Vector()
        self.GetAttachment( "muzzle", vGunPosition )

        # Follow mode
        if self.enemy:
            enemyPos = self.enemy.EyePosition()
            bTargettingPlayer = self.enemy.IsPlayer()
        else:
            enemyPos = self.attackposition
            bTargettingPlayer = False

        # Direction towards the enemy
        targetDir = enemyPos - self.attackposition
        VectorNormalize( targetDir )

        # Direction from the gunship to the enemy
        enemyDir = enemyPos - vGunPosition
        VectorNormalize( enemyDir )

        lastSpeed = VectorNormalize( self.attackvelocity )
        chaseAngles = QAngle()
        lastChaseAngles = QAngle()

        VectorAngles( targetDir, chaseAngles )
        VectorAngles( self.attackvelocity, lastChaseAngles )

        # Debug info
        #if g_debug_gunship.GetInt() == GUNSHIP_DEBUG_STITCHING:
            # Final position
        #    ndebugoverlay.Cross3D( self.attackposition, -Vector(2,2,2), Vector(2,2,2), 0, 0, 255, true, 4.0f )
        
        yawDiff = AngleDiff( lastChaseAngles[YAW], chaseAngles[YAW] )

        if bTargettingPlayer:
            maxYaw = 6
        else:
            maxYaw = 30

        yawDiff = clamp( yawDiff, -maxYaw, maxYaw )

        chaseAngles[PITCH] = 0.0
        chaseAngles[ROLL] = 0.0

        bMaxHits = self.bursthits >= self.GUNSHIP_MAX_HITS_PER_BURST or (self.enemy and not self.enemy.IsAlive())

        if bMaxHits:
            # We've hit our target. Stop chasing, and return to max speed.
            chaseAngles[YAW] = lastChaseAngles[YAW]
            lastSpeed = self.BASE_STITCH_VELOCITY
        else:
            # Move towards the target yaw
            chaseAngles[YAW] = anglemod( lastChaseAngles[YAW] - yawDiff )
        
        # If we've hit the target already, or we're not close enough to it, then just stitch along
        if bMaxHits or ( self.attackposition - enemyPos ).LengthSqr() > (64 * 64):
            AngleVectors( chaseAngles, targetDir )

            # Update our new velocity
            self.attackvelocity = targetDir * lastSpeed

            #if g_debug_gunship.GetInt() == GUNSHIP_DEBUG_STITCHING:
            #    ndebugoverlay.Line( self.attackposition, self.attackposition + (self.attackvelocity * 0.1), 255, 0, 0, True, 4.0 )

            # Move along that velocity for this step in time
            self.attackposition += ( self.attackvelocity * 0.1 )
            self.attackposition.z = enemyPos.z
        else:
            # Otherwise always continue to hit an NPC when close enough
            self.attackposition = enemyPos
            
    def FireCannonRound(self):
        ''' Fire a round from the cannon '''
        vecToEnemy = Vector()
        vecMuzzle = Vector()
        vecAimDir = Vector()
        angAimDir = QAngle()

        self.GetAttachment("muzzle", vecMuzzle, angAimDir)
        AngleVectors(angAimDir, vecAimDir)
        vecEnemyTarget = self.GetEnemyTarget()
        
        # Aim with the muzzle's attachment point.
        VectorSubtract( vecEnemyTarget, vecMuzzle, vecToEnemy )
        VectorNormalize( vecToEnemy )

        # If the gun is wildly off target, stop firing!
        # FIXME  - this should use a vector pointing 
        # to the enemy's location PLUS the stitching 
        # error! (sjb) !!!BUGBUG

        '''
        if g_debug_gunship.GetInt() == GUNSHIP_DEBUG_STITCHING:
            QAngle vecAimAngle
            Vector	vForward, vRight, vUp
            GetAttachment( "muzzle", vecMuzzle, &vForward, &vRight, &vUp )
            AngleVectors( vecAimAngle, &vForward, &vRight, &vUp )
            NDebugOverlay::Line( vecMuzzle, vecEnemyTarget, 255, 255, 0, true, 1.0 )

            NDebugOverlay::Line( vecMuzzle, vecMuzzle + ( vForward * 64.0 ), 255, 0, 0, true, 1.0 )
            NDebugOverlay::Line( vecMuzzle, vecMuzzle + ( vRight * 32.0 ), 0, 255, 0, true, 1.0 )
            NDebugOverlay::Line( vecMuzzle, vecMuzzle + ( vUp * 32.0 ), 0, 0, 255, true, 1.0 )
        '''

        # Robin: Check the dotproduct to the enemy, NOT to the offsetted firing angle
        # Fixes problems firing at close enemies, where the enemy is valid but
        # the offset firing stitch isn't.
        vecDotCheck = Vector(vecToEnemy)
        if self.enemy:
            VectorSubtract( self.enemy.GetAbsOrigin(), vecMuzzle, vecDotCheck )
            VectorNormalize( vecDotCheck )

        if DotProduct( vecDotCheck, vecAimDir ) < 0.8:
            self.StopCannonBurst()
            return

        self.DoMuzzleFlash()

        #m_OnFireCannon.FireOutput( this, this, 0 )

        self.nextfireguntime = gpGlobals.curtime + 0.05

        flPrevHealth = 0
        if self.enemy:
            flPrevHealth = self.enemy.health
            
        attackinfo = self.unitinfo.AttackRange

        # Make sure we hit missiles
        if self.IsTargettingMissile():
            # Fire a fake shot
            self.FireBullets( 1, vecMuzzle, vecToEnemy, VECTOR_CONE_5DEGREES, 8192, self.ammotype, 1 )

            pMissile = self.enemy

            missileDir = Vector()
            AngleVectors( pMissile.GetAbsAngles(), missileDir )

            threatDir = (self.WorldSpaceCenter() - pMissile.GetAbsOrigin())
            threatDist = VectorNormalize( threatDir )

            # Check that the target is within some threshold
            if (DotProduct( threatDir, missileDir ) > 0.95) and (threatDist < 1024.0):
                if random.randint( 0, 1 ) == 0:
                    info = CTakeDamageInfo( self, self, 200, DMG_MISSILEDEFENSE )
                    CalculateBulletDamageForce(info, self.ammotype, -threatDir, self.WorldSpaceCenter())
                    self.enemy.TakeDamage( info )
            else:
                #FIXME: Some other metric
                pass
        else:
            self.burstsize -= 1

            # Fire directly at the target
            info = FireBulletsInfo_t(1, vecMuzzle, vecToEnemy, vec3_origin, attackinfo.maxrange, self.ammotype)
            info.tracerfreq = 1
            info.playerdamage = attackinfo.damage
            info.damage = attackinfo.damage

            # If we've already hit the player, do 0 damage. This ensures we don't hit the
            # player multiple times during a single burst.
            if self.bursthits >= self.GUNSHIP_MAX_HITS_PER_BURST:
                info.playerdamage = 1.0

            self.FireBullets(info)

            if self.enemy and flPrevHealth != self.enemy.health:
                self.bursthits += 1
                
    def MakeTracer(self, vecTracerSrc, tr, iTracerType):
        if iTracerType == TRACER_LINE:
            vecDir = tr.endpos - vecTracerSrc

            flTracerDist = VectorNormalize( vecDir )

            UTIL_Tracer( vecTracerSrc, tr.endpos, 0, TRACER_DONT_USE_ATTACHMENT, 8000, True, "GunshipTracer" )
        else:
            super().MakeTracer( vecTracerSrc, tr, iTracerType )

    def DoMuzzleFlash(self):
        super().DoMuzzleFlash()
        
        data = CEffectData()

        data.attachmentindex = self.LookupAttachment( "muzzle" )
        data.entindex = self.entindex()
        DispatchEffect( "GunshipMuzzleFlash", data )
        
    def EventHandlerRangeAttack1(self, data):
        self.FireCannonRound()

    # Events
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_RANGE_ATTACK1' : EventHandlerRangeAttack1,
    } )
    
    g_iGunshipEffectIndex = -1
    
    GUNSHIP_STITCH_MIN = 120.0
    
    GUNSHIP_MISSILE_MAX_RESPONSE_TIME = 0.4
    
    GUNSHIP_BELLYBLAST_TARGET_HEIGHT = 512.0
    
    BASE_STITCH_VELOCITY = 800 # Units per second
    MAX_STITCH_VELOCITY = 1000 # Units per second
    
    GUNSHIP_MAX_HITS_PER_BURST = 5
    
    timenextping = 0.0
    cannonsound = None
    rotorsound = None
    airexhaustsound = None
    airblastsound = None
    
    iscrashing = False
    isfiring = False
    attackposition = vec3_origin
    attackvelocity = vec3_origin
    groundattacktarget = None
    isgroundattacking = False
    burstsize = 0 
    bursthits = 0
    
    ammotype = -1
    
    penetrationdepth = 24
    burstdelay = 2.0
    gunshipburstsize = 15
    gunshipburstmin = 800
    gunshipburstdist = 768
    
    nextfireguntime = 0.0

    # Spawnflags
    SF_GUNSHIP_NO_GROUND_ATTACK = ( 1 << 12 )
    SF_GUNSHIP_USE_CHOPPER_MODEL = ( 1 << 13 )
    
class CombineGunshipInfo(UnitInfo):
    name = 'unit_combinegunship'
    cls_name = 'unit_combinegunship'
    displayname = '#CombGunship_Name'
    description = '#CombGunship_Description'
    #image_name = 'vgui/combine/units/unit_combinegunship'
    costs = [('requisition', 150), ('power', 180)]
    buildtime = 120.0
    zoffset = 128.0
    scale = 0.75
    modelname = 'models/gunship.mdl'
    hulltype = 'HULL_LARGE_CENTERED'
    health = 2000
    turnspeed = 10
    maxspeed = 450
    population = 6
    attributes = ['synth', 'pulse']
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    class AttackRange(UnitInfo.AttackRange):
        damage = 12
        minrange = 320.0
        maxrange = 1500.0
        attackspeed = 0.1
        cone = 0.8
    attacks = 'AttackRange'
    
class CombineHelicopterInfo(CombineGunshipInfo):
    name = 'unit_combinehelicopter'
    modelname = 'models/combine_helicopter.mdl'
    keyvalues = {'spawnflags' : str(UnitCombineGunship.SF_GUNSHIP_USE_CHOPPER_MODEL)}
    scale = 0.75
    