from . gametestsuite import GameTestSuite
from . gametestcase import GenericGameTestCase
from entities import CBaseEntity, entity
from utils import UTIL_RemoveImmediate

import weakref
import gc

def CreateEntCircularReferenceTestSuite():
    suite = GameTestSuite()
    suite.addTest(EntCircularReferenceTestCase())
    return suite

class EntCircularReferenceTestCase(GenericGameTestCase):
    testent1_weakref = None
    testent2_weakref = None

    def setUp(self):
        super().setUp()

        self.testsleft = [
            (self.testSetup, []),
            (self.testResult, []),
        ]

    def testSetup(self):
        global testent1_weakref, testent2_weakref

        # Create some test entities
        @entity('entcircref_testentity')
        class EntCircularReferenceTestEntity(CBaseEntity):
            pass

        testent1 = self.CreateEntityByName('entcircref_testentity')
        testent1.Spawn()

        self.testent1_weakref = weakref.ref(testent1.Get())
        self.assertTrue(self.testent1_weakref() is not None)

        testent2 = self.CreateEntityByName('entcircref_testentity')
        testent2.Spawn()

        self.testent2_weakref = weakref.ref(testent2.Get())
        self.assertTrue(self.testent2_weakref() is not None)

        # Create circular reference
        testent1.Get().testent2 = testent2.Get()
        testent2.Get().testent1 = testent1.Get()

        # Remove entities
        UTIL_RemoveImmediate(testent1)
        UTIL_RemoveImmediate(testent2)
        testent1 = None
        testent2 = None

        # Entity Handles should compare to None
        self.assertTrue(testent1 == None, msg='Ent1 Handle should be None')
        self.assertTrue(testent2 == None, msg='Ent2 Handle should be None')

        # Just need to wait for a frame to cleanup last reference
        # The last reference can't directly be cleaned up because it's still inside a function in CBaseEntity,
        # causes the instance to be removed while executing the function.
        return 0.0001

    def testResult(self):
        # Do garbage collection to ensure ent instances are cleaned up
        while gc.collect() > 0: pass

        # Expect instances to be collected if circular garbage collection works
        self.assertTrue(self.testent1_weakref() is None, msg='Ent1 should be garbage collected')
        self.assertTrue(self.testent2_weakref() is None, msg='Ent2 should be garbage collected')
