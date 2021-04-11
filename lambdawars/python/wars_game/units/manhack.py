from srcbase import *
from vmath import (Vector, vec3_origin, QAngle, AngularImpulse, SimpleSplineRemapVal, CrossProduct, VectorNormalize, 
                   VectorAdd, RandomVector, DotProduct, VectorSubtract, VectorAngles)
import random
from core.units import UnitInfo, UnitBaseCombat as BaseClass, UnitBaseAirLocomotion
from entities import entity, Activity
from fields import IntegerField, FloatField, FlagsField, SetField
from unit_helper import UnitAnimConfig, LegAnimType_t
from math import ceil

if isserver:
    from core.units import UnitCombatAirNavigator, BaseAction
    from physics import CalculateDefaultPhysicsDamage, PhysCallbackDamage, FVPHYSICS_PLAYER_HELD
    from entities import (CTakeDamageInfo, GetWorldEntity, CalculateMeleeDamageForce, SpawnBlood, 
                         CSprite, PropBreakablePrecacheAll, FClassnameIs, g_vecAttackDir, PropBreakableCreateAll, D_HT)
    from utils import UTIL_Remove, UTIL_ScaleForGravity, UTIL_TraceHull, trace_t, UTIL_DecalTrace, UTIL_TraceLine
    from gameinterface import CBroadcastRecipientFilter
    from te import CEffectData, DispatchEffect, te
else:
    from sound import CSoundEnvelopeController
    from gameinterface import CPASAttenuationFilter

MANHACK_GIB_COUNT = 5 
MANHACK_INGORE_WATER_DIST = 384

# Sound stuff
MANHACK_PITCH_DIST1 = 512
MANHACK_MIN_PITCH1 = (100)
MANHACK_MAX_PITCH1 = (160)
MANHACK_WATER_PITCH1 = (85)
MANHACK_VOLUME1 = 0.55

MANHACK_PITCH_DIST2 = 400
MANHACK_MIN_PITCH2 = (85)
MANHACK_MAX_PITCH2 = (190)
MANHACK_WATER_PITCH2 = (90)

MANHACK_NOISEMOD_HIDE = 5000

# ANIMATION EVENTS
MANHACK_AE_START_ENGINE = 50
MANHACK_AE_DONE_UNPACKING = 51
MANHACK_AE_OPEN_BLADE = 52

#MANHACK_GLOW_SPRITE = "sprites/laserdot.vmt"
MANHACK_GLOW_SPRITE = "sprites/glow1.vmt"

MANHACK_CHARGE_MIN_DIST = 200

@entity('unit_manhack', networked=True)
class UnitManhack(BaseClass):
    aiclimb = False
    LocomotionClass = UnitBaseAirLocomotion
    if isserver:
        NavigatorClass = UnitCombatAirNavigator
    
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 2048.0
        self.testroutestartheight = 2048.0

    if isserver:
        def Precache(self):
            #
            # Model.
            #
            self.PrecacheModel("models/manhack.mdl")
            self.PrecacheModel(MANHACK_GLOW_SPRITE)
            PropBreakablePrecacheAll("models/manhack.mdl")
            
            self.PrecacheScriptSound("NPC_Manhack.Die")
            self.PrecacheScriptSound("NPC_Manhack.Bat")
            self.PrecacheScriptSound("NPC_Manhack.Grind")
            self.PrecacheScriptSound("NPC_Manhack.Slice")
            self.PrecacheScriptSound("NPC_Manhack.EngineNoise")
            self.PrecacheScriptSound("NPC_Manhack.Unpack")
            self.PrecacheScriptSound("NPC_Manhack.ChargeAnnounce")
            self.PrecacheScriptSound("NPC_Manhack.ChargeEnd")
            self.PrecacheScriptSound("NPC_Manhack.Stunned")

            # Sounds used on Client:
            self.PrecacheScriptSound("NPC_Manhack.EngineSound1")
            self.PrecacheScriptSound("NPC_Manhack.EngineSound2")
            self.PrecacheScriptSound("NPC_Manhack.BladeSound")

            super().Precache()

    def Spawn(self):    
        super().Spawn()
        
        self.locomotion.desiredheight = 52.0
        self.locomotion.flynoiserate = 48.0
        self.locomotion.flynoisez = 24.0
        
        self.SetBloodColor(DONT_BLEED)
        
        if isserver:
            self.navigator.usesimplifiedroutebuilding = False
        
            self.nextenginesoundtime = gpGlobals.curtime
            self.watersuspendtime = gpGlobals.curtime
            
            self.SetBodygroup(self.MANHACK_BODYGROUP_BLADE, self.MANHACK_BODYGROUP_ON)
            self.SetBodygroup(self.MANHACK_BODYGROUP_BLUR, self.MANHACK_BODYGROUP_ON)
            
            self.StartEye()
            self.BladesInit()
    
    if isserver:
        def UpdateOnRemove(self):
            self.DestroySmokeTrail()
            self.KillSprites(0.0)
            super().UpdateOnRemove()

        def UnitThink(self):
            super().UnitThink()
            
            self.PlayFlySound()
            self.CheckCollisions(self.think_freq)
            
        def BladesInit(self):
            if not self.bladesactive:
                # manhack is packed up, so has no power of its own. 
                # don't start the engine sounds.
                # make us fall a little slower than we should, for visual's sake
                self.SetGravity(UTIL_ScaleForGravity(400))

                #SetActivity( ACT_IDLE )
            else:
                engineSound = False if (self.GetSpawnFlags() & self.SF_NPC_GAG) else True
                self.StartEngine(engineSound)
                #SetActivity( ACT_FLY )
                
        def StartEngine(self, fStartSound):
            """ Crank up the engine! """
            if fStartSound:
                self.SoundInit()

            # Make the blade appear.
            self.SetBodygroup(1, 1)

            # Pop up a little if falling fast!
            vecVelocity = Vector()
            self.GetVelocity(vecVelocity, None)
            if (self.GetSpawnFlags() & self.SF_MANHACK_PACKED_UP) and vecVelocity.z < 0:
                # DevMsg(" POP UP \n" )
                # ApplyAbsVelocityImpulse( Vector(0,0,-vecVelocity.z*0.75) )
                pass

            # Under powered flight now.
            # SetMoveType( MOVETYPE_STEP )
            # SetGravity( MANHACK_GRAVITY )
            self.AddFlag( FL_FLY )

        def SoundInit(self):
            """ Start the manhack's engine sound. """
            self.enginepitch1 = MANHACK_MIN_PITCH1
            self.enginepitch1time = gpGlobals.curtime
            self.enginepitch2 = MANHACK_MIN_PITCH2
            self.enginepitch2time = gpGlobals.curtime

        def StopLoopingSounds(self):
            super().StopLoopingSounds()
            self.enginepitch1 = -1
            self.enginepitch1time = gpGlobals.curtime
            self.enginepitch2 = -1
            self.enginepitch2time = gpGlobals.curtime
            
        def ShouldGib(self, info):
            return self.gib
            
        def PlayerHasMegaPhysCannon(self):
            return False
            
        def HasPhysicsAttacker(self, dt):
            # If the player is holding me now, or I've been recently thrown
            # then return a pointer to that player
            if self.IsHeldByPhyscannon() or (gpGlobals.curtime - dt <= self.lastphysicsinfluencetime):
                return self.physicsattacker
            return None

        def TakeDamageFromVehicle(self, index, pEvent):
            """ Take damage from a vehicle it's like a really big crowbar  """
            # Use the vehicle velocity to determine the damage
            otherIndex = not index
            pOther = pEvent.GetEnt(otherIndex)

            flSpeed = pEvent.preVelocity[ otherIndex ].Length()
            flSpeed = clamp( flSpeed, 300.0, 600.0 )
            flDamage = SimpleSplineRemapVal( flSpeed, 300.0, 600.0, 0.0, 1.0 )
            if flDamage == 0.0:
                return

            flDamage *= 20.0

            damagePos = Vector()
            pEvent.pInternalData.GetContactPoint( damagePos )

            damageForce = 2.0 * pEvent.postVelocity[index] * pEvent.pObjects[index].GetMass()
            if damageForce == vec3_origin:
                # self can happen if self entity is a func_breakable, and can't move.
                # Use the velocity of the entity that hit us instead.
                damageForce = 2.0 * pEvent.postVelocity[not index] * pEvent.pObjects[not index].GetMass()
            
            assert(damageForce != vec3_origin)
            dmgInfo = CTakeDamageInfo(pOther, pOther, damageForce, damagePos, flDamage, DMG_CRUSH)
            self.TakeDamage(dmgInfo)

        def TakeDamageFromPhysicsImpact(self, index, pEvent):
            """ Take damage from combine ball """
            pHitEntity = pEvent.GetEnt(not index)

            # NOTE: Bypass the normal impact energy scale here.
            flDamageScale = 10.0 if self.PlayerHasMegaPhysCannon() else 1.0
            damageType = 0
            damage = CalculateDefaultPhysicsDamage(index, pEvent, flDamageScale, True, damageType)
            if damage == 0:
                return

            damagePos = Vector()
            pEvent.pInternalData.GetContactPoint(damagePos)
            damageForce = pEvent.postVelocity[index] * pEvent.pObjects[index].GetMass()
            if damageForce == vec3_origin:
                # self can happen if self entity is motion disabled, and can't move.
                # Use the velocity of the entity that hit us instead.
                damageForce = pEvent.postVelocity[not index] * pEvent.pObjects[not index].GetMass()

            # FIXME: self doesn't pass in who is responsible if some other entity "caused" self collision
            PhysCallbackDamage(self, CTakeDamageInfo( pHitEntity, pHitEntity, damageForce, damagePos, damage, damageType ), pEvent, index)

        MANHACK_SMASH_TIME = 0.35 # How long after being thrown from a physcannon that a manhack is eligible to die from impact
        def VPhysicsCollision(self, index, pEvent):
            super().VPhysicsCollision(index, pEvent)

            # Take no impact damage while being carried.
            if self.IsHeldByPhyscannon():
                return

            # Wake us up
            #if self.GetSpawnFlags() & self.SF_MANHACK_PACKED_UP:
            #    SetCondition(COND_LIGHT_DAMAGE)

            otherIndex = not index
            pHitEntity = pEvent.GetEnt(otherIndex)

            pPlayer = self.HasPhysicsAttacker(self.MANHACK_SMASH_TIME)
            if pPlayer:
                if not pHitEntity:
                    self.TakeDamageFromPhyscannon(pPlayer)
                    #self.StopBurst(True)
                    return

                # Don't take damage from NPCs or server ragdolls killed by the manhack
                #pRagdollProp = dynamic_cast<CRagdollProp*>(pHitEntity)
                #if not pHitEntity.IsNPC() and (not pRagdollProp or pRagdollProp.GetKiller() != self):
                #    self.TakeDamageFromPhyscannon( pPlayer )
                #    self.StopBurst( True )
                #    return

            if pHitEntity:
                # It can take physics damage if it rams into a vehicle
                #if pHitEntity.GetServerVehicle():
                #    self.TakeDamageFromVehicle(index, pEvent)
                if pHitEntity.HasPhysicsAttacker(0.5):
                    # It also can take physics damage from things thrown by the player.
                    self.TakeDamageFromPhysicsImpact(index, pEvent)
                elif FClassnameIs( pHitEntity, "prop_combine_ball" ):
                    # It also can take physics damage from a combine ball.
                    self.TakeDamageFromPhysicsImpact(index, pEvent)
                elif self.health <= 0:
                    self.TakeDamageFromPhysicsImpact(index, pEvent)

                #self.StopBurst(True)

        def VPhysicsShadowCollision(self, index, pEvent):
            otherIndex = not index
            pOther = pEvent.GetEnt(otherIndex)

            if pOther.GetMoveType() == MOVETYPE_VPHYSICS:
                self.HitPhysicsObject( pOther )
            
            super().VPhysicsShadowCollision( index, pEvent )

        def CrashTouch(self, pOther):
            """ Manhack is out of control! (dying) Just explode as soon as you touch anything! """
            info = CTakeDamageInfo(GetWorldEntity(), GetWorldEntity(), 25, DMG_CRUSH)

            CorpseGib(info)

        def CreateSmokeTrail(self):
            """ Create smoke trail! """
            if self.HasSpawnFlags(self.SF_MANHACK_NO_DAMAGE_EFFECTS):
                return

            if self.smoketrail != None:
                return

            pSmokeTrail =  SmokeTrail.CreateSmokeTrail()
            if not pSmokeTrail:
                return

            pSmokeTrail.spawnrate = 20
            pSmokeTrail.particlelifetime = 0.5
            pSmokeTrail.startsize	= 8
            pSmokeTrail.endsize		= 32
            pSmokeTrail.spawnradius	= 5
            pSmokeTrail.m_minspeed		= 15
            pSmokeTrail.m_maxspeed		= 25
            
            pSmokeTrail.m_startcolor = Vector(0.4, 0.4, 0.4)
            pSmokeTrail.endcolor = Vector(0, 0, 0)
            
            pSmokeTrail.SetLifetime(-1)
            pSmokeTrail.FollowEntity(self)

            self.smoketrail = pSmokeTrail

        def DestroySmokeTrail(self):
            if self.smoketrail:
                UTIL_Remove(self.smoketrail)
                self.smoketrail = None

        def CorpseGib(self, info):
            vecGibVelocity = Vector()
            vecGibAVelocity = AngularImpulse()

            if info.GetDamageType() & DMG_CLUB:
                # If clubbed to death, break apart before the attacker's eyes!
                vecGibVelocity = g_vecAttackDir * -150

                vecGibAVelocity.x = random.uniform( -2000, 2000 )
                vecGibAVelocity.y = random.uniform( -2000, 2000 )
                vecGibAVelocity.z = random.uniform( -2000, 2000 )
            else:
                # Shower the pieces with my velocity.
                vecGibVelocity = Vector(self.currentvelocity)

                vecGibAVelocity.x = random.uniform( -500, 500 )
                vecGibAVelocity.y = random.uniform( -500, 500 )
                vecGibAVelocity.z = random.uniform( -500, 500 )

            # TODO: Causes random problems when enabled (collision with terrain disappearing...)
            #PropBreakableCreateAll(self.GetModelIndex(), None, self.GetAbsOrigin(), self.GetAbsAngles(), vecGibVelocity, vecGibAVelocity, 1.0, 60, COLLISION_GROUP_DEBRIS )

            self.RemoveDeferred()

            self.KillSprites(0.0)

            return True

        def ComputeSliceBounceVelocity(self, pHitEntity, tr):
            """ Computes the slice bounce velocity """
            if pHitEntity.IsAlive() and FClassnameIs( pHitEntity, "func_breakable_surf" ):
                # We want to see if the manhack hits a breakable pane of glass. To keep from checking
                # The classname of the HitEntity on each impact, we only do this check if we hit 
                # something that's alive. Anyway, prevent the manhack bouncing off the pane of glass,
                # since this impact will shatter the glass and let the manhack through.
                return

            vecDir = Vector()
            
            # If the manhack isn't bouncing away from whatever he sliced, force it.
            VectorSubtract(self.WorldSpaceCenter(), pHitEntity.WorldSpaceCenter(), vecDir)
            VectorNormalize(vecDir)
            vecDir *= 200
            vecDir[2] = 0.0
            
            # Knock it away from us
            if self.VPhysicsGetObject() != None:
                self.VPhysicsGetObject().ApplyForceOffset(vecDir * 4, self.GetAbsOrigin())

            # Also set our velocity
            self.currentvelocity = Vector(vecDir)

        def IsHeldByPhyscannon(self):
            return self.VPhysicsGetObject() and (self.VPhysicsGetObject().GetGameFlags() & FVPHYSICS_PLAYER_HELD)

        def Slice(self, pHitEntity, flInterval, tr):
            """ We've touched something that we can hurt. Slice it! """
            dir = (tr.endpos - tr.startpos)
            if dir == vec3_origin:
                dir = tr.ent.GetAbsOrigin() - self.GetAbsOrigin()
                
             # Tell AI we sliced (or tried to slice)
            self.DispatchEvent('OnSlice', dir)  
            
            # Don't hurt the player if I'm in water
            if self.GetWaterLevel() > 0 and pHitEntity.IsPlayer():
                return
                
            # Can't do damage within nextattacktime
            if gpGlobals.curtime < self.nextattacktime:
                return

            # Can't slice allies and neutral units
            if self.IRelationType(pHitEntity) != D_HT:
                return

            # Can't slice players holding it with the phys cannon
            if self.IsHeldByPhyscannon():
                if pHitEntity and (pHitEntity == self.HasPhysicsAttacker(FLT_MAX)):
                    return

            if pHitEntity.takedamage == DAMAGE_NO:
                return

            # Damage must be scaled by flInterval so framerate independent
            attackinfo = self.unitinfo.AttackMelee
            #flDamage = attackinfo.damage * flInterval
            flDamage = attackinfo.damage

            #if pHitEntity.IsPlayer():
            #    flDamage *= 2.0
            
            # Held manhacks do more damage
            #if self.IsHeldByPhyscannon():
                # Deal 100 damage/sec
                #flDamage = 100.0 * flInterval
            
            '''
            #elif pHitEntity.IsNPC() and self.HasPhysicsAttacker(self.MANHACK_SMASH_TIME):
            #    extern ConVar sk_combine_guard_health
                # NOTE: The else here is essential.
                # The physics attacker *will* be set even when the manhack is held
            #    flDamage = sk_combine_guard_health.GetFloat() # the highest healthed fleshy enemy
            
            elif ( dynamic_cast<CBaseProp*>(pHitEntity) or dynamic_cast<CBreakable*>(pHitEntity) )
            
                # If we hit a prop, we want it to break immediately
                flDamage = pHitEntity.GetHealth()
            
            elif ( pHitEntity.IsNPC() and IRelationType( pHitEntity ) == D_HT  and FClassnameIs( pHitEntity, "npc_combine_s" ) ) 
            
                flDamage *= 6.0f
            '''

            #if flDamage < 1.0:
            #    flDamage = 1.0

            info = CTakeDamageInfo(self, self, flDamage, DMG_SLASH)

            # check for actual "ownership" of damage
            pPlayer = self.HasPhysicsAttacker(self.MANHACK_SMASH_TIME)
            if pPlayer:
                info.SetAttacker(pPlayer)

            CalculateMeleeDamageForce(info, dir, tr.endpos)
            pHitEntity.TakeDamage( info )

            # Spawn some extra blood where we hit
            if pHitEntity.BloodColor() == DONT_BLEED:
                data = CEffectData()
                velocity = Vector(self.currentvelocity)

                data.origin = tr.endpos
                data.angles = self.GetAbsAngles()

                VectorNormalize(velocity)
                
                data.normal = (tr.plane.normal + velocity) * 0.5

                DispatchEffect("ManhackSparks", data)

                self.EmitSound("NPC_Manhack.Grind")

                #TODO: What we really want to do is get a material reference and emit the proper sprayage! - jdw
            else:
                SpawnBlood(tr.endpos, g_vecAttackDir, pHitEntity.BloodColor(), 6)
                self.EmitSound( "NPC_Manhack.Slice" )

            # Pop back a little bit after hitting the player
            self.ComputeSliceBounceVelocity( pHitEntity, tr )

            # Save off when we last hit something
            self.lastdamagetime = gpGlobals.curtime

            # Reset our state and give the player time to react
            #self.StopBurst( True )
            
        def Bump(self, pHitEntity, flInterval, tr):
            """ We've touched something solid. Just bump it. """
            if not self.VPhysicsGetObject():
                return

            # Surpressing this behavior
            if self.bumpsuppresstime > gpGlobals.curtime:
                return

            if pHitEntity.GetMoveType() == MOVETYPE_VPHYSICS: #and pHitEntity.Classify()!=CLASS_MANHACK )
                self.HitPhysicsObject( pHitEntity )

            # We've hit something so deflect our velocity based on the surface
            # norm of what we've hit
            if flInterval > 0:
                moveLen = ( (self.currentvelocity * flInterval) * (1.0 - tr.fraction) ).Length()

                moveVec = (tr.plane.normal/flInterval)*moveLen

                # If I'm totally dead, don't bounce me up
                if self.health <=0 and moveVec.z > 0:
                    moveVec.z = 0

                # If I'm right over the ground don't push down
                #if moveVec.z < 0:
                #    floorZ = self.GetFloorZ(self.GetAbsOrigin())
                #    if (abs(self.GetAbsOrigin().z - floorZ) < 36)
                #        moveVec.z = 0
                        
                myUp = Vector()
                self.VPhysicsGetObject().LocalToWorldVector(myUp, Vector( 0.0, 0.0, 1.0 ))

                # plane must be something that could hit the blades
                if abs(DotProduct(myUp, tr.plane.normal)) < 0.25:
                    data = CEffectData()
                    velocity = Vector(self.currentvelocity)

                    data.origin = tr.endpos
                    data.angles = self.GetAbsAngles()

                    VectorNormalize( velocity )
                    
                    data.normal = ( tr.plane.normal + velocity ) * 0.5

                    DispatchEffect( "ManhackSparks", data )

                    filter = CBroadcastRecipientFilter()

                    te.DynamicLight( filter, 0.0, self.GetAbsOrigin(), 255, 180, 100, 0, 50, 0.3, 150 )
                    
                    # add some spin, but only if we're not already going fast..
                    vecVelocity = Vector()
                    vecAngVelocity = AngularImpulse()
                    self.VPhysicsGetObject().GetVelocity(vecVelocity, vecAngVelocity)
                    flDot = DotProduct(myUp, vecAngVelocity)
                    if abs(flDot) < 100:
                        #torque = myUp * (1000 - flDot * 10)
                        torque = myUp * (1000 - flDot * 2)
                        self.VPhysicsGetObject().ApplyTorqueCenter( torque )
                    
                    if not (self.GetSpawnFlags() & self.SF_NPC_GAG):
                        self.EmitSound( "NPC_Manhack.Grind" )

                    # For decals and sparks we must trace a line in the direction of the surface norm
                    # that we hit.
                    decalTrace = trace_t()
                    UTIL_TraceLine( self.GetAbsOrigin(), self.GetAbsOrigin() - (tr.plane.normal * 24),MASK_SOLID, self, COLLISION_GROUP_NONE, decalTrace )

                    if decalTrace.fraction != 1.0:
                        # Leave decal only if colliding horizontally
                        if (DotProduct(Vector(0,0,1),decalTrace.plane.normal)<0.5) and (DotProduct(Vector(0,0,-1),decalTrace.plane.normal)<0.5):
                            UTIL_DecalTrace( decalTrace, "ManhackCut" )
                
                # See if we will not have a valid surface
                if tr.allsolid or tr.startsolid:
                    # Build a fake reflection back along our current velocity because we can't know how to reflect off
                    # a non-existant surface! -- jdw

                    vecRandomDir = RandomVector( -1.0, 1.0 )
                    self.currentvelocity = Vector( vecRandomDir * 50.0 )
                    self.bumpsuppresstime = gpGlobals.curtime + 0.5
                else:
                    # This is a valid hit and we can deflect properly
                    VectorNormalize( moveVec )
                    hitAngle = -DotProduct( tr.plane.normal, -moveVec )

                    vReflection = tr.plane.normal * hitAngle * 2.0 + -moveVec

                    flSpeed = self.currentvelocity.Length()
                    self.currentvelocity = Vector( self.currentvelocity + vReflection * flSpeed * 0.5 )

            # -------------------------------------------------------------
            # If I'm on a path check LOS to my next node, and fail on path
            # if I don't have LOS.  Note this is the only place I do this,
            # so the manhack has to collide before failing on a path
            # -------------------------------------------------------------
            '''
            if GetNavigator().IsGoalActive() && !(GetNavigator().GetPath().CurWaypointFlags() & bits_WP_TO_PATHCORNER):
                AIMoveTrace_t moveTrace
                GetMoveProbe().MoveLimit( NAV_GROUND, GetAbsOrigin(), GetNavigator().GetCurWaypointPos(), 
                    MoveCollisionMask(), GetEnemy(), &moveTrace )

                if (IsMoveBlocked( moveTrace ) && 
                    not moveTrace.pObstruction.ClassMatches( self.GetClassname() )):
                    TaskFail(FAIL_NO_ROUTE)
                    GetNavigator().ClearGoal()
                    return
            '''

        def CheckCollisions(self, flInterval):
            # Trace forward to see if I hit anything. But trace forward along the
            # owner's view direction if you're being carried.
            physobj = self.VPhysicsGetObject()
            if not physobj:
                return
            
            vecTraceDir = Vector()
            vecCheckPos = Vector()
            physobj.GetVelocity(vecTraceDir, None)
            vecTraceDir *= flInterval
            if self.IsHeldByPhyscannon():
                pCarrier = self.HasPhysicsAttacker(float('inf'))
                if pCarrier:
                    if pCarrier.CollisionProp().CalcDistanceFromPoint(self.WorldSpaceCenter()) < 30:
                        AngleVectors(pCarrier.EyeAngles(), vecTraceDir, None, None)
                        vecTraceDir *= 40.0

            VectorAdd(self.GetAbsOrigin(), vecTraceDir, vecCheckPos)
            
            tr = trace_t()
            pHitEntity = None
            
            UTIL_TraceHull( self.GetAbsOrigin(), 
                            vecCheckPos, 
                            self.WorldAlignMins(), 
                            self.WorldAlignMaxs(),
                            self.movecollisionmask,
                            self,
                            COLLISION_GROUP_NONE,
                            tr )

            if (tr.fraction != 1.0 or tr.startsolid) and tr.ent:
                self.PhysicsMarkEntitiesAsTouching(tr.ent, tr)
                pHitEntity = tr.ent

                if self.held and tr.ent.IsNPC()() and tr.ent.IsPlayerAlly():
                    # Don't slice Alyx when she approaches to hack. We need a better solution for self!!
                    #Msg("Ignoring!\n")
                    return

                if (pHitEntity != None and 
                     pHitEntity.takedamage == DAMAGE_YES and 
                     gpGlobals.curtime > self.watersuspendtime):
                
                    # Slice self thing
                    self.Slice(pHitEntity, flInterval, tr)
                    self.bladespeed = 20.0
                else:
                    # Just bump into this thing.
                    self.Bump(pHitEntity, flInterval, tr)
                    self.bladespeed = 20.0

        def PlayFlySound(self):
            if self.enemy:
                flEnemyDist = (self.GetAbsOrigin() - self.enemy.GetAbsOrigin()).Length()
            else:
                flEnemyDist = float('inf')

            if self.GetSpawnFlags() & self.SF_NPC_GAG:
                # Quiet!
                return

            if self.watersuspendtime > gpGlobals.curtime:
                # Just went in water. Slow the motor!!
                if self.dirtypitch:
                    self.enginepitch1 = MANHACK_WATER_PITCH1
                    self.enginepitch1time = gpGlobals.curtime + 0.5
                    self.enginepitch2 = MANHACK_WATER_PITCH2
                    self.enginepitch2time = gpGlobals.curtime + 0.5
                    self.dirtypitch = False
            
            # Spin sound based on distance from enemy (unless we're crashing)
            elif self.enemy and self.IsAlive():
                if flEnemyDist < MANHACK_PITCH_DIST1:
                    # recalculate pitch.
                    flDistFactor = min( 1.0, 1 - flEnemyDist / MANHACK_PITCH_DIST1 ) 
                    iPitch1 = MANHACK_MIN_PITCH1 + ( ( MANHACK_MAX_PITCH1 - MANHACK_MIN_PITCH1 ) * flDistFactor) 

                    # NOTE: MANHACK_PITCH_DIST2 must be < MANHACK_PITCH_DIST1
                    flDistFactor = min( 1.0, 1 - flEnemyDist / MANHACK_PITCH_DIST2 ) 
                    iPitch2 = MANHACK_MIN_PITCH2 + ( ( MANHACK_MAX_PITCH2 - MANHACK_MIN_PITCH2 ) * flDistFactor) 

                    self.enginepitch1 = int(iPitch1)
                    self.enginepitch1time = gpGlobals.curtime + 0.1
                    self.enginepitch2 = int(iPitch2)
                    self.enginepitch2time = gpGlobals.curtime + 0.1

                    self.dirtypitch = True
                elif self.dirtypitch:
                    self.enginepitch1 = MANHACK_MIN_PITCH1
                    self.enginepitch1time = gpGlobals.curtime + 0.1
                    self.enginepitch2 = MANHACK_MIN_PITCH2
                    self.enginepitch2time = gpGlobals.curtime + 0.2
                    self.dirtypitch = False
                
            
            # If no enemy just play low sound
            elif self.IsAlive() and self.dirtypitch:
                self.enginepitch1 = MANHACK_MIN_PITCH1
                self.enginepitch1time = gpGlobals.curtime + 0.1
                self.enginepitch2 = MANHACK_MIN_PITCH2
                self.enginepitch2time = gpGlobals.curtime + 0.2

                self.dirtypitch = False

            # Play special engine every once in a while
            if gpGlobals.curtime > self.nextenginesoundtime and flEnemyDist < 48:
                self.nextenginesoundtime = gpGlobals.curtime + random.uniform(3.0, 10.0)

                self.EmitSound( "NPC_Manhack.EngineNoise" )

        def Event_Killed(self, info):
            # turn off the blur!
            self.SetBodygroup(self.MANHACK_BODYGROUP_BLUR, self.MANHACK_BODYGROUP_OFF)

            filter = CBroadcastRecipientFilter()
            
            # Sparks
            for i in range(0, 3):
                sparkPos = self.GetAbsOrigin()
                sparkPos.x += random.uniform(-12,12)
                sparkPos.y += random.uniform(-12,12)
                sparkPos.z += random.uniform(-12,12)
                te.Sparks(filter, 0.0, sparkPos, 2, 1, None)
            
            # Light
            te.DynamicLight(filter, 0.0, self.GetAbsOrigin(), 255, 180, 100, 0, 100, 0.1, 0 )
            if self.enginepitch1 < 0:
                # Probably self manhack was killed immediately after spawning. Turn the sound
                # on right now so that we can pitch it up for the crash!
                self.SoundInit()

            # Always gib when clubbed or blasted or crushed, or just randomly
            if (info.GetDamageType() & (DMG_CLUB|DMG_CRUSH|DMG_BLAST)) or (random.randint(0, 1)):
                self.gib = True
            else:
                self.gib = False
                
                #FIXME: These don't stay with the ragdolls currently -- jdw
                # Long fadeout on the sprites!!
                self.KillSprites(0.0)

            super().Event_Killed( info )
        
        def HitPhysicsObject(self, pOther):
            pOtherPhysics = pOther.VPhysicsGetObject()
            pos = Vector()
            posOther = Vector()
            # Put the force on the line between the manhack origin and hit object origin
            self.VPhysicsGetObject().GetPosition( pos, None )
            pOtherPhysics.GetPosition( posOther, None )
            dir = posOther - pos
            VectorNormalize(dir)
            # size/2 is approx radius
            pos += dir * self.WorldAlignSize().x * 0.5
            cross = Vector()

            # UNDONE: Use actual manhack up vector so the fake blade is
            # in the right plane?
            # Get a vector in the x/y plane in the direction of blade spin (clockwise)
            CrossProduct( dir, Vector(0,0,1), cross )
            VectorNormalize( cross )
            # force is a 30kg object going 100 in/s
            pOtherPhysics.ApplyForceOffset(cross * 30 * 100, pos)

        def ClampMotorForces(self, linear, angular):
            scale = self.bladespeed / 100.0

            # Msg("%.0f %.0f %.0f\n", linear.x, linear.y, linear.z )

            fscale = 3000 * scale

            if m_flEngineStallTime > gpGlobals.curtime:
                linear.x = 0.0
                linear.y = 0.0
                linear.z = clamp( linear.z, -fscale, 1200 if fscale < 1200 else fscale )
            else:
                # limit reaction forces
                linear.x = clamp( linear.x, -fscale, fscale )
                linear.y = clamp( linear.y, -fscale, fscale )
                linear.z = clamp( linear.z, -fscale, 1200 if fscale < 1200 else fscale )

            angular.x *= scale
            angular.y *= scale
            angular.z *= scale

        def KillSprites(self, flDelay):
            if self.eyeglow:
                self.eyeglow.FadeAndDie( flDelay )
                self.eyeglow = None

            if self.lightglow:
                self.lightglow.FadeAndDie( flDelay )
                self.lightglow = None

            # Re-enable for light trails
            '''
            if ( m_hLightTrail )
            
                m_hLightTrail.FadeAndDie( flDelay )
                m_hLightTrail = None
            '''
        
        def ShowHostile(self, hostile=True):
            if self.showinghostile == hostile:
                return

            #TODO: Open the manhack panels or close them, depending on the state
            self.showinghostile = hostile

            if hostile:
                self.EmitSound( "NPC_Manhack.ChargeAnnounce" )
            else:
                self.EmitSound( "NPC_Manhack.ChargeEnd" )
                
        def StartEye(self):
            #Create our Eye sprite
            if self.eyeglow == None:
                self.eyeglow = CSprite.SpriteCreate(MANHACK_GLOW_SPRITE, self.GetLocalOrigin(), False)
                self.eyeglow.SetAttachment(self, self.LookupAttachment( "Eye" ))
                
                if self.hackedbyalyx:
                    self.eyeglow.SetTransparency(kRenderTransAdd, 0, 255, 0, 128, kRenderFxNoDissipation)
                    self.eyeglow.SetColor(0, 255, 0)
                else:
                    self.eyeglow.SetTransparency(kRenderTransAdd, 255, 0, 0, 128, kRenderFxNoDissipation)
                    self.eyeglow.SetColor(255, 0, 0)

                self.eyeglow.SetBrightness(164, 0.1)
                self.eyeglow.SetScale(0.25, 0.1)
                self.eyeglow.SetAsTemporary()

            #Create our light sprite
            if self.lightglow == None:
                self.lightglow = CSprite.SpriteCreate(MANHACK_GLOW_SPRITE, self.GetLocalOrigin(), False)
                self.lightglow.SetAttachment(self, self.LookupAttachment("Light"))

                if self.hackedbyalyx:
                    self.lightglow.SetTransparency(kRenderTransAdd, 0, 255, 0, 128, kRenderFxNoDissipation)
                    self.lightglow.SetColor( 0, 255, 0 )
                else:
                    self.lightglow.SetTransparency(kRenderTransAdd, 255, 0, 0, 128, kRenderFxNoDissipation)
                    self.lightglow.SetColor( 255, 0, 0 )

                self.lightglow.SetBrightness( 164, 0.1 )
                self.lightglow.SetScale( 0.25, 0.1 )
                self.lightglow.SetAsTemporary()
                
        def SetEyeState(self, state):
            # Make sure we're active
            self.StartEye()

            if state == self.MANHACK_EYE_STATE_STUNNED:
                if self.eyeglow:
                    #Toggle our state
                    self.eyeglow.SetColor( 255, 128, 0 )
                    self.eyeglow.SetScale( 0.15, 0.1 )
                    self.eyeglow.SetBrightness( 164, 0.1 )
                    self.eyeglow.renderfx = kRenderFxStrobeFast
                
                if self.lightglow:
                    self.lightglow.SetColor( 255, 128, 0 )
                    self.lightglow.SetScale( 0.15, 0.1 )
                    self.lightglow.SetBrightness( 164, 0.1 )
                    self.lightglow.renderfx = kRenderFxStrobeFast
                    
                self.EmitSound("NPC_Manhack.Stunned")
            elif state == self.MANHACK_EYE_STATE_CHARGE:
                    if self.eyeglow:
                        #Toggle our state
                        if self.hackedbyalyx:
                            self.eyeglow.SetColor( 0, 255, 0 )
                        else:
                            self.eyeglow.SetColor( 255, 0, 0 )

                        self.eyeglow.SetScale( 0.25, 0.5 )
                        self.eyeglow.SetBrightness( 164, 0.1 )
                        self.eyeglow.renderfx = kRenderFxNone

                    if self.lightglow:
                        if self.hackedbyalyx:
                            self.lightglow.SetColor( 0, 255, 0 )
                        else:
                            self.lightglow.SetColor( 255, 0, 0 )

                        self.lightglow.SetScale( 0.25, 0.5 )
                        self.lightglow.SetBrightness( 164, 0.1 )
                        self.lightglow.renderfx = kRenderFxNone
            else:
                if self.eyeglow:
                    self.eyeglow.renderfx = kRenderFxNone
                    
    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if (self.enginepitch1 < 0) or (self.enginepitch2 < 0):
                self.SoundShutdown()
            else:
                self.SoundInit()
                if self.enginesound1 and self.enginesound2:
                    dt = self.enginepitch1time - gpGlobals.curtime if (self.enginepitch1time >= gpGlobals.curtime) else 0.0
                    CSoundEnvelopeController.GetController().SoundChangePitch(self.enginesound1, self.enginepitch1, dt)
                    dt = self.enginepitch2time - gpGlobals.curtime if (self.enginepitch2time >= gpGlobals.curtime) else 0.0
                    CSoundEnvelopeController.GetController().SoundChangePitch(self.enginesound2, self.enginepitch2, dt)

        def OnRestore(self):
            super().OnRestore()
            self.SoundInit()

        def UpdateOnRemove(self):
            """ Start the manhack's engine sound. """
            super().UpdateOnRemove()
            self.SoundShutdown()

        def SoundInit(self):
            """ Start the manhack's engine sound. """
            if (self.enginepitch1 < 0) or (self.enginepitch2 < 0):
                return

            # play an engine start sound!!
            filter = CPASAttenuationFilter(self)

            # Bring up the engine looping sound.
            if not self.enginesound1:
                self.enginesound1 = CSoundEnvelopeController.GetController().SoundCreate( filter, self.entindex(),
                                                                                          "NPC_Manhack.EngineSound1" )
                CSoundEnvelopeController.GetController().Play( self.enginesound1, 0.0, self.enginepitch1 )
                CSoundEnvelopeController.GetController().SoundChangeVolume( self.enginesound1, 0.7, 2.0 )

            if not self.enginesound2:
                self.enginesound2 = CSoundEnvelopeController.GetController().SoundCreate( filter, self.entindex(),
                                                                                          "NPC_Manhack.EngineSound2" )
                CSoundEnvelopeController.GetController().Play( self.enginesound2, 0.0, self.enginepitch2 )
                CSoundEnvelopeController.GetController().SoundChangeVolume( self.enginesound2, 0.7, 2.0 )

            if not self.bladesound:
                self.bladesound = CSoundEnvelopeController.GetController().SoundCreate( filter, self.entindex(),
                                                                                        "NPC_Manhack.BladeSound" )
                CSoundEnvelopeController.GetController().Play( self.bladesound, 0.0, self.enginepitch1 )
                CSoundEnvelopeController.GetController().SoundChangeVolume( self.bladesound, 0.7, 2.0 )

        def SoundShutdown(self):
            # Kill the engine!
            if self.enginesound1:
                CSoundEnvelopeController.GetController().SoundDestroy( self.enginesound1 )
                self.enginesound1 = None

            # Kill the engine!
            if self.enginesound2:
                CSoundEnvelopeController.GetController().SoundDestroy( self.enginesound2 )
                self.enginesound2 = None

            # Kill the blade!
            if self.bladesound:
                CSoundEnvelopeController.GetController().SoundDestroy( self.bladesound )
                self.bladesound = None
                
    def StartMeleeAttack(self, enemy):
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackMelee.attackspeed
        return False
    def RepairStep(self, intervalamount, repairhpps):
        if self.health >= self.maxhealth:
            return True
            
        # Cap speed at four or more workers
        n = len(self.constructors)
        if n > 1:
            intervalamount *= (1 + ((n - 1) ** 0.5)) / n
            
        self.health += int(ceil(intervalamount*repairhpps))
        self.health = min(self.health, self.maxhealth)
        if self.health >= self.maxhealth:
            self.OnHealed()
            return True
        return False  
    def OnHealed(self):pass
    def NeedsUnitConstructing(self, unit=None):
        return True
    repairable = True
    constructors = SetField(networked=True, save=False)
    constructability = 'combine_repair'
        
    # Animation state
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=90.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.playfallactinair = False
        
    if isserver:
         class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionAttack(BaseClass.BehaviorGenericClass.ActionAttack):
                last_dir = None
                last_moveaway = 0.0

                def OnStart(self):
                    self.last_moveaway = gpGlobals.curtime
                    return super().OnStart()
                    
                def Update(self):
                    outer = self.outer
                    enemy = self.enemy

                    if not outer.IsValidEnemy(enemy):
                        return self.Done('Lost enemy')
                    
                    # Might be waiting until moving closer until we are under attack or until we have LOS
                    if self.waitmoveuntilunderattack and (self.atgoal or (gpGlobals.curtime - outer.lastenemyattack) < 2.0 or outer.FastLOSCheck(enemy.WorldSpaceCenter())):
                        self.ClearWaitMoveUntilUnderAttack()

                    if self.last_dir and self.outer.mv.HasBlocker(self.outer.enemy):
                        return self.OnSlice(self.last_dir)
                        
                    vel = outer.GetAbsVelocity().Length()
                    if vel < 20.0 and self.last_moveaway + 0.5 < gpGlobals.curtime:
                        if not self.last_dir:
                            self.last_dir = enemy.GetAbsOrigin() - outer.GetAbsOrigin()
                        outer.SetNavIgnore(2.0) # Temporary ignore other units
                        return self.OnSlice(self.last_dir)
                            
                    return super().Update()
                
                def OnSlice(self, dir):
                    self.last_dir = Vector(dir)
                    self.last_dir.z = 0
                    VectorNormalize(self.last_dir)
                    self.last_moveaway = gpGlobals.curtime
                    return self.SuspendFor(self.behavior.ActionMoveAway, 'Sliced, moving away for new attack', -self.last_dir, 0.35)

                def OnNavAtGoal(self):
                    self.atgoal = True
                    # Base ActionAttack sets facing, which we don't want

            class ActionOrderAttack(ActionAttack):
                """ Order version of the attack action.
                    Clears the order when the enemy died.
                """
                def Init(self, order):
                    """ Inialize method.

                        Args:
                           order (Order): The order used for initializing the action.
                    """
                    super().Init(order.target, forcedenemy=True)
                    self.order = order

                def OnEnd(self):
                    self.order.Remove(dispatchevent=False)
                    super().OnEnd()

                def OnEnemyLost(self):
                    return self.Done('Lost enemy, clearing order')

            class ActionPreDeployed(BaseAction):
                """ Used as starting action when the metro police deploys a manhack. 
                    Does nothing. """
                def OnStart(self):
                    self.outer.aimoving = True
                    
                def OnEnd(self):
                    self.outer.aimoving = False
                    
                def Release(self):
                    return self.ChangeTo(self.behavior.ActionIdle, 'Released!')
                    
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_MANHACK_UNPACK',
    ])
    
    # Activity translation table
    acttables = {
        Activity.ACT_IDLE : Activity.ACT_FLY,
        Activity.ACT_RUN : Activity.ACT_FLY,
    }
    
    selectionparticlename = 'unit_circle_ground'
    cancappcontrolpoint = False
    jumpheight = 0
    
    movecollisionmask = MASK_NPCSOLID
    smoketrail = None
    hackedbyalyx = False
    eyeglow = None
    lightglow = None
    showinghostile = False
    lastphysicsinfluencetime = 0.0
    physicsattacker = None
    lastdamagetime = 0.0
    watersuspendtime = 0.0
    dirtypitch = False
    bladesactive = True
    maxenginepower = 1.0
    nextenginesoundtime = 0.0
    gib = True
    held = False
    bumpsuppresstime = 0.0
    currentvelocity = vec3_origin

    enginesound1 = None
    enginesound2 = None
    bladesound = None
    
    enginepitch1 = IntegerField(value=-1, networked=True, propname='propint1')
    enginepitch1time = FloatField(value=0.0, networked=True, propname='propfloat1')
    enginepitch2 = IntegerField(value=-1, networked=True, propname='propint2')
    enginepitch2time = FloatField(value=0.0, networked=True, propname='propfloat2')
    
    # Spawn flags
    spawnflags = FlagsField(keyname='spawnflags', flags=[
                            ('SF_NPC_GAG', (1 << 1), False),
                            ('SF_MANHACK_PACKED_UP', (1 << 16), False),
                            ('SF_MANHACK_NO_DAMAGE_EFFECTS', (1 << 17), False),
                            ('SF_MANHACK_USE_AIR_NODES', (1 << 18), False),
                            ('SF_MANHACK_CARRIED', (1 << 19), False),  # Being carried by a metrocop
                            ('SF_MANHACK_NO_DANGER_SOUNDS', (1 << 20), False)],
                            cppimplemented=True)
        
    MANHACK_EYE_STATE_IDLE = 0
    MANHACK_EYE_STATE_CHASE = 1
    MANHACK_EYE_STATE_CHARGE = 2
    MANHACK_EYE_STATE_STUNNED = 3
    
    MANHACK_BODYGROUP_BLADE = 1
    MANHACK_BODYGROUP_BLUR = 2
    MANHACK_BODYGROUP_OFF = 0
    MANHACK_BODYGROUP_ON = 1

class ManhackInfo(UnitInfo):
    name = 'unit_manhack'
    cls_name = 'unit_manhack'
    #tier = 1
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    costs = [[('requisition', 10)], [('kills', 1)]]
    #techrequirements = ['build_comb_armory']
    buildtime = 15.0
    health = 40
    maxspeed = 328.0
    viewdistance = 640
    displayname = '#CombManhack_Name'
    description = '#CombManhack_Description' 
    image_name = 'vgui/combine/units/unit_manhack'
    modelname = 'models/manhack.mdl'
    attributes = ['mechanic', 'slash']
    hulltype = 'HULL_TINY_CENTERED'
    #accuracy = 2.0
    #sai_hint = set(['sai_unit_support'])
    
    class AttackMelee(UnitInfo.AttackMelee):
        maxrange = 0.0
        damage = 3
        damagetype = DMG_SLASH
        attackspeed = 1.0
    attacks = 'AttackMelee'