from __future__ import absolute_import

from srcbase import *
from . gametestsuite import GameTestSuite
from unittest.util import strclass
from . gametestcase import GenericGameTestCase

from gamerules import CHL2WarsGameRules, GameRules, InstallGameRules

import weakref
import sys

def CreateGameRulesTestSuite():
    suite = GameTestSuite()
    suite.addTest(GameRulesTestCase())
    return suite

class GameRulesTestCase(GenericGameTestCase):
    unitname = None
    TestGameRules = None
    
    def __init__(self, *args, **kwargs):
        super(GameRulesTestCase, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "test GameRulesTestCase %s" % (strclass(self.__class__))
        
    def setUp(self):
        super(GameRulesTestCase, self).setUp()
        
        self.testsleft = [
            (self.testCreateGamerules,),
            (self.testRemoveGamerules,),
            (self.testCleanupGamerules,),
        ]
        
    def testCreateGamerules(self):
        class TestGameRules(CHL2WarsGameRules):
            pass
        self.TestGameRules = TestGameRules
            
        self.oldgamerules = None
        if GameRules():
            self.oldgamerules = type(GameRules())
            
        # Install our test gamerules
        InstallGameRules(TestGameRules)
        self.assertTrue(type(GameRules()) == TestGameRules)
        self.assertEqual(sys.getrefcount(GameRules()), 2) # One is hold by the global gamerules variable, and one is hold by getting the reference here.
        self.testref = weakref.ref(GameRules())
        return 0.1
        
    def testRemoveGamerules(self):
        # Deinstall our test gamerules
        InstallGameRules(self.oldgamerules)
        return 0.1
        
    def testCleanupGamerules(self):
        # Should no longer point to the TestGameRules type
        self.assertTrue(type(GameRules()) != self.TestGameRules)
        self.TestGameRules = None
        
        # Test if Python instance is destroyed, since the ref count went zero
        # Note: it's ok to have lingering references around to the gamerules, but for this simple test we don't expect it.
        self.assertIsNone(self.testref())
        
        # No exception should have occurred
        self.assertFalse(self.testExceptionOccurred())