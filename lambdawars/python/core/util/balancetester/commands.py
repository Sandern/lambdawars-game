"""Console commands for launching balance tester runs from the server."""
from gameinterface import concommand, AutoCompletion, FCVAR_CHEAT
from .runner import RunBalanceTester

import filesystem

def BalanceTestFolderFilter(folder):
    return folder != '.' and folder != '..'

@concommand('balancetester_run', flags=FCVAR_CHEAT,
            completionfunc=AutoCompletion(lambda: filter(BalanceTestFolderFilter, filesystem.ListDir('scripts/balancetests'))))
def BalanceTesterRun(args):
    """Run the balance tester for the provided script folder.

    Args:
        args: Command arguments from the engine. ``args[1]`` is expected to
            be the name of the directory inside ``scripts/balancetests`` that
            contains the YAML/definition files to execute.
    """
    RunBalanceTester(args[1])
