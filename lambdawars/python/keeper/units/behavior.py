from vmath import Vector
from core.units.behavior_generic import BehaviorGeneric
from core.units.intention import BaseAction
from unit_helper import GF_NOCLEAR, GF_REQTARGETALIVE, GF_USETARGETDIST, GF_NOLOSREQUIRED, GF_DIRECTPATH
from particles import *
import ndebugoverlay
from navmesh import RandomNavAreaPositionWithin

from keeper.common import keydist
from keeper import keeperworld
from keeper.gold import goldlist
from keeper.tiles import tiles, tilespertype, nonblocktiles
from keeper.rooms import controllerspertype
import random
from keeper.taskqueue import taskqueues
from keeper.spells import calltoarments

import operator
from collections import defaultdict

from entities import CTakeDamageInfo

class BehaviorKeeper(BehaviorGeneric):
    class ActionIdle(BaseAction):
        nextwandertime = 0
        nextwandertimemin = 3
        nextwandertimemax = 15
        wandering = False
        task = None
        
        def OnStart(self):
            if self.outer.grabreleased:
                self.outer.grabreleased = False
                trans = self.OnReturnFromGrabbed()
                if trans:
                    return trans
                    
            if self.outer.canexecutetasks:
                taskqueues[self.outer.GetOwnerNumber()].OnImpFree(self.outer)
                if taskqueues[self.outer.GetOwnerNumber()].FindTaskForImp(self.outer):
                    return self.Continue()
            return super(BehaviorKeeper.ActionIdle, self).OnStart()
            
        def OnReturnFromGrabbed(self):
            pass
            
        def OnEnd(self):
            if self.outer.canexecutetasks:
                taskqueues[self.outer.GetOwnerNumber()].OnImpRemoved(self.outer)
            
        def Update(self):
            trans = self.CheckEnemies()
            if trans: return trans
                
            if self.nextwandertime < gpGlobals.curtime and nonblocktiles[self.outer.GetOwnerNumber()]:
                self.wandering = True
                return self.SuspendFor(self.behavior.ActionMoveToRandomTile, 'Wandering around')
                
        def OnResume(self):
            # Check for task
            if self.outer.canexecutetasks and taskqueues[self.outer.GetOwnerNumber()].FindTaskForImp(self.outer):
                return self.Continue()
            
            if self.wandering:
                self.nextwandertime = gpGlobals.curtime + random.randint(self.nextwandertimemin, self.nextwandertimemax)
                self.wandering = False
            return super(BehaviorKeeper.ActionIdle, self).OnResume()
            
        def CheckEnemies(self):
            """ Checks if we have an enemy. If that is the case suspend for the attack action. """
            if self.outer.enemy:
                if self.outer.attacks:
                    return self.SuspendFor(self.behavior.ActionAttack, 'Got an enemy', self.outer.enemy)
                    
        def OnNewEnemy(self, enemy):
            """ Listens to the OnNewEnemy event."""
            if self.outer.attacks:
                return self.SuspendFor(self.behavior.ActionAttack, 'Got an enemy', enemy)
                
        def OnKilled(self):
            return self.ChangeTo(self.behavior.ActionDie, 'Changing to die action')
            
        def OnSlap(self):
            return self.SuspendFor(self.behavior.ActionSlapped, 'Slapped')
            
        def OnPlayerGrab(self):
            return self.ChangeTo(self.behavior.ActionPlayerGrab, 'Grabbed')

    class ActionTask(BaseAction):
        def Init(self, task):
            super(BehaviorKeeper.ActionTask, self).Init()
            
            self.task = task
            self.StartExecutingTask(self.task)
            
        def OnEnd(self):
            super(BehaviorKeeper.ActionTask, self).OnEnd()
            
            self.EndExecutingTask(self.task)
                
        def StartExecutingTask(self, task=None):
            if self.outer.executingtask:
                self.EndExecutingTask(self.task)
                PrintWarning("#%d StartExecutingTask: Imp already executing task, ending it...\n" % (self.outer.entindex()))
            assert(not self.outer.executingtask)
            self.outer.executingtask = True
            #if task: # NOTE: Can execute tasks without a task object. That's just to notify the task queue we are not free.
            task.AcceptTask(self.outer)
            taskqueues[self.outer.GetOwnerNumber()].OnImpExecutingTask(self.outer)
            
        def EndExecutingTask(self, task):
            if self.outer.executingtask:
                self.outer.executingtask = False
                #if task:
                self.outer.lasttaskkey = task.key
                taskqueues[self.outer.GetOwnerNumber()].OnImpFree(self.outer, self.task)
        
    class ActionMoveToTile(BehaviorGeneric.ActionMoveInRange):
        ''' Moves the creature to a random tile. '''
        def Init(self, tile):
            super(BehaviorKeeper.ActionMoveToTile, self).Init(tile, 48.0, goalflags=GF_NOLOSREQUIRED)
            
    class ActionMoveToBlock(ActionMoveToTile):
        def Init(self, block):
            assert(block)
            self.block = block
            super(BehaviorKeeper.ActionMoveToBlock, self).Init(self.ComputeTargetTile())
            
        def ComputeTargetTile(self):
            tilegrid = keeperworld.keeperworld.tilegrid
            mykey = self.outer.key
            mytile = tilegrid[mykey]
            assert(mytile)
            assert(self.block.neighbors)
            myarealist = mytile.connectedareas
            
            besttile = None
            bestdist = None
            for tile in self.block.neighbors.values():
                if not tile or tile.isblock:
                    continue
                if myarealist == tile.connectedareas:
                    dist = keydist(mykey, tile.key)
                    if not besttile or dist < bestdist:
                        besttile = tile
                        bestdist = dist
                
            assert(besttile)
            return besttile

    class ActionMoveToRandomTile(BehaviorGeneric.ActionMoveInRange):
        ''' Moves the creature to a random tile. '''
        def Init(self):
            tilegrid = keeperworld.keeperworld.tilegrid
            mykey = self.outer.key
            mytile = tilegrid[mykey]
            reachableset = mytile.connectedareas & nonblocktiles[self.outer.GetOwnerNumber()]
            tile = random.sample(reachableset, 1)[0] if reachableset else None
            self.tile = tile
            
            super(BehaviorKeeper.ActionMoveToRandomTile, self).Init(tile, 48.0, goalflags=GF_NOLOSREQUIRED)
            
        def OnStart(self):
            if not self.tile:
                return self.Done('No target tile')
            return super(BehaviorKeeper.ActionMoveToRandomTile, self).OnStart()
            
    class ActionSlapped(BaseAction):
        def OnStart(self):
            return self.Done('Just done')

    class ActionPlayerGrab(BaseAction):
        ''' Does nothing and changes back to ActionIdle when no longer grabbed. '''
        def OnStart(self):
            self.canbeseen = self.outer.CanBeSeen()
            self.outer.SetCanBeSeen(False)
            
        def OnEnd(self):
            self.outer.grabreleased = True
            self.outer.SetCanBeSeen(self.canbeseen)
            
        def Update(self):
            if not self.outer.grabbedbyplayer:
                return self.ChangeTo(self.behavior.ActionIdle, 'No longer grabbed by player')
                
    class ActionDig(ActionTask):
        def Init(self, task):
            super(BehaviorKeeper.ActionDig, self).Init(task)
            self.block = task.tile
            
        def Update(self):
            block = self.block
            if not block:
                return self.Done('Block killed')
            if not block.IsReachable(self.outer):
                ndebugoverlay.Box(block.GetAbsOrigin(), -Vector(32, 32, 32), Vector(32, 32, 32), 255, 0, 0, 255, 0.1)
                return self.Done('Cannot reach block %s at %s' % (str(block), str(block.key)))
                
            # Move to the block if needed
            pos = keeperworld.keeperworld.GetPosFromKey(block.key)
            dist = (pos - self.outer.GetAbsOrigin()).Length2D()
            if dist > 130.0: # TODO: This depends on the block/tile size
                self.movingtotile = True
                return self.SuspendFor(self.behavior.ActionMoveToBlock, "Moving to block", block) 
                
            # Attack block
            return self.SuspendFor(self.behavior.ActionAttack, 'Digging block at %s' % (str(block.key)), block, forcedenemy=True,
                                    goalflags=GF_NOCLEAR|GF_USETARGETDIST|GF_NOLOSREQUIRED|GF_DIRECTPATH)

        def OnTaskDeleted(self, task):
            return self.Done('Task ended')
                                    
    class ActionTrain(BaseAction):
        ''' Find a train tile and start training '''
        traintile = None
        nextmovetile = 0.0
        movingtotile = False
        training = False
        def OnStart(self):
            self.outer.StartTraining()
            if not self.outer.trainroom:
                return self.Done('No train room.')
                
        def Update(self):
            if not self.outer.CanTrain():
                return self.Done('Cannot train')
                
            trainroom = self.outer.trainroom
            if not trainroom:
                return self.Done('Train room got removed :(')
                
            if not self.traintile or self.nextmovetile < gpGlobals.curtime:
                self.traintile = trainroom.RandomTile()
                assert(self.traintile)
                self.nextmovetile = gpGlobals.curtime + 5.0
            
            # Move to the train tile if needed
            pos = keeperworld.keeperworld.GetPosFromKey(self.traintile.key)
            dist = (pos - self.outer.GetAbsOrigin()).Length2D()
            if dist > 32.0:
                self.movingtotile = True
                return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to train tile", pos, tolerance=12.0)
                
            self.training = True
            succ, waitforact = self.outer.DoTraining()
            if not succ:
                return self.Done('Training failed')
            if waitforact:
                return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Training....', self.outer.animstate.specificmainactivity)
            return self.SuspendFor(self.behavior.ActionWait, 'Traning...', 0.5)
            
        def OnEnd(self):
            self.outer.EndTraining()
            
        def OnResume(self):
            if self.training:
                self.training = False
                outer = self.outer
                
                if not self.outer.ShouldContinueTraining():
                    return self.Done('Done training')
            elif self.movingtotile:
                self.nextmovetile = gpGlobals.curtime + 5.0 # Make sure this timer doesn't tell us to move again, just in case
                self.movingtotile = False
                
            return super(BehaviorCreature.ActionTrain, self).OnResume()
            
class BehaviorImp(BehaviorKeeper):
    class ActionIdle(BehaviorKeeper.ActionIdle):
        def OnReturnFromGrabbed(self):
            self.outer.UpdateKey()
            self.outer.lasttaskkey = None
            tilegrid = keeperworld.keeperworld.tilegrid
            tile = tilegrid[self.outer.key]
            if tile.type == 'training':
                return self.SuspendFor(self.behavior.ActionTrain, 'Imp trainig time') 
        
        def Update(self):
            trans = self.CheckEnemies()
            if trans:
                return trans
                
            # Return gold if we still got some
            if self.outer.carryinggold and not taskqueues[self.outer.GetOwnerNumber()].IsTreasureFull():
                return self.SuspendFor(self.behavior.ActionReturnGold, 'Returning gold we still got')
            
            return super(BehaviorImp.ActionIdle, self).Update()
            
        def OnNewEnemy(self, enemy):
            """ Listens to the OnNewEnemy event."""
            return self.CheckEnemies()
                
        def CheckEnemies(self):
            """ Checks if we have an enemy. If that is the case suspend for the attack action. """
            if self.outer.enemy and self.outer.attacks:
                if not self.outer.heart or (gpGlobals.curtime - self.outer.heart.lastenemyattack < 10.0):
                    return self.SuspendFor(self.behavior.ActionAttack, 'Got an enemy', self.outer.enemy)
                else:
                    return self.SuspendFor(self.behavior.ActionMoveToRandomTile, 'Fleeing')
                    
        def OnNewTask(self, task):
            if self.outer.enemy:
                return # Don't accept tasks if we have an enemy

            if task.type == 'claimtile':
                return self.SuspendFor(self.behavior.ActionConvertTile, 'Got a tile', task, task.tile)
            elif task.type == 'dig':
                block = task.tile
                self.outer.targetblock = block
                self.updateidlepositiononresume = True
                if block:
                    return self.SuspendFor(self.behavior.ActionDig, 'Digging block', task)
                else:
                    task.DeleteTaskIfDone()
            elif task.type == 'getgold':
                gold = task.gold
                if not gold:
                    task.DeleteTaskIfDone()
                elif not self.outer.carryinggold and not gold.carriedbyimp:
                    return self.SuspendFor(self.behavior.ActionGetGoldTask, 'Moving to gold task at %s' % (str(task.key)), task)

            elif task.type == 'fortify':
                block = task.tile
                if block:
                    return self.SuspendFor(self.behavior.ActionFortifyWallTask, 'Fortifying wall at %s' % (str(block.key)), task)
                else:
                    task.DeleteTaskIfDone()
            else:
                PrintWarning('#%d: invalid task %s\n' % (self.outer.entindex(), task.type))

    class ActionTrain(BehaviorKeeper.ActionTrain):
        def OnStart(self):
            taskqueues[self.outer.GetOwnerNumber()].OnImpRemoved(self.outer)
        
            return super(BehaviorImp.ActionTrain, self).OnStart()
            
        def OnEnd(self):
            taskqueues[self.outer.GetOwnerNumber()].OnImpFree(self.outer)
        
            super(BehaviorImp.ActionTrain, self).OnEnd()
            
    class ActionAttack(BehaviorGeneric.ActionAttack):
        def Update(self):
            if not self.enemy:
                return self.Done('enemy lost')
                
            try:
                isblock = self.enemy.isblock
            except AttributeError:
                isblock = False
                
            if isblock:
                if not self.outer.GetOwnerNumber() in self.enemy.selectedbyplayers:
                    return self.Done('No longer ordered to dig this block.')

            return super(BehaviorImp.ActionAttack, self).Update()
            
    class ActionConvertTile(BehaviorKeeper.ActionTask):
        ''' Convert unclaimed land to our own tiles. '''
        def Init(self, task, tile):
            super(BehaviorImp.ActionConvertTile, self).Init(task)
            self.tile = tile
            
        def Update(self):
            outer = self.outer
            if not self.tile or not self.tile.IsClaimable(outer.GetOwnerNumber()):
                return self.Done('Tile changed.')

            path = outer.navigator.path
            if path.pathcontext != self or not path.success:
                pos = keeperworld.keeperworld.GetPosFromKey(self.tile.key)
                return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to tile", pos, tolerance=12.0, pathcontext=self) 
                
            self.creatingtile = True
            self.tile.impassigned = outer.GetHandle()
            return self.SuspendFor(self.behavior.ActionWait, 'Creating tile...', 0.5)
            
        def OnResume(self):
            outer = self.outer
            if not self.tile or not self.tile.IsClaimable(outer.GetOwnerNumber()):
                return self.Done('Tile changed.')
                
            if self.creatingtile:
                DispatchParticleEffect('grub_death_juice', PATTACH_ABSORIGIN, outer)
                outer.EmitSound('Imp.ConvertTile')
                self.tile.Claim(outer.GetOwnerNumber())
                self.tile.impassigned = None
                return self.Done('Converted ground to tile')
            
        creatingtile = False
        
    class ActionFortifyWallTask(BehaviorKeeper.ActionTask):
        def OnStart(self):
            return self.SuspendFor(self.behavior.ActionFortifyWall, 'Fortifying wall', self.task, self.task.tile)
        def OnResume(self):
            return self.Done('Done fortifying wall')
            
    class ActionFortifyWall(BehaviorKeeper.ActionMoveToBlock):
        def Init(self, task, block):
            self.task = task
            self.block = block
            super(BehaviorImp.ActionFortifyWall, self).Init(self.block)

        def OnResume(self):
            if not self.block or self.block.fortified:
                return self.Done('block changed.')
                
            if self.fortifying:
                self.outer.EmitSound('Imp.FortifyWall')
                self.block.Fortify()
                self.block.impassigned = None
                return self.Done('Fortified wall')
            else:
                return super(BehaviorImp.ActionFortifyWall, self).OnResume()
                
        def OnNavComplete(self):
            self.fortifying = True
            if not self.block:
                return self.Done('Block changed.')
            self.block.impassigned = self.outer.GetHandle()
            return self.SuspendFor(self.behavior.ActionWait, 'Fortifying wall...', 1.0)
            
        fortifying = False
        
    class ActionGetGoldTask(BehaviorKeeper.ActionTask):
        def OnStart(self):
            return self.SuspendFor(self.behavior.ActionGetGold, 'Getting gold', self.task.gold)
        def OnResume(self):
            return self.Done('Done getting gold')
                
    class ActionGetGold(BehaviorGeneric.ActionMoveInRange):
        def Init(self, gold):
            super(BehaviorImp.ActionGetGold, self).Init(gold, 48.0, goalflags=GF_NOLOSREQUIRED)
            
            self.gold = gold
            
        def Update(self):
            if not self.gold:
                return self.Done('Gold disappeared')
            if self.gold.carriedbyimp or self.gold.GetOwnerNumber() > 1:
                return self.Done('Some other imp picked the gold up')
                
            return self.Continue()
            
        def OnNavComplete(self):
            self.outer.CarryGold(self.gold)
            return self.ChangeTo(self.behavior.ActionReturnGold, 'Picked up gold. Returning it')
                
    class ActionReturnGold(BehaviorGeneric.ActionMoveInRange):
        def Init(self):
            self.troom = self.FindNearestTreasureRoom()
            super(BehaviorImp.ActionReturnGold, self).Init(self.troom, 48.0, goalflags=GF_NOLOSREQUIRED)
            
        def OnStart(self):
            if not self.troom:
                taskqueues[self.outer.GetOwnerNumber()].NoTreasureRoom(self.outer)
                return self.Done('No treasure room')
            return super(BehaviorImp.ActionReturnGold, self).OnStart()
            
        def OnNavComplete(self):
            gold = self.outer.DropGold()
            #gold = self.troom.AddGold(gold)
            #if gold:
            #    self.outer.CarryGold(gold) # Not done yet
            return self.Done('Dropped gold in treasure room')
            
        def FindNearestTreasureRoom(self):
            bestroom = None
            bestdistsqr = None
            for r in controllerspertype[self.outer.GetOwnerNumber()]['dk_treasure_controller']:
                if r.IsFull():
                    continue
                distsqr = (self.outer.GetAbsOrigin() - r.GetAbsOrigin()).LengthSqr()
                if not bestroom or distsqr < bestdistsqr:
                    bestroom = r
                    bestdistsqr = distsqr
        
            if not bestroom:
                return None
            return bestroom.RandomNotFullTile()
            
class BehaviorCreature(BehaviorKeeper):
    def __init__(self, *args, **kwargs):
        super(BehaviorCreature, self).__init__(*args, **kwargs)

        self.RebuildActivitiesMap()
        
    def RebuildActivitiesMap(self):
        self.activities = [
            (self.ActionGoToSleep, 'Time for a nap...', self.outer.GetSleepPriority),
            (self.ActionEat, 'Need some food...', self.outer.GetEatPriority),
            (self.ActionTrain, 'Going to train...', self.outer.GetTrainPriority),
            (self.ActionMoveToRandomTile, 'Wandering around', self.outer.GetWanderPriority),
            (None, None, self.outer.DoNothingPriority),
        ]
        
    def GetSortedActivities(self):
        sortedacts = defaultdict(list)
        for a in self.activities:
            sortedacts[a[2]()].append(a)
        return sorted(sortedacts.items(), key=operator.itemgetter(0))

    class ActionIdle(BehaviorKeeper.ActionIdle):
        def Update(self):
            trans = self.CheckEnemies()
            if trans:
                return trans
                
            outer = self.outer
                
            # Payday for everything
            if outer.paypending and outer.CanBePayed():
                return self.SuspendFor(self.behavior.ActionGetPay, 'Want my pay!')
                
            # Next check for call to arms
            calltoarms = calltoarments[outer.GetOwnerNumber()]
            if calltoarms:
                return self.OnCallToArms(calltoarms)
        
            # First thing we should do is to ensure we have a lair
            if not outer.lair:
                lair = outer.FindLair()
                if lair:
                    return self.SuspendFor(self.behavior.ActionBuildHome, 'Building a home...', lair)
                else:
                    pass # One time complaint message..
                    
            # Next check if we are happy. Otherwise leave this crappy keeper.
            if outer.ShouldLeave():
                return self.SuspendFor(self.behavior.ActionLeave, 'Bye bye')
                    
            acts = self.behavior.GetSortedActivities()
            if acts:
                activity = random.sample(acts[0][1], 1)[0]
                if activity[0]:
                    return self.SuspendFor(activity[0], activity[1])
            '''
            # TODO: Make a more interesting behavior system for creatures...
            # Sleeping...
            if self.outer.lair and self.outer.NeedSleep():
                return self.SuspendFor(self.behavior.ActionGoToSleep, 'Time for a nap...')
                
            # Eating..
            if self.outer.NeedEating():
                return self.SuspendFor(self.behavior.ActionEat, 'Need some food...')
                
            # Training...
            if self.outer.CanTrain() and self.outer.NeedTraining():
                return self.SuspendFor(self.behavior.ActionTrain, 'Going to train...')
            '''
            return self.Continue()
        
        
        def OnPayDay(self):
            if self.outer.enemy: 
                return
            return self.SuspendFor(self.behavior.ActionGetPay, 'Want my pay!')
            
        def OnCallToArms(self, calltoarment):
            origin = calltoarment.GetAbsOrigin()
            hextent = Vector(128, 128, 0)
            pos = RandomNavAreaPositionWithin(origin - hextent, origin + hextent)
            #ndebugoverlay.Box(pos, -Vector(8, 8, 8), Vector(8, 8, 8), 255, 0, 0, 255, 1.0)
            return self.SuspendFor(self.behavior.ActionAttackMove, 'Call to arms!', pos, tolerance=100.0)
            
    class ActionBuildHome(BaseAction):
        ''' Find a free spot in the lair rooms and build a home. '''
        def Init(self, lair):
            self.lair = lair
            
        def Update(self):
            if not self.lair or self.lair.attachedlair:
                self.lair = self.outer.FindLair()
                if not self.lair: return self.Done('No lair')
                
            # Move to our lair if needed
            pos = keeperworld.keeperworld.GetPosFromKey(self.lair.key)
            dist = (pos - self.outer.GetAbsOrigin()).Length2D()
            if dist > 32.0:
                return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to tile lair", pos, tolerance=12.0) 
                
            # Build our lair!
            self.outer.CreateLair(self.lair)
            return self.Done('Built lair')
            
    class ActionLeave(BehaviorGeneric.ActionMoveInRange):
        def Init(self):
            super(BehaviorCreature.ActionLeave, self).Init(self.outer.portal, 32.0, goalflags=GF_NOLOSREQUIRED)
            
        def OnStart(self):
            self.outer.OnLeaving()
            return super(BehaviorCreature.ActionLeave, self).OnStart()
            
        def OnEnd(self):
            self.outer.creaturestatus = ''
            
        def OnNavComplete(self):
            self.outer.health = 0
            self.outer.SetThink(self.outer.SUB_Remove, gpGlobals.curtime)
            return self.Done('Bye bye')
            
    class ActionGetPay(BehaviorGeneric.ActionMoveInRange):
        def Init(self):
            super(BehaviorCreature.ActionGetPay, self).Init(self.outer.heart, 128.0, goalflags=GF_NOLOSREQUIRED)
            
        def OnNavComplete(self):
            if not self.outer.GetPay():
                return self.Done('Did not get my pay :(')
            return self.Done('Got my pay.')
            
    class ActionGoToSleep(BaseAction):
        def OnStart(self):
            if not self.outer.lair:
                return self.Done('Lair gone.')
            dist = (self.outer.lair.GetAbsOrigin() - self.outer.GetAbsOrigin()).Length2D()
            if dist > 32.0:
                return self.SuspendFor(self.behavior.ActionMoveToLair, "Moving to lair tile") 
            return self.ChangeTo(self.behavior.ActionSleep, 'Starting to sleep...')
            
        def OnResume(self):
            if not self.outer.lair:
                return self.Done('Lair gone.')
            return self.ChangeTo(self.behavior.ActionSleep, 'Starting to sleep...')
                
    class ActionMoveToLair(BehaviorGeneric.ActionMoveInRange):
        def Init(self):
            super(BehaviorCreature.ActionMoveToLair, self).Init(self.outer.lair, 32.0, goalflags=GF_NOLOSREQUIRED)
            
    class ActionSleep(BaseAction):
        ''' sleep. '''
        def OnStart(self):
            self.sleeptime = gpGlobals.curtime + 5.0
            self.outer.StartSleeping()
        
        def Update(self):
            fraction = self.outer.health / float(self.outer.maxhealth)
            if self.sleeptime < gpGlobals.curtime and fraction > 0.35:
                return self.Done('done sleeping')
            self.outer.Sleep()
            
        def OnEnd(self):
            self.outer.EndSleeping()
            
    class ActionEat(BaseAction):
        ''' Find a hatchery and eat '''
        hatchery = None
        eating = False
        grub = None
        def OnStart(self):
            self.outer.StartEating()
            
        def Update(self):
            outer = self.outer
            if not self.hatchery:
                self.hatchery = outer.FindHatchery()
                if not self.hatchery or not self.hatchery.roomcontroller:
                    return self.Done('No hatchery')
                    
            # Move to the hatchery tile if needed
            if not self.grub:
                self.grub = self.hatchery.roomcontroller.GetRandomGrub()
                if not self.grub:
                    return self.Done('Hatchery has no grubs')
                
            path = outer.navigator.path
            if path.pathcontext != self or not path.success:
                pos = self.grub.GetAbsOrigin()
                return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to grub in hatchery", pos, tolerance=12.0, pathcontext=self)
                
            self.eating = True
            #grub.Remove() # Eat the grub!
            self.grub.health = 0
            info = CTakeDamageInfo(outer, outer, 0, 0)
            self.grub.TakeDamage(info)
            #self.grub.SetThink(self.grub.SUB_Remove, gpGlobals.curtime) # Eat the grub!
            return self.SuspendFor(self.behavior.ActionWait, 'Eating...', 1.0)
            
        def OnEnd(self):
            self.outer.EndEating()
            
        def OnResume(self):
            if self.eating:
                self.eating = False
                outer = self.outer
                outer.Eat()
                if outer.health >= outer.maxhealth or random.random() < 0.7:
                    return self.Done('Done eating')
                
            return super(BehaviorCreature.ActionEat, self).OnResume()
     
class BehaviorHero(BehaviorKeeper):
    class ActionIdle(BehaviorKeeper.ActionIdle):
        def Update(self):
            # 
            trans = super(BehaviorHero.ActionIdle, self).Update()
            if trans:
                return trans
                
            # Default to attack moving the dungeon heart
            if self.outer.targetheart:
                hearttile = keeperworld.keeperworld.GetTileFromPos(
                                self.outer.targetheart.GetAbsOrigin())
                if hearttile and hearttile.IsReachable(self.outer):
                    return self.SuspendFor(self.behavior.ActionAttackMove, 'Attack moving dungeon heart', self.outer.targetheart)
    
class BehaviorHeroDigger(BehaviorHero):
    class ActionIdle(BehaviorHero.ActionIdle):
        def OnNewTask(self, task):
            if self.outer.enemy:
                return # Don't accept tasks if we have an enemy (that's just silly)
                
            if task.type == 'dig':
                block = task.tile
                self.outer.targetblock = block
                self.updateidlepositiononresume = True
                if block:
                    return self.SuspendFor(self.behavior.ActionDig, 'Digging block', task)                     
                                            
class BehaviorFood(BehaviorKeeper):
    ''' Limits movement to our hatchery tiles. '''
    class ActionIdle(BehaviorKeeper.ActionIdle):
        nextwandertimemin = 1
        nextwandertimemax = 5
    
        def Update(self):
            if self.outer.hatchery and self.nextwandertime < gpGlobals.curtime and nonblocktiles[self.outer.GetOwnerNumber()]:
                self.wandering = True
                return self.SuspendFor(self.behavior.ActionMoveToTile, 'Wandering around', self.outer.hatchery.RandomTile())
                
    