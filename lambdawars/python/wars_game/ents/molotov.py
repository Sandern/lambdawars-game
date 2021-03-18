from srcbase import (SOLID_BBOX, FSOLID_NOT_STANDABLE, COLLISION_GROUP_PROJECTILE, COLLISION_GROUP_DEBRIS,
                     FSOLID_VOLUME_CONTENTS, FSOLID_TRIGGER, DAMAGE_NO, DAMAGE_EVENTS_ONLY, DMG_BURN)
from vmath import Vector
from entities import entity
from core.ents import ThrowableObject as BaseClass
from core.units import CreateUnit
from utils import UTIL_EntitiesInSphere
from particles import PrecacheParticleSystem, PATTACH_ABSORIGIN_FOLLOW
from wars_game.abilities.throwmolotov import MolotovAttack
from fields import BooleanField

if isserver:
    from entities import CTakeDamageInfo

@entity('molotov', networked=True)
class Molotov(BaseClass):
    if isserver:
        def Precache(self):
            self.PrecacheModel(self.MOLOTOV_MODEL)
            self.PrecacheScriptSound('molotov.ignite')
            self.PrecacheScriptSound('molotov.extinguish')

            PrecacheParticleSystem(self.molotov_particle_name)

            super().Precache()

        def Spawn(self):
            self.Precache()

            super().Spawn()

            self.SetModel(self.MOLOTOV_MODEL)

            #self.SetSolid(SOLID_BBOX)
            #self.SetMoveType(MOVETYPE_FLYGRAVITY)
            self.SetSolidFlags(FSOLID_NOT_STANDABLE)
            #self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
            # Get better collision group?
            self.SetCollisionGroup(COLLISION_GROUP_DEBRIS)

            self.CreateVPhysics()

            self.Ignite(12.0, False)
            flame_entity = self.GetEffectEntity() # Above Ignite call sets the effect entity to the flame entity
            flame_entity.SetOwnerNumber(self.GetOwnerNumber())
            flame_entity.SetAttacker(self)
            flame_entity.SetFlameRadiusDamagePerSecond(0) # Pure visual

            #self.SetTouch(self.MolotovTouch)
        
    def CreateVPhysics(self):
        # Create the object in the physics system
        self.VPhysicsInitNormal(SOLID_BBOX, 0, False)
        self.VPhysicsGetObject().EnableDrag(False)
        return True

    def Detonate(self, other):
        self.SetTouch(None)
        self.is_burning_on_ground = True
        #DispatchParticleEffect(self.molotov_particle_name, self.GetAbsOrigin(), QAngle(0, 0, 0))
        #self.SetAbsVelocity(vec3_origin)
        if gpGlobals.curtime - self.__last_molotov_ignite_sound > 1.5:
            self.EmitSound('molotov.ignite')
            Molotov.__last_molotov_ignite_sound = gpGlobals.curtime
        self.burn_start_thinktime = gpGlobals.curtime
        self.SetThink(self.MolotovBurnThink, gpGlobals.curtime)
        
    def VPhysicsCollision(self, index, event):
        super().VPhysicsCollision(index, event)
        
        # Require a short minimum time before we zero the velocity on collision
        if gpGlobals.curtime - self.spawntime < 0.15:
            return

        # Will create another fire effect
        self.Extinguish()

        # Try merge with nearby dropped molotovs to reduce clutter
        targets = UTIL_EntitiesInSphere(320, self.GetAbsOrigin(), 16.0, 0)
        for target in targets:
            if target and target != self and target.GetClassname() == self.GetClassname() and target.is_burning_on_ground:
                # Increase burn time
                target.burn_start_thinktime = gpGlobals.curtime
                # Remove our self
                self.SetThink(self.SUB_Remove, gpGlobals.curtime)
                return
            
        physobj = self.VPhysicsGetObject()
        vel = Vector()
        ang = Vector()
        physobj.GetVelocity(vel, ang)
        vel.x = vel.y = 0.0
        physobj.SetVelocity(vel, ang)

        self.Detonate(None)

    def MolotovTouch(self, other):
        if other.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS | FSOLID_TRIGGER):
            # Some NPCs are triggers that can take damage (like antlion grubs). We should hit them.
            if (other.takedamage == DAMAGE_NO) or (other.takedamage == DAMAGE_EVENTS_ONLY):
                return

        if other.GetCollisionGroup() == COLLISION_GROUP_PROJECTILE:
            return
                
        self.Detonate(other)

    def MolotovBurnThink(self):
        if self.burn_start_thinktime + self.burn_time < gpGlobals.curtime:
            self.is_burning_on_ground = False
            if gpGlobals.curtime - self.__last_molotov_ignite_sound > 1.0:
                self.EmitSound('molotov.extinguish')
                Molotov.__last_molotov_extinguish_sound = gpGlobals.curtime
            self.SetThink(self.SUB_Remove, gpGlobals.curtime)
            return

        srcdamage = self.GetAbsOrigin()
        #attacker = self.GetThrower()
        self.damagecontroller = CreateUnit('unit_damage_controller', owner_number=self.GetOwnerNumber())
        if self.GetThrower():
            attacker = self.GetThrower()
        else:
            attacker = self.damagecontroller

        # TODO: in a better way!?
        attributes = {}
        for attr in MolotovAttack.attributes:
            attributes[attr.name] = attr(attacker)

        targets = UTIL_EntitiesInSphere(320, self.GetAbsOrigin(), 64.0, 0)
        for target in targets:
            if not target or not target.IsUnit():
                continue

            dmg_info = CTakeDamageInfo(self, attacker, 0, DMG_BURN)
            dmg_info.SetDamagePosition(srcdamage)
            dmg_info.attributes = attributes
            dmg_info.forcefriendlyfire = True

            target.TakeDamage(dmg_info)

        self.SetNextThink(gpGlobals.curtime + 0.1)

    if isclient:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.DestroyBurnParticle()

        def OnIsBurningOnGround(self):
            self.CreateBurnParticle()

        def DestroyBurnParticle(self):
            if not self.molotov_particle:
                return
            self.ParticleProp().StopEmission(self.molotov_particle)
            self.molotov_particle = None

        def CreateBurnParticle(self):
            if self.molotov_particle:
                return
            self.molotov_particle = self.ParticleProp().Create(self.molotov_particle_name, PATTACH_ABSORIGIN_FOLLOW)
            self.molotov_particle.SetControlPoint(1, Vector(60, 0, 0))
    else:
        def UpdateOnRemove(self):
            if self.damagecontroller:
                self.damagecontroller.Remove()
            
            super().UpdateOnRemove()

    burn_start_thinktime = 0
    #MOLOTOV_MODEL = 'models/pg_props/pg_weapons/pg_molotov.mdl'
    MOLOTOV_MODEL = "models/props_junk/garbage_glassbottle003a.mdl"

    __last_molotov_ignite_sound = 0
    __last_molotov_extinguish_sound = 0

    burn_time = 3.0;
    molotov_particle = None
    molotov_particle_name = 'particle_molotov_BASE'
    damagecontroller = None
    is_burning_on_ground = BooleanField(value=False, networked=True, clientchangecallback='OnIsBurningOnGround')
