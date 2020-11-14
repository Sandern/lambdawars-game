import random
import traceback
from operator import attrgetter
from collections import defaultdict

from vmath import vec3_origin
from gameinterface import concommand, ConVar, FCVAR_CHEAT

from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from playermgr import SimulatedPlayer, relationships, ListAlliesOfOwnerNumber
from profiler import profile
from entities import D_LI, entitylist
from gamerules import gamerules
from navmesh import NavMeshGetPathDistance

from core.units import GetUnitInfo, unitlist, unitlistpertype, CreateUnit
from core.buildings import buildinglist
from core.signals import (buildingstarted, buildingfinished, unitspawned, unitchangedownernumber, cp_fortified,
                          cp_fortificationdestroyed)
from core.resources import resources

from .info import StrategicAIInfo, strategicplayers
from .abilityrules import dbabilityrules, AbilityRuleBase
from .groups import dbgroups

wars_strategicai_debug = ConVar('wars_strategicai_debug', '0', FCVAR_CHEAT)

wars_strategicai_debug_rules = ConVar('wars_strategicai_debug_rules', '0', FCVAR_CHEAT)

def SAIMsg(msg, verbose=1):
    if wars_strategicai_debug.GetInt() >= verbose:
        print(msg)

class StrategicAIDefault(StrategicAIInfo):
    """ Default base Strategic AI. """
    destroying = False
    
    name = 'cpu_wars_default'
    displayname = 'CPU'
    
    pendingpopulationcount = 0
    accumulatingrequisition = False
    
    def __init__(self, ownernumber, difficulty='medium'):
        super().__init__()
        
        if difficulty == None:
            difficulty = 'medium'

        self.ownernumber = ownernumber

        self.player = SimulatedPlayer(ownernumber)
        
        self.buildings = set()
        self.groups = set()
        
        self.executerules = []
        self.executerulestypes = set()
        self.ruletypelastexecuted = defaultdict(lambda: 0)
        
        # List of currently excluded group categories
        self.excludegroupcats = set([])
        
        # Count units per hint
        self.hintunitcounts = defaultdict(lambda: 0)
        self.groupcounts = defaultdict(lambda: 0)
        
        self.difficulty = difficulty

    def Initialize(self):
        SAIMsg('SAI#%d Initialize' % (self.ownernumber))
    
        # Use think rates as an indirect way to slow down decision making
        thinkrate = 0.8
        if self.difficulty <= self.difficulty_easy:
            thinkrate = 1.5
        elif self.difficulty >= self.difficulty_hard:
            thinkrate = 0.1
        RegisterTickMethod(self.Update, thinkrate)
        
        buildingstarted.connect(self.OnBuildingStarted)
        buildingfinished.connect(self.OnBuildingConstructed)
        unitspawned.connect(self.OnUnitSpawned)
        unitchangedownernumber.connect(self.OnUnitChangedOwner)
        
        # TODO: Should be in wars_game package
        cp_fortified.connect(self.OnCPFortificationChanged)
        cp_fortificationdestroyed.connect(self.OnCPFortificationChanged)
        
        self.RebuildBuildingList()
        self.RebuildUnitList()
        self.RecomputeIncomeRate()
        self.RecalcPendingPopulationCount()
        
    def Shutdown(self):
        SAIMsg('SAI#%d Shutdown' % (self.ownernumber))
        
        self.destroying = True
        
        del self.executerules[:]
        self.executerulestypes.clear()
        
        # Might already be unregistered due crashing in the Update method
        if IsTickMethodRegistered(self.Update):
            UnregisterTickMethod(self.Update)
        
        buildingstarted.disconnect(self.OnBuildingStarted)
        buildingfinished.disconnect(self.OnBuildingConstructed)
        unitspawned.disconnect(self.OnUnitSpawned)
        unitchangedownernumber.disconnect(self.OnUnitChangedOwner)
        
        # TODO: Should be in wars_game package
        cp_fortified.disconnect(self.OnCPFortificationChanged)
        cp_fortificationdestroyed.disconnect(self.OnCPFortificationChanged)
        
        # Kill all groups
        for g in list(self.groups):
            try:
                g.DisbandGroup()
            except:
                traceback.print_exc()
        self.groups = set([])
        
    def OnRestore(self):
        ''' Called after restoring the cpu player from a save file. '''
        pass
        
    __difficulty = None
    @property
    def difficulty(self):
        return self.__difficulty
    @difficulty.setter
    def difficulty(self, difficulty):
        if type(difficulty) == str:
            difficulty = getattr(self, 'difficulty_%s' % (difficulty), self.difficulty_medium)
            
        if difficulty not in self.supporteddifficulties.values():
            PrintWarning('CPU difficulty "%s" not found in supported difficulties. Defaulting to medium...\n' % (difficulty))
        
        if self.__difficulty == difficulty:
            return
        self.__difficulty = difficulty
            
        for name, diffvalue in self.supporteddifficulties.items():
            if diffvalue == difficulty:
                self.difficultyname = name
                break
            
        self.UpdateDifficulty()
        
    def UpdateDifficulty(self):
        ''' Updates difficulty settings. Called when the difficulty setting changed. '''
        # Remove attacking group on easy
        if self.difficulty <= self.difficulty_easy:
            self.excludegroupcats.add('attack')
        else:
            self.excludegroupcats.discard('attack')
    
        # Used for determining how much resources the CPU should at least have before building something
        # On lower difficulties, require more
        self.scaleminres = 1.15
        if self.difficulty <= self.difficulty_easy:
            self.scaleminres = 2
        elif self.difficulty >= self.difficulty_hard:
            self.scaleminres = 1
        
    # Initializing
    def RebuildBuildingList(self):
        SAIMsg('SAI#%d RebuildBuildingList len=%d' % (self.ownernumber, len(buildinglist[self.ownernumber])))
        for b in buildinglist[self.ownernumber]:
            if not b.isconstructed:
                continue
            self.OnBuildingConstructed(b)
            
    def RebuildUnitList(self):
        for unit in unitlist[self.ownernumber]:
            if unit.sai_group and unit.sai_group.sai == self:
                continue
            self.OnUnitSpawned(unit)
            
    def RecalcPendingPopulationCount(self):
        self.pendingpopulationcount = 0
        for b in buildinglist[self.ownernumber]:
            if b.isconstructed:
                continue
            self.pendingpopulationcount += b.unitinfo.providespopulation
        
    # Signals listeners
    def OnBuildingStarted(self, building, *args, **kwargs):
        ''' Called when construction of building is started. '''
        if building.unitinfo.providespopulation:
            self.RecalcPendingPopulationCount()
    
    def OnBuildingConstructed(self, building, *args, **kwargs):
        ''' Called when construction of building is finished. '''
        unitinfo = building.unitinfo
        if building.GetOwnerNumber() != self.ownernumber:
            if unitinfo.generateresources and relationships[(self.ownernumber, building.GetOwnerNumber())] == D_LI:
                self.RecomputeIncomeRate()
            return
            
        self.buildings.add(building.GetHandle())
        
        if unitinfo.generateresources:
            self.RecomputeIncomeRate()
        if unitinfo.providespopulation:
            self.RecalcPendingPopulationCount()
    
    def OnUnitSpawned(self, unit, *args, **kwargs):
        self.OnAddNewUnit(unit)
        
    def OnUnitChangedOwner(self, unit, *args, **kwargs):
        self.OnAddNewUnit(unit)
        
        if unit.isbuilding:
            if unit.GetOwnerNumber() != self.ownernumber:
                if unit in self.buildings:
                    self.buildings.discard(unit)
                if unit.unitinfo.generateresources and relationships[(self.ownernumber, unit.GetOwnerNumber())] == D_LI:
                    self.RecomputeIncomeRate()
            else:
                self.OnBuildingConstructed(unit)
                
    def OnCPFortificationChanged(self, building, *args, **kwargs):
        self.RecomputeIncomeRate()
        
    def OnAddNewUnit(self, unit):
        try:
            if not unit.handlesactive:
                return
            if unit.GetOwnerNumber() != self.ownernumber:
                return
            if unit.sai_group and unit.sai_group.sai == self:
                return
        except AttributeError:
            traceback.print_exc()
            return # Not an unit
            
        SAIMsg('SAI#%d OnAddNewUnit unit=%s' % (self.ownernumber, str(unit)))
            
        self.FindGroupForUnit(unit)
    
    
    # Groups management
    def FindGroupForUnit(self, unit):
        if self.destroying:
            return
        
        # Find a potential best new group
        bestnewgroup = self.FindNewGroupForUnit(unit)
            
        # First check existing groups
        for group in self.groups:
            if group.disbanding:
                continue
                
            if bestnewgroup and group.priority < bestnewgroup.priority:
                continue
                
            try:
                if group.TryAddUnit(unit):
                    return
            except:
                traceback.print_exc()
                
        # Did not find an existing group, so create a new one
        if bestnewgroup:
            bestnewgroup.AddUnit(unit)
            bestnewgroup.Init()

    def IsGroupTypeAllowed(self, groupcls):
        """ Tests if group is allowed.

            Args:
                groupcls (object): cls to be tested
        """
        return not groupcls.category or groupcls.category not in self.excludegroupcats
            
    def FindNewGroupForUnit(self, unit):
        bestgroup = None
    
        groupsinfo = []
        for groupcls in dbgroups.values():
            if not self.IsGroupTypeAllowed(groupcls):
                #print('Category for %s not allowed' % (str(groupcls)))
                continue
        
            try:
                group = groupcls(self)
                if group.MatchesUnit(unit):
                    groupsinfo.append(group)
                #else:
                #    print('no match for %s (unit: %s, unit hints: %s, group hints: %s)' % (str(groupcls), 
                #          str(unit.unitinfo), str(unit.unitinfo.sai_hint), groupcls.matchunithints))
            except:
                traceback.print_exc()
                continue
                
        if groupsinfo:
            groupsinfo.sort(key=attrgetter('priority'), reverse=True)
            samepriorgroups = []
            prior = groupsinfo[0].priority
            for g in groupsinfo:
                if g.priority != prior:
                    break
                samepriorgroups.append(g)
                
            random.shuffle(samepriorgroups)
            bestgroup = samepriorgroups[0]
        else:
            DevMsg(1, 'No group found for unit #%d:%s\n' % (unit.entindex(), str(unit.unitinfo.name)))
            
        return bestgroup
            
    # Ability rules (i.e. decide on what ability to execute)
    def BuildAbilityRules(self, unit):
        abirules = []
        for rule in dbabilityrules.values():
            try:
                r = rule(self, unit)
                if r.MatchesUnit(unit):
                    abirules.append(r)
            except:
                traceback.print_exc()
        return abirules
        
    def GetAbilityRules(self, unit):
        # Get rules
        sai_abirules = getattr(unit, 'sai_abirules', None)
        if not sai_abirules:
            unit.sai_abirules = self.BuildAbilityRules(unit)
            sai_abirules = unit.sai_abirules
        return sai_abirules

    def FindRuleAndAdd(self, unit, rules):
        # Copy keys of abilities, used for filtering
        unit.sai_abilities = set(unit.abilities.values())
        
        # Update priorities on this unit and sort the rules on it
        [rule.UpdatePriority() for rule in rules]
        rules.sort(key=attrgetter('priority'), reverse=True)
        
        # Find best rule, but don't execute it yet (there might be better options)
        ra = None
        for rule in rules:
            if rule.priority < -20 or (rule.expectedcosts and self.accumulatingrequisition):
                continue
        
            rule.PreFindRuleAction()
            ra = rule.FindRuleAction()
            if ra:
                break
                
        if ra and ra != AbilityRuleBase.STOPSEARCH:
            self.executerules.append(ra)
            self.executerulestypes.add(ra.name)
        
    # Main functions
    def UpdateHintUnitCounts(self):
        self.hintunitcounts.clear()
        
        for unittype, l in unitlistpertype[self.ownernumber].items():
            info = GetUnitInfo(unittype, fallback=None)
            if not info:
                continue
            for hint in info.sai_hint:
                self.hintunitcounts[hint] += len(l)
                
    def UpdateGroupCounts(self):
        self.groupcounts.clear()
        
        for g in self.groups:
            self.groupcounts[g.name] += 1
            
    # TODO: Make this better :)
    controlpoint_types = [
        'control_point',
        'control_point_reb_lvl1',
        'control_point_reb_lvl2',
        'control_point_comb_lvl1',
        'control_point_comb_lvl2',
    ]
    def RecomputeIncomeRate(self):
        ''' Computes a dictionary incomerates with the rate of income per 
            resource type. The computed rate is per minute.
        '''
        self.incomerates = defaultdict(lambda: 0)
        incomecounts = defaultdict(lambda: 0)
        
        owners = ListAlliesOfOwnerNumber(self.ownernumber)
        
        for b in self.buildings:
            if not b or not b.unitinfo.generateresources:
                continue
                
            info = b.unitinfo
            genres = info.generateresources
            splitfactor = 1.0 / float(len(owners)) if info.reducesplittedresources else 1
            self.incomerates[genres['type']] += ((genres['amount']*splitfactor) / genres['interval']) * 60.0
            incomecounts[genres['type']] += 1
            
        # Add allies (shared income)
        for owner in owners:
            if owner == self.ownernumber:
                continue
            for cpunittype in self.controlpoint_types:
                for cp in unitlistpertype[owner][cpunittype]:
                    if not cp or not cp.unitinfo.generateresources:
                        continue
                    info = cp.unitinfo
                    genres = info.generateresources
                    splitfactor = 1.0 / float(len(owners)) if info.reducesplittedresources else 1
                    self.incomerates[genres['type']] += ((genres['amount']*splitfactor) / genres['interval']) * 60.0
                    incomecounts[genres['type']] += 1
            
        self.incomecounts = incomecounts
        SAIMsg('SAI#%d RecomputeIncomeRate incomerates=%s' % (self.ownernumber, str(self.incomerates)))
            
    @profile('StrategicAIDefault.Update')
    def Update(self):
        # Must be valid
        if not self.IsValidAI(self):
            self.Shutdown()
            return
            
        # Check if we should execute abilities which cost something
        # Hover some resources before making a decision
        # Only do this if the main resource is requisition.
        # For Overrun, just keep spending.
        if gamerules.GetMainResource() == 'requisition':
            restype = 'requisition'
            minres = int(max(92*self.scaleminres, self.incomerates[restype]*self.scaleminres))
            self.accumulatingrequisition = resources[self.ownernumber][restype] < minres
        else:
            self.accumulatingrequisition = False
            
        # Update counts
        self.UpdateHintUnitCounts()
        self.UpdateGroupCounts()
        
        # Clear old selected rules
        del self.executerules[:]
        self.executerulestypes.clear()
        
        # Update groups (i.e. one or more units)
        # Orders them around
        # Might add rules to execute
        for g in list(self.groups):
            g.Update()
        
        debugrules = wars_strategicai_debug_rules.GetInt()
        
        # Execute the top rules. Just keep going until we find a rule we can't execute.
        random.shuffle(self.executerules) # Add randomness for same priority rules
        self.executerules.sort(key=attrgetter('priority'), reverse=True)
        for ra in self.executerules[0:10]:
            if not ra.ExecuteRuleAction():
                if debugrules:
                    DevMsg(1, '%.2f:SAI#%d Skipped rule %s (%s) with priority %d. Reason: %s\n' % (gpGlobals.curtime, self.ownernumber, ra.name, getattr(ra, 'ability', None), ra.priority, ra.DebugReasonFailed()))
                continue
            ra.executed = True
            if debugrules:
                DevMsg(1, '%.2f:SAI#%d Executed rule %s (%s) with priority %d\n' % (gpGlobals.curtime, self.ownernumber, ra.name, getattr(ra, 'ability', None), ra.priority))
            self.ruletypelastexecuted[ra.name] = gpGlobals.curtime
            
    # Useful methods
    def FindNearest(self, classnames, origin, filter=None):
        classnames = [classnames] if type(classnames) == str else classnames
        for classname in classnames:
            cur = entitylist.FindEntityByClassname(None, classname) 
            best = None
            while cur:
                if not filter or filter(cur):
                    dist = NavMeshGetPathDistance(origin, cur.GetAbsOrigin())
                    if dist >= 0:
                        if not best:
                            best = cur
                            bestdist = dist
                        else:
                            if dist < bestdist:
                                best = cur
                                bestdist = dist
                cur = entitylist.FindEntityByClassname(cur, classname)
        return best
    
    # Debug
    def PrintDebug(self):
        print('Debug information for strategic AI %d (difficulty: %s)' % (self.ownernumber, self.difficultyname))
        print('\tIncome rates: %s' % (str(self.incomerates)))
        print('\tIncome sources and counts: %s' % (str(self.incomecounts)))
        print('\tBuildings: %d' % (len(self.buildings)))
        print('\tGroups: %d' % (len(self.groups)))
        print('\tHint Unit Counts:')
        for h, c in self.hintunitcounts.items():
            print('\t\t%s: %d' % (h, c))
        print('\tLast ability rules:')
        for ra in self.executerules:
            print('Cost: %s, ra: %s, executed: %s' % (str(ra.expectedcosts), ra.__class__.__name__, str(ra.executed)))
        print('\tPrinting group counts:')
        for name, count in self.groupcounts.items():
            print('\t\t%s: %d' % (name, count))
        print('\tscaleminres: %f' % (self.scaleminres))
        print('\tpendingpopulationcount: %d' % (self.pendingpopulationcount))
        print('\taccumulatingrequisition: %s' % (self.accumulatingrequisition))
            
if isserver:
    @concommand('wars_strategicai_debug_testgroupfind', flags=FCVAR_CHEAT)
    def DebugStrategicAITestGroupFind(args):
        ownernumber = int(args[1])
        if ownernumber in strategicplayers:
            unit = CreateUnit(args[2], vec3_origin, owner_number=ownernumber)
            try:
                strategicplayers[ownernumber].FindNewGroupForUnit(unit)
            except:
                traceback.print_exc()
            unit.Remove()
        else:
            print('No strategic AI for %d' % (ownernumber))
        