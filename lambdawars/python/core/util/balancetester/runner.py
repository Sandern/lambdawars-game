"""Utility routines for executing balance-test packages and producing reports."""
import gamemgr
from gamedb import dbgamepackages
from srcbuiltins import DictToKeyValues, RegisterPerFrameMethod, UnregisterPerFrameMethod
from kvdict import LoadFileIntoDictionaries
from gameinterface import ConVar, engine
import filesystem
import os
import traceback

from .balancetest import BalanceTest
from .reporter import WriteReport

balancetester_timescale = ConVar('balancetester_timescale', '5', 0)

balancetestfolder = 'scripts/balancetests'

balancetestsleft = []
balancetestsdone = []
balancetestsresults = []

def UpdateBalanceTest():
    """Advance the currently active balance test by one step per frame.

    Pops completed tests off the queue, performs cleanup, and triggers the
    end-of-run report once all queued tests have finished executing.
    """
    global balancetestsleft, balancetestsdone
    
    try:
        if not balancetestsleft:
            # End it
            EndBalanceTest()
            
            return
        
        activetest = balancetestsleft[0]
        if activetest.UpdateSteps():
            return
        
        print('Finish %s' % (activetest.filename))
        activetest.Cleanup()
        balancetestsdone.append(balancetestsleft.pop(0))
    except:
        traceback.print_exc()
        EndBalanceTest()
        

def RunBalanceTest(name, balancetestinfo):
    """Placeholder hook for running a named balance test package.

    The current implementation simply logs the package that would run; it can
    be extended to support ad-hoc execution or debugging of individual tests.
    """
    print('Running balance test package %s' % (name))
    

def EndBalanceTest():
    """Clean up after balance tests finish and emit the HTML report.

    Unregisters the per-frame runner, writes the aggregated HTML report, and
    restores the server timescale back to the default value.
    """
    # Unregister the updater
    UnregisterPerFrameMethod(UpdateBalanceTest)

    print('finished running balance tests')
    # Write report
    WriteReport(balancetestsdone)
    
    # Change back host timescale
    engine.ServerCommand('host_timescale 1\n')


def RunBalanceTester(singletest=''):
    """Queue balance tests, adjust timescale, and register the per-frame runner.

    Args:
        singletest (str): Optional filename within ``scripts/balancetests`` to
            run exclusively. When omitted, every definition file in the
            directory is processed.
    """
    global balancetestsleft, balancetestsdone
    
    balancetestsleft = []
    balancetestsdone = []
    
    # Build tests to run
    for filename in filesystem.ListDir(balancetestfolder):
        path = os.path.join(balancetestfolder, filename)
        if os.path.isdir(path):
            continue
        kv = LoadFileIntoDictionaries(path)
        if not kv:
            PrintWarning('%s is not a valid balance test file!\n' % (path))
            continue
        for testname, definition in kv.items():
            if singletest and filename != singletest:
                continue
            balancetestsleft.append(BalanceTest(filename, testname, definition))
        
    # Change host timescale
    engine.ServerCommand('host_timescale %d\n' % (balancetester_timescale.GetFloat()))
    
    # Start testing
    RegisterPerFrameMethod(UpdateBalanceTest)
