from srcbase import *
from vmath import Vector, QAngle, vec3_origin
from core.gamerules import GamerulesInfo, WarsBaseGameRules
from core.abilities import GetAbilityInfo, GetTechNode
from playermgr import OWNER_LAST, OWNER_ENEMY, relationships
from gamemgr import dblist, BaseInfo, BaseInfoMetaclass, dbgamepackages
import random
import bisect
import traceback
from collections import defaultdict
from math import ceil
from gamerules import gamerules
from core.units import unitlist, PrecacheUnit, CreateUnitNoSpawn, PlaceUnit, GetUnitInfo, UnitBase, CreateUnitFancy
from core.buildings.base import constructedlistpertype, buildinglist
from core.resources import SetResource, GiveResources, TakeResources
from core.signals import unitremoved
from wars_game.resources import ResKillsInfo
from fow import FogOfWarMgr
from navmesh import RandomNavAreaPosition, RandomNavAreaPositionWithin, RecastMgr
from wars_game.statuseffects import StunnedEffectInfo
import ndebugoverlay

from profiler import StartProfiler, EndProfiler
from vprof import vprofcurrentprofilee

if isserver:
    from entities import (entlist, MouseTraceData, CreateEntityByName, DispatchSpawn, D_LI, D_HT, variant_t, g_EventQueue, \
        GetClassByClassname)
    from utils import UTIL_HudMessageAll, hudtextparms, UTIL_FindPosition, FindPositionInfo, UTIL_DropToFloor, UTIL_PlayerByIndex
    from gameinterface import concommand, FCVAR_CHEAT, ConVar, AutoCompletion
    from core.usermessages import SendUserMessage, CReliableBroadcastRecipientFilter, CSingleUserRecipientFilter
    from core.units import UnitCombatAirNavigator

    overrun_max_active_enemies = ConVar('overrun_max_active_enemies', '30')
    
# Wave type dictionary
dbwavetypeid = 'overrun_wavetype'
dbwavetypes = dblist[dbwavetypeid]

# Helpers for health mods
def HMod(unit):
    return 'healthmod_%s' % (unit)
def HModEasy(unit):
    return 'easy_healthmod_%s' % (unit)
def HModNormal(unit):
    return 'normal_healthmod_%s' % (unit)
def HModHard(unit):
    return 'hard_healthmod_%s' % (unit)

def HModGrow(unit):
    return 'healthgrowmod_%s' % (unit)
def HModGrowEasy(unit):
    return 'easy_healthgrowmod_%s' % (unit)
def HModGrowNormal(unit):
    return 'normal_healthgrowmod_%s' % (unit)
def HModGrowHard(unit):
    return 'hard_healthgrowmod_%s' % (unit)


# Small helper function for selecting units to some probability distribution
# http://rosettacode.org/wiki/Probabilistic_choice#Python
def probchoice(items, probs):
    """ Splits the interval 0.0-1.0 in proportion to probs
        then finds where each random.random() choice lies
    """

    prob_accumulator = 0
    accumulator = []
    for p in probs:
        prob_accumulator += p
        accumulator.append(prob_accumulator)
 
    while True:
        r = random.random()
        yield items[bisect.bisect(accumulator, r)]


class Overrun(WarsBaseGameRules):
    if isserver:
        def InitGamerules(self):
            super().InitGamerules()
            
            self.playersready = set()
            
            random.seed()
            
            self.wavefilters = {
                'distribution': self.WaveDistributionFilter,
                'constraints': self.WaveConstraintsFilter,
            }

            self.healthmodifiers = defaultdict(lambda: 1.0)
            self.healthgrowmodifiers = defaultdict(lambda: 1.0) # Modifies the above health modifiers each wave
            self.nextwave = gpGlobals.curtime + self.waveinterval
            
            self.basehealthgrowmodifier = 1.0
            
            self.constraints = defaultdict(lambda: defaultdict(lambda: 0)) # Format: [unittype][property] => [value]

            # Spawned and killed enemy types per wave
            self.wavespawnedtypescount = defaultdict(lambda: 0)
            self.waveskilledtypescount = defaultdict(lambda: 0)
            
            self.manager = entlist.FindEntityByClassname(None, 'overrun_manager')

            # Setup default info, possible overridden by gamelobby
            if self.manager:
                if self.manager.wavetype:
                    self.wavetype = self.manager.wavetype
                self.indoor = self.manager.indoor
            else:
                self.indoor = False
            
            if not self.wavetype:
                self.wavetype = 'antlions'

            unitremoved.connect(self.OnUnitKilled)
            
        def ShutdownGamerules(self):
            super().ShutdownGamerules()

            self.wavefilters.clear()
            
            unitremoved.disconnect(self.OnUnitKilled)
            
        def Precache(self):
            super().Precache()
            
            dbwavetypes[self.wavetype].Precache()
            
        def ClientActive(self, client):
            super().ClientActive(client)
            
            filter = CSingleUserRecipientFilter(client)
            filter.MakeReliable()
            SendUserMessage( filter, 'overrun.waveupdate', [self.wave, self.__nextwave] )

        def EndOverrun(self, victory=False):
            if victory:
                self.EndGame(winners=self.gameplayers, losers=[])
            else:
                self.EndGame(winners=[], losers=self.gameplayers)
            
        def PreSuiciderSpawn(self, unit):
            unit.BehaviorGenericClass = unit.BehaviorOverrunClass
            unit.spawnsuiciders = False
        def OnUnitKilled(self, unit, *args, **kwargs):
            self.lastactivitytime = gpGlobals.curtime

            if unit.GetOwnerNumber() == OWNER_ENEMY:
                if getattr(unit, 'overrunspawned', False):
                    unittype = unit.GetUnitType()
                    if not unit.IsAlive():
                        self.wavekillcount += 1
                        self.waveskilledtypescount[unittype] += 1
                    else:
                        self.spawnsleft += 1 # Add back the spawn count
                        #print('Unit got removed without being killed. Adding back to spawn pile.')
                        # This will let the constraint code spawn the unit again
                        self.wavespawnedtypescount[unittype] -= 1
                
        def ClientCommand(self, player, args):
            """ Processes Overrun player commands """
            command = args[0]
            
            if command == 'overrun_wave_ready':
                # Player indicates being ready for next wave
                playerdata = self.GetPlayerGameData(player=player)
                if playerdata:
                    steamid = playerdata.get('steamid', None)
                    if steamid:
                        self.playersready.add(steamid)
                    else:
                        PrintWarning('overrun_wave_ready: Player has no steam id\n')
                return True
                
            return super().ClientCommand(player, args)
            
        def ArePlayersReady(self):
            """ Tests if players are ready for next wave. """
            for playerdata in self.gameplayers:
                if playerdata.get('iscpu', False):
                    continue
                    
                steamid = playerdata.get('steamid', None)
                if not steamid:
                    continue
                    
                if steamid not in self.playersready:
                    return False
            
            return True
            
        def SetPlayersReady(self):
            """ Sets all players to ready for the next wave. """
            for playerdata in self.gameplayers:
                if playerdata.get('iscpu', False):
                    continue
                    
                steamid = playerdata.get('steamid', None)
                if not steamid:
                    continue
                    
                self.playersready.add(steamid)
                
        def MainThink(self):
            super().MainThink()

            if self.gameover:
                return
                
            # Players might be victorious or defeated, in which case the game ends
            if not self.waveinprogress and self.finalwave != 0 and self.wave >= self.finalwave:
                self.EndOverrun(victory=True)
                return
            elif self.CheckDefeat():
                self.EndOverrun(victory=False)
                return
                
            # Don't run until a valid wave type is set
            if not self.waveinfo:
                return

            if self.modificator_camera:
                if not self.snapcameranexttime > gpGlobals.curtime:
                    for i in range(1, gpGlobals.maxClients+1):
                        player = UTIL_PlayerByIndex(i)
                        if player is None or not player.IsConnected():
                            continue     
                        #player.SnapCameraTo(enemy.GetAbsOrigin() + Vector(0,0,1))
                        player.SetLocalAngles(QAngle(random.randint(-180, 180), random.randint(-180, 180), 0))
                        player.SnapEyeAngles(QAngle(random.randint(-180, 180), random.randint(-180, 180), 0))
                    self.snapcameranexttime = gpGlobals.curtime + random.randint(10, 20)
            if self.modificator_random:
                if not self.checkplayersunit > gpGlobals.curtime:
                    for i in range(1, gpGlobals.maxClients+1):
                        player = UTIL_PlayerByIndex(i)
                        if player is None or not player.IsConnected():
                            continue
                        playerowner = player.GetOwnerNumber()
                        if self.modificator_random == 2:
                            owner = player.GetOwnerNumber()
                            unitowner = OWNER_ENEMY
                        elif self.modificator_random == 1:
                            owner = OWNER_ENEMY
                            unitowner = player.GetOwnerNumber()
                        if not len(unitlist[unitowner]) > 0:
                            continue

                        unit = random.choice(unitlist[unitowner])
                        options = (['changeowner', 'suicide', 'requisition', 'stun', 'lowhp', 'morerequisition'], 
                                   [0.059, 0.04, 0.45, 0.25, 0.2, 0.001])
                        type = next(probchoice(options[0], options[1]))

                        if type == 'changeowner':
                            unit.SetOwnerNumber(owner)
                        elif type == 'suicide':
                            unit.Suicide()
                        elif type == 'requisition':
                            if self.modificator_random == 2:
                                TakeResources(player.GetOwnerNumber(), [('kills', 100)])
                            elif self.modificator_random == 1:
                                GiveResources(player.GetOwnerNumber(), [('kills', 100)])
                        elif type == 'morerequisition':
                            if self.modificator_random == 2:
                                TakeResources(player.GetOwnerNumber(), [('kills', 5000)])
                            elif self.modificator_random == 1:
                                GiveResources(player.GetOwnerNumber(), [('kills', 5000)])
                        elif type == 'stun':
                            StunnedEffectInfo.CreateAndApply(unit, attacker=None, duration=5.0)
                        elif type == 'lowhp':
                            unit.health = 1

                    self.checkplayersunit = gpGlobals.curtime + 60

            vprofcurrentprofilee.EnterScope("Overrun", 0, "Overrun", False)
            StartProfiler('Overrun')
            
            if self.waveinprogress:
                enemiesalive = len(unitlist[OWNER_ENEMY]) - len(buildinglist[OWNER_ENEMY])
                unitsleft = ((self.spawnsleft+enemiesalive)/float(self.spawnsize))
                lastwaveprogress = self.waveprogress
                self.waveprogress = self.wavekillcount / float(self.spawnsize)
                
                # Broadcast wave progress to clients
                if self.nextwaveprogressupdatetime < gpGlobals.curtime and self.oldwaveprogress != self.waveprogress:
                    filter = CReliableBroadcastRecipientFilter()
                    SendUserMessage(filter, 'overrun.waveprogress', [self.waveprogress])
                
                    self.nextwaveprogressupdatetime = gpGlobals.curtime + 1
                    self.oldwaveprogress = self.waveprogress
                
                if self.CheckConstraintsSatisfied() and (unitsleft < 0.025 or self.wavekillcount >= self.spawnsize):
                    # Start count down for next wave and clear all players being ready.
                    self.nextwave = gpGlobals.curtime + max(0,self.waveinterval + random.uniform(-self.waveintervalnoise, self.waveintervalnoise))
                    self.playersready.clear()
                    self.waveinprogress = False

                    # Give income to players for surviving the wave
                    players = self.GetRealPlayers()
                    owners = set([p.GetOwnerNumber() for p in players])
                    DevMsg(1, "Wave %d ended. Active owners: %s\n" % (self.wave, str(owners)))
                    income = int(self.waveincome)
                    if self.difficulty == 'easy':
                        income *= 2
                        if not income > 0:
                            income = 200
                    elif self.difficulty == 'normal':
                        income *= 1.25
                        if not income > 0:
                            income = 50
                    if self.modificator_suiciders == 1:
                        income *= 5
                    elif self.modificator_suiciders == 2:
                        income *= 0.2
                    income = (round(income))
                    for ownernumber in owners:
                        DevMsg(1, "Giving player %d resources (%d)\n" % (ownernumber, income))
                        GiveResources(ownernumber, [(ResKillsInfo, income)], firecollected=True)

                    # Replenish energy of all units on the map
                    UnitBase.ReplenishAllUnitsEnergy()
                else:
                    # Detect inactivity
                    if self.waveprogress != lastwaveprogress:
                        self.lastactivitytime = gpGlobals.curtime
                        
                    if gpGlobals.curtime - self.lastactivitytime > self.inactivitytimeout:
                        enemies = list(unitlist[OWNER_ENEMY])
                        '''enemysample = random.sample(enemies, min(10, len(enemies)))
                        nodamagetaken = True
                        for e in enemysample:
                            if gpGlobals.curtime - e.lasttakedamage < 3.0:
                                nodamagetaken = False
                                break'''
                                
                        PrintWarning('Overrun: Enemy inactivity detected. Killing all currently alive enemies.\n')
                        if not self.spawnsleft:
                            PrintWarning('Overrun: force satisfy constraints\n')
                            self.ForceSatisfyConstraints()
                        [e.Remove() for e in enemies]
                
            elif self.nextwave < gpGlobals.curtime or self.ArePlayersReady():
                # Either wave prepare time is over or all players indicated they are ready
                self.SpawnWave()
            else:
                # In between waves, so no spawning is going on
                self.lastactivitytime = gpGlobals.curtime

            # Update spawner
            if self.nextspawninterval < gpGlobals.curtime:
                # Get spawn points
                spawnpoints = self.BuildSpawnPointListFrame()
                if spawnpoints:
                    self.UpdateConstraints(spawnpoints)
                    self.UpdateSpawner(spawnpoints)
                
                self.nextspawninterval = gpGlobals.curtime + self.spawninterval
                
            # Let wave info do its thing
            self.waveinfo.Update(self)

            EndProfiler('Overrun')
            vprofcurrentprofilee.ExitScope()
                
        def CheckGameOver(self):
            if self.gameover:   # someone else quit the game already
                # check to see if we should change levels now
                if self.intermissionendtime < gpGlobals.curtime:
                    self.ChangeToGamelobby()  # intermission is over
                return True
            return False
        
        criticalbuildingtypes = [
            'build_comb_hq',
            'build_comb_hq_overrun',
            'build_reb_hq',
            'build_reb_hq_overrun',
        ]

        def CheckDefeat(self):
            if self.manager and self.manager.usecustomconditions:
                return False
                
            for data in self.gameplayers:
                if self.IsPlayerDefeated(data):
                    continue
                ownernumber = data['ownernumber']
                # Count the HQ buildings
                countunitscomb = len([b for b in constructedlistpertype[ownernumber]['overrun_build_comb_hq'] if b.IsAlive()])
                countunitsreb = len([b for b in constructedlistpertype[ownernumber]['overrun_build_reb_hq'] if b.IsAlive()])
                countunits = countunitscomb + countunitsreb
                for data1 in self.gameplayers:
                    ownernumber1 = data1['ownernumber']
                    # Count the HQ buildings
                    countunitscomb = len([b for b in constructedlistpertype[ownernumber1]['overrun_build_comb_hq'] if b.IsAlive()])
                    countunitsreb = len([b for b in constructedlistpertype[ownernumber1]['overrun_build_reb_hq'] if b.IsAlive()])
                    countunits += countunitscomb + countunitsreb
                if not countunits:
                    self.PlayerDefeated(data)
                        
            # Everybody should still be going
            everybodydefeated = True
            for data in self.gameplayers:
                if self.IsPlayerDefeated(data):
                    continue
                everybodydefeated = False
                break
            return everybodydefeated

        __nextwave = 0

        def __GetNextWave(self):
            return self.__nextwave

        def __SetNextWave(self, wavetime):
            self.__nextwave = wavetime
            filter = CReliableBroadcastRecipientFilter()
            SendUserMessage( filter, 'overrun.waveupdate', 
                [self.wave, self.__nextwave] )
        nextwave = property(__GetNextWave, __SetNextWave, None, "Level time at which the next wave is spawned")
        
        __wavetype = ''

        def __GetWaveType(self):
            return self.__wavetype

        def __SetWaveType(self, wavetype):
            try:
                self.waveinfo = dbwavetypes[wavetype]()
            except KeyError:
                PrintWarning('Failed  to set wavetype to %s\n' % (wavetype))
                return
            self.__wavetype = wavetype

        wavetype = property(__GetWaveType, __SetWaveType, None, "Wave type")
        
        def __GetUnitRadiusAndHeightFromInfo(self, unitinfo):
            size = unitinfo.maxs - unitinfo.mins
            size.z = 0
            return size.Length() * 0.5, unitinfo.maxs.z - unitinfo.mins.z
            
        def __TestSupportUnitInfo(self, unittype):
            unitinfo = GetUnitInfo(unittype, fallback=None)
            if not unitinfo or not unitinfo.mins:
                # Don't know what kind of unit, just assume True for now!
                return True

            # TODO: Improve detection. Air navigator is hard coded to air mesh.
            cls = GetClassByClassname(unitinfo.cls_name)
            navigatorcls = getattr(cls, 'NavigatorClass', None)
            if navigatorcls and issubclass(navigatorcls, UnitCombatAirNavigator):
                return RecastMgr().IsMeshLoaded('air')
                
            radius, height = self.__GetUnitRadiusAndHeightFromInfo(unitinfo)
            meshname = RecastMgr().FindBestMeshNameForRadiusHeight(radius, height)
            if not meshname:
                DevMsg(1, 'Filtering unit %s from Overrun wave (mesh %s is not available)\n' % (unitinfo.name, meshname))
                return False
            return True
                
        def WaveDistributionFilter(self, distribution, default):
            """ Filters units that are not supported on this map from the distribution info.
                The filtering process is based on the available navigation meshes, set through
                the entity recast_mgr.

                Args:
                    distribution (WaveInfo): current distribution used for spawning enemies
                    default (object): default returned when everything is filtered away
            """
            if not distribution:
                return distribution
                
            unittypes = []
            probs = []
            for unittype, prob in zip(distribution[0], distribution[1]):
                if not self.__TestSupportUnitInfo(unittype):
                    continue
            
                unittypes.append(unittype)
                probs.append(prob)
                
            # Could be filtered until empty!
            if not unittypes:
                return default
            
            # Normalize the probabilities again and return the filtered distribution
            distsum = sum(probs)
            normalizedprobs = [ x / distsum for x in probs ]
            return (unittypes, normalizedprobs)
            
        def WaveConstraintsFilter(self, constraints, default):
            """ Filters units that are not supported on this map from the constraints info.
                The filtering process is based on the available navigation meshes, set through
                the entity recast_mgr.
            """
            if not constraints:
                return constraints
                
            newconstraints = {}
            for unittype, info in constraints.items():
                if not self.__TestSupportUnitInfo(unittype):
                    continue
                newconstraints[unittype] = info
            
            return newconstraints

        def GetFromWaveInfo(self, waveinfo, name, default):
            diffkey = '%s_%s' % (self.difficulty, name)
            ret = waveinfo.get(diffkey, None)
            if ret != None:
                return ret

            fnfilter = self.wavefilters.get(name, lambda v, d: v)
            return fnfilter(waveinfo.get(name, default), default)
            
        def UpdateHealthModifiers(self, waveinfo):
            # Update health + grow modifiers
            for key in waveinfo.keys():
                diffkey = '%s_healthmod_' % (self.difficulty)
                diffkeygrow = '%s_healthgrowmod_' % (self.difficulty)
                if key.startswith(diffkeygrow):
                    unit = key.lstrip(diffkeygrow)
                    self.healthgrowmodifiers[unit] = waveinfo[key]
                elif key.startswith('healthgrowmod_'):
                    unit = key.lstrip('healthgrowmod_')
                    self.healthgrowmodifiers[unit] = waveinfo[key]
                elif key.startswith(diffkey):
                    unit = key.lstrip(diffkey)
                    self.healthmodifiers[unit] = waveinfo[key]
                elif key.startswith('healthmod_'):
                    unit = key.lstrip('healthmod_')
                    self.healthmodifiers[unit] = waveinfo[key]
                    
        def GrowHealthModifiers(self):
            # Grow healthmodifiers
            for unit, growmod in self.healthgrowmodifiers.items():
                self.healthmodifiers[unit] *= growmod
                DevMsg(1, "UpdateHealthModifiers: Grown health mod %s to %f\n" % (unit, self.healthmodifiers[unit]))
            if self.difficulty == 'hard':
                self.basehealthgrowmodifier *= 1.05
            elif self.difficulty == 'medium':
                self.basehealthgrowmodifier *= 1.025
            elif self.difficulty == 'easy':
                self.basehealthgrowmodifier *= 1.001
                        
        def UpdateWaveInfo(self):
            """ Updates Wave settings. """
            if self.wave in self.waveinfo.distribution:  
                waveinfo = self.waveinfo.distribution[self.wave]
                self.curwavedistribution = self.GetFromWaveInfo(waveinfo, 'distribution', self.curwavedistribution)
                
                # Spawn size settings
                newspawnsize = self.GetFromWaveInfo(waveinfo, 'spawnsize', None)
                if newspawnsize != None:
                    self.spawnsize = newspawnsize * max(1, self.activeplayers)
                self.spawngrowrate = self.GetFromWaveInfo(waveinfo, 'growrate', self.spawngrowrate)
                
                # Update constraints
                constraints = self.GetFromWaveInfo(waveinfo, 'constraints', None)
                if constraints != None:
                    self.constraints.clear()
                    self.constraints.update(constraints)
                
                # Number of enemies alive at same time
                newmaxenemiesalive = self.GetFromWaveInfo(waveinfo, 'maxenemiesalive', None)
                if newmaxenemiesalive != None:
                    self.maxenemiesalive = newmaxenemiesalive * max(1, self.activeplayers)
                self.maxenemiesalivegrowrate = self.GetFromWaveInfo(waveinfo, 'maxenemiesalivegrowrate', self.maxenemiesalivegrowrate)
                
                # Wave income
                self.waveincome = self.GetFromWaveInfo(waveinfo, 'waveincome', self.waveincome)
                self.waveincomegrow = self.GetFromWaveInfo(waveinfo, 'waveincomegrow', self.waveincomegrow)
                
                # Wave interval
                self.waveinterval = self.GetFromWaveInfo(waveinfo, 'waveinterval', self.waveinterval)
                self.waveintervalnoise = self.GetFromWaveInfo(waveinfo, 'waveintervalnoise', self.waveintervalnoise)
                self.waveintervaldecreaserate = self.GetFromWaveInfo(waveinfo, 'waveintervaldecreaserate', self.waveintervaldecreaserate)
                self.inactivitytimeout = waveinfo.get('inactivitytimeout', self.inactivitytimeout)
                
                self.UpdateHealthModifiers(waveinfo)
                
            self.GrowHealthModifiers()
            
            # Default enemies alive at same time to the convar specified maximum
            if self.maxenemiesalive == 0:
                self.maxenemiesalive = overrun_max_active_enemies.GetInt()
                
        def WavePointInFOW(self, point, owernumber):
            """ Check if this spawn point is hidden in the FOW. """
            origin = point.GetAbsOrigin()
            if (FogOfWarMgr().PointInFOW(origin, owernumber) and
                FogOfWarMgr().PointInFOW(origin + Vector(320.0, 0, 0), owernumber) and
                FogOfWarMgr().PointInFOW(origin - Vector(320.0, 0, 0), owernumber) and
                FogOfWarMgr().PointInFOW(origin + Vector(0.0, 320.0, 0), owernumber) and
                FogOfWarMgr().PointInFOW(origin - Vector(0.0, 320.0, 0), owernumber) ):
                return True
            return False

        def RebuildSpawnPointsList(self):
            """ Build list of wave spawn points. """
            
            # Get all wavepoints per priority
            wavepointsmap = {}
            wavespawnpoint = entlist.FindEntityByClassname(None, 'overrun_wave_spawnpoint')
            while wavespawnpoint:
                if not wavespawnpoint.disabled:
                    wavespawnpoint.precomputedpaths.clear() # Clear cached paths, because routes might change on new wave
                    if wavespawnpoint.priority not in wavepointsmap:
                        wavepointsmap[wavespawnpoint.priority] = [wavespawnpoint]
                    else:
                        wavepointsmap[wavespawnpoint.priority].append(wavespawnpoint)
                wavespawnpoint = entlist.FindEntityByClassname(wavespawnpoint, 'overrun_wave_spawnpoint')
                
            # Create a list of the lists of wavepoints, sorted on priority
            self.wavespawnpoints = []
            keys = sorted(list(wavepointsmap.keys()), reverse=True)
            for key in keys:
                self.wavespawnpoints.append(wavepointsmap[key])
            
            if not self.wavespawnpoints:
                PrintWarning("overrun gamemode: No overrun_wave_spawnpoint entities found (wave %s)!" % (self.wave))
                
        def BuildHeadcrabCannisterSpawnPointsList(self):
            points = []
            wavespawnpoint = entlist.FindEntityByClassname(None, 'overrun_headcrabcannister_spawnpoint')
            while wavespawnpoint:
                if not wavespawnpoint.disabled:
                    points.append(wavespawnpoint)
                wavespawnpoint = entlist.FindEntityByClassname(wavespawnpoint, 'overrun_headcrabcannister_spawnpoint')
            return points
                
        def BuildSpawnPointListFrame(self):
            """ Build spawn point list for this frame. """
            players = self.GetRealPlayers()
            if not players:
                return []
            owernumber = players[0].GetOwnerNumber()
            
            pointlist = None
            for pointlist in self.wavespawnpoints:
                valid = True
                for point in pointlist:
                    if not self.WavePointInFOW(point, owernumber):
                        valid = False
                        break
                     
                if valid:
                    break
            
            if not pointlist:
                return
                
            if self.curwavepointpriority != pointlist[0].priority:
                DevMsg(1, "BuildSpawnPointListFrame: Wave point priority changed from %d to %d\n" % (self.curwavepointpriority, pointlist[0].priority))
                self.curwavepointpriority = pointlist[0].priority
                
            #for point in pointlist:
            #    ndebugoverlay.Box(point.GetAbsOrigin(), -Vector(8, 8, 8), Vector(8, 8, 8), 255, 0, 0, 255, 15.0)
                        
            # Randomize points
            points = list(pointlist)
            random.shuffle(points)
                     
            return points
                
        def SpawnWave(self):
            self.wave += 1
            self.nextwave = gpGlobals.curtime # Wave is now, update hud
            
            if self.manager:
                self.manager.OnNewWave(self.wave)
            
            self.RebuildSpawnPointsList()
            
            oldspawnsize = self.spawnsize
            oldwaveinterval = self.waveinterval
            oldmaxenemiesalive = self.maxenemiesalive
            self.UpdateWaveInfo()
                
            # Update spawnsize (except for wave 1)
            if self.wave != 1:
                if oldspawnsize == self.spawnsize:
                    self.spawnsize = min(100000, int(ceil(self.spawnsize*self.spawngrowrate)))
                if oldwaveinterval == self.waveinterval:
                    self.waveinterval = max(0, self.waveinterval-self.waveintervaldecreaserate)
                if oldmaxenemiesalive == self.maxenemiesalive:
                    self.maxenemiesalive = min(overrun_max_active_enemies.GetInt(), int(ceil(self.maxenemiesalive*self.maxenemiesalivegrowrate)))
                self.waveincome = self.waveincome * self.waveincomegrow

            # Send wave message to all players
            params = hudtextparms()
            params.x = -1
            params.y = -1
            params.effect = 0
            params.r1 = params.g1 = params.b1 = 255
            params.a1 = 255
            params.r2 = params.g2 = params.b2 = 255
            params.a2 = 255
            params.fadeinTime = 1.0
            params.fadeoutTime = 0.5
            params.holdTime = 5.0
            params.fxTime = 3.0
            params.channel = 0
            UTIL_HudMessageAll(params, "WAVE %d INCOMING!" % (self.wave))
            
            # Should have a curwavedistribution set
            if not self.curwavedistribution:
                return
            
            # Spawn wave
            if self.wavespawnpoints:
                # Set the amount that needs to be spawned
                self.spawnsleft = self.spawnsize
                
                # Units are selected according to the wave distribution.
                self.curwavedistributor = probchoice(self.curwavedistribution[0], self.curwavedistribution[1]) if self.curwavedistribution[0] else None
                
            try:
                # Tell wave info we created a new wave
                self.waveinfo.OnNewWave(self.wave)
            except:
                traceback.print_exc()
            
            self.lastactivitytime = gpGlobals.curtime
            self.waveinprogress = True
            self.wavekillcount = 0
            self.wavespawnedtypescount.clear()
            self.waveskilledtypescount.clear()
            
    def SpawnUnit(self, point, info, unittype):
        """ Spawns an unit for Overrun, marking it as Overrun spawned for tracking.
        
            Args:
                point (Vector): position around which to spawn the unit.
                info (object): Find position info of existing in progress unit spawning code.
                unittype (string): The type of unit to spawn.
        """
        # Find a position on the navigation mesh around the spawn point
        UTIL_FindPosition(info)
        if not info.success:
            return None
        
        # Create and spawn unit
        unit = CreateUnitNoSpawn(unittype, owner_number=OWNER_ENEMY)
        unit.BehaviorGenericClass = unit.BehaviorOverrunClass
        unit.SetAbsOrigin(info.position + Vector(0, 0, 64))
        unit.wavespawnpoint = point
        DispatchSpawn(unit)
        unit.Activate() 
        
        # Apply (health) modifiers
        if self.difficulty == 'hard':
            healthmodifier = 1.0
            unit.viewdistance = 1920
            unit.sensedistance = 1920
        elif self.difficulty == 'medium':
            healthmodifier = 0.75
        elif self.difficulty == 'easy':
            healthmodifier = 0.5

        unit.health = int(unit.health * self.healthmodifiers[unittype] * self.basehealthgrowmodifier * healthmodifier)
        unit.maxhealth = int(unit.maxhealth * self.healthmodifiers[unittype] * self.basehealthgrowmodifier * healthmodifier)
        
        # Drop the unit to the floor
        UTIL_DropToFloor(unit, MASK_NPCSOLID)
        
        # Indicates the unit got spawned by the Overrun rules and not by some ability or other stuff
        unit.overrunspawned = True 
        
        self.wavespawnedtypescount[unittype] += 1
        
        return unit
    def SpawnUnit_Modificator(self, unit_list):
        for u in unit_list:
            info = FindPositionInfo(u.GetAbsOrigin(), -Vector(32, 32, 0), Vector(32, 32, 64), 0, 128)
            UTIL_FindPosition(info)
            if not info.success:
                continue
        
            unittype = u.unitinfo.name
            # Create and spawn unit
            unit = CreateUnitNoSpawn(unittype, owner_number=u.GetOwnerNumber())
            #unit.BehaviorGenericClass = unit.BehaviorOverrunClass
            unit.SetAbsOrigin(info.position + Vector(random.randint(-32, 32), random.randint(-32, 32), 64))
            DispatchSpawn(unit)
            unit.Activate() 
            unit.health = int(unit.health * 0.5)
            unit.maxhealth = int(unit.maxhealth * 0.5)
            u.health = int(u.health * 0.5)
            u.maxhealth = int(u.maxhealth * 0.5)
        
            # Drop the unit to the floor
            UTIL_DropToFloor(unit, MASK_NPCSOLID)
        
        
    def CheckConstraintsSatisfied(self):
        """ Checks if constraints for current wave are satisfied. """
        for unittype, constraint in self.constraints.items():
            mustkill = constraint.get('mustkill', None)
            if mustkill == None:
                continue
            mincount = self.constraints[unittype].get('min', 0)
            if mincount != 0:
                mustkill = min(mustkill, mincount)
                
            if self.waveskilledtypescount[unittype] < mustkill:
                return False
        return True
        
    def ForceSatisfyConstraints(self):
        """ Used by inactivity timer to force the constraints to be satisfied. """
        for unittype, constraint in self.constraints.items():
            mustkill = constraint.get('mustkill', None)
            if mustkill == None:
                continue
            mincount = self.constraints[unittype].get('min', 0)
            if mincount != 0:
                mustkill = min(mustkill, mincount)
                
            self.waveskilledtypescount[unittype] = mustkill
        
    def UpdateConstraints(self, spawnpoints):
        # Check constraints of this wave (if any)
        progress = self.waveprogress
        for unittype, constraint in self.constraints.items():
            mincount = constraint.get('min', 0)
            if mincount == 0:
                continue
            maxspawnatprogress = constraint.get('maxspawnatprogress', 1.0)
            if progress < maxspawnatprogress:
                continue
            
            while self.wavespawnedtypescount[unittype] < mincount:
                idx = random.randint(0,len(spawnpoints)-1)
                point = spawnpoints[idx]
                maxradius = point.maxradius if point.maxradius else None
                info = FindPositionInfo(point.GetAbsOrigin()+Vector(0,0,32.0), -Vector(40, 40, 0), Vector(40, 40, 100), maxradius=maxradius)
        
                self.SpawnUnit(point, info, unittype)
                
    def UpdateSpawner(self, spawnpoints):
        if not self.spawnsleft:
            return
            
        tobespawned = min(self.spawnsleft, self.maxspawnperinterval)
    
        # Check if we should spawn. If there are more than self.maxenemiesalive
        # minus tobespawned antlions present we wait.
        alive = len(unitlist[OWNER_ENEMY]) - len(buildinglist[OWNER_ENEMY])
        
        if alive + tobespawned > self.maxenemiesalive:
            return
        
        # Select random spawn point from list
        # Then use the wave distribution to spawn some units
        idx = random.randint(0,len(spawnpoints)-1)
        point = spawnpoints[idx]
        maxradius = point.maxradius if point.maxradius else None
        info = FindPositionInfo(point.GetAbsOrigin()+Vector(0,0,32.0), -Vector(40, 40, 0), Vector(40, 40, 100), maxradius=maxradius)

        for i in range(0, tobespawned):
            if self.curwavedistributor:
                # Select unit type
                unittype = next(self.curwavedistributor)
                maxcount = self.constraints[unittype].get('max', 0)
                if maxcount != 0 and self.wavespawnedtypescount[unittype] >= maxcount:
                    continue
                
                # Spawn the unit
                if not self.SpawnUnit(point, info, unittype):
                    continue
                
            self.spawnsleft -= 1
                
        self.lastactivitytime = gpGlobals.curtime

    def StartGame(self):
        super().StartGame()
        amount = 100
        if self.modificator_suiciders == 1:
            amount *= 5
        elif self.modificator_suiciders == 2:
            amount *= 0.25
        if self.modificator_vampire == 1:
            amount *= 1.2
        elif self.modificator_vampire == 2:
            amount *= 0.8
        if self.difficulty == 'medium':
            amount *= 2.0
        elif self.difficulty == 'easy':
            amount *= 4.0
        amount = round(amount)
        self.RebuildSpawnPointsList()
        
        for data in self.gameplayers:
            SetResource(data['ownernumber'], ResKillsInfo.name, amount)
        
            if self.waveinfo.locksomeunits:
                techlist = ['overrun_deploymanhack', 'overrun_unit_manhack', 'overrun_unit_strider', 'overrun_unit_scanner', 'overrun_unit_observer', 'overrun_unit_clawscanner']
                for tech in techlist:
                    technode = GetTechNode(tech, data['ownernumber'])
                    technode.locked = True
        if self.difficulty == 'hard':
            for upgrade in self.hardmodeupgrades:
                technode = GetTechNode(upgrade, OWNER_ENEMY)
                technode.techenabled = True
            
        self.UpdateWaveInfo()
        self.nextwave = gpGlobals.curtime + self.waveinterval + random.uniform(-self.waveintervalnoise, self.waveintervalnoise)

    def SetupRelationships(self):
        """ Everybody likes everybody """
        for ownernumber1 in range(OWNER_LAST, OWNER_LAST+12):
            for ownernumber2 in range(OWNER_LAST, OWNER_LAST+12):
                relationships[(ownernumber1, ownernumber2)] = D_LI
            relationships[(ownernumber1, OWNER_LAST+14)] = D_HT
            
    def ApplyDataToPlayer(self, player):
        rv = super().ApplyDataToPlayer(player)
        
        # Make sure all players are on the same team
        player.ChangeTeam(2)
        
        #probably not the best place to put it
        if self.manager: # trigger overrun_manager wavetype
            self.manager.WaveTypeDecision(self.wavetype)
            self.manager.DifficultyDecision(self.difficulty)
     
        return rv

    @classmethod    
    def GetCustomFields(cls):
        """ Returns a list of custom settings to be displayed in the game lobby settings. """
        
        # Build wave type list
        wavetypes = ['random']
        for key, info in dbwavetypes.items():
            if info.ShouldAddWaveType():
                wavetypes.append(key)
        wavetypes.sort()
        
        fields = {
            '_difficulty' : {'name' : '#Overrun_Difficulty', 'type' : 'choices', 'values' : ['easy', 'normal', 'hard'], 'default' : 'hard'},
            '_wavetype' : {'name' : '#Overrun_WaveType', 'type' : 'choices', 'values' : wavetypes, 'default' : wavetypes[0] if wavetypes else ''},
            '_waves' : {'name' : '#Overrun_Waves', 'type' : 'choices', 'values' : ['10', '20', 'endless'], 'default' : 'endless'},
            #'inversion' : {'name' : 'Inversion', 'type' : 'choices', 'values' : ['no', 'yes'], 'default' : 'no'},
            'camera flip' : {'name' : '#Modificator_Camera', 'type' : 'choices', 'values' : ['no', 'yes'], 'default' : 'no'},
            'armor' : {'name' : '#Modificator_Armor', 'type' : 'choices', 'values' : ['no', 'yes', 'inverted'], 'default' : 'no'},
            #'vampire' : {'name' : 'Vampire', 'type' : 'choices', 'values' : ['no', 'yes', 'inverted'], 'default' : 'no'},
            'suiciders' : {'name' : '#Modificator_Suiciders', 'type' : 'choices', 'values' : ['no', 'yes', 'inverted'], 'default' : 'no'},
            'random effect' : {'name' : '#Modificator_Effect', 'type' : 'choices', 'values' : ['no', 'yes', 'inverted'], 'default' : 'no'},
            #'consume' : {'name' : 'Consume', 'type' : 'choices', 'values' : ['no', 'yes'], 'default' : 'no'},
        }
        fields.update(super().GetCustomFields())
        return fields
        
    def ApplyCustomField(self, fieldname, value):
        if super().ApplyCustomField(fieldname, value):
            return True
            
        if fieldname == '_difficulty':
            self.difficulty = value
            return True
        elif fieldname == '_wavetype':
            if value == 'random':
                wavetypes = []
                for key, info in dbwavetypes.items():
                    if info.ShouldAddWaveType():
                        wavetypes.append(key)
                self.wavetype = random.choice(wavetypes)
            else:
                self.wavetype = value
            return True
        elif fieldname == '_waves':
            try:
                if value == 'endless':
                    self.finalwave = 0
                else:
                    self.finalwave = int(value)
            except ValueError:
                self.finalwave = 0
            return True
        elif fieldname == 'camera flip':
            if value == 'yes':
                self.modificator_camera = 1
        elif fieldname == 'suiciders':
            if value == 'yes':
                self.modificator_suiciders = 1
            elif value == 'inverted':
                self.modificator_suiciders = 2
        elif fieldname == 'vampire':
            if value == 'yes':
                self.modificator_vampire = 1
            elif value == 'inverted':
                self.modificator_vampire = 2
        elif fieldname == 'armor':
            if value == 'yes':
                self.modificator_armor = 1
            elif value == 'inverted':
                self.modificator_armor = 2
        elif fieldname == 'random effect':
            if value == 'yes':
                self.modificator_random = 1
            elif value == 'inverted':
                self.modificator_random = 2
            
        return False
        
    def GetMainResource(self):
        return 'kills'
           
    # Current wave.
    wave = 0
    #: Final wave. Zero or None when the waves are endless.
    finalwave = 0
    basehealthgrowmodifier = 1.0
    manager = None
    maxspawnperinterval = 5
    spawninterval = 0.2
    nextspawninterval = 0.0
    #: Indicates an active wave is in progress
    waveinprogress = False
    #: Last wave progress broadcasted to players
    oldwaveprogress = 0.0
    #: Wave progress from 0 to 1
    waveprogress = 0.0
    #: Next time the wave progress is broadcasted to all players
    nextwaveprogressupdatetime = 0.0
    #: Enemies left to spawn
    spawnsleft = 0
    #: Number of enemies killed during the current wave
    wavekillcount = 0
    
    #: Map is indoor
    indoor = False
    
    hardmodeupgrades = ['combine_hp_upgrade', 'mortarsynth_upgrade', 'strider_maxenergy_upgrade', 'medic_healrate_upgrade', 
                        'medic_regenerate_upgrade', 'medic_maxenergy_upgrade', 'medic_smg1_upgrade', 'rebel_hp_upgrade']
    # Last time enemies were active, used for killing them off when wave is stuck
    lastactivitytime = 0.0
    inactivitytimeout = 30.0
    
    curwavepointpriority = 0
    
    spawnsize = 0 # Set this in wavedistributions!
    spawngrowrate = 1.15
    maxenemiesalive = 0
    maxenemiesalivegrowrate = 1.5 # Assuming base size of ~10, then around wave 5 around 100 max alive
    
    waveincome = 0 # Set this in wavedistributions!
    waveincomegrow = 1.15
    
    waveinterval = 0.0 # Set this in wavedistributions!
    waveintervalnoise = 5.0
    waveintervaldecreaserate = 1.0
    
    difficulty = 'normal'
    curwavedistribution = None
    waveinfo = None
    #Modificators:
    modificator_inversion = 0
    modificator_camera = 0
    modificator_suiciders = 0
    modificator_armor = 0
    modificator_vampire = 0
    modificator_random = 0
    modificator_consume = 0
    
    checkplayersunit = 0
    checkplayersunit_consume = 0
    snapcameranexttime = 0

    supportsscrap = False # Don't drop scrap when units are killed

class BaseWaveTypeMetaClass(BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        # Validate wave settings
        for wave, waveinfo in newcls.distribution.items():
            distribution = waveinfo.get('distribution', None)
            if distribution:
                # Verify the number of entries matches the number of distribution probabilities
                assert len(distribution[0]) == len(distribution[1]), 'Wave Type "%s" has no valid wave distribution for wave %d (number of distributions does not match number of units' %(newcls.name, wave)
                
                # Normalize wave distribution to 1
                distsum = sum(distribution[1])
                normalizedprobs = [ x / distsum for x in distribution[1] ]
                
                # Update entry with normalized probs
                waveinfo['distribution'] = (distribution[0], normalizedprobs)
        return newcls

class BaseWaveType(BaseInfo, metaclass=BaseWaveTypeMetaClass):
    id = dbwavetypeid
    
    priority = 0
    spawncloseaspossible = False # Spawn units close as possible, based on wave point priority
    locksomeunits = False
    # Dictionary containing your wave distribution.
    # The first number indicates at which wave the new info gets applied (you must specify 1).
    # For each waveinfo a new dictionary is created.
    # 'distribution' contains two lists.
    # The first list contains the type of units in the wave.
    # The second list the way those units are distributed.
    #
    # Other properties:
    # spawnsize: Units to be spawned during a wave
    # growrate: Modifier for grow of spawnsize per wave.
    # constraints: dictionary containing the minimum and maximum per unittype during a wave.
    #              This is mainly to restrict strong units from spawning too much or ensuring at
    #              at least one spawns.
    # 
    distribution = {}
    
    @classmethod
    def ShouldAddWaveType(cls):
        ''' Whether to add this wave type to the list of available wave types in the gamelobby. '''
        return True
        
    @classmethod
    def Precache(cls):
        # Precache all units
        unittypes = set()
        for wave in cls.distribution.values():
            if 'distribution' not in wave:
                continue
            unittypes |= set(wave['distribution'][0])
        for unittype in unittypes:
            PrecacheUnit(unittype)
        
    def OnNewWave(self, wave):
        pass
        
    def Update(self, gamerules):
        """ Allows custom code for this wave type, called each overrun think freq. """
        pass

class AntlionWaveType(BaseWaveType):
    name = 'antlions'
    locksomeunits = True
                
    distribution = {
        0: {
                # Prepare time
                'easy_waveinterval' : 120,
                'normal_waveinterval' : 90,
                'hard_waveinterval' : 60,
                
                #HModHard('unit_antlion') : 1.2,
                #HModHard('unit_antlionworker') : 1.2,
            },
        1: {
                'inactivitytimeout' : 20.0,
                'spawnsize' : 75,
                'maxenemiesalive' : 28,
                'growrate' : 1.1,
                'easy_waveinterval' : 120,
                'normal_waveinterval' : 90,
                'hard_waveinterval' : 60,
				
                'waveincome' : 100,
                'waveincomegrow' : 1.008,
        
                'distribution' : (['unit_antlion_small'], 
                                 [1.0]),
            },
        2: {
                'easy_waveinterval' : 120,
                'normal_waveinterval' : 60,
                'hard_waveinterval' : 5,
                'distribution' : (['unit_antlion', 'unit_antlionworker'], 
                                  [0.85, 0.20]),
            },
        7: {
            'distribution': (['unit_antlion', 'unit_antlionworker', 'unit_antlionsuicider'],
                             [0.8, 0.2, 0.05]),

            },
        8: {
                'distribution' : (['unit_antlion', 'unit_antlionworker'], 
                                  [0.4, 0.80]),
            },
        10: {
                'distribution' : (['unit_antlion', 'unit_antlionsuicider', 'unit_antlionworker', 'unit_antlionguard'], 
                                  [0.8, 0.15, 0.20, 0.05]),
                'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
                
                
                
            },
        11: {
                'distribution' : (['unit_antlion', 'unit_antlionworker'], 
                                  [0.9, 0.20]),
            },
        12: {
                'distribution' : (['unit_antlionsuicider', 'unit_antlionworker'], 
                                  [1.0, 0.9]),
            },
        13: {
                'distribution' : (['unit_antlionguardcavern', 'unit_antlionworker'], 
                                  [0.15, 0.9]),
            },
        14: {
                'distribution' : (['unit_antlionworker'], 
                                  [1.0]),
            },
        15: {
                'distribution' : (['unit_antlion', 'unit_antlionsuicider', 'unit_antlionworker', 'unit_antlionguard', 'unit_antlionguardcavern', 'unit_antlionguardcavernboss'], 
                                  [0.7, 0.25, 0.20, 0.02, 0.008, 0.002]),
                'growrate' : 1.05,
                
             },
        16: {
                'distribution' : (['unit_antlionguard', 'unit_antlionworker'], 
                                  [1.0, 0.80]),
            },
        18: {
                'distribution' : (['unit_antlionguardcavernboss', 'unit_antlionworker'], 
                                  [1.0, 0.80]),
            },
        19: {
                'distribution' : (['unit_antlionsuicider', 'unit_antlionguardcavern', 'unit_antlionworker'], 
                                  [0.85, 0.20, 0.80]),
            },
             
        20: {
                'distribution' : (['unit_antlion', 'unit_antlionsuicider', 'unit_antlionworker', 'unit_antlionguard', 'unit_antlionguardcavern', 'unit_antlionguardcavernboss'], 
                                  [0.01, 0.70, 0.05, 0.10, 0.30, 0.50]),
                'growrate' : 1.2,
                'waveincome' : 0,
                'waveincomegrow' : 0.0,
             },
    }

class ZombieWaveType(BaseWaveType):
    name = 'zombie'
    
    #spawncloseaspossible = False
    locksomeunits = True
    
    distribution = {
        0: {
                # Zombies are slower, so have a larger time out
                'inactivitytimeout' : 80.0,
                
                # Prepare time
                'easy_waveinterval' : 120,
                'normal_waveinterval' : 60,
                'hard_waveinterval' : 30,
                
                #HModHard('unit_zombie') : 1.2,
                #HModHard('unit_fastzombie') : 1.2,
                #HModHard('unit_headcrab_fast') : 1.2,
                #HModHard('unit_headcrab') : 1.2,
            },
        1: {
                'distribution' : (['unit_headcrab', 'unit_zombie'], 
                                  [0.75, 0.25]),
                'spawnsize' : 50,
                'growrate' : 1.01,
                'maxenemiesalive' : 50,
                
                'waveincome' : 30,
                'waveincomegrow' : 1.05,
            },
        2: {
                'distribution' : (['unit_headcrab_fast', 'unit_zombie', 'unit_headcrab'], 
                                  [0.33, 0.4, 0.33]),
                'easy_waveinterval' : 120,
                'normal_waveinterval' : 60,
                'hard_waveinterval' : 10,
                
            },
        4: {
                'distribution' : (['unit_headcrab_fast', 'unit_fastzombie'], 
                                  [0.75, 0.3]),
                       
            },
            
        5: {
                'distribution' : (['unit_fastzombie'], 
                                  [1.0]),
        
                #'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
                
            },
        6: {
                'distribution' : (['unit_headcrab_fast','unit_headcrab','unit_zombie'], 
                                  [0.6, 0.25, 0.25]),
                
            },            
        7: {
                'distribution' : (['unit_headcrab_fast', 'unit_zombie', 'unit_fastzombie'], 
                                  [0.5, 0.1, 0.5]),
                                  
                
            },
            
        8: {
                'distribution' : (['unit_poisonzombie','unit_fastzombie','unit_zombie'], 
                                  [0.5, 0.28, 0.25]),
                
            },
        9: {
                'distribution' : (['unit_fastzombie'], 
                                  [1.0]),
        
                #'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
                
            },
            
        10: {
                'distribution' : (['unit_headcrab_fast', 'unit_headcrab', 'unit_zombie', 'unit_fastzombie', 'unit_zombine', 
                                   'unit_poisonzombie'], 
                                  [0.1, 0.05, 0.40, 0.3, 0.08, 0.02]),
                'waveincome' : 0,
                'waveincomegrow' : 0.0, 
                'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
            },

        11: {
                'distribution' : (['unit_headcrab_fast', 'unit_fastzombie', 'unit_zombine','unit_headcrab_poison_boss'], 
                                  [0.5, 0.5, 0.5, 0.5]),
            },

        12: {
                'distribution' : (['unit_headcrab_fast', 'unit_headcrab_poison', 'unit_zombie', 'unit_fastzombie', 'unit_zombine', 
                                   'unit_poisonzombie', 'unit_poisonzombieboss'], 
                                  [0.1, 0.05, 0.40, 0.3, 0.08, 0.02, 0.05]),
            },

        15: {
                'distribution' : (['unit_headcrab_fast', 'unit_headcrab', 'unit_zombie', 'unit_fastzombie', 'unit_zombine', 
                                   'unit_poisonzombie', 'unit_poisonzombieboss' ,'unit_headcrab_poison_boss'], 
                                  [0.1, 0.05, 0.40, 0.3, 0.08, 0.02, 0.025, 0.025]),
                #'waveincome' : 0,
                #'waveincomegrow' : 0.0, 
            },

        16: {
                'distribution' : (['unit_poisonzombie', 'unit_zombine'], 
                                  [0.5, 0.5]),
            }, 
        17: {
                'distribution' : (['unit_headcrab_poison_boss', 'unit_poisonzombieboss'], 
                                  [0.1, 0.9]),
            }, 

        20: {
                'distribution' : (['unit_headcrab_fast', 'unit_headcrab', 'unit_zombie', 'unit_fastzombie', 'unit_zombine', 
                                   'unit_poisonzombie', 'unit_poisonzombieboss' ,'unit_headcrab_poison_boss'], 
                                  [0.1, 0.05, 0.30, 0.3, 0.08, 0.02, 0.5, 0.1]),
                
            },
    }
    
    spotid = 0
    nextfirecannisters = -1
    nextallowfirecannisters = 0.0
    firecannistersleft = 0
    minnextfire = 60.0
    maxnextfire = 100.0
    minfirecan = 1
    maxfirecan = 1
    mincansize = 3
    maxcansize = 6
    headcrabtype = "0"
    
    @classmethod
    def Precache(cls):
        super().Precache()
        
        PrecacheUnit('unit_headcrabcanister')
    
    def OnNewWave(self, wave):
        if wave == 6:
            self.headcrabtype = "1"
            
        if wave == 8:
            self.minnextfire = 40.0
            self.maxnextfire = 80.0
            self.minfirecan = 1
            self.maxfirecan = 2
        elif wave == 13:
            self.minnextfire = 30.0
            self.maxnextfire = 45.0
            self.minfirecan = 1
            self.maxfirecan = 2
        elif wave == 20:
            self.minnextfire = 20.0
            self.maxnextfire = 30.0
            self.minfirecan = 1
            self.maxfirecan = 1
            
    def UpdateHeadcrabCannisters(self, gamerules):
        """ Fires headcrab canisters at random intervals during the wave. """
        if gamerules.indoor or not gamerules.waveinprogress:
            return
    
        if self.nextfirecannisters == -1:
            self.nextfirecannisters = gpGlobals.curtime + random.uniform(50.0, 100.0)
            
        if self.nextfirecannisters < gpGlobals.curtime:
            self.nextfirecannisters = gpGlobals.curtime + random.uniform(self.minnextfire, self.maxnextfire)
            self.firecannistersleft += random.randint(self.minfirecan, self.maxfirecan)
            
        if self.firecannistersleft <= 0 or self.nextallowfirecannisters > gpGlobals.curtime:
            return

        self.nextallowfirecannisters = gpGlobals.curtime + 1.0
        
        spawnpoints = gamerules.BuildHeadcrabCannisterSpawnPointsList()
        
        unitinfo = GetUnitInfo('unit_headcrabcanister', fallback=None)
        if not unitinfo:
            return
        
        n = self.firecannistersleft
        for i in range(0, n):
            # Get target position
            centerpos = None
            
            if spawnpoints:
                point = random.choice(spawnpoints)
                centerpos = point.GetAbsOrigin()
                radius = point.maxradius
            else:
                building = self.RandomEnemyBuilding()
                if building:
                    centerpos = building.GetAbsOrigin()
                    radius = 1500.0
                
            # Get a random target position within the extent
            if centerpos:
                hextent = Vector(radius, radius, 0.0)
                targetpos = RandomNavAreaPositionWithin(centerpos - hextent, centerpos + hextent)
            else:
                targetpos = RandomNavAreaPosition()
                
            if targetpos == vec3_origin:
                continue
            
            # And fire
            self.firecannistersleft -= 1
            self.FireCannister(targetpos)
                
    def Update(self, gamerules):
        self.UpdateHeadcrabCannisters(gamerules)
                
    def RandomEnemyBuilding(self):
        buildings = []
        for l in buildinglist.values():
            buildings += l.copy()
        return random.choice(buildings) if buildings else None
        
    def PreSpawnHeadcrab(self, headcrab):
        headcrab.BehaviorGenericClass = headcrab.BehaviorOverrunClass 
           
    def FireCannister(self, targetpos):
        """ Launches a headcrab canister at the target spot.
        
            Args:
                targetpos (Vector): target spot
        """
    
        spotname = "hcspot%d" % (self.spotid)
    
        # Create a launch spot
        spot = CreateEntityByName( "info_target" )
        spot.KeyValue("targetname", spotname )
        spot.SetAbsOrigin(targetpos + Vector(64.0, 90.0, 712.0)) # Start position
        spot.SetAbsAngles(QAngle( 60, 0, 0 )) 
        DispatchSpawn(spot)

        # Create and setup the canister
        can = CreateUnitNoSpawn( "unit_headcrabcanister" )
        can.SetOwnerNumber(OWNER_ENEMY)
        can.KeyValue("name", "head")
        can.KeyValue("HeadcrabType", self.headcrabtype)
        can.KeyValue("HeadcrabCount", "%d" % (random.randint(self.mincansize, self.maxcansize)))
        can.KeyValue("FlightSpeed", "512")
        can.KeyValue("FlightTime", "1")
        can.KeyValue("Damage", "75")
        can.KeyValue("DamageRadius", "250")
        can.KeyValue("LaunchPositionName", spotname)
        can.lifetime = 60.0
        can.SetAbsOrigin(targetpos)
        can.SetAbsAngles(QAngle(-90, 0, 0))
        can.fnprespawnheadcrab = self.PreSpawnHeadcrab
        
        # Adjust headcrab cannister position, could be invalid
        PlaceUnit(can, targetpos)
        
        DispatchSpawn(can)
        can.Activate()
        
        self.spotid += 1
        
        # Cleanup
        g_EventQueue.AddEvent( can, "FireCanister", variant_t(), 1.0, None, None, 0 )
        g_EventQueue.AddEvent( spot, "kill", variant_t(), 25.0, None, None, 0 )

class CombineWaveType(BaseWaveType):
    name = 'combine'
    
    distribution = {
        0: {
                # Prepare time
                'inactivitytimeout' : 20.0,
                'easy_waveinterval' : 140,
                'normal_waveinterval' : 70,
                'hard_waveinterval' : 45,
            },
        1: {
                'distribution' : (['unit_metropolice','unit_combine_citizen'], 
                                  [0.75,0.50]),
                'spawnsize' : 10,
                'growrate' : 1.1,
                'maxenemiesalive' : 80,
                
                'waveincome' : 10,
                'waveincomegrow' : 1.41,
            },
        2: {
                'distribution' : (['unit_metropolice_smg1','unit_metropolice_riot','unit_metropolice'], 
                                  [1.0, 1.0, 1.0]),
                'easy_waveinterval' : 140,
                'normal_waveinterval' : 70,
                'hard_waveinterval' : 15,
            },
        3: {
                'distribution' : (['unit_metropolice_smg1','unit_metropolice_riot','unit_metropolice','unit_manhack'], 
                                  [1.0, 1.0, 1.0, 1.0]),
            },
        5: {
                'distribution' : (['unit_combine'], 
                                  [1.0]),
            },
        6: {
                'distribution' : (['unit_combine', 'unit_combine_sg', 'unit_combine_ar2', 'enemy_unit_combine_sniper'], 
                                  [0.8, 0.8, 0.8,0.2]),
            },
        7: {
                'distribution' : (['unit_combine', 'unit_combine_sg'], 
                                  [0.75, 0.50]),
            },
        8: {
                'distribution' : (['unit_combine', 'unit_combine_sg', 'unit_combine_ar2', 'enemy_unit_combine_sniper'], 
                                  [0.40, 0.30, 0.20, 0.10]),
                #'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
            },
        9: {
                'distribution' : (['unit_combine_heavy', 'unit_combine_elite'], 
                                  [0.80, 0.20]),
            },
        10: {
                'distribution' : (['enemy_unit_combine_sniper', 'unit_combine_sg', 'unit_combine_ar2', 'unit_combine_elite', 'unit_hunter', 'unit_combine_heavy'], 
                                  [0.30, 0.30, 0.10, 0.29, 0.01, 0.20]),
                'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
            },
        11: {
                'distribution' : (['unit_combine_ar2', 'unit_hunter', 'unit_combine_heavy'], 
                                  [0.50, 0.50, 0.25]),
            },
        14: {
                'distribution' : (['unit_combine_heavy', 'unit_combine_sg', 'unit_combine_ar2', 'unit_combine_elite','unit_hunter', 'unit_crab_synth'], 
                                  [0.30, 0.30, 0.20, 0.10,0.20, 0.10]),
            },
        15: {
                'distribution' : (['unit_combine_heavy', 'unit_hunter', 'unit_combine_ar2', 'unit_combine_elite', 'overrun_unit_mortar_synth', 'unit_crab_synth'], 
                                  [0.30, 0.30, 0.10, 0.29, 0.01, 0.15]),
                'waveincomegrow' : 0.0,
                'waveincome' : 0,
            },
        16: {
                'distribution' : (['unit_hunter','overrun_unit_mortar_synth','unit_crab_synth','unit_strider'],
                                  [0.38, 0.33, 0.33, 0.1]),
            },
        20: {
                'distribution' : (['unit_hunter','overrun_unit_mortar_synth','unit_crab_synth','unit_strider','unit_combine_heavy','unit_combine_elite','unit_combine_ar2'],
                                  [0.5, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5]),
            },
    }

class RebelWaveType(BaseWaveType):
    name = 'rebels'

    distribution = {
        0: {
            'inactivitytimeout' : 20.0,
            'easy_waveinterval': 160,
            'normal_waveinterval': 80,
            'hard_waveinterval': 35,
        },
        1: {
                'distribution' : (['unit_rebel_scout'], [1.0]),

                'spawnsize' : 20,
                'growrate' : 1.03,
                'maxenemiesalive' : 80,

                'waveincome' : 45,
                'waveincomegrow' : 1.06,
        },
        2: {
                'distribution' : (['unit_rebel_scout', 'unit_rebel_partisan', 'unit_rebel_saboteur'], [0.7, 0.3, 0.4]),

                'easy_waveinterval' : 160,
                'normal_waveinterval' : 80,
                'hard_waveinterval' : 16,
        },
        5: {
                'distribution' : (['unit_rebel', 'unit_rebel_sg', 'unit_rebel_ar2', 'unit_rebel_medic', 'unit_rebel_partisan', 'unit_rebel_partisan_molotov'], [0.2, 0.2, 0.3, 0.10, 0.10, 0.10]),

            },
        7: {
                'distribution' : (['unit_rebel_flamer', 'unit_rebel_ar2', 'unit_rebel_medic', 'unit_rebel_partisan', 'unit_rebel_partisan_molotov'], [0.2, 0.3, 0.3, 0.1, 0.1]),

        },
        8: {
                'distribution' : (['unit_vortigaunt', 'unit_rebel', 'unit_rebel_sg', 'unit_rebel_medic', 'unit_rebel_winchester'], [0.2, 0.6, 0.1, 0.1, 0.2]),
        },
        9: {
                'distribution' : (['enemy_unit_rebel_veteran', 'unit_rebel'], [0.8, 0.2])
        },
        10: {
            'distribution': (
            ['unit_vortigaunt', 'unit_rebel_sg', 'unit_rebel_ar2', 'unit_rebel_flamer', 'unit_rebel_heavy'],
            [0.30, 0.30, 0.10, 0.30, 0.15]),
                'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
        },
        11: {
            'distribution' : (['unit_rebel_rpg', 'unit_rebel_sg', 'unit_rebel_heavy', 'unit_rebel_winchester'], [0.5, 0.5, 0.20, 0.20]),

        },
        14: {
            'distribution': (['unit_rebel', 'unit_rebel_sg', 'unit_rebel_ar2', 'unit_rebel_flamer', 'unit_rebel_medic', 'unit_rebel_rpg', 'unit_vortigaunt', 'unit_rebel_heavy'], [0.10, 0.10, 0.10, 0.30, 0.10, 0.20, 0.10, 0.25]),
        },
        15: {
            'distribution': (
            ['unit_rebel_rpg', 'unit_vortigaunt', 'unit_rebel_tau', 'unit_rebel_flamer', 'unit_dog', 'unit_rebel_heavy'],
            [0.30, 0.30, 0.10, 0.29, 0.01, 0.30]),
            'waveincomegrow': 0.0,
            'waveincome': 0,

        },
        16: {
            'distribution' : (['unit_rebel', 'unit_rebel_sg', 'unit_rebel_ar2', 'unit_rebel_medic', 'enemy_unit_rebel_veteran'], [0.20, 0.20, 0.20, 0.20, 0.20]),

        },
        17: {
            'distribution' : (['unit_rebel_flamer', 'unit_rebel_tau', 'unit_rebel_rpg', 'unit_rebel_heavy', 'unit_vortigaunt'], [0.20, 0.20, 0.20, 0.20, 0.20]),

        },
        19: {
            'distribution' : (['unit_rebel_engineer', 'unit_rebel_winchester'], [0.9, 0.1]),

        },
        20: {
            'distribution' : (['unit_dog', 'unit_rebel_tau', 'unit_rebel_rpg', 'unit_rebel_heavy', 'unit_vortigaunt', 'unit_rebel_flamer', 'unit_rebel_ar2'], [0.20, 0.20, 0.20, 0.20, 0.20, 0.2, 0.2]),

        },
    }
class AlltypesWaveType(BaseWaveType):
    name = 'alltypes'
    
    #spawncloseaspossible = True
    locksomeunits = False
    
    distribution = {
        0: {
                'inactivitytimeout' : 60.0,
                
                # Prepare time
                'easy_waveinterval' : 180,
                'normal_waveinterval' : 90,
                'hard_waveinterval' : 50,
                
                #HModHard('unit_zombie') : 1.2,
                #HModHard('unit_fastzombie') : 1.2,
                #HModHard('unit_headcrab_fast') : 1.2,
                #HModHard('unit_headcrab') : 1.2,
            },
        1: {
                'distribution' : (['unit_headcrab', 'unit_rebel_partisan', 'unit_antlion', 'unit_combine_citizen'], 
                                  [0.25, 0.25, 0.25, 0.25]),
                'spawnsize' : 40,
                'growrate' : 1.06,
                'maxenemiesalive' : 100,
                
                'waveincome' : 75,
                'waveincomegrow' : 1.15,
            },
        2: {
                'distribution' : (['unit_headcrab_fast', 'unit_antlion', 'unit_headcrab', 'unit_rebel_scout', 'unit_metropolice_smg1', 'unit_rebel_saboteur'], 
                                  [0.1, 0.15, 0.5, 0.2, 0.25, 0.1]),
                'easy_waveinterval' : 180,
                'normal_waveinterval' : 90,
                'hard_waveinterval' : 5,
                
            },
        5: {
                'distribution' : (['unit_fastzombie', 'unit_antlionworker', 'unit_rebel', 'unit_manhack'],   
                                  [0.5, 0.5, 0.5, 0.5]),
                
            },
        6: {
                'distribution' : (['unit_poisonzombie', 'unit_rebel_sg'], 
                                  [1.0, 1.0]),
                
            },            
        7: {
                'distribution' : (['unit_antlionsuicider', 'unit_antlionworker'], 
                                  [1.0, 1.0]),
                                  
                
            },
            
        8: {
                'distribution' : (['unit_combine_ar2','unit_combine_sg'], 
                                  [0.5, 0.56]),
                
            },
        9: {
                'distribution' : (['unit_rebel_ar2','unit_rebel_engineer'], 
                                  [0.5, 0.57]),
        
                #'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
                
            },
            
        10: {
                'distribution' : (['unit_rebel_medic', 'unit_rebel_tau', 'enemy_unit_combine_sniper', 'unit_combine_elite', 'unit_antlionguard', 
                                   'unit_zombine'], 
                                  [0.1, 0.05, 0.40, 0.3, 0.08, 0.02]),
                'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
            },

        11: {
                'distribution' : (['unit_poisonzombieboss', 'enemy_unit_rebel_veteran'], 
                                  [0.5, 0.55]),
            },

        12: {
                'distribution' : (['unit_antlionguardcavern', 'unit_combine_heavy'], 
                                  [0.5, 0.54]),
            },

        13: {
                'distribution' : (['unit_rebel_flamer', 'unit_rebel_heavy', 'unit_vortigaunt', 'unit_antlion'], 
                                  [0.5, 0.51, 0.5, 0.5]),
            },

        14: {
                'distribution' : (['unit_hunter', 'unit_crab_synth'], 
                                  [0.5, 0.58]),
            },

        15: {
                'distribution' : (['unit_hunter', 'unit_crab_synth', 'overrun_unit_mortar_synth', 'unit_combine_heavy', 'unit_rebel_flamer', 
                                   'unit_rebel_heavy', 'unit_rebel_rpg','unit_vortigaunt','unit_headcrab_poison_boss','unit_antlionguardcavernboss'], 
                                  [0.25, 0.25, 0.1, 0.3, 0.3, 0.3, 0.05, 0.05, 0.01, 0.01]),
                #'waveincome' : 0,
                #'waveincomegrow' : 0.0, 
            },

        16: {
                'distribution' : (['unit_headcrab_poison_boss'], 
                                  [1.0]),
            }, 
        17: {
                'distribution' : (['unit_antlionguardcavernboss', 'unit_rebel_tau'], 
                                  [1.0, 1.0]),
            }, 
        18: {
                'distribution' : (['unit_dog', 'unit_rebel_rpg'], 
                                  [0.5, 0.58]),
            }, 
        19: {
                'distribution' : (['unit_strider'], 
                                  [1.0]),
            }, 

        20: {
                'distribution' : (['unit_strider', 'overrun_unit_mortar_synth', 'unit_dog', 'unit_rebel_rpg', 'unit_crab_synth', 'unit_rebel_flamer', 
                                   'unit_antlionguardcavernboss', 'unit_antlionsuicider' ,'unit_headcrab_poison_boss'], 
                                  [0.05, 0.2, 0.3, 0.4, 1.0, 0.6, 0.01, 0.01, 0.01]),
                'waveincome' : 0,
                'waveincomegrow' : 0.0, 
                
            },
        21: {
                'distribution' : (['unit_headcrab_poison_boss', 'unit_poisonzombieboss'], 
                                  [0.5, 0.6]),
            }, 
        22: {
                'distribution' : (['unit_antlionworker', 'unit_combine_elite'], 
                                  [1.0, 1.0]),
            }, 
        23: {
                'distribution' : (['unit_rebel_engineer', 'unit_rebel_tau'], 
                                  [0.5, 0.6]),
            }, 
        24: {
                'distribution' : (['unit_combine_citizen', 'unit_hunter'], 
                                  [0.5, 0.6]),
            }, 

        25: {
                'distribution' : (['overrun_unit_mortar_synth', 'unit_dog', 'unit_antlionsuicider', 'unit_headcrab_poison_boss'], 
                                  [0.2, 0.7, 0.7, 0.01]),
                #'waveincome' : 0,
                #'waveincomegrow' : 0.0, 
                
            },
        26: {
                'distribution' : (['unit_headcrab_poison_boss', 'unit_poisonzombieboss', 'unit_zombine'], 
                                  [0.5, 0.5, 0.9]),
            }, 
        27: {
                'distribution' : (['unit_antlionsuicider', 'unit_antlionguardcavernboss', 'unit_antlionworker'], 
                                  [1.0, 1.0, 1.0]),
            }, 
        28: {
                'distribution' : (['unit_rebel_rpg', 'unit_rebel_heavy', 'unit_dog'], 
                                  [0.5, 0.65, 1.0]),
            }, 
        29: {
                'distribution' : (['unit_crab_synth', 'unit_strider', 'overrun_unit_mortar_synth'], 
                                  [0.5, 0.75, 1.0]),
            }, 

        30: {
                'distribution' : (['overrun_unit_mortar_synth', 'unit_dog', 'unit_antlionsuicider', 'unit_headcrab_poison_boss',
                                   'unit_crab_synth', 'unit_rebel_heavy', 'unit_antlionguardcavernboss', 'unit_poisonzombieboss',
                                   'unit_strider', 'unit_rebel_rpg', 'unit_antlionworker', 'unit_zombine'], 
                                  [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]),
                
            },
        31: {
                'distribution' : (['unit_strider', 'unit_dog', 'unit_antlionsuicider', 'unit_headcrab_poison_boss'], 
                                  [1.0, 1.0, 1.0, 1.0]),
                
            },
    }
    

class InfectedWaveType(BaseWaveType):
    name = 'infected'
    
    @classmethod
    def ShouldAddWaveType(cls):
        return 'l4d' in dbgamepackages.keys() and dbgamepackages['l4d'].loaded
    
    distribution = {
        0: {
                # Prepare time
                'easy_waveinterval' : 70,
                'normal_waveinterval' : 60,
                'hard_waveinterval' : 45,
                
                HModHard('unit_infected') : 1.2,
            },
            
        1: {
                'distribution' : (['unit_infected'],
                                  [1.0]),
                                  
                'spawnsize' : 25,
                'growrate' : 1.15,
                'maxenemiesalive' : 8,
                
                'waveincome' : 5,
                'waveincomegrow' : 1.15,
            },
        4: {
                HModGrowEasy('unit_infected') : 1.05,
                HModGrowNormal('unit_infected') : 1.2,
                HModGrowHard('unit_infected') : 1.3,
            },
        6: {
                'waveintervaldecreaserate' : 1, # At this point we added a lot of time, so we start decreasing again.
            },
        10: {
                'growrate' : 1.10,
                'waveincomegrow' : 1.10,
            },
            
        20: {
                'waveincomegrow' : 1.0,
             },
    }
    
if isserver:
    @concommand('overrun_nextwave', 'Spawn the next wave.', FCVAR_CHEAT)
    def cc_overrun_nextwave(args):
        if gamerules.info.name != OverrunInfo.name:
            print('Overrun mode not active.')
            return
        gamerules.SpawnWave()

    def GetWaveTypes():
        if gamerules.info.name != OverrunInfo.name:
            return []
        return dbwavetypes.keys()
    
    @concommand('overrun_setwavetype', 'Changes the wave type.', FCVAR_CHEAT, completionfunc=AutoCompletion(GetWaveTypes))
    def cc_overrun_setwavetype(args):
        if gamerules.info.name != OverrunInfo.name:
            return
        if args[1] not in dbwavetypes.keys():
            PrintWarning('Invalid wave type. Valid options are: %s' % (str(dbwavetypes.keys())))
            return
        gamerules.wavetype = args[1]
        
    @concommand('overrun_debug_status', 'Prints current status.', FCVAR_CHEAT)
    def cc_overrun_debug_status(args):
        if gamerules.info.name != OverrunInfo.name:
            print('Overrun mode not active.')
            return
        print('OVERRUN STATUS: ')
        print('\tlast activity seconds ago: %f, timeout: %f' % (gpGlobals.curtime - gamerules.lastactivitytime, gamerules.inactivitytimeout))
        print('\twave: %d' % (gamerules.wave))
        print('\tspawnsleft: %d' % (gamerules.spawnsleft))
        print('\tspawnsize: %d' % (gamerules.spawnsize))
        print('\tmaxenemiesalive: %d' % (gamerules.maxenemiesalive))
        print('\thealth modifiers: ')
        for unit, modifier in gamerules.healthmodifiers.items():
            print('\t\t%s -> %f ' % (unit, modifier))
        print('\thealth grow modifiers: ')
        for unit, modifier in gamerules.healthgrowmodifiers.items():
            print('\t\t%s -> %f ' % (unit, modifier))
            
    @concommand('overrun_stresstest_mode', 'Activates Overrun stress test mode for the current enemy type.', FCVAR_CHEAT)
    def cc_overrun_stresstest_mode(args):
        # Make all buildings take no damage
        for o, l in buildinglist.items():
            for b in l:
                b.takedamage = DAMAGE_NO
                
        # Go to last wave
        lastwave = max(gamerules.waveinfo.distribution.keys())
        while gamerules.wave < lastwave:
            gamerules.SpawnWave()
        gamerules.spawnsize = 1000
        gamerules.maxenemiesalive = 10000
        
        # Give resources
        players = gamerules.GetRealPlayers()
        owners = set([p.GetOwnerNumber() for p in players])
        for ownernumber in owners:
            GiveResources(ownernumber, [(ResKillsInfo, 10000)], firecollected=False)
        
        # Set interval to zero
        gamerules.waveinterval = 0

class OverrunInfo(GamerulesInfo):
    name = 'overrun'
    displayname = '#Overrun_Name'
    description = '#Overrun_Description'
    cls = Overrun
    mappattern = '^or_.*$'
    factionpattern = '^overrun_.*$'
    useteams = False
    supportcpu = True
    huds = GamerulesInfo.huds + [
        'wars_game.hud.HudOverrun',
        'core.hud.HudPlayerNames',
    ]
