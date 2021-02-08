from core.abilities.target import AbilityTargetGroup

class AbilityFocusEnemy(AbilityTargetGroup):
    name = "focusenemy_building"
    image_name = 'vgui/abilities/attackmove.vmt'
    rechargetime = 0
    displayname = "#AbilityFocusEnemyG_Name"
    description = "#AbilityFocusEnemyG_Description"
    hidden = True
    cloakallowed = True
    
    # Ability
    def DoAbility(self):
        data = self.mousedata

        
        if not data.ent.IsUnit():
            return
        for unit in self.units:
            unit.focusenemy = data.ent
        if isserver:
            self.Completed()