from srcbase import *
from vmath import Vector, QAngle, VectorNormalize, AngleVectors, DotProduct, RandomVector, VectorAngles, vec3_origin
import random
from entities import entity, Activity
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass, EventHandlerAnimation
from core.abilities import AbilityUpgrade, AbilityJumpGroup, AbilityJump
from core.attributes import AttributeInfo
from core.ents.homingprojectile import HomingProjectile
from unit_helper import UnitAnimConfig, LegAnimType_t
from particles import PrecacheParticleSystem, DispatchParticleEffect, StopParticleEffect, StopParticleEffects, PATTACH_ABSORIGIN_FOLLOW, PATTACH_POINT_FOLLOW
from wars_game.statuseffects import StunnedEffectInfo
from wars_game.buildings.neutral_barricade import NeutralBarricadeInfo
from wars_game import attributes

if isserver:
    from entities import (CPhysicsProp, FClassnameIs, PropBreakablePrecacheAll, ClearMultiDamage, CTakeDamageInfo,
                          CalculateMeleeDamageForce, ApplyMultiDamage, AddMultiDamage, RadiusDamage, CLASS_NONE,
                          CreateEntityByName, D_HT, ImpulseScale, SpawnBlood)
    from utils import (UTIL_PrecacheOther, UTIL_SetOrigin, UTIL_SetSize, 
                       UTIL_ImpactTrace, UTIL_Remove, trace_t, UTIL_TraceLine, UTIL_PointContents)
    from te import CEffectData, DispatchEffect
    from gameinterface import ConVar, PrecacheMaterial
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    
if isserver:
    hunter_cheap_explosions = ConVar("hunter_cheap_explosions", "1")
    
    s_szHunterFlechetteBubbles = "HunterFlechetteBubbles"
    s_szHunterFlechetteSeekThink = "HunterFlechetteSeekThink"
    s_szHunterFlechetteDangerSoundThink = "HunterFlechetteDangerSoundThink"
    s_szHunterFlechetteSpriteTrail = "sprites/bluelaser1.vmt"
    s_nHunterFlechetteImpact = -2
    s_nFlechetteFuseAttach = -1

    FLECHETTE_AIR_VELOCITY = 2500

    HUNTER_FOV_DOT = 0.0 # 180 degree field of view
    HUNTER_CHARGE_MIN = 256
    HUNTER_CHARGE_MAX = 1024  # what do these do anyway?
    HUNTER_FACE_ENEMY_DIST = 512.0
    HUNTER_MELEE_REACH = 80
    HUNTER_BLOOD_LEFT_FOOT = 0
    HUNTER_IGNORE_ENEMY_TIME = 5 # How long the hunter will ignore another enemy when distracted by the player.

    HUNTER_FACING_DOT = 0.8 # The angle within which we start shooting
    HUNTER_SHOOT_MAX_YAW_DEG = 60.0 # Once shooting, clamp to +/- these degrees of yaw deflection as our target moves
    HUNTER_SHOOT_MAX_YAW_COS = 0.5 # The cosine of the above angle

    HUNTER_FLECHETTE_WARN_TIME = 1.0

    HUNTER_SEE_ENEMY_TIME_INVALID = -1

    NUM_FLECHETTE_VOLLEY_ON_FOLLOW = 4

    HUNTER_SIEGE_MAX_DIST_MODIFIER = 2.0
    
    def ApplyChargeDamage(hunter, pTarget, flDamage):
        """ Purpose: Calculate & apply damage & force for a charge to a target.
            Done outside of the hunter because we need to do this inside a trace filter. """
        attackDir = ( pTarget.WorldSpaceCenter() - hunter.WorldSpaceCenter() )
        VectorNormalize( attackDir )
        offset = RandomVector( -32, 32 ) + pTarget.WorldSpaceCenter()

        # Generate enough force to make a 75kg guy move away at 700 in/sec
        # FIXME: Make it more proper, it deals too much damage.
        vecForce = attackDir * ImpulseScale( 75, 700 )

        # Deal the damage
        info = CTakeDamageInfo( hunter, hunter, vecForce, offset, flDamage, DMG_CLUB )
        pTarget.TakeDamage( info )

    @entity('hunter_flechette')
    class HunterFlechette(HomingProjectile):
        @staticmethod
        def FlechetteCreate(vecOrigin, angAngles, owner, enemy, damage=4.0, velocity=320):
            # Create a new entity with CHunterFlechette private data
            flechette = CreateEntityByName("hunter_flechette")
            UTIL_SetOrigin(flechette, vecOrigin)
            flechette.SetAbsAngles(angAngles)
            flechette.damage = damage
            flechette.velocity = velocity
            flechette.dietime = gpGlobals.curtime + 2.0
            flechette.explodetolerance = 32.0
            flechette.SetOwnerEntity(owner)
            flechette.SetOwnerNumber(owner.GetOwnerNumber())
            flechette.Spawn()
            flechette.Activate()
            flechette.SetTargetAndFire(enemy)
            return flechette

        def CreateSprites(self, bBright):
            if bBright:
                DispatchParticleEffect("hunter_flechette_trail_striderbuster", PATTACH_ABSORIGIN_FOLLOW, self)
            else:
                DispatchParticleEffect("hunter_flechette_trail", PATTACH_ABSORIGIN_FOLLOW, self)
            return True
        
        def Precache(self):
            super().Precache()

            self.PrecacheModel("sprites/light_glow02_noz.vmt")

            self.PrecacheScriptSound("NPC_Hunter.FlechetteNearmiss")
            self.PrecacheScriptSound("NPC_Hunter.FlechetteHitBody")
            self.PrecacheScriptSound("NPC_Hunter.FlechetteHitWorld")
            self.PrecacheScriptSound("NPC_Hunter.FlechettePreExplode")
            self.PrecacheScriptSound("NPC_Hunter.FlechetteExplode")

            PrecacheParticleSystem("hunter_flechette_trail_striderbuster")
            PrecacheParticleSystem("hunter_flechette_trail")
            PrecacheParticleSystem("hunter_projectile_explosion_1")
            PrecacheParticleSystem("hunter_particle_splash")
            
        def Spawn(self):
            super().Spawn()

            # Make us glow until we've hit the wall
            self.skin = 1
            
        def SetTargetAndFire(self, *args, **kwargs):
            super().SetTargetAndFire(*args, **kwargs)
            
            self.CreateSprites(False)
            
        def Activate(self):
            super().Activate()
            self.SetupGlobalModelData()
            
        def SetupGlobalModelData(self):
            global s_nHunterFlechetteImpact, s_nFlechetteFuseAttach
            if s_nHunterFlechetteImpact == -2:
                s_nHunterFlechetteImpact = self.LookupSequence("impact")
                s_nFlechetteFuseAttach = self.LookupAttachment("attach_fuse")
            
        s_nImpactCount = 0
        
        def StickTo(self, pOther, tr):
            self.EmitSound( "NPC_Hunter.FlechetteHitWorld" )

            self.SetMoveType( MOVETYPE_NONE )
            
            if not pOther.IsWorld():
                self.SetParent(pOther)
                self.SetSolid(SOLID_NONE)
                self.SetSolidFlags(FSOLID_NOT_SOLID)

            # Do an impact effect.
            #Vector vecDir = GetAbsVelocity()
            #float speed = VectorNormalize( vecDir )

            #Vector vForward
            #AngleVectors( GetAbsAngles(), &vForward )
            #VectorNormalize ( vForward )

            #CEffectData	data
            #data.m_vOrigin = tr.endpos
            #data.m_vNormal = vForward
            #data.m_nEntIndex = 0
            #DispatchEffect( "BoltImpact", data )
            
            vecVelocity = self.GetAbsVelocity()
            bAttachedToBuster = False #StriderBuster_OnFlechetteAttach( pOther, vecVelocity )

            self.SetTouch(None)

            # We're no longer flying. Stop checking for water volumes.
            self.SetThink(None, 0, s_szHunterFlechetteBubbles)

            # Stop seeking.
            self.seektarget = None
            self.SetThink(None, 0, s_szHunterFlechetteSeekThink)

            # Get ready to explode.
            if not bAttachedToBuster:
                self.SetThink(self.DangerSoundThink)
                self.SetNextThink(gpGlobals.curtime + (self.explodedelay - HUNTER_FLECHETTE_WARN_TIME))
            else:
                self.DangerSoundThink()

            # Play our impact animation.
            self.ResetSequence(s_nHunterFlechetteImpact)

            self.s_nImpactCount += 1
            if self.s_nImpactCount & 0x01:
                UTIL_ImpactTrace(tr, DMG_BULLET)
                
                # Shoot some sparks
                # TODO
                #if UTIL_PointContents(self.GetAbsOrigin()) != CONTENTS_WATER:
                #    te.Sparks(self.GetAbsOrigin())

        def FlechetteTouch(self, pOther):
            if pOther.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS | FSOLID_TRIGGER):
                # Some NPCs are triggers that can take damage (like antlion grubs). We should hit them.
                if (pOther.takedamage == DAMAGE_NO) or (pOther.takedamage == DAMAGE_EVENTS_ONLY):
                    return

            if FClassnameIs(pOther, "hunter_flechette"):
                return

            tr = super().GetTouchTrace()

            if pOther.takedamage != DAMAGE_NO:
                vecNormalizedVel = self.GetAbsVelocity()

                ClearMultiDamage()
                VectorNormalize(vecNormalizedVel)

                damage = self.damage
                #CBreakable *pBreak = dynamic_cast <CBreakable *>(pOther)
                #if ( pBreak and ( pBreak.GetMaterialType() == matGlass ) )
                #{
                #    damage = MAX( pOther.GetHealth(), damage )
                #}

                dmgInfo = CTakeDamageInfo(self, self.GetOwnerEntity(), damage, DMG_DISSOLVE | DMG_NEVERGIB)
                CalculateMeleeDamageForce(dmgInfo, vecNormalizedVel, tr.endpos, 0.7)
                dmgInfo.SetDamagePosition(tr.endpos)
                pOther.DispatchTraceAttack(dmgInfo, vecNormalizedVel, tr)

                ApplyMultiDamage()

                # Keep going through breakable glass.
                if pOther.GetCollisionGroup() == COLLISION_GROUP_BREAKABLE_GLASS:
                     return
                     
                self.SetAbsVelocity(Vector(0, 0, 0))

                # play body "thwack" sound
                self.EmitSound( "NPC_Hunter.FlechetteHitBody" )

                StopParticleEffects(self)

                vForward = Vector()
                AngleVectors(self.GetAbsAngles(), vForward)
                VectorNormalize(vForward)

                tr2 = trace_t()
                UTIL_TraceLine(self.GetAbsOrigin(), self.GetAbsOrigin() + vForward * 128, MASK_BLOCKLOS, pOther, COLLISION_GROUP_NONE, tr2)

                if tr2.fraction != 1.0:
                    #ndebugoverlay.Box( tr2.endpos, Vector( -16, -16, -16 ), Vector( 16, 16, 16 ), 0, 255, 0, 0, 10 )
                    #ndebugoverlay.Box( GetAbsOrigin(), Vector( -16, -16, -16 ), Vector( 16, 16, 16 ), 0, 0, 255, 0, 10 )

                    '''
                    if tr2.ent == None or (tr2.ent and tr2.ent.GetMoveType() == MOVETYPE_NONE):
                        data = CEffectData()

                        data.origin = tr2.endpos
                        data.normal = vForward
                        data.entindex = tr2.fraction != 1.0
                    
                        #DispatchEffect( "BoltImpact", data )'''

                if ( ((pOther.GetMoveType() == MOVETYPE_VPHYSICS) or (pOther.GetMoveType() == MOVETYPE_PUSH)) and 
                    ((pOther.health > 0) or (pOther.takedamage == DAMAGE_EVENTS_ONLY)) ):
                    #pProp = dynamic_cast<CPhysicsProp *>( pOther )
                    #if pProp:
                    #    pProp.SetInteraction( PROPINTER_PHYSGUN_NOTIFY_CHILDREN )
                
                    # We hit a physics object that survived the impact. Stick to it.
                    self.StickTo(pOther, tr)
                else:
                    self.SetTouch(None)
                    self.SetThink(None)
                    self.SetThink(None, 0, s_szHunterFlechetteBubbles)

                    UTIL_Remove(self)
            else:
                # See if we struck the world
                if pOther.GetMoveType() == MOVETYPE_NONE and not( tr.surface.flags & SURF_SKY ):
                    # We hit a physics object that survived the impact. Stick to it.
                    self.StickTo( pOther, tr )
                elif pOther.GetMoveType() == MOVETYPE_PUSH and FClassnameIs(pOther, "func_breakable"):
                    # We hit a func_breakable, stick to it.
                    # The MOVETYPE_PUSH is a micro-optimization to cut down on the classname checks.
                    self.StickTo( pOther, tr )
                else:
                    # Put a mark unless we've hit the sky
                    if (tr.surface.flags & SURF_SKY) == False:
                        UTIL_ImpactTrace(tr, DMG_BULLET)

                    UTIL_Remove(self)

        def BubbleThink(self):
            """ Think every 0.1 seconds to make bubbles if we're flying through water. """
            self.SetNextThink(gpGlobals.curtime + 0.1, s_szHunterFlechetteBubbles)

            if self.GetWaterLevel()  == 0:
                return

            UTIL_BubbleTrail(self.GetAbsOrigin() - self.GetAbsVelocity() * 0.1, self.GetAbsOrigin(), 5)
            
        def Shoot(self, vecVelocity, bBrightFX):
            self.vecshootposition = self.GetAbsOrigin()

            self.SetAbsVelocity(vecVelocity)

            # Doppler think is single player only, needs mp implementation
            #self.SetThink(self.DopplerThink)
            #self.SetNextThink(gpGlobals.curtime)

            self.SetThink(self.BubbleThink, gpGlobals.curtime + 0.1, s_szHunterFlechetteBubbles)

        def DangerSoundThink(self):
            self.EmitSound( "NPC_Hunter.FlechettePreExplode" )

            #CSoundEnt.InsertSound( SOUND_DANGER|SOUND_CONTEXT_EXCLUDE_COMBINE, GetAbsOrigin(), 150.0f, 0.5, self )
            self.SetThink(self.ExplodeThink)
            self.SetNextThink(gpGlobals.curtime + HUNTER_FLECHETTE_WARN_TIME)

        def ExplodeThink(self):
            self.Explode()

        s_nExplosionCount = 0
        
        def Explode(self):
            self.SetSolid( SOLID_NONE )

            # Don't catch self in own explosion!
            self.takedamage = DAMAGE_NO

            self.EmitSound( "NPC_Hunter.FlechetteExplode" )
            
            # Move the explosion effect to the tip to reduce intersection with the world.
            vecFuse = Vector()
            self.GetAttachment( s_nFlechetteFuseAttach, vecFuse )
            #DispatchParticleEffect("hunter_projectile_explosion_1", vecFuse, self.GetAbsAngles(), None)
            DispatchParticleEffect("hunter_particle_splash", vecFuse, self.GetAbsAngles(), None)

            nDamageType = DMG_DISSOLVE
            
            owner = self.GetOwnerEntity()
            
            explodedamage = self.damage
            
            # Perf optimization - only every other explosion makes a physics force. self is
            # hardly noticeable since flechettes usually explode in clumps.
            self.s_nExplosionCount += 1
            if (self.s_nExplosionCount & 0x01) and hunter_cheap_explosions.GetBool():
                nDamageType |= DMG_PREVENT_PHYSICS_FORCE

            if self.projtarget:
                origin = self.GetAbsOrigin()
                #vecNormalizedVel = self.GetAbsVelocity()

                #ClearMultiDamage()
                #VectorNormalize(vecNormalizedVel)
                
                dmginfo = CTakeDamageInfo(self, owner, explodedamage, DMG_DISSOLVE | DMG_NEVERGIB)
                dmginfo.attributes = owner.attributes if owner else None
                #CalculateMeleeDamageForce(dmginfo, vecNormalizedVel, origin, 0.7)
                dmginfo.SetDamagePosition(origin)

                #AddMultiDamage(dmginfo, self.projtarget)
                RadiusDamage(dmginfo, self.GetAbsOrigin(), self.exploderadius, CLASS_NONE, None)
                #ApplyMultiDamage()
                #self.projtarget.TakeDamage(dmginfo)   #double damage does?
            else:
                dmginfo = CTakeDamageInfo(self, owner, explodedamage, nDamageType)
                dmginfo.attributes = owner.attributes if owner else None
                RadiusDamage(dmginfo, self.GetAbsOrigin(), self.exploderadius, CLASS_NONE, None)
                        
            self.AddEffects(EF_NODRAW)

            self.SetThink(self.SUB_Remove)
            self.SetNextThink(gpGlobals.curtime + 0.1)
            
        modelname = "models/weapons/hunter_flechette.mdl"
        damage = 4.0
        #explodedamage = 12.0
        exploderadius = 48.0
        explodedelay = 2.5

@entity('unit_hunter', networked=True)
class UnitHunter(BaseClass):
    if isserver:
        def Precache(self):
            super().Precache()
        
            PropBreakablePrecacheAll("models/hunter.mdl")

            self.PrecacheScriptSound( "NPC_Hunter.Idle" )
            self.PrecacheScriptSound( "NPC_Hunter.Scan" )
            self.PrecacheScriptSound( "NPC_Hunter.Alert" )
            self.PrecacheScriptSound( "NPC_Hunter.Pain" )
            self.PrecacheScriptSound( "NPC_Hunter.PreCharge" )
            self.PrecacheScriptSound( "NPC_Hunter.Angry" )
            self.PrecacheScriptSound( "NPC_Hunter.Death" )
            self.PrecacheScriptSound( "NPC_Hunter.FireMinigun" )
            self.PrecacheScriptSound( "NPC_Hunter.Footstep" )
            self.PrecacheScriptSound( "NPC_Hunter.BackFootstep" )
            self.PrecacheScriptSound( "NPC_Hunter.FlechetteVolleyWarn" )
            self.PrecacheScriptSound( "NPC_Hunter.FlechetteShoot" )
            self.PrecacheScriptSound( "NPC_Hunter.FlechetteShootLoop" )
            self.PrecacheScriptSound( "NPC_Hunter.FlankAnnounce" )
            self.PrecacheScriptSound( "NPC_Hunter.MeleeAnnounce" )
            self.PrecacheScriptSound( "NPC_Hunter.MeleeHit" )
            self.PrecacheScriptSound( "NPC_Hunter.TackleAnnounce" )
            self.PrecacheScriptSound( "NPC_Hunter.TackleHit" )
            self.PrecacheScriptSound( "NPC_Hunter.ChargeHitEnemy" )
            self.PrecacheScriptSound( "NPC_Hunter.ChargeHitWorld" )
            self.PrecacheScriptSound( "NPC_Hunter.FoundEnemy" )
            self.PrecacheScriptSound( "NPC_Hunter.FoundEnemyAck" )
            self.PrecacheScriptSound( "NPC_Hunter.DefendStrider" )
            self.PrecacheScriptSound( "NPC_Hunter.HitByVehicle" )

            PrecacheParticleSystem( "hunter_muzzle_flash" )
            PrecacheParticleSystem( "blood_impact_synth_01" )
            PrecacheParticleSystem( "blood_impact_synth_01_arc_parent" )
            PrecacheParticleSystem( "blood_spurt_synth_01" )
            PrecacheParticleSystem( "blood_drip_synth_01" )

            #PrecacheInstancedScene( "scenes/npc/hunter/hunter_scan.vcd" )
            #PrecacheInstancedScene( "scenes/npc/hunter/hunter_eyeclose.vcd" )
            #PrecacheInstancedScene( "scenes/npc/hunter/hunter_roar.vcd" )
            #PrecacheInstancedScene( "scenes/npc/hunter/hunter_pain.vcd" )
            #PrecacheInstancedScene( "scenes/npc/hunter/hunter_eyedarts_top.vcd" )
            #PrecacheInstancedScene( "scenes/npc/hunter/hunter_eyedarts_bottom.vcd" )
            
            PrecacheMaterial( "effects/water_highlight" )

            UTIL_PrecacheOther( "hunter_flechette" )
            #UTIL_PrecacheOther( "sparktrail" )

    def Spawn(self):
        super().Spawn()
        
        self.SetBloodColor(DONT_BLEED)

    if isclient:
        bleedingfx = None
        
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            # Start bleeding at 30% health.
            if (self.health <= self.maxhealth * 0.3):
                self.StartBleeding()
            else:
                self.StopBleeding()
        
        def StartBleeding(self):
            if self.isbleeding:
                return
            self.isbleeding = True
            
            prop = self.ParticleProp()

            # Start gushing blood from our... anus or something.
            if not self.bleedingfx:
                #print('Bleeding fx: %s' % (self.animstate.headbottomattachment))
                self.bleedingfx = prop.Create("blood_drip_synth_01", PATTACH_POINT_FOLLOW, self.animstate.headbottomattachment)

            # Emit spurts of our blood
            self.SetNextClientThink(gpGlobals.curtime + 0.1)
           
        def StopBleeding(self):
            if not self.isbleeding:
                return
                
            prop = self.ParticleProp()
            if self.bleedingfx:
                prop.StopEmission(self.bleedingfx)
                self.bleedingfx = None
                
            #StopParticleEffect(self, 'blood_drip_synth_01')
            #StopParticleEffects(self)
            self.isbleeding = False
            
        def ClientThink(self):
            """ Our health is low. Show damage effects. """
            if not self.isbleeding:
                return
                
            prop = self.ParticleProp()
                
            # Spurt blood from random points on the hunter's head.
            vecOrigin = Vector()
            angDir = QAngle()
            self.GetAttachment(self.animstate.headcenterattachment, vecOrigin, angDir)
            
            vecDir = RandomVector( -1, 1 )
            VectorNormalize( vecDir )
            VectorAngles( vecDir, Vector( 0, 0, 1 ), angDir )

            vecDir *= self.animstate.headradius
            DispatchParticleEffect( "blood_spurt_synth_01", vecOrigin + vecDir, angDir )
            #print('BleedThink: %s' % (vecOrigin))
            #prop.Create("blood_spurt_synth_01", vecOrigin + vecDir, angDir)

            self.SetNextClientThink(gpGlobals.curtime + random.uniform(0.6, 1.5))

    def DoMuzzleFlash(self, nAttachment):
        super().DoMuzzleFlash()
        
        DispatchParticleEffect("hunter_muzzle_flash", PATTACH_POINT_FOLLOW, self, nAttachment)

        # Dispatch the elight
        data = CEffectData()
        data.attachmentindex = nAttachment
        data.entindex = self.entindex()
        DispatchEffect("HunterMuzzleFlash", data)

    def GetShootDir(self, vecSrc, pTargetEntity, bStriderBuster, nShotNum, bSingleShot):
        """ Given a target to shoot at, decide where to aim. """
        #RestartGesture( ACT_HUNTER_GESTURE_SHOOT )

        self.EmitSound("NPC_Hunter.FlechetteShoot")

        vecBodyTarget = Vector()

        #if pTargetEntity.Classify() == CLASS_PLAYER_ALLY_VITAL:
            # Shooting at Alyx, most likely (in EP2). The attack is designed to displace
            # her, not necessarily actually harm her. So shoot at the area around her feet.
        #    vecBodyTarget = pTargetEntity.GetAbsOrigin()
        #else:
        vecBodyTarget = pTargetEntity.BodyTarget(vecSrc)

        vecTarget = Vector(vecBodyTarget)

        vecDelta = pTargetEntity.GetAbsOrigin() - self.GetAbsOrigin()
        flDist = vecDelta.Length()

        if not bStriderBuster:
            # If we're not firing at a strider buster, miss in an entertaining way for the 
            # first three shots of each volley.
            '''
            if (nShotNum < 3) and (flDist > 200):
                vecTargetForward = Vector()
                vecTargetRight = Vector()
                pTargetEntity.GetVectors(vecTargetForward,vecTargetRight, None )

                vecForward = Vector()
                self.GetVectors(vecForward, None, None)

                flDot = DotProduct(vecTargetForward, vecForward)

                if flDot < -0.8:
                    # Our target is facing us, shoot the ground between us.
                    flPerc = 0.7 + ( 0.1 * nShotNum )
                    vecTarget = self.GetAbsOrigin() + ((pTargetEntity.GetAbsOrigin() * flPerc - self.GetAbsOrigin()))
                elif flDot > 0.8:
                    # Our target is facing away from us, shoot to the left or right.
                    vecMissDir = Vector(vecTargetRight)
                    if self.missleft:
                        vecMissDir *= -1.0

                    vecTarget = pTargetEntity.EyePosition() + vecMissDir * (36.0 * (3 - nShotNum))
                else:
                    # Our target is facing vaguely perpendicular to us, shoot across their view.
                    vecTarget = pTargetEntity.EyePosition() + vecTargetForward * (36.0 * (3 - nShotNum))
            '''
            # If we can't see them, shoot where we last saw them.
            #elif not self.HasCondition( COND_SEE_ENEMY ):
            #    Vector vecDelta = vecTarget - pTargetEntity.GetAbsOrigin()
            #    vecTarget = m_vecEnemyLastSeen + vecDelta
        else:
            # If we're firing at a striderbuster, lead it.
            flSpeed = self.flechettespeed

            flSpeed *= 1.5

            flDeltaTime = flDist / flSpeed
            vecTarget = vecTarget + flDeltaTime * pTargetEntity.GetSmoothedVelocity()

        vecDir = vecTarget - vecSrc
        VectorNormalize(vecDir)
        return vecDir

    def ShootFlechette(self, pTargetEntity, bSingleShot):
        if not pTargetEntity:
            return False

        nShotNum = self.volleysize - self.flechettesqueued

        bStriderBuster = False #IsStriderBuster(pTargetEntity)

        # Choose the next muzzle to shoot from.
        vecSrc = Vector()
        angMuzzle = QAngle()

        if self.topmuzzle:
            self.GetAttachment(self.animstate.topgunattachment, vecSrc, angMuzzle)
            self.DoMuzzleFlash(self.animstate.topgunattachment)
        else:
            self.GetAttachment(self.animstate.bottomgunattachment, vecSrc, angMuzzle)
            self.DoMuzzleFlash(self.animstate.bottomgunattachment)

        self.topmuzzle = not self.topmuzzle

        vecDir = self.GetShootDir(vecSrc, pTargetEntity, bStriderBuster, nShotNum, bSingleShot)

        bClamped = False
        #if hunter_clamp_shots.GetBool():
        #    bClamped = self.ClampShootDir( vecDir )

        #manipulator = CShotManipulator(vecDir)
        #vecShoot = Vector()

        #if( IsUsingSiegeTargets() and nShotNum >= 2 && (nShotNum % 2) == 0 )
            # Near perfect accuracy for these three shots, so they are likely to fly right into the windows.
            # NOTE! In siege behavior in the map that this behavior was designed for (ep2_outland_10), the
            # Hunters will only ever shoot at siege targets in siege mode. If you allow Hunters in siege mode
            # to attack players or other NPCs, this accuracy bonus will apply unless we apply a bit more logic to it.
        #    vecShoot = manipulator.ApplySpread( VECTOR_CONE_1DEGREES * 0.5, 1.0 )
        #else:
        #    vecShoot = manipulator.ApplySpread( VECTOR_CONE_4DEGREES, 1.0 )
        vecShoot = vecDir

        angShoot = QAngle()
        VectorAngles(vecShoot, angShoot)

        attackinfo = self.unitinfo.AttackRange
        flechette = HunterFlechette.FlechetteCreate(vecSrc, angShoot, self, pTargetEntity, damage=attackinfo.damage, velocity=self.flechettespeed)

        flechette.AddEffects(EF_NOSHADOW)

        #vecShoot *= self.flechettespeed

        #flechette.Shoot(vecShoot, bStriderBuster)

        #if self.ShouldSeekTarget(pTargetEntity, bStriderBuster):
        #    flechette.SetSeekTarget( pTargetEntity )

        #if nShotNum == 1 and pTargetEntity.Classify() == CLASS_PLAYER_ALLY_VITAL:
            # Make this person afraid and react to ME, not to the flechettes. 
            # Otherwise they could be scared into running towards the hunter.
            #CSoundEnt.InsertSound( SOUND_DANGER|SOUND_CONTEXT_REACT_TO_SOURCE|SOUND_CONTEXT_EXCLUDE_COMBINE, pTargetEntity.EyePosition(), 180.0f, 2.0f, this )

        return bClamped
        
    def ChargeDamage(self, target):
        if not target:
            return

        # Might want to do this if the player is controlling an unit?
        # if target.IsPlayer()
            # # Kick the player angles
            # target.ViewPunch( QAngle( 20, 20, -30 ) )

            # Vector	dir = target.WorldSpaceCenter() - self.WorldSpaceCenter()
            # VectorNormalize( dir )
            # dir.z = 0.0
            
            # Vector vecNewVelocity = dir * 250.0
            # vecNewVelocity[2] += 128.0
            # target.SetAbsVelocity( vecNewVelocity )

            # color32 red = {128,0,0,128}
            # UTIL_ScreenFade( target, red, 1.0, 0.1f, FFADE_IN )
        
        # Damage
        flDamage = random.randrange(120, 400, 40)
        
        # If it's being held by the player, break that bond
        #Pickup_ForcePlayerToDropThisObject( target )

        # Calculate the physics force
        ApplyChargeDamage(self, target, flDamage) 
        
        # Stun target if still alive
        if target and target.IsUnit() and target.IsAlive():
            StunnedEffectInfo.CreateAndApply(target, attacker=self, duration=3)
        
    def HandleChargeImpact(self, vecImpact, hitentity):
        """ Handles the guard charging into something. Returns 0 on no impact, 1 on world and 2 on entity. """
        # Cause a shock wave from this point which will disrupt nearby physics objects
        self.ImpactShock(vecImpact, 128, 350)

        # Did we hit anything interesting?
        if not hitentity or hitentity.IsWorld():
            # Robin: Due to some of the finicky details in the motor, the guard will hit
            #		  the world when it is blocked by our enemy when trying to step up 
            #		  during a moveprobe. To get around this, we see if the enemy's within
            #		  a volume in front of the guard when we hit the world, and if he is,
            #		  we hit him anyway.
            #self.EnemyIsRightInFrontOfMe( hitentity )

            # Did we manage to find him? If not, increment our charge miss count and abort.
            if hitentity.IsWorld():
                self.chargemisses += 1
                return 1

        # Hit anything we don't like
        hitisbarricade = hitentity.IsUnit() and issubclass(getattr(hitentity, 'unitinfo', None), NeutralBarricadeInfo)
        if self.IRelationType(hitentity) == D_HT or hitisbarricade:
            if hitentity not in self.chargehitunits:
                self.EmitSound( "NPC_Hunter.ChargeHitEnemy" )

                #if not self.IsPlayingGesture( self.ACT_ANTLIONGUARD_CHARGE_HIT ):
                #    self.DoAnimation( self.ANIM_GESTURE, self.ACT_ANTLIONGUARD_CHARGE_HIT )
                
                self.ChargeDamage( hitentity )
                
                hitentity.ApplyAbsVelocityImpulse( ( self.BodyDirection2D() * 400 ) + Vector( 0, 0, 200 ) )

                if not hitentity.IsAlive():# and self.enemy == hitentity:
                    self.enemy = None

                # We've hit something, so clear our miss count
                self.chargemisses = 0
                
                self.chargehitunits.add(hitentity)
                
            isbuilding = hitentity.IsUnit() and getattr(hitentity, 'isbuilding', False)
            if not isbuilding:
                return 0 # Keep running, don't crash

        # Hit something we don't hate. If it's not moveable, crash into it.
        if hitentity.GetMoveType() == MOVETYPE_NONE or hitentity.GetMoveType() == MOVETYPE_PUSH:
            return 1

        # If it's a vphysics object that's too heavy, crash into it too.
        if hitentity.GetMoveType() == MOVETYPE_VPHYSICS:
            pPhysics = hitentity.VPhysicsGetObject()
            if pPhysics:
                # If the object is being held by the player, knock it out of his hands
                #if ( pPhysics.GetGameFlags() & FVPHYSICS_PLAYER_HELD )
                #    Pickup_ForcePlayerToDropThisObject( hitentity )
                #    return False
                    
                if not pPhysics.IsMoveable() or pPhysics.GetMass() > self.VPhysicsGetObject().GetMass() * 0.5:
                    return 1

        return 0
        
    if isserver:
        __firetimeout = 0.25
        
        def StartRangeAttack(self, enemy):
            if (gpGlobals.curtime - self.nextattacktime) > self.__firetimeout:
                self.nextattacktime = gpGlobals.curtime - 0.001
        
            while self.nextattacktime < gpGlobals.curtime:
                attackinfo = self.unitinfo.AttackRange
                self.flechettesqueued = 1
                self.ShootFlechette(enemy, False)
                self.currentburst -= 1
                if self.currentburst <= 0:
                    self.nextattacktime = gpGlobals.curtime + random.uniform(attackinfo.minresttime, attackinfo.maxresttime)
                    self.currentburst = random.randint(attackinfo.minburst, attackinfo.maxburst)
                else:
                    self.nextattacktime += + attackinfo.attackspeed
                self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
    else:
        def StartRangeAttack(self, enemy):
            self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
        
    if isserver:
        def StartMeleeAttack(self, enemy):
            # Do melee damage
            self.MeleeAttack(self.unitinfo.AttackMelee.maxrange, self.unitinfo.AttackMelee.damage, QAngle(20.0, 0.0, -12.0), Vector(-250.0, 1.0, 1.0)) 
                
            return super().StartMeleeAttack(enemy)
    
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        enthurt = self.CheckTraceHullAttack( distance, -Vector(16,16,32), Vector(16,16,32), damage, self.unitinfo.AttackMelee.damagetype, 5.0 )
        if enthurt != None:     # hitted something
            # Play a random attack hit sound
            self.EmitSound( "NPC_Hunter.MeleeHit" )
            self.EmitSound( "NPC_Hunter.TackleHit" )
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), enthurt.BloodColor(), damage)
        
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=60.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    
    class AnimStateClass(BaseClass.AnimStateClass):
        def OnNewModel(self):
            super().OnNewModel()
            
            outer = self.outer
            studiohdr = outer.GetModelPtr()
            
            self.bodyyaw = outer.LookupPoseParameter("body_yaw")
            self.bodypitch = outer.LookupPoseParameter("body_pitch")
            
            self.aimyaw = outer.LookupPoseParameter("aim_yaw")
            self.aimpitch = outer.LookupPoseParameter("aim_pitch")
            
            self.topgunattachment = outer.LookupAttachment( "top_eye" )
            self.bottomgunattachment = outer.LookupAttachment( "bottom_eye" )
            self.staggeryawposeparam = outer.LookupAttachment( "stagger_yaw" )
        
            self.headcenterattachment = outer.LookupAttachment( "head_center" )
            self.headbottomattachment = outer.LookupAttachment( "head_radius_measure" )

            # Measure the radius of the head.
            vecHeadCenter = Vector()
            vecHeadBottom = Vector()
            outer.GetAttachment( self.headcenterattachment, vecHeadCenter )
            outer.GetAttachment( self.headbottomattachment, vecHeadBottom )
            self.headradius = ( vecHeadCenter - vecHeadBottom ).Length()
            
            self.SetOuterPoseParameter(self.aimpitch, 0)
            self.SetOuterPoseParameter(self.aimyaw, 0)

        def OnEndSpecificActivity(self, specificactivity):
            if specificactivity == self.outer.ACT_HUNTER_CHARGE_START or specificactivity == self.outer.ACT_HUNTER_CHARGE_RUN:
                return self.outer.ACT_HUNTER_CHARGE_RUN
            return super().OnEndSpecificActivity(specificactivity)
            
        topgunattachment = -1
        bottomgunattachment = -1
        staggeryawposeparam = -1
            
    # Ability sounds
    abilitysounds = {
        'attackmove' : 'ability_comb_hunter_attackmove',
        'holdposition' : 'ability_comb_hunter_holdposition',
    }
            
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_HUNTER_DEPLOYRA2',
        'ACT_HUNTER_DODGER',
        'ACT_HUNTER_DODGEL',
        'ACT_HUNTER_GESTURE_SHOOT',
        'ACT_HUNTER_FLINCH_STICKYBOMB',
        'ACT_HUNTER_STAGGER',
        'ACT_DI_HUNTER_MELEE',
        'ACT_DI_HUNTER_THROW',
        'ACT_HUNTER_MELEE_ATTACK1_VS_PLAYER',
        'ACT_HUNTER_ANGRY',
        'ACT_HUNTER_WALK_ANGRY',
        'ACT_HUNTER_FOUND_ENEMY',
        'ACT_HUNTER_FOUND_ENEMY_ACK',
        'ACT_HUNTER_CHARGE_START',
        'ACT_HUNTER_CHARGE_RUN',
        'ACT_HUNTER_CHARGE_STOP',
        'ACT_HUNTER_CHARGE_CRASH',
        'ACT_HUNTER_CHARGE_HIT',
        'ACT_HUNTER_RANGE_ATTACK2_UNPLANTED',
        'ACT_HUNTER_IDLE_PLANTED',
        'ACT_HUNTER_FLINCH_N',
        'ACT_HUNTER_FLINCH_S',
        'ACT_HUNTER_FLINCH_E',
        'ACT_HUNTER_FLINCH_W',
    ] )
            
    # Activity translation table
    acttables = dict(BaseClass.acttables)
    acttables.update({ 
        'default' : {
            Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_GLIDE,
        }
    })
            
    # Events
    events = dict(BaseClass.events)
    events.update({
        'ANIM_STARTCHARGE' : EventHandlerAnimation('ACT_HUNTER_CHARGE_START'),
        'ANIM_STOPCHARGE' : EventHandlerAnimation('ACT_HUNTER_CHARGE_STOP'),
        'ANIM_CRASHCHARGE' : EventHandlerAnimation('ACT_HUNTER_CHARGE_CRASH'),
        'AE_BEING_JUMP' : EventHandlerAnimation(Activity.ACT_JUMP),
    })
            
    if isserver:
        # Anim events
        aetable = {
            'AE_HUNTER_FOOTSTEP_LEFT' : EmitSoundAnimEventHandler('NPC_Hunter.Footstep'),
            'AE_HUNTER_FOOTSTEP_RIGHT' : EmitSoundAnimEventHandler('NPC_Hunter.Footstep'),
            'AE_HUNTER_FOOTSTEP_BACK' : EmitSoundAnimEventHandler('NPC_Hunter.BackFootstep'),
            'AE_HUNTER_MELEE_ANNOUNCE' : EmitSoundAnimEventHandler('NPC_Hunter.MeleeAnnounce'),
            
            'AE_HUNTER_MELEE_ATTACK_LEFT' : BaseAnimEventHandler(),
            'AE_HUNTER_MELEE_ATTACK_RIGHT' : BaseAnimEventHandler(),
            'AE_HUNTER_DIE' : None,
            'AE_HUNTER_SPRAY_BLOOD' : None,
            'AE_HUNTER_START_EXPRESSION' : BaseAnimEventHandler(),
            'AE_HUNTER_END_EXPRESSION' : BaseAnimEventHandler(),
        }
        
    attackmelee1act = 'ACT_HUNTER_MELEE_ATTACK1_VS_PLAYER'
    attackrange1act = Activity.ACT_RANGE_ATTACK2
        
    topmuzzle = False
    flechettesqueued = 0
    flechettedelay = 0.1
    currentburst = 10
    missleft = False
    canshootmove = False
    chargemisses = 0
    isbleeding = False
    
    volleysize = 8
    flechettespeed = 2000

    barsoffsetz = 32.0
    
    customeyeoffset = Vector(-7.424252, -1.865250, 68.108299)
    
'''
class HunterFlechetteAttributeInfo(AttributeInfo):
    name = 'flechette'
    damage = 6
    description = '    Flechettes provide an explosive damage of %s\n' % (damage)'''

class CombineHunterUnlock(AbilityUpgrade):
    name = 'combine_hunter_unlock'
    displayname = '#CombHunterUnlock_Name'
    description = '#CombHunterUnlock_Description'
    image_name = "vgui/abilities/ability_unknown.vmt"
    buildtime = 200.0
    costs = [[('kills', 5)], [('requisition', 5)]]

class AbilityHunterJump(AbilityJumpGroup):
    name = 'hunter_jump'
    hidden = True
    jumpgravity = 0.5
    jump_start_anim_speed = 5.0
    maxrange = 768
    jump_homing = True
    only_direct = False
    only_navmesh = True
    jumpstartsound = 'NPC_Hunter.PreCharge'
    image_name = 'vgui/combine/abilities/combine_hunter_jump'
    displayname = '#AbilityHunterJump_Name'
    description = '#AbilityHunterJump_Description'
    rechargetime = 6.0
    sai_hint = AbilityJumpGroup.sai_hint | set(['sai_combine_ball'])

class CombineHunterInfo(UnitInfo):
    name = 'unit_hunter'
    cls_name = 'unit_hunter'
    displayname = '#CombHunter_Name'
    description = '#CombHunter_Description'
    image_name = 'vgui/combine/units/unit_hunter'
    costs = [('requisition', 65), ('power', 50)]
    buildtime = 43.0
    health = 300
    maxspeed = 348.0
    population = 4
    viewdistance = 896
    attributes = ['synth', 'flechette']
    modelname = 'models/hunter.mdl'
    hulltype = 'HULL_MEDIUM_TALL'
    sound_select = 'unit_hunter_select'
    sound_move = 'unit_hunter_move'
    sound_attack = 'unit_hunter_attack'
    sound_death = 'NPC_Hunter.Death'
    #tier = 3
    abilities = {
        0 : 'chargehunter',
        1: 'hunter_jump',
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'patrol',
    }
    
    class AttackMelee(UnitInfo.AttackMelee):
        damage = 70
        damagetype = DMG_SLASH
        attackspeed = 1.5
    
    class AttackRange(UnitInfo.AttackRange):
        damage = 7
        cone = 0.99
        minrange = 64.0
        maxrange = 640.0
        attackspeed = 0.1
        usesbursts = True
        minburst = 10
        maxburst = 10
        minresttime = 1.1
        maxresttime = 1.3
    attacks = ['AttackMelee', 'AttackRange']
    infest_zombietype = None # Prevent zombiefying headcrab_infest ability

class OverrunCombineHunterInfo(CombineHunterInfo):
    name = 'overrun_unit_hunter'
    hidden = True
    buildtime = 0
    techrequirements = ['or_tier3_research']
    tier = 0
    costs = [('kills', 5)]
