from unittest import TestCase, TestSuite
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered, GetRegisteredTickMethods

def CreateRegisterMethodTestSuite():
    suite = TestSuite()
    suite.addTest(TickMethodTestCase())
    return suite

class TickMethodTestCase(TestCase):
    def runTest(self):
        def testTickMethod():
            pass
            
        # Register method and test if registered
        RegisterTickMethod(testTickMethod, 0.1)
        self.assertTrue(IsTickMethodRegistered(testTickMethod), msg='Method is not registered!')
        self.assertTrue(testTickMethod in GetRegisteredTickMethods(), msg='Method is not in the tick method list!')
        
        # TODO: Test if tick method runs. We will need to force an update the the game systems for this
        
        # Unregister method and test if no longer registered
        UnregisterTickMethod(testTickMethod)
        self.assertTrue(not IsTickMethodRegistered(testTickMethod), msg='Method is still registered!')
        self.assertTrue(testTickMethod not in GetRegisteredTickMethods(), msg='Method is still in the tick method list!')
