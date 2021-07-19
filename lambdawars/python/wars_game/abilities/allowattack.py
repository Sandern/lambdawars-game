from core.abilities import AbilityInstant

class AbilityNoAttack(AbilityInstant):
    name = "noattack"
    image_name = 'vgui/abilities/ability_noattack.vmt'
    displayname = "#AbilityNoAttack_Name"
    description = ""
    hidden = True
    cloakallowed = True
    
    # Ability
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()

            for unit in list(self.units):
                unit.attacks = []
                unit.UpdateAttackInfo()
                unit.allowattack = False
                    
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectGroupUnits()
class AbilityAllowAttack(AbilityInstant):
    name = "allowattack"
    image_name = 'vgui/abilities/ability_allowattack.vmt'
    displayname = "#AbilityAllowAttack_Name"
    description = ""
    hidden = True
    cloakallowed = True
    
    # Ability
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()

            for unit in list(self.units):
                unit.RebuildAttackInfo()
                unit.allowattack = True
                    
            self.Completed()