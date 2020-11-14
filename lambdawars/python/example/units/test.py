from core.units import UnitInfo, UnitBaseCombat as BaseClass
from entities import entity

# Define a new entity for our unit
@entity('unit_test')
class UnitTest(BaseClass):
    def Spawn(self):
        self.capabilities |= self.CAP_MOVE_GROUND           
        
        super(UnitTest, self).Spawn()
    
# 
class TestInfo(UnitInfo):
    name = 'unit_test'
    displayname = 'Example Unit'
    description = 'Very awesome example unit.'
    cls_name = 'unit_test'
    modelname = 'models/Zombie/classic.mdl'
    hulltype = 'HULL_HUMAN'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }