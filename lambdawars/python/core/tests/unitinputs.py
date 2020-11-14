from srcbase import SOLID_BSP
from vmath import *
from srctests.gametestsuite import GameTestSuite
from . units import GenericGameUnitTestCase
from gamemgr import dblist
from vmath import vec3_origin
from playermgr import OWNER_NEUTRAL, OWNER_ENEMY, OWNER_LAST

if isserver:
    from utils import UTIL_RemoveImmediate
    from physics import ForcePhysicsSimulate, Physics_RunThinkFunctions
    from entities import CFuncBrush, g_EventQueue, variant_t, CreateEntityByName, DispatchSpawn
    from gameinterface import ServiceEventQueue

from core.units import CreateUnit

def CreateUnitInputsTestSuite():
    suite = GameTestSuite()
    # Should be good enough to test one unit
    suite.addTest(GenericGameUnitInputsTestCase(unitname='unit_combine'))
    return suite
    
class GenericGameUnitInputsTestCase(GenericGameUnitTestCase):
    def testSpawnUsingParameters(self, unitname, ownernumber):
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        target = CreateEntityByName('info_target')
        target.SetAbsOrigin(Vector(-512, 0, 0))
        target.KeyValue('targetname', 'targetent')
        DispatchSpawn(target)
        target.Activate()
        
        # Create and spawn the unit
        unit = self.OnUnitCreated(CreateUnit(unitname, vec3_origin, owner_number=ownernumber))
        self.assertIsNotNone(unit, msg=unitmsg)
        
        # Test order inputs
        value = variant_t()
        value.SetString('targetent')
        
        g_EventQueue.AddEvent( unit, "Order", value, 0, None, None )
        ServiceEventQueue()
        self.assertTrue(len(unit.orders) == 1, msg=unitmsg)
        g_EventQueue.AddEvent( unit, "QueueOrder", value, 0, None, None )
        ServiceEventQueue()
        self.assertTrue(len(unit.orders) == 2, msg=unitmsg)
        g_EventQueue.AddEvent( unit, "QueueOrder", value, 0, None, None )
        ServiceEventQueue()
        self.assertTrue(len(unit.orders) == 3, msg=unitmsg)
        g_EventQueue.AddEvent( unit, "CancelOrder", value, 0, None, None )
        ServiceEventQueue()
        self.assertTrue(len(unit.orders) == 2, msg=unitmsg)
        g_EventQueue.AddEvent( unit, "CancelAllOrders", value, 0, None, None )
        ServiceEventQueue()
        self.assertTrue(len(unit.orders) == 0, msg=unitmsg)
        
        # Test enable/disable sensing
        # TODO: Test if it actually works
        g_EventQueue.AddEvent( unit, "EnableSensing", value, 0, None, None )
        ServiceEventQueue()
        g_EventQueue.AddEvent( unit, "DisableSensing", value, 0, None, None )
        ServiceEventQueue()
        
        # Remove the unit. Handle should be None after removing.
        UTIL_RemoveImmediate(unit)
        self.assertTrue(unit == None, msg=unitmsg)
        
        UTIL_RemoveImmediate(target)
        self.assertTrue(target == None, msg=unitmsg)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred(), msg=unitmsg)
       
        
    def runTest(self):
        unitname = self.unitname
    
        self.testSpawnUsingParameters(unitname, OWNER_LAST)
        