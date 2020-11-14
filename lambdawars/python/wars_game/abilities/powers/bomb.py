from vmath import VectorNormalize
from core.abilities import AbilityTarget

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    
# Spawns a helicopter bomb
class AbilityBomb(AbilityTarget):
    name = "bomb"

    if isserver:
        def DoAbility(self):
            data = self.mousedata
        
            vecShootDir = data.endpos - (self.player.GetAbsOrigin() + self.player.GetCameraOffset())
            VectorNormalize( vecShootDir )
            bomb = CreateEntityByName( "grenade_helicopter" )
            bomb.SetAbsOrigin( self.player.GetAbsOrigin() + self.player.GetCameraOffset() )
            bomb.SetAbsVelocity( vecShootDir * 10000.0 )
            DispatchSpawn( bomb )      

            self.Completed()
        
    infoprojtextures = [{'texture' : 'decals/testeffect'}]
        