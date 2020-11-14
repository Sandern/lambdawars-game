from core.abilities import AbilityTarget

if isserver:
    from entities import CreateEntityByName, DispatchSpawn, variant_t

class AbilityExplosiveBarrel(AbilityTarget):
    name = "explosivebarrel"
    
    def StartAbility(self):
        data = self.player.GetMouseData()
        bomb = CreateEntityByName( "prop_physics" )
        bomb.KeyValue('model', 'models/props_c17/oildrum001_explosive.mdl')
        bomb.SetAbsOrigin( data.groundendpos )
        bomb.AcceptInput('Wake', None, None, variant_t(), 0)
        DispatchSpawn( bomb )      
        bomb.Activate()
        self.Completed()
        
    serveronly = True
    allowmulitpleability = True
        