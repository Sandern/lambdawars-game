import sys
import os
import unittest
import types
from collections import defaultdict
import time
import pkgutil
import traceback

from gamemgr import dbgamepackages
from srcbuiltins import RegisterPerFrameMethod, UnregisterPerFrameMethod
from gameinterface import ConVar, concommand, FCVAR_CHEAT, AutoCompletion, engine
import filesystem as fs

from .gametestsuite import GameTestSuite
from .gamerunner import GameTextTestRunner

try:
    from coverage import coverage
except ImportError:
    coverage = None
    
suitefactories = defaultdict(list)

if isserver:
    py_tests_debug = ConVar('py_tests_debug', '0', 0)

def AutoDiscoverTestSuites():
    """ Collects all available test suites. """
    global suitefactories
    suitefactories.clear()

    checkmodules = []
    
    skipstartsymbol = '$' if isserver else '#'
    stripsymbol = '$#'
    gp = dbgamepackages['srctests']
    for testsuitename in gp.modules:
        if testsuitename.startswith(skipstartsymbol):
            continue
        testsuitename = testsuitename.lstrip(stripsymbol)
        modulename = '%s.%s' % (gp.name, testsuitename)
        
        # Find test suites in the srctests directory
        checkmodules.append((testsuitename, sys.modules[modulename]))
        
    # Find <gamepackage>.tests for each loaded game package
    for gamegp in dbgamepackages.values():
        if gamegp.name == 'srctests':
            continue
            
        # Add __init__.py from the gp tests
        modname = '%s.tests' % (gamegp.name)
        try:
            __import__(modname)
            modinst = sys.modules[modname]
            checkmodules.append((gamegp.name, modinst))
        except ImportError:
            continue
            
        # Add all sub modules (only one level)
        name = modinst.__name__
        path = modinst.__path__
        pathrel = []
        for v in path:
            if fs.IsAbsolutePath(v):
                v = fs.FullPathToRelativePath(os.path.normpath(v))
            pathrel.append(os.path.normpath(v))
            
        for item in pkgutil.iter_modules(pathrel):
            submod = '%s.%s' % (name, item[1])
            try:
                __import__(submod)
                checkmodules.append((submod, sys.modules[submod]))
            except ImportError:
                continue
            
    # Now check all modules for test suite create methods of the format Create<MyFancyTestName>TestSuite
    for testsuitename, modinst in checkmodules:
        for attrname in dir(modinst):
            if not attrname.startswith('Create') or not attrname.endswith('TestSuite'):
                continue
            fnsuite = getattr(modinst ,attrname)
            if not isinstance(fnsuite, types.FunctionType):
                continue
            suitefactories[testsuitename].append(fnsuite)
            
testsuitesleft = []
testresults = []
activerunner = None
runstarttime = 0.0
nextruntime = 0.0

count = 0

covrunner = None

def SetupTestRun(suitekeys):
    """ Setups a new test run.
    
        Also see RunTestIteration.
    """
    global testsuitesleft, testresults, activerunner, runstarttime, count, nextruntime, covrunner
    
    AutoDiscoverTestSuites()
    
    count = 0
    
    runstarttime = time.time()
    
    # Reset
    testsuitesleft = []
    testresults = []
    activerunner = None
    nextruntime = 0.0
    
    # Create all test suites
    if not suitekeys:
        suitekeys = suitefactories.keys()
        
    for key in suitekeys:
        if isserver and key.startswith('$'):
            continue
        elif isclient and key.startswith('#'):
            continue
            
        suitecreators = suitefactories[key]
        for fnsuite in suitecreators:
            testsuitesleft.append(fnsuite())
            
    # Start code coverage tool
    if coverage:
        covrunner = coverage()
        covrunner.start()
            
    if isserver:
        if not py_tests_debug.GetBool():
            # Run tests at 25x times the normal game speed
            engine.ServerCommand('host_timescale 25\n')
        else:
            engine.ServerCommand('host_timescale 1\n')

def RunTestIteration():
    """ Updates the current test run per frame.
    
        Test cases can return an amount of time to yield to the game, allowing the game
        to proceed (e.g. moving an unit).
    """
    global testsuitesleft, testresults, activerunner, nextruntime, count
    
    try:
        if nextruntime > gpGlobals.curtime:
            return
        
        while testsuitesleft:
            testsuite = testsuitesleft[0]
            
            if isinstance(testsuite, GameTestSuite):
                if not activerunner:
                    activerunner = GameTextTestRunner(verbosity=2)
                    activerunner.startRun(testsuite)
                ret = activerunner.updateRun()
                if ret != None:
                    nextruntime = gpGlobals.curtime + ret
                    return # Must wait
                testresult = activerunner.endRun()
                activerunner = None
            else:
                testresult = unittest.TextTestRunner(verbosity=2).run(testsuite)
        
            testresults.append(testresult)
            testsuitesleft.remove(testsuite)
        
            # Might not have enough edicts, so reuse between test suites (or even reuse between all test cases?)
            engine.AllowImmediateEdictReuse()
            
        FinishTestRun()
    except:
        traceback.print_exc()
        FinishTestRun()

def FinishTestRun():
    """ Clears all test variables, prints the test report and resets host_timescale. """
    global testsuitesleft, testresults, activerunner, runstarttime, covrunner
    
    UnregisterPerFrameMethod(RunTestIteration)
    
    if covrunner:
        covrunner.stop()
        covrunner.html_report()
        covrunner = None
        
    if isserver:
        engine.ServerCommand('host_timescale 1\n')

    totalcount = 0
    failurecount = 0
    errorcount = 0
    skippedcount = 0
    
    for testresult in testresults:
        totalcount += testresult.testsRun
        failurecount += len(testresult.failures)
        errorcount += len(testresult.errors)
        skippedcount += len(testresult.skipped)
            
    print('\n\n======================================================================')
    print('Finished running tests in %f seconds' % (time.time() - runstarttime))
    print('Total runned tests: %d' % (totalcount))
    print('Failures: %d' % (failurecount))
    print('Errors: %d' % (errorcount))
    print('Skipped: %d' % (skippedcount))
    
    # Print all errors again at the end
    if failurecount > 0 or errorcount > 0:
        PrintWarning('Errors or failures encountered during running tests:\n')
    
        for testresult in testresults:
            if testresult.wasSuccessful():
                continue
            testresult.printErrors()
            
        print('Total runned tests: %d' % (totalcount))
        print('Failures: %d' % (failurecount))
        print('Errors: %d' % (errorcount))
        print('Skipped: %d' % (skippedcount))

def RunTests(suitekeys):
    sys.argv = ['lambdawars']
    
    # Get all test suites
    SetupTestRun(suitekeys)
    
    # Install the runner, updating per game frame
    RegisterPerFrameMethod(RunTestIteration)

class TestsAutoCompletion(AutoCompletion):
    def __call__(self, partial):
        # Regenerate test suites on first key
        if not suitefactories or not partial.replace('py_run_tests ', ''):
            AutoDiscoverTestSuites()
        return super().__call__(partial)

@concommand('py_run_tests' if isserver else 'cl_py_run_tests', flags=FCVAR_CHEAT, completionfunc=TestsAutoCompletion(lambda: suitefactories.keys()), 
            helpstring='Runs unit tests. Leave arguments empty to run all available test suites. Note: after the tests are completed, the map becomes invalid.')
def PyRunTests(args):
    RunTests(args.ArgS().split())

@concommand('py_stop_tests' if isserver else 'cl_py_stop_tests', flags=FCVAR_CHEAT)
def PyStopTests(args):
    FinishTestRun()
