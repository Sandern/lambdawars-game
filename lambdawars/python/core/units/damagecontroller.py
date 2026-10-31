"""Damage controller classes for Lambda Wars.

This serves as a dummy unit purely to set as attacker in the damage info.
This way the dummy unit will apply the attributes during doing damage.
"""
from .baseobject import UnitBaseObject as BaseClass, UnitObjectInfo
from entities import entity, EFL_SERVER_ONLY
from srcbase import EF_NODRAW

class UnitDamageControllerInfo(UnitObjectInfo):
    """Information class for damage controller units."""
    hidden = False
    cls_name = 'unit_damage_controller'
    
@entity('unit_damage_controller')
class UnitDamageController(BaseClass):
    """Dummy unit used as damage attacker to apply attributes.
    
    This invisible unit is used to apply damage with specific attributes
    by being set as the attacker in damage info.
    """
    def __init__(self):
        """Initialize the damage controller as server-only and invisible."""
        super().__init__()
        
        self.AddEFlags(EFL_SERVER_ONLY)
        self.AddEffects(EF_NODRAW)
    def Event_KilledOther(self, victim, info):
        """Handle when this controller kills another unit.
        
        Args:
            victim: Unit that was killed.
            info: Damage information.
        """
        super().Event_KilledOther(victim, info)

        if self.unit_owner:
            self.unit_owner.kills += 1
    unit_owner = None
        
@entity('unit_damage_controller_all')
class UnitDamageControllerAll(UnitDamageController):
    """Damage controller that can damage friendly units."""
    def Spawn(self):
        """Spawn the damage controller and enable friendly damage."""
        super().Spawn()
        
        self.friendlydamage = True