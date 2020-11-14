from core.abilities import AbilityInstant
from core.units import GetUnitInfo
from srcbase import FL_NPC
from vmath import Vector
from utils import trace_t, UTIL_EntitiesInBox
from entities import D_HT
from wars_game.statuseffects import ReducedVisionEffectInfo

class AbilityFlash(AbilityInstant):
    ''' Blinds the enemies reducing their vision range. '''
    name = "flash"
    rechargetime = 20
    energy = 0
    displayname = "#CombFlash_Name"
    description = "#CombFlash_Description"
    image_name = 'vgui/combine/abilities/flash'
    hidden = True
    cloakallowed = True
    
    defaultautocast = True
    autocastcheckonenemy = True
    
    radius = 512.0
    
    # Ability
    def DoAbility(self):
        radius = self.radius
        
        self.SelectSingleUnit()
        units = self.TakeEnergy(self.units)
        for unit in units:
            unit.AttackFlash()
        
            origin = unit.GetAbsOrigin()
            enemies = UTIL_EntitiesInBox(32, origin-Vector(radius,radius,radius), origin+Vector(radius,radius,radius), FL_NPC)
            for enemy in enemies:
                if not enemy or not enemy.IsAlive() or not enemy.IsUnit() or enemy in units:
                    continue
                    
                if 'mechanic' in enemy.attributes:
                    continue

                if 'building' in enemy.attributes:
                    continue

                if unit.IRelationType(enemy) != D_HT:
                    continue
                    
                ReducedVisionEffectInfo.CreateAndApply(enemy, attacker=unit, duration=8.0)
            
        self.SetRecharge(units)
        self.Completed()
        
    @classmethod
    def CheckAutoCast(info, unit):
        if not info.CanDoAbility(None, unit=unit):
            return False
        return False
        
    # This ability object won't be created on the executing client
    serveronly = True