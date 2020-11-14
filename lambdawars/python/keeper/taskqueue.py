from core.units import unitlistpertype

from gamerules import gamerules
from gameinterface import engine, ConVar, FCVAR_CHEAT, concommand
from vprof import vprofcurrentprofilee
from profiler import profile
from _navmesh import NavMeshGetPathDistance
from .common import nearestkeybydist
from core.dispatch import receiver
from .signals import updatealltasks
from utils import UTIL_ListPlayersForOwnerNumber

import random
from collections import defaultdict
import bisect

if isserver:
    from core.signals import resourceupdated
    
    dk_taskqueue_showowner = ConVar('dk_taskqueue_showowner', '-1', FCVAR_CHEAT)
else:
    from core.signals import FireSignalRobust, refreshhud

class Task(object):
    def __init__(self, taskqueue, type, maximps=1, key=None, tile=None):
        super().__init__()
        
        self.taskqueue = taskqueue
        self.type = type
        self.maximps = maximps
        self.key = key
        self.tile = tile
        
        self.imps = []
        
    def GetTile(self):
        return self.taskqueue.keeperworld.tilegrid[self.key]
        
    def AcceptTask(self, imp):
        self.imps.append(imp.GetHandle())
        self.UpdateTaskAvailability()
        
    def IsTaskAvailable(self):
        return self.maximps != len(self.imps)
                    
    def UpdateTaskAvailability(self):
        taskqueue = self.taskqueue
        if self not in taskqueue.tasks:
            return # We were completed, don't insert again!
            
        self.imps = [_f for _f in self.imps if _f]
        if not self.IsTaskAvailable():
            if self.key in taskqueue.keytofreetasks:
                try: taskqueue.keytofreetasks[self.key].remove(self)
                except ValueError: pass
                if not taskqueue.keytofreetasks[self.key]:
                    del taskqueue.keytofreetasks[self.key] # Don't want empty entries
        else:
            if self not in taskqueue.keytofreetasks[self.key]:
                taskqueue.keytofreetasks[self.key].append(self)
                    
    def IsTaskDone(self):
        # Called when the imp says it`s done with the task (could for example decide to do something else).
        return True
        
    def DeleteTaskIfDone(self):
        if self.IsTaskDone(): self.taskqueue.DeleteTask(self)
        
    def TestCanImpDo(self, imp):
        return True
        
# Different task types
class TaskClaimTile(Task):
    def IsTaskDone(self):
        tilegrid = self.taskqueue.keeperworld.tilegrid
        tile = tilegrid[self.key]
        if tile.type != 'ground' and tile.GetOwnerNumber() == self.taskqueue.ownernumber:
            return True
        return False
        
class TaskDig(Task):
    def IsTaskDone(self):
        taskqueue = self.taskqueue
        ownernumber = taskqueue.ownernumber
        tilegrid = taskqueue.keeperworld.tilegrid
        tile = tilegrid[self.key]
        if not self.tile or tile != self.tile or (ownernumber > 1 and ownernumber not in self.tile.selectedbyplayers):
            return True
        return False
        
    def TestCanImpDo(self, imp):
        block = self.GetTile()
        return block and block.IsReachable(imp)
        
class TaskFortify(Task):
    def IsTaskDone(self):
        tile = self.GetTile()
        if tile == self.tile and not tile.fortified:
            return False
        return True
        
class TaskPickupGold(Task):
    def IsTaskDone(self):
        if not self.gold:
            #print('Gold task done, no gold handle. key: %s, tile: %s' %(str(self.key), str(self.tile)))
            return True
        taskqueue = self.taskqueue
        treasuretile = self.gold.treasuretile
        if not treasuretile or treasuretile.GetOwnerNumber() != taskqueue.ownernumber:
            return False
        #print('Gold task done, in treasure room. key: %s, tile: %s' %(str(self.key), str(self.tile)))
        return True
        
    def TestCanImpDo(self, imp):
        tq = self.taskqueue
        tile = self.GetTile()
        return tq.totalgold < tq.maxtotalgold and tile and tile.IsReachable(imp)
        
    def IsTaskAvailable(self):
        tq = self.taskqueue
        return tq.totalgold < tq.maxtotalgold and super(TaskPickupGold, self).IsTaskAvailable()
        
# Task manager
class TaskQueue(object):
    ownernumber = 0
    
    istreasurefull = False
    waitingforgoldroom = False
    didnotreasureroom = False
    totalgold = 0
    maxtotalgold = 0
    
    def __init__(self):
        super(TaskQueue, self).__init__()
        
        self.keeperworld = gamerules.keeperworld
        
        self.Init()
        
    def Init(self):
        self.freeimps = [] # List of idling imps
        self.tasks = [] # List of ALL tasks
        self.keytotasks = defaultdict(list) # Dictionary with keys to lists of tasks
        self.keytofreetasks = defaultdict(list) # Dictionary with keys to lists of free tasks

    # ==== Imp Management ====
    def FindNearestFreeImp(self, key, freeimps=None):
        ''' Returns the nearest free imp for the given key. '''
        if not freeimps: freeimps = self.freeimps
        impkeys = [imp.key for imp in freeimps]
        nearestkey = nearestkeybydist(key, impkeys)
        return freeimps[impkeys.index(nearestkey)]
    
    def OnImpFree(self, imp, task=None):
        ''' Adds a creature to the list of free creatures available to perform tasks from this queue.
            If a task is specified, it will also clear that task if it fullfills the "task done" conditions.
        '''
        if task: 
            if task.IsTaskDone(): 
                self.DeleteTask(task)
            else:
                try: task.imps.remove(imp.GetHandle()) # Imp just wanted to be removed
                except ValueError: PrintWarning('OnImpFree: imp #%d not doing this task!\n' % (imp.entindex()))
                task.UpdateTaskAvailability()
    
        h = imp.GetHandle()
        if h not in self.freeimps:
            self.freeimps.append(h)
            
    def OnImpExecutingTask(self, imp):
        ''' Called when a creature accepts doing a task. 
            Removes the creature from the free list.
        '''
        try:
            self.freeimps.remove(imp.GetHandle())
        except ValueError:
            PrintWarning('OnImpExecutingTask: imp not in free list\n')

    def OnImpRemoved(self, imp):
        ''' Called when a creature now longer wants to be in the free list.
            Used for cleaning up.
        '''
        try:
            self.freeimps.remove(imp.GetHandle())
        except ValueError:
            PrintWarning('Creature #%d not in the free creature list.\n' % (imp.entindex()))
  
    # ==== Task Insertion/Deletion ====
    def InsertTask(self, task):
        if task in self.tasks:
            raise Exception('Task %s already exists' % (str(task)))
        self.tasks.append(task)
        if task.key:
            self.keytotasks[task.key].append(task)
            self.keytofreetasks[task.key].append(task)
            
        self.FindImpForTask(task)
            
    def DeleteTask(self, task):
        if task not in self.tasks:
            return
        self.tasks.remove(task)
        if task.key:
            self.keytotasks[task.key].remove(task)
            if not self.keytotasks[task.key]:
                del self.keytotasks[task.key] # Don't want empty entries
                
            if task.key in self.keytofreetasks:
                try: self.keytofreetasks[task.key].remove(task)
                except ValueError: pass
                if not self.keytofreetasks[task.key]:
                    del self.keytofreetasks[task.key] # Don't want empty entries
                    
        for imp in task.imps:
            if not imp:
                continue
            imp.DispatchEvent('OnTaskDeleted', task)
            
    def UpdateAllTaskAvailability(self):
        [t.UpdateTaskAvailability() for t in self.tasks]
                    
    def HasTaskWithTile(self, tile, type=''):
        for t in self.tasks:
            if type:
                if t.type == type and t.tile == tile:
                    return True
            else:
                if t.tile == tile:
                    return True
        return False
        
    def CancelTasksWithTile(self, tile, type=''):
        for t in list(self.tasks):
            if type:
                if t.type == type and t.tile == tile:
                    self.DeleteTask(t)
            else:
                if t.tile == tile:
                    self.DeleteTask(t)
                
    def FindNearestTasks(self, key, taskkeys):
        nearestkey = nearestkeybydist(key, taskkeys)
        return self.keytofreetasks[nearestkey], nearestkey
    
    def InsertClaimTileTask(self, tile):
        assert(tile)
        for t in self.tasks:
            if t.tile == tile:
                return
        task = TaskClaimTile(self, 'claimtile', maximps=1, key=tile.key, tile=tile)
        self.InsertTask(task)
        return task
        
    def InsertDigWallTask(self, block):
        assert(block)
        if self.HasTaskWithTile('dig', block):
            return
        self.CancelTasksWithTile(block, type='fortify') # Remove any fortify task
        task = TaskDig(self, 'dig', maximps=3, key=block.key, tile=block)
        self.InsertTask(task)
        return task
        
    def RemoveDigWallTask(self, block):
        # Remove any task related to this tile
        # Active imps will decide themselves to stop
        self.CancelTasksWithTile(block, type='dig')
                
    def InsertPickupGoldTask(self, gold):
        assert(gold)
        
        kw = self.keeperworld
        key = kw.GetKeyFromPos(gold.GetAbsOrigin())
        tile = kw.tilegrid[key]
        if not tile or tile.isblock or not tile.walkabletile:
            PrintWarning('InsertPickupGoldTask: trying to insert gold task at an invalid position!\n')
            return
        
        for task in self.tasks:
            try:
                if task.gold == gold:
                    return # Already inserted
            except AttributeError:
                continue
    
        task = TaskPickupGold(self, 'getgold', maximps=1, key=key)
        task.gold = gold
        self.InsertTask(task)
        return task
        
    def RemoveTasksWithGold(self, gold):
        for t in list(self.tasks):
            try:
                if t.gold == gold:
                    self.DeleteTask(t)
                    break
            except AttributeError:
                pass
        
    def InsertFortifyTask(self, block):
        assert(block)
        if self.HasTaskWithTile(block, type='fortify'):
            return
        task = TaskFortify(self, 'fortify', maximps=1, key=block.key, tile=block)
        self.InsertTask(task)

    def OnTileRemoved(self, tile):
        # Remove any task related to this tile
        # Active imps will decide themselves to stop or listen to the task delete event.
        for i in range(len(self.tasks)-1, -1, -1):
            if self.tasks[i].tile == tile:
                self.DeleteTask(self.tasks[i])
                
    # Resource events
    def UpdateMaxGold(self):
        players = UTIL_ListPlayersForOwnerNumber(self.ownernumber)
        for player in players:
            player.maxgold = self.maxtotalgold
    
    @profile('TaskQueueUpdate')
    def SetCurrentGold(self, totalgold, maxtotalgold):
        maxgoldchanged = self.maxtotalgold != maxtotalgold

        self.totalgold = totalgold
        self.maxtotalgold = maxtotalgold
            
        # Need to tell imps to start doing gold tasks again
        if self.istreasurefull and self.totalgold < self.maxtotalgold:
            self.UpdateAllTaskAvailability()
            self.UpdateAllTasks()
            self.istreasurefull = False
        elif not self.istreasurefull and self.totalgold >= self.maxtotalgold:
            self.UpdateAllTaskAvailability()
            self.istreasurefull = True
            
        if maxgoldchanged: self.UpdateMaxGold()
            
    def IsTreasureFull(self):
        return self.totalgold >= self.maxtotalgold
            
    def NoTreasureRoom(self, unit): # TODO: Move somewhere else
        if not self.didnotreasureroom:
            unit.EmitAmbientSound(-1, unit.GetAbsOrigin(), 'Rooms.BuildTreasureRoom')
            self.didnotreasureroom = True
        
    def OnResourceUpdated(self):
        pass

    # ==== Main update loop ====
    debuglastmaxtask = 0
    @profile('TaskQueueUpdate')
    def Update(self):
        vprofcurrentprofilee.EnterScope("TaskQueueUpdate", 0, "TaskQueueUpdate", False)
        
        # NOTE: Only update when imps return the task
        '''
        # Update tasks
        for task in list(self.tasks):
            if task.IsTaskDone():
                self.DeleteTask(task)
        '''
        
        # Show debug if the player wants it
        if dk_taskqueue_showowner.GetInt() == self.ownernumber:
            totalimps = unitlistpertype[self.ownernumber]['unit_imp']
            nbusyimps = len(totalimps) - len(self.freeimps)
            engine.Con_NPrintf(0, 'Busy imps: %d, Free imps: %d, Tasks: %d, Free tasks: %d' % (nbusyimps, len(self.freeimps), len(self.tasks), len(self.keytofreetasks)))

            for i in range(0, max(self.debuglastmaxtask, len(self.tasks))):
                if i < len(self.tasks):
                    t = self.tasks[i]
                    engine.Con_NPrintf(i+1, 'Task "%s" at %s, imps: %d, tile: %s' % 
                                            (t.type, str(t.key), len(t.imps), str(t.tile.type if t.tile else 'None')))
                else:
                    engine.Con_NPrintf(i+1, '')
            self.debuglastmaxtask = len(self.tasks)
            
        if not self.freeimps or not self.tasks or not list(self.keytofreetasks.keys()):
            vprofcurrentprofilee.ExitScope()
            return
            
        t = random.sample(self.tasks, 1)[0]
        if self.FindImpForTask(t):
            PrintWarning('Found imp for task %s\n' % (str(t)))
        #self.UpdateAllTasks()

        vprofcurrentprofilee.ExitScope()
        
    def UpdateAllTasks(self):
        ''' Try to assign tasks to all free imps. '''
        [self.FindTaskForImp(imp) for imp in self.freeimps]
        
    def GetImpsForTask(self, task):
        ''' Returns list of free imps capable of doing this task. '''
        imps = []
        for imp in self.freeimps:
            if task.TestCanImpDo(imp):
                imps.append(imp)
        return imps
                
    def FindImpForTask(self, task):
        ''' Find a free imp for this task. '''
        imps = self.GetImpsForTask(task)
        if not imps:
            return False
            
        oldcount = len(task.imps)
        while imps and task.maximps != len(task.imps):
            freeimp = self.FindNearestFreeImp(task.key, imps)
            if freeimp:
                #print('FindImpForTask: dispatching OnNewTask. Free imps: %d' % (len(self.freeimps)))
                freeimp.DispatchEvent('OnNewTask', task)
            imps.remove(freeimp)
        return oldcount != len(task.imps)
        
    dispatchingevent = False
    def FindTaskForImp(self, freeimp):
        ''' Find a free task for this imp. '''
        if freeimp.executingtask:
            return False
        
        foundtask = False
        testkeys = set(self.keytofreetasks.keys())
        
        while not foundtask and testkeys:
            testkey = freeimp.lasttaskkey if freeimp.lasttaskkey else freeimp.key
            tasks, nearestkey = self.FindNearestTasks(testkey, testkeys)
            pos = self.keeperworld.GetPosFromKey(nearestkey)
            if not tasks:
                testkeys.discard(nearestkey)
                continue
            for t in tasks:
                if t.maximps == len(t.imps) or not t.TestCanImpDo(freeimp):
                    continue

                assert( not self.dispatchingevent )
                self.dispatchingevent = True
                freeimp.DispatchEvent('OnNewTask', t)
                self.dispatchingevent = False
                if freeimp in t.imps:
                    foundtask = True
                    break
                
            # No task found, carry on.
            testkeys.discard(nearestkey)
            
        return foundtask
                
if isserver:
    taskqueues = defaultdict(TaskQueue)
else:
    taskqueues = None

    
@receiver(updatealltasks)
def UpdateAllTasks(owner, **kwargs):
    taskqueues[owner].UpdateAllTasks()
    
if isserver:
    @receiver(resourceupdated)
    def OnResourceUpdated(ownernumber, type, amount, **kwargs):
        taskqueues[ownernumber].OnResourceUpdated()
        
    @concommand('dk_forceupdatetasks')
    def CCForceUpdateTasks(args):
        for tq in taskqueues.values():
            tq.UpdateAllTasks()
            
    @concommand('dk_forceupdatetaskavailability')
    def CCForceUpdateTaskAvailability(args):
        for tq in taskqueues.values():
            tq.UpdateAllTaskAvailability()
            
        