from srcbase import SOLID_NONE, EF_NODRAW, SOLID_OBB, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, FL_NPC
from vmath import Vector, vec3_origin
from core.units import UnitDamageControllerInfo, UnitDamageControllerAll, CreateUnit
from particles import PrecacheParticleSystem, DispatchParticleEffect
from entities import entity
from wars_game.statuseffects import StunnedEffectInfo
from utils import UTIL_EntitiesInBox, UTIL_EntitiesInSphere

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_SetSize
    from core.ents import CTriggerArea
    
    from achievements import ACHIEVEMENT_WARS_GRENADE
    from playermgr import ListPlayersForOwnerNumber
    from wars_game.achievements import IsCommonGameMode

@entity('unit_damage_controller_all_grenade')
class UnitDamageControllerAllGrenade(UnitDamageControllerAll):
    def Event_KilledOther(self, victim, info):
        super().Event_KilledOther(victim, info)

        #if IsCommonGameMode():
        self.grenadekillcount += 1
        
        if IsCommonGameMode():
            # Grenade achievement: kill 10 with one grenade.
            if self.grenadekillcount == 10:
                for player in ListPlayersForOwnerNumber(self.GetOwnerNumber()):
                    player.AwardAchievement(ACHIEVEMENT_WARS_GRENADE)
                
    grenadekillcount = 0

class UnitGrenadeDamageInfo(UnitDamageControllerInfo):
    name = 'grenade_frag_damage'
    attributes = ['explosive']
    cls_name = 'unit_damage_controller_all_grenade'

if isserver:
    from srcbase import (DAMAGE_EVENTS_ONLY, DAMAGE_YES, DAMAGE_NO, FSOLID_NOT_STANDABLE, SOLID_BBOX,
                         kRenderGlow, kRenderFxNoDissipation, kRenderTransAdd, kRenderFxNone)
    from entities import entity, CBaseGrenade as BaseClass, CSprite, CSpriteTrail
    
    @entity('grenade_frag')
    class GrenadeFrag(BaseClass):
        def Spawn(self):
            self.Precache()
            
            self.spawntime = gpGlobals.curtime
            
            self.friendlydamage = True
            
            self.damagecontroller = CreateUnit('grenade_frag_damage', owner_number=self.GetOwnerNumber())
            self.SetThrower(self.damagecontroller)
            
            self.SetModel( self.GRENADE_MODEL )

            self.damage = self.DAMAGE
            self.damageradius = self.DMGRADIUS

            self.takedamage = DAMAGE_YES
            self.health = 1

            self.SetSize( -Vector(4,4,4), Vector(4,4,4) )
            self.SetCollisionGroup( WARS_COLLISION_GROUP_IGNORE_ALL_UNITS )
            self.CreateVPhysics()

            self.BlipSound()
            self.nextbliptime = gpGlobals.curtime + self.FRAG_GRENADE_BLIP_FREQUENCY

            self.AddSolidFlags( FSOLID_NOT_STANDABLE )

            self.punted = False

            super().Spawn()
            
        def UpdateOnRemove(self):
            if self.damagecontroller:
                self.damagecontroller.Remove()
            
            super().UpdateOnRemove()
        
        def CreateEffects(self):
            # Start up the eye glow
            self.main_glow = CSprite.SpriteCreate("sprites/redglow1.vmt", self.GetLocalOrigin(), False)

            attachment = self.LookupAttachment( "fuse" )

            if self.main_glow is not None:
                self.main_glow.FollowEntity(self)
                self.main_glow.SetAttachment(self, attachment)
                self.main_glow.SetTransparency(kRenderGlow, 255, 255, 255, 200, kRenderFxNoDissipation)
                self.main_glow.SetScale(0.2)
                self.main_glow.SetGlowProxySize(4.0)
                self.main_glow.AddFOWFlags(self.GetFOWFlags())
                self.main_glow.SetOwnerNumber(self.GetOwnerNumber())
                
            # Start up the eye trail
            self.glow_trail = CSpriteTrail.SpriteTrailCreate("sprites/bluelaser1.vmt", self.GetLocalOrigin(), False)

            if self.glow_trail is not None:
                self.glow_trail.FollowEntity(self)
                self.glow_trail.SetAttachment(self, attachment)
                self.glow_trail.SetTransparency(kRenderTransAdd, 255, 0, 0, 255, kRenderFxNone)
                self.glow_trail.SetStartWidth(8.0)
                self.glow_trail.SetEndWidth(1.0)
                self.glow_trail.SetLifeTime(0.5)
                self.glow_trail.AddFOWFlags(self.GetFOWFlags())
                self.glow_trail.SetOwnerNumber(self.GetOwnerNumber())

        def CreateVPhysics(self):
            # Create the object in the physics system
            physobj = self.VPhysicsInitNormal(SOLID_BBOX, 0, False)
            physobj.EnableDrag(False)
            return True
            
        def Precache(self):
            self.PrecacheModel( self.GRENADE_MODEL )

            self.PrecacheScriptSound("Grenade.Blip")

            self.PrecacheModel("sprites/redglow1.vmt")
            self.PrecacheModel("sprites/bluelaser1.vmt")

            super().Precache()
            
        def SetTimer(self, detonateDelay, warnDelay):
            self.detonatetime = gpGlobals.curtime + detonateDelay - 0.75
            self.warnaitime = gpGlobals.curtime + warnDelay - 0.75
            self.SetThink( self.DelayThink )
            self.SetNextThink( gpGlobals.curtime )
            
            # Always use damage controller if created
            if self.damagecontroller:
                self.SetThrower(self.damagecontroller)
                self.damagecontroller.unit_owner = self.unit_owner or self.GetOwnerEntity()

            self.CreateEffects()
            
        def DelayThink(self): 
            if gpGlobals.curtime > self.detonatetime:
                self.Detonate()
                return
            
            if gpGlobals.curtime > self.nextbliptime:
                self.BlipSound()
                
                if self.haswarnedai:
                    self.nextbliptime = gpGlobals.curtime + self.FRAG_GRENADE_BLIP_FAST_FREQUENCY
                else:
                    self.nextbliptime = gpGlobals.curtime + self.FRAG_GRENADE_BLIP_FREQUENCY

            self.SetNextThink( gpGlobals.curtime + 0.1 )

        def SetVelocity(self, velocity, angVelocity):
            physobj = self.VPhysicsGetObject()
            if physobj != None:
                physobj.AddVelocity(velocity, angVelocity)

        def OnTakeDamage(self, inputInfo):
            # Grenades are not affected by damage
            return 0
            
        def VPhysicsCollision(self, index, event):
            super().VPhysicsCollision(index, event)
            
            # Require a short minimum time before we zero the velocity on collision
            if gpGlobals.curtime - self.spawntime < 0.15:
                return
                
            physobj = self.VPhysicsGetObject()
            vel = Vector()
            ang = Vector()
            physobj.GetVelocity(vel, ang)
            vel.x = vel.y = 0.0
            physobj.SetVelocity(vel, ang)
            
        def BlipSound(self): 
            self.EmitSound( "Grenade.Blip" )
        
        def InputSetTimer(self, inputdata):
            self.SetTimer(inputdata.value.Float(), inputdata.value.Float() - self.FRAG_GRENADE_WARN_TIME)
                
        @classmethod
        def Fraggrenade_Create(cls, position, angles, velocity, ang_velocity, owner_ent, timer):
            # Don't set the owner here, or the player can't interact with grenades he's thrown
            grenade = cls.Create('grenade_frag', position, angles, owner_ent)
            
            grenade.SetTimer(timer, timer - cls.FRAG_GRENADE_WARN_TIME)
            grenade.SetVelocity(velocity, ang_velocity)
            #grenade.SetThrower(owner_ent) # Uses a custom damage controller as thrower to apply the explode attributes
            grenade.takedamage = DAMAGE_EVENTS_ONLY

            if owner_ent:
                grenade.SetOwnerNumber(owner_ent.GetOwnerNumber())
                grenade.unit_owner = owner_ent
                grenade.AddFOWFlags(owner_ent.GetFOWFlags())

            return grenade

        main_glow = None
        glow_trail = None
        unit_owner = None
            
        haswarnedai = False
        nextbliptime = 0.0
        damagecontroller = None
        spawntime = 0.0
        
        GRENADE_MODEL = "models/Weapons/w_grenade.mdl"
        
        DAMAGE = 200.0
        DMGRADIUS = 320.0
    
        FRAG_GRENADE_BLIP_FREQUENCY = 1.0
        FRAG_GRENADE_BLIP_FAST_FREQUENCY = 0.3

        FRAG_GRENADE_GRACE_TIME_AFTER_PICKUP = 1.5
        FRAG_GRENADE_WARN_TIME = 1.5

        GRENADE_COEFFICIENT_OF_RESTITUTION = 0.2

    @entity('grenade_smoke')
    class GrenadeSmoke(GrenadeFrag):
        def Precache(self):
            super().Precache()
                
            self.PrecacheScriptSound("ability_smoke_grenade")
            PrecacheParticleSystem(self.smokeparticle)
        
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
                
            if self.fowblocker:
                self.fowblocker.Remove()
                self.fowblocker = None
        
        def Explode(self, trace, bitsdamagetype):
            if self.exploded:
                return
            self.exploded = True
                
            self.EmitSound('ability_smoke_grenade')
                
            origin = self.GetAbsOrigin()
            
            self.SetThink(self.SUB_Remove, gpGlobals.curtime + self.smokeduration, 'SmokeRemoveThink')
            self.SetTouch(None)
            self.SetSolid(SOLID_NONE)
                
            self.AddEffects(EF_NODRAW)
            self.SetAbsVelocity(vec3_origin)
            self.takedamage = DAMAGE_NO
                
            fowblocker = CreateEntityByName('fow_blocker')
            if fowblocker:
                radius = 220.0
                fowblocker.SetName('smoke_fow_blocker')
                fowblocker.SetAbsOrigin(origin)
                DispatchSpawn(fowblocker)
                mins = -Vector(radius, radius, 0)
                maxs = Vector(radius, radius, 256)
                UTIL_SetSize(fowblocker, mins, maxs)
                fowblocker.SetSolid(SOLID_OBB)
                fowblocker.CollisionProp().UpdatePartition()
                fowblocker.PhysicsTouchTriggers()
                fowblocker.Activate()
                    
                DispatchParticleEffect(self.smokeparticle, origin, self.GetAbsAngles(), fowblocker)
                    
                self.fowblocker = fowblocker
            
        smokeparticle = 'pg_smoke_grenade'
        fowblocker = None
        smokeduration = 18.0
        exploded = False
        GRENADE_MODEL = "models/Weapons/w_flashbang_combine.mdl"

    @entity('grenade_stun')
    class GrenadeStun(GrenadeFrag):
        def Precache(self):
            super().Precache()

            self.PrecacheScriptSound('build_comb_mturret_explode')
            self.PrecacheScriptSound('StunGrenade.Detonate')
            PrecacheParticleSystem('particle_stun_frag_BASE')


        def Explode(self, trace, bitsdamagetype):
            if self.exploded:
                return
            self.exploded = True
            origin = self.GetAbsOrigin()

            self.SetThink(self.SUB_Remove, gpGlobals.curtime, 'SmokeRemoveThink')
            self.SetTouch(None)
            self.SetSolid(SOLID_NONE)
            DispatchParticleEffect("particle_stun_frag_BASE", origin, self.GetAbsAngles())
            #self.EmitSound('build_comb_mturret_explode')
            self.EmitSound('StunGrenade.Detonate')

            self.AddEffects(EF_NODRAW)
            self.SetAbsVelocity(vec3_origin)
            self.takedamage = DAMAGE_NO
            stunduration = 5.0
            enemies = UTIL_EntitiesInSphere(256, self.GetAbsOrigin(), self.damageradius, FL_NPC)

            for enemy in enemies:
                #print("IsUnit", enemy.IsUnit(), "IsAlive", enemy.IsAlive(), "enemy", enemy)
                if enemy.IsUnit() and enemy.IsAlive():
                    #print("IsUnit", enemy.IsUnit(), "IsAlive", enemy.IsAlive(), "enemy", enemy)

                    StunnedEffectInfo.CreateAndApply(enemy, attacker=self, duration=stunduration)
        def SetTimer(self, detonateDelay, warnDelay):
            self.detonatetime = gpGlobals.curtime + detonateDelay - 1.2
            self.warnaitime = gpGlobals.curtime + warnDelay - 1.2
            self.SetThink( self.DelayThink )
            self.SetNextThink( gpGlobals.curtime )
            
            # Always use damage controller if created
            if self.damagecontroller:
                self.SetThrower(self.damagecontroller)

            self.CreateEffects()

        def CreateEffects(self):
            # Start up the eye glow
            self.main_glow = CSprite.SpriteCreate("sprites/blueflare1.vmt", self.GetLocalOrigin(), False)

            attachment = self.LookupAttachment( "fuse" )

            if self.main_glow is not None:
                self.main_glow.FollowEntity(self)
                self.main_glow.SetAttachment(self, attachment)
                self.main_glow.SetTransparency(kRenderGlow, 255, 255, 255, 200, kRenderFxNoDissipation)
                self.main_glow.SetScale(0.2)
                self.main_glow.SetGlowProxySize(4.0)
                self.main_glow.AddFOWFlags(self.GetFOWFlags())
                self.main_glow.SetOwnerNumber(self.GetOwnerNumber())

            # Start up the eye trail
            self.glow_trail = CSpriteTrail.SpriteTrailCreate("sprites/bluelaser1.vmt", self.GetLocalOrigin(), False)

            if self.glow_trail is not None:
                self.glow_trail.FollowEntity(self)
                self.glow_trail.SetAttachment(self, attachment)
                self.glow_trail.SetTransparency(kRenderTransAdd, 225, 225, 225, 255, kRenderFxNone)
                self.glow_trail.SetStartWidth(8.0)
                self.glow_trail.SetEndWidth(1.0)
                self.glow_trail.SetLifeTime(0.5)
                self.glow_trail.AddFOWFlags(self.GetFOWFlags())
                self.glow_trail.SetOwnerNumber(self.GetOwnerNumber())
        exploded = False

    '''@entity('grenade_heal')
    class GrenadeHeal(GrenadeFrag):
        if isserver:
            def Precache(self):
                pass

            def Explode(self, trace, bitsdamagetype):
                if self.exploded:
                    return
                self.exploded = True
                origin = self.GetAbsOrigin()

                self.SetThink(self.SUB_Remove, gpGlobals.curtime, 'SmokeRemoveThink')
                self.SetTouch(None)
                self.SetSolid(SOLID_NONE)

                self.AddEffects(EF_NODRAW)
                self.SetAbsVelocity(vec3_origin)
                self.takedamage = DAMAGE_NO
                healduration = 10.0
                friends = UTIL_EntitiesInSphere(300, self.GetAbsOrigin(), self.damageradius, FL_NPC)

                for f in friends:
                    if f.IsUnit() and f.IsAlive():
                        pass


        exploded = False'''

    @entity('trigger_heal_explosion')
    class HealArea(CTriggerArea):
        def Precache(self):
            super().Precache()
            # PrecacheParticleSystem('pg_heal')

        def Spawn(self):
            self.Precache()

            super().Spawn()

            self.SetThink(self.HealThink, gpGlobals.curtime, 'HealThink')

        def Heal(self, unit, heal):
            """
            @type unit: core.units.base.UnitBase
            @type heal: float
            """
            # Must not be mechanic
            if 'mechanic' in unit.attributes:
                return

            if unit.health < unit.maxhealth:
                self.healing = True
                unit.health += min(heal, (unit.maxhealth - unit.health))
                # DispatchParticleEffect("pg_heal", PATTACH_ABSORIGIN_FOLLOW, entity)
                if hasattr(unit, 'EFFECT_DOHEAL'):
                    unit.DoAnimation(unit.EFFECT_DOHEAL)

        def HealThink(self):

            dt = gpGlobals.curtime - self.GetLastThink('HealThink')
            heal = int(round(dt * self.healrate))

            self.healing = False

            for entity in self.touchingents:
                if not entity:
                    continue

                if not entity.IsUnit() or entity.isbuilding or entity.IRelationType(self) != D_LI:
                    continue

                self.Heal(entity, heal)

            self.SetNextThink(gpGlobals.curtime + 0.5, 'HealThink')

        #: Heal rate per second of this building
        healrate = 4
        #: Whether or not the area was healing units last think
        healing = False