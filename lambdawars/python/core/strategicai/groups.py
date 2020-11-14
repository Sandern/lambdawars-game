import random
import traceback

from vmath import Vector, vec3_origin
import ndebugoverlay
from gamemgr import dblist, BaseInfo, BaseInfoMetaclass
from entities import entitylist, Disposition_t, MouseTraceData
from navmesh import NavMeshGetPathDistance, RandomNavAreaPosition
from core.abilities import DoAbilitySimulated
from core.buildings import buildinglist
from core.units import unitlist, unitlistpertype
from playermgr import SimulatedPlayer, relationships
from utils import UTIL_FindPositionSimple

dbid = 'strategicai_groups'
dbgroups = dblist[dbid]


class GroupBaseMetaClass(BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = BaseInfoMetaclass.__new__(cls, name, bases, dct)

        # For convenience, allow defining the hint as a single set
        if type(newcls.matchunithints) == set:
            newcls.matchunithints = [newcls.matchunithints]

        return newcls


class GroupBase(BaseInfo, metaclass=GroupBaseMetaClass):
    """ Base group. Provides methods for managing the group,
        but does not contain information about the goal of the group.

        Note that you can't decide on what units you will get.
        The production of rules is separated from groups and is part
        of the abilityrules. These rules will decide on what's best
        to produce.
    """

    id = dbid
    autogenname = True
    priority = 0

    #: Category of this group type. Used to filter groups by the CPU player.
    category = ''

    #: Hints for matching an unit to this group. You may specify multiple sets.
    matchunithints = []

    #: State of group. Can be used for executing different behavior.
    state = 'active'

    removed = False
    disbanding = False
    changingtonewgroup = False

    # Methods for strategic AI
    def MatchesUnit(self, unit):
        ''' Tests if this unit can be added to this type of groups. '''
        hints = unit.unitinfo.sai_hint
        for testhints in self.matchunithints:
            if testhints <= hints:
                return True
        return False

    def TryAddUnit(self, unit):
        ''' Decide on whether to add this unit to this existing group. '''
        return False

    # Group Management methods
    def __init__(self, sai):
        super().__init__()

        self.sai = sai
        self.units = set()

    def Init(self):
        self.fnstates = {}
        self.CreateStateMethods()
        self.sai.groups.add(self)

    def Remove(self):
        self.sai.groups.discard(self)
        self.removed = True

    def DisbandGroup(self):
        ''' Disband group to allow assiging/creating new groups from the freed units. '''
        if self.disbanding:
            return
        self.sai.groupcounts[
            self.name] -= 1  # Ensure units don't count this as a group when finding/creating a new group
        self.disbanding = True
        self.Validate()
        [self.RemoveUnit(u) for u in list(self.units)]
        assert (self.removed)

    def ChangeToNewGroup(self, newgroup):
        # Make a copy of the units group, then disband this group and hand over to the new group
        units = list(self.units)
        self.changingtonewgroup = True
        self.DisbandGroup()
        for unit in units:
            newgroup.AddUnit(unit)

    def Validate(self):
        ''' Makes sure this group still exists, otherwise removes
            the group. '''
        owner = self.sai.ownernumber
        self.units = set([unit for unit in self.units if unit and unit.IsAlive() and unit.GetOwnerNumber() == owner])
        valid = len(self.units) > 0
        if not valid:
            self.Remove()
            return False
        return True

    def AddUnit(self, unit):
        assert (not self.disbanding)
        h = unit.GetHandle()
        unit.sai_group = self
        self.units.add(h)

    def RemoveUnit(self, unit):
        ''' Removes a non dead unit from the group and
            hands it over back to the cpu player.'''
        try:
            h = unit.GetHandle()
            unit.sai_group = None
            self.units.discard(h)
            if not self.changingtonewgroup:
                self.sai.FindGroupForUnit(unit)  # Hand it back over to the cpu player to find a new group
        except:
            traceback.print_exc()
            self.units.discard(unit)

        if not self.units:
            self.Remove()

    # Main methods
    def CreateStateMethods(self):
        self.fnstates.update({
            'inactive': self.StateInActive,
            'active': self.StateActive,
        })

    def Update(self):
        ''' Update goal of the group. Move units around.'''
        if not self.Validate():
            return
        try:
            self.fnstates[self.state]()
        except:
            traceback.print_exc()

    def StateInActive(self):
        assert (0)

    def StateActive(self):
        assert (0)

    # Convenient to order units around
    def Order(self, position, target=None):
        data = MouseTraceData()
        data.endpos = position
        data.groundendpos = position
        data.ent = target

        self.sai.player.rightmousepressed = data
        self.sai.player.rightmousedoublepressed = data
        self.sai.player.rightmousereleased = data

        for unit in self.units:
            unit.Order(self.sai.player)

    def MoveOrder(self, position, target=None):
        for unit in self.units:
            unit.MoveOrder(position, target=target, selection=[unit])

    def AttackMove(self, position, target=None):
        ''' Performs attack move on position or target. Falls back to move order for units not supporthing this. '''
        nonattackmoveunits = []
        attackmoveunits = []
        for unit in self.units:
            h = unit.GetHandle()
            if 'attackmove' in unit.abilitiesbyname:
                attackmoveunits.append(h)
            else:
                nonattackmoveunits.append(h)

        for unit in nonattackmoveunits:
            unit.MoveOrder(position, target=target, selection=nonattackmoveunits)

        if attackmoveunits:
            leftpressed = MouseTraceData()
            leftpressed.endpos = position
            leftpressed.groundendpos = position
            leftpressed.ent = target
            mouse_inputs = [('leftpressed', leftpressed)]
            simulatedplayer = SimulatedPlayer(self.sai.ownernumber, selection=attackmoveunits)
            DoAbilitySimulated(simulatedplayer, 'attackmove', mouse_inputs=mouse_inputs)

    # Misc
    def FindRulesForUnits(self, units):
        try:
            for unit in units:
                rules = self.sai.GetAbilityRules(unit)
                self.sai.FindRuleAndAdd(unit, rules)
        except:
            traceback.print_exc()

    def GroupOrigin(self):
        origin = Vector(0.0, 0.0, 0.0)
        for unit in self.units:
            if unit:
                origin += unit.GetAbsOrigin()
        origin /= len(self.units)
        return origin

    def FindNearest(self, classnames, origin, filter=None):
        return self.sai.FindNearest(classnames, origin, filter)

    def FindRandomTarget(self, classname, origin, filter=None):
        targets = []
        cur = entitylist.FindEntityByClassname(None, classname)
        if not cur:
            return None
        best = None
        while cur:
            if not filter or filter(cur):
                targets.append(cur)
            cur = entitylist.FindEntityByClassname(cur, classname)

        try:
            return random.sample(targets, 1)[0]
        except ValueError:
            return None

    def FindRandomEnemyBuilding(self, ownernumber, origin=None, maxdist=None):
        targets = []
        for o, l in buildinglist.items():
            if not self.IsEnemy(ownernumber, o):
                continue
            for b in l:
                if not maxdist or (b.GetAbsOrigin() - origin).Length2D() < maxdist:
                    targets.append(b.GetHandle())
        try:
            return random.sample(targets, 1)[0]
        except ValueError:
            return None

    def IsReachablePos(self, pos):
        for unit in self.units:
            if unit and NavMeshGetPathDistance(unit.GetAbsOrigin(), pos, unit=unit) < 0:
                return False
        return True

    def HaveAbility(self, abiname):
        ''' Returns True if all units have the specified ability. '''
        for unit in self.units:
            if unit and abiname not in unit.abilities:
                return False
        return True

    def IsEnemy(self, ownernumber, ownernumber2):
        return relationships[(ownernumber, ownernumber2)] == Disposition_t.D_HT

    def GetEnemyUnitCount(self):
        count = 0
        myownernumber = self.sai.ownernumber
        for ownernumber, l in unitlist.items():
            if self.IsEnemy(myownernumber, ownernumber):
                count += len(l)
        return count

    def IsSameGroup(self, othergroup):
        return self.name == othergroup.name

    # Debug
    def GetDebugString(self):
        return 'SAIGroup: %s. Units: %d. State: %s' % (self.__class__.__name__, len(self.units), self.state)

    def DrawDebugUnit(self, unit):
        lines = self.GetDebugString().splitlines()
        for i, line in enumerate(lines):
            unit.EntityText(i, '#%d %s' % (unit.entindex(), line) if i == 0 else '\t%s' % (line), 0.1)


class GroupBuildings(GroupBase):
    ''' Managing all default buildings
        Just loops through all buildings and tries to find production rules to execute.
    '''
    matchunithints = set(['sai_building'])

    def UpdateBuilding(self, building):
        try:
            rules = self.sai.GetAbilityRules(building)
            self.sai.FindRuleAndAdd(building, rules)
        except:
            traceback.print_exc()

    def Update(self):
        if not self.Validate():
            return

        # Update production rules (check buildings and decide on what to produce)
        [self.UpdateBuilding(b) for b in self.units]


class GroupGeneric(GroupBase):
    state = 'inactive'

    # Gathering units (inactive state)
    gatherunitstimeout = 0.0
    mincountunits = 1
    maxcountunits = 1
    maxcountunitshardlimit = False
    maxadddistanceactive = 1024.0
    mincountactive = 0

    def Init(self):
        super().Init()

        self.nextgatherunitstimeout = gpGlobals.curtime + self.gatherunitstimeout if self.gatherunitstimeout else None
        self.mincountactive = random.randint(self.mincountunits, self.maxcountunits)

    def FindAndAddUnitRules(self):
        # Try to find rules for a small number of units in the group
        units = random.sample(self.units, min(3, len(self.units)))
        self.FindRulesForUnits(units)

    # Decide on whether to add this unit to this existing group
    def TryAddUnit(self, unit):
        if self.state != 'inactive' and self.maxadddistanceactive and (
            self.GroupOrigin() - unit.GetAbsOrigin()).Length2D() > self.maxadddistanceactive:
            return False

        if not self.MatchesUnit(unit) or (self.maxcountunitshardlimit and len(self.units) >= self.maxcountunits):
            return False

        self.AddUnit(unit)
        return True

    def StateInActive(self):
        self.FindAndAddUnitRules()

        if len(self.units) >= self.mincountactive or (
            self.nextgatherunitstimeout and gpGlobals.curtime > self.nextgatherunitstimeout):
            self.state = 'active'

    def GetDebugString(self):
        debugstr = '\nmincountunits: %d, gatherunitstimeout: %.1f' % (self.mincountactive, self.gatherunitstimeout)
        return super().GetDebugString() + debugstr


class GroupRandomAttackMove(GroupGeneric):
    ''' Randomly pick positions and attack move. '''
    mincountunits = 4
    maxcountunits = 8
    gatherunitstimeout = 200.0

    priority = -20
    ordertimeout = 0.0

    matchunithints = set(['sai_unit_combat'])

    category = 'attack'

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        self.FindAndAddUnitRules()

        if not unit.orders or self.ordertimeout < gpGlobals.curtime:
            curpos = self.GroupOrigin()
            pos = RandomNavAreaPosition()
            if pos != vec3_origin and self.IsReachablePos(pos):
                # ndebugoverlay.Box(pos, -Vector(32, 32, 32), Vector(32, 32, 32), 255, 0, 0, 255, 25.0)
                self.AttackMove(pos)
            self.ordertimeout = gpGlobals.curtime + 100.0


class GroupAttackEnemyBuilding(GroupRandomAttackMove):
    priority = -2
    curtarget = None

    def MatchesUnit(self, unit):
        if not super().MatchesUnit(unit):
            return False

        if not self.units:
            self.curtarget = self.FindRandomEnemyBuilding(unit.GetOwnerNumber(), unit.GetAbsOrigin())
            if not self.curtarget:
                return False

        return True

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        if not self.curtarget:
            self.DisbandGroup()
            return

        self.FindAndAddUnitRules()

        if not unit.orders or self.ordertimeout < gpGlobals.curtime:
            curpos = self.GroupOrigin()
            # target = self.FindRandomEnemyBuilding(self.sai.ownernumber, curpos)
            if self.curtarget:
                self.AttackMove(self.curtarget.GetAbsOrigin(), self.curtarget)
                self.ordertimeout = gpGlobals.curtime + 100.0
            else:
                self.DisbandGroup()


class GroupDefend(GroupGeneric):
    mincountunits = 4
    maxcountunits = 8
    gatherunitstimeout = 100.0
    maxadddistanceactive = 0

    matchunithints = set(['sai_unit_combat'])

    ordertimeout = 0.0

    priority = 10
    curtarget = None
    ispatroltarget = False
    idletimeout = 0.0
    nextdecideattacktime = 0.0

    category = 'defense'

    def MatchesUnit(self, unit):
        if not super().MatchesUnit(unit):
            return False

        if not self.units:
            # Only need one defend group
            count = self.sai.groupcounts[self.name]
            if count >= 1:
                return False

            self.curtarget = self.FindDefendTarget()
            if self.curtarget:
                # print 'def target higher prior'
                self.priority = 10
                return True

            self.curtarget = self.FindPatrolTarget()
            if self.curtarget:
                self.ispatroltarget = True
                # print self.priority
                return True

            return False

        return True

    def FindDefendTarget(self):
        # Get a random sample of buildings to consider
        mybuildings = buildinglist[self.sai.ownernumber]
        samplebuildings = random.sample(mybuildings, min(10, len(mybuildings)))
        if not samplebuildings:
            return None

        # Try to pick a building or control point being attacked/captured
        rettarget = None
        for building in samplebuildings:
            if self.TargetNeedsDefending(building):
                rettarget = building.GetHandle()
                break

        if rettarget:
            return rettarget

        # Check control points
        for cp in unitlistpertype[self.sai.ownernumber]['control_point']:
            if self.TargetNeedsDefending(cp):
                rettarget = cp.GetHandle()
                break

        return rettarget

    def TargetNeedsDefending(self, target):
        return target and (gpGlobals.curtime - target.lasttakedamage < 3.0)

    def FindPatrolTarget(self):
        mybuildings = buildinglist[self.sai.ownernumber]
        if not mybuildings:
            return None

        return random.sample(mybuildings, 1)[0].GetHandle()

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        self.FindAndAddUnitRules()

        if not self.ispatroltarget and not self.TargetNeedsDefending(self.curtarget):
            self.ispatroltarget = True

        if self.ispatroltarget:
            newtarget = self.FindDefendTarget()
            if newtarget:
                self.curtarget = newtarget
                self.ispatroltarget = False
            elif self.nextdecideattacktime < gpGlobals.curtime:
                if (self.sai.IsGroupTypeAllowed(GroupAttackEnemyBuilding) and len(self.units) >= self.maxcountunits
                    and random.random() > 0.5):
                    attackgroup = GroupAttackEnemyBuilding(self.sai)
                    if attackgroup.MatchesUnit(unit):
                        # Decide to change this group into an attacking group
                        self.ChangeToNewGroup(attackgroup)
                        attackgroup.Init()
                        return

                self.nextdecideattacktime = gpGlobals.curtime + random.uniform(10.0, 30.0)

        if self.ispatroltarget:
            if self.idletimeout > gpGlobals.curtime:
                return

        if not unit.orders or self.ordertimeout < gpGlobals.curtime:
            if self.ispatroltarget:
                self.curtarget = self.FindPatrolTarget()

            if not self.curtarget:
                self.DisbandGroup()
                return

            curpos = self.GroupOrigin()
            targetpos = UTIL_FindPositionSimple(self.curtarget.GetAbsOrigin(), 2048.0)
            self.AttackMove(targetpos)
            self.ordertimeout = gpGlobals.curtime + 130.0
            if self.ispatroltarget:
                self.idletimeout = gpGlobals.curtime + random.uniform(25.0, 30.0)


class GroupBuilder(GroupGeneric):
    mincountunits = 1
    maxcountunits = 1
    maxcountunitshardlimit = True

    priority = 0

    matchunithints = set(['sai_unit_builder'])

    category = 'economy'

    def MatchesUnit(self, unit):
        count = self.sai.groupcounts[self.name]
        if count >= 5:
            return False
        if count <= 2:
            # print('Builders high priority')
            self.priority = 20  # We should have some builders at least!
        return super().MatchesUnit(unit)

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        if unit.orders:
            return

        rules = self.sai.GetAbilityRules(unit)
        self.sai.FindRuleAndAdd(unit, rules)


class GroupScout(GroupGeneric):
    ''' Randomly pick positions and attack move.
        This group always consists of one unit.'''
    mincountunits = 1
    maxcountunits = 1
    gatherunitstimeout = 200.0
    maxcountunitshardlimit = True

    priority = -10
    ordertimeout = 0.0

    matchunithints = set(['sai_unit_scout'])

    def MatchesUnit(self, unit):
        count = self.sai.groupcounts[self.name]
        if count > 1:  # One scout is enough
            return False
        return super().MatchesUnit(unit)

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        if unit.enemy and not unit.cloaked and unit.energy > 25 and 'infiltrate' in unit.abilitiesbyname:
            simulatedplayer = SimulatedPlayer(self.sai.ownernumber, selection=[unit.GetHandle()])
            DoAbilitySimulated(simulatedplayer, 'infiltrate', mouse_inputs=[])

        self.FindAndAddUnitRules()

        if not unit.orders or self.ordertimeout < gpGlobals.curtime:
            curpos = self.GroupOrigin()
            pos = RandomNavAreaPosition()
            if pos != vec3_origin and self.IsReachablePos(pos):
                # ndebugoverlay.Box(pos, -Vector(32, 32, 32), Vector(32, 32, 32), 255, 0, 0, 255, 5.0)
                if self.HaveAbility('attackmove'):
                    self.AttackMove(pos)
                else:
                    self.MoveOrder(pos)
                self.ordertimeout = gpGlobals.curtime + 100.0