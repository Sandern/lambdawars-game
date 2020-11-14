from srcbase import SOLID_BSP
from vmath import *
from unittest.util import strclass
from srctests.gametestsuite import GameTestSuite
from . units import GenericGameUnitTestCase
from gamemgr import dblist
from vmath import vec3_origin
from playermgr import OWNER_LAST
from entities import GetClassByClassname

if isserver:
    from utils import UTIL_RemoveImmediate
    from physics import ForcePhysicsSimulate
    from entities import CFuncBrush

from core.units import CreateUnit, GetUnitInfo

def CreateLOSUnitsTestSuite():
    suite = GameTestSuite()
    
    for name, info in dblist['units'].items():
        unitinfo = GetUnitInfo(name)
        if not unitinfo:
            continue
        cls = GetClassByClassname(unitinfo.cls_name)
        if not cls or issubclass(cls, CFuncBrush):
            continue
            
        suite.addTest(GenericGameUnitLOSTestCase(unitname=name, srcunitname='unit_combine'))
        suite.addTest(GenericGameUnitLOSTestCase(unitname=name, srcunitname='unit_antlion'))
    return suite
    
class GenericGameUnitLOSTestCase(GenericGameUnitTestCase):
    testunit = None
    testenemy = None
    
    def __init__(self, unitname='', srcunitname='', *args, **kwargs):
        super().__init__(unitname=unitname, *args, **kwargs)
        
        self.srcunitname = srcunitname
    
    def __str__(self):
        return "test los from %s to target %s(%s)" % (self.srcunitname, self.unitname, strclass(self.__class__))
    
    def setUp(self):
        super().setUp()
        
        unitname = self.unitname
        srcunitname = self.srcunitname
        
        self.testsleft = [
            (self.testUnitLOSSetup, [unitname, srcunitname, OWNER_LAST]),
            (self.testUnitLOSResult, [unitname, srcunitname, OWNER_LAST]),
        ]
    
    def testUnitLOSSetup(self, unitname, srcunitname, ownernumber):
        unitmsg = 'unit: %s, srcunit: %s, owner: %d' % (unitname, srcunitname, ownernumber)
        
        enemy = self.OnUnitCreated(CreateUnit(srcunitname, vec3_origin + Vector(-512, 0, 0), owner_number=ownernumber+1))
        self.assertIsNotNone(enemy, msg=unitmsg)
        self.testenemy = enemy
        
        # Create and spawn the unit
        unit = self.OnUnitCreated(CreateUnit(unitname, vec3_origin, owner_number=ownernumber))
        self.testunit = unit
        self.assertIsNotNone(unit, msg=unitmsg)
        
        if unit.IsSolid() and unit.GetSolid() != SOLID_BSP and not isinstance(unit, CFuncBrush):
            ForcePhysicsSimulate()
            return 0.5
            
            #self.assertTrue(enemy.attacks[0].CanAttack(enemy, unit))
            #time.sleep(0.1)
            self.assertTrue(enemy.HasRangeAttackLOSTarget(unit), msg=unitmsg)
        else:
            DevMsg(1, 'LOSUnitsTestSuite: Skipping %s (not solid)' % (unitname))

    def testUnitLOSResult(self, unitname, srcunitname, ownernumber):
        unitmsg = 'unit: %s, source unit: %s, owner: %d' % (unitname, srcunitname, ownernumber)
        if not self.testunit:
            return
            
        unit = self.testunit
        enemy = self.testenemy
            
        if unit.IsSolid() and unit.GetSolid() != SOLID_BSP and not isinstance(unit, CFuncBrush):
            self.assertTrue(enemy.HasRangeAttackLOSTarget(unit), msg=unitmsg)
            
        # Remove the unit. Handle should be None after removing.
        UTIL_RemoveImmediate(unit)
        self.assertTrue(unit == None, msg=unitmsg)
        UTIL_RemoveImmediate(enemy)
        self.assertTrue(enemy == None, msg=unitmsg)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
        