from vmath import *
from . units import GenericGameUnitTestCase
from srctests.gametestsuite import GameTestSuite
from playermgr import OWNER_LAST
from navmesh import RecastMgr


def CreateUnitNavigationTestSuite():
    suite = GameTestSuite()
    suite.addTest(UnitBuildingNavigationTestCase())
    return suite


class UnitBuildingNavigationTestCase(GenericGameUnitTestCase):
    """ Tests navigation of units around buildings.
    
        Buildings cut and block navigation areas.
    """
    def setUp(self):
        super().setUp()
        
        self.testsleft = [
            # Test move around one building
            (self.testMoveAroundBuilding1, []),
            (self.testMoveOrderResult, ['testMoveAroundBuilding1']),
            
            # Test move to building behind and adjacent another building
            (self.testMoveToBuildingBehindBuilding, []),
            (self.testMoveOrderResult, ['testMoveToBuildingBehindBuilding']),
            
            # Test move to barricade from two sides
            (self.testMoveToBarricade, ['target_barricade_start']),
            (self.testMoveOrderResult, ['testMoveToBarricade start']),
            (self.testMoveToBarricade, ['target_barricade_end']),
            (self.testMoveOrderResult, ['testMoveToBarricade end']),
        ]
        
    def testMoveAroundBuilding1(self):
        ''' Tests moving a unit around a building.
            A building blocks the navigation mesh areas below the building, so the path finder
            creates a path around the building.
        
            Scenario:
            1. Create one soldier (unit_combine)
            2. Create one obstacle building (build_reb_barracks)
            3. Order unit to the other side of the building
        '''
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = 'testMoveAroundBuilding1 unit: %s, owner: %d' % (unitname, ownernumber)
        
        spawnspot = self.GetPositionByTargetName('target_plus_512')
        obstaclespot = self.GetPositionByTargetName('target_origin')
        movespot = self.GetPositionByTargetName('target_min_512')
        
        # Create unit
        unit = self.CreateUnit('unit_combine', spawnspot, owner_number=ownernumber)
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit = unit
        
        # Create obstacle
        obstacle = self.CreateUnit('build_reb_barracks', obstaclespot, owner_number=ownernumber)
        self.assertIsNotNone(obstacle, msg=unitmsg)
        self.obstacle = obstacle
        
        # Make sure obstacle is registered
        RecastMgr().Update(0.1)
        
        # Calculate approximately time needed to move 1100 hammer units
        # Can differ due acceleration and unit specific other things
        # The rebel barracks is about 150 units wide
        maxspeed = unit.mv.maxspeed
        acceltime = maxspeed / (unit.locomotion.acceleration * maxspeed) 
        neededtime = (1150.0 / maxspeed) + acceltime
        
        # Tell unit to move to 512 hammer units further on the test map
        unit.MoveOrder(movespot)
        
        self.movespot = movespot
        self.neededtime = neededtime
        
        return neededtime
        
    def testMoveToBuildingBehindBuilding(self):
        ''' Tests moving to a building directly behind another building.
        
            There are some special rules when moving to buildings, because they are in blocked navigation areas.
        '''
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = 'testMoveToBuildingBehindBuilding unit: %s, owner: %d' % (unitname, ownernumber)
        
        spawnspot = self.GetPositionByTargetName('target_plus_512')
        obstaclespot = self.GetPositionByTargetName('target_origin')
        dir = obstaclespot - spawnspot
        VectorNormalize(dir)
        
        # Create unit
        unit = self.CreateUnit('unit_combine', spawnspot, owner_number=ownernumber)
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit = unit
        
        # Create obstacle
        obstacle = self.CreateUnit('build_reb_barracks', obstaclespot, owner_number=ownernumber)
        self.assertIsNotNone(obstacle, msg=unitmsg)
        self.obstacle = obstacle
        mins = obstacle.CollisionProp().OBBMins()
        movetargetspot = self.GetPositionByTargetName('target_origin') + (dir * -mins.x)
        
        # Create obstacle target
        movetarget = self.CreateUnit('build_reb_billet', movetargetspot, owner_number=ownernumber)
        self.assertIsNotNone(movetarget, msg=unitmsg)
        self.movetarget = movetarget
        
        # Make sure obstacle is registered
        RecastMgr().Update(0.1)
        
        # Calculate approximately time needed to move 1150 hammer units
        # Can differ due acceleration and unit specific other things
        # The rebel barracks is about 120 units wide
        maxspeed = unit.mv.maxspeed
        acceltime = maxspeed / (unit.locomotion.acceleration * maxspeed) 
        neededtime = (1150.0 / maxspeed) + acceltime
        
        # Tell unit to move to the target building
        unit.MoveOrder(movetarget.GetAbsOrigin(), target=movetarget)
        
        self.neededtime = neededtime
        
        return neededtime
        
    def testMoveToBarricade(self, targetstartname):
        ''' Tests moving to a barricade. 
        
            The test barricade can be approached from two sides. 
            The unit should pick the shortest path to the barricade.
        '''
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = 'testMoveToBarricade unit: %s, owner: %d' % (unitname, ownernumber)
        
        targetstart = self.GetPositionByTargetName(targetstartname)
        movetarget = self.GetEntityByTargetName('target_rock_barricade')
        
        # Create unit
        unit = self.CreateUnit('unit_combine', targetstart, owner_number=ownernumber)
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit = unit
        
        # Move to barricade
        self.movetarget = movetarget
        
        dist = targetstart.DistTo(movetarget.GetAbsOrigin())
        
        # Calculate approximately time needed to move x hammer units
        # Can differ due acceleration and unit specific other things
        maxspeed = unit.mv.maxspeed
        acceltime = maxspeed / (unit.locomotion.acceleration * maxspeed) 
        neededtime = (dist / maxspeed) + acceltime
        
        # Tell unit to move to the target barricade
        unit.MoveOrder(movetarget.GetAbsOrigin(), target=movetarget)
        
        self.neededtime = neededtime
        
        return neededtime
        
    def testMoveOrderResult(self, testname):
        ''' Verifies the result of a move order. 
        
            Expects 'self.unit' to the unit executing the move order and 'self.movespot' to be the target spot.
            Alternatively a 'movetarget' might be filled in.
        '''
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = '%s unit: %s, owner: %d' % (testname, unitname, ownernumber)
    
        unit = self.unit
        
        if self.movespot:
            # Test unit reached the spot more or less
            distmovespot = (unit.GetAbsOrigin()-self.movespot).Length2D()
            self.assertLess(distmovespot, 32.0, msg='%s: dist to goal: %f, tol: 32, expected max time: %f' % (testname, distmovespot, self.neededtime))
            
        # Should have no orders left
        self.assertEqual(len(unit.orders), 0, msg='%s: %s' % (testname, str(list(map(str, unit.orders)))))
        
        # Last navigation should have been a success
        self.assertTrue(unit.navigator.path.success, msg=unitmsg)
        
        self.DoCleanupUnits()
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
        
        self.movespot = None
        self.movetarget = None
        
        return 1.0
        
    movespot=  None
    movetarget = None
        