from vmath import vec3_origin, QAngle, VectorAngles, VectorNormalize
from core.units import CreateUnitFancy
from utils import UTIL_RemoveImmediate
from readmap import StringToVector

import re
from collections import defaultdict
import traceback

class BalanceTest(object):
    def __init__(self, filename, testname, definition):
        super().__init__()
        
        self.filename = filename
        self.testname = testname
        self.definition = definition
        self.stepnum = 0
        
        self.groups = defaultdict(dict)
        
        self.recordedhealth = defaultdict(lambda: False)
        self.recordedcosts = False
        
        self.info = []
        self.errors = []
        
    def AddInfo(self, info):
        self.info.append(info)
        print(info)
    def AddError(self, error):
        self.errors.append(error)
        PrintWarning('%s\n' % (error))
        
    def Cleanup(self):
        for group in self.groups.values():
            for unit in group.get('units', []):
                if not unit:
                    continue
                UTIL_RemoveImmediate(unit)
                
    def CreateGroup(self, step):
        groupname = step['name']
        
        group = self.groups[groupname]
        
        # Setup defaults
        group['units'] = []
        group['prehealth'] = defaultdict(lambda: 0)
        group['costs'] = defaultdict(lambda: defaultdict(lambda: 0))
    
        units = step.get('unit', [])
        units = units if type(units) == list else [units]
        for unitdef in units:
            spawnpos = StringToVector(unitdef['origin'])
            
            angles = QAngle()
            dir = vec3_origin - spawnpos
            VectorNormalize(dir)
            VectorAngles(dir, angles)
            
            amount = unitdef.get('amount', 1)
            for i in range(0, amount):
                unit = CreateUnitFancy(unitdef['unittype'], position=spawnpos, angles=angles, owner_number=int(unitdef['owner']))
                group['units'].append(unit)
                        
    def GetTotalHealthForGroup(self, groupname):
        group = self.groups[groupname]
        totalhp = 0
        for unit in group.get('units', []):
            if not unit:
                continue
            totalhp += unit.health
        return totalhp
        
    def GetTotalCostsForGroup(self, groupname):
        group = self.groups[groupname]
        totalhp = 0
        costs = defaultdict(lambda: 0)
        for unit in group.get('units', []):
            costset = []
            for testset in unit.unitinfo.costs:
                for c in testset:
                    if c[0] == 'requisition':
                        costset = testset
                        break
                if costset: break
                
            if not costset:
                continue
                
            for c in costset:
                costs[c[0]] += c[1]
        return costs
                
    def RecordHealth(self, variablename='prehealth'):
        if self.recordedhealth[variablename]:
            return
        self.recordedhealth[variablename] = True
        for groupname, group in self.groups.items():
            group[variablename] = self.GetTotalHealthForGroup(groupname)
            group[variablename+'_fract'] = group[variablename] / group['prehealth']
            self.AddInfo('%s for group "%s": %s (fract %f)' % (variablename, groupname, group[variablename], group[variablename+'_fract']))
            
    def RecordCosts(self):
        if self.recordedcosts:
            return
        self.recordedcosts = True
        for groupname, group in self.groups.items():
            group['costs'] = self.GetTotalCostsForGroup(groupname)
            self.AddInfo('Costs for group "%s": %s' % (groupname, str(dict(group['costs']))))
            
    def GetHealthFractGroupAfterRun(self, groupname):
        group = self.groups[groupname]
        print('Before health: %f' % (group['prehealth']))
        print('Cur health: %f' % (self.GetTotalHealthForGroup(groupname)))
        return self.GetTotalHealthForGroup(groupname) / group['prehealth']
            
    def GetAliveGroupsCount(self):
        count = 0
        for k, v in self.groups.items():
            units = v['units']
            if len(list(filter(bool, units))) > 0:
                count += 1
        return count
                        
    def IsOnlyGroupLeft(self, groupname):
        count = self.GetAliveGroupsCount()
        if count == 1 and len(list(filter(bool, self.groups[groupname]['units']))) > 0:
            return True
        return False
        
    def UpdateSteps(self):
        if not self.started:
            self.started = True
            print('Running test %s from package %s' % (self.testname, self.filename))
    
        if self.waitendtime > gpGlobals.curtime:
            return True
       
        if not self.definition:
            return False
            
        while True:
            #print('definition: %s' % (str(self.definition)))
            step = self.definition.get(str(self.stepnum), None)
            if not step:    
                break
            
            steptype = step.get('type', None)
            if not steptype:
                print('Invalid step in %s' % (self.filename))
                continue
                
            if steptype == 'spawn':
                self.stepnum += 1
                self.CreateGroup(step)
            elif steptype == 'run_until_one_is_left':
                self.RecordHealth(variablename='prehealth')
                self.RecordCosts()
                if self.GetAliveGroupsCount() > 1:
                    return True
                self.RecordHealth(variablename='posthealth')
                self.stepnum += 1
            elif steptype == 'expectations':
                expwinnergroup = step['winner']
                self.expectedwinner = expwinnergroup
                
                # See if the expected group won
                won = self.IsOnlyGroupLeft(expwinnergroup)
                if won:
                    self.AddInfo('Group %s won as expected' % (expwinnergroup))
                else:
                    self.AddError('Group %s did not win as expected' % (expwinnergroup))
                    
                # Only evaluate remaining if the expected group won
                if won:
                    wingroup = self.groups[expwinnergroup]
                
                    wingroup_hpleft = self.GetTotalHealthForGroup(expwinnergroup)
                    dmgreceived = wingroup['prehealth'] - wingroup_hpleft
                    dmgreceived_fract = dmgreceived / wingroup['prehealth']
                   
                    # Calculate the cost for the damage done
                    # 1. Calculate the damage per cost point for damage received and dealt
                    winnercosts = wingroup['costs']
                    costsothergroup = defaultdict(lambda: 0)
                    dmgdid_hp = 0
                    
                    costdmgreceived = defaultdict(lambda: 0)
                    costdmgdid = defaultdict(lambda: 0)
                    
                    resourcekeys = set()
                    for groupname, group in self.groups.items():
                        resourcekeys |= set(group['costs'].keys())
                        if groupname == expwinnergroup:
                            continue
                        dmgdid_hp += group['prehealth']
                        for k, c in group['costs'].items():
                            costsothergroup[k] += c
  
                    for reskey in resourcekeys:
                        # Damage received per resource point of attack. Say do 40 damage, cost 10, then it's 4 damage per resource point
                        if costsothergroup[reskey]:
                            costdmgreceived[reskey] = dmgreceived / costsothergroup[reskey]
                        else:
                            costdmgreceived[reskey] = float('inf')

                        if winnercosts[reskey]:
                            costdmgdid[reskey] = dmgdid_hp / (winnercosts[reskey]*dmgreceived_fract)
                        else:
                            costdmgdid[reskey] = float('inf')
                            
                    self.AddInfo('Damage per resource point received to "%s" from "other groups": %s' % (expwinnergroup, str(dict(costdmgreceived))))
                    self.AddInfo('Damage per resource point given from "%s" to "other groups": %s' % (expwinnergroup, str(dict(costdmgdid))))
                    
                    self.costdmgreceived = costdmgreceived
                    self.costdmgdid = costdmgdid
                    
                    self.costeffectiveness = defaultdict(lambda: 0)
                    for k, v in costdmgreceived.items():
                        self.costeffectiveness[k] = costdmgdid[k] - costdmgreceived[k]
                        wingroup['costeffectiveness_%s' % (k)] = self.costeffectiveness[k]
                        
                    # Test conditions for winner group
                    conditions = step.get('winner_condition', [])
                    if type(conditions) != list:
                        conditions = [conditions]
                    for cond in conditions:
                        try:
                            # Test for "number<varname<numer" construction, testing if the variable is in range
                            match = re.search('^(?P<lower>.*)<(?P<varname>.*)<(?P<upper>.*)$', cond)
                            if match:
                                lower = float(match.group('lower'))
                                upper = float(match.group('upper'))
                                varname = match.group('varname')
                                
                                value = float(wingroup[varname])
                                if value < lower:
                                    self.AddError('Winner condition: %s does not meet expected lower bound "%.2f". Found %.2f instead.' % (varname, lower, value))
                                elif value > upper:
                                    self.AddError('Winner condition: %s does not meet expected upper bound "%.2f". Found %.2f instead.' % (varname, upper, value))
                                else:
                                    self.AddInfo("Winner condition: %s meets condition %s. Actual value is %.2f" % (varname, cond, value))
                                continue
                        except:
                            PrintWarning("Malformed conditions: %s\n" % (cond))
                            traceback.print_exc()
                
                self.stepnum += 1
            else:
                print('Unknown step %s' % (steptype))
                self.stepnum += 1
    
        return False
        
    started = False
    waitendtime = 0
    
    # For reports:
    expectedwinner = None
    costdmgreceived = None
    costdmgdid = None
    costeffectiveness = None
