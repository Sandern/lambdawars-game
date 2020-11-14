import cProfile
import tracemalloc
from collections import defaultdict

from srcbuiltins import RegisterTickMethod
from gameinterface import engine, concommand, FCVAR_CHEAT
    
from core.usermessages import usermessage

if isserver:
    from utils import UTIL_IsCommandIssuedByServerAdmin

# Is profiling on?
profiling_on = False

prs = defaultdict(cProfile.Profile)

# Enable/disable
def StartProfiler(name):
    if profiling_on:
        prs[name].enable(True,True)

def EndProfiler(name):
    prs[name].disable()
    
# Decorator
def profile(name):
    """ Use this decorator to profile a method
    """
    def fnwrapper(fn):
        def fnwrapper2(*args):
            if profiling_on:
                StartProfiler(name)
                try:
                    rv = fn(*args)
                finally:
                    EndProfiler(name)
                return rv
            else:
                return fn(*args)
        return fnwrapper2
    return fnwrapper

# Print stats
def PrintStats(names):
    if type(names) != list:
        names = [names]
        
    for name in names:
        print('Printing stats for %s' % (name))
        try:
            prs[name].print_stats()
        except:
            print('No stats...')

def Reset(name):
    prs[name] = cProfile.Profile()

def ResetAll():
    global prs
    prs = defaultdict(cProfile.Profile)

def __cc_may_execute_command():
    return isclient or UTIL_IsCommandIssuedByServerAdmin()

@concommand('profiling_start' if isserver else 'cl_profiling_start', flags=FCVAR_CHEAT)
def cc_profiling_start(args):
    global profiling_on
    if not __cc_may_execute_command():
        return
    profiling_on = True

@concommand('profiling_stopandprint' if isserver else 'cl_profiling_stopandprint', flags=FCVAR_CHEAT)
def cc_profiling_stopandprint(args):
    global profiling_on
    if not __cc_may_execute_command():
        return
    profiling_on = False
    specific = None
    
    if len(args) > 1:
        specific = args[1]
        PrintStats(specific)
    else:
        for key in prs.keys():
            PrintStats(key)
    ResetAll()

profiling_timed = None

@concommand('profiling_run' if isserver else 'cl_profiling_run', flags=FCVAR_CHEAT)
def cc_profiling_run(args):
    global profiling_on, profiling_timed
    if not __cc_may_execute_command():
        return
    if profiling_on:
        print('profiling_run already running!')
        return
    profiling_on = True
    profiling_timed = None
    if len(args) > 1:
        profiling_timed = []
        for i in range(2, len(args)):
            profiling_timed.append(args[i])
    print('Profiling started (%f seconds)' % (float(args[1])))
    RegisterTickMethod(profiling_run_end, float(args[1]), looped=False)

def profiling_run_end():
    global profiling_on, profiling_timed
    profiling_on = False
    print('profiling done (%s): ' % ('client' if isclient else 'server'))
    for key in prs.keys():
        PrintStats(key)
    ResetAll()
    
# VProf, used by benchmark map
@usermessage('startvprof')
def StartVProf(*args, **kwargs):
    engine.ExecuteClientCmd('vprof_reset')
    engine.ExecuteClientCmd('vprof_on')

@usermessage('endvprof')
def EndVProf(*args, **kwargs):
    engine.ExecuteClientCmd('vprof_off')
    engine.ExecuteClientCmd('vprof_generate_report_hierarchy')
    engine.ExecuteClientCmd('vprof_generate_report')


@concommand('start_tracemalloc' if isserver else 'cl_start_tracemalloc', flags=FCVAR_CHEAT)
def StartTraceMalloc(*args, **kwargs):
    if not __cc_may_execute_command():
        return
    tracemalloc.start()

@concommand('end_tracemalloc' if isserver else 'cl_end_tracemalloc', flags=FCVAR_CHEAT)
def EndTraceMalloc(*args, **kwargs):
    if not __cc_may_execute_command():
        return
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    print("[ Top 10 ]")
    for stat in top_stats[:10]:
        print(stat)
    tracemalloc.stop()
