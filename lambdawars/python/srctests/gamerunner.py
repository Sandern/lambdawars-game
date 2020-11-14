from unittest import TextTestRunner
from unittest.signals import registerResult

import time

class GameTextTestRunner(TextTestRunner):
    result = None
    startTime = None
    
    activeTest = None
    
    def startRun(self, test):
        self.result = self._makeResult()
        registerResult(self.result)
        self.result.failfast = self.failfast
        self.result.buffer = self.buffer
        self.startTime = time.time()
        startTestRun = getattr(self.result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
            
        self.activeTest = test
        
    def endRun(self):
        self.activeTest = None
        
        stopTime = time.time()
        timeTaken = stopTime - self.startTime
        
        result = self.result
        result.printErrors()
        if hasattr(result, 'separator2'):
            self.stream.writeln(result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()

        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write("FAILED")
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
        else:
            self.stream.write("OK")
        if skipped:
            infos.append("skipped=%d" % skipped)
        if expectedFails:
            infos.append("expected failures=%d" % expectedFails)
        if unexpectedSuccesses:
            infos.append("unexpected successes=%d" % unexpectedSuccesses)
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            self.stream.write("\n")
            
        return result
        
    def updateRun(self):
        if not self.activeTest:
            return None
    
        result = self.result
        
        ret = None
        try:
            if not self.activeTest.started:
                self.activeTest.startRun(result)
                self.activeTest.started = True
            ret = self.activeTest.updateRun(result)
        finally:
            if ret == None:
                try:
                    self.activeTest.endRun(result)
                    
                    stopTestRun = getattr(result, 'stopTestRun', None)
                    if stopTestRun is not None:
                        stopTestRun()
                except:
                    return None
        return ret
    
    def run(self, test):
        assert False, 'wrong usage'