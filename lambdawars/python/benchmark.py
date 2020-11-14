from srcbuiltins import RegisterTickMethod, UnregisterTickMethod
from vmath import Vector
import profiler
from profiler import StartVProf, EndVProf
from gameinterface import ConCommand, FCVAR_GAMEDLL, FCVAR_CHEAT, ConVarRef, engine, AsyncFinishAllWrites
from utils import UTIL_PlayerByIndex
from core.units import unitlist
from entities import MouseTraceData
from playermgr import SimulatedPlayer

import time
import os
from datetime import datetime

sv_cheats = ConVarRef('sv_cheats')
sv_fogofwar = ConVarRef('sv_fogofwar')
unit_nodamage = ConVarRef('unit_nodamage')
unit_ai_disable = ConVarRef('unit_ai_disable')
unit_navigator_eattest = ConVarRef('unit_navigator_eattest')

benchmarkfolder = 'benchmarks'
if not os.path.isdir(benchmarkfolder):
    os.mkdir(benchmarkfolder)
    
# The benchmark
if isserver:
    from core.units import CreateUnitNoSpawn, CreateUnitsInArea
    from core.signals import map_clientactive

    class Benchmark(object):
        def __call__(self, *args, **kwargs):
            self.StartBenchmark()
        
        def StartBenchmark(self):
            sv_cheats.SetValue(True)
            sv_fogofwar.SetValue(False)
            #unit_navigator_eattest.SetValue(True)
            
            self.player = UTIL_PlayerByIndex(1)
            profiler.profiling_on = True
            StartVProf()
            timestamp = datetime.now()
            engine.ClientCommand(self.player, 'con_logfile %s/%s_%s-%s-%s_%s-%s-%s.txt' % (benchmarkfolder, self.name, 
                timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second))
                
            if self.delayinit:
                RegisterTickMethod(self.InitBenchmark, self.delayinit, False)
            else:
                self.InitBenchmark()
            
        def EndBenchmark(self):
            profiler.profiling_on = False
            profiler.PrintStats(self.print_stats)
            profiler.ResetAll()
            EndVProf()
            engine.ServerExecute()
            AsyncFinishAllWrites()
            engine.ClientCommand(self.player, 'con_logfile ""')

            self.CleanupBenchmark()

        # For overriding
        def InitBenchmark(self): pass
        def CleanupBenchmark(self): pass
        
        name = 'Benchmark'
        print_stats = []
        delayinit = None
            
    # Spawn benchmarks
    spawning_benchmarks = {
        'AntlionsLow' : ('unit_antlion', 100),
        'Antlions' : ('unit_antlion', 200),
        'AntlionsHigh' : ('unit_antlion', 400),
        'CombineOne' : ('unit_combine', 1),
        'Combine' : ('unit_combine', 200),
        'CombineHigh' : ('unit_combine', 400),
    }
    class SpawningBenchmark(Benchmark):
        def __init__(self, name):
            self.name = 'Spawning%s_%s' % (spawning_benchmarks[name][1], name)
            self.benchmark = spawning_benchmarks[name]
            
        def InitBenchmark(self):
            origin1 = Vector(0, -320, 12.0)
            origin2 = Vector(0, 320, 12.0)
            
            mins = -Vector(512, 128, 0)
            maxs = Vector(512, 128, 64)
            
            profiler.StartProfiler('SpawningUnits')
            CreateUnitsInArea(self.benchmark[0], origin1, mins, maxs, 12.0, self.benchmark[1], 2)
            profiler.EndProfiler('SpawningUnits')
            
            self.EndBenchmark()

        print_stats = ['SpawningUnits']
        
    # Units fighting benchmarks 
    fighting_benchmarks = {
        'AntlionsLow' : ('unit_antlion', 100),
        'Antlions' : ('unit_antlion', 200),
        'CombineLow50' : ('unit_combine', 50),
        'CombineMed' : ('unit_combine', 100),
        'Combine' : ('unit_combine', 200),
        'Stalker' : ('unit_stalker', 5),
        
        'AntlionMix' : (['unit_antlion', 'unit_antlionworker', 'unit_antlionguard'], 200),
        'AllMix' : (['unit_antlion', 'unit_antlionworker', 'unit_antlionguard', 'unit_combine', 'unit_rebel', 'unit_vortigaunt', 'unit_hunter', 'unit_headcrab', 'unit_metropolice', 'unit_stalker'], 200),
        'Vortigaunt' : ('unit_vortigaunt', 50),
    }
    
    class FightingBenchmark(Benchmark):
        def __init__(self, name):
            self.name = 'Fighting%d_%s' % (fighting_benchmarks[name][1], name)
            self.benchmark = fighting_benchmarks[name]
            
        def InitBenchmark(self):
            unit_nodamage.SetValue(True)
            
            origin1 = Vector(0, -320, 12.0)
            origin2 = Vector(0, 320, 12.0)
            
            mins = -Vector(512, 128, 0)
            maxs = Vector(512, 128, 64)
            
            CreateUnitsInArea(self.benchmark[0], origin1, mins, maxs, 12.0, self.benchmark[1], 2)
            CreateUnitsInArea(self.benchmark[0], origin2, mins, maxs, 12.0, self.benchmark[1], 3)
            
            RegisterTickMethod(self.EndBenchmark, 10.0, False)
            
        def CleanupBenchmark(self):
            unit_nodamage.SetValue(False)
            
        print_stats = ['ServerUnits', 'StalkerLaserThink']
        
      
    # Moving benchmarks
    moving_benchmarks = {
        'Combine' : ('unit_combine', 400),
    }
    
    class MovingBenchmark(Benchmark):
        def __init__(self, name):
            self.name = 'OrderMove%d_%s' % (moving_benchmarks[name][1], name)
            self.benchmark = moving_benchmarks[name]
            
        def InitBenchmark(self):
            origin1 = Vector(0, -1024, 12.0)
            movetarget = Vector(0, 1024, 12.0)
            
            mins = -Vector(700, 256, 0)
            maxs = Vector(700, 256, 64)
            
            data = MouseTraceData()
            data.groundendpos = movetarget
            data.endpos = movetarget
            
            simulatedplayer = SimulatedPlayer(2, data, leftmousepressed=data, leftmousereleased=data)

            units = CreateUnitsInArea(self.benchmark[0], origin1, mins, maxs, 12.0, self.benchmark[1], 2)
            for unit in units:
                simulatedplayer.AddUnit(unit)
                
            simulatedplayer.OrderUnits()
            
            RegisterTickMethod(self.EndBenchmark, 5.0, False)
            
        print_stats = ['ServerUnits']
        
    class OrderStressBenchmark(Benchmark):
        def __init__(self, name):
            self.name = 'OrderStress%d_%s' % (moving_benchmarks[name][1], name)
            self.benchmark = moving_benchmarks[name]
            
        def InitBenchmark(self):
            origin1 = Vector(0, -1024, 12.0)
            movetarget = Vector(0, 1024, 12.0)
            
            mins = -Vector(700, 256, 0)
            maxs = Vector(700, 256, 64)
            
            data = MouseTraceData()
            data.groundendpos = movetarget
            data.endpos = movetarget
            
            
            simulatedplayer = SimulatedPlayer(2, data, leftmousepressed=data, leftmousereleased=data)

            units = CreateUnitsInArea(self.benchmark[0], origin1, mins, maxs, 12.0, self.benchmark[1], 2)
            for unit in units:
                simulatedplayer.AddUnit(unit)
                
            data.ent = units[0]
                
            t = time.time()
            for i in range(0, 200):
                simulatedplayer.OrderUnits()
            print('%f' % (time.time() - t))
            self.EndBenchmark()
            
        print_stats = ['ServerUnits', 'OrderUnit', 'grouporder_apply']
        delayinit = 2.0
                
    # Stress benchmark
    class StressBenchmark(Benchmark):
        def __init__(self, name):
            self.name = 'StressTest%d_%s' % (fighting_benchmarks[name][1], name)
            self.benchmark = fighting_benchmarks[name]
            
        def InitBenchmark(self):
            self.origin1 = Vector(0, -320, 12.0)
            self.origin2 = Vector(0, 320, 12.0)
            
            self.mins = -Vector(512, 128, 0)
            self.maxs = Vector(512, 128, 64)

            RegisterTickMethod(self.Update, 0.1, True)
            
        def Update(self):
            tospawn = self.benchmark[1] - len(unitlist[2])
            if tospawn > 0:
                CreateUnitsInArea(self.benchmark[0], self.origin1, self.mins, self.maxs, 12.0, tospawn, 2)
            tospawn = self.benchmark[1] - len(unitlist[3])
            if tospawn > 0:
                CreateUnitsInArea(self.benchmark[0], self.origin2, self.mins, self.maxs, 12.0, tospawn, 3)
                
        def CleanupBenchmark(self):
            UnregisterTickMethod(self.Update)
            
        print_stats = ['ServerUnits', 'OrderUnit']
            
        
    map_clientactive[__name__].disconnect(dispatch_uid='benchmark')
    
    map_clientactive[__name__].connect( FightingBenchmark('Antlions'), weak=False, dispatch_uid='benchmark' )
    #map_clientactive[__name__].connect( SpawningBenchmark('CombineHigh'), weak=False, dispatch_uid='benchmark' )
    #map_clientactive[__name__].connect( MovingBenchmark('Combine'), weak=False, dispatch_uid='benchmark' )
    #map_clientactive[__name__].connect( OrderStressBenchmark('Combine'), weak=False, dispatch_uid='benchmark' )
    #map_clientactive[__name__].connect( StressBenchmark('AllMix'), weak=False, dispatch_uid='benchmark' )
    