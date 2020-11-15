from srcbase import *
from vmath import *
from entities import CBaseCombatCharacter as BaseClass, entity, CWarsFlora, MOVECOLLIDE_FLY_CUSTOM
from gameinterface import ConVar, FCVAR_CHEAT
from utils import trace_t, UTIL_TraceHull, UTIL_ImpactTrace, UTIL_Remove, UTIL_SetOrigin, CWarsBulletsFilter
import ndebugoverlay

if isserver:
    from entities import (FL_EDICT_ALWAYS, CreateEntityByName, ClearMultiDamage, ApplyMultiDamage, CTakeDamageInfo,
                          CalculateMeleeDamageForce)

PELLET_MODEL = "models/swarm/Shotgun/ShotgunPellet.mdl"

if isserver:
    asw_flamer_force = ConVar("asw_flamer_force", "0.7f", FCVAR_CHEAT, "Force imparted by the flamer projectiles")
    asw_flamer_size = ConVar("asw_flamer_size", "40", FCVAR_CHEAT, "Radius at which flamer projectiles set aliens on fire")
    asw_flamer_debug = ConVar("asw_flamer_debug", "0", FCVAR_CHEAT, "Visualize flamer projectile collision")

    ASW_FLAMER_HULL_MINS = Vector(-asw_flamer_size.GetFloat(), -asw_flamer_size.GetFloat(), -asw_flamer_size.GetFloat() * 2.0)
    ASW_FLAMER_HULL_MAXS = Vector(asw_flamer_size.GetFloat(), asw_flamer_size.GetFloat(), asw_flamer_size.GetFloat() * 2.0)

@entity('flamer_projectile')
class FlamerProjectile(BaseClass):
    def Spawn(self):
        self.Precache()
        
        self.SetAllowNavIgnore(True)

        #SetModel( PELLET_MODEL )
        self.SetMoveType(MOVETYPE_FLYGRAVITY, MOVECOLLIDE_FLY_CUSTOM)

        self.damage = 5
        self.takedamage = DAMAGE_NO

        self.SetSize(-Vector(1,1,1), Vector(1,1,1))
        # self.SetSolid(SOLID_BBOX)
        self.SetSolid(SOLID_NONE)
        self.SetGravity(0.05)
        #SetCollisionGroup(ASW_COLLISION_GROUP_FLAMER_PELLETS) # ASW_COLLISION_GROUP_SHOTGUN_PELLET
        self.SetCollisionGroup(WARS_COLLISION_GROUP_IGNORE_ALL_UNITS) # pass through most units
        # self.SetCollisionGroup(COLLISION_GROUP_PROJECTILE)
        self.SetBlocksLOS(False)

        self.CreateEffects()
        self.vecoldpos = vec3_origin

        self.dietime = gpGlobals.curtime + 1.0 # will need to change size scale algos below if this changes
        self.SetThink(self.CollideThink, gpGlobals.curtime)

        # flamer projectile only lasts 1 second
        #SetThink(SUB_Remove)
        #SetNextThink(gpGlobals.curtime + 1.0)

    def CreateEffects(self):
        # Start up the eye glow
        #self.mainglow = CSprite::SpriteCreate( "swarm/sprites/whiteglow1.vmt", GetLocalOrigin(), False )

        #int	nAttachment = LookupAttachment( "fuse" )		# todo: make an attachment on the new model? is that even needed?

        if self.mainglow is not None:
            self.mainglow.FollowEntity(self)
            #self.mainglow.SetAttachment( self, nAttachment )
            self.mainglow.SetTransparency(kRenderGlow, 255, 255, 255, 200, kRenderFxNoDissipation)
            self.mainglow.SetScale(0.2)
            self.mainglow.SetGlowProxySize(4.0)

        # Start up the eye trail
        #self.glowtrail	= CSpriteTrail::SpriteTrailCreate( "swarm/sprites/greylaser1.vmt", GetLocalOrigin(), False )

        if self.glowtrail is not None:
            self.glowtrail.FollowEntity(self)
            #self.glowtrail.SetAttachment( self, nAttachment )
            self.glowtrail.SetTransparency(kRenderTransAdd, 128, 128, 128, 255, kRenderFxNone)
            self.glowtrail.SetStartWidth(8.0)
            self.glowtrail.SetEndWidth(1.0)
            self.glowtrail.SetLifeTime(0.5)

    def CreateVPhysics(self):
        # Create the object in the physics system
        self.VPhysicsInitNormal(SOLID_BBOX, FSOLID_NOT_STANDABLE, False)
        return True

    '''def PhysicsSolidMaskForEntity(self):
    
        return ( super().PhysicsSolidMaskForEntity() | CONTENTS_HITBOX ) & ~CONTENTS_GRATE
    '''

    def Precache(self):
        self.PrecacheModel(PELLET_MODEL)

        self.PrecacheModel("swarm/sprites/whiteglow1.vmt")
        self.PrecacheModel("swarm/sprites/greylaser1.vmt")

        super().Precache()

    def FlameHit(self, pOther, vecHitPos, bOnlyHurtUnignited):
        if not pOther:
            return

        bHurt = True

        if pOther.takedamage != DAMAGE_NO:
            if pOther == self.lasthitent:
                return

            if bOnlyHurtUnignited:
                if isinstance(pOther, CBaseAnimating) and pOther.IsOnFire():
                    bHurt = False
                    
            if bHurt:
                vecNormalizedVel = self.GetAbsVelocity()

                ClearMultiDamage()
                VectorNormalize( vecNormalizedVel )

                if self.GetOwnerEntity() and self.GetOwnerEntity().IsPlayer() and pOther.IsNPC():
                    dmgInfo = CTakeDamageInfo(self, self.getscreditedfordamage, self.damage, DMG_BURN)
                    dmgInfo.AdjustPlayerDamageInflictedForSkillLevel()
                    #CalculateMeleeDamageForce(dmgInfo, vecNormalizedVel, vecHitPos, 0)#asw_flamer_force.GetFloat())
                    dmgInfo.SetDamagePosition(vecHitPos)
                    dmgInfo.SetWeapon(self.creatorweapon)
                    if self.creatorweapon:
                        dmgInfo.attributes = self.creatorweapon.primaryattackattributes

                    pOther.TakeDamage(dmgInfo)
                else:
                    dmgInfo = CTakeDamageInfo(self, self.getscreditedfordamage, self.damage, DMG_BURN)
                    #CalculateMeleeDamageForce(dmgInfo, vecNormalizedVel, vecHitPos, 0)#asw_flamer_force.GetFloat())
                    dmgInfo.SetDamagePosition(vecHitPos)
                    dmgInfo.SetWeapon(self.creatorweapon)
                    if self.creatorweapon:
                        dmgInfo.attributes = self.creatorweapon.primaryattackattributes
                        
                    pOther.TakeDamage(dmgInfo)

                ApplyMultiDamage()

                # keep going through normal entities?
                self.lasthitent = pOther

            '''
            if pOther.Classify() == CLASS_ASW_SHIELDBUG:	# We also want to bounce off shield bugs
                Vector vel = GetAbsVelocity()
                Vector dir = vel
                VectorNormalize( dir )

                # reflect velocity around normal
                vel = -2.0f * dir + vel
                vel *= 0.4f

                # absorb 80% in impact
                self.SetAbsVelocity( vel )'''
            return

        #if pOther.GetCollisionGroup() == ASW_COLLISION_GROUP_PASSABLE:
        #    return

        tr = super().GetTouchTrace()

        # See if we struck the world
        if pOther.GetMoveType() == MOVETYPE_NONE and not ( tr.surface.flags & SURF_SKY ):
            vel = self.GetAbsVelocity()
            if tr.startsolid:
                if not self.insolid:
                    # UNDONE: Do a better contact solution that uses relative velocity?
                    vel *= -1.0 # bounce backwards
                    self.SetAbsVelocity(vel)
                
                self.insolid = True
                return
            
            self.insolid = False
            if tr.DidHit():
                dir = Vector(vel)
                VectorNormalize(dir)

                # reflect velocity around normal
                vel = tr.plane.normal * DotProduct(vel,tr.plane.normal) * -2.0 + vel
                vel *= 0.4
                
                # absorb 80% in impact
                #vel *= GRENADE_COEFFICIENT_OF_RESTITUTION
                self.SetAbsVelocity( vel )
            return
        else:
            # Put a mark unless we've hit the sky
            if not (tr.surface.flags & SURF_SKY):
                UTIL_ImpactTrace(tr, DMG_BURN)
            
            #self.KillEffects()
            UTIL_Remove(self)

    @classmethod
    def Flamer_Projectile_Create(cls, damage, position, angles, velocity, angVelocity, pOwner, pEntityToCreditForTheDamage= None, pCreatorWeapon=None):
        pellet = CreateEntityByName( "flamer_projectile" )
        pellet.SetAbsAngles( angles )
        pellet.Spawn()
        pellet.SetOwnerNumber(pOwner.GetOwnerNumber())
        pellet.SetOwnerEntity( pOwner )
        pellet.damage = damage
        pellet.getscreditedfordamage = pEntityToCreditForTheDamage if pEntityToCreditForTheDamage else pOwner
        UTIL_SetOrigin( pellet, position )
        pellet.SetAbsVelocity( velocity )

        pellet.creatorweapon = pCreatorWeapon

        return pellet
    

    '''
    #define ASW_FLAMER_PROJECTILE_ACCN 650.0f
    void def PhysicsSimulate()
    
        # Make sure not to simulate self guy twice per frame
        if (m_nSimulationTick == gpGlobals.tickcount)
            return

        # slow down the projectile's velocity	
        Vector dir = GetAbsVelocity()
        VectorNormalize(dir)		
        SetAbsVelocity(GetAbsVelocity() - (dir * gpGlobals.frametime * ASW_FLAMER_PROJECTILE_ACCN))
        dir = GetAbsVelocity()
        
        super().PhysicsSimulate()
    '''

    # need to force send as it has no model
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)

    def CollideThink(self):
        if gpGlobals.curtime >= self.dietime:
            self.SUB_Remove()
            return

        self.SetNextThink(gpGlobals.curtime + 0.1)
        
        origin = self.GetAbsOrigin()
        
        CWarsFlora.IgniteFloraInRadius(origin, 32.0, 30.0)

        if self.vecoldpos == vec3_origin:
            self.vecoldpos = origin

        tr  = trace_t()
        UTIL_TraceHull(origin, self.vecoldpos, -Vector(16, 16, 16), Vector(16, 16, 16), MASK_SOLID, self.BuildTraceFilter(), tr)

        # ndebugoverlay.Cross3D(origin, 0, 255, 0, 255, True, 0.1)

        if tr.ent and not isinstance(tr.ent, FlamerProjectile):
            # print("Flamer projectile CollideThinked %s" % tr.ent.GetClassname())
            self.FlameHit(tr.ent, tr.endpos, False)

            if asw_flamer_debug.GetBool():
                ndebugoverlay.Cross3D(tr.endpos, 10, 0, 0, 255, True, 10.0)
        
        '''
        # scan for setting on fire nearby NPCs
        if not bHit:
            tr = trace_t()
            ray = Ray_t()
            filter = CTraceFilterAliensEggsGoo( self, COLLISION_GROUP_NONE )				
            #UTIL_TraceHull(GetAbsOrigin(), GetAbsOrigin() + Vector(0,0,1), ASW_FLAMER_HULL_MINS, ASW_FLAMER_HULL_MAXS, MASK_SOLID, self, COLLISION_GROUP_NONE, &tr) 
            float size_scale = 0.5f + 0.5f * (1.0f - clamp<float>(self.dietime - gpGlobals.curtime, 0.0f, 1.0f))	# NOTE: assumes 1.0 lifetime
            ray.Init( GetAbsOrigin(), self.vecoldpos, ASW_FLAMER_HULL_MINS * size_scale, ASW_FLAMER_HULL_MAXS * size_scale )
            enginetrace.TraceRay( ray, MASK_SOLID, &filter, &tr )
            if ( tr.m_pEnt )
            						
                FlameHit(tr.m_pEnt, tr.endpos, !m_bHurtIgnited)
                #NDebugOverlay::Cross3D(tr.endpos, 10, 255, 0, 0, True, 10.0f)
                if (asw_flamer_debug.GetBool())
                
                    Msg("Flame hit %d %s\n", tr.m_pEnt.entindex(), tr.m_pEnt.GetClassname())
                    NDebugOverlay::SweptBox(GetAbsOrigin(), self.vecoldpos, ASW_FLAMER_HULL_MINS * size_scale, ASW_FLAMER_HULL_MAXS * size_scale, vec3_angle, 255, 255, 0, 0 ,0.1f)
                    NDebugOverlay::Line(GetAbsOrigin(), tr.m_pEnt.GetAbsOrigin(), 255, 255, 0, False, 0.1f )
                
            
            else if (tr.allsolid or tr.startsolid)
            
                if (asw_flamer_debug.GetBool())
                    NDebugOverlay::Box(GetAbsOrigin(), ASW_FLAMER_HULL_MINS * size_scale, ASW_FLAMER_HULL_MAXS * size_scale, 0, 0, 255, 0 ,0.1f)
            
            else
            
                if (asw_flamer_debug.GetBool())
                    NDebugOverlay::Box(GetAbsOrigin(), ASW_FLAMER_HULL_MINS * size_scale, ASW_FLAMER_HULL_MAXS * size_scale, 255, 0, 0, 0 ,0.1f)
        '''
        
        self.vecoldpos = self.GetAbsOrigin()

    def BuildTraceFilter(self):
        owner = self.GetOwnerEntity()
        trace_filter = CWarsBulletsFilter(owner, COLLISION_GROUP_PROJECTILE)
        trace_filter.SetPassEntity(owner)
        if owner.garrisoned_building:
            trace_filter.AddEntityToIgnore(owner.garrisoned_building)
        return trace_filter
        
    lasthitent = None
    mainglow = None
    glowtrail = None
    creatorweapon = None
    getscreditedfordamage = None
    insolid = False
    dietime = 0.0
    