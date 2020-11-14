''' Util for testing balance '''
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
    print('Running balance test package %s' % (name))
    
def EndBalanceTest():
    # Unregister the updater
    UnregisterPerFrameMethod(UpdateBalanceTest)

    print('finished running balance tests')
    # Write report
    WriteReport(balancetestsdone)
    
    # Change back host timescale
    engine.ServerCommand('host_timescale 1\n')

def RunBalanceTester(singletest=''):
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
