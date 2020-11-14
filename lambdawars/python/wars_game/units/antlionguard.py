from srcbase import *
from vmath import *
from core.units import UnitInfo, UnitBaseCombat as BaseClass, EventHandlerAnimation
from wars_game.buildings.neutral_barricade import NeutralBarricadeInfo

from fields import BooleanField, FlagsField
from entities import entity
if isserver:
    from entities import (CSprite, gEntList, ImpulseScale, CalculateExplosiveDamageForce,
                          CTakeDamageInfo, D_HT, CalculateMeleeDamageForce)
    from utils import (UTIL_Remove, CTraceFilterMelee, CTraceFilterEntitiesOnly, CTraceFilter, trace_t, Ray_t,
                       UTIL_TraceRay, UTIL_TraceHull, StandardFilterRules, PassServerEntityFilter,
                       UTIL_ScreenShake, SHAKE_START)
    from particles import PrecacheParticleSystem
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from gamerules import GameRules
else:
    from entities import DataUpdateType_t, CLIENT_THINK_ALWAYS
    from particles import ParticleAttachment_t, DLight, DLIGHT_NO_MODEL_ILLUMINATION
    
if isserver:
    def ApplyChargeDamage(pAntlionGuard, pTarget, flDamage):
        """ Purpose: Calculate & apply damage & force for a charge to a target.
            Done outside of the guard because we need to do this inside a trace filter. """
        attackDir = ( pTarget.WorldSpaceCenter() - pAntlionGuard.WorldSpaceCenter() )
        VectorNormalize( attackDir )
        offset = RandomVector( -32, 32 ) + pTarget.WorldSpaceCenter()

        # Generate enough force to make a 75kg guy move away at 700 in/sec
        vecForce = attackDir * ImpulseScale( 75, 700 )

        # Deal the damage
        info = CTakeDamageInfo( pAntlionGuard, pAntlionGuard, vecForce, offset, flDamage, DMG_CLUB )
        pTarget.TakeDamage( info )

        # If I am a cavern guard attacking the player, and he still lives, then poison him too.
        if pAntlionGuard.cavernbreed and pTarget.IsPlayer() and pTarget.IsAlive() and pTarget.health > pAntlionGuard.ANTLIONGUARD_POISON_TO:
            # That didn't finish them. Take them down to one point with poison damage. It'll heal.
            pTarget.TakeDamage( CTakeDamageInfo( pAntlionGuard, pAntlionGuard, pTarget.health - pAntlionGuard.ANTLIONGUARD_POISON_TO, DMG_POISON ) )
            
    class CTraceFilterSkipPhysics(CTraceFilter):
        """ A simple trace filter class to skip small moveable physics objects """
        def __init__(self, passentity, collisionGroup, minMass):
            super(CTraceFilterSkipPhysics, self).__init__()
            
            self.passent = passentity
            self.collisiongroup = collisionGroup
            self.minmass = minMass
            
        def ShouldHitEntity(self, pHandleEntity, contentsMask):
            if not StandardFilterRules( pHandleEntity, contentsMask ):
                return False

            if not PassServerEntityFilter(pHandleEntity, self.passent):
                return False

            # Don't test if the game code tells us we should ignore this collision...
            pEntity = pHandleEntity
            if pEntity:
                if not pEntity.ShouldCollide(self.collisiongroup, contentsMask ):
                    return False
                
                if not GameRules().ShouldCollide(self.collisiongroup, pEntity.GetCollisionGroup()):
                    return False

                # don't test small moveable physics objects (unless it's an NPC)
                if not pEntity.IsUnit() and pEntity.GetMoveType() == MOVETYPE_VPHYSICS:
                    pPhysics = pEntity.VPhysicsGetObject()
                    assert(pPhysics)
                    if pPhysics.IsMoveable() and pPhysics.GetMass() < self.minmass:
                        return False
                elif pEntity.IsUnit() and self.passent.IRelationType( pEntity ) == D_HT:
                    pPhysics = pEntity.VPhysicsGetObject()
                    if pPhysics != None: 
                        if pPhysics.IsMoveable() and pPhysics.GetMass() < self.minmass:
                            ApplyChargeDamage( self.passent, pEntity, pEntity.health )
                            return False

                # If we hit an antlion, don't stop, but kill it
                #if pEntity.Classify() == CLASS_ANTLION:
                #    pGuard = self.passent
                #    ApplyChargeDamage( pGuard, pEntity, pEntity.health )
                #    return False
                    
            return True

    def TraceHull_SkipPhysics(vecAbsStart, vecAbsEnd, hullMin, 
                         hullMax, mask, ignore, 
                         collisionGroup, ptr, minMass ):
        traceFilter = CTraceFilterSkipPhysics( ignore, collisionGroup, minMass )
        UTIL_TraceHull(vecAbsStart, vecAbsEnd, hullMin, hullMax, mask, traceFilter, ptr)
        
    class CTraceFilterCharge(CTraceFilterEntitiesOnly):
        def __init__(self, passentity, collisionGroup, pAttacker):
            super().__init__()
        
            self.passent = passentity
            self.collisiongroup = collisionGroup
            self.attacker = pAttacker
        
        def ShouldHitEntity(self, pHandleEntity, contentsMask):
            if not StandardFilterRules( pHandleEntity, contentsMask ):
                return False

            if not PassServerEntityFilter( pHandleEntity, self.passent ):
                return False

            # Don't test if the game code tells us we should ignore this collision...
            pEntity = pHandleEntity 
            
            if pEntity:
                if not pEntity.ShouldCollide( self.collisiongroup, contentsMask ):
                    return False
                
                if not GameRules().ShouldCollide( self.collisiongroup, pEntity.GetCollisionGroup() ):
                    return False

                if pEntity.takedamage == DAMAGE_NO:
                    return False

                # Translate the vehicle into its driver for damage
                # if pEntity.GetServerVehicle() != None:
                    # pDriver = pEntity.GetServerVehicle().GetPassenger()

                    # if pDriver != None:
                        # pEntity = pDriver
        
                attackDir = pEntity.WorldSpaceCenter() - self.attacker.WorldSpaceCenter()
                VectorNormalize( attackDir )

                flDamage = 250

                info = CTakeDamageInfo( self.attacker, self.attacker, flDamage, DMG_CRUSH )
                CalculateMeleeDamageForce( info, attackDir, info.GetAttacker().WorldSpaceCenter(), 4.0 )

                pVictimBCC = pEntity if pEntity.IsUnit else None

                # Only do these comparisons between NPCs
                if pVictimBCC:
                    # Can only damage other NPCs that we hate
                    if self.attacker.IRelationType( pEntity ) == D_HT:
                        pEntity.TakeDamage( info )
                        return True
                else:
                    # Otherwise just damage passive objects in our way
                    pEntity.TakeDamage( info )
                    #Pickup_ForcePlayerToDropThisObject( pEntity )

            return False

@entity('unit_antlionguard', networked=True)
class UnitAntlionGuard(BaseClass):
    """ Antlion Guard """
    def __init__(self):
        super().__init__()
        
        self.caveglow = [None, None]

    def Precache(self):
        super().Precache() 
        
        if isclient:
            return
        
        self.PrecacheScriptSound( "NPC_AntlionGuard.Shove" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.HitHard" )

        if self.HasSpawnFlags(self.SF_ANTLIONGUARD_INSIDE_FOOTSTEPS):
            self.PrecacheScriptSound( "NPC_AntlionGuard.Inside.StepLight" )
            self.PrecacheScriptSound( "NPC_AntlionGuard.Inside.StepHeavy" )
        else:
            self.PrecacheScriptSound( "NPC_AntlionGuard.StepLight" )
            self.PrecacheScriptSound( "NPC_AntlionGuard.StepHeavy" )

        self.PrecacheScriptSound( "NPC_AntlionGuard.NearStepLight" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.NearStepHeavy" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.FarStepLight" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.FarStepHeavy" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.BreatheLoop" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.ShellCrack" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.Pain_Roar" )
        self.PrecacheModel( "sprites/grubflare1.vmt" )

        self.PrecacheScriptSound( "NPC_AntlionGuard.Anger" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.Roar" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.Die" )

        self.PrecacheScriptSound( "NPC_AntlionGuard.GrowlHigh" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.GrowlIdle" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.BreathSound" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.Confused" )
        self.PrecacheScriptSound( "NPC_AntlionGuard.Fallover" )

        self.PrecacheScriptSound( "NPC_AntlionGuard.FrustratedRoar" )

        PrecacheParticleSystem( "blood_antlionguard_injured_light" )
        PrecacheParticleSystem( "blood_antlionguard_injured_heavy" )

    def Spawn(self):
        self.SetBloodColor(BLOOD_COLOR_YELLOW)
        
        if isclient:
            super().Spawn()
            return
            
        super().Spawn()
        
        #self.AddEffects(EF_DIMLIGHT)
        
        if self.cavernbreed:
            self.skin = 1
            
            # Add glows
            self.caveglow[0] = self.CreateGlow( "attach_glow1" )
            self.caveglow[1] = self.CreateGlow( "attach_glow2" )  
        
    def UpdateOnRemove(self):
        self.DestroyGlows()

        super().UpdateOnRemove()
        
    def DestroyGlows(self):
        if self.caveglow[0]:
            UTIL_Remove( self.caveglow[0] )

            # reset it to NULL in case there is a double death cleanup for some reason.
            self.caveglow[0] = None

        if self.caveglow[1]:
            UTIL_Remove( self.caveglow[1] )

            # reset it to NULL in case there is a double death cleanup for some reason.
            self.caveglow[1] = None

    def CreateGlow(self, attachname):
        # Create the glow sprite
        sprite = CSprite.SpriteCreate( "sprites/grubflare1.vmt", self.GetLocalOrigin(), False )
        assert(sprite)
        if sprite == None:
            return

        sprite.TurnOn()
        sprite.SetTransparency( RenderMode_t.kRenderWorldGlow, 156, 169, 121, 164, RenderFx_t.kRenderFxNoDissipation )
        sprite.SetScale( 1.0 )
        sprite.SetGlowProxySize( 16.0 )
        attachment = self.LookupAttachment( attachname )
        sprite.SetParent( self, attachment )
        sprite.SetLocalOrigin( vec3_origin )
        sprite.SetOwnerNumber(self.GetOwnerNumber())

        # Don't uselessly animate, we're a static sprite!
        sprite.SetNextThink( TICK_NEVER_THINK )
        
        return sprite
        
    def OnChangeOwnerNumber(self, oldownernumber):
        super().OnChangeOwnerNumber(oldownernumber)
        
        for sprite in self.caveglow:
            if sprite:
                sprite.SetOwnerNumber(self.GetOwnerNumber())
                
    def Event_Killed(self, info):
        super().Event_Killed(info)
        
        self.DestroyGlows()
    
    def Shove(self):
        #target = self.enemy
        #if not target:
        #    return
        
        attackinfo = self.unitinfo.AttackMelee
        damage = attackinfo.damage
        
        # If the target's still inside the shove cone, ensure we hit him
        # vecForward = Vector()
        # vecEnd = Vector()
        # AngleVectors( self.GetAbsAngles(), vecForward )
        # flDistSqr = ( target.WorldSpaceCenter() - self.WorldSpaceCenter() ).LengthSqr()
        # v2LOS = ( target.WorldSpaceCenter() - self.WorldSpaceCenter() ).AsVector2D()
        # Vector2DNormalize(v2LOS)
        # flDot	= DotProduct2D (v2LOS, vecForward.AsVector2D() )
        # if flDistSqr < (self.attackinfo.maxrange*self.attackinfo.maxrange) and flDot >= self.ANTLIONGUARD_MELEE1_CONE:
            # vecEnd = target.WorldSpaceCenter()
        # else:
        vecEnd = self.WorldSpaceCenter() + (self.BodyDirection3D() * attackinfo.maxrange)

        # Use the melee trace to ensure we hit everything there
        tr = trace_t()
        dmgInfo = CTakeDamageInfo(self, self, damage, attackinfo.damagetype)
        traceFilter = CTraceFilterMelee( self, Collision_Group_t.COLLISION_GROUP_NONE, dmgInfo, 1.0, True )
        ray = Ray_t()
        ray.Init( self.WorldSpaceCenter(), vecEnd, Vector(-40,-40,   0), Vector(40, 40, 100)) #Vector(-16,-16,-16), Vector(16,16,16) ) # <- Use a rather big ray to ensure we hit something. It's really annoying to see it hit the air.
        UTIL_TraceRay( ray, MASK_SHOT_HULL, traceFilter, tr ) 
        pHurt = tr.ent

        # Knock things around
        self.ImpactShock(tr.endpos, 100.0, 250.0)

        if pHurt:
            traceDir = ( tr.endpos - tr.startpos )
            VectorNormalize( traceDir )

            # Generate enough force to make a 75kg guy move away at 600 in/sec
            vecForce = traceDir * ImpulseScale(75, 600)
            info = CTakeDamageInfo(self, self, vecForce, tr.endpos, damage, DMG_CLUB)
            pHurt.TakeDamage( info )

            self.EmitSound("NPC_AntlionGuard.Shove")

    '''def ImpactShock(self, origin, radius, magnitude, ignored = None):
        # Also do a local physics explosion to push objects away
        vecSpot = Vector()
        falloff = 1.0 / 2.5

        entity = None

        # Find anything within our radius
        
        while True:
            entity = gEntList.FindEntityInSphere( entity, origin, radius )
            if entity == None:
                break
            # Don't affect the ignored target
            if entity == ignored:
                continue
            if entity == self:
                continue

            # UNDONE: Ask the object if it should get force if it's not MOVETYPE_VPHYSICS?
            if entity.GetMoveType() == MOVETYPE_VPHYSICS or ( entity.VPhysicsGetObject() and entity.IsPlayer() == False ):
                vecSpot = entity.BodyTarget( self.GetAbsOrigin() )
                
                # decrease damage for an ent that's farther from the bomb.
                flDist = ( self.GetAbsOrigin() - vecSpot ).Length()

                if radius == 0 or flDist <= radius:
                    adjustedDamage = flDist * falloff
                    adjustedDamage = magnitude - adjustedDamage
            
                    if adjustedDamage < 1:
                        adjustedDamage = 1

                    info = CTakeDamageInfo( self, self, adjustedDamage, DMG_BLAST )
                    CalculateExplosiveDamageForce( info, (vecSpot - self.GetAbsOrigin()), self.GetAbsOrigin() )

                    entity.VPhysicsTakeDamage( info )'''
    
    # Charging
    def ChargeDamage(self, pTarget):
        if not pTarget:
            return

        # Might want to do this if the player is controlling an unit?
        # if pTarget.IsPlayer()
            # # Kick the player angles
            # pTarget.ViewPunch( QAngle( 20, 20, -30 ) )

            # Vector	dir = pTarget.WorldSpaceCenter() - self.WorldSpaceCenter()
            # VectorNormalize( dir )
            # dir.z = 0.0
            
            # Vector vecNewVelocity = dir * 250.0
            # vecNewVelocity[2] += 128.0
            # pTarget.SetAbsVelocity( vecNewVelocity )

            # color32 red = {128,0,0,128}
            # UTIL_ScreenFade( pTarget, red, 1.0, 0.1f, FFADE_IN )
        
        # Player takes less damage
        flDamage = 250
        
        # If it's being held by the player, break that bond
        #Pickup_ForcePlayerToDropThisObject( pTarget )

        # Calculate the physics force
        ApplyChargeDamage(self, pTarget, flDamage) 
    
    def ChargeLookAhead(self):
        """ While charging, look ahead and see if we're going to run into anything.
            If we are, start the gesture so it looks like we're anticipating the hit. """
        tr = trace_t()
        vecForward = Vector()
        self.GetVectors(vecForward, None, None)
        vecTestPos = self.GetAbsOrigin() + ( vecForward * self.groundspeed * 0.75 )
        testHullMins = self.WorldAlignMins()
        testHullMins.z += (self.stepsize * 2)
        TraceHull_SkipPhysics( self.GetAbsOrigin(), vecTestPos, testHullMins, self.WorldAlignMaxs(), MASK_SHOT_HULL, self, COLLISION_GROUP_NONE,  tr, self.VPhysicsGetObject().GetMass() * 0.5 )

        #NDebugOverlay::Box( tr.startpos, testHullMins, GetHullMaxs(), 0, 255, 0, True, 0.1f )
        #NDebugOverlay::Box( vecTestPos, testHullMins, GetHullMaxs(), 255, 0, 0, True, 0.1f )

        if tr.fraction != 1.0:
            # Start playing the hit animation
            pass
            #self.DoAnimation( self.ANIM_GESTURE, self.ACT_ANTLIONGUARD_CHARGE_ANTICIPATION )

    def HandleChargeImpact(self, vecImpact, pEntity):
        """ Handles the guard charging into something. Returns 0 on no impact, 1 on world and 2 on entity. """
        # Cause a shock wave from this point which will disrupt nearby physics objects
        self.ImpactShock(vecImpact, 128, 350)

        # Did we hit anything interesting?
        if not pEntity or pEntity.IsWorld():
            # Robin: Due to some of the finicky details in the motor, the guard will hit
            #		  the world when it is blocked by our enemy when trying to step up 
            #		  during a moveprobe. To get around this, we see if the enemy's within
            #		  a volume in front of the guard when we hit the world, and if he is,
            #		  we hit him anyway.
            #self.EnemyIsRightInFrontOfMe( pEntity )

            # Did we manage to find him? If not, increment our charge miss count and abort.
            if pEntity.IsWorld():
                self.chargemisses += 1
                return 1

        # Hit anything we don't like
        hitisbarricade = pEntity.IsUnit() and issubclass(getattr(pEntity, 'unitinfo', None), NeutralBarricadeInfo)
        if (self.IRelationType(pEntity) == D_HT or hitisbarricade) and (self.GetNextAttack() < gpGlobals.curtime):
            self.EmitSound( "NPC_AntlionGuard.Shove" )

            if not self.IsPlayingGesture( self.ACT_ANTLIONGUARD_CHARGE_HIT ):
                self.DoAnimation( self.ANIM_GESTURE, self.ACT_ANTLIONGUARD_CHARGE_HIT )
            
            self.ChargeDamage( pEntity )
            
            pEntity.ApplyAbsVelocityImpulse( ( self.BodyDirection2D() * 400 ) + Vector( 0, 0, 200 ) )

            if not pEntity.IsAlive():# and self.enemy == pEntity:
                self.enemy = None

            self.SetNextAttack(gpGlobals.curtime + 2.0)
            #self.SetActivity( ACT_ANTLIONGUARD_CHARGE_STOP )

            # We've hit something, so clear our miss count
            self.chargemisses = 0
            isbuilding = pEntity.IsUnit() and getattr(pEntity, 'isbuilding', False)
            if not isbuilding:
                return 2

        # Hit something we don't hate. If it's not moveable, crash into it.
        if pEntity.GetMoveType() == MOVETYPE_NONE or pEntity.GetMoveType() == MOVETYPE_PUSH:
            return 1

        # If it's a vphysics object that's too heavy, crash into it too.
        if pEntity.GetMoveType() == MOVETYPE_VPHYSICS:
            pPhysics = pEntity.VPhysicsGetObject()
            if pPhysics:
                # If the object is being held by the player, knock it out of his hands
                #if ( pPhysics.GetGameFlags() & FVPHYSICS_PLAYER_HELD )
                #    Pickup_ForcePlayerToDropThisObject( pEntity )
                #    return False
                    
                if not pPhysics.IsMoveable() or pPhysics.GetMass() > self.VPhysicsGetObject().GetMass() * 0.5:
                    return 1

        return 0
                    
    # Client effects
    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)

            #if type == DataUpdateType_t.DATA_UPDATE_CREATED:
            #    self.SetNextClientThink(CLIENT_THINK_ALWAYS)

            bleedinglevel = self.GetBleedingLevel()
            if bleedinglevel != self.bleedinglevel:
                self.bleedinglevel = bleedinglevel
                #self.UpdateBleedingPerformance() # Disable for now, causes heap corruption when the guard dies
                
        def GetBleedingLevel(self):
            if self.health > ( self.maxhealth >> 1 ):
                # greater than 50%
                return 0
            elif self.health > ( self.maxhealth >> 2 ):
                # less than 50% but greater than 25%
                return 1
            else:
                return 2
                
        def UpdateBleedingPerformance(self):
            prop = self.ParticleProp()
            
            if self.bleedingfx:
                prop.StopEmission(self.bleedingfx)
                self.bleedingfx = None

            if self.bleedinglevel == 1:
                self.bleedingfx = prop.Create( "blood_antlionguard_injured_heavy", ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW )
                if self.bleedingfx:
                    prop.AddControlPoint( self.bleedingfx, 1, self, ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW )
            elif self.bleedinglevel == 2:
                self.bleedingfx = prop.Create( "blood_antlionguard_injured_heavy", ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW )
                if self.bleedingfx:
                    prop.AddControlPoint( self.bleedingfx, 1, self, ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW )
            
        bleedingfx = None
        bleedinglevel = 0
        
        # def ClientThink(self):
            # # update the dlight. (always done because clienthink only exists for cavernguard)
            # if not self.dlight:
                # self.dlight = DLight(self)
                # self.dlight.color.r = 220
                # self.dlight.color.g = 255
                # self.dlight.color.b = 80
                # self.dlight.radius	= 180
                # self.dlight.minlight = int(128.0 / 256.0)
                # self.dlight.flags = DLIGHT_NO_MODEL_ILLUMINATION

            # self.dlight.origin	= self.GetAbsOrigin()

            # super().ClientThink()
        # dlight = None
        
    # Anim event handlers
    if isserver:
        def GuardShoveHandler(self, event):
            self.EmitSound("NPC_AntlionGuard.StepLight", event.eventtime)
            self.Shove()
            
        def GuardChargeHit(self, event):
            UTIL_ScreenShake( self.GetAbsOrigin(), 32.0, 4.0, 1.0, 512, SHAKE_START )
            self.EmitSound("NPC_AntlionGuard.HitHard")

            startPos = self.GetAbsOrigin()
            checkSize = ( self.CollisionProp().BoundingRadius() + 8.0 )
            endPos = startPos + ( self.BodyDirection3D() * checkSize )

            traceFilter = CTraceFilterCharge( self, COLLISION_GROUP_NONE, self )

            tr = trace_t()
            UTIL_TraceHull(startPos, endPos, self.WorldAlignMins(), self.WorldAlignMaxs(), MASK_SHOT, traceFilter, tr)

            #if g_debug_antlionguard.GetInt() == 1:
            #    hullMaxs = self.WorldAlignMaxs()
            #    hullMaxs.x += checkSize

            #    ndebugoverlay.BoxDirection( startPos, self.WorldAlignMins(), hullMaxs, self.BodyDirection2D(), 100, 255, 255, 20, 1.0 )

            #ndebugoverlay.Box3D( startPos, endPos, BodyDirection2D(), 
            #if self.chargetarget and self.chargetarget.IsAlive() == False:
            #    self.chargetarget = None
            #    self.chargetargetposition =None

            # Cause a shock wave from this point which will distrupt nearby physics objects
            self.ImpactShock( tr.endpos, 200, 500 )

    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_ANTLIONGUARD_SEARCH',
        'ACT_ANTLIONGUARD_PEEK_FLINCH',
        'ACT_ANTLIONGUARD_PEEK_ENTER',
        'ACT_ANTLIONGUARD_PEEK_EXIT',
        'ACT_ANTLIONGUARD_PEEK1',
        'ACT_ANTLIONGUARD_BARK',
        'ACT_ANTLIONGUARD_PEEK_SIGHTED',
        'ACT_ANTLIONGUARD_CHARGE_START',
        'ACT_ANTLIONGUARD_CHARGE_CANCEL',
        'ACT_ANTLIONGUARD_CHARGE_RUN',
        'ACT_ANTLIONGUARD_CHARGE_CRASH',
        'ACT_ANTLIONGUARD_CHARGE_STOP',
        'ACT_ANTLIONGUARD_CHARGE_HIT',
        'ACT_ANTLIONGUARD_CHARGE_ANTICIPATION',
        'ACT_ANTLIONGUARD_SHOVE_PHYSOBJECT',
        'ACT_ANTLIONGUARD_FLINCH_LIGHT',
        'ACT_ANTLIONGUARD_UNBURROW',
        'ACT_ANTLIONGUARD_ROAR',
        'ACT_ANTLIONGUARD_RUN_HURT',
        'ACT_ANTLIONGUARD_PHYSHIT_FR',
        'ACT_ANTLIONGUARD_PHYSHIT_FL',
        'ACT_ANTLIONGUARD_PHYSHIT_RR',
        'ACT_ANTLIONGUARD_PHYSHIT_RL',
    ] )

    # Vars
    chargemisses = 0
    
    # Events
    events = dict(BaseClass.events)
    events.update({
        'ANIM_STARTCHARGE' : EventHandlerAnimation('ACT_ANTLIONGUARD_CHARGE_START'),
        'ANIM_STOPCHARGE' : EventHandlerAnimation('ACT_ANTLIONGUARD_CHARGE_STOP'),
        'ANIM_CRASHCHARGE' : EventHandlerAnimation('ACT_ANTLIONGUARD_CHARGE_CRASH'),
    })
    
    if isserver:
        # Animation events
        aetable = {
            'AE_ANTLIONGUARD_CHARGE_HIT' : GuardChargeHit,
            'AE_ANTLIONGUARD_SHOVE_PHYSOBJECT' : None,
            'AE_ANTLIONGUARD_SHOVE' : GuardShoveHandler,
            'AE_ANTLIONGUARD_FOOTSTEP_LIGHT' : EmitSoundAnimEventHandler('NPC_AntlionGuard.FarStepLight'),
            'AE_ANTLIONGUARD_FOOTSTEP_HEAVY' : EmitSoundAnimEventHandler('NPC_AntlionGuard.FarStepHeavy'),
            'AE_ANTLIONGUARD_CHARGE_EARLYOUT' : BaseAnimEventHandler(),
            'AE_ANTLIONGUARD_VOICE_GROWL' : EmitSoundAnimEventHandler('NPC_AntlionGuard.Anger'),
            'AE_ANTLIONGUARD_VOICE_BARK' : EmitSoundAnimEventHandler('NPC_AntlionGuard.GrowlHigh'),
            'AE_ANTLIONGUARD_VOICE_PAIN' : EmitSoundAnimEventHandler('NPC_AntlionGuard.Pain_Roar'),
            'AE_ANTLIONGUARD_VOICE_SQUEEZE' : EmitSoundAnimEventHandler('NPC_AntlionGuard.Anger'),
            'AE_ANTLIONGUARD_VOICE_SCRATCH' : EmitSoundAnimEventHandler('NPC_AntlionGuard.Anger'),
            'AE_ANTLIONGUARD_VOICE_GRUNT' : EmitSoundAnimEventHandler('NPC_AntlionGuard.GrowlIdle'),
            'AE_ANTLIONGUARD_BURROW_OUT' : EmitSoundAnimEventHandler('NPC_Antlion.BurrowOut'),
            'AE_ANTLIONGUARD_VOICE_ROAR' : EmitSoundAnimEventHandler('NPC_AntlionGuard.Roar'),
        }
        
    # Settings
    jumpheight = 120.0
    ANTLIONGUARD_MELEE1_CONE = 0.7
    ANTLIONGUARD_POISON_TO = 12
    cavernbreed = BooleanField(value=False, keyname='cavernbreed')
    
    # Spawn flags
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_ANTLIONGUARD_SERVERSIDE_RAGDOLL', ( 1 << 16 ), False), 
         ('SF_ANTLIONGUARD_INSIDE_FOOTSTEPS', ( 1 << 17 ), False)], 
        cppimplemented=True)
            
    # Replace the default animstate class
    class AnimStateClass(BaseClass.AnimStateClass):
        def OnNewModel(self):
            super().OnNewModel()
            
            studiohdr = self.outer.GetModelPtr()
            
            headpitch = self.outer.LookupPoseParameter(studiohdr, "head_pitch")
            if headpitch < 0:
                return False
            headyaw = self.outer.LookupPoseParameter(studiohdr, "head_yaw")
            if headyaw < 0:
                return False
                
            self.outer.SetPoseParameter(studiohdr, headpitch, 0.0)
            self.outer.SetPoseParameter(studiohdr, headyaw, 0.0)
        
        def OnEndSpecificActivity(self, specificactivity):
            if specificactivity == self.outer.ACT_ANTLIONGUARD_CHARGE_START or specificactivity == self.outer.ACT_ANTLIONGUARD_CHARGE_RUN:
                return self.outer.ACT_ANTLIONGUARD_CHARGE_RUN
            return super().OnEndSpecificActivity(specificactivity)
    
# Register unit
class AntlionGuardSharedInfo(UnitInfo):
    cls_name    ='unit_antlionguard'
    maxspeed = 272.0
    attributes = ['heavy', 'crush']
    abilities   = {
        0 : 'charge',
        8 : 'attackmove',
        9 : 'holdposition',
    }
    sound_select = 'unit_antlionguard_select'
    sound_move = 'unit_antlionguard_move'
    sound_attack = 'unit_antlionguard_attack'
    sound_death = 'NPC_AntlionGuard.Die'
    modelname = 'models/antlion_guard.mdl'
    hulltype = 'HULL_LARGE'
    
    class AttackMelee(UnitInfo.AttackMelee):
        damage = 250
        damagetype = DMG_SLASH
        maxrange = 128.0
        attackspeed = 1.4
        cone = 0.99
    attacks = 'AttackMelee'
    
class AntlionGuardInfo(AntlionGuardSharedInfo):
    name        ='unit_antlionguard'
    image_name = 'vgui/units/unit_antlionguard.vmt'
    image_dis_name = 'vgui/units/unit_antlionguard_dis.vmt'
    portrait = 'resource/portraits/antlionGuardPortrait.bik'
    costs = [('grubs', 25)]
    population = 8
    buildtime = 120.0
    techrequirements = ['tier3_research']    
    abilities   = {
        0 : 'charge',
        8 : 'attackmove',
        9 : 'holdposition',
    }
    selectionpriority = 1
    displayname = '#AntlionGuard_Name'
    description = '#AntlionGuard_Description'
    health = 2000

class AntlionGuardCavernInfo(AntlionGuardSharedInfo):
    name = 'unit_antlionguardcavern'
    image_name = 'vgui/units/unit_antlionguardcavern.vmt'
    image_dis_name = 'vgui/units/unit_antlionguard_dis.vmt'
    portrait = 'resource/portraits/antlionGuardBreed.bik'
    costs = [('grubs', 35)]
    population = 8
    buildtime = 180.0
    techrequirements = ['tier3_research']    
    selectionpriority = 2
    displayname = '#AntlionGuardCavern_Name'
    description = '#AntlionGuardCavern_Description'
    keyvalues = {'cavernbreed' : '1' }
    health = 3000
    
class AntlionGuardCavernBossInfo(AntlionGuardCavernInfo):
    name = 'unit_antlionguardcavernboss'
    scale = 1.25
    health = 7500
    displayname = '#AntlionGuardCavernBoss_Name'
    description = '#AntlionGuardCavernBoss_Description'

class MissionAntlionGuardInfo(AntlionGuardInfo):
    name ='mission_unit_antlionguard'
    costs = [('requisition', 70)]
    techrequirements = []
    population = 4
    buildtime = 40.0
    health = 750
    maxspeed = 344.0

class MissionAntlionGuardCavernInfo(AntlionGuardCavernInfo):
    name ='mission_unit_antlionguardcavern'
    health = 500
    viewdistance = 704
    engagedistance = 700
    scrapdropchance = 0.0
    scale = 0.85