from vmath import Vector
from . units import GenericGameUnitTestCase
from srctests.gametestsuite import GameTestSuite
from playermgr import OWNER_LAST

def CreateUnitNavigationFollowTestSuite():
    suite = GameTestSuite()
    suite.addTest(UnitFollowNavigationTestCase())
    return suite
    
class UnitFollowNavigationTestCase(GenericGameUnitTestCase):
    """ Tests follow code of units. Should follow another friendly unit when ordered.
    """
    movespot = None
    neededtime = None
    
    def setUp(self):
        super().setUp()
        
        self.testsleft = [
            # Test move around one building
            (self.testFollowUnit, []),
            (self.testFollowResult, []),
        ]
        
    def testFollowUnit(self):
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = 'testFollowUnit unit: %s, owner: %d' % (unitname, ownernumber)
        
        spawnspot = self.GetPositionByTargetName('target_plus_512')
        movespot = self.GetPositionByTargetName('target_min_512')
        
        # Create the unit which will follow the other unit
        unit = self.CreateUnit('unit_combine', spawnspot + Vector(64.0, 0, 0), owner_number=ownernumber)
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit1 = unit

        # Create unit being followed
        unit = self.CreateUnit('unit_combine', spawnspot, owner_number=ownernumber)
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit2 = unit
        
        # Make unit1 follow unit2
        self.unit1.MoveOrder(position=self.unit2.GetAbsOrigin(), target=self.unit2)
        
        # Make unit2 move to the spot
        self.unit2.MoveOrder(position=movespot)
        
        # Wait for the result
        maxspeed = self.unit2.mv.maxspeed
        acceltime = maxspeed / (self.unit2.locomotion.acceleration * maxspeed) 
        neededtime = ((movespot - spawnspot).Length2D() / maxspeed) + acceltime + 5.0
        
        self.movespot = movespot
        self.neededtime = neededtime
        
        return neededtime
        
    def testFollowResult(self):
        testname = 'testFollowResult'
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = '%s unit: %s, owner: %d' % (testname, unitname, ownernumber)
    
        unit = self.unit2
        
        if self.movespot:
            # Test unit reached the spot more or less
            distmovespot = (unit.GetAbsOrigin()-self.movespot).Length2D()
            self.assertLess(distmovespot, 32.0, msg='%s: dist to goal: %f, tol: 32, expected max time: %f' % (testname, distmovespot, self.neededtime))
            
        # Should have no orders left
        self.assertEqual(len(unit.orders), 0, msg='%s: %s' % (testname, str(list(map(str, unit.orders)))))
        
        # Last navigation should have been a success
        self.assertTrue(unit.navigator.path.success, msg=unitmsg)
        
        # Unit 1 should still be following
        unit = self.unit1
        distfollow = (unit.GetAbsOrigin() - self.unit2.GetAbsOrigin()).Length2D()
        self.assertLess(distmovespot, 64.0, msg='%s: dist to follow target: %f, tol: 64' % (testname, distfollow))
        
        self.DoCleanupUnits()
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
        
        self.movespot = None
        self.movetarget = None
        
        return 1.0