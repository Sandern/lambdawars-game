from core.abilities import AbilityTarget
        
class AbilityControlUnit(AbilityTarget):
    name = "controlunit"
    displayname = "Control Unit"
    description = "Directly control an unit you own."

    if isserver:
        def StartAbility(self):
            if self.player.GetControlledUnit():
                self.player.SetControlledUnit(None)
                self.Completed()
        
        def DoAbility(self):
            ent = self.player.GetMouseData().ent
            if self.player.GetOwnerNumber() != ent.GetOwnerNumber() or not ent.IsUnit():
                self.Cancel()
                return
            self.player.SetControlledUnit(ent)
            self.Completed()    
        