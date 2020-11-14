from vmath import *
from core.buildings import UnitBaseAutoTurret, WarsTurretInfo
import random
from entities import entity
if isserver:
    from ..ents.grenade_spit import GrenadeSpit
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_PredictedPosition
from gameinterface import *
    
sv_gravity = ConVarRef('sv_gravity')

@entity('build_spitturret')
class SpitTurret(UnitBaseAutoTurret):
    pitchturnspeed = 2000.0
    yawturnspeed = 2000.0
    firerate = 0.1
    
    def Fire(self, bulletcount, attacker=None, ingorespread=False):
        speed = 1000.0
        
        vTarget = Vector()
        UTIL_PredictedPosition( self.enemy, 0.5, vTarget ) 
        #vTarget = self.enemy.GetAbsOrigin()
    
        vSpitPos = self.EyePosition() + Vector(0, 0, 140.0)
        vecToTarget = ( vTarget  - vSpitPos )
        time = vecToTarget.Length() / speed
        vecToTarget.z += sv_gravity.GetFloat() * time * 0.5
        speed = VectorNormalize( vecToTarget )

        for i in range(0, 3):            
            grenade = CreateEntityByName("grenade_spit")
            grenade.SetAbsOrigin(vSpitPos)
            grenade.SetAbsAngles(vec3_angle)
            DispatchSpawn( grenade )
            grenade.Get().damage = 100.0
            grenade.Get().dmgradius = 200.0
            grenade.SetThrower( self )
            grenade.SetOwnerEntity( self )
            grenade.SetOwnerNumber( self.GetOwnerNumber() )
                                
            grenade.SetAbsVelocity( vecToTarget * speed )
            if i == 0:
                grenade.SetSpitSize( GrenadeSpit.SPIT_LARGE )
            else:
                grenade.SetSpitSize( random.randint( GrenadeSpit.SPIT_SMALL, GrenadeSpit.SPIT_MEDIUM ) )
                
            # Tumble through the air
            grenade.SetLocalAngularVelocity(
                QAngle( random.uniform( -250, -500 ),
                        random.uniform( -250, -500 ),
                        random.uniform( -250, -500 ) ) )

class SpitTurretInfo(WarsTurretInfo):
    name = "build_spitturret"
    cls_name = "build_spitturret"
    image_name = "vgui/abilities/ability_rebelhq.vmt"
    health = 1000
    modelname = 'models/props_wasteland/medbridge_post01.mdl'
