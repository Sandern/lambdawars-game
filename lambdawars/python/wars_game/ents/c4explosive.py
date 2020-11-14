from srcbase import *
from vmath import *
from core.units import UnitBaseObject as BaseClass, UnitObjectInfo
from te import te, TE_EXPLFLAG_NONE, TE_EXPLFLAG_DLIGHT
from entities import entity, FOWFLAG_UNITS_MASK
from particles import PrecacheParticleSystem, DispatchParticleEffect
from physics import physprops

if isserver:
    from entities import CTakeDamageInfo, RadiusDamage, CLASS_NONE
    from utils import UTIL_DecalTrace, UTIL_PointContents, UTIL_TraceLine, trace_t
    from gameinterface import CPASFilter

class C4ExplosiveInfo(UnitObjectInfo):
    name = 'c4explosive_ent'
    cls_name = 'c4explosive'
    modelname = 'models/pg_props/pg_obj/ja_tnt.mdl'
    attributes = ['explosive']
    viewdistance = 128.0
    
    class AttackExplode(UnitObjectInfo.AttackBase):
        maxrange = 350.0
        damage = 220.0
        damagetype = DMG_BLAST
        attackspeed = 0
    attacks = 'AttackExplode'
    
@entity('c4explosive')
class C4Explosive(BaseClass):
    def Precache(self):
        self.PrecacheScriptSound('ability_c4exposive')
        self.PrecacheScriptSound(self.beepsound)
        self.PrecacheScriptSound("BaseGrenade.Explode")
        self.indexfireball = self.PrecacheModel('sprites/zerogxplode.vmt')
        self.indexwaterfireball = self.PrecacheModel('sprites/WXplo1.vmt')

        PrecacheParticleSystem("dss_explosion_grenade")
        
        super().Precache()

    def Spawn(self):
        self.Precache()

        super().Spawn()
        
        self.friendlydamage = True
        
        self.SetThink(self.StartBeepThink, gpGlobals.curtime + (self.detonatetime - 4.2), 'StartBeepThink')
        self.SetThink(self.DetonateThink, gpGlobals.curtime + self.detonatetime)
        
    def StartBeepThink(self):
        self.EmitSound(self.beepsound)
        
    def DetonateThink(self):
        self.Detonate()
        
    def Detonate(self):
        tr = trace_t()
        spot = Vector() # trace starts here!
        origin = self.GetAbsOrigin()

        self.SetThink(None)

        vecSpot = origin + Vector (0 , 0 , 8)
        UTIL_TraceLine(vecSpot, vecSpot + Vector ( 0, 0, -32 ), MASK_SHOT_HULL, self, COLLISION_GROUP_NONE, tr)

        if tr.startsolid:
            # Since we blindly moved the explosion origin vertically, we may have inadvertently moved the explosion into a solid,
            # in which case nothing is going to be harmed by the grenade's explosion because all subsequent traces will startsolid.
            # If this is the case, we do the downward trace again from the actual origin of the grenade. (sjb) 3/8/2007  (for ep2_outland_09)
            UTIL_TraceLine(origin, origin + Vector( 0, 0, -32), MASK_SHOT_HULL, self, COLLISION_GROUP_NONE, tr)

        self.Explode(tr)

        #if GetShakeAmplitude():
        #    UTIL_ScreenShake(origin, GetShakeAmplitude(), 150.0, 1.0, GetShakeRadius(), SHAKE_START)
        
    def Explode(self, pTrace):
        #self.SetModelName(NULL_STRING)#invisible
        self.AddSolidFlags(FSOLID_NOT_SOLID)

        #m_takedamage = DAMAGE_NO

        # Pull out of the wall a bit
        if pTrace.fraction != 1.0:
            self.SetAbsOrigin(pTrace.endpos + (pTrace.plane.normal * 0.6))

        vecAbsOrigin = self.GetAbsOrigin()
        contents = UTIL_PointContents(vecAbsOrigin, MASK_ALL)

        origin = self.GetAbsOrigin()
        
        attackinfo = self.unitinfo.AttackExplode
        dmgradius = attackinfo.maxrange
        damage = attackinfo.damage
        bitsDamageType = attackinfo.damagetype

        if pTrace.fraction != 1.0:
            vecNormal = pTrace.plane.normal
            pdata = physprops.GetSurfaceData(pTrace.surface.surfaceProps)
            filter = CPASFilter(vecAbsOrigin)

            te.Explosion(filter, -1.0, # don't apply cl_interp delay
                vecAbsOrigin,
                self.indexfireball if not ( contents & MASK_WATER ) else self.indexwaterfireball,
                dmgradius * .03, 
                25,
                TE_EXPLFLAG_NONE|TE_EXPLFLAG_DLIGHT,
                int(dmgradius),
                int(damage),
                vecNormal,
                pdata.game.material)
        else:
            filter = CPASFilter(vecAbsOrigin)
            te.Explosion(filter, -1.0, # don't apply cl_interp delay
                vecAbsOrigin, 
                self.indexfireball if not ( contents & MASK_WATER ) else self.indexwaterfireball,
                dmgradius * .03, 
                25,
                TE_EXPLFLAG_NONE|TE_EXPLFLAG_DLIGHT,
                int(dmgradius),
                int(damage))

        # Use the thrower's position as the reported position
        #vecReported = m_hThrower ? m_hThrower.GetAbsOrigin() : vec3_origin
        vecReported = Vector(vec3_origin)
        blastforce = Vector(vec3_origin)
        
        self.EmitSound( "BaseGrenade.Explode" )
        info = CTakeDamageInfo(self, self, None, blastforce, vecAbsOrigin, damage, bitsDamageType, 0, vecReported)
        info.forcefriendlyfire = True

        RadiusDamage(info, vecAbsOrigin, dmgradius, CLASS_NONE, None)
        DispatchParticleEffect("dss_explosion_grenade", origin, self.GetAbsAngles())

        UTIL_DecalTrace(pTrace, "Scorch")

        self.SetThink(self.SUB_Remove, gpGlobals.curtime)
        self.SetTouch(None)
        self.SetSolid(SOLID_NONE)
        
        self.AddEffects(EF_NODRAW)
        self.SetAbsVelocity(vec3_origin)
        
    beepsound = 'c4explosive.Beeb'
    unitinfofallback = C4ExplosiveInfo
    detonatetime = 4.2 # Default explode time, overridden by ability
    
    #: Fog of war flags of this unit.
    fowflags = FOWFLAG_UNITS_MASK
    
    