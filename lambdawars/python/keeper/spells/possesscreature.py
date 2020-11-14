from core.abilities import AbilityTarget
        
class AbilityControlUnit(AbilityTarget):
    name = "possesscreature"
    displayname = "Possess Creature"
    description = "Directly control an unit you own."
    requireunits = False
    
    if isserver:
        def StartAbility(self):
            if self.player.GetControlledUnit():
                self.player.SetControlledUnit(None)
                self.Completed()
            else:
                self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), 'Spells.PossessCreature')
        
        def DoAbility(self):
            ent = self.player.GetMouseData().ent
            if self.player.GetOwnerNumber() != ent.GetOwnerNumber() or not ent.IsUnit():
                self.Cancel()
                return
            self.player.SetControlledUnit(ent)
            self.Completed()    
        