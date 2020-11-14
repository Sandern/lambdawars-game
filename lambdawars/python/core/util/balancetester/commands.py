from gameinterface import concommand, AutoCompletion, FCVAR_CHEAT
from .runner import RunBalanceTester

import filesystem

def BalanceTestFolderFilter(folder):
    return folder != '.' and folder != '..'

@concommand('balancetester_run', flags=FCVAR_CHEAT,
            completionfunc=AutoCompletion(lambda: filter(BalanceTestFolderFilter, filesystem.ListDir('scripts/balancetests'))))
def BalanceTesterRun(args):
    RunBalanceTester(args[1])
