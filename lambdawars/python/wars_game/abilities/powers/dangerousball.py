from srcbase import *
from vmath import *
from core.abilities import AbilityMouseOverride
from entities import entity
from particles import PATTACH_ABSORIGIN_FOLLOW

if isserver:
    from entities import CreateEntityByName, DispatchSpawn, CBaseAnimating as BaseClass, FOWFLAG_UNITS_MASK, CTakeDamageInfo
    from particles import PrecacheParticleSystem
else:
    from entities import C_BaseAnimating as BaseClass, DataUpdateType_t


@entity('dangerousball', networked=True)
class DangerousBall(BaseClass):
    def ShouldDraw(self):
        return False    # Don't draw our model (we only use it for the physics)
        
    def OnDataChanged(self, type):
        super().OnDataChanged(type)
        
        if type == DataUpdateType_t.DATA_UPDATE_CREATED:
            self.particlefx = self.ParticleProp().Create(self.PARTICLES_NAME, PATTACH_ABSORIGIN_FOLLOW)
        
    # The following methods are only implemented on the server
    if isserver:
        def __init__(self):
            super().__init__()
        
            # This entity updates the fog of war 
            self.viewdistance = 1024.0
                
        def Precache(self):
            super().Precache()
        
            # Preache our model (containing the physic model) and the particle system
            self.PrecacheModel( self.DANGEROUSBALL_MODEL )  
            PrecacheParticleSystem(self.PARTICLES_NAME)

        def Spawn(self):
            self.Precache()
            
            # point sized, solid, bouncing
            self.SetCollisionGroup(Collision_Group_t.COLLISION_GROUP_PROJECTILE)
            self.SetModel(self.DANGEROUSBALL_MODEL)
            self.SetMoveType(MoveType_t.MOVETYPE_VPHYSICS)
            self.SetSolidFlags(FSOLID_TRIGGER)
            self.SetTouch(self.DissolveTouch)   
            self.AddEFlags(EF_NOSHADOW)
           
            # Init physics
            physicsObject = self.VPhysicsInitNormal(SolidType_t.SOLID_VPHYSICS, self.GetSolidFlags(), False)
            vecAbsVelocity = self.GetAbsVelocity()
            physicsObject.AddVelocity(vecAbsVelocity, None)
            
            self.AddFOWFlags(FOWFLAG_UNITS_MASK)
            
        def DissolveTouch(self, touchent):
            """ Kill everything we touch """
            info = CTakeDamageInfo(None, None, 99999, DMG_DISSOLVE|DMG_SHOCK)
            touchent.TakeDamage(info)
            #touchent.Dissolve( "", gpGlobals.curtime, False, ENTITY_DISSOLVE_NORMAL )
            
        def VPhysicsCollision(self, index, event):
            """ If we hit something, bump up """
            super().VPhysicsCollision( index, event )
            
            self.VPhysicsGetObject().AddVelocity( Vector(0,0,1) * 200.0, None ) 
            
    DANGEROUSBALL_MODEL = "models/combine_helicopter/helicopter_bomb01.mdl"
    PARTICLES_NAME = "dangerousball"


# Spawns a dangerous ball
class AbilityDangerousBall(AbilityMouseOverride):
    # Info
    name = "dangerousball"
    description = "A dangerous ball"
    
    # Ability
    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()
            
            PrecacheParticleSystem(DangerousBall.PARTICLES_NAME)
        
        def Init(self):
            super().Init()

            # Spawn the ball from the player origin in the direction the mouse is pointing
            data = self.player.GetMouseData()
            playerpos = self.player.GetAbsOrigin() + self.player.GetCameraOffset()
            vecShootDir = data.endpos - playerpos
            VectorNormalize(vecShootDir)
            ball = CreateEntityByName( "dangerousball" )
            if not ball:
                self.Completed()
                return
            ball.SetAbsOrigin(playerpos)
            ball.SetAbsVelocity(vecShootDir * 10000.0)
            ball.SetOwnerNumber(self.player.GetOwnerNumber())
            DispatchSpawn(ball)      
            self.ball = ball.GetHandle()  
        
        def Cleanup(self):
            super().Cleanup()
            
            # Remove the ball
            if self.ball:
                self.ball.Remove()
                
        lastmousesample = None
        ticksignal = 0.1
        def Tick(self):
            # Clear this ability in case the ball entity got killed for some reason
            if not self.ball:
                self.Completed()
                return
                
            if self.player.IsLeftPressed():
                if self.lastmousesample:
                    # Add velocity in the direction the mouse is being dragged
                    # Moving faster will add more velocity
                    data = self.player.GetMouseData()
                    dir = data.endpos - self.lastmousesample.endpos
                    dist = VectorNormalize( dir )
                    dir.z = 0.0
                    self.ball.VPhysicsGetObject().AddVelocity(dir * dist * 1.5, None) 
                    
                    # If additionally right is pressed an upward velocity is added to the ball
                    if self.player.IsRightPressed():
                        self.ball.VPhysicsGetObject().AddVelocity(Vector(0,0,1) * 125.0, None) 
                    
                # Store mouse sample for the next update
                self.lastmousesample = self.player.GetMouseData() 
            
        def OnLeftMouseButtonReleased(self):
            """ Clear current mouse sample """
            self.lastmousesample = None
            return True
            
        def OnRightMouseButtonPressed(self): 
            """ Clear this ability when right is pressed """
            if self.player.IsLeftPressed():
                return True
            self.Completed()
            return True
            
    allowmulitpleability = True
