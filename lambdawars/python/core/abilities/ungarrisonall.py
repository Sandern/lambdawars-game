"""Ungarrison ability for evacuating units from buildings.

Allows players to order all garrisoned units to exit a building,
freeing up the building for other uses or repositioning units.
"""
from .base import AbilityBase

class AbilityUngarrison(AbilityBase):
    # Info
    name = "ungarrisonall"
    displayname = "#AbilityUngarrisonAll_Name"
    description = "#AbilityUngarrisonAll_Description"
    image_name = 'vgui/abilities/exit_building.vmt'
    hidden = True
    
    # Ability Code
    def Init(self):
        super().Init()
        
        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()

        for unit in self.units:
            unit.UnGarrisonAll()
        self.Completed()
        
    #@classmethod    
    #def ShouldShowAbility(info, unit):
    #    return bool(unit.units)
        
    serveronly = True # Do not instantiate on the client