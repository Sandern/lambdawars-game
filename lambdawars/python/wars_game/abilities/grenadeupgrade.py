from core.abilities.instant import AbilityInstant
from core.units import GetUnitInfo
from wars_game.units.rebel import RebelInfo
import copy
if isserver:
    from core.abilities import GetAbilityInfo
    from core.units.behavior_generic import BaseAction, BehaviorGeneric

class GrenadeUnlockAbility(AbilityInstant):
    interruptible = False
    hidden = True
    serveronly = True
    image_name = 'vgui/abilities/ability_grenade_upgrade'
    activatesoundscript = 'ability_combine_shotgun_upgrade'
    
    def DoAbility(self):
        # Just do the ability on creation ( == when you click the ability slot )
        self.SelectGroupUnits()
        
        if isserver:
            count = self.TakeResources(count=len(self.units))
            if not count:
                self.Cancel()
                return
        
        for unit in self.units:
            if hasattr(unit, 'grenadeUnlocked'):
                unit.grenadeUnlocked = True
        
        self.hidden = True #after unlock hide the ability
        
        if isclient:
            self.PlayActivateSound()
            
    @classmethod
    def ShouldShowAbility(info, unit):
        if hasattr(unit, 'grenadeUnlocked'):
            return not unit.grenadeUnlocked
        return False

class RebelGrenadeUnlockAbility(GrenadeUnlockAbility):            
    name = 'rebel_grenade_upgrade'
    displayname = '#AbilityGrenadeUpgrade_Name'
    description = '#AbilityGrenadeUpgrade_Description'
    costs = [('requisition', 10),('scrap', 5)]
    techrequirements = ['grenade_unlock']
    sai_hint = set(['sai_grenade_unit_unlock'])

    
class CombineGrenadeUnlockAbility(GrenadeUnlockAbility):            
    name = 'combine_grenade_upgrade'
    displayname = '#AbilityGrenadeUpgrade_Name'
    description = '#AbilityGrenadeUpgrade_Description'
    costs = [('requisition', 10),('power', 10)]
    techrequirements = ['grenade_unlock_combine']
    sai_hint = set(['sai_grenade_unit_unlock'])