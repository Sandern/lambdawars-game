from srcbase import *
from vmath import *
from core.dispatch import receiver
from core.signals import postlevelshutdown
from wars_game.attributes import AcidAttribute

from sound import CSoundEnvelopeController
from entities import entity, CBaseGrenade as BaseClass
if isserver:
    from entities import (CTakeDamageInfo, SOUND_DANGER, EFL_FORCE_CHECK_TRANSMIT, Class_T, RadiusDamage)
    from utils import UTIL_SetSize, UTIL_Remove, UTIL_DecalTrace
    from te import CEffectData, DispatchEffect
    from gameinterface import CPASAttenuationFilter
    from particles import PrecacheParticleSystem, DispatchParticleEffect
else:
    from entities import DATA_UPDATE_CREATED
    from particles import ParticleAttachment_t
    
if isserver:
    spitprecached = False

    @receiver(postlevelshutdown)
    def ResetSpitPrecached(sender, **kwargs):
        global spitprecached
        spitprecached = False

@entity('grenade_spit', networked=True)
class GrenadeSpit(BaseClass):
    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if type == DATA_UPDATE_CREATED:
                self.ParticleProp().Create("antlion_spit_trail", ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW)

    if isserver:
        def __init__(self):
            super().__init__()
            self.playsound = True
            self.hissSound = None

        def Spawn(self):
            self.Precache( )
            self.SetSolid( SOLID_BBOX )
            self.SetMoveType( MOVETYPE_FLYGRAVITY )
            self.SetSolidFlags( FSOLID_NOT_STANDABLE )

            self.SetModel( "models/spitball_large.mdl" )
            UTIL_SetSize( self, vec3_origin, vec3_origin )

            #SetUse( self.DetonateUse )
            self.SetTouch( self.GrenadeSpitTouch )
            self.SetNextThink( gpGlobals.curtime + 0.1 )

            self.damage = self.ANTLIONWORKER_SPITGRENADEDMG
            self.damageradius = self.ANTLIONWORKER_SPITGRENADERADIUS 
            self.damagetype = DMG_ACID
            self.takedamage = DAMAGE_NO
            self.health = 1

            #self.SetGravity( UTIL_ScaleForGravity( self.SPIT_GRAVITY ) ) # Changing gravity fucks up tossing code
            #self.SetFriction( 0.8 )

            self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())

            self.AddEFlags(EFL_FORCE_CHECK_TRANSMIT)

            # We're self-illuminating, so we don't take or give shadows
            self.AddEffects(EF_NOSHADOW|EF_NORECEIVESHADOW)

        def SetSpitSize(self, nSize):
            if nSize == self.SPIT_LARGE:
                self.playsound = True
                self.SetModel( "models/spitball_large.mdl" )
            elif nSize == self.SPIT_MEDIUM:
                self.playsound = True
                self.damage *= 0.5
                self.SetModel( "models/spitball_medium.mdl" )    
            elif nSize == self.SPIT_SMALL:
                self.playsound = True
                self.damage *= 0.25
                self.SetModel( "models/spitball_small.mdl" )  

        def Event_Killed(self, info):
            self.Detonate( )
        
        def GrenadeSpitTouch(self, pOther):
            """ Handle spitting """
            if pOther.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS | FSOLID_TRIGGER):
                # Some NPCs are triggers that can take damage (like antlion grubs). We should hit them.
                if ( pOther.takedamage == DAMAGE_NO ) or ( pOther.takedamage == DAMAGE_EVENTS_ONLY ):
                    return

            # Don't hit other spit
            if pOther.GetCollisionGroup() == COLLISION_GROUP_PROJECTILE:
                return

            # We want to collide with water
            pTrace = self.GetTouchTrace()

            # copy out some important things about self trace, because the first TakeDamage
            # call below may cause another trace that overwrites the one global pTrace points
            # at.
            bHitWater = ( ( pTrace.contents & CONTENTS_WATER ) != 0 )
            # pTraceEnt = pTrace.ent
            tracePlaneNormal = Vector(pTrace.plane.normal)

            if bHitWater:
                # Splash!
                data = CEffectData()
                data.flags = 0
                data.origin = pTrace.endpos
                data.normal = Vector( 0, 0, 1 )
                data.scale = 8.0

                DispatchEffect( "watersplash", data )
            else:
                # Make a splat decal
                pNewTrace = pTrace
                UTIL_DecalTrace( pNewTrace, "BeerSplash" )

            # Part normal damage, part poison damage
            # Take direct damage if hit
            # NOTE: assume that pTrace is invalidated from self line forward!
            #if pTraceEnt:
            #    pTraceEnt.TakeDamage( CTakeDamageInfo( self, self.GetThrower(), self.damage * (1.0-poisonratio), DMG_ACID ) )
            #    pTraceEnt.TakeDamage( CTakeDamageInfo( self, self.GetThrower(), self.damage * poisonratio, DMG_POISON ) )

            #CSoundEnt.InsertSound( SOUND_DANGER, self.GetAbsOrigin(), int(self.damageradius * 2.0), 0.5, self.GetThrower() )

            vecAngles = QAngle()
            VectorAngles( tracePlaneNormal, vecAngles )
            
            # FIXME
            if pOther.IsUnit() or bHitWater:
                # Do a lighter-weight effect if we just hit an unit
                DispatchParticleEffect( "antlion_spit_player", self.GetAbsOrigin(), vecAngles )
            else:
                DispatchParticleEffect( "antlion_spit", self.GetAbsOrigin(), vecAngles )
                
            self.Detonate()

        def Detonate(self):
            self.takedamage = DAMAGE_NO

            self.EmitSound( "GrenadeSpit.Hit" )	
            
            info = CTakeDamageInfo(self, self.GetThrower(), self.damage, self.damagetype)
            info.attributes = {AcidAttribute.name : AcidAttribute(self.GetThrower())}
            RadiusDamage(info, self.GetAbsOrigin(), self.damageradius, Class_T.CLASS_NONE, self.GetOwnerEntity())
            
            # Stop our hissing sound
            if self.hissSound is not None:
                CSoundEnvelopeController.GetController().SoundDestroy( self.hissSound )
                self.hissSound = None

            UTIL_Remove( self )

        def IniselfsSound(self):
            if not self.playsound:
                return

            controller = CSoundEnvelopeController.GetController()
            if self.hissSound is None:
                filter = CPASAttenuationFilter( self )
                self.hissSound = controller.SoundCreate( filter, self.entindex(), "NPC_Antlion.PoisonBall" )
                controller.Play( self.hissSound, 1.0, 100 )

        # Don't need think
        # def Think(self):
            # self.IniselfsSound()
            # if self.hissSound == None:
                # return
            
            # # Add a doppler effect to the balls as they travel
            # # Fix for mp?
            # # pPlayer = AI_GetSinglePlayer()
            # # if pPlayer != None:
                # # dir = Vector()
                # # VectorSubtract( pPlayer.GetAbsOrigin(), self.GetAbsOrigin(), dir )
                # # VectorNormalize(dir)

                # # velReceiver = DotProduct( pPlayer.GetAbsVelocity(), dir )
                # # velTransmitter = -DotProduct( self.GetAbsVelocity(), dir )
                
                # # # speed of sound == 13049in/s
                # # iPitch = 100 * ((1 - velReceiver / 13049) / (1 + velTransmitter / 13049))

                # # # clamp pitch shifts
                # # if iPitch > 250:
                    # # iPitch = 250

                # # if iPitch < 50:
                    # # iPitch = 50

                # # # Set the pitch we've calculated
                # # CSoundEnvelopeController.GetController().SoundChangePitch( self.hissSound, iPitch, 0.1 )

            # # Set us up to think again shortly
            # self.SetNextThink( gpGlobals.curtime + 0.05 )

        def Precache(self):
            global spitprecached
            if spitprecached:
                return
            spitprecached = True
            # m_nSquidSpitSprite = PrecacheModel("sprites/greenglow1.vmt")# client side spittle.

            self.PrecacheModel( "models/spitball_large.mdl" ) 
            self.PrecacheModel("models/spitball_medium.mdl") 
            self.PrecacheModel("models/spitball_small.mdl") 

            self.PrecacheScriptSound( "GrenadeSpit.Hit" )

            PrecacheParticleSystem( "antlion_spit_player" )
            PrecacheParticleSystem( "antlion_spit" )
            PrecacheParticleSystem( "antlion_spit_trail" )
            
        # Settings
        SPIT_GRAVITY = 600
        ANTLIONWORKER_SPITGRENADEDMG = 20
        ANTLIONWORKER_SPITGRENADERADIUS = 40
        SPIT_SMALL = 0
        SPIT_MEDIUM = 1
        SPIT_LARGE = 2
