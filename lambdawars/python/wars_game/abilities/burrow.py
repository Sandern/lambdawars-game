from core.abilities import AbilityBase

class AbilityBurrow(AbilityBase):
    # Info
    name = "burrow"
    image_name = 'vgui/antlions/abilities/ant_burrow_down.vmt'
    rechargetime = 1
    displayname = "#AbilityBurrow_Name"
    description = "#AbilityBurrow_Description"
    hidden = True
    
    # Ability Code
    def Init(self):
        super().Init()
        
        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()

        for unit in self.units:
            unit.Burrow()
        self.SetRecharge(self.units)
        self.Completed()
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        return not unit.burrowed
        
    serveronly = True # Do not instantiate on the client

class AbilityUnBurrow(AbilityBase):
    # Info
    name = "unburrow"
    image_name = 'vgui/antlions/abilities/ant_burrow_up.vmt'
    rechargetime = 1
    displayname = "#AbilityUnBurrow_Name"
    description = "#AbilityUnBurrow_Description"
    hidden = True
    
    # Ability Code
    def Init(self):
        super().Init()
        
        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()

        for unit in self.units:
            unit.UnBurrow()
        self.SetRecharge(self.units)
        self.Completed()
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        return unit.burrowed
        
    serveronly = True # Do not instantiate on the client

