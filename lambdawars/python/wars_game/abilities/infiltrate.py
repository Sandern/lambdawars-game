from core.abilities import AbilityInstant

class AbilityInfiltrate(AbilityInstant):
    # Info
    name = "infiltrate"
    rechargetime = 0
    energy = 20
    displayname = "#RebInfiltrate_Name"
    description = "#RebInfiltrate_Description"
    image_name = 'vgui/rebels/abilities/infiltrate'
    hidden = True
    cloakallowed = True
    activatesoundscript = 'ability_infiltrate'
    
    # Ability Code
    @classmethod    
    def GetRequirements(cls, player, unit):
        requirements = super().GetRequirements(player, unit)
        
        # Decloaking never requires energy
        if unit.cloaked:
            requirements.discard('energy')
         
        return requirements
        
    if isserver:
        def DoAbility(self):
            # Just do the ability on creation ( == when you click the ability slot )
            self.SelectGroupUnits()
            
            # Cloak all if one is not cloaked
            # Only uncloak if all units in the selection are cloaked
            cloak = False
            for unit in self.units:
                if not unit.cloaked and unit.energy >= self.energy:
                    cloak = True
                    break
            
            if cloak:
                units = self.TakeEnergy(self.units)
                self.SetRecharge(units)
            else:
                units = self.units
                # self.SetRecharge(units)  # Make the ability obtain a cooldown after uncloak

            for unit in units:
                if not cloak:
                    unit.UnCloak()
                else:
                    unit.Cloak()

            # Make the ability obtain a cooldown if you activate cloak with low energy
            # for unit in self.units:
            #     if unit.cloaked and unit.energy <= 3:
            #         self.SetRecharge(units)
                    
            self.Completed()
    else:
        def DoAbility(self):
            # Just do the ability on creation ( == when you click the ability slot )
            self.SelectGroupUnits()
            self.PlayActivateSound()
        
    #serveronly = True # Do not instantiate on the client

class AbilityInfiltrateChar(AbilityInfiltrate):
    name = 'infiltrate_char'
    energy = 5
    cloakallowed = True

class AbilityInfiltrateRebScout(AbilityInfiltrate):
	name = 'infiltrate_reb_scout'
	energy = 10
	techrequirements = ['build_reb_munitiondepot']
	cloakallowed = True

class AbilityInfiltrateRebScout(AbilityInfiltrate):
    name = 'infiltrate_comb_sniper'
    energy = 25
    cloakallowed = True