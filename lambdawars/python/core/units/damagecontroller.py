''' This serves as a dummy unit purely to set as attacker in the damage info.
    This way the dummy unit will apply the attributes during doing damage.
'''
from .baseobject import UnitBaseObject as BaseClass, UnitObjectInfo
from entities import entity, EFL_SERVER_ONLY
from srcbase import EF_NODRAW

class UnitDamageControllerInfo(UnitObjectInfo):
    hidden = False
    cls_name = 'unit_damage_controller'
    
@entity('unit_damage_controller')
class UnitDamageController(BaseClass):
    def __init__(self):
        super().__init__()
        
        self.AddEFlags(EFL_SERVER_ONLY)
        self.AddEffects(EF_NODRAW)
        
@entity('unit_damage_controller_all')
class UnitDamageControllerAll(UnitDamageController):
    def Spawn(self):
        super().Spawn()
        
        self.friendlydamage = True