from core.abilities.base import AbilityBase


class AbilityClearFocus(AbilityBase):
    name = "focusclear"
    displayname = "#AbilityClearFocus_Name"
    description = "#AbilityClearFocus_Description"
    image_name = 'vgui/abilities/holdposition.vmt'
    hidden = True
    def Init(self):
        super().Init()
        
        self.SelectGroupUnits()

        for unit in self.units:
            unit.ClearFocus()
        self.Completed()
        
    serveronly = True 