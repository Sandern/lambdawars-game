from unittest import TestCase
from unittest.case import _Outcome

from . import excepthook

from entities import CreateEntityByName

if isserver:
    from entities import entlist, DispatchSpawn
    from utils import UTIL_RemoveImmediate

def TIME_TO_TICKS( dt ): 
    return ( int( 0.5 + float(dt) / gpGlobals.interval_per_tick ) )

class GameTestCase(TestCase):
    started = False
    success = False
    
    testsleft = None
    
    orig_result = None
    setupsuccess = False
    expecting_failure = None
    
    def startRun(self, result):
        self.orig_result = result
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()

        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)
        if (getattr(self.__class__, "__unittest_skip__", False) or
            getattr(testMethod, "__unittest_skip__", False)):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(testMethod, '__unittest_skip_why__', ''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        self.expecting_failure = getattr(testMethod,
                                    "__unittest_expecting_failure__", False)
        outcome = _Outcome(result)
        try:
            self._outcome = outcome

            with outcome.testPartExecutor(self):
                self.setUp()
            self.setupsuccess = outcome.success
            if outcome.success:
                outcome.expecting_failure = self.expecting_failure
        finally:
            pass
            
    def endRun(self, result):
        outcome = self._outcome
        try:
            if self.setupsuccess:
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    self.tearDown()

            self.doCleanups()
            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if self.expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if self.orig_result is None:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None
        
    def updateRun(self, result):
        testMethod = getattr(self, self._testMethodName)
        outcome = self._outcome
        
        try:
            if self.setupsuccess:
                with outcome.testPartExecutor(self, isTest=True):
                    ret = testMethod()
                    if ret != None:
                        return ret
        finally:
            pass
        
    def runTest(self):
        while self.testsleft:
            testargs = self.testsleft.pop(0)
            assert len(testargs) > 0
            testmethod = testargs[0]
            args = testargs[1] if len(testargs) > 1 else []
            kwargs = testargs[2] if len(testargs) > 2 else {}
                
            ret = testmethod(*args, **kwargs)
            if ret == None:
                continue # Next test method
            if ret > 0:
                return ret # Yield to game event loop

class GenericGameTestCase(GameTestCase):
    def setUp(self):
        super(GenericGameTestCase, self).setUp()
        
        excepthook.InstallCustomExceptHook()
        
        self.toActivateEntities = []
        self.cleanupEntities = []
        self.cleanupUnits = []
        
    def GetPositionByTargetName(self, targetname):
        target = entlist.FindEntityByName(None, targetname)
        if not target:
            raise Exception('target entity for %s is missing!' % (targetname))
        return target.GetAbsOrigin()
            
    def GetEntityByTargetName(self, targetname):
        target = entlist.FindEntityByName(None, targetname)
        if not target:
            raise Exception('target entity for %s is missing!' % (targetname))
        return target
        
    def OnEntityCreated(self, ent):
        if ent:
            self.cleanupEntities.append(ent)
        return ent
        
    def OnUnitCreated(self, unit):
        if unit:
            self.cleanupUnits.append(unit.GetHandle())
        return unit
        
    def CreateEntityByName(self, *args, **kwargs):
        return self.OnEntityCreated(CreateEntityByName(*args, **kwargs))
       
    def CreateEntity(self, entityname, keyvaluesmap):
        ent = self.CreateEntityByName(entityname)
        if not ent:
            raise Exception('Could not create entity %s!' % (entityname))
        for k, v in keyvaluesmap.items():
            ent.KeyValue(k, v)
        return ent
            
    def CreateAndSpawnEntity(self, entityname, keyvaluesmap, activate=True):
        ent = self.CreateEntity(entityname, keyvaluesmap)
        DispatchSpawn(ent)
        if activate:
            ent.Activate()
        return ent
            
    def CreateUnit(self, *args, **kwargs):
        from core.units import CreateUnit # FIXME
        return self.OnUnitCreated(CreateUnit(*args, **kwargs))
        
    def ActivateEntities(self):
        for ent in self.toActivateEntities:
            if not ent:
                continue
            ent.Activate()
        self.toActivateEntities = []
        
    def DoCleanupUnits(self, allowException=True):
        for unit in self.cleanupUnits + self.cleanupEntities:
            if not unit:
                continue
            if allowException:
                UTIL_RemoveImmediate(unit)
            else:
                try:
                    UTIL_RemoveImmediate(unit)
                except:
                    pass
        
    def tearDown(self):
        super(GenericGameTestCase, self).tearDown()
        
        excepthook.UninstallCustomExceptHook()
        
        self.DoCleanupUnits(False)
        
    def testExceptionOccurred(self):
        return excepthook.CheckExceptionOcurred()
