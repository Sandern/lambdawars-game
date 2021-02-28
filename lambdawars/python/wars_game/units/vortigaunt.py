from srcbase import (MOVETYPE_FLY, SOLID_BBOX, FSOLID_TRIGGER, FSOLID_NOT_SOLID, COLLISION_GROUP_NONE, MASK_SHOT, MASK_SOLID, BLOOD_COLOR_GREEN,
                     MOVETYPE_NONE, kRenderTransAddFrameBlend, kRenderFxNone, DMG_SHOCK, FL_NPC, MASK_SOLID_BRUSHONLY)
from vmath import Vector, QAngle, VectorVectors, VectorNormalize, vec3_origin, AngleVectors, DotProduct, RemapValClamped
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass, EventHandlerAnimation
from unit_helper import UnitAnimConfig, LegAnimType_t
import random

from utils import UTIL_SetOrigin, UTIL_TraceLine, trace_t
from entities import entity, Activity, FBEAM_FADEOUT, FOWFLAG_HIDDEN, FOWFLAG_NOTRANSMIT
from gameinterface import ConVar, PrecacheMaterial
from sound import ATTN_NORM, CSoundParameters, EmitSound, CHAN_BODY
from animation import Animevent
from fields import BooleanField
from particles import PrecacheParticleSystem, PATTACH_POINT_FOLLOW, PATTACH_ABSORIGIN_FOLLOW

from wars_game.abilities.vortattack import VortAttack
from wars_game.statuseffects import StunnedEffectInfo

if isserver:
    from te import te, CEffectData, DispatchEffect
    from entities import (CreateEntityByName, CSprite, CTakeDamageInfo, 
                         ClearMultiDamage, ApplyMultiDamage, D_HT, CBaseEntity as BaseDispelEffect, EFL_FORCE_CHECK_TRANSMIT)
           
    from gameinterface import CPVSFilter, CPASAttenuationFilter, CBroadcastRecipientFilter
    from utils import UTIL_SetSize, UTIL_EntitiesInBox, UTIL_ScreenShake, ShakeCommand_t, CTraceFilterSkipFriendly, UTIL_Remove
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    import ndebugoverlay
else:
    from entities import ClientEntityList, C_BaseEntity as BaseDispelEffect, SHOULDTRANSMIT_START, SHOULDTRANSMIT_END
    from te import ClientEffectRegistration, FX_AddQuad, FXQUAD_BIAS_SCALE, FXQUAD_BIAS_ALPHA, FXQUAD_COLOR_FADE
    
COS_30 = 0.866025404 # sqrt(3) / 2
COS_60 = 0.5 # sqrt(1) / 2

if isserver:
    g_debug_vortigaunt_aim = ConVar( "g_debug_vortigaunt_aim", "0" )
    
# Client side effect
if isclient:
    def DispelCallback(data):
        # Kaboom!
        startPos = data.origin + Vector(0, 0, 16)
        endPos = data.origin + Vector(0, 0, -128)

        tr = trace_t()
        UTIL_TraceLine( startPos, endPos, MASK_SOLID_BRUSHONLY, None, COLLISION_GROUP_NONE, tr )

        if tr.fraction < 1.0:
            #Add a ripple quad to the surface
            FX_AddQuad(tr.endpos + (tr.plane.normal * 8.0),
                Vector(0, 0, 1),
                64.0, 
                2500.0, 
                0.8,
                1.0,	# start alpha
                0.0,	# end alpha
                0.3,
                random.uniform(0, 360),
                0.0,
                Vector(0.5, 1.0, 0.5),
                0.75, 
                "effects/ar2_altfire1b", 
                (FXQUAD_BIAS_SCALE|FXQUAD_BIAS_ALPHA|FXQUAD_COLOR_FADE))
            
            #Add a ripple quad to the surface
            FX_AddQuad(tr.endpos + (tr.plane.normal * 8.0),
                Vector(0, 0, 1),
                16.0, 
                1200.0,
                0.9,
                1.0, # start alpha
                0.0, # end alpha
                0.9,
                random.uniform(0, 360),
                0.0,
                Vector(0.5, 1.0, 0.5),
                1.25, 
                "effects/rollerglow", 
                (FXQUAD_BIAS_SCALE|FXQUAD_BIAS_ALPHA))
    vortdispel = ClientEffectRegistration('vortdispel', DispelCallback)
    
@entity('unit_vortigaunt', networked=True)
class UnitVortigaunt(BaseClass):   
    VORTFX_ZAPBEAM = 0 # Beam that damages the target
    VORTFX_ARMBEAM = 1 # Smaller beams from the hands as we charge up

    VORTIGAUNT_LEFT_CLAW = "leftclaw"
    VORTIGAUNT_RIGHT_CLAW = "rightclaw"

    HAND_LEFT = 0
    HAND_RIGHT = 1
    HAND_BOTH = 2
    
    VORTIGAUNT_LIMP_HEALTH = 20
    VORTIGAUNT_SENTENCE_VOLUME = 0.35 # volume of vortigaunt sentences
    VORTIGAUNT_VOL = 0.35 # volume of vortigaunt sounds
    VORTIGAUNT_ATTN = ATTN_NORM # attenutation of vortigaunt sentences
    VORTIGAUNT_HEAL_RECHARGE = 30.0 # How long to rest between heals
    VORTIGAUNT_ZAP_GLOWGROW_TIME = 0.5 # How long does glow last
    VORTIGAUNT_HEAL_GLOWGROW_TIME = 1.4 # How long does glow last
    VORTIGAUNT_GLOWFADE_TIME = 0.5 # How long does it fade
    VORTIGAUNT_CURE_LIFESPAN = 8.0 # cure tokens only live this long (so they don't get stuck on geometry)
    
    VORTIGAUNT_BEAM_ALL = 1
    VORTIGAUNT_BEAM_ZAP = 0
    VORTIGAUNT_BEAM_HEAL = 1
    VORTIGAUNT_BEAM_DISPEL = 2
    
    DISPELRANGE_SENSE = 600.0
    DISPELRANGE = 512.0
    
    energyregenrate = 3.0 # Dynamicly set in UnitThink
    canshootmove = False # Don't shoot while moving, it's annoying
    detector = True
    glowchangetime = 0.0
    glowage = 0.0
    stoploopingsounds = False
    curglowindex = 0

    def Spawn(self):
        super().Spawn()
        
        self.SetBloodColor(BLOOD_COLOR_GREEN)

        if isserver:
            self.lefthandattachment = self.LookupAttachment(self.VORTIGAUNT_LEFT_CLAW)
            self.righthandattachment = self.LookupAttachment(self.VORTIGAUNT_RIGHT_CLAW)
            
    if isserver:
        def __init__(self):
            super().__init__()
            
            self.handeffect = [None, None] 

        def Precache(self):
            super().Precache()
            
            PrecacheMaterial( "effects/rollerglow" )
            
            self.lightingsprite = self.PrecacheModel("sprites/lgtning.vmt")
            self.PrecacheModel("sprites/vortring1.vmt")
            
            self.PrecacheScriptSound( "NPC_Vortigaunt.SuitOn" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.SuitCharge" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.ZapPowerup" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.ClawBeam" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.StartHealLoop" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.Swing" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.StartShootLoop" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.FootstepLeft" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.FootstepRight" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.DispelStart" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.DispelImpact" )
            self.PrecacheScriptSound( "NPC_Vortigaunt.Explode" )
            self.PrecacheScriptSound("unit_vortigaunt_attack_dyn")
            self.PrecacheScriptSound("unit_vortigaunt_hurt")

            PrecacheParticleSystem( "vortigaunt_beam" )
            PrecacheParticleSystem( "vortigaunt_beam_charge" )
            PrecacheParticleSystem( "vortigaunt_hand_glow" )

            PrecacheMaterial( "sprites/light_glow02_add" )
            
        if isserver:
            def UpdateOnRemove(self):
                super().UpdateOnRemove()
                
                self.ClearBeams()

            def Event_Killed(self, info):
                super().Event_Killed(info)

                self.ClearBeams()
                self.ClearHandGlow()
             
            def IsInCombat(self):
                """ Tests if this unit is considered as being in combat. """
                outofcombattime = 4.0
                
                # Should have taken damage any time soon
                if self.enemy or gpGlobals.curtime - self.lasttakedamage < outofcombattime:
                    return True
                
                # Antlions shouldn't be engaging enemy
                antlions = getattr(self, 'abibugbait_antlions', None)
                if antlions:
                    for antlion in antlions:
                        if antlion and (antlion.enemy or gpGlobals.curtime - antlion.lasttakedamage < outofcombattime):
                            return True
                            
                # Nearby "others" shouldn't be engaging enemies
                others = self.senses.GetOthers()
                for other in others:
                    if other and (other.enemy or gpGlobals.curtime - other.lasttakedamage < outofcombattime):
                        return True
                        
                return False
            
            wasincombat = None
            def UnitThink(self):
                super().UnitThink()
                
                isincombat = self.IsInCombat()
                if isincombat != self.wasincombat:
                    self.wasincombat = isincombat
                    if isincombat:
                        #print('Vortigaunt changed to combat state')
                        self.energyregenrate = 1.0
                    else:
                        #print('Vortigaunt is no longer in combat')
                        self.energyregenrate = 3.0
        
        def ArmBeam(self, beamType, nHand):
            """ Small beam from arm to nearby geometry """
            # This code has been disabled as it seems to quickly overload the particle system and cause crashes
            """tr = trace_t()
            flDist = 1.0
            side = -1 if (nHand == self.HAND_LEFT) else 1

            forward = Vector()
            right = Vector()
            up = Vector()
            AngleVectors( self.GetLocalAngles(), forward, right, up )
            vecSrc = self.GetLocalOrigin() + up * 36 + right * side * 16 + forward * 32

            for i in range(0, 3):
                vecAim = forward * random.uniform( -1, 1 ) + right * side * random.uniform( 0, 1 ) + up * random.uniform( -1, 1 )
                tr1 = trace_t()
                UTIL_TraceLine ( vecSrc, vecSrc + vecAim * (10*12), MASK_SOLID, self, COLLISION_GROUP_NONE, tr1)
                
                # Don't hit the sky
                SURF_SKY = 0x0004
                if tr1.surface.flags & SURF_SKY:
                    continue

                # Choose a farther distance if we have one
                if flDist > tr1.fraction:
                    tr = tr1
                    flDist = tr.fraction

            # Couldn't find anything close enough
            if flDist == 1.0:
                return

            # Tell the client to start an arm beam
            uchAttachment = self.lefthandattachment if (nHand==self.HAND_LEFT) else self.righthandattachment
            self.SendMessage( [
                self.VORTFX_ARMBEAM,
                uchAttachment,
                tr.endpos,
                tr.plane.normal,
            ] )"""
            if self.VORTFX_ARMBEAM:
                self.EmitSound("unit_vortigaunt_attack_dyn")

        def StartHandGlow(self, beamType, nHand):
            """ Put glowing sprites on hands """
            # We need this because there's a rare case where a scene can interrupt and turn off our hand glows, but are then
            # turned back on in the same frame due to how animations are applied and anim events are executed after the AI frame.
            if self.glowchangetime > gpGlobals.curtime:
                return

            if (beamType is self.VORTIGAUNT_BEAM_DISPEL or 
                beamType is self.VORTIGAUNT_BEAM_HEAL or 
                beamType is self.VORTIGAUNT_BEAM_ZAP):
                    # Validate the hand's range
                    if nHand >= len( self.handeffect ):
                        return

                    # Start up
                    if self.handeffect[nHand] is None:
                        # Create the token if it doesn't already exist
                        self.handeffect[nHand] = VortigauntEffectDispel.CreateEffectDispel( self.GetAbsOrigin(), self, None )
                        if self.handeffect[nHand] is None:
                            return

                    # Stomp our settings
                    self.handeffect[nHand].SetParent( self, self.lefthandattachment if (nHand==self.HAND_LEFT) else self.righthandattachment )
                    self.handeffect[nHand].SetMoveType( MOVETYPE_NONE )
                    self.handeffect[nHand].SetLocalOrigin( Vector( 8.0, 4.0, 0.0 ) )
            elif beamType is self.VORTIGAUNT_BEAM_ALL:
                assert( 0 )

        def EndHandGlow(self, beamType=VORTIGAUNT_BEAM_ALL):
            """ Fade glow from hands. """
            if self.handeffect[0]:
                self.handeffect[0].FadeAndDie()
                self.handeffect[0] = None

            if self.handeffect[1]:
                self.handeffect[1].FadeAndDie()
                self.handeffect[1] = None

            # Zap
            if beamType == self.VORTIGAUNT_BEAM_ZAP or beamType == self.VORTIGAUNT_BEAM_ALL:
                self.glowage = 0

                # Stop our smaller beams as well
                self.ClearBeams()

        def CreateBeamBlast(self, vecOrigin):
            """ Creates a blast where the beam has struck a target 
                vecOrigin - position to eminate from. """
            pBlastSprite = CSprite.SpriteCreate( "sprites/vortring1.vmt", vecOrigin, True )
            if pBlastSprite != None:
                pBlastSprite.AddFOWFlags(FOWFLAG_HIDDEN|FOWFLAG_NOTRANSMIT)
                pBlastSprite.SetOwnerNumber(self.GetOwnerNumber())
                pBlastSprite.SetTransparency( kRenderTransAddFrameBlend, 255, 255, 255, 255, kRenderFxNone )
                pBlastSprite.SetBrightness( 255 )
                pBlastSprite.SetScale( random.uniform( 1.0, 1.5 ) )
                pBlastSprite.AnimateAndDie( 45.0 )
                pBlastSprite.EmitSound( "NPC_Vortigaunt.Explode" )

            filter = CPVSFilter( vecOrigin )
            te.GaussExplosion( filter, 0.0, vecOrigin, Vector( 0, 0, 1 ), 0 )

        def ZapBeam(self, nHand):
            """ Heavy damage directly forward.
                nHand - Handedness of the beam. """
            forward = Vector()
            self.GetVectors( forward, None, None )

            vecSrc = self.GetAbsOrigin() + self.GetViewOffset()
            vecAim = self.GetShootEnemyDir( vecSrc, False )	# We want a clear shot to their core
            
            attackinfo = VortAttack

            if g_debug_vortigaunt_aim.GetBool():
                if self.enemy:
                    vecTarget = self.enemy.BodyTarget( vecSrc, False )
                     
                    ndebugoverlay.Cross3D( vecTarget, 4.0, 255, 0, 0, True, 10.0 )
                    #CBaseAnimating *pAnim = GetEnemy().GetBaseAnimating()
                    #if pAnim:
                    #    pAnim.DrawServerHitboxes( 10.0 )

            # If we're too far off our center, the shot must miss!
            #if DotProduct( vecAim, forward ) < COS_60:
                # Missed, so just shoot forward
            #    vecAim = forward
            
            filter = CTraceFilterSkipFriendly(self, COLLISION_GROUP_NONE, self)
            tr = trace_t()
            # UTIL_TraceLine(vecSrc, vecSrc + ( vecAim * attackinfo.maxrange ), MASK_SHOT, filter, tr)
            UTIL_TraceLine(vecSrc, vecSrc + (vecAim * attackinfo.maxrange * 1.1), MASK_SHOT, filter, tr)

            if g_debug_vortigaunt_aim.GetBool():
                ndebugoverlay.Line( tr.startpos, tr.endpos, 255, 0, 0, True, 10.0 )
            

            # Send a message to the client to create a "zap" beam
            uchAttachment = self.lefthandattachment if (nHand==self.HAND_LEFT) else self.righthandattachment
            self.SendMessage( [
                self.VORTFX_ZAPBEAM,
                uchAttachment,
                tr.endpos,
            ] )

            entity = tr.ent
            if entity and self.takedamage:
                if g_debug_vortigaunt_aim.GetBool():
                    ndebugoverlay.Box( tr.endpos, -Vector(2,2,2), Vector(2,2,2), 255, 0, 0, 8, 10.0 )

                
                dmgInfo = CTakeDamageInfo(self, self, attackinfo.damage, attackinfo.damagetype)
                dmgInfo.SetDamagePosition(tr.endpos)
                VectorNormalize( vecAim )# not a unit vec yet
                # hit like a 5kg object flying 100 ft/s
                dmgInfo.SetDamageForce( vecAim * 5.0 * 100.0 * 12.0 )
                
                # Our zaps do special things to antlions
                if entity.GetClassname() == "unit_antlion":
                    # Make a worker flip instead of explode
                    if entity.IsWorker():
                        entity.Flip()
                    else:
                        # Always gib the antlion hit!
                        dmgInfo.ScaleDamage( 4.0 )
                    
                    # Look in a ring and flip other antlions nearby
                    self.DispelAntlions(tr.endpos, 200.0, False)

                # Send the damage to the recipient
                entity.DispatchTraceAttack( dmgInfo, vecAim, tr )
                
                self.ApplyKnockBack(entity, vecAim, stunchance=1.0, speed=250)

            # Create a cover for the end of the beam
            self.CreateBeamBlast( tr.endpos )

        def ClearHandGlow(self):
            """ Clear glow from hands immediately """
            if self.handeffect[0] is not None:
                UTIL_Remove(self.handeffect[0])
                self.handeffect[0] = None

            if self.handeffect[1] is not None:
                UTIL_Remove(self.handeffect[1])
                self.handeffect[1] = None
            
            self.glowage = 0

        def ClearBeams(self):
            """ remove all beams """
            # Stop looping suit charge sound.
            if self.stoploopingsounds:
                self.StopSound( "NPC_Vortigaunt.StartHealLoop" )
                self.StopSound( "NPC_Vortigaunt.StartShootLoop" )
                self.StopSound( "NPC_Vortigaunt.SuitCharge" )
                self.StopSound( "NPC_Vortigaunt.ZapPowerup" )
                self.stoploopingsounds = False

        def DispelAntlions(self, vecOrigin, flRadius, bDispel=True):
            # More effects
            if bDispel:
                UTIL_ScreenShake(vecOrigin, 20.0, 150.0, 1.0, 1250.0, ShakeCommand_t.SHAKE_START)

                filter2 = CBroadcastRecipientFilter()
                te.BeamRingPoint( filter2, 0, vecOrigin,	#origin
                    64,			#start radius
                    800,		#end radius
                    self.lightingsprite, #texture
                    0,			#halo index
                    0,			#start frame
                    2,			#framerate
                    0.1,		#life
                    128,			#width
                    0,			#spread
                    0,			#amplitude
                    255,	#r
                    255,	#g
                    225,	#b
                    32,		#a
                    0,		#speed
                    FBEAM_FADEOUT
                    )

                #Shockring
                te.BeamRingPoint( filter2, 0, vecOrigin + Vector( 0, 0, 16 ),	#origin
                    64,			#start radius
                    800,		#end radius
                    self.lightingsprite, #texture
                    0,			#halo index
                    0,			#start frame
                    2,			#framerate
                    0.2,		#life
                    64,			#width
                    0,			#spread
                    0,			#amplitude
                    255,	#r
                    255,	#g
                    225,	#b
                    200,		#a
                    0,		#speed
                    FBEAM_FADEOUT
                    )

                # Ground effects
                data = CEffectData()
                data.origin = vecOrigin

                DispatchEffect("VortDispel", data)

            # Make antlions flip all around us!
            enemies = UTIL_EntitiesInBox(32, vecOrigin-Vector(flRadius,flRadius,flRadius), vecOrigin+Vector(flRadius,flRadius,flRadius), FL_NPC)
            for enemy in enemies:
                isenemy = self.IRelationType(enemy) == D_HT
            
                # Attempt to trace a line to hit the target
                filter = CTraceFilterSkipFriendly(self, COLLISION_GROUP_NONE, self)
                tr = trace_t()
                UTIL_TraceLine(vecOrigin, enemy.BodyTarget(vecOrigin), MASK_SOLID_BRUSHONLY, filter, tr)
                if tr.fraction < 1.0 and tr.ent != enemy:
                    continue
                vecDir = (enemy.GetAbsOrigin() - vecOrigin)
                vecDir[2] = 0.0
                flDist = VectorNormalize(vecDir)

                flFalloff = RemapValClamped(flDist, 0, flRadius*0.75, 1.0, 0.1)
                
                if isenemy:
                    self.ApplyKnockBack(enemy, vecDir, stunchance=1.0)

                vecDir *= (flRadius * 1.5 * flFalloff)
                vecDir[2] += (flRadius * 0.5 * flFalloff)

                # gib nearby antlions, knock over distant ones. 
                if flDist < 250 and bDispel and isenemy:
                    # splat!
                    vecDir[2] += 400.0 * flFalloff
                    dmgInfo = CTakeDamageInfo(self, self, vecDir, enemy.GetAbsOrigin(), 125, self.unitinfo.AttackRange.damagetype)
                    enemy.TakeDamage(dmgInfo)
                else:
                    # Turn them over
                    if hasattr(enemy, 'Flip'):
                        try:
                            enemy.Flip(True)
                        except AttributeError:
                            pass

                    # Display an effect between us and the flipped creature
                    # Tell the client to start an arm beam
                    '''uchAttachment = enemy.LookupAttachment("mouth")
                    self.SendMessage( [
                        self.VORTFX_ARMBEAM,
                        enemy.entindex(),
                        uchAttachment,
                        vecOrigin,
                        Vector(0, 0, 1),
                    ] )'''
            
            # Stop our effects
            if bDispel:
                self.EndHandGlow(self.VORTIGAUNT_BEAM_ALL)
                
        def ApplyKnockBack(self, target, dir, speed=400.0, stunchance=1.0, stunduration=1.05):
            """ Applies a knockback to the given target with a stun chance. """
            curvel = target.GetAbsVelocity().LengthSqr()
            if curvel < 2000.0 * 2000.0 and not (target.IsUnit() and target.isbuilding):
                target.ApplyAbsVelocityImpulse((dir * speed) + Vector(0, 0, 85))
                
            if target.IsUnit() and stunchance and random.random() < stunchance:
                StunnedEffectInfo.CreateAndApply(target, attacker=self, duration=stunduration)

        # Anim event handlers
        def ShootSoundStart(self, event):
            filter = CPASAttenuationFilter(self)

            params = CSoundParameters()
            if self.GetParametersForSound( "NPC_Vortigaunt.StartHealLoop", params, None ):
                ep = EmitSound( params )
                #ep.pitch = 100 + m_iBeams * 10
                ep.pitch = 150

                self.EmitSoundFilter( filter, self.entindex(), ep )
                self.stoploopingsounds = True

        def ZapPowerUp(self, event):
            if self.glowchangetime > gpGlobals.curtime:
                return

            nHand = 0
            if event.options:
                nHand = int( event.options )

            if ( nHand == self.HAND_LEFT ) or (nHand == self.HAND_BOTH ):
                self.ArmBeam( self.VORTIGAUNT_BEAM_ZAP, self.HAND_LEFT )
            
            if ( nHand == self.HAND_RIGHT ) or (nHand == self.HAND_BOTH ):
                self.ArmBeam( self.VORTIGAUNT_BEAM_ZAP, self.HAND_RIGHT )
            
            # Make hands glow if not already glowing
            if self.glowage == 0:
                if ( nHand == self.HAND_LEFT ) or (nHand == self.HAND_BOTH ):
                    self.StartHandGlow( self.VORTIGAUNT_BEAM_ZAP, self.HAND_LEFT )
                 
                if ( nHand == self.HAND_RIGHT ) or (nHand == self.HAND_BOTH ):
                    self.StartHandGlow( self.VORTIGAUNT_BEAM_ZAP, self.HAND_RIGHT )
                
                self.glowage = 1

            filter = CPASAttenuationFilter( self )
            
            params = CSoundParameters()
            if self.GetParametersForSound( "NPC_Vortigaunt.ZapPowerup", params, None ):
                ep = EmitSound( params )
                #ep.pitch = 100 + m_iBeams * 10
                ep.pitch = 150
        
                self.EmitSoundFilter( filter, self.entindex(), ep )

                self.stoploopingsounds = True
                
        def ZapShoot(self, event):
            self.ClearBeams()

            ClearMultiDamage()

            nHand = 0
            if event.options:
                nHand = int( event.options )

            if (nHand == self.HAND_LEFT) or (nHand == self.HAND_BOTH):
                self.ZapBeam( self.HAND_LEFT )
            
            if (nHand == self.HAND_RIGHT) or (nHand == self.HAND_BOTH):
                self.ZapBeam(self.HAND_RIGHT)

            self.EndHandGlow()

            self.EmitSound( "NPC_Vortigaunt.ClawBeam" )
            self.stoploopingsounds = True
            ApplyMultiDamage()

            # Suppress our aiming until we're done with the animation
            self.aimdelay = gpGlobals.curtime + 0.75

            # Stagger the next time we can attack
            self.nextattack = gpGlobals.curtime + random.uniform( 2.0, 3.0 )

        def ZapDone(self, event):
            self.ClearBeams()
            
        def StartDispel(self, event):
            self.StartHandGlow( self.VORTIGAUNT_BEAM_DISPEL, self.HAND_LEFT )
            self.StartHandGlow( self.VORTIGAUNT_BEAM_DISPEL, self.HAND_RIGHT )

            # Boom!
            #EmitSound( "NPC_Vortigaunt.DispelImpact" )
            params = CSoundParameters()
            if self.GetParametersForSound( "NPC_Vortigaunt.DispelImpact", params, None ):
                filter = CPASAttenuationFilter(self)
                ep = EmitSound( params )
                ep.channel = CHAN_BODY
                self.EmitSoundFilter(filter, self.entindex(), ep)

        def Dispel(self, event):
            self.DispelAntlions(self.GetAbsOrigin(), self.DISPELRANGE)
                
    else:
        def ReceiveMessage(self, msg):
            messageType = msg[0]
            if messageType is self.VORTFX_ZAPBEAM:
                # Find our attachment point
                attachment = msg[1]
                
                # Get our attachment position
                vecStart = Vector()
                vecAngles = QAngle()
                self.GetAttachment(attachment, vecStart, vecAngles)

                # Get the final position we'll strike
                vecEndPos = msg[2]

                # Place a beam between the two points
                effect = self.ParticleProp().Create( "vortigaunt_beam", PATTACH_POINT_FOLLOW, attachment )
                if effect:
                    effect.SetControlPoint(0, vecStart)
                    effect.SetControlPoint(1, vecEndPos)

            elif messageType is self.VORTFX_ARMBEAM:
                if len(msg) == 5:
                    entindex = msg[1]
                    ent = ClientEntityList().GetBaseEntityFromHandle(ClientEntityList().EntIndexToHandle(entindex))
                    attachment = msg[2]
                    vecEndPos = msg[3]
                    vecNormal = msg[4]
                else:
                    ent = self
                    attachment = msg[1]
                    vecEndPos = msg[2]
                    vecNormal = msg[3]
                    
                if ent:
                    effect = ent.ParticleProp().Create("vortigaunt_beam_charge", PATTACH_POINT_FOLLOW, attachment)
                    if effect:
                        # Set the control point's angles to be the surface normal we struct
                        vecRight = Vector()
                        vecUp = Vector()
                        VectorVectors(vecNormal, vecRight, vecUp)
                        effect.SetControlPointOrientation(1, vecNormal, vecRight, vecUp)
                        effect.SetControlPoint(1, vecEndPos)
            else:
                PrintWarning("Received unknown message %d" % messageType)

    def OnTakeDamage(self, dmginfo):
        if self.takedamage and self.health > 0:
            self.EmitSound('unit_vortigaunt_hurt')
        return super().OnTakeDamage(dmginfo)

    # Ability sounds
    abilitysounds = {
        'attackmove' : 'ability_reb_vortigaunt_attackmove',
        'holdposition' : 'ability_reb_vortigaunt_holdposition',
    }
                
    # Events
    events = dict(BaseClass.events)
    events.update({
        'ANIM_VORTIGAUNT_DISPEL' : EventHandlerAnimation('ACT_VORTIGAUNT_DISPEL'),
    })
    
    # Activity list
    activitylist = list( BaseClass.activitylist )
    activitylist.extend( [
        'ACT_VORTIGAUNT_AIM',
        'ACT_VORTIGAUNT_START_HEAL',
        'ACT_VORTIGAUNT_HEAL_LOOP',
        'ACT_VORTIGAUNT_END_HEAL',
        'ACT_VORTIGAUNT_TO_ACTION',
        'ACT_VORTIGAUNT_TO_IDLE',
        'ACT_VORTIGAUNT_HEAL',
        'ACT_VORTIGAUNT_DISPEL',
        'ACT_VORTIGAUNT_ANTLION_THROW',
    ] )
    
    # Activity translation table
    acttables = {
        Activity.ACT_MP_JUMP_LAND : Activity.ACT_LAND,
        Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_GLIDE,
        Activity.ACT_MP_JUMP_START : Activity.ACT_JUMP,
        Activity.ACT_MP_JUMP : Activity.ACT_JUMP,
    }
    
    if isserver:
        # Anim events
        aetable = {
            'AE_VORTIGAUNT_CLAW_LEFT' : BaseAnimEventHandler(),
            'AE_VORTIGAUNT_CLAW_RIGHT' : BaseAnimEventHandler(),
            'AE_VORTIGAUNT_ZAP_POWERUP' : ZapPowerUp,
            'AE_VORTIGAUNT_ZAP_SHOOT' : ZapShoot,
            'AE_VORTIGAUNT_ZAP_DONE' : ZapDone,
            'AE_VORTIGAUNT_HEAL_STARTGLOW' : None,
            'AE_VORTIGAUNT_HEAL_STARTBEAMS' : None,
            'AE_VORTIGAUNT_HEAL_STARTSOUND' : None,
            'AE_VORTIGAUNT_SWING_SOUND' : EmitSoundAnimEventHandler('NPC_Vortigaunt.Swing'),
            'AE_VORTIGAUNT_SHOOT_SOUNDSTART' : ShootSoundStart,
            'AE_VORTIGAUNT_HEAL_PAUSE' : None,
            'AE_VORTIGAUNT_START_DISPEL' : StartDispel,
            'AE_VORTIGAUNT_ACCEL_DISPEL' : BaseAnimEventHandler(),
            'AE_VORTIGAUNT_DISPEL' : Dispel,
            'AE_VORTIGAUNT_START_HURT_GLOW' : None,
            'AE_VORTIGAUNT_STOP_HURT_GLOW' : None,
            'AE_VORTIGAUNT_START_HEAL_GLOW' : None,
            'AE_VORTIGAUNT_STOP_HEAL_GLOW' : None,
            Animevent.AE_NPC_LEFTFOOT : EmitSoundAnimEventHandler('NPC_Vortigaunt.FootstepLeft'),
            Animevent.AE_NPC_RIGHTFOOT : EmitSoundAnimEventHandler('NPC_Vortigaunt.FootstepRight'),
        }
    
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=60.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def OnNewModel(self):
            super(UnitVortigaunt.AnimStateClass, self).OnNewModel()
            
            studiohdr = self.outer.GetModelPtr()
            
            self.bodyyaw = self.outer.LookupPoseParameter("body_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("aim_pitch")
            
            headpitch = self.outer.LookupPoseParameter(studiohdr, "head_pitch")
            if headpitch < 0:
                return
            headyaw = self.outer.LookupPoseParameter(studiohdr, "head_yaw")
            if headyaw < 0:
                return
            headroll = self.outer.LookupPoseParameter(studiohdr, "head_roll")
            if headroll < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, headpitch, 0.0)
            self.outer.SetPoseParameter(studiohdr, headyaw, 0.0)
            self.outer.SetPoseParameter(studiohdr, headroll, 0.0)
            
            spineyaw = self.outer.LookupPoseParameter(studiohdr, "spine_yaw")
            if spineyaw < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, spineyaw, 0.0)

#=============================================================================
# 
#  Dispel Effect
#
#=============================================================================
@entity('vort_effect_dispel', networked=True)
class VortigauntEffectDispel(BaseDispelEffect):
    @staticmethod
    def CreateEffectDispel(vecOrigin, pOwner, pTarget):
        pToken = CreateEntityByName( "vort_effect_dispel" )
        if not pToken:
            return None

        # Set up our internal data
        UTIL_SetOrigin( pToken, vecOrigin )
        pToken.SetOwnerEntity( pOwner )
        pToken.Spawn()

        return pToken
        
    fadeout = BooleanField(value=False, networked=True)

    if isserver:
        def Spawn(self):
            self.Precache()

            UTIL_SetSize( self, Vector( -4, -4, -4 ), Vector( 4, 4, 4 ) )

            self.SetSolid(SOLID_BBOX)
            self.SetSolidFlags(FSOLID_NOT_SOLID)

            # No model but we still need to force this!
            self.AddEFlags(EFL_FORCE_CHECK_TRANSMIT)

            super(VortigauntEffectDispel, self).Spawn()

        def FadeAndDie(self):
            self.fadeout = True
            self.SetThink( self.SUB_Remove )
            self.SetNextThink( gpGlobals.curtime + 2.0 )
    else:
        def UpdateOnRemove(self):
            if self.effect:
                self.effect.StopEmission()
                self.effect = None

            if self.dlight != None:
                self.dlight.die = gpGlobals.curtime

        def OnDataChanged(self, type):
            if self.fadeout:
                if self.effect:
                    self.effect.StopEmission()
                    self.effect = None

            super(VortigauntEffectDispel, self).OnDataChanged( type )

        def NotifyShouldTransmit(self, state):
            super(VortigauntEffectDispel, self).NotifyShouldTransmit( state )
            
            # Turn off
            if state == SHOULDTRANSMIT_END:
                if self.effect:
                    self.effect.StopEmission()
                    self.effect = None
 
            # Turn on
            if state == SHOULDTRANSMIT_START:
                self.effect = self.ParticleProp().Create("vortigaunt_hand_glow", PATTACH_ABSORIGIN_FOLLOW)
                self.effect.SetControlPointEntity(0, self)

        def SetupEmitters(self):
            """ Create our emitter """
            self.dlight = None

            self.dlight = effects.CL_AllocDlight(index)
            self.dlight.origin = self.GetAbsOrigin()
            self.dlight.color.r = 64
            self.dlight.color.g = 255
            self.dlight.color.b = 64
            self.dlight.radius = 0
            self.dlight.minlight = DLIGHT_MINLIGHT
            self.dlight.die = FLT_MAX

            return True
            
        def ClientThink(self):
            if self.dlight != None:
                self.dlight.origin = self.GetAbsOrigin()
                self.dlight.radius = DLIGHT_RADIUS
                
        effect = None
        dlight = None

# Register unit
class VortigauntInfo(UnitInfo):
    name = 'unit_vortigaunt'
    cls_name = 'unit_vortigaunt'
    displayname = '#Vortigaunt_Name'
    description = '#Vortigaunt_Description'
    image_name = 'vgui/rebels/units/unit_vortigaunt.vmt'
    costs = [('requisition', 40), ('scrap', 50)]
    buildtime = 40.0
    viewdistance = 896.0
    sensedistance = 896.0
    health = 280
    maxspeed = 216.0
    unitenergy = 160
    unitenergy_initial = 160
    population = 3
    attributes = ['creature', 'shock']
    sound_select = 'unit_vortigaunt_select'
    sound_move = 'unit_vortigaunt_move'
    sound_attack = 'unit_vortigaunt_attack'
    sound_death = 'unit_vortigaunt_death'
    modelname = 'models/vortigaunt.mdl'
    hulltype = 'HULL_WIDE_HUMAN'
    abilities = {
        0 : 'vortattack',
        1 : 'dispel',
        2 : 'inwardfocus',
        5 : 'bugbait',
        6 : 'bugbaitrecall',
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'patrol',
    }
    attacks = VortAttack
    sai_hint = set(['sai_unit_combat'])
    infest_zombietype = ''
    
class OverrunVortigauntInfo(VortigauntInfo):
    name = 'overrun_unit_vortigaunt'
    hidden = True
    buildtime = 0
    techrequirements = ['or_tier3_research']
    unitenergy_initial = VortigauntInfo.unitenergy
    costs = [('kills', 5)]
    abilities = {
        0 : 'vortattack',
        1 : 'dispel',
        2 : 'inwardfocus',
        8 : 'attackmove',
        9 : 'holdposition',
        10 : 'patrol',
    }
    
    