from core.abilities import AbilityInstant

class AbilityStriderSpeed(AbilityInstant):
    name = 'striderspeed'
    displayname = '#CombStriderSpeed_Name'
    description = '#CombStriderSpeed_Description'
    image_name = 'vgui/combine/abilities/combine_strider_crouch'
    rechargetime = 3.0
    #energy = 10
    serveronly = True # Do not instantiate on the client
    
    def DoAbility(self):
        self.SelectGroupUnits()
        
        enablespeed = False
        for unit in self.units:
            if not unit.speedenabled:
                enablespeed = True
                break
                
        units = [unit for unit in self.units if unit.speedenabled != enablespeed]
                
        if not enablespeed:
            units = self.TakeEnergy(units)
            
        for unit in units:
            if enablespeed:
                unit.EnableSpeed()
            else:
                unit.DisableSpeed()
        self.SetRecharge(units)
        self.Completed()