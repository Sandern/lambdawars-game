from unittest import TestSuite, TestCase

from entities import entity, CBaseEntity, PyHandle
from _srctests import SrcPyTest_EntityArg, SrcPyTest_ExtractEntityArg

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_RemoveImmediate

# A test python entity we can use.
@entity('testpythonent')
class TestPythonEnt(CBaseEntity):
    pass   
    
# Add all tests
def CreateConverterTestSuite():
    suite = TestSuite()
    suite.addTest(EntityConverterTestCase('test_nonearg'))
    suite.addTest(EntityConverterTestCase('test_validpythonentity'))
    suite.addTest(EntityConverterTestCase('test_removedpythonentity'))
    suite.addTest(EntityConverterTestCase('test_nonehandlearg'))
    suite.addTest(EntityConverterTestCase('test_validpythonhandle'))
    suite.addTest(EntityConverterTestCase('test_removedpythonhandle'))
    
    suite.addTest(EntityConverterTestCase('test_extractentity'))
    suite.addTest(EntityConverterTestCase('test_extractnonhandle'))
    return suite

class EntityConverterTestCase(TestCase):
    """ Test functions related to entity converting """
    
    if isserver:
        def CreateTestEntity(self):
            return CreateEntityByName('testpythonent')
        def RemoveTestEntity(self, arg):
            UTIL_RemoveImmediate(arg)
        def SpawnEntity(self, arg):
            DispatchSpawn(arg)
    else:
        def CreateTestEntity(self):
            ent = TestPythonEnt()
            ent.InitializeAsClientEntity(None, False)
            return ent.GetHandle()
        def RemoveTestEntity(self, arg):
            arg.Remove()
        def SpawnEntity(self, arg):
            arg.Spawn()
            
    def setUp(self):
        pass

    # Arguments tests
    def test_nonearg(self):
        SrcPyTest_EntityArg(None)
        
    def test_validpythonentity(self):
        arg = self.CreateTestEntity().Get()
        self.assertTrue(type(arg) == TestPythonEnt)
        self.SpawnEntity(arg)
        self.assertTrue(SrcPyTest_EntityArg(arg))
        self.RemoveTestEntity(arg)
        
    def test_removedpythonentity(self):
        arg = self.CreateTestEntity().Get()
        self.assertTrue( type(arg) == TestPythonEnt )
        self.SpawnEntity(arg)
        self.RemoveTestEntity(arg)
        # Note: entity is not valid anymore, but entity exists as long as Python
        # holds a reference. However usually we always work with handles.
        self.assertTrue(SrcPyTest_EntityArg(arg))
        
    def test_nonehandlearg(self):
        SrcPyTest_EntityArg(PyHandle(None))
        
    def test_validpythonhandle(self):
        arg = self.CreateTestEntity()
        self.assertTrue( type(arg) == PyHandle )
        self.SpawnEntity(arg)
        self.assertTrue(SrcPyTest_EntityArg(arg))
        self.RemoveTestEntity(arg)
        
    def test_removedpythonhandle(self):
        arg = self.CreateTestEntity()
        self.assertTrue( type(arg) == PyHandle )
        self.SpawnEntity(arg)
        self.RemoveTestEntity(arg)
        self.assertFalse(SrcPyTest_EntityArg(arg))
        
    # Extract tests
    def test_extractentity(self):
        arg = self.CreateTestEntity().Get()
        self.assertTrue(type(arg) == TestPythonEnt)
        self.SpawnEntity(arg)
        self.assertTrue(SrcPyTest_ExtractEntityArg(arg))
        self.RemoveTestEntity(arg)
        
    def test_extractnonhandle(self):
        self.assertFalse(SrcPyTest_ExtractEntityArg(PyHandle(None)))
