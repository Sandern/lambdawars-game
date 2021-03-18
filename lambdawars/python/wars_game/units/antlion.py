from srcbase import *
from vmath import *
from core.units import UnitInfo, UnitBaseCombat as BaseClass, EventHandlerAnimation
import random
import math

from unit_helper import UnitAnimConfig, LegAnimType_t

from entities import entity, Activity, ACT_GLIDE
from gameinterface import *
if isserver:
    from te import CEffectData, DispatchEffect
    from utils import (UTIL_SetOrigin, UTIL_TraceLine, trace_t, UTIL_SetSize, UTIL_ScreenShake, UTIL_PredictedPosition, SHAKE_START,
                       SF_ENVEXPLOSION_NODAMAGE, SF_ENVEXPLOSION_NOSPARKS, SF_ENVEXPLOSION_NODLIGHTS, SF_ENVEXPLOSION_NOSMOKE)
    from entities import (PropBreakableCreateAll, breakablepropparams_t, PropBreakablePrecacheAll, RadiusDamage,
                          CTakeDamageInfo, Class_T, g_EventQueue, SpawnBlood)
    from particles import DispatchParticleEffect, PrecacheParticleSystem
    from core.units.intention import BaseAction
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler, TossGrenadeAnimEventHandler
else:
    from particles import SimpleParticle, AddSimpleParticle, ParticleMgr
    from entities import C_BasePlayer, ENTITY_LIST_SIMULATE
    import playermgr
    
from utils import UTIL_PrecacheOther
from fields import BooleanField, FlagsField, input
import ndebugoverlay

# Use all the gibs
AntlionGibs_Unique = [
    "models/gibs/antlion_gib_large_1.mdl",
    "models/gibs/antlion_gib_large_2.mdl",
    "models/gibs/antlion_gib_large_3.mdl"
]

AntlionGibs_Medium = [
    "models/gibs/antlion_gib_medium_1.mdl",
    "models/gibs/antlion_gib_medium_2.mdl",
    "models/gibs/antlion_gib_medium_3.mdl"
]

AntlionGibs_Small = [
    "models/gibs/antlion_gib_small_1.mdl",
    "models/gibs/antlion_gib_small_2.mdl",
    "models/gibs/antlion_gib_small_3.mdl"
]

sv_gravity = ConVarRef('sv_gravity')

# if isserver:
    # g_debug_antlion_worker = ConVar('g_debug_antlion_worker', "0" )

    # # Spit helper method
    # def VecCheckThrowTolerance(ent, vecSpot1, vecSpot2, flSpeed, flTolerance):
        # flSpeed = max( 1.0, flSpeed )

        # flGravity = sv_gravity.GetFloat()

        # vecGrenadeVel = (vecSpot2 - vecSpot1)

        # # throw at a constant time
        # time = vecGrenadeVel.Length( ) / flSpeed
        # vecGrenadeVel = vecGrenadeVel * (1.0 / time)

        # # adjust upward toss to compensate for gravity loss
        # vecGrenadeVel.z += flGravity * time * 0.5

        # vecApex = vecSpot1 + (vecSpot2 - vecSpot1) * 0.5
        # vecApex.z += 0.5 * flGravity * (time * 0.5) * (time * 0.5)

        # tr = trace_t()
        # UTIL_TraceLine( vecSpot1, vecApex, MASK_SOLID, ent, ent.CalculateIgnoreOwnerCollisionGroup(), tr )
        # if tr.fraction != 1.0:
            # # fail!
            # if g_debug_antlion_worker.GetBool():
                # ndebugoverlay.Line( vecSpot1, vecApex, 255, 0, 0, True, 5.0 )

            # return vec3_origin

        # if g_debug_antlion_worker.GetBool():
            # ndebugoverlay.Line( vecSpot1, vecApex, 0, 255, 0, True, 5.0 )

        # UTIL_TraceLine( vecApex, vecSpot2, MASK_SOLID_BRUSHONLY, ent, ent.CalculateIgnoreOwnerCollisionGroup(), tr )
        # if tr.fraction != 1.0:
            # bFail = True

            # # Didn't make it all the way there, but check if we're within our tolerance range
            # if flTolerance > 0.0:
                # flNearness = ( tr.endpos - vecSpot2 ).LengthSqr()
                # if flNearness < ( flTolerance*flTolerance ):
                    # if g_debug_antlion_worker.GetBool():
                        # ndebugoverlay.Sphere( tr.endpos, vec3_angle, flTolerance, 0, 255, 0, 0, True, 5.0 )

                    # bFail = False

            # if bFail:
                # if g_debug_antlion_worker.GetBool():
                    # ndebugoverlay.Line( vecApex, vecSpot2, 255, 0, 0, True, 5.0 )
                    # ndebugoverlay.Sphere( tr.endpos, vec3_angle, flTolerance, 255, 0, 0, 0, True, 5.0 )
                # return vec3_origin

        # if g_debug_antlion_worker.GetBool():
            # ndebugoverlay.Line( vecApex, vecSpot2, 0, 255, 0, True, 5.0 )

        # return vecGrenadeVel


# DUST
DUST_STARTSIZE = 16
DUST_ENDSIZE = 48
DUST_RADIUS	= 32.0
DUST_STARTALPHA	= 0.3
DUST_ENDALPHA = 0.0
DUST_LIFETIME = 2.0

def CreateDust(origin, angles):
    offset = Vector()
    vecColor = Vector(0.3, 0.25, 0.2)

    iParticleCount = 16
    
    g_Mat_DustPuff = [None]*2
    g_Mat_DustPuff[0] = ParticleMgr().GetPMaterial("particle/particle_smokegrenade")
    g_Mat_DustPuff[1] = ParticleMgr().GetPMaterial("particle/particle_noisesphere")

    # Spawn the dust
    particle = SimpleParticle() 
    for i in range(0, iParticleCount):
        # Offset this dust puff's origin
        offset[0] = random.uniform( -DUST_RADIUS, DUST_RADIUS )
        offset[1] = random.uniform( -DUST_RADIUS, DUST_RADIUS )
        offset[2] = random.uniform(  -16, 8 )
        
        offset += origin

        particle.pos = offset
        particle.dietime = random.uniform( 0.75, 1.25 )
        particle.lifetime = 0.0
        
        dir = particle.pos - origin
        particle.velocity = dir * random.uniform( 0.5, 1.0 )
        dir.z = abs(dir.z)

        colorRamp = random.uniform( 0.5, 1.0 )
        color = vecColor*colorRamp

        color[0] = max(0.0, min(color[0], 1.0 ))
        color[1] = max(0.0, min(color[1], 1.0 ))
        color[2] = max(0.0, min(color[2], 1.0 ))

        color *= 255

        particle.color[0] = int(color[0])
        particle.color[1] = int(color[1])
        particle.color[2] = int(color[2])

        particle.startalpha= int(random.uniform( 64, 128 ))
        particle.endalpha = 0

        particle.startsize = int(random.randint( 50, 70 ))
        particle.endsize = int(particle.startsize * 3)
        particle.roll = int(random.randint( 0, 360 ))
        particle.rolldelta = int(random.uniform( -0.2, 0.2 ))

        # Though it appears there are two particle handle entries in g_Mat_DustPuff, in fact
        # only the one present at index 0 actually draws. Trying to spawn a particle with
        # the other material will give you no particle at all. Therefore while instead of this:
        # AddSimpleParticle( &particle, g_Mat_DustPuff[random.randint(0,1)  )
        # we have to do this:
        AddSimpleParticle(particle, g_Mat_DustPuff[0])

@entity('unit_antlion', networked=True)
class UnitAntlion(BaseClass):
    """ Antlion """
    def __init__(self):
        super().__init__()
        
        self.activespit = None
        self.wingsopen = False
        self.savedrop = 800.0

    def Precache(self):
        if isclient:
            super().Precache()
            return
            
        if self.IsWorker() or self.IsSuicider():
            #PropBreakablePrecacheAll( self.unitinfo.modelname )
            UTIL_PrecacheOther( "grenade_spit" )
            PrecacheParticleSystem( "blood_impact_antlion_worker_01" )
            PrecacheParticleSystem( "antlion_gib_02" )
            PrecacheParticleSystem( "blood_impact_yellow_01" )
        else:
            #PropBreakablePrecacheAll( self.unitinfo.modelname )
            PrecacheParticleSystem( "blood_impact_antlion_01" )
            PrecacheParticleSystem( "AntlionGib" )
            
        # Gibs
        for g in AntlionGibs_Unique:
            self.PrecacheModel(g)
        for g in AntlionGibs_Medium:
            self.PrecacheModel(g)
        for g in AntlionGibs_Small:
            self.PrecacheModel(g)
            
        # Sounds
        self.PrecacheScriptSound( "NPC_Antlion.RunOverByVehicle" )
        self.PrecacheScriptSound( "NPC_Antlion.MeleeAttack" )
        self.footstep = self.PrecacheScriptSound( "NPC_Antlion.Footstep" )
        self.PrecacheScriptSound( "NPC_Antlion.BurrowIn" )
        self.PrecacheScriptSound( "NPC_Antlion.BurrowOut" )
        self.PrecacheScriptSound( "NPC_Antlion.FootstepSoft" )
        self.PrecacheScriptSound( "NPC_Antlion.FootstepHeavy" )
        self.PrecacheScriptSound( "NPC_Antlion.MeleeAttackSingle" )
        self.PrecacheScriptSound( "NPC_Antlion.MeleeAttackDouble" )
        self.PrecacheScriptSound( "NPC_Antlion.Distracted" )
        self.PrecacheScriptSound( "NPC_Antlion.Idle" )
        self.PrecacheScriptSound( "NPC_Antlion.Pain" )
        self.PrecacheScriptSound( "NPC_Antlion.Land" )
        self.PrecacheScriptSound( "NPC_Antlion.WingsOpen" )
        self.PrecacheScriptSound( "NPC_Antlion.LoopingAgitated" )

        self.PrecacheScriptSound( "NPC_Antlion.PoisonBurstScream" )
        self.PrecacheScriptSound( "NPC_Antlion.PoisonBurstScreamSubmerged" )
        self.PrecacheScriptSound( "NPC_Antlion.PoisonBurstExplode" )
        self.PrecacheScriptSound( "NPC_Antlion.MeleeAttack_Muffled" )
        self.PrecacheScriptSound( "NPC_Antlion.TrappedMetal" )
        self.PrecacheScriptSound( "NPC_Antlion.ZappedFlip" )
        self.PrecacheScriptSound( "NPC_Antlion.PoisonShoot" )
        self.PrecacheScriptSound( "NPC_Antlion.PoisonBall" )
        
        super().Precache() 
        
    def Spawn(self):
        if self.IsWorker():
            # Bump up the worker's eye position a bit
            self.SetViewOffset(Vector(0.0, 0.0, 32.0))   
            
        self.SetBloodColor(BLOOD_COLOR_ANTLION)
            
        if isclient:
            super().Spawn()
            return
            
        super().Spawn()
        
        self.skin = random.randint(0, self.ANTLION_SKIN_COUNT-1)
            
    def IsWorker(self):
        return self.unitinfo.name == 'unit_antlionworker'
        
    def IsSuicider(self):
        return self.unitinfo.name == 'unit_antlionsuicider'
            
    # Server only function, called when the sequence changes
    def OnSequenceSet(self, oldsequence):
        act = self.GetSequenceActivity(self.GetSequence())
        # Floating in the air with our cute antlion wings
        if act == ACT_GLIDE and self.wingsopen == False:   
            self.SetWings(True)
        elif act != ACT_GLIDE and self.wingsopen == True:
            self.SetWings(False)
            
    def GetSpitVector(self, vecStartPos, vecTarget):
        """ Get a toss direction that will properly lob spit to hit a target
            Input  : vecStartPos - Where the spit will start from
                     vecTarget - Where the spit is meant to land
                     vecOut - The resulting vector to lob the spit
            Output : Returns true on success, false on failure. """
        # antlion workers exist only in episodic.
        # Try the most direct route
        vecToss = VecCheckThrowTolerance(self, vecStartPos, vecTarget, self.ANTLIONWORKER_SPITSPEED, 32.0, self.CalculateIgnoreOwnerCollisionGroup())

        # If this failed then try a little faster (flattens the arc)
        if vecToss == vec3_origin:
            vecToss = VecCheckThrowTolerance(self, vecStartPos, vecTarget, self.ANTLIONWORKER_SPITSPEED * 1.5, 32.0, self.CalculateIgnoreOwnerCollisionGroup())
            if vecToss == vec3_origin:
                return False, vecToss

        return True, vecToss
                
    def SetWings(self, state):       
        if state:
            self.SetGravity(self.gravityinair)
            self.SetBodygroup(1, 1)
            
            filter = CPASAttenuationFilter( self, "NPC_Antlion.WingsOpen" )
            filter.MakeReliable()
            self.EmitSoundFilter( filter, self.entindex(), "NPC_Antlion.WingsOpen" )
            self.loopingstarted = True
        else:
            self.SetGravity(1.0)
            self.SetBodygroup(1, 0)
            
            self.StopSound( "NPC_Antlion.WingsOpen" )
            
        self.wingsopen = state
        
    def WingsOpenHandler(self, event):
        self.SetWings(True)
        
    def WingsCloseHandler(self, event):
        self.SetWings(False)
        
    def StopLoopingSounds(self):
        if self.loopingstarted:
            self.StopSound( "NPC_Antlion.WingsOpen" )
            self.loopingstarted = False
            
        #if self.agitatedsound:
        #    self.StopSound( "NPC_Antlion.LoopingAgitated" )
        #    self.agitatedsound = False

    def CanBecomeRagdoll(self):
        if self.IsWorker() or self.IsSuicider():
            return self.dontexplode
        return super().CanBecomeRagdoll()    
            
    def ShouldGib(self, info):
        if info.GetDamageType() & (DMG_NEVERGIB|DMG_DISSOLVE):
            self.dontexplode = True
            return False

        if self.IsWorker() or self.IsSuicider():
            return not self.dontexplode

        if info.GetDamageType() & (DMG_ALWAYSGIB|DMG_BLAST):
            return True

        if self.health < -20:
            return True
        
        return False      
        
    bodybone = -1
    def CorpseGib(self, info):
        if self.IsWorker():
            self.DoPoisonBurst()
        elif self.IsSuicider():
            self.DoSuicidePoisonBurst()
        else:
            # Use the bone position to handle being moved by an animation (like a dynamic scripted sequence)
            if self.bodybone == -1:
                self.bodybone = self.LookupBone( "Antlion.Body_Bone" )

            vecOrigin = Vector()
            angBone = QAngle()
            self.GetBonePosition( self.bodybone, vecOrigin, angBone )

            DispatchParticleEffect( "AntlionGib", vecOrigin, QAngle( 0, 0, 0 ) )

        # FIXME: Code below causes problems with the physics
        #velocity = Vector(vec3_origin)
        #angVelocity = RandomAngularImpulse( -150.0, 150.0 )
        #params = breakablepropparams_t( self.EyePosition(), self.GetAbsAngles(), velocity, angVelocity )
        #params.impactEnergyScale = 1.0
        #params.defBurstScale = 150.0
        #params.defCollisionGroup = COLLISION_GROUP_DEBRIS
        #PropBreakableCreateAll( self.GetModelIndex(), None, params, self, -1, True, True )

        return True

    def DoPoisonBurst(self):
        if self.GetWaterLevel() < 2:
            info = CTakeDamageInfo( self, self, self.ANTLIONWORKER_BURSTDAMAGE, DMG_BLAST_SURFACE | DMG_POISON | DMG_PREVENT_PHYSICS_FORCE )

            RadiusDamage( info, self.GetAbsOrigin(), self.ANTLIONWORKER_BURSTRADIUS, Class_T.CLASS_NONE, self )

            DispatchParticleEffect( "antlion_gib_02", self.WorldSpaceCenter(), self.GetAbsAngles() )
        else:
            data = CEffectData()
            data.origin = self.WorldSpaceCenter()
            data.magnitude = 100
            data.scale = 128
            data.flags = ( SF_ENVEXPLOSION_NODAMAGE | SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSMOKE )

            DispatchEffect( "WaterSurfaceExplosion", data )

        self.EmitSound("NPC_Antlion.PoisonBurstExplode" )
        
    def DoSuicidePoisonBurst(self):
        info = CTakeDamageInfo( None, None, self.ANTLIONSUICIDER_BURSTDAMAGE, DMG_BLAST | DMG_POISON| DMG_PREVENT_PHYSICS_FORCE )

        RadiusDamage( info, self.WorldSpaceCenter(), self.ANTLIONSUICIDER_BURSTRADIUS, Class_T.CLASS_NONE, self )

        DispatchParticleEffect( "antlion_gib_02", self.WorldSpaceCenter(), self.GetAbsAngles() )

        self.EmitSound("NPC_Antlion.PoisonBurstExplode" )

    if isserver:
        def StartMeleeAttack(self, enemy):
            if self.IsSuicider():
                self.takedamage = DAMAGE_NO
                self.DoSuicidePoisonBurst()
                g_EventQueue.AddEvent(self, 'kill', 0.0, self, self)
                return False
                
            # Do melee damage
            self.MeleeAttack(self.ANTLION_MELEE1_RANGE, self.unitinfo.AttackMelee.damage, QAngle(20.0, 0.0, -12.0), Vector(-250.0, 1.0, 1.0)) 
                
            return super().StartMeleeAttack(enemy)
    
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        enthurt = self.CheckTraceHullAttack( distance, -Vector(16,16,32), Vector(16,16,32), damage, self.unitinfo.AttackMelee.damagetype, 5.0 )
        if enthurt is not None:     # hitted something
            # Play a random attack hit sound
            self.EmitSound("NPC_Antlion.MeleeAttack")   
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), enthurt.BloodColor(), damage)   
        
    # Burrowing
    def Burrow(self):
        if self.burrowed:
            return
        self.DispatchEvent('OnBurrow')  
        self.UpdateAbilities()
        
    def UnBurrow(self):
        if not self.burrowed:
            return
        self.RemoveSolidFlags(FSOLID_NOT_SOLID)
        self.DispatchEvent('OnUnBurrow') 
        self.UpdateAbilities()
        
    @input(inputname='Unburrow')
    def InputUnburrow(self, inputdata):
        if not self.IsAlive():
            return
        self.UnBurrow()
        
    @input(inputname='Burrow')
    def InputBurrow(inputdata):
        if not self.IsAlive():
            return
        self.Burrow()
            
    def Flip(self, zapped=False):
        # We can't flip an already flipped antlion
        if self.isflipped:
            return

        # Must be on the ground
        if not (self.GetFlags() & FL_ONGROUND):
            return;

        self.DispatchEvent('OnFlip')  
        
        if zapped:
            self.zapduration = gpGlobals.curtime + self.SequenceDuration(self.SelectWeightedSequence(self.ACT_ANTLION_ZAP_FLIP)) + 0.1

            self.EmitSound("NPC_Antlion.ZappedFlip")

    if isclient:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            if self.burrowtexture:
                self.burrowtexture.Shutdown()
                self.burrowtexture = None 
                
        def OnBurrowedChanged(self):
            localplayer = C_BasePlayer.GetLocalPlayer()
            if localplayer and localplayer.GetOwnerNumber() == self.GetOwnerNumber():
                if self.burrowed and not self.burrowtexture:
                    # mins = self.WorldAlignMins()
                    # maxs = self.WorldAlignMaxs()
                    # color = playermgr.dbplayers[self.GetOwnerNumber()].color
                    # TODO: Replace by a particle effect
                    #self.burrowtexture = ProjectedTexture( 'decals/testeffect', mins, maxs, self.GetAbsOrigin(), 
                    #        self.GetAbsAngles(), color.r(), color.g(), color.b(), color.a() ) 
                    self.AddToEntityList(ENTITY_LIST_SIMULATE)
                elif not self.burrowed and self.burrowtexture:
                    self.burrowtexture.Shutdown()
                    self.burrowtexture = None  
            elif self.burrowtexture:
                self.burrowtexture.Shutdown()
                self.burrowtexture = None 
            self.UpdateAbilities()
        
    def EventHandlerStartBurrow(self, data=0):
        # Link throwing up dust to the animation
        #if isclient:
            #CreateDust(self.GetAbsOrigin(), self.GetAbsAngles())
        self.animstate.isburrowed = True
        self.animstate.specificmainactivity = self.ACT_ANTLION_BURROW_IN
        self.animstate.RestartMainSequence()
                
    def EventHandlerStopBurrow(self, data=0):
        #if isclient:
            #CreateDust(self.GetAbsOrigin(), self.GetAbsAngles())
            
        self.animstate.isburrowed = False
        self.animstate.specificmainactivity = self.ACT_ANTLION_BURROW_OUT
        self.animstate.RestartMainSequence()
       
    '''
    def ShouldJump(self):
        if self.enemy == None:
            return False

        #Too soon to try to jump
        if self.jumptime > gpGlobals.curtime:
            return False

        # only jump if you're on the ground
        if not (self.GetFlags() & FL_ONGROUND): # or self.GetNavType() == NAV_JUMP:
            return False

        # Don't jump if I'm not allowed
        #if ( CapabilitiesGet() & bits_CAP_MOVE_JUMP ) == False:
        #    return false

        vEnemyForward = Vector()
        vForward = Vector()

        self.enemy.GetVectors(vEnemyForward, None, None)
        self.GetVectors(vForward, None, None)

        flDot = DotProduct( vForward, vEnemyForward )

        if flDot < 0.5:
             flDot = 0.5

        vecPredictedPos = Vector()

        #Get our likely position in two seconds
        UTIL_PredictedPosition(self.enemy, flDot * 2.5, vecPredictedPos)

        # Don't jump if we're already near the target
        if ( GetAbsOrigin() - vecPredictedPos ).LengthSqr() < (512*512):
            return False

        #Don't retest if the target hasn't moved enough
        #FIXME: Check your own distance from last attempt as well
        if (self.lastjumpattempt - vecPredictedPos).LengthSqr() < (128*128):
            self.jumptime = gpGlobals.curtime + random.uniform(1.0, 2.0)
            return False

        targetDir = (vecPredictedPos - GetAbsOrigin())

        flDist = VectorNormalize( targetDir )

        # don't jump at target it it's very close
        if flDist < ANTLION_JUMP_MIN:
            return False

        targetPos = vecPredictedPos + targetDir * (GetHullWidth()*4.0)

        #if ( CAntlionRepellant::IsPositionRepellantFree( targetPos ) == false )
        #     return false

        # Try the jump
        #AIMoveTrace_t moveTrace
        #GetMoveProbe().MoveLimit( NAV_JUMP, GetAbsOrigin(), targetPos, MASK_NPCSOLID, GetNavTargetEntity(), &moveTrace )

        #See if it succeeded
        if ( IsMoveBlocked( moveTrace.fStatus ) )
        
            if ( g_debug_antlion.GetInt() == 2 )
            
                NDebugOverlay::Box( targetPos, GetHullMins(), GetHullMaxs(), 255, 0, 0, 0, 5 )
                NDebugOverlay::Line( GetAbsOrigin(), targetPos, 255, 0, 0, 0, 5 )
            

            self.jumptime = gpGlobals.curtime + random.RandomFloat( 1.0f, 2.0f )
            return False

        #if g_debug_antlion.GetInt() == 2:
        #    NDebugOverlay.Box( targetPos, GetHullMins(), GetHullMaxs(), 0, 255, 0, 0, 5 )
        #    NDebugOverlay.Line( GetAbsOrigin(), targetPos, 0, 255, 0, 0, 5 )

        #Save this jump in case the next time fails
        self.savedjump = #moveTrace.vJumpVelocity
        self.lastjumpattempt = targetPos

        return true
    '''
    
    # Leap attack, copied from fast zombie
    def LeapAttackTouch(self, other):
        if not other.IsSolid():
            # Touching a trigger or something.
            return
            
        #self.SetCollisionGroup(self.CalculateOwnerCollisionGroup())
            
        # Stop the zombie and knock the player back
        vecNewVelocity = Vector(0, 0, self.GetAbsVelocity().z)
        self.SetAbsVelocity(vecNewVelocity)

        forward = Vector()
        AngleVectors(self.GetLocalAngles(), forward)
        # qaPunch = QAngle(15, random.randint(-5,5), random.randint(-5,5))
        # qaPunch = QAngle(-3, 5, -3)
        
        attackinfo = self.unitinfo.AttackRange
        #self.ClawAttack(100.0, attackinfo.damage, qaPunch, forward * 500, self.ZOMBIE_BLOOD_BOTH_HANDS)
        self.MeleeAttack(self.ANTLION_MELEE1_RANGE, self.unitinfo.AttackMelee.damage, QAngle(20.0, 0.0, -12.0), Vector(-250.0, 1.0, 1.0)) 
        
        self.SetTouch(None)
        
    def StartLeapAttack(self):
        self.DoAnimation(self.ANIM_LEAP_ATTACK) 
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackLeap.attackspeed
        return True
        
    def BeginAttackJump(self):
        self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
        
        self.SetTouch(self.LeapAttackTouch)
    
        # Set this to true. A little bit later if we fail to pathfind, we check
        #this value to see if we just jumped. If so, we assume we've jumped 
        # to someplace that's not pathing friendly, and so must jump again to get out.
        self.justjumped = True

        self.jumpstartaltitude = self.GetLocalOrigin().z
        
    def LeapAttackSound(self):
        pass
        
    CLAMP = 1300.0
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
            # How fast does the antlion need to travel to reach my enemy's eyes given gravity?
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
            self.locomotion.IgnoreFriction(1.0)
            self.SetAbsVelocity(vecJumpDir)
            self.nextattack = gpGlobals.curtime + 2
    
    
    # Anim event handlers
    if isserver:
        def MeleeHandler(self, event):
            pass # Animation event specified attack moment. However actual damage is already done at start of the animation.

        class AntlionWorkerSpit(TossGrenadeAnimEventHandler):
            def HandleEvent(self, unit, event):
                enemy = unit.enemy
                if enemy:
                    # Put this check somewhere else
                    if unit.activespit:
                        return
                        
                    info = unit.unitinfo.AttackRange
                
                    vSpitPos = Vector()
                    unit.GetAttachment( "mouth", vSpitPos )

                    vTarget = Vector()
                    UTIL_PredictedPosition( enemy, 0.5, vTarget ) 

                    grenade = self.TossGrenade(unit, vSpitPos, vTarget, unit.CalculateIgnoreOwnerCollisionGroup())
                    if grenade:
                        grenade.damage = info.damage
                        grenade.damagetype = info.damagetype

                        unit.activespit = grenade
                    
                        for i in range(0, 8):
                            DispatchParticleEffect( "blood_impact_yellow_01", vSpitPos + RandomVector( -12.0, 12.0 ), RandomAngle( 0, 360 ) )

                        unit.EmitSound("NPC_Antlion.PoisonShoot") 
                elif unit.controllerplayer is not None:
                    vSpitPos = Vector()
                    unit.GetAttachment( "mouth", vSpitPos )                
               
                    # Player doesn not run sensing/ai code, so enemy is None.
                    # Use the crosshair position.
                    forward = Vector()
                    AngleVectors(unit.controllerplayer.EyeAngles(), forward)
                    tr = trace_t()
                    UTIL_TraceLine(unit.controllerplayer.Weapon_ShootPosition(), unit.controllerplayer.Weapon_ShootPosition() + forward*8000, MASK_SOLID, unit, unit.CalculateIgnoreOwnerCollisionGroup(), tr)
                    vTarget = tr.endpos
                    
                    grenade = self.TossGrenade(unit, vSpitPos, vTarget, unit.CalculateIgnoreOwnerCollisionGroup())
                    
                    unit.EmitSound("NPC_Antlion.PoisonShoot") 
        
        def BurrowInHandler(self, event):
            self.EmitSound('NPC_Antlion.BurrowIn', event.eventtime)
            UTIL_ScreenShake(self.GetAbsOrigin(), 0.5, 80.0, 1.0, 256.0, SHAKE_START)
                
        def BurrowOutHandler(self, event):
            self.EmitSound('NPC_Antlion.BurrowOut', event.eventtime)
            UTIL_ScreenShake(self.GetAbsOrigin(), 0.5, 80.0, 1.0, 256.0, SHAKE_START)  

        def VanishHandler(self, event=None):
            self.takedamage = DAMAGE_NO
            self.SetWings(False)   
            #self.AddEffects(EF_NODRAW)

    # Vars    
    ANTLION_MELEE1_RANGE = 100.0
    ANTLION_SKIN_COUNT = 4
    ANTLIONWORKER_BURSTDAMAGE = 25.0
    ANTLIONWORKER_BURSTRADIUS = 64.0
    ANTLIONWORKER_SPITSPEED = 600
    ANTLIONSUICIDER_BURSTDAMAGE = 100.0
    ANTLIONSUICIDER_BURSTRADIUS = 35.0
    dontexplode = False
    
    jumpheight = 200.0
    constructactivity = 'ACT_ANTLION_FRUSTRATION1'
    isflipped = False
    loopingstarted = False
    gravityinair = 0.4
    
    jumptime = 0.0
    savedjump = Vector(vec3_origin)
    lastjumpattempt = Vector(vec3_origin)
    
    burrowtexture = None
    burrowed = BooleanField(value=False, networked=True, clientchangecallback='OnBurrowedChanged', keyname='burrowed')
    
    # Default vars
    assignedgrub = None
    carryinggrub = None
    
    # Spawn flags
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_ANTLION_WORKER', ( 1 << 16 ), False), # Use the "worker" model
        ('SF_ANTLION_SUICIDER', ( 1 << 17 ), False)], 
        cppimplemented=True)
            
    # Events
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_STARTBURROW' : EventHandlerStartBurrow,
        'ANIM_STOPBURROW' : EventHandlerStopBurrow,
        'ANIM_FLIP' : EventHandlerAnimation('ACT_ANTLION_FLIP'),
        'ANIM_LEAP_ATTACK' : EventHandlerAnimation('ACT_ANTLION_JUMP_START'),
    } )
    
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_ANTLION_DISTRACT',
        'ACT_ANTLION_DISTRACT_ARRIVED',
        'ACT_ANTLION_BURROW_IN',
        'ACT_ANTLION_BURROW_OUT',
        'ACT_ANTLION_BURROW_IDLE',
        'ACT_ANTLION_CHARGE_IN',
        'ACT_ANTLION_CHARGE_LOOP',
        'ACT_ANTLION_CHARGE_OUT',
        'ACT_ANTLION_FRUSTRATION1',
        'ACT_ANTLION_RUN_AGITATED',
        'ACT_ANTLION_FLIP',
        'ACT_ANTLION_POUNCE',
        'ACT_ANTLION_POUNCE_MOVING',
        'ACT_ANTLION_DROWN',
        'ACT_ANTLION_JUMP_START',
        'ACT_ANTLION_LAND',
        'ACT_ANTLION_WORKER_EXPLODE',
        'ACT_ANTLION_ZAP_FLIP'
    ] )
    
    # Activity translation table
    acttables = { 
        Activity.ACT_MP_JUMP_START : 'ACT_ANTLION_JUMP_START',
        Activity.ACT_MP_JUMP_LAND : 'ACT_ANTLION_LAND',
        Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_GLIDE,
    }
    
    if isserver:
        # Animation Event Table
        aetable = {
            'AE_ANTLION_WALK_FOOTSTEP' : BaseAnimEventHandler(),
            'AE_ANTLION_MELEE_HIT1' : MeleeHandler,
            'AE_ANTLION_MELEE_HIT2' : MeleeHandler,
            'AE_ANTLION_MELEE_POUNCE' : None,
            'AE_ANTLION_FOOTSTEP_SOFT' : BaseAnimEventHandler(),
            'AE_ANTLION_FOOTSTEP_HEAVY' : BaseAnimEventHandler(),
            'AE_ANTLION_START_JUMP' : LeapAttack,
            'AE_ANTLION_BURROW_IN' : BurrowInHandler,
            'AE_ANTLION_BURROW_OUT' : BurrowOutHandler,
            'AE_ANTLION_VANISH' : VanishHandler,
            'AE_ANTLION_OPEN_WINGS' : WingsOpenHandler,
            'AE_ANTLION_CLOSE_WINGS' : WingsCloseHandler,
            'AE_ANTLION_MELEE1_SOUND' : EmitSoundAnimEventHandler('NPC_Antlion.MeleeAttackSingle'),
            'AE_ANTLION_MELEE2_SOUND' : EmitSoundAnimEventHandler('NPC_Antlion.MeleeAttackDouble'),
            'AE_ANTLION_WORKER_EXPLODE_SCREAM' : None, 
            'AE_ANTLION_WORKER_EXPLODE_WARN' : None, 
            'AE_ANTLION_WORKER_EXPLODE' : None,
            'AE_ANTLION_WORKER_SPIT' : AntlionWorkerSpit("grenade_spit", ANTLIONWORKER_SPITSPEED),
            'AE_ANTLION_WORKER_DONT_EXPLODE' : None,
        }
    
    # Replace the default animstate class
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=20.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        """ Special animstate for antlion """
        def __init__(self, outer, animconfig):
            super().__init__(outer, animconfig)
            
            self.isburrowed = outer.burrowed
            
        def OnNewModel(self):
            super().OnNewModel()
            
            studiohdr = self.outer.GetModelPtr()
            
            headpitch = self.outer.LookupPoseParameter(studiohdr, "head_pitch")
            if headpitch < 0:
                return
            headyaw = self.outer.LookupPoseParameter(studiohdr, "head_yaw")
            if headyaw < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, headpitch, 0.0)
            self.outer.SetPoseParameter(studiohdr, headyaw, 0.0)
            
            self.isburrowed = self.outer.burrowed
            if self.isburrowed:
                self.specificmainactivity = self.outer.ACT_ANTLION_BURROW_IDLE
            
        def OnEndSpecificActivity(self, specificactivity):
            if self.isburrowed:
                return self.outer.ACT_ANTLION_BURROW_IDLE
            return super().OnEndSpecificActivity(specificactivity)
        
    # Antlion AI
    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionIdle(BaseClass.BehaviorGenericClass.ActionIdle):
                def OnStart(self):
                    if self.outer.burrowed:
                        return self.ChangeTo(self.behavior.ActionBurrow, 'Starting burrowed..')
                    return super().OnStart()

                def OnBurrow(self):
                    return self.ChangeTo(self.behavior.ActionBurrow, 'Burrowing..')

                def OnFlip(self):
                    return self.ChangeTo(self.behavior.ActionFlip, 'Flipping...')

                def OnForceField(self, forcefield):
                    self.outer.Flip(True)
                    return self.Continue()

            class ActionBurrow(BaseAction):
                def OnStart(self):
                    outer = self.outer
                    if not outer.burrowed: # In case the antlion was spawned burrowed
                        outer.DoAnimation(self.outer.ANIM_STARTBURROW)
                        outer.burrowed = True
                    outer.aimoving = True
                    outer.AddSolidFlags(FSOLID_NOT_SOLID)
                    outer.SetCanBeSeen(False)
            
                def Update(self):
                    if self.outer.tamer:
                        self.outer.UnBurrow()
                    else:
                        return super().Update()
                def OnEnd(self):
                    outer = self.outer
                    outer.takedamage = DAMAGE_YES
                    outer.aimoving = False
                    outer.burrowed = False
                    #outer.RemoveEffects(EF_NODRAW)
                    outer.SetCanBeSeen(True)
                    
                def OnUnBurrow(self):
                    self.outer.DoAnimation(self.outer.ANIM_STOPBURROW)
                    return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Unburrowed', self.outer.animstate.specificmainactivity, self.behavior.ActionIdle)
                
            class ActionFlip(BaseAction):
                def OnStart(self):
                    self.outer.aimoving = True
                    self.outer.isflipped = True
                    self.outer.DoAnimation(self.outer.ANIM_FLIP)
                    return self.SuspendFor(self.behavior.ActionWaitForActivity, "Flipped...", self.outer.animstate.specificmainactivity)
                    
                def OnEnd(self):
                    self.outer.aimoving = False
                
                def OnResume(self):
                    self.outer.isflipped = False
                    return self.ChangeTo(self.behavior.ActionIdle, "Done flipped")
    tamer = None

# Register unit
# Note: info object without name is not registered.
class AntlionInfoShared(UnitInfo):
    cls_name = 'unit_antlion'
    hulltype = 'HULL_MEDIUM'
    attributes = ['chitin']
    sound_select = 'unit_antlion_select'
    sound_move = 'unit_antlion_move'
    sound_attack = 'unit_antlion_attack'
    sound_death = 'NPC_Antlion.Pain'
    
    maxspeed = 354.90
    turnspeed = 300.0
    
    scrapdropchance=0.0
    
    # Antlion melee attack
    class AttackMelee(UnitInfo.AttackMelee):
        damage = 10
        damagetype = DMG_SLASH
        attackspeed = 1.5

    class AttackSlash(AttackMelee):
        damage = 2
        damagetype = DMG_SLASH
        attackspeed = 1.0

    # Worker acid attack
    class AttackRange(UnitInfo.AttackRange):
        damage = 20
        damagetype = DMG_ACID
        attackspeed = 1.6
        maxrange = 704.0
        
    # Antlion jump attack
    class AttackLeap(UnitInfo.AttackBase):
        cone = 0.7
        damage = 15
        damagetype = DMG_SLASH
        attackspeed = 2.0
        minrange = 256.0
        maxrange = 720.0
        requiresmovement = True
        
        nextattacktime = 0.0
        
        def ShouldUpdateAttackInfo(self, unit): 
            return self.nextattacktime < gpGlobals.curtime

        def CanAttack(self, enemy):
            unit = self.unit
            if self.nextattacktime > gpGlobals.curtime:
                return False
            return unit.CanRangeAttack(enemy)

        def Attack(self, enemy, action):
            self.nextattacktime = gpGlobals.curtime + 6.0
            return self.unit.StartLeapAttack()
        
    attacks = ['AttackMelee']

    class AttackFly(AttackLeap):
        damage = 120
        minrange = 64.0
        maxrange = 768.0

class AntlionInfo(AntlionInfoShared):
    name = 'unit_antlion'
    attributes = ['chitin', 'creature', 'slash']
    abilities = {
        0 : 'burrow',
        1 : 'unburrow',
        8 : 'attackmove',
        9 : 'holdposition',
    }
    image_name = 'vgui/antlions/units/unit_ant_antlion.vmt'
    portrait = 'resource/portraits/antlionPortrait.bik'
    costs = [[('requisition', 10)], [('grubs', 1)]]
    buildtime = 5.0
    health = 80
    displayname = '#Antlion_Name'
    description = '#Antlion_Description'
    modelname = 'models/antlion.mdl'
    attacks = ['AttackMelee', 'AttackLeap']
    population = 0

class AntlionWorkerInfo(AntlionInfoShared):
    name = 'unit_antlionworker'
    keyvalues = {'spawnflags' : str(UnitAntlion.SF_ANTLION_WORKER)}
    abilities = {
        0 : 'burrow',
        1 : 'unburrow',
        2 : 'harvest',
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'construct',
        11 : 'build_ant_minihive',
    }
    image_name = 'vgui/units/unit_antlion_worker.vmt'
    image_dis_name = 'vgui/units/unit_antlion_worker_dis.vmt'
    portrait = 'resource/portraits/antlionWorkerPortrait.bik'
    costs = [('grubs', 1)]
    buildtime = 35.0
    health = 120
    displayname = '#AntlionWorker_Name'
    description = '#AntlionWorker_Description' 
    modelname = 'models/antlion_worker.mdl'
    attacks = ['AttackMelee', 'AttackRange']
    
class AntlionSuiciderInfo(AntlionInfoShared):
    name = 'unit_antlionsuicider'
    attributes = ['chitin', 'creature', 'acid']
    keyvalues = {'spawnflags' : str(UnitAntlion.SF_ANTLION_SUICIDER)}
    abilities = {
        0 : 'burrow',
        1 : 'unburrow',
        8 : 'attackmove',
        9 : 'holdposition',
    }
    image_name = 'vgui/units/unit_antlion_worker.vmt'
    image_dis_name = 'vgui/units/unit_antlion_worker_dis.vmt'
    portrait = 'resource/portraits/antlionWorkerPortrait.bik'
    costs = [('grubs', 1)]
    viewdistance = 704
    buildtime = 22.0
    scale = 1.0
    health = 90
    maxspeed = 432
    techrequirements = ['tier2_research']   
    displayname = '#AntlionSuicider_Name'
    description = '#AntlionSuicider_Description' 
    modelname = 'models/antlion_worker.mdl'

# Mission versions
class SmallAntlion(AntlionInfoShared):
    name = 'unit_antlion_small'
    attributes = ['chitin', 'creature', 'slash']
    abilities = {
        0 : 'burrow',
        1 : 'unburrow',
        8 : 'attackmove',
        9 : 'holdposition',
    }
    image_name = 'vgui/antlions/units/unit_ant_antlion.vmt'
    portrait = 'resource/portraits/antlionPortrait.bik'
    scrapdropchance = 0.0
    health = 90
    viewdistance = 576
    sensedistance = 1200
    scale = 0.75
    displayname = '#Antlion_Name'
    description = '#Antlion_Description'
    modelname = 'models/antlion.mdl'
    attacks = ['AttackSlash', 'AttackFly']
    population = 0
    #tier = 1

class MissionAntlionWorker(AntlionWorkerInfo):
    name = 'mission_unit_antlionworker'
    hidden = True
    scrapdropchance = 0.0
    viewdistance = 704
    engagedistance = 700
    health = 70

class MissionAntlionSuicider(AntlionSuiciderInfo):
    name = 'mission_unit_antlionsuicider'
    hidden = False
    scrapdropchance = 0.0
    costs = [('requisition', 4)]
    techrequirements = []
    buildtime = 2.0
    health = 35
    scale = 0.6