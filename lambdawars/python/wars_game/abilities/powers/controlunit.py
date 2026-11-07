from core.abilities import AbilityTarget
from gameinterface import engine

        
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
            engine.ClientCommand(self.player, "c_thirdpersonshoulderoffset %s" % (ent.unitinfo.shoulder_offset))
            engine.ClientCommand(self.player, "c_thirdpersonshoulderaimdist %s" % (ent.unitinfo.shoulder_aimdist))
            engine.ClientCommand(self.player, "c_thirdpersonshoulderheight %s" % (ent.unitinfo.shoulder_height))
            self.Completed()    
        