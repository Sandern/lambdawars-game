from srcbase import *
from . gametestsuite import GameTestSuite
from unittest.util import strclass
from . gametestcase import GenericGameTestCase
from gamerules import gamerules
from vmath import vec3_origin

def CreateCollisionTestSuite():
    suite = GameTestSuite()
    
    collisiongroupcombos = [
        # Any combination with WARS_COLLISION_GROUP_IGNORE_ALL_UNITS should not collide with any of the other unit collision group
        (WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, False),
        (WARS_COLLISION_GROUP_IGNORE_UNIT_START, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, False),
        (WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, WARS_COLLISION_GROUP_IGNORE_UNIT_START, False),
        (WARS_COLLISION_GROUP_UNIT_START, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, False),
        (WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, WARS_COLLISION_GROUP_UNIT_START, False),
        
        # WARS_COLLISION_GROUP_IGNORE_UNIT_START to WARS_COLLISION_GROUP_IGNORE_UNIT_END should 
        # not collide with WARS_COLLISION_GROUP_UNIT_START to WARS_COLLISION_GROUP_UNIT_END
        (WARS_COLLISION_GROUP_IGNORE_UNIT_START, WARS_COLLISION_GROUP_UNIT_START, False),
        (WARS_COLLISION_GROUP_UNIT_START, WARS_COLLISION_GROUP_IGNORE_UNIT_START, False),
        
        (WARS_COLLISION_GROUP_IGNORE_UNIT_START+1, WARS_COLLISION_GROUP_UNIT_START, True),
        (WARS_COLLISION_GROUP_UNIT_START, WARS_COLLISION_GROUP_IGNORE_UNIT_START+1, True),
        
        # Should collide with others
        (WARS_COLLISION_GROUP_UNIT_START, WARS_COLLISION_GROUP_UNIT_START, True),
        (WARS_COLLISION_GROUP_UNIT_START, WARS_COLLISION_GROUP_UNIT_START+1, True),
        (WARS_COLLISION_GROUP_UNIT_START+1, WARS_COLLISION_GROUP_UNIT_START, True),
        
        # With buildings
        (WARS_COLLISION_GROUP_UNIT_START, WARS_COLLISION_GROUP_BUILDING, True),
        (WARS_COLLISION_GROUP_BUILDING, WARS_COLLISION_GROUP_UNIT_START, True),
        
        # WARS_COLLISION_GROUP_IGNORE_ALL_UNITS should collide with buildings
        (WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, WARS_COLLISION_GROUP_BUILDING, True),
        (WARS_COLLISION_GROUP_BUILDING, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, True),
        
        # Specific ignores should also collide with buildings
        (WARS_COLLISION_GROUP_IGNORE_UNIT_START, WARS_COLLISION_GROUP_BUILDING, True),
        (WARS_COLLISION_GROUP_BUILDING, WARS_COLLISION_GROUP_IGNORE_UNIT_START, True),
    ]
    
    for col1, col2, shouldcollide in collisiongroupcombos:
        suite.addTest(ShouldCollideTestCase(col1=col1, col2=col2, shouldcollide=shouldcollide))
    return suite

class ShouldCollideTestCase(GenericGameTestCase):
    unitname = None
    
    def __init__(self, col1=0, col2=0, shouldcollide=False, *args, **kwargs):
        super(ShouldCollideTestCase, self).__init__(*args, **kwargs)
        
        self.col1 = col1
        self.col2 = col2
        self.shouldcollide = shouldcollide
        
    def __str__(self):
        return "test ShouldCollide %s -> %s (%s)" % (self.col1, self.col2, strclass(self.__class__))

    def testShouldCollide(self, unit, collisiongroup, contentsmask):
        if not unit.ShouldCollide(collisiongroup, contentsmask):
            return False
        if unit and not gamerules.ShouldCollide(unit.GetCollisionGroup(), collisiongroup):
            return False
        return True
        
    def runTest(self):
        # Create and spawn the unit
        unit = self.CreateUnit('unit_combine', vec3_origin, owner_number=2)
        self.assertIsNotNone(unit)
        
        unit.SetCollisionGroup(self.col1)
        collided = self.testShouldCollide(unit, self.col2, MASK_SOLID)
        if self.shouldcollide:
            self.assertTrue(collided)
        else:
            self.assertFalse(collided)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred())
