from unittest.util import strclass
from srctests.gametestcase import GenericGameTestCase
from srctests.gametestsuite import GameTestSuite
import playermgr
from gamemgr import dblist
from vmath import vec3_origin, VectorNormalize, VectorAngles, QAngle
from playermgr import OWNER_NEUTRAL, OWNER_ENEMY, OWNER_LAST
from entities import GetClassByClassname, CFuncBrush
#from navmesh import IsAreaBlocked
from gameinterface import ConVar

from core.units import CreateUnit, GetUnitInfo, UnitBaseCombat

if isserver:
    from utils import UTIL_RemoveImmediate
    
import sys

py_tests_units_testonly = ConVar('py_tests_units_testonly' if isserver else 'cl_py_tests_units_testonly', '', flags=0, helpstring='Tests one specific unit name only')

def CreateUnitsTestSuite():
    suite = GameTestSuite()
    
    testonlyunitname = py_tests_units_testonly.GetString()
    
    for name, info in dblist['units'].items():
        if testonlyunitname and name != testonlyunitname:
            continue
            
        unitinfo = GetUnitInfo(name)
        if not unitinfo:
            continue
        cls = GetClassByClassname(unitinfo.cls_name)
        if not cls or issubclass(cls, CFuncBrush):
            continue
    
        suite.addTest(GenericGameUnitTestCase(unitname=name))
            
        if issubclass(cls, UnitBaseCombat):
            suite.addTest(CombatGameUnitTestCase(unitname=name))
        
    return suite
    
class GenericGameUnitTestCase(GenericGameTestCase):
    ''' Test case for all unit types. 
    
        Only tests functionality available in all units.
    '''
    unitname = None
    
    testunit = None
    
    def __init__(self, unitname='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.unitname = unitname
        
    def __str__(self):
        return "test %s (%s)" % (self.unitname, strclass(self.__class__))
        
    def setUp(self):
        super().setUp()
        
        unitname = self.unitname
        
        self.testsleft = [
            (self.testSpawnUsingParameters, [unitname, OWNER_NEUTRAL]),
            (self.testRemove, [unitname, OWNER_NEUTRAL]),
            (self.testSpawnUsingParameters, [unitname, OWNER_ENEMY]),
            (self.testRemove, [unitname, OWNER_ENEMY]),
            (self.testSpawnUsingParameters, [unitname, OWNER_LAST]),
            (self.testRemove, [unitname, OWNER_LAST]),
        ]
        
    def testSpawnUsingParameters(self, unitname, ownernumber):
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        # Create and spawn the unit
        self.testunit = self.OnUnitCreated(CreateUnit(unitname, vec3_origin, owner_number=ownernumber))
        self.assertIsNotNone(self.testunit, msg=unitmsg)
        
        #self.testnavareas = []
        #if self.testunit.isbuilding:
        #    self.testnavareas += self.testunit.areasids
            
        # TODO
        # Test if eye position is not too close to bottom. This would be a suspicious position.
        # The eye offset matters for fog of war calculations and los testing
        #bottomz = self.testunit.GetAbsOrigin().z + self.testunit.CollisionProp().OBBMins().z
        #self.assertTrue( abs(self.testunit.EyePosition().z - bottomz) > 16.0, msg='%s => suspicious eye offset!' % (unitmsg) )
                
        # Perform some idle simulation
        return 1.0
        
    def testRemove(self, unitname, ownernumber):
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        # Remove the unit. Handle should be None after removing.
        UTIL_RemoveImmediate(self.testunit)
        self.assertTrue(self.testunit == None, msg=unitmsg)
        
        # Blocked areas should be cleared (buildings), otherwise indicates incorrect cleanup
        # TODO: Update test
        #for areaid in self.testnavareas:
        #    self.assertFalse(IsAreaBlocked(areaid), msg=unitmsg)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
        
        return 0
        
class CombatGameUnitTestCase(GenericGameTestCase):
    ''' Test case for combat type units.
    '''
    unitname = None
    
    def __init__(self, unitname='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.unitname = unitname
        
    def __str__(self):
        return "test %s (%s)" % (self.unitname, strclass(self.__class__))
        
    def setUp(self):
        super().setUp()
        
        unitname = self.unitname
        
        self.testsleft = [
            (self.issueMoveOrder, [unitname]),
            (self.testMoverOrderResult, [unitname]),
        ]
        
    def issueMoveOrder(self, unitname):
        ownernumber = OWNER_LAST
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        spawnspot = self.GetPositionByTargetName('target_origin')
        movespot = self.GetPositionByTargetName('target_min_512')
        
        angles = QAngle()
        dir = movespot - spawnspot
        VectorNormalize(dir)
        VectorAngles(dir, angles)
        
        # Create and spawn the unit
        unit = self.OnUnitCreated(CreateUnit(unitname, spawnspot, owner_number=ownernumber, angles=angles))
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit = unit
        
        # Calculate approximately time needed to move 512 hammer units
        # Can differ due acceleration and unit specific other things
        maxspeed = unit.mv.maxspeed
        acceltime = maxspeed / (unit.locomotion.acceleration * maxspeed) 
        neededtime = (512.0 / maxspeed) + acceltime + 5.0
        
        # Tell unit to move to 512 hammer units further on the test map
        unit.MoveOrder(movespot)
        
        self.movespot = movespot
        self.neededtime = neededtime
        
        return neededtime
        
    def testMoverOrderResult(self, unitname):
        ownernumber = OWNER_LAST
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        unit = self.unit
        
        # Test unit reached the spot more or less
        distmovespot = (unit.GetAbsOrigin()-self.movespot).Length2D()
        self.assertLess(distmovespot, 32.0, msg='dist to goal: %f, tol: 32, expected max time: %f' % (distmovespot, self.neededtime))
        
        # Last navigation should have been a success
        self.assertTrue(unit.navigator.path.success, msg=unitmsg)
        
        # Should have no orders left
        self.assertEqual(len(unit.orders), 0, msg=str(list(map(str, unit.orders))))
        
        self.DoCleanupUnits()
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
        