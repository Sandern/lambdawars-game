from srcbase import *
from . gametestsuite import GameTestSuite
from . gametestcase import GenericGameTestCase
from vmath import vec3_origin
from entities import CBaseEntity, entity
if isserver:
    from entities import DispatchSpawn
    from utils import UTIL_RemoveImmediate

def CreateEntHandlesTestSuite():
    suite = GameTestSuite()
    suite.addTest(EntHandlesTestCase())
    suite.addTest(EntHandlesNativeTestCase())
    return suite

class EntHandlesTestCase(GenericGameTestCase):
    def runTest(self):
        @entity('enthandles_testentity')
        class EntHandlesTestEntity(CBaseEntity):
            pass
            
        testent = self.CreateEntityByName('enthandles_testentity')
        testent.Spawn()
        
        testent = testent.Get()
        handle = testent.GetHandle()
        
        # Both testent and handle should be True
        self.assertTrue(bool(testent))
        self.assertTrue(bool(handle))
        
        # Neither testent or handle should equal None
        self.assertTrue(testent != None)
        self.assertTrue(handle != None)
        
        # The testent and handle should be equal
        self.assertTrue(handle == testent)
        # Should be equal to self
        self.assertTrue(handle == handle)
        self.assertTrue(testent == testent)
        
        enthandles_testset = set()
        enthandles_testset.add(testent)
        
        # The handle should return true for being in the list
        self.assertTrue(handle in enthandles_testset)
        
        # When adding the handle, it should do nothing
        enthandles_testset.add(handle)
        self.assertTrue(len(enthandles_testset) == 1)
        
        # Inverse same tests
        enthandles_testset.clear()
        enthandles_testset.add(handle)
        
        # The testent should return true for being in the list
        self.assertTrue(testent in enthandles_testset)
        
        # When adding the testent, it should do nothing
        enthandles_testset.add(testent)
        self.assertTrue(len(enthandles_testset) == 1)
        
        # After removing the testent, the handle should equal None and the testent evaluates False
        UTIL_RemoveImmediate(testent)
        self.assertFalse(bool(testent))
        self.assertTrue(handle == None)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred())

class EntHandlesNativeTestCase(GenericGameTestCase):
    def runTest(self):
        handle = self.CreateEntityByName( "prop_physics" ) # Always returns a handle
        handle.KeyValue('model', 'models/props_c17/oildrum001_explosive.mdl')
        handle.SetAbsOrigin(vec3_origin)
        DispatchSpawn( handle )
        handle.Activate()
        
        # Handle should evaluate to True
        self.assertTrue(bool(handle))
        # Should not be None
        self.assertTrue(handle != None)
        # Should be equal to self
        self.assertTrue(handle == handle)
        
        # After removing the handle, the handle should equal None and the handle evaluates False
        UTIL_RemoveImmediate(handle)
        self.assertFalse(bool(handle))
        self.assertTrue(handle == None)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred())
