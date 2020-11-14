from srcbase import *
from vmath import *
import random

# Imports
from sound import CSoundEnvelopeController, PITCH_NORM
from entities import entity
if isserver:
    from entities import (IMouse, CBaseGrenade as BaseClass,
                          CSoundEnt, SOUND_DANGER, SOUNDENT_CHANNEL_REPEATED_DANGER)
    import utils
    from te import CEffectData, DispatchEffect
    from gameinterface import CReliableBroadcastRecipientFilter
else:
    from entities import IMouse, C_BaseGrenade as BaseClass 
    
# Helicopter grenade entity
@entity('grenade_helicopter', networked=True)
class GrenadeHelicopter(BaseClass, IMouse):
    def __init__(self):
        BaseClass.__init__(self)
        IMouse.__init__(self)    
        
    def GetIMouse(self):
        return self
        
    def GetCursor(self):
        return 14
        
    def UpdateOnRemove(self):
        super(GrenadeHelicopter, self).UpdateOnRemove()
        
    # Server only methods ( or only implemented on the server )
    if isserver:
        def OnClickLeftPressed(self, player):
            """ On left pressed add velocity """
            data = player.GetMouseDataLeftPressed()
            dir = data.normal
            dir.Negate()
            physicsObject = self.VPhysicsGetObject()            
            physicsObject.AddVelocity( dir * 1000.0, None )            
    
        def Precache(self):
            super(GrenadeHelicopter, self).Precache()
        
            self.PrecacheModel( self.GRENADE_HELICOPTER_MODEL )  
            
            self.PrecacheScriptSound( "ReallyLoudSpark" )
            self.PrecacheScriptSound( "NPC_AttackHelicopterGrenade.Ping" )
    
        def Spawn(self):
            self.Precache()
            
            self.blinkerAtTop = False

            # point sized, solid, bouncing
            self.SetCollisionGroup( Collision_Group_t.COLLISION_GROUP_PROJECTILE )
            self.SetModel( self.GRENADE_HELICOPTER_MODEL )
            
            physicsObject = self.VPhysicsInitNormal( SolidType_t.SOLID_VPHYSICS, self.GetSolidFlags(), False )
            self.SetMoveType( MoveType_t.MOVETYPE_VPHYSICS )

            vecAbsVelocity = self.GetAbsVelocity()
            physicsObject.AddVelocity( vecAbsVelocity, None )
            
            # contact grenades arc lower
            angles = QAngle()
            VectorAngles(self.GetAbsVelocity(), angles)
            self.SetLocalAngles( angles )
            
            # Tumble in air
            vecAngVel = QAngle( random.uniform ( -100, -500 ), 0, 0 )
            self.SetLocalAngularVelocity( vecAngVel )
            
            # Explode on contact
            self.SetTouch( self.ExplodeConcussion )

            # use a lower gravity for grenades to make them easier to see
            self.SetGravity( utils.UTIL_ScaleForGravity( 400 ) )
            
            self.warnsound = None
            
            self.SetThink( self.AnimateThink, gpGlobals.curtime, "AnimateThink" )
            
        def UpdateOnRemove(self):
            if self.warnsound:
                controller = CSoundEnvelopeController.GetController()
                controller.SoundDestroy( self.warnsound )
            super(GrenadeHelicopter, self).UpdateOnRemove()
            
        def AnimateThink(self):
            self.StudioFrameAdvance()
            self.SetThink( self.AnimateThink, gpGlobals.curtime + 0.1, "AnimateThink" )
            
        def BecomeActive(self):
            if self.active:
                return
                
            self.active = True
        
            self.SetThink( self.ExplodeThink, 0, "ExplodeThink" )   
            self.SetNextThink( gpGlobals.curtime + self.BOMB_LIFETIME, "ExplodeThink" )
            
            self.SetThink( self.RampSoundThink, gpGlobals.curtime + self.BOMB_LIFETIME - self.BOMB_RAMP_SOUND_TIME, "RampSoundThink" );

            controller = CSoundEnvelopeController.GetController()
            filter = CReliableBroadcastRecipientFilter()
            self.warnsound = controller.SoundCreate( filter, self.entindex(), "NPC_AttackHelicopterGrenade.Ping" )
            controller.Play( self.warnsound, 1.0, PITCH_NORM )

            self.SetThink( self.WarningBlinkerThink, gpGlobals.curtime, "WarningBlinkerThink" )
            
            self.blinkFastTime = gpGlobals.curtime + self.BOMB_LIFETIME / 2.0

        def WarningBlinkerThink(self):
            # Just flip it to the other attachment.
            if self.blinkerAtTop:
                self.skin = self.SKIN_REGULAR           
                self.blinkerAtTop = False
            else:
                self.skin = self.SKIN_DUD
                self.blinkerAtTop = True

            # Frighten people
            #CSoundEnt.InsertSound ( SOUND_DANGER, self.WorldSpaceCenter(), 4096, 0.2, self, SOUNDENT_CHANNEL_REPEATED_DANGER )

            if gpGlobals.curtime >= self.blinkFastTime:
                self.SetThink( self.WarningBlinkerThink, gpGlobals.curtime + 0.1, "WarningBlinkerThink" )
            else:
                self.SetThink( self.WarningBlinkerThink, gpGlobals.curtime + 0.2, "WarningBlinkerThink" )
            
        def RampSoundThink(self):
            if self.warnsound:
                controller = CSoundEnvelopeController.GetController()
                controller.SoundChangePitch( self.warnsound, 140, self.BOMB_RAMP_SOUND_TIME )

            self.SetThink( None, gpGlobals.curtime, "RampSoundThink" )
            
        def VPhysicsCollision(self, index, event):
            """ If we hit something, start the timer """
            super(GrenadeHelicopter, self).VPhysicsCollision( index, event )
            self.BecomeActive()

            #impactSpeed = pEvent.preVelocity.Length()
            #if impactSpeed > 400.0 && pEvent.pEntities[ 1 ].IsWorld():
            #    self.EmitSound( "NPC_AttackHelicopterGrenade.HardImpact" )     
            
        def DoExplosion(self, vecOrigin, vecVelocity):
            """ Pow! """
            owner = self
            if self.GetOwnerEntity():
                owner = self.GetOwnerEntity()
            utils.ExplosionCreate( self.GetAbsOrigin(), self.GetAbsAngles(), owner, self.DAMAGE, 
                self.RADIUS, (utils.SF_ENVEXPLOSION_NOSPARKS|utils.SF_ENVEXPLOSION_NODLIGHTS|utils.SF_ENVEXPLOSION_NODECAL|utils.SF_ENVEXPLOSION_NOFIREBALL|utils.SF_ENVEXPLOSION_NOPARTICLES), 
                self.FORCE, self )

            if self.SHAKE_AMPLITUDE:
                utils.UTIL_ScreenShake( self.GetAbsOrigin(), self.SHAKE_AMPLITUDE, 150.0, 1.0, self.SHAKE_RADIUS, utils.ShakeCommand_t.SHAKE_START )

            data = CEffectData()
            # If we're under water do a water explosion
            if self.GetWaterLevel() != 0 and (self.GetWaterType() & CONTENTS_WATER):
                data.origin = self.WorldSpaceCenter()
                data.magnitude = 128
                data.scale = 128
                data.flags = 0
                DispatchEffect( "WaterSurfaceExplosion", data )
            else:
                # Otherwise do a normal explosion
                data.origin = self.GetAbsOrigin()
                DispatchEffect( "HelicopterMegaBomb", data )

            utils.UTIL_Remove( self )
        
        def ExplodeThink(self):
            vecVelocity = Vector()
            self.GetVelocity( vecVelocity, None )
            self.DoExplosion( self.GetAbsOrigin(), vecVelocity )       
            
        def ExplodeConcussion(self, other):
            if other.IsSolid():
                return

            if self.explodeOnContact == False:
                if other.IsWorld():
                    return

            vecVelocity = Vector()
            self.GetVelocity( vecVelocity, None )
            self.DoExplosion( self.GetAbsOrigin(), vecVelocity )

    # Static class data
    GRENADE_HELICOPTER_MODEL        = "models/combine_helicopter/helicopter_bomb01.mdl"    
    BOMB_LIFETIME                   = 10.0 #2.5
    BOMB_RAMP_SOUND_TIME            = 1.0
    SHAKE_AMPLITUDE                 = 25.0
    SHAKE_RADIUS                    = 512.0
    DAMAGE                          = 25
    RADIUS                          = 275
    FORCE                           = 55000.0
    SKIN_REGULAR                    = 0
    SKIN_DUD                        = 1
    
    explodeOnContact                = False
    active                          = False
