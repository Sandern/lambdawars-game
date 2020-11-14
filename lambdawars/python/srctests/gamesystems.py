from __future__ import absolute_import

from srcbase import *
from . gametestsuite import GameTestSuite
from unittest.util import strclass
from . gametestcase import GenericGameTestCase
from gameinterface import AutoGameSystemPerFrame

import weakref

def CreateGameSystemTestSuite():
    suite = GameTestSuite()
    #suite.addTest(GameSystemTestCase())
    #suite.addTest(GameSystemCrashTestCase())
    return suite

class TestGameSystem1(AutoGameSystemPerFrame):
    def __init__(self, testcase):
        super(TestGameSystem1, self).__init__()
    
        self.testcase = testcase
        
    def FrameUpdatePostEntityThink(self):
        self.testcase.calledpostentitythink = True

class TestGameSystem2(AutoGameSystemPerFrame):
    def __init__(self, testcase):
        super(TestGameSystem2, self).__init__()
    
        self.testcase = testcase
        
    def FrameUpdatePostEntityThink(self):
        self.testcase.testgamesystems = None

class GameSystemTestCase(GenericGameTestCase):
    def __init__(self, *args, **kwargs):
        super(GameSystemTestCase, self).__init__(*args, **kwargs)
        
        self.calledpostentitythink = False

    def __str__(self):
        return "test GameSystemTestCase %s" % (strclass(self.__class__))
        
    def setUp(self):
        super(GameSystemTestCase, self).setUp()
        
        self.testsleft = [
            (self.testCreateGameSystem,),
            (self.testGameSystemResult,),
        ]
        
    def testCreateGameSystem(self):
        # Create a test auto game system
        self.testgamesystem = TestGameSystem1(self)
        self.testref = weakref.ref(self.testgamesystem)
        
        return 1.0
        
    def testGameSystemResult(self):
        # Clear auto game system
        self.testgamesystem = None
        
        # Test if Python instance is destroyed, since the ref count went zero
        # Note: it's ok to have lingering references around to the game system, but for this simple test we don't expect it.
        self.assertIsNone(self.testref())
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred())

class GameSystemCrashTestCase(GenericGameTestCase):
    def __init__(self, *args, **kwargs):
        super(GameSystemCrashTestCase, self).__init__(*args, **kwargs)
        
        self.testgamesystems = []
        
    def __str__(self):
        return "test GameSystemCrashTestCase %s" % (strclass(self.__class__))
        
    def runTest(self):
        # Create a number of game systems
        for i in range(0, 5):
            self.testgamesystems.append(TestGameSystem2(self))
        
        # The following will crash the game because all game systems are cleared from
        # within FrameUpdatePostEntityThink. This changes the game systems list, resulting
        # in a crash. See InvokePerFrameMethod in igamesystems.cpp
        self.SimulateServer(0.1)
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred())