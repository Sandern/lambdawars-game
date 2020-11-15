from srcbase import *
from vmath import *
from core.dispatch import receiver
from core.signals import postlevelshutdown
from core.units import UnitDamageControllerInfo, UnitDamageControllerAll, CreateUnit
from wars_game.attributes import ExplosiveAttribute
from sound import CSoundEnvelopeController
from entities import entity, CBaseGrenade as BaseClass
from playermgr import dbplayers
if isserver:
    from entities import (CTakeDamageInfo, SOUND_DANGER, EFL_FORCE_CHECK_TRANSMIT, Class_T, RadiusDamage, SmokeTrail, CSpriteTrail)
    from utils import UTIL_SetSize, UTIL_Remove, UTIL_DecalTrace, ExplosionCreate
    from te import CEffectData, DispatchEffect
    from gameinterface import CPASAttenuationFilter
    from particles import PrecacheParticleSystem, DispatchParticleEffect
else:
    from entities import DATA_UPDATE_CREATED
    from particles import ParticleAttachment_t
    
class UnitDamageControllerMortarSynthInfo(UnitDamageControllerInfo):
    name = 'unit_damage_controller'
    attributes = ['explosive']
@entity('grenade_energy', networked=True)
class GrenadeEnergy(BaseClass):

    if isserver:
        def __init__(self):
            super().__init__()
            self.playsound = True
            self.hissSound = None

        def Precache(self):
            self.PrecacheModel( "models/Weapons/w_Grenade.mdl" )

            self.PrecacheScriptSound( "BaseGrenade.Explode" )
            self.PrecacheScriptSound( "BaseExplosionEffect.Sound" )

        def Spawn(self):
            self.Precache( )
            self.SetSolid( SOLID_BBOX )
            self.SetMoveType( MOVETYPE_FLYGRAVITY )
            self.SetSolidFlags( FSOLID_NOT_STANDABLE )

            self.SetModel( "models/Weapons/w_Grenade.mdl" )
            UTIL_SetSize( self, vec3_origin, vec3_origin )
            #PrecacheParticleSystem( "explosion_turret_break" )
            PrecacheParticleSystem( "RPGShotDown" )

            self.SetTouch( self.GrenadeSpitTouch )
            self.SetNextThink( gpGlobals.curtime + 0.1 )

            self.damage = self.ANTLIONWORKER_SPITGRENADEDMG
            self.damageradius = self.ANTLIONWORKER_SPITGRENADERADIUS 
            self.damagetype = DMG_BLAST
            self.takedamage = DAMAGE_NO
            self.health = 1
            # Smoke trail.
            self.CreateSmokeTrail()

            self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())

            self.AddEFlags(EFL_FORCE_CHECK_TRANSMIT)
        def UpdateOnRemove(self):
            if self.damagecontroller:
                self.damagecontroller.Remove()
            
            super().UpdateOnRemove()

        def Event_Killed(self, info):
            self.Detonate( )
        
        def GrenadeSpitTouch(self, pOther):
            """ Handle spitting """
            if ( pOther.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS | FSOLID_TRIGGER) ):
                if ( pOther.takedamage == DAMAGE_NO ) or ( pOther.takedamage == DAMAGE_EVENTS_ONLY ):
                    return

            # Don't hit other spit
            if ( pOther.GetCollisionGroup() == COLLISION_GROUP_PROJECTILE ):
                return

            self.Detonate()

        def Detonate(self):
            origin = self.GetAbsOrigin()
            self.takedamage = DAMAGE_NO
            self.damagecontroller = CreateUnit('unit_damage_controller', owner_number=self.GetOwnerNumber())
            if not self.GetThrower():
                self.SetThrower(self.damagecontroller)

            ExplosionCreate(origin, self.GetAbsAngles(), self, 0, 150, True )
            info = CTakeDamageInfo(self, self.GetThrower(), self.damage, self.damagetype)
            info.attributes = {ExplosiveAttribute.name : ExplosiveAttribute(self.GetThrower())}
            RadiusDamage(info, origin, self.damageradius, Class_T.CLASS_NONE, self.GetOwnerEntity())

            if self.smoketrail:
                self.smoketrail.SetLifetime(0.1)
                self.smoketrail = None
            if self.glow_trail:
                self.glow_trail = None
            if self.glow_trail_1:
                self.glow_trail_1 = None
            if self.glow_trail_2:
                self.glow_trail_2 = None
            UTIL_Remove( self )
        def CreateSmokeTrail(self):
            if self.glow_trail:
                return
            self.teamcolor = dbplayers[self.GetOwnerNumber()].color
            attachment = self.LookupAttachment( "fuse" )
            self.glow_trail = CSpriteTrail.SpriteTrailCreate("sprites/bluelaser1.vmt", self.GetLocalOrigin(), False)

            if self.glow_trail is not None:
                self.glow_trail.FollowEntity(self)
                self.glow_trail.SetAttachment(self, attachment)
                self.glow_trail.SetTransparency(kRenderTransAdd, self.teamcolor[0], self.teamcolor[1], self.teamcolor[2], 255, kRenderFxNone)
                self.glow_trail.SetStartWidth(16.0)
                self.glow_trail.SetEndWidth(1.0)
                self.glow_trail.SetLifeTime(0.5)
                self.glow_trail.AddFOWFlags(self.GetFOWFlags())
                self.glow_trail.SetOwnerNumber(self.GetOwnerNumber())
            if self.glow_trail_1:
                return
            self.glow_trail_1 = CSpriteTrail.SpriteTrailCreate("sprites/flare1.vmt", self.GetLocalOrigin(), False) #заменяешь там где sprites/flare1.vmt
            if self.glow_trail_1 is not None:
                self.glow_trail_1.FollowEntity(self)
                self.glow_trail_1.SetAttachment(self, attachment)
                self.glow_trail_1.SetTransparency(kRenderTransAdd, self.teamcolor[0], self.teamcolor[1], self.teamcolor[2], 255, kRenderFxNone)
                self.glow_trail_1.SetStartWidth(80.0)
                self.glow_trail_1.SetEndWidth(0.5)
                self.glow_trail_1.SetLifeTime(0.5)
                self.glow_trail_1.AddFOWFlags(self.GetFOWFlags())
                self.glow_trail_1.SetOwnerNumber(self.GetOwnerNumber())
            if self.glow_trail_2:
                return
            self.glow_trail_2 = CSpriteTrail.SpriteTrailCreate("sprites/animglow01.vmt", self.GetLocalOrigin(), False)
            if self.glow_trail_2 is not None:
                self.glow_trail_2.FollowEntity(self)
                self.glow_trail_2.SetAttachment(self, attachment)
                self.glow_trail_2.SetTransparency(kRenderTransAdd, self.teamcolor[0], self.teamcolor[1], self.teamcolor[2], 255, kRenderFxNone) 
                self.glow_trail_2.SetStartWidth(80.0) 
                self.glow_trail_2.SetEndWidth(20.0) 
                self.glow_trail_2.SetLifeTime(0.5)
                self.glow_trail_2.AddFOWFlags(self.GetFOWFlags())
                self.glow_trail_2.SetOwnerNumber(self.GetOwnerNumber())
        teamcolor = (0, 0, 0)
        smoketrail = None
        glow_trail = None
        glow_trail_1 = None
        glow_trail_2 = None
        damagecontroller = None
        # Settings
        ANTLIONWORKER_SPITGRENADEDMG = 500
        ANTLIONWORKER_SPITGRENADERADIUS = 150