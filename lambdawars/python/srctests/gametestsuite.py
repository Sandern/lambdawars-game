from unittest import TestSuite

class GameTestSuite(TestSuite):
    """ GameTestSuite is an extension to TestSuite, which allows Test Cases to yield
        time to the game engine. This allows the game to run while the test case state
        is frozen.
        
        Each test case in the suite must of the type GameTestCase.
    """
    started = False
    topLevel = False
    
    def __init__(self, suitename=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.name = suitename
    
    def startRun(self, result):
        self.topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = self.topLevel = True
            
        self.testsleft = list(self)
        
    def updateRun(self, result):
        while self.testsleft:
            test = self.testsleft[0]
            
            if result.shouldStop:
                break

            if _isnotsuite(test):
                self._tearDownPreviousClass(test, result)
                self._handleModuleFixture(test, result)
                self._handleClassSetUp(test, result)
                result._previousTestClass = test.__class__

                if (getattr(test.__class__, '_classSetupFailed', False) or
                    getattr(result, '_moduleSetUpFailed', False)):
                    continue

            #if not debug:
            if not test.started:
                test.startRun(result)
                test.started = True
                
            ret = test.updateRun(result)
            #else:
            #    test.debug()
            if ret == None:
                test.endRun(result)
                self.testsleft.remove(test)
            else:
                return ret # Yielding to game loop
                
    def endRun(self, result):
        if self.topLevel:
            self._tearDownPreviousClass(None, result)
            self._handleModuleTearDown(result)
            result._testRunEntered = False
    
    def run(self, result, debug=False):
        assert False, 'wrong usage'

def _isnotsuite(test):
    "A crude way to tell apart testcases and suites with duck-typing"
    try:
        iter(test)
    except TypeError:
        return True
    return False