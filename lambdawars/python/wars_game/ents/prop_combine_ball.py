from srcbase import *
from vmath import *
import random
import math
from decals import CHAR_TEX_FLESH
from physics import (PhysModelCreateSphere, PhysSetGameFlags, PhysClearGameFlags, physprops, 
                     FVPHYSICS_WAS_THROWN, FVPHYSICS_NO_NPC_IMPACT_DMG, FVPHYSICS_DMG_DISSOLVE, FVPHYSICS_HEAVY_OBJECT)
from entities import entity
from sound import EmitSound, SOUND_NORMAL_CLIP_DIST, ATTN_NORM, SNDLVL_NORM, CHAN_STATIC, CSoundEnvelopeController
from fields import FlagsField
from wars_game.attributes import EnergyBallAttribute
from particles import PATTACH_ABSORIGIN_FOLLOW

if isserver:
    from physics import PhysCallbackRemove, PhysCallbackSetVelocity, PhysIsInCallback
    from entities import (CBaseAnimating as BaseClass, CreateEntityByName, CSpriteTrail, FClassnameIs, 
                          CTakeDamageInfo, g_EventQueue, variant_t, EFL_NO_DISSOLVE, ENTITY_DISSOLVE_NORMAL, FBEAM_FADEOUT)
    from utils import UTIL_Remove, UTIL_PlayerByIndex, UTIL_ScreenShake, SHAKE_START, trace_t, UTIL_TraceLine, UTIL_ClearTrace, Ray_t, UTIL_EntitiesAlongRay, UTIL_EntitiesInSphere, UTIL_GetLocalPlayer
    from gameinterface import CSingleUserRecipientFilter, CPASAttenuationFilter, CBroadcastRecipientFilter, ConVar, FCVAR_REPLICATED
    from te import CEffectData, DispatchEffect, te
    from particles import PrecacheParticleSystem
    
    from achievements import ACHIEVEMENT_WARS_PINGPONG
    from playermgr import ListPlayersForOwnerNumber
    from wars_game.achievements import IsCommonGameMode
else:
    from entities import C_BaseAnimating as BaseClass
    from te import FX_AddQuad, FX_ElectricSpark, FXQUAD_BIAS_SCALE, FXQUAD_BIAS_ALPHA, ClientEffectRegistration

s_pWhizThinkContext = "WhizThinkContext"
s_pHoldDissolveContext = "HoldDissolveContext"
s_pExplodeTimerContext = "ExplodeTimerContext"
s_pAnimThinkContext = "AnimThinkContext"
s_pCaptureContext = "CaptureContext"
s_pRemoveContext = "RemoveContext"

if isserver:
    sk_combineball_guidefactor = ConVar( "sk_combineball_guidefactor","0.5", FCVAR_REPLICATED)
    sk_combine_ball_search_radius = ConVar( "sk_combine_ball_search_radius", "512", FCVAR_REPLICATED)
    sk_combineball_seek_angle = ConVar( "sk_combineball_seek_angle","15.0", FCVAR_REPLICATED)
    sk_combineball_seek_kill = ConVar( "sk_combineball_seek_kill","0", FCVAR_REPLICATED)

    # Create
    def CreateCombineBall(origin, velocity, radius, mass, lifetime, pOwner):
        ball = CreateEntityByName("prop_combine_ball") 
        ball.radius = radius

        ball.SetOwnerNumber(pOwner.GetOwnerNumber() if pOwner else 0)
        ball.SetAbsOrigin(origin)
        ball.SetOwnerEntity(pOwner)
        ball.originalowner = pOwner

        ball.SetAbsVelocity(velocity)
        ball.Spawn()

        ball.state = PropCombineBall.STATE_THROWN
        ball.speed = velocity.Length()

        ball.EmitSound( "NPC_CombineBall.Launch" )

        PhysSetGameFlags(ball.VPhysicsGetObject(), FVPHYSICS_WAS_THROWN)

        ball.StartWhizSoundThink()

        ball.SetMass( mass )
        ball.StartLifetime( lifetime )
        ball.weaponlaunched = True

        return ball
else:
    # Client effects
    def CombineBallImpactCallback(data):
        # Quick flash
        FX_AddQuad(data.origin,
                    data.normal,
                    data.radius * 10.0,
                    0,
                    0.75, 
                    1.0,
                    0.0,
                    0.4,
                    random.randint(0, 360), 
                    0,
                    Vector(1.0, 1.0, 1.0), 
                    0.25, 
                    "effects/combinemuzzle1_nocull",
                    (FXQUAD_BIAS_SCALE|FXQUAD_BIAS_ALPHA) )

        # Lingering burn
        FX_AddQuad(data.origin,
                    data.normal, 
                    data.radius * 2.0,
                    data.radius * 4.0,
                    0.75, 
                    1.0,
                    0.0,
                    0.4,
                    random.randint( 0, 360 ), 
                    0,
                    Vector( 1.0, 1.0, 1.0 ), 
                    0.5, 
                    "effects/combinemuzzle2_nocull",
                    (FXQUAD_BIAS_SCALE|FXQUAD_BIAS_ALPHA))

        # Throw sparks
        FX_ElectricSpark(data.origin, 2, 1, data.normal)
    cball_bounce = ClientEffectRegistration('cball_bounce', CombineBallImpactCallback)
    
    def CombineBallExplosionCallback(data):
        normal = Vector(0,0,1)

        # Throw sparks
        FX_ElectricSpark( data.origin, 4, 1, normal )

    cball_explode = ClientEffectRegistration('cball_explode', CombineBallExplosionCallback)

@entity('prop_combine_ball', networked=True)
class PropCombineBall(BaseClass):
    # Settings
    PROP_COMBINE_BALL_MODEL = "models/effects/combineball.mdl"
    PROP_COMBINE_BALL_SPRITE_TRAIL = "sprites/combineball_trail_black_1.vmt" 

    PROP_COMBINE_BALL_LIFETIME = 4.0 # Seconds

    PROP_COMBINE_BALL_HOLD_DISSOLVE_TIME = 8.0

    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_COMBINE_BALL_BOUNCING_IN_SPAWNER', 0x10000, False)], 
        cppimplemented=True)
    
    MAX_COMBINEBALL_RADIUS = 12

    particletrailname = 'particle_trail_ball'

    # Damage 
    DAMAGE_COMBINEBALL = 100

    # States
    STATE_NOT_THROWN = 0
    STATE_HOLDING = 1
    STATE_THROWN = 2
    STATE_LAUNCHED = 3 # by a combine_ball launcher
    state = STATE_NOT_THROWN
    
    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if type == DATA_UPDATE_CREATED:
                self.ParticleProp().Create(self.particletrailname, PATTACH_ABSORIGIN_FOLLOW)

    if isserver:
        # Vars
        glowtrail = None
        holdingsound = None
        radius = 0.0
        bouncecount = 0
        maxbounces = 0
        speed = 0
        weaponlaunched = False
        originalowner = None
        
        ballkillcount = 0
        
        __radius = 0
        @property
        def radius(self):
            return self.__radius
        @radius.setter
        def radius(self, radius):
            self.__radius = min(max(radius, 1), self.MAX_COMBINEBALL_RADIUS)
        
        def Precache(self):
        
            #NOTENOTE: We don't call into the base class because it chains multiple 
            #			precaches we don't need to incur

            self.PrecacheModel( self.PROP_COMBINE_BALL_MODEL )
            self.PrecacheModel( self.PROP_COMBINE_BALL_SPRITE_TRAIL )

            self.explosiontexture = self.PrecacheModel( "sprites/lgtning.vmt" )

            self.PrecacheScriptSound( "NPC_CombineBall.Launch" )
            self.PrecacheScriptSound( "NPC_CombineBall.KillImpact" )


            self.PrecacheScriptSound( "NPC_CombineBall_Episodic.Explosion" )
            self.PrecacheScriptSound( "NPC_CombineBall_Episodic.WhizFlyby" )
            self.PrecacheScriptSound( "NPC_CombineBall_Episodic.Impact" )
            

            self.PrecacheScriptSound( "NPC_CombineBall.HoldingInPhysCannon" )
            
            PrecacheParticleSystem(self.particletrailname)
            
        def IsInField(self):
            return self.state == self.STATE_NOT_THROWN
        
        def CreateVPhysics(self):
            """ Create vphysics """
            self.SetSolid( SOLID_BBOX )

            flSize = self.radius

            self.SetCollisionBounds( Vector(-flSize, -flSize, -flSize), Vector(flSize, flSize, flSize) )
            pPhysicsObject = PhysModelCreateSphere(self, flSize, self.GetAbsOrigin(), False)
            if not pPhysicsObject:
                return False
            self.VPhysicsSetObject( pPhysicsObject )
            self.SetMoveType( MOVETYPE_VPHYSICS )
            pPhysicsObject.Wake()

            nMaterialIndex = physprops.GetSurfaceIndex("metal_bouncy")
            pPhysicsObject.SetMaterialIndex( nMaterialIndex )
            
            pPhysicsObject.SetMass( 750.0 )
            pPhysicsObject.EnableGravity( False )
            pPhysicsObject.EnableDrag( False )

            flDamping = 0.0
            flAngDamping = 0.5
            pPhysicsObject.SetDamping( flDamping, flAngDamping )
            pPhysicsObject.SetInertia( Vector( 1e30, 1e30, 1e30 ) )

            if self.WasFiredByNPC():
                # Don't do impact damage. Just touch them and do your dissolve damage and move on.
                PhysSetGameFlags(pPhysicsObject, FVPHYSICS_NO_NPC_IMPACT_DMG)
            else:
                PhysSetGameFlags(pPhysicsObject, FVPHYSICS_DMG_DISSOLVE | FVPHYSICS_HEAVY_OBJECT)

            return True

        def Spawn(self):
            self.Precache()
            
            super().Spawn()

            self.SetModel(self.PROP_COMBINE_BALL_MODEL)

            #self.SetCollisionGroup(COLLISION_GROUP_NONE)
            self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
            self.SetThink(self.EnableFriendlyFireThink, gpGlobals.curtime + 0.35, 'EnableFriendlyFireThink')

            self.CreateVPhysics()

            vecAbsVelocity = self.GetAbsVelocity()
            self.VPhysicsGetObject().SetVelocity( vecAbsVelocity, None )

            self.state = self.STATE_NOT_THROWN
            self.lastbouncetime = -1.0
            self.firedgrabbedoutput = False
            self.forward = True
            self.captureinprogress = False

            # No shadow!
            self.AddEffects( EF_NOSHADOW )

            # Start up the eye trail
            self.glowtrail = CSpriteTrail.SpriteTrailCreate( self.PROP_COMBINE_BALL_SPRITE_TRAIL, self.GetAbsOrigin(), False )

            if self.glowtrail != None:
                self.glowtrail.FollowEntity( self )
                self.glowtrail.SetTransparency( kRenderTransAdd, 0, 0, 0, 255, kRenderFxNone )
                self.glowtrail.SetStartWidth( self.radius )
                self.glowtrail.SetEndWidth( 0 )
                self.glowtrail.SetLifeTime( 0.1 )
                self.glowtrail.TurnOff()

            self.emit = True
            self.held = False
            self.launched = False
            self.struckentity = False
            self.weaponlaunched = False

            self.nextdamagetime = gpGlobals.curtime
            
        def EnableFriendlyFireThink(self):
            self.SetCollisionGroup(COLLISION_GROUP_NONE)
            
        def WasFiredByNPC(self):
            return self.GetOwnerEntity() and self.GetOwnerEntity().IsUnit()
            
        def OutOfBounces(self):
            return self.state == self.STATE_LAUNCHED and self.maxbounces != 0 and self.bouncecount >= self.maxbounces
        
        def StartAnimating(self):
            # Start our animation cycle. Use the random to avoid everything thinking the same frame
            self.SetThink( self.AnimThink, gpGlobals.curtime + random.uniform( 0.0, 0.1), s_pAnimThinkContext )

            nSequence = self.LookupSequence( "idle" )

            self.SetCycle( 0 )
            self.animtime = gpGlobals.curtime
            self.ResetSequence( nSequence )
            self.ResetClientsideFrame()

        def StopAnimating(self):
            self.SetThink( None, gpGlobals.curtime, s_pAnimThinkContext )

        def StartLifetime(self, flDuration):
            """ Starts the lifetime countdown on the ball 
                flDuration - number of seconds to live before exploding """
            self.SetThink(self.ExplodeThink, gpGlobals.curtime + flDuration, s_pExplodeTimerContext )

        def ClearLifetime(self):
            """ Stops the lifetime on the ball from expiring """
            # Prevent it from exploding
            self.SetThink( None, gpGlobals.curtime, s_pExplodeTimerContext )

        def SetMass(self, mass):
            pObj = self.VPhysicsGetObject()

            if pObj != None:
                pObj.SetMass( mass )
                pObj.SetInertia(Vector(500, 500, 500))

        def UpdateOnRemove(self):
            """ Cleanup """
            if self.glowtrail != None:
                UTIL_Remove( self.glowtrail )
                self.glowtrail = None

            #Sigh... self is the only place where I can get a message after the ball is done dissolving.
            # if hl2_episodic.GetBool():
                # if self.IsDissolving():
                    # if self.GetSpawner():
                        # self.GetSpawner().BallGrabbed( self )
                        # self.NotifySpawnerOfRemoval()

            super().UpdateOnRemove()

        def ExplodeThink(self):
            self.DoExplosion()

        def DieThink(self):
            """ Fade out.  """
            # if self.GetSpawner():
                # # Let the spawner know we died so it does it's thing
                # if hl2_episodic.GetBool() and self.IsInField():
                    # self.GetSpawner().BallGrabbed( self )
                # self.GetSpawner().RespawnBall( 0.1 )

            UTIL_Remove( self )

        def FadeOut(self, flDuration):
            """ Fade out.  """
            self.AddSolidFlags( FSOLID_NOT_SOLID )

            # Start up the eye trail
            if self.glowtrail != None:
                self.glowtrail.SetBrightness( 0, flDuration )

            self.SetThink( self.DieThink )
            self.SetNextThink( gpGlobals.curtime + flDuration )

        def StartWhizSoundThink(self):
            self.SetThink( self.WhizSoundThink, gpGlobals.curtime + 2.0 * gpGlobals.interval_per_tick, s_pWhizThinkContext )

        def WhizSoundThink(self):
            """ Danger sounds.  """
            vecPosition = Vector()
            vecVelocity = Vector()
            pPhysicsObject = self.VPhysicsGetObject()
            
            if pPhysicsObject == None:
                #NOTENOTE: We should always have been created at self point
                #assert( 0 )
                self.SetThink( self.WhizSoundThink, gpGlobals.curtime + 2.0 * gpGlobals.interval_per_tick, s_pWhizThinkContext )
                return

            pPhysicsObject.GetPosition(vecPosition, None)
            pPhysicsObject.GetVelocity(vecVelocity, None)
            
            # Multiplayer equivelent, loops through players and decides if it should go or not, like SP.
            if gpGlobals.maxClients > 1:
                pPlayer = None

                for i in range(1, gpGlobals.maxClients+1):
                    pPlayer = UTIL_PlayerByIndex(i)
                    if pPlayer:
                        vecDelta = Vector()
                        VectorSubtract(pPlayer.GetAbsOrigin(), vecPosition, vecDelta)
                        VectorNormalize(vecDelta)
                        if DotProduct(vecDelta, vecVelocity) > 0.5:
                            vecEndPoint = Vector()
                            VectorMA(vecPosition, 2.0 * gpGlobals.interval_per_tick, vecVelocity, vecEndPoint)
                            flDist, t = CalcDistanceToLineSegment(pPlayer.GetAbsOrigin(), vecPosition, vecEndPoint)
                            if flDist < 200.0:
                                # We're basically doing what CPASAttenuationFilter does, on a per-user basis, if it passes we create the filter and send off the sound
                                # if it doesn't, we skip the player.
                                vecRelative = Vector()

                                VectorSubtract(pPlayer.EarPosition(), vecPosition, vecRelative)
                                distance = VectorLength(vecRelative)
                                maxAudible = (2 * SOUND_NORMAL_CLIP_DIST) / ATTN_NORM
                                if distance <= maxAudible:
                                    continue

                                # Set the recipient to the player it checked against so multiple sounds don't play.
                                filter = CSingleUserRecipientFilter(pPlayer)

                                ep = EmitSound()
                                ep.channel = CHAN_STATIC
                                ep.soudname = "NPC_CombineBall_Episodic.WhizFlyby"
                                
                                ep.volume = 1.0
                                ep.soundlevel = SNDLVL_NORM

                                self.EmitSoundFilter(filter, self.entindex(), ep)
            else:
                pPlayer = UTIL_GetLocalPlayer()

                if pPlayer:
                    vecDelta = Vector()
                    VectorSubtract( pPlayer.GetAbsOrigin(), vecPosition, vecDelta )
                    VectorNormalize( vecDelta )
                    if DotProduct( vecDelta, vecVelocity ) > 0.5:
                        vecEndPoint = Vector()
                        VectorMA( vecPosition, 2.0 * gpGlobals.interval_per_tick, vecVelocity, vecEndPoint )
                        flDist, t = CalcDistanceToLineSegment( pPlayer.GetAbsOrigin(), vecPosition, vecEndPoint )
                        if flDist < 200.0:
                            filter = CPASAttenuationFilter(origin=vecPosition, attenuation=ATTN_NORM)

                            ep = EmitSound()
                            ep.channel = CHAN_STATIC
                            ep.soundname = "NPC_CombineBall_Episodic.WhizFlyby"
                            
                            ep.volume = 1.0
                            ep.soundlevel = SNDLVL_NORM

                            self.EmitSoundFilter(filter, self.entindex(), ep)

                            self.SetThink(self.WhizSoundThink, gpGlobals.curtime + 0.5, s_pWhizThinkContext)
                            return

            self.SetThink( self.WhizSoundThink, gpGlobals.curtime + 2.0 * gpGlobals.interval_per_tick, s_pWhizThinkContext )
        
        def StopLoopingSounds(self):
            """ Stop looping sounds """
            if self.holdingsound:
                controller = CSoundEnvelopeController.GetController()
                controller.Shutdown( self.holdingsound )
                controller.SoundDestroy( self.holdingsound )
                self.holdingsound = None

        def DissolveRampSoundThink(self):
            dt = self.GetBallHoldDissolveTime() - self.GetBallHoldSoundRampTime()
            if self.holdingsound:
                controller = CSoundEnvelopeController.GetController()
                controller.SoundChangePitch( self.holdingsound, 150, dt )
            
            self.SetThink( self.DissolveThink, gpGlobals.curtime + dt, s_pHoldDissolveContext )

        def DissolveThink(self):
            """ Pow! """
            self.DoExplosion()

        def DoExplosion(self):
            """ Pow! """
            # don't do self twice
            if self.GetMoveType() == MOVETYPE_NONE:
                return

            if PhysIsInCallback():
                #g_PostSimulationQueue.QueueCall( self, self.DoExplosion )
                self.SetThink(self.DoExplosion, gpGlobals.curtime, 'DoExplosion' )
                return
            
            # Tell the respawner to make a new one
            #if self.GetSpawner():
            #    GetSpawner().RespawnBallPostExplosion()

            #Shockring
            filter2 = CBroadcastRecipientFilter()

            if self.OutOfBounces() == False:
                self.EmitSound( "NPC_CombineBall_Episodic.Explosion" )

                UTIL_ScreenShake( self.GetAbsOrigin(), 20.0, 150.0, 1.0, 1250.0, SHAKE_START )

                data = CEffectData()

                data.origin = self.GetAbsOrigin()

                DispatchEffect( "cball_explode", data )

                te.BeamRingPoint( filter2, 0, self.GetAbsOrigin(),	#origin
                    self.radius,	#start radius
                    1024,		#end radius
                    self.explosiontexture, #texture
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
                    32,		#a
                    0,		#speed
                    FBEAM_FADEOUT
                    )

                #Shockring
                te.BeamRingPoint( filter2, 0, self.GetAbsOrigin(),	#origin
                    self.radius,	#start radius
                    1024,		#end radius
                    self.explosiontexture, #texture
                    0,			#halo index
                    0,			#start frame
                    2,			#framerate
                    0.5,		#life
                    64,			#width
                    0,			#spread
                    0,			#amplitude
                    255,	#r
                    255,	#g
                    225,	#b
                    64,		#a
                    0,		#speed
                    FBEAM_FADEOUT
                    )
            
            else:
            
                #Shockring
                te.BeamRingPoint( filter2, 0, self.GetAbsOrigin(),	#origin
                    128,	#start radius
                    384,		#end radius
                    self.explosiontexture, #texture
                    0,			#halo index
                    0,			#start frame
                    2,			#framerate
                    0.25,		#life
                    48,			#width
                    0,			#spread
                    0,			#amplitude
                    255,	#r
                    255,	#g
                    225,	#b
                    64,		#a
                    0,		#speed
                    FBEAM_FADEOUT
                    )
            

            #if hl2_episodic.GetBool():
            #    CSoundEnt::InsertSound( SOUND_COMBAT | SOUND_CONTEXT_EXPLOSION, WorldSpaceCenter(), 180.0f, 0.25, self )

            # Turn us off and wait because we need our trails to finish up properly
            self.SetAbsVelocity( vec3_origin )
            self.SetMoveType( MOVETYPE_NONE )
            self.AddSolidFlags( FSOLID_NOT_SOLID )

            self.emit = False

            self.SetThink( self.SUB_Remove, gpGlobals.curtime + 0.5, s_pRemoveContext )
            self.StopLoopingSounds()
            
        def CollisionEventToTrace(self, index, pEvent, tr):
            UTIL_ClearTrace( tr )
            pEvent.GetSurfaceNormal( tr.plane.normal )
            pEvent.GetContactPoint( tr.endpos )
            tr.plane.dist = DotProduct( tr.plane.normal, tr.endpos )
            VectorMA( tr.endpos, -1.0, pEvent.preVelocity[index], tr.startpos )
            tr.ent = pEvent.GetEnt(int(not index))
            tr.fraction = 0.01 # spoof!
            
        def IncrementKillCount(self, victim):
            ''' Increments kill count for combine ball and test for achievement. '''
            if victim.GetOwnerNumber() == self.GetOwnerNumber():
                return
            self.ballkillcount += 1
            
            if self.GetOwnerEntity():
                self.GetOwnerEntity().kills += 1

            if IsCommonGameMode():
                # Ping Pong achievement: kill 5 with one ball.
                if self.ballkillcount == 5:
                    for player in ListPlayersForOwnerNumber(self.GetOwnerNumber()):
                        player.AwardAchievement(ACHIEVEMENT_WARS_PINGPONG)

        def DissolveEntity(self, entity):
            if entity.IsEFlagSet(EFL_NO_DISSOLVE):
                return False

            if not entity.IsUnit():
                return False

            entity.Dissolve("", gpGlobals.curtime, False, ENTITY_DISSOLVE_NORMAL)
            self.IncrementKillCount(entity) # Won't call Event_KilledOther after dissolve
            
            # Note that we've struck an entity
            self.struckentity = True

            return True
        
        def OnHitEntity(self, hitentity, flSpeed, index, pEvent):
            ownerent = hitentity.GetOwnerEntity()
            isstrider = FClassnameIs(hitentity, "unit_strider") or (ownerent and FClassnameIs(ownerent, "unit_strider"))
            isdog = FClassnameIs(hitentity, "unit_dog")
            istank = FClassnameIs(hitentity, "char_rebel_flamer") or FClassnameIs(hitentity, "char_metropolice_tank")
            # Detonate on the strider + the bone followers in the strider
            #if ( FClassnameIs(hitentity, "unit_strider") or 
            #    (ownerent and FClassnameIs(ownerent, "unit_strider")) ):
            #    self.DoExplosion()
            #    return

            info = CTakeDamageInfo(self, self.GetOwnerEntity(), self.GetAbsVelocity(), self.GetAbsOrigin(), self.DAMAGE_COMBINEBALL, DMG_DISSOLVE)
            info.attributes = {EnergyBallAttribute.name : EnergyBallAttribute(self.GetOwnerEntity())}
            info.forcefriendlyfire = True

            isdissolving = (hitentity.GetFlags() & FL_DISSOLVING) != 0
            shouldhit = hitentity.PassesDamageFilter(info)

            #One more check
            #Combine soldiers are not allowed to hurt their friends with combine balls (they can still shoot and hurt each other with grenades).
            pBCC = hitentity

            #if pBCC and pBCC.IsUnit():
            #    shouldhit = (shouldhit and 
            #                 pBCC.IRelationType(self.GetOwnerEntity()) != D_LI)
                             
            isbuilding = getattr(hitentity, 'isbuilding', False)

            if not isdissolving and shouldhit:
                # Explode on hitting strider/dog, dissolve on regular units and just bounce on buildings
                if isstrider or isdog or istank: #hitentity.VPhysicsGetObject() != None: #self.WasFiredByNPC() or self.maxbounces == -1:
                    # Since Combine balls fired by NPCs do a metered dose of damage per impact, we have to ignore touches
                    # for a little while after we hit someone, or the ball will immediately touch them again and do more
                    # damage. 
                    #if gpGlobals.curtime >= self.nextdamagetime:
                    self.EmitSound("NPC_CombineBall.KillImpact")

                    info.SetDamage(300)
                    #info.SetDamage(hitentity.maxhealth)
                    if isstrider:
                        if ownerent:
                            ownerent.TakeDamage(info)
                        else:
                            hitentity.TakeDamage(info)
                        self.DoExplosion()
                        return
                    hitentity.TakeDamage(info)
                    self.DoExplosion()
                    return
                    # Ignore touches briefly.
                    #self.nextdamagetime = gpGlobals.curtime + 0.1

                elif not isbuilding:
                    if self.state == self.STATE_THROWN and hitentity.IsUnit():
                        self.EmitSound( "NPC_CombineBall.KillImpact" )
                    
                    if self.state != self.STATE_HOLDING:
                        self.DissolveEntity(hitentity)
                        if hitentity.ClassMatches("unit_hunter") or hitentity.ClassMatches("char_rebel_rpg") or hitentity.ClassMatches("unit_crab_synth") or hitentity.ClassMatches("char_combine_elite") and not istank:
                            self.DoExplosion()
                            return

            vecFinalVelocity = Vector()
            if self.IsInField():
                # Don't deflect when in a spawner field
                vecFinalVelocity = pEvent.preVelocity[index]
            else:
                # Don't slow down when hitting other entities.
                vecFinalVelocity = pEvent.postVelocity[index]
                VectorNormalize( vecFinalVelocity )
                vecFinalVelocity *= self.speed
            
            PhysCallbackSetVelocity( pEvent.GetEnt(index).VPhysicsGetObject(), vecFinalVelocity )
            
        def Event_KilledOther(self, victim, info):
            super().Event_KilledOther(victim, info)
            
            if victim and victim.IsUnit():
                self.IncrementKillCount(victim)

        def DoImpactEffect(self, preVelocity, index, pEvent):
            # Do that crazy impact effect!
            tr = trace_t()
            self.CollisionEventToTrace( int(not index), pEvent, tr )
            
            pTraceEntity = pEvent.GetEnt(index)
            UTIL_TraceLine( tr.startpos - preVelocity * 2.0, tr.startpos + preVelocity * 2.0, MASK_SOLID, pTraceEntity, COLLISION_GROUP_NONE, tr )

            if tr.fraction < 1.0:
                # See if we hit the sky
                if tr.surface.flags & SURF_SKY:
                    self.DoExplosion()
                    return

                # Send the effect over
                data = CEffectData()

                data.radius = 16
                data.normal = tr.plane.normal
                data.origin = tr.endpos + tr.plane.normal * 1.0

                DispatchEffect( "cball_bounce", data )
            
            self.EmitSound( "NPC_CombineBall_Episodic.Impact" )
            
        def IsAttractiveTarget(self, pEntity):
            """ Tells whether this combine ball should consider deflecting towards this entity. """
            if not pEntity.IsAlive():
                return False

            if pEntity.GetFlags() & EF_NODRAW:
                return False

            # Don't guide toward striders
            if FClassnameIs( pEntity, "npc_strider" ):
                return False

            if self.WasFiredByNPC():
                # Fired by an NPC
                if not pEntity.IsUnit() and not pEntity.IsPlayer():
                    return False

                # Don't seek entities of the same class.
                if pEntity.GetClassname() == self.GetOwnerEntity().GetClassname():
                    return False
            else:
                if self.GetOwnerEntity():
                    pass
                    # Things we check if this ball has an owner that's not an NPC.
                    #if( GetOwnerEntity().IsPlayer() ) 
                    #    if( pEntity.Classify() == CLASS_PLAYER				||
                    #        pEntity.Classify() == CLASS_PLAYER_ALLY		||
                    #        pEntity.Classify() == CLASS_PLAYER_ALLY_VITAL )
                    #        # Not attracted to other players or allies.
                    #        return False

                # The default case.
                if not pEntity.IsUnit():
                    return False

                #if( pEntity.Classify() == CLASS_BULLSEYE )
                #    return False

                # We must be able to hit them
                tr = trace_t()
                UTIL_TraceLine( self.WorldSpaceCenter(), pEntity.BodyTarget( self.WorldSpaceCenter() ), MASK_SOLID, self, COLLISION_GROUP_NONE, tr )

                if tr.fraction < 1.0 and tr.ent != pEntity:
                    return False

            return True

        def DeflectTowardEnemy(self, flSpeed, index, pEvent):
            """ Deflects the ball toward enemies in case of a collision  """
            # Bounce toward a particular enemy choose one that's closest to my new velocity.
            vecVelDir = pEvent.postVelocity[index]
            VectorNormalize( vecVelDir )

            pBestTarget = None

            vecStartPoint = Vector()
            pEvent.GetContactPoint( vecStartPoint )

            flBestDist = MAX_COORD_FLOAT

            vecDelta = Vector()

            # If we've already hit something, get accurate
            bSeekKill = self.struckentity and (self.weaponlaunched or sk_combineball_seek_kill.GetInt() )

            if bSeekKill:
                targets = UTIL_EntitiesInSphere(1024, self.GetAbsOrigin(), sk_combine_ball_search_radius.GetFloat(), FL_NPC | FL_CLIENT)
                for target in targets:
                    if not self.IsAttractiveTarget(target):
                        continue

                    VectorSubtract(target.WorldSpaceCenter(), vecStartPoint, vecDelta)
                    distance = VectorNormalize(vecDelta)

                    if distance < flBestDist:
                        # Check our direction
                        if DotProduct( vecDelta, vecVelDir ) > 0.0:
                            pBestTarget = target
                            flBestDist = distance
            else:
                flMaxDot = 0.966
                if not self.weaponlaunched:
                    flMaxDot = sk_combineball_seek_angle.GetFloat()
                    flGuideFactor = sk_combineball_guidefactor.GetFloat()
                    for i in range(self.bouncecount, -1, -1):
                        flMaxDot *= flGuideFactor
                    
                    flMaxDot = math.cos( flMaxDot * math.pi / 180.0 )

                    if flMaxDot > 1.0:
                        flMaxDot = 1.0

                # Otherwise only help out a little
                extents = Vector(256, 256, 256)
                ray = Ray_t()
                ray.Init( vecStartPoint, vecStartPoint + vecVelDir *  2048.0, -extents, extents )
                targets = UTIL_EntitiesAlongRay(1024, ray, FL_NPC | FL_CLIENT)
                for target in targets:
                    if not self.IsAttractiveTarget(target):
                        continue

                    VectorSubtract( target.WorldSpaceCenter(), vecStartPoint, vecDelta )
                    distance = VectorNormalize( vecDelta )
                    flDot = DotProduct( vecDelta, vecVelDir )
                    
                    if flDot > flMaxDot:
                        if distance < flBestDist:
                            pBestTarget = target
                            flBestDist = distance

            if pBestTarget:
                vecDelta = Vector()
                VectorSubtract( pBestTarget.WorldSpaceCenter(), vecStartPoint, vecDelta )
                VectorNormalize( vecDelta )
                vecDelta *= self.speed
                PhysCallbackSetVelocity( pEvent.GetEnt(index).VPhysicsGetObject(), vecDelta ) 
                
        def IsHittableEntity(self, hitentity):
            if hitentity.IsWorld():
                return False

            if hitentity.GetMoveType() == MOVETYPE_PUSH:
                if hitentity.GetOwnerEntity() and FClassnameIs(hitentity.GetOwnerEntity(), "unit_strider"):
                    # The Strider's Bone Followers are MOVETYPE_PUSH, and we want the combine ball to hit these.
                    return True

                # If the entity we hit can take damage, we're good
                if hitentity.takedamage == DAMAGE_YES:
                    return True
                return False
            return True

        def VPhysicsCollision(self, index, pEvent):
            preVelocity = pEvent.preVelocity[index]
            flSpeed = VectorNormalize( preVelocity )

            if self.maxbounces == -1:
                pHit = physprops.GetSurfaceData( pEvent.surfaceProps[int(not index)] )

                if pHit.game.material != CHAR_TEX_FLESH:
                
                    hitentity = pEvent.GetEnt(int(not index))
                    if hitentity and self.IsHittableEntity( hitentity ):
                        self.OnHitEntity( hitentity, flSpeed, index, pEvent )

                    # Remove self without affecting the object that was hit. (Unless it was flesh)
                    #NotifySpawnerOfRemoval()
                    PhysCallbackRemove( self )

                    # disable dissolve damage so we don't kill off the player when he's the one we hit
                    PhysClearGameFlags( self.VPhysicsGetObject(), FVPHYSICS_DMG_DISSOLVE )
                    return

            # Prevents impact sounds, effects, etc. when it's in the field
            if not self.IsInField():
                super().VPhysicsCollision( index, pEvent )

            if self.state == self.STATE_HOLDING:
                return

            # If we've collided going faster than our desired, then up our desired
            if flSpeed > self.speed:
                self.speed = flSpeed

            # Make sure we don't slow down
            vecFinalVelocity = pEvent.postVelocity[index]
            VectorNormalize( vecFinalVelocity )
            vecFinalVelocity *= self.speed
            PhysCallbackSetVelocity( pEvent.GetEnt(index).VPhysicsGetObject(), vecFinalVelocity ) 

            hitentity = pEvent.GetEnt(int(not index))
            if hitentity and self.IsHittableEntity( hitentity ):
                self.OnHitEntity( hitentity, flSpeed, index, pEvent )
                return

            if self.IsInField():
                #if self.HasSpawnFlags( SF_COMBINE_BALL_BOUNCING_IN_SPAWNER ) and self.GetSpawner():
                #    self.BounceInSpawner( self.speed, index, pEvent )
                #    return

                PhysCallbackSetVelocity( pEvent.GetEnt(index).VPhysicsGetObject(), vec3_origin ) 

                # Delay the fade out so that we don't change our 
                # collision rules inside a vphysics callback.
                emptyVariant = variant_t()
                g_EventQueue.AddEvent( self, "FadeAndRespawn", 0.01, None, None )
                return

            #if self.IsBeingCaptured():
            #    return

            # Do that crazy impact effect!
            self.DoImpactEffect( preVelocity, index, pEvent )

            # Only do the bounce so often
            if gpGlobals.curtime - self.lastbouncetime < 0.25:
                return

            # Save off our last bounce time
            self.lastbouncetime = gpGlobals.curtime

            # Reset the sound timer
            self.SetThink( self.WhizSoundThink, gpGlobals.curtime + 0.01, s_pWhizThinkContext )

            # Deflect towards nearby enemies
            self.DeflectTowardEnemy( flSpeed, index, pEvent )

            # Once more bounce
            self.bouncecount += 1

            if self.OutOfBounces() and self.bouncedie == False:
                self.StartLifetime( 0.5 )
                #Hack: Stop this from being called by doing this.
                self.bouncedie = True

        def AnimThink(self):
            self.StudioFrameAdvance()
            self.SetThink( self.AnimThink, gpGlobals.curtime + 0.1, s_pAnimThinkContext )
        