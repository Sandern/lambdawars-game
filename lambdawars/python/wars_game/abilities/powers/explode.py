from core.abilities import AbilityTarget

if isserver:
    from entities import CreateEntityByName, eventqueue, variant_t, DispatchSpawn

class AbilityExplode(AbilityTarget):
    name = "explode"

    if isserver:
        def DoAbility(self):
            data = self.player.GetMouseData()
        
            bomb = CreateEntityByName("env_explosion")
            bomb.SetAbsOrigin(data.endpos)
            bomb.KeyValue("iMagnitude", "100")
            bomb.KeyValue("DamageForce", "500")
            bomb.KeyValue("fireballsprite", "sprites/zerogxplode.spr")
            bomb.KeyValue("rendermode", "5")
            DispatchSpawn(bomb)
            bomb.Activate()    
            
            value = variant_t()
            eventqueue.AddEvent(bomb, "Explode", value, 0.5, None, None)
            eventqueue.AddEvent(bomb, "kill", value, 1.0, None, None)
            
            self.Completed()
        
    infoprojtextures = [{'texture': 'decals/testeffect'}]

class AbilityExplodeHeal(AbilityExplode):
    name = 'explode_heal'


    if isserver:
        def DoAbility(self):

            bomb_heal = CreateEntityByName("env_explosion")
            bomb_heal.KeyValue("iMagnitude", "-200")
            DispatchSpawn(bomb_heal)
            bomb.Activate()