from vmath import *
from . units import GenericGameUnitTestCase
from srctests.gametestsuite import GameTestSuite
from vmath import vec3_origin
from playermgr import OWNER_LAST

if isserver:
    from utils import UTIL_RemoveImmediate

from core.units import CreateUnit


def CreateUnitSensingTestSuite():
    suite = GameTestSuite()
    # Just test it for soldier and for a strider. Strider is an air unit, so may behave differently
    suite.addTest(GenericGameUnitSensingTestCase(unitname='unit_combine'))
    suite.addTest(GenericGameUnitSensingTestCase(unitname='unit_strider'))
    return suite


class GenericGameUnitSensingTestCase(GenericGameUnitTestCase):
    nonexitingunittype = 'nonexistingunitzjdlkfjds'
    
    testunit = None
    testenemy = None
    testfriend = None
    
    def setUp(self):
        super().setUp()

        ownernumber = OWNER_LAST
        self.testsleft = [
            (self.testCreateUnit, [ownernumber]),
            (self.testSensing1, [ownernumber]),
            (self.testSensing2, [ownernumber]),
            (self.testSensing3, [ownernumber]),
        ]
        
    def testCreateUnit(self, ownernumber):
        unitname = self.unitname
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        # Create an enemy
        enemy = self.OnUnitCreated(CreateUnit('unit_combine', vec3_origin + Vector(-512, 0, 0), owner_number=ownernumber+1))
        self.assertIsNotNone(enemy, msg=unitmsg)
        self.testenemy = enemy
        
        # Create and spawn the unit
        unit = self.OnUnitCreated(CreateUnit(unitname, vec3_origin, owner_number=ownernumber))
        self.assertIsNotNone(unit, msg=unitmsg)
        self.testunit = unit
        
        return 1.0
        
    def testSensing1(self, ownernumber):
        unitname = self.unitname
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        unit = self.testunit
        enemy = self.testenemy
        
        # There is now one enemy in the sensing component of the unit
        self.assertEqual(unit.senses.CountSeen(), 1)
        self.assertEqual(unit.senses.CountSeenEnemy(), 1)
        self.assertEqual(unit.senses.GetNearestEnemy(), enemy)
        self.assertEqual(unit.senses.CountSeenOther(), 0)
        self.assertEqual(len(unit.senses.GetEnemies()), 1)
        self.assertEqual(len(unit.senses.GetOthers()), 0)
        self.assertEqual(unit.senses.GetEnemy(0), enemy)
        self.assertEqual(len(unit.senses.GetEnemies(unittype=self.nonexitingunittype)), 0)
        self.assertEqual(len(unit.senses.GetOthers(unittype=self.nonexitingunittype)), 0)
        
        # Create a friend
        friend = self.OnUnitCreated(CreateUnit('unit_combine', vec3_origin + Vector(512, 0, 0), owner_number=ownernumber))
        self.assertIsNotNone(friend, msg=unitmsg)
        self.testfriend = friend

        # FIXME: Shouldn't be needed, but maybe due the high host_timescale it gets skipped (making the test unreliable)
        unit.senses.ForcePerformSensing()
        
        return 1.0
        
    def testSensing2(self, ownernumber):
        unitname = self.unitname
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        unit = self.testunit
        enemy = self.testenemy
        friend = self.testfriend
        
        # There is now one enemy and one friend in the sensing component of the unit
        self.assertEqual(unit.senses.CountSeen(), 2)
        self.assertEqual(unit.senses.CountSeenEnemy(), 1)
        self.assertEqual(unit.senses.GetNearestEnemy(), enemy)
        self.assertEqual(unit.senses.CountSeenOther(), 1)
        self.assertEqual(len(unit.senses.GetEnemies()), 1)
        self.assertEqual(len(unit.senses.GetOthers()), 1)
        self.assertEqual(unit.senses.GetEnemy(0), enemy)
        self.assertEqual(unit.senses.GetOther(0), friend)
        self.assertEqual(len(unit.senses.GetEnemies(unittype=self.nonexitingunittype)), 0)
        self.assertEqual(len(unit.senses.GetOthers(unittype=self.nonexitingunittype)), 0)
        
        # Remove the enemy
        UTIL_RemoveImmediate(enemy)
        self.assertTrue(enemy == None, msg=unitmsg)

        # FIXME: Shouldn't be needed, but maybe due the high host_timescale it gets skipped (making the test unreliable)
        unit.senses.ForcePerformSensing()
        
        return 1.0
        
    def testSensing3(self, ownernumber):
        unitname = self.unitname
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        unit = self.testunit
        friend = self.testfriend
        
        # There is now one friend in the sensing component of the unit
        self.assertEqual(unit.senses.CountSeen(), 1)
        self.assertEqual(unit.senses.CountSeenEnemy(), 0)
        self.assertEqual(unit.senses.GetNearestEnemy(), None)
        self.assertEqual(unit.senses.CountSeenOther(), 1)
        self.assertEqual(len(unit.senses.GetEnemies()), 0)
        self.assertEqual(len(unit.senses.GetOthers()), 1)
        self.assertEqual(unit.senses.GetOther(0), friend)
        self.assertEqual(len(unit.senses.GetEnemies(unittype=self.nonexitingunittype)), 0)
        self.assertEqual(len(unit.senses.GetOthers(unittype=self.nonexitingunittype)), 0)
        
        self.DoCleanupUnits()
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
