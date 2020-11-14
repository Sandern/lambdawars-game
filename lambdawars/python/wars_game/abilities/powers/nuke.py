from core.abilities import AbilityTarget
from vmath import *
from srcbase import *

if isserver:
    from entities import *
    from utils import *
    from particles import *
    
# Create a small nuke entity
if isserver:
    @entity('nuke')
    class Nuke(CBaseAnimating):
        def Precache(self):
            super().Precache()
            
            self.PrecacheModel( self.NUKE_MODEL )  
            
            self.PrecacheScriptSound('ep02_outro.RocketTakeOffBlast')
            self.PrecacheScriptSound('d3_citadel.timestop_explosion_2')            
            
            PrecacheParticleSystem("big_explosion")
            PrecacheParticleSystem("choreo_launch_rocket_jet")
        
        def Spawn(self):
            self.Precache()
        
            super().Spawn()
            
            # point sized, solid, bouncing
            self.SetCollisionGroup( Collision_Group_t.COLLISION_GROUP_PROJECTILE )
            self.SetModel( self.NUKE_MODEL )
            
            physicsObject = self.VPhysicsInitNormal( SolidType_t.SOLID_VPHYSICS, self.GetSolidFlags(), False )
            self.SetMoveType( MoveType_t.MOVETYPE_VPHYSICS )
            
            # Create some smoke and make some sound
            DispatchParticleEffect("choreo_launch_rocket_jet", ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW, self)
            self.EmitSound("ep02_outro.RocketTakeOffBlast", 0.0)

        def VPhysicsCollision(self, index, event):
            """ If we hit something, BOOOOOM """
            super(Nuke, self).VPhysicsCollision(index, event)
            
            self.Explode()
            
        def Explode(self):
            DispatchParticleEffect("big_explosion", self.GetAbsOrigin(), QAngle(0, 0, 0))
            self.EmitSound("d3_citadel.timestop_explosion_2", 0.0)
            flags = SF_ENVEXPLOSION_NOFIREBALL|SF_ENVEXPLOSION_NOFIREBALLSMOKE
            ExplosionCreate( self.GetAbsOrigin(), QAngle(), self, 100000, 2500, flags, 10000.0, self) #, -1, None, Class_T.CLASS_NONE )  

            # NOTE: Do not directly remove here
            g_EventQueue.AddEvent(self, 'kill', 0.0, self, self)
            
        NUKE_MODEL      = 'models/props_silo/rocket.mdl'

class AbilityNuke(AbilityTarget):
    # Info
    name = "nuke"
    
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.player.GetMouseData()
            
            # Spawn a nuke
            tr = trace_t()
            UTIL_TraceLine( data.endpos, data.endpos + Vector(0, 0, 1) * 2048.0, MASK_SHOT, None, Collision_Group_t.COLLISION_GROUP_NONE, tr)
            nuke = CreateEntityByName( "nuke" )
            nuke.SetAbsOrigin( tr.endpos )
            nuke.SetAbsVelocity( Vector(0, 0, -1) * 10000.0 )
            nuke.SetAbsAngles( QAngle(180, 0, 0 ) )
            nuke.SetOwnerNumber(self.player.GetOwnerNumber())
            DispatchSpawn( nuke )
            nuke.Activate()       
            
            self.Completed()
        
    infoprojtextures = [
        {'texture' : 'decals/nuke',
         'mins' : Vector(-512, -512, 0),
         'maxs' : Vector(512, 512, 128)}]
        