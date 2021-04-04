from srcbase import *
from vmath import *
import random

from fields import BooleanField, FlagsField, VectorField, FloatField, UpgradeField
from core.units import UnitInfo, UnitBaseCombat as BaseClass, UnitBaseAirLocomotion, EventHandlerAnimation, EventHandlerAnimationMisc, UnitCombatAnimStateEx
from core.abilities import AbilityUpgrade, AbilityUpgradeValue
from wars_game.statuseffects import StunnedEffectInfo

from entities import entity, Activity, FireBulletsInfo_t, FBEAM_FADEOUT
from unit_helper import UnitAnimConfig, LegAnimType_t
from utils import UTIL_PlayerByIndex, UTIL_TraceLine, UTIL_TraceEntity, trace_t, UTIL_Tracer, TRACER_DONT_USE_ATTACHMENT, UTIL_PointContents
from gamerules import GetAmmoDef
from te import CEffectData, DispatchEffect, te
import ndebugoverlay
from utils import UTIL_AngleDiff

if isserver:
    from core.units import UnitCombatAirNavigator
    from utils import (UTIL_FindWaterSurface, UTIL_ScreenShake, SHAKE_START, UTIL_YawToVector, UTIL_PrecacheOther, 
                       UTIL_BloodSpray, FX_BLOODSPRAY_ALL, FX_BLOODSPRAY_DROPS, UTIL_Remove, UTIL_Approach)
    from entities import (PropBreakableCreateAll, breakablepropparams_t, PropBreakablePrecacheAll, BCF_NO_ANIMATION_SKIP, 
                          EFL_NO_DISSOLVE, EFL_NO_MEGAPHYSCANNON_RAGDOLL, GetAttachmentPositionInSpaceOfBone,
                          BoneFollowerManager, CreateServerRagdollAttached, CTakeDamageInfo)
    from gameinterface import CPASAttenuationFilter, PrecacheMaterial, CPVSFilter, CBroadcastRecipientFilter
    from te import CreateConcussiveBlast
    from animation import Animevent
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
else:
    from te import ClientEffectRegistration, C_StriderFX
    from gameinterface import C_RecipientFilter

# Client side effect
if isclient:
    def MuzzleFlash_Strider(self, hEntity, attachmentIndex):
        # TODO
        pass
           
    def StriderMuzzleFlashCallback(data):
        pass
        #MuzzleFlash_Strider(data.entity, data.attachmentindex)
        
    StriderMuzzleFlash = ClientEffectRegistration('StriderMuzzleFlash', StriderMuzzleFlashCallback)

# Strider class
@entity('unit_strider', networked=True)
class UnitStrider(BaseClass):    
    """ Strider """
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 450.0
        self.testroutestartheight = 1024.0

        if isserver:
            self.SetShadowCastDistance(2048.0) # Use a much higher shadow cast distance
        else:
            self.cannonfx = C_StriderFX()
            
    # Shared
    if isserver:
        def Precache(self):
            PropBreakablePrecacheAll( self.unitinfo.modelname )
            
            self.PrecacheScriptSound( "NPC_Strider.StriderBusterExplode" )
            self.PrecacheScriptSound( "explode_5" )
            self.PrecacheScriptSound( "NPC_Strider.Charge" )
            self.PrecacheScriptSound( "NPC_Strider.RagdollDetach" )
            self.PrecacheScriptSound( "NPC_Strider.Whoosh" )
            self.PrecacheScriptSound( "NPC_Strider.Creak" )
            self.PrecacheScriptSound( "NPC_Strider.Alert" )
            self.PrecacheScriptSound( "NPC_Strider.Pain" )
            self.PrecacheScriptSound( "NPC_Strider.Death" )
            self.PrecacheScriptSound( "NPC_Strider.FireMinigun" )
            self.PrecacheScriptSound( "NPC_Strider.Shoot" )
            self.PrecacheScriptSound( "NPC_Strider.OpenHatch" )
            self.PrecacheScriptSound( "NPC_Strider.Footstep" )
            self.PrecacheScriptSound( "NPC_Strider.Skewer" )
            self.PrecacheScriptSound( "NPC_Strider.Hunt" )
            PrecacheMaterial( "effects/water_highlight" )
            self.impacteffecttexture = self.PrecacheModel( "sprites/physbeam.vmt" )
            PrecacheMaterial( "sprites/bluelaser1" )
            PrecacheMaterial( "effects/blueblacklargebeam" )
            PrecacheMaterial( "effects/strider_pinch_dudv" )
            PrecacheMaterial( "effects/blueblackflash" )
            PrecacheMaterial( "effects/strider_bulge_dudv" )
            PrecacheMaterial( "effects/strider_muzzle" )

            self.PrecacheModel( "models/chefhat.mdl" )

            #UTIL_PrecacheOther( "sparktrail" )

            super().Precache()
    else:
        def Precache(self):
            self.impacteffecttexture = self.PrecacheModel( "sprites/physbeam.vmt" )
            super().Precache()
            
        def ReceiveMessage(self, msg):
            messagetype = msg[0]
            if messagetype == self.STRIDER_MSG_STREAKS:
                pos = msg[1]
                self.cannonfx.SetRenderOrigin( pos )
                self.cannonfx.EffectInit( self.entindex(), self.LookupAttachment( "BigGun" ) )
                self.cannonfx.LimitTime( self.STRIDERFX_BIG_SHOT_TIME )
            elif messagetype == self.STRIDER_MSG_BIG_SHOT:
                tmp = msg[1]
                self.cannonfx.SetTime( self.STRIDERFX_BIG_SHOT_TIME )
                self.cannonfx.LimitTime( self.STRIDERFX_END_ALL_TIME )
            elif messagetype == self.STRIDER_MSG_DEAD:
                self.cannonfx.EffectShutdown()
        
        def OnHitPosChanged(self):
            self.cannonfx.Update(self, self.hit_pos)
            
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            self.cannonfx.Update(self, self.hit_pos)
            
        def UpdateOnRemove(self):
            self.cannonfx.EffectShutdown()
            self.cannonfx = None
            
            super().UpdateOnRemove()
            
    def Spawn(self):
        if isserver:
            self.EnableServerIK()
        
        self.minigunammo = GetAmmoDef().Index("StriderMinigun")
        self.minigundirectammo = GetAmmoDef().Index("StriderMinigunDirect")

        super().Spawn()

        self.SetBloodColor(DONT_BLEED)
        
        self.locomotion.desiredheight = 450.0 * self.unitinfo.scale
        self.locomotion.maxheight = 450.0 * self.unitinfo.scale
        self.body_height = self.locomotion.desiredheight
        self.STRIDER_STOMP_RANGE *= self.unitinfo.scale
        #self.locomotion.flynoiserate = 48.0
        #self.locomotion.flynoisez = 24.0
        
        if isserver:
            self.SetDefaultEyeOffset()
            
            self.AddEFlags(EFL_NO_DISSOLVE|EFL_NO_MEGAPHYSCANNON_RAGDOLL)
            
            # Don't allow us to skip animation setup because our attachments are critical to us!
            self.SetBoneCacheFlags(BCF_NO_ANIMATION_SKIP)

            origin = self.GetLocalOrigin()
            origin.z += self.locomotion.desiredheight
            
            self.SetLocalOrigin(origin)
            
    def OnUnitTypeChanged(self, oldunittype):
        super().OnUnitTypeChanged(oldunittype)
        
        if self.locomotion:
            self.locomotion.desiredheight = 450.0 * self.unitinfo.scale
            self.locomotion.maxheight = 450.0 * self.unitinfo.scale
            self.body_height = self.locomotion.desiredheight
            
    def Weapon_ShootPosition(self):
        vecShootPos = Vector()
        self.GetAttachment(self.animstate.canonattachment, vecShootPos)

        return vecShootPos

    def MakeTracer(self, vecTracerSrc, tr, iTracerType):
        self.GetAttachment(self.animstate.minigunattachment, vecTracerSrc)
        UTIL_Tracer(vecTracerSrc, tr.endpos, self.entindex(), self.animstate.minigunattachment, 5000, True, "StriderTracer")
        
    def UnitThink(self):
        super().UnitThink()
        
        if self.bone_follower_manager:
            self.bone_follower_manager.UpdateBoneFollowers(self)

        if self.speedenabled and self.energy == 0:
            self.DisableSpeed()

    if isclient:
        def DoImpactEffect(self, tr, nDamageType):
            super().DoImpactEffect(tr, nDamageType)

            # Add a halo
            #filter = CBroadcastRecipientFilter()
            filter = C_RecipientFilter()
            te.BeamRingPoint(filter, 0.0, 
                tr.endpos,							#origin
                0,									#start radius
                64,									#end radius
                self.impacteffecttexture,			#texture
                0,									#halo index
                0,									#start frame
                0,									#framerate
                0.2,								#life
                10,									#width
                0,									#spread
                0,									#amplitude
                255,								#r
                255,								#g
                255,								#b
                50,									#a
                0,									#speed
                FBEAM_FADEOUT
                )

            #filter = CPVSFilter(tr.endpos)
            filter = C_RecipientFilter()
            te.EnergySplash(filter, 0.0, tr.endpos, tr.plane.normal, False)
            
            # Punch the effect through?
            if tr.ent and not tr.ent.IsUnit():
                vecDir = tr.endpos - tr.startpos
                VectorNormalize( vecDir )

                retrace = trace_t()

                vecReTrace = tr.endpos + vecDir * 12

                if UTIL_PointContents( vecReTrace, MASK_ALL ) == CONTENTS_EMPTY:
                    UTIL_TraceLine( vecReTrace, vecReTrace - vecDir * 24, MASK_SHOT, None, COLLISION_GROUP_NONE, retrace )

                    super().DoImpactEffect( retrace, nDamageType )
                
    def DoMuzzleFlash(self):
        super().DoMuzzleFlash()
        
        data = CEffectData()
        
        data.attachmentindex = self.animstate.minigunattachment
        data.entindex = self.entindex()
        DispatchEffect( "StriderMuzzleFlash", data )
        
    def DispatchShootMinigun(self):
        enemy = self.enemy
        if enemy:
            target_pos = enemy.BodyTarget(self.GetAbsOrigin())
            self.ShootMinigun(target_pos, 0.0, vec3_origin)
        elif self.controlledbyplayer:
            player = UTIL_PlayerByIndex(self.controlledbyplayer)
            if not player:
                return
            
            forward = Vector()
            AngleVectors(player.GetAbsAngles(), forward)
            start = player.Weapon_ShootPosition()
        
            tr = trace_t()
            UTIL_TraceLine(start, start+forward*MAX_TRACE_LENGTH, MASK_SHOT, self, COLLISION_GROUP_NONE, tr)
    
            self.ShootMinigun(tr.endpos, 0.0, vec3_origin)
    
    def ShootMinigun(self, target, aimError, vecSpread):
        if target:
            muzzlePos = Vector()
            muzzleAng = QAngle()
            
            self.GetAttachment( "minigun", muzzlePos, muzzleAng )
            
            vecShootDir = target - muzzlePos
            VectorNormalize( vecShootDir )
            
            info = FireBulletsInfo_t()
            info.shots = 1
            info.vecsrc = muzzlePos
            info.vecdirshooting = vecShootDir
            info.vecspread = vecSpread
            info.distance = MAX_TRACE_LENGTH
            info.tracerfreq = 0
            info.damage = self.unitinfo.AttackRange.damage
    
            if self.minigun_use_direct_fire:
                # exactly on target w/tracer
                info.ammotype = self.minigundirectammo
            else:
                # exactly on target w/tracer
                info.ammotype = self.minigunammo
            self.FireBullets(info)

            #g_pEffects.MuzzleFlash(muzzlePos, muzzleAng, random.uniform(2.0, 4.0) , MUZZLEFLASH_TYPE_STRIDER)
            self.DoMuzzleFlash()

            self.EmitSound('NPC_Strider.FireMinigun')

    if isserver:
        __firetimeout = 0.25
        currentburst = 12

        def StartRangeAttack(self, enemy):
            if (gpGlobals.curtime - self.nextattacktime) > self.__firetimeout:
                self.nextattacktime = gpGlobals.curtime - 0.001

            while self.nextattacktime < gpGlobals.curtime:
                attackinfo = self.unitinfo.AttackRange
                #self.flechettesqueued = 1
                #self.ShootFlechette(self.enemy, False)
                self.currentburst -= 1
                if self.currentburst <= 0:
                    self.nextattacktime = gpGlobals.curtime + random.uniform(attackinfo.minresttime,
                                                                             attackinfo.maxresttime)
                    self.currentburst = random.randint(attackinfo.minburst, attackinfo.maxburst)
                else:
                    self.nextattacktime += + attackinfo.attackspeed
                self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
    else:
        def StartRangeAttack(self, enemy):
            self.DoAnimation(self.ANIM_RANGE_ATTACK1)
            return False
    # Server only
    if isserver:
        def InitBoneFollowers(self):
            self.bone_follower_manager = BoneFollowerManager()
            
            # Don't do this if we're already loaded
            if self.bone_follower_manager.GetNumBoneFollowers() != 0:
                return

            # Init our followers
            self.bone_follower_manager.InitBoneFollowers(self, self.followerbonenames)
            
        '''def CreateVPhysics(self):
            # The strider has bone followers for every solid part of its body, 
            # so there's no reason for the bounding box to be solid.
            #super().CreateVPhysics()

            if not self.disable_bonefollowers:
                self.InitBoneFollowers()

            return True'''

        def UpdateOnRemove(self):
            if self.bone_follower_manager:
                self.bone_follower_manager.DestroyBoneFollowers()
            
            super().UpdateOnRemove()
            
        def OnTakeDamage_Alive(self, info):
            damage = super().OnTakeDamage_Alive(info)
            
            inflictor = info.GetInflictor()
            
            # Two special cases for Combine Elite alt fire ability and Rebel rpg
            entclsname = inflictor.GetClassname()
            if entclsname == 'prop_combine_ball':
                StunnedEffectInfo.CreateAndApply(self, attacker=inflictor, duration=3)
                
            return damage
            
        def Explode(self):
            velocity = vec3_origin
            angVelocity = RandomAngularImpulse( -150, 150 )

            # Break into pieces
            params = breakablepropparams_t( self.EyePosition(), self.GetAbsAngles(), velocity, angVelocity )
            params.impactEnergyScale = 1.0
            params.defBurstScale = 600.0
            params.defCollisionGroup = COLLISION_GROUP_NPC
            PropBreakableCreateAll( self.GetModelIndex(), None, params, self, -1, True, True )

            # Go away
            self.lifestate = LIFE_DEAD

            self.SetThink( self.SUB_Remove )
            self.SetNextThink( gpGlobals.curtime + 0.1 )

            self.AddEffects( EF_NODRAW )
            
            self.StopSmoking()

            if self.bone_follower_manager:
                self.bone_follower_manager.DestroyBoneFollowers()

        def Event_Killed(self, info):
            super().Event_Killed(info)

            if self.bone_follower_manager:
                self.bone_follower_manager.DestroyBoneFollowers()
            
            self.CancelFireCannon()
            
        def StartSmoking(self):
            if self.smoke != None:
                return

            # TODO: Add smoke trail to python
            #self.smoke = SmokeTrail.CreateSmokeTrail()
            
            if self.smoke:
                self.smoke.m_SpawnRate = 32
                self.smoke.m_ParticleLifetime = 3.0
                self.smoke.m_StartSize = 16
                self.smoke.m_EndSize = 64
                self.smoke.m_SpawnRadius = 20
                self.smoke.m_MinSpeed = 8
                self.smoke.m_MaxSpeed = 64
                self.smoke.m_Opacity = 0.3
                
                self.smoke.m_StartColor.Init( 0.25, 0.25, 0.25 )
                self.smoke.m_EndColor.Init( 0, 0, 0 )
                self.smoke.SetLifetime( 500.0 )
                self.smoke.FollowEntity( self, "MiniGunBase" )
                
        def StopSmoking(self, delay=0.1):
            if self.smoke:
                self.smoke.SetLifetime(delay)
                
        def LeftFootHit(self, eventtime):
            footPosition = Vector()
            angles = QAngle()

            self.GetAttachment( "left foot", footPosition, angles )

            filter = CPASAttenuationFilter( self, "NPC_Strider.FootstepEverywhere" )
            self.EmitSoundFilter( filter, 0, "NPC_Strider.FootstepEverywhere", footPosition, eventtime )

            self.FootFX( footPosition )

            return footPosition

        def RightFootHit(self, eventtime):
            footPosition = Vector()

            self.GetAttachment( "right foot", footPosition )
            
            filter = CPASAttenuationFilter( self, "NPC_Strider.FootstepEverywhere" )
            self.EmitSoundFilter( filter, 0, "NPC_Strider.FootstepEverywhere", footPosition, eventtime )

            self.FootFX( footPosition )

            return footPosition

        def BackFootHit(self, eventtime):
            footPosition = Vector()

            self.GetAttachment( "back foot", footPosition )

            filter = CPASAttenuationFilter( self, "NPC_Strider.FootstepEverywhere" )
            self.EmitSoundFilter( filter, 0, "NPC_Strider.FootstepEverywhere", footPosition, eventtime )

            self.FootFX( footPosition )

            return footPosition
            
        def FootFX(self, origin):
            tr = trace_t()
            UTIL_TraceLine( origin + Vector(0, 0, 48), origin - Vector(0,0,100), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr )
            yaw = random.randint(0,120)
            
            if UTIL_PointContents( tr.endpos + Vector( 0, 0, 1 ), MASK_WATER ) & MASK_WATER:
                flWaterZ = UTIL_FindWaterSurface( tr.endpos, tr.endpos.z, tr.endpos.z + 100.0 )

                data = CEffectData()
                data.flags = 0
                data.origin = tr.endpos
                data.origin.z = flWaterZ
                data.normal = Vector( 0, 0, 1 )
                data.scale = random.uniform( 10.0, 14.0 )

                DispatchEffect( "watersplash", data )
            else:
                filter = CPVSFilter(origin)
                for i in range(0, 3):
                    dir = UTIL_YawToVector( yaw + i*120 ) * 10
                    VectorNormalize( dir )
                    dir.z = 0.25
                    VectorNormalize( dir )
                    te.Dust(filter, 0.0, tr.endpos, dir, 12, 50)

            UTIL_ScreenShake( tr.endpos, 4.0, 1.0, 0.5, 1000, SHAKE_START, False )
            
            #if npc_strider_shake_ropes_radius.GetInt():
            #    CRopeKeyframe.ShakeRopes( tr.endpos, npc_strider_shake_ropes_radius.GetFloat(), npc_strider_shake_ropes_magnitude.GetFloat() )

            #
            # My feet are scary things! NOTE: We might want to make danger sounds as the feet move
            # through the air. Then soldiers could run from the feet, which would look cool.
            #
            #CSoundEnt.InsertSound( SOUND_DANGER|SOUND_CONTEXT_EXCLUDE_COMBINE, tr.endpos, 512, 1.0, self )
            
        def WhooshLeftHandler(self, event):
            footPosition = Vector()
            self.GetAttachment("left foot", footPosition)

            sound_filter = CPASAttenuationFilter(self, "NPC_Strider.Whoosh")
            self.EmitSoundFilter(sound_filter, 0, "NPC_Strider.Whoosh", footPosition)
            
        def WhooshBackHandler(self, event):
            footPosition = Vector()
            self.GetAttachment("back foot", footPosition)

            sound_filter = CPASAttenuationFilter(self, "NPC_Strider.Whoosh")
            self.EmitSoundFilter(sound_filter, 0, "NPC_Strider.Whoosh", footPosition)
            
        def WhooshRightHandler(self, event):
            footPosition = Vector()
            self.GetAttachment("right foot", footPosition)

            sound_filter = CPASAttenuationFilter(self, "NPC_Strider.Whoosh")
            self.EmitSoundFilter(sound_filter, 0, "NPC_Strider.Whoosh", footPosition)
            
        def CalculateStompHitPosition(self, enemy):
            skewerPosition = Vector()
            footPosition = Vector()
            self.GetAttachment("left skewer", skewerPosition)
            self.GetAttachment("left foot", footPosition)
            vecStabPos = (enemy.WorldSpaceCenter() + enemy.EyePosition()) * 0.5

            return vecStabPos - skewerPosition + footPosition
            
        def StompHit(self, followerboneindex):
            enemy = self.stomp_target
            if not enemy:
                enemy = self.enemy

            enemy = enemy if enemy and enemy.IsUnit() else None
            is_valid_target = enemy and enemy.GetModelPtr()
            if self.HasSpawnFlags(self.SF_CAN_STOMP_PLAYER):
                is_valid_target = is_valid_target or (enemy and enemy.IsPlayer())

            if not is_valid_target:
                return

            # Find out which foot is doing the hitting
            attachment_name = 'left foot' if followerboneindex == self.STRIDER_LEFT_LEG_FOLLOWER_INDEX else 'right foot'
            foot_position = Vector()
            success = self.GetAttachment(attachment_name, foot_position)
            if not success:
                return

            delta = Vector()
            VectorSubtract(enemy.GetAbsOrigin(), foot_position, delta)
            delta.z = 0
            if delta.LengthSqr() > (self.STRIDER_STOMP_RANGE * self.STRIDER_STOMP_RANGE):
                return

            # DVS E3 HACK: Assume we stab our victim midway between their eyes and their center.
            stab_pos = (enemy.WorldSpaceCenter() + enemy.EyePosition()) * 0.5
            hit_position = enemy.GetAbsOrigin()

            sound_filter = CPASAttenuationFilter(self, "NPC_Strider.Skewer")
            self.EmitSoundFilter(sound_filter, 0, "NPC_Strider.Skewer", hit_position)

            damage_info = CTakeDamageInfo(self, self, 600, DMG_CRUSH)
            forward = Vector()
            enemy.GetVectors(forward, None, None)
            damage_info.SetDamagePosition(hit_position)
            damage_info.SetDamageForce(forward * -50 * 300)
            enemy.TakeDamage(damage_info)

            if not enemy or enemy.IsAlive():
                return

            blood_delta = foot_position - stab_pos
            blood_delta.z = 0 # effect looks better
            VectorNormalize(blood_delta)
            UTIL_BloodSpray(stab_pos + blood_delta * 4, blood_delta, BLOOD_COLOR_RED, 8, FX_BLOODSPRAY_ALL)
            UTIL_BloodSpray(stab_pos + blood_delta * 4, blood_delta, BLOOD_COLOR_RED, 11, FX_BLOODSPRAY_DROPS)
                

        def AimCannonAt(self, targetpos, flInterval):
            """ Aim Gun at a target.
                Returns true if you hit the target, false if not there yet."""
            #if not pEntity:
            #    return True

            gunMatrix = matrix3x4_t()
            self.GetAttachment( self.animstate.canonattachment, gunMatrix )

            # transform the enemy into gun space
            localEnemyPosition = Vector()
            VectorITransform( targetpos, gunMatrix, localEnemyPosition )
            
            # do a look at in gun space (essentially a delta-lookat)
            localEnemyAngles = QAngle()
            VectorAngles( localEnemyPosition, localEnemyAngles )
            
            # convert to +/- 180 degrees
            localEnemyAngles.x = UTIL_AngleDiff(localEnemyAngles.x, 0)
            localEnemyAngles.y = UTIL_AngleDiff(localEnemyAngles.y, 0)

            targetYaw = self.aimyaw + localEnemyAngles.y
            targetPitch = self.aimpitch + localEnemyAngles.x
            
            unitAngles = Vector( localEnemyAngles.x, localEnemyAngles.y, localEnemyAngles.z ) 
            angleDiff = VectorNormalize(unitAngles)
            aimSpeed = 16

            # Exponentially approach the target
            yawSpeed = abs(aimSpeed*flInterval*localEnemyAngles.y)
            pitchSpeed = abs(aimSpeed*flInterval*localEnemyAngles.x)

            yawSpeed = max(yawSpeed,5)
            pitchSpeed = max(pitchSpeed,5)

            self.aimyaw = UTIL_Approach( targetYaw, self.aimyaw, yawSpeed )
            self.aimpitch = UTIL_Approach( targetPitch, self.aimpitch, pitchSpeed )

            self.SetPoseParameter( self.animstate.yawcontrol, self.aimyaw )
            self.SetPoseParameter( self.animstate.pitchcontrol, self.aimpitch )

            # read back to avoid drift when hitting limits
            # as long as the velocity is less than the delta between the limit and 180, this is fine.
            self.aimpitch = self.GetPoseParameter( self.animstate.pitchcontrol )
            self.aimyaw = self.GetPoseParameter( self.animstate.yawcontrol )

            # UNDONE: Zero out any movement past the limit and go ahead and fire if the strider hit its 
            # target except for clamping.  Need to clamp targets to limits and compare?
            if angleDiff < 1:
                return True

            return False
            
        def ChargeCannon(self, targetpos):
            # Play charge sound
            filter2 = CPASAttenuationFilter(self, "NPC_Strider.Charge")
            self.EmitSoundFilter(filter2, self.entindex(), "NPC_Strider.Charge")
            
            # Start charge effect
            self.hit_pos = targetpos
            self.SendMessage( [
                self.STRIDER_MSG_STREAKS,
                targetpos,
            ] )

        def FireCannon(self, targetpos, damage=600.0, radius=256.0):
            #if GetNextThink( "CANNON_HIT" ) > gpGlobals.curtime:
            #    DevMsg( "Strider refiring cannon?\n" )
            #    return

            #m_nextShootTime = gpGlobals.curtime + 5
            tr = trace_t()
            vecShootPos = Vector()
            self.GetAttachment( self.animstate.canonattachment, vecShootPos )

            vecShootDir = targetpos - vecShootPos
            flDist = VectorNormalize( vecShootDir )

            UTIL_TraceLine( vecShootPos, vecShootPos + vecShootDir * flDist, MASK_SHOT, self, COLLISION_GROUP_NONE, tr )
            self.blasthit = tr.endpos
            self.blasthit += tr.plane.normal * 16
            self.blastnormal = tr.plane.normal

            # tell the client side effect to complete
            self.SendMessage( [
                self.STRIDER_MSG_BIG_SHOT,
                tr.endpos,
            ] )
            
            self.hit_pos = targetpos

            filter2 = CPASAttenuationFilter( self, "NPC_Strider.Shoot" )
            self.EmitSoundFilter( filter2, self.entindex(), "NPC_Strider.Shoot")
            #SetContextThink( self.CannonHitThink, gpGlobals.curtime + 0.2, "CANNON_HIT" )
            
            CreateConcussiveBlast(self.blasthit, self.blastnormal, None, 2.5, damage, radius)
            
        def CancelFireCannon(self):
            self.SendMessage([self.STRIDER_MSG_DEAD])
            
        # Event handlers
        def DieHandler(self, event):
            self.Explode()
            
        def LeftFootHitHandler(self, event):
            self.LeftFootHit(event.eventtime)
        def RightFootHitHandler(self, event):
            self.RightFootHit(event.eventtime)
        def BackFootHitHandler(self, event):
            self.BackFootHit(event.eventtime)
            
        def StompLHandler(self, event):
            self.StompHit(self.STRIDER_LEFT_LEG_FOLLOWER_INDEX)
        def StompRHandler(self, event):
            self.StompHit(self.STRIDER_RIGHT_LEG_FOLLOWER_INDEX)
        
        # Animation Events
        # Good thing the strider ones are hard coded...
        STRIDER_AE_FOOTSTEP_LEFT = 1
        STRIDER_AE_FOOTSTEP_RIGHT = 2
        STRIDER_AE_FOOTSTEP_BACK = 3
        STRIDER_AE_FOOTSTEP_LEFTM = 4
        STRIDER_AE_FOOTSTEP_RIGHTM = 5
        STRIDER_AE_FOOTSTEP_BACKM = 6
        STRIDER_AE_FOOTSTEP_LEFTL = 7
        STRIDER_AE_FOOTSTEP_RIGHTL = 8
        STRIDER_AE_FOOTSTEP_BACKL = 9
        STRIDER_AE_WHOOSH_LEFT = 11
        STRIDER_AE_WHOOSH_RIGHT = 12
        STRIDER_AE_WHOOSH_BACK = 13
        STRIDER_AE_CREAK_LEFT = 21
        STRIDER_AE_CREAK_RIGHT = 22
        STRIDER_AE_CREAK_BACK = 23
        STRIDER_AE_SHOOTCANNON = 100
        STRIDER_AE_CANNONHIT = 101
        STRIDER_AE_SHOOTMINIGUN = 105
        STRIDER_AE_STOMPHITL = 110
        STRIDER_AE_STOMPHITR = 111
        STRIDER_AE_FLICKL = 112
        STRIDER_AE_FLICKR = 113
        STRIDER_AE_WINDUPCANNON = 114

        STRIDER_AE_DIE = 999
        
        aetable = {
            STRIDER_AE_DIE : DieHandler,
            STRIDER_AE_SHOOTCANNON : None,
            STRIDER_AE_WINDUPCANNON : None,
            STRIDER_AE_CANNONHIT : None,
            STRIDER_AE_SHOOTMINIGUN : None,
            STRIDER_AE_STOMPHITL : StompLHandler,
            STRIDER_AE_STOMPHITR : StompRHandler,
            STRIDER_AE_FLICKL : None,
            STRIDER_AE_FLICKR : None,
            STRIDER_AE_FOOTSTEP_LEFT : LeftFootHitHandler,
            STRIDER_AE_FOOTSTEP_LEFTM : LeftFootHitHandler,
            STRIDER_AE_FOOTSTEP_LEFTL : LeftFootHitHandler,
            STRIDER_AE_FOOTSTEP_RIGHT : RightFootHitHandler,
            STRIDER_AE_FOOTSTEP_RIGHTM : RightFootHitHandler,
            STRIDER_AE_FOOTSTEP_RIGHTL : RightFootHitHandler,
            STRIDER_AE_FOOTSTEP_BACK : BackFootHitHandler,
            STRIDER_AE_FOOTSTEP_BACKM : BackFootHitHandler,
            STRIDER_AE_FOOTSTEP_BACKL : BackFootHitHandler,
            
            STRIDER_AE_WHOOSH_LEFT : WhooshLeftHandler,
            STRIDER_AE_WHOOSH_BACK : WhooshBackHandler,
            STRIDER_AE_WHOOSH_RIGHT : WhooshRightHandler,
            
            STRIDER_AE_CREAK_LEFT : EmitSoundAnimEventHandler('NPC_Strider.Creak'),
            STRIDER_AE_CREAK_BACK : EmitSoundAnimEventHandler('NPC_Strider.Creak'),
            STRIDER_AE_CREAK_RIGHT : EmitSoundAnimEventHandler('NPC_Strider.Creak'),
        }
        
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionStunned(BaseClass.BehaviorGenericClass.ActionStunned):
                def OnStart(self):
                    outer = self.outer
                    stunnedstatus = outer.GetStatusEffect('stunned')
                    if not stunnedstatus or stunnedstatus.duration > 2.0:
                        outer.DoAnimation(outer.ANIM_BIG_FLINCH, data=255)
                    else:
                        outer.DoAnimation(outer.ANIM_SMALL_FLINCH, data=255)
                    outer.EmitSound("NPC_Strider.Pain")
                    return super().OnStart()
        
    # These bones have physics shadows
    # It allows a one-way interaction between the strider and
    # the physics world
    followerbonenames = [
        # Head
        "Combine_Strider.Body_Bone",
        "Combine_Strider.Neck_Bone",
        "Combine_Strider.Gun_Bone1",
        "Combine_Strider.Gun_Bone2",

        # lower legs
        "Combine_Strider.Leg_Left_Bone1",
        "Combine_Strider.Leg_Right_Bone1",
        "Combine_Strider.Leg_Hind_Bone1",
        
        # upper legs
        "Combine_Strider.Leg_Left_Bone",
        "Combine_Strider.Leg_Right_Bone",
        "Combine_Strider.Leg_Hind_Bone",
    ]

    # NOTE: These indices must directly correlate with the above list!
    STRIDER_BODY_FOLLOWER_INDEX = 0
    STRIDER_NECK_FOLLOWER_INDEX = 1
    STRIDER_GUN1_FOLLOWER_INDEX = 2
    STRIDER_GUN2_FOLLOWER_INDEX = 3
    
    STRIDER_LEFT_LEG_FOLLOWER_INDEX = 4
    STRIDER_RIGHT_LEG_FOLLOWER_INDEX = 5
    STRIDER_BACK_LEG_FOLLOWER_INDEX = 6

    STRIDER_LEFT_UPPERLEG_FOLLOWER_INDEX = 7
    STRIDER_RIGHT_UPPERLEG_FOLLOWER_INDEX = 8
    STRIDER_BACK_UPPERLEG_FOLLOWER_INDEX = 9

    aiclimb = False
    if isserver:
        NavigatorClass = UnitCombatAirNavigator
    
    # Animation state
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=90.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    class AnimStateClass(UnitCombatAnimStateEx):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.playfallactinair = False
            
        def OnNewModel(self):
            super().OnNewModel()
            
            outer = self.outer
            studiohdr = outer.GetModelPtr()
            
            self.bodyheight = outer.LookupPoseParameter(studiohdr, "body_height")
            self.yawcontrol = outer.LookupPoseParameter(studiohdr, "yaw")
            self.pitchcontrol = outer.LookupPoseParameter(studiohdr, "pitch")
            self.canonattachment = outer.LookupAttachment("BigGun")
            self.minigunattachment = outer.LookupAttachment("MiniGun")
            
            self.leftfoot = outer.LookupAttachment("left foot")
            self.rightfoot = outer.LookupAttachment("right foot")
            self.backfoot = outer.LookupAttachment("back foot")
            
            self.minigunbase = outer.LookupAttachment("minigunbase")
            self.minigunyaw = outer.LookupPoseParameter("minigunYaw")
            self.minigunpitch = outer.LookupPoseParameter("minigunPitch")
            
            outer.SetPoseParameter(self.bodyheight, outer.body_height)
            
        def Update(self, eye_yaw, eye_pitch):
            super().Update(eye_yaw, eye_pitch)
            
            outer = self.outer
            if outer.enemy:
                self.AimAtPoint(outer.enemy.GetAbsOrigin())
            else:
                self.pitchtarget = self.yawtarget = 0.0
            self.ApproachGunTargets()
            
            outer.SetPoseParameter(self.bodyheight, Approach(outer.body_height * (1/outer.unitinfo.scale),
                outer.GetPoseParameter(self.bodyheight), self.GetAnimTimeInterval()*100.0))
            
        MINIGUN_MAX_YAW = 90.0
        MINIGUN_MIN_YAW = -90.0
        MINIGUN_MAX_PITCH = 45.0
        MINIGUN_MIN_PITCH = -45.0
        def AimAtPoint(self, point, snap=False):
            gunMatrix = matrix3x4_t()
            outer = self.outer

            outer.GetAttachment(self.minigunbase, gunMatrix)

            forward = Vector()
            pos = Vector()
            MatrixGetColumn(gunMatrix, 0, forward)
            MatrixGetColumn(gunMatrix, 3, pos)

            # transform the point into gun space
            localPointPosition = Vector()
            VectorITransform(point, gunMatrix, localPointPosition)
            
            # do a look at in gun space (essentially a delta-lookat)
            localPointAngles = QAngle()
            VectorAngles(localPointPosition, localPointAngles)

            # convert to +/- 180 degrees
            pdiff = UTIL_AngleDiff(localPointAngles.x, 0)
            ydiff = UTIL_AngleDiff(localPointAngles.y, 0)

            self.pitchtarget += 0.5 * pdiff
            self.yawtarget -= 0.5 * ydiff
                
        def ApproachGunTargets(self):
            outer = self.outer
            
            self.pitchtarget = max(self.MINIGUN_MIN_PITCH, self.pitchtarget)
            self.pitchtarget = min(self.MINIGUN_MAX_PITCH, self.pitchtarget)
            self.yawtarget = max(self.MINIGUN_MIN_YAW, self.yawtarget)
            self.yawtarget = min(self.MINIGUN_MAX_YAW, self.yawtarget)
            
            outer.SetPoseParameter(self.minigunyaw, Approach(self.yawtarget,
                outer.GetPoseParameter(self.minigunyaw), self.GetAnimTimeInterval()*self.yawrate))
            outer.SetPoseParameter(self.minigunpitch, Approach(self.pitchtarget,
                outer.GetPoseParameter(self.minigunpitch), self.GetAnimTimeInterval()*self.pitchrate))
                
        pitchtarget = 0.0
        yawtarget = 0.0
        pitchrate = 180.0
        yawrate = 360.0
        
    def EventHandlerRangeAttack1(self, data):
        self.DispatchShootMinigun()
        
    originalbodyheight = None
    speedenabled = False
    def EnableSpeed(self):
        if self.speedenabled:
            return
        self.speedenabled = True

        self.energyregenrate -= self.speed_energy_drain
        self.originalbodyheight = self.body_height
        self.body_height = self.body_height * 0.5
        self.mv.maxspeed = self.mv.maxspeed * 2
        
    def DisableSpeed(self):
        #self.DoAnimation(self.ANIM_STAND)
        if not self.speedenabled:
            return
        self.speedenabled = False

        self.energyregenrate += self.speed_energy_drain
        if self.originalbodyheight:
            self.body_height = self.originalbodyheight
        self.mv.maxspeed = self.unitinfo.maxspeed


    class LocomotionClass(UnitBaseAirLocomotion):
        def CalcFootPosHeight(self, footposparam):
            outer = self.outer
            origin = outer.GetAbsOrigin()
            footpos = Vector()
            outer.GetAttachment(footposparam, footpos)
            footpos.z = origin.z
            
            tr = trace_t()
            
            # First trace from origin to foot, because the foot might be in a solid (since it has no real collision)
            UTIL_TraceLine(origin, footpos, MASK_NPCWORLDSTATIC, outer, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, tr)
            if tr.fraction != 1:
                return (origin.z - footpos.z)
            
            # If the strider foot is in the air, the above trace won't hit. Do a second trace from the foot to the ground
            UTIL_TraceLine(footpos, footpos + Vector(0, 0, -1) * MAX_TRACE_LENGTH, MASK_NPCWORLDSTATIC, outer,
                           WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, tr)
            #ndebugoverlay.Line(footpos, tr.endpos, 255, 255, 0, True, 0.1)
            
            return (origin.z - tr.endpos.z)
            
        def UpdateCurrentHeight(self):
            outer = self.outer
            origin = outer.GetAbsOrigin()
            body_height = outer.body_height
            animstate = outer.animstate
            
            trace = trace_t()
            UTIL_TraceEntity(outer, origin, origin - Vector(0,0,MAX_TRACE_LENGTH), MASK_NPCWORLDSTATIC, None,
                             outer.GetCollisionGroup(), trace)
            minheight = max(body_height, origin.z - trace.endpos.z)
            
            z1 = self.CalcFootPosHeight(animstate.leftfoot)
            z2 = self.CalcFootPosHeight(animstate.rightfoot)
            z3 = self.CalcFootPosHeight(animstate.backfoot)
            
            self.currentheight = min(minheight, max(z1, z2, z3))

            
    # Events
    events = dict(BaseClass.events)
    events.update({
        'ANIM_RANGE_ATTACK1': EventHandlerRangeAttack1,
        'ANIM_STOMPL': EventHandlerAnimation('ACT_STRIDER_STOMPL'),
        'ANIM_STOMPR': EventHandlerAnimation('ACT_STRIDER_STOMPR'),
        'ANIM_BIG_FLINCH': EventHandlerAnimationMisc(Activity.ACT_GESTURE_BIG_FLINCH, onlywhenstill=False),
        'ANIM_SMALL_FLINCH': EventHandlerAnimationMisc(Activity.ACT_GESTURE_SMALL_FLINCH, onlywhenstill=False),
        'ANIM_CROUCH': EventHandlerAnimation('ACT_CROUCH'),
        'ANIM_STAND': EventHandlerAnimation('ACT_STAND'),
    })
    
    # Activities
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        "ACT_STRIDER_LOOKL",
        "ACT_STRIDER_LOOKR",
        "ACT_STRIDER_DEPLOYRA1",
        "ACT_STRIDER_AIMRA1",
        "ACT_STRIDER_FINISHRA1",
        "ACT_STRIDER_DODGER",
        "ACT_STRIDER_DODGEL",
        "ACT_STRIDER_STOMPL",
        "ACT_STRIDER_STOMPR",
        "ACT_STRIDER_FLICKL",
        "ACT_STRIDER_FLICKR",
        "ACT_STRIDER_CARRIED",
        "ACT_STRIDER_DEPLOY",
        "ACT_STRIDER_GESTURE_DEATH",
        'ACT_STRIDER_SLEEP',
        'ACT_CROUCH',
        'ACT_STAND',
    ])
    
    # Ability sounds
    abilitysounds = {
        'attackmove': 'ability_comb_strider_attackmove',
        'holdposition': 'ability_comb_strider_holdposition',
    }

    # Spawn flags
    spawnflags = FlagsField(keyname='spawnflags', flags=
                            [('SF_CAN_STOMP_PLAYER', 0x10000, False),
                            ('SF_TAKE_MINIMAL_DAMAGE_FROM_NPCS', 0x20000, False)],
                            cppimplemented=True)
            
    # Vars
    smoke = None
    minigun_use_direct_fire = False
    stomp_target = None
    bone_follower_manager = None
    ragdoll = None
    aimyaw = 0
    aimpitch = 0
    
    # Settings
    scaleprojectedtexture = 3.5
    selectionparticlename = 'unit_circle_ground'
    jumpheight = 0.0
    canshootmove = True
    cancappcontrolpoint = False

    disable_bonefollowers = BooleanField(value=False, keyname='disablephysics')
    hit_pos = VectorField(value=Vector(0, 0, 0), networked=True, clientchangecallback='OnHitPosChanged')
    body_height = FloatField(value=450.0, networked=True)
    maxenergy = UpgradeField(abilityname='strider_maxenergy_upgrade', cppimplemented=True)
    
    speed_energy_drain = FloatField(value=4.0)
    
    STRIDER_STOMP_RANGE = 260
    
    # Messages for C_StriderFX
    STRIDER_MSG_BIG_SHOT = 1
    STRIDER_MSG_STREAKS = 2
    STRIDER_MSG_DEAD = 3

    STRIDERFX_BIG_SHOT_TIME = 1.25
    STRIDERFX_END_ALL_TIME = 4.0

class StriderUnlock(AbilityUpgrade):
    name = 'strider_unlock'
    displayname = '#CombStriderUnlock_Name'
    description = '#CombStriderUnlock_Description'
    image_name = "vgui/combine/abilities/strider_unlock"
    techrequirements = ['build_comb_synthfactory']
    buildtime = 90.0
    costs = [[('requisition', 150), ('power', 300)], [('kills', 5)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])
    
class StriderMaxEnergyUpgrade(AbilityUpgradeValue):
    name = 'strider_maxenergy_upgrade'
    displayname = '#StriderMaxEnUpgr_Name'
    description = '#StriderMaxEnUpgr_Description'
    #techrequirements = ['strider_unlock']
    buildtime = 56.0
    costs = [('requisition', 30), ('power', 30)]
    techrequirements = ['build_comb_synthfactory']
    upgradevalue = 150
    image_name = 'vgui/combine/abilities/combine_strider_energy_unlock'
    sai_hint = AbilityUpgradeValue.sai_hint | set(['sai_grenade_upgrade'])
    
class StriderInfo(UnitInfo):
    name = 'unit_strider'
    cls_name = 'unit_strider'
    displayname = '#CombStrider_Name'
    description = '#CombStrider_Description'
    image_name = 'vgui/combine/units/unit_strider'
    costs = [('requisition', 180), ('power', 180)]
    buildtime = 70.0
    viewdistance = 1024
    modelname = 'models/combine_strider.mdl'
    hulltype = 'HULL_LARGE_CENTERED'
    techrequirements = ['build_comb_tech_center']
    health = 1500
    maxspeed = 144.0
    turnspeed = 15.0
    unitenergy = 75
    unitenergy_initial = 25
    population = 6
    attributes = ['synth', 'large', 'pulse_cannon']
    sound_death = 'NPC_Strider.Death'
    scale = 0.75
    selectionpriority = 5
    sound_select = 'unit_strider_select'
    sound_move = 'unit_strider_move'
    sound_attack = 'unit_strider_attack'
    #tier =3
    ability_0 = 'impale'
    ability_1 = 'stridercannon'
    ability_2 = 'striderspeed'
    ability_8 = 'attackmove'
    ability_9 = 'holdposition'
    ability_10 = 'patrol'

    class AttackRange(UnitInfo.AttackRange):
        damage = 5
        minrange = 0.0
        maxrange = 896.0
        attackspeed = 0.19
        usesbursts = True
        minburst = 12
        maxburst = 12
        minresttime = 1.25
        maxresttime = 1.38
    attacks = 'AttackRange'
    sai_hint = set(['sai_unit_combat', 'sai_unit_super'])