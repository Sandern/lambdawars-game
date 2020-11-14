import random
import traceback
import math

from vmath import Vector, vec3_origin
from entities import Disposition_t, MouseTraceData
from playermgr import relationships, OWNER_NEUTRAL, SimulatedPlayer

from core.units import unitlistpertype, unitlist, UnitBaseShared
from core.abilities import DoAbilitySimulated
from core.strategicai import GroupBase, GroupRandomAttackMove, GroupGeneric, AbilityRuleBase, \
    AbilityPlaceBuildingRuleRandom, AbilityPlaceBuildingRuleHintBased
from wars_game.buildings.combine import poweredlist
from wars_game.ents.controlpoint import controlpointlist
from navmesh import NavMeshGetPositionNearestNavArea


class GroupCaptureControlPoint(GroupRandomAttackMove):
    ''' Group for capturing control points.

        Gathers a group of units and picks a target nearby our buildings.
    '''
    priority = 10

    category = 'cpcapturing'

    curtarget = None

    def Init(self):
        unit = random.sample(self.units, 1)[0]

        # Lower group counts when there are hardly units on the map
        # Bigger counts are needed in the later stages
        enemycount = self.GetEnemyUnitCount()
        if self.curtarget and relationships[
            (unit.GetOwnerNumber(), self.curtarget.GetOwnerNumber())] == Disposition_t.D_NU:
            self.mincountunits = 1
            self.maxcountunits = 1
            self.maxcountunitshardlimit = True
        else:
            self.maxcountunits = enemycount
            self.mincountunits = min(self.mincountunits, enemycount)

        super().Init()

    def IsTargetAssignedToGroup(self, target):
        for group in self.sai.groups:
            if not group.IsSameGroup(self):
                continue
            if group.curtarget == target:
                return True
        return False

    def ShouldCaptureControlPoints(self, sai):
        ''' Determines if this cpu player should capture control points.
            On below normal difficulty we clamp the number of points being captured.
        '''
        if sai.difficulty <= sai.difficulty_easy:
            owner = self.sai.ownernumber
            maxothercp = 0
            totalcp = 0
            for otherowner, l in controlpointlist.items():
                cpcount = len(l)
                totalcp += cpcount
                if otherowner == OWNER_NEUTRAL or otherowner == owner:
                    continue
                maxothercp = max(maxothercp, cpcount)

            owncount = len(controlpointlist[self.sai.ownernumber])
            if owncount >= maxothercp or owncount >= (totalcp / 2):
                return False
        return True

    def MatchesUnit(self, unit):
        fntestvalid = lambda cur: relationships[(
        unit.GetOwnerNumber(), cur.GetOwnerNumber())] == Disposition_t.D_NU and not self.IsTargetAssignedToGroup(cur)

        # Special case for scouts: only use them if there are still neutral control points
        origin = unit.GetAbsOrigin()
        if 'sai_unit_scout' in unit.unitinfo.sai_hint and not 'sai_unit_combat' in unit.unitinfo.sai_hint:
            if not self.FindNearest('control_point', origin, filter=fntestvalid):
                return False
            # Special case for Combine Citizen: don't go salvage, but capture
            self.priority = 14
        elif not super().MatchesUnit(unit):
            return False

        if not self.ShouldCaptureControlPoints(self.sai):
            return False

        if not self.units:
            # Can't have too many of these groups (shouldn't be needed, rather attack enemy)
            count = self.sai.groupcounts[self.name]
            if count > 2:
                return False

            # There must be a target
            origin = unit.GetAbsOrigin()

            fntestvalid2 = lambda cur: relationships[(
            unit.GetOwnerNumber(), cur.GetOwnerNumber())] == Disposition_t.D_HT and not self.IsTargetAssignedToGroup(
                cur)
            self.curtarget = self.FindNearest('control_point', origin, filter=fntestvalid) or self.FindNearest(
                'control_point', origin, filter=fntestvalid2)
            if not self.curtarget:
                return False

        return True

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        if not self.ShouldCaptureControlPoints(self.sai):
            self.DisbandGroup()
            return

        self.FindAndAddUnitRules()

        # Check if cur target is captured, in that case disband
        # Make sure we have a target
        if self.curtarget:
            if relationships[(self.sai.ownernumber, self.curtarget.GetOwnerNumber())] == Disposition_t.D_LI:
                self.DisbandGroup()
                return
        else:
            fntestvalid = lambda cur: relationships[(self.sai.ownernumber, cur.GetOwnerNumber())] != Disposition_t.D_LI
            self.curtarget = self.FindNearest('control_point', unit.GetAbsOrigin(), filter=fntestvalid)
            # If we can't find anything, disband
            if not self.curtarget:
                self.DisbandGroup()
                return

        targetpos = self.curtarget.GetAbsOrigin()
        grouporigin = self.GroupOrigin()

        # Don't need to do anything if our group is around the point and capturing
        if self.curtarget.playercapturing == unit.GetOwnerNumber() and (grouporigin - targetpos).Length2D() < 256.0:
            return

        # Update orders if needed
        disp = relationships[(self.sai.ownernumber, self.curtarget.GetOwnerNumber())]
        try:
            if not unit.curorder or (
                unit.curorder.position and (unit.curorder.position - targetpos).Length2D() > 256.0):
                if disp != Disposition_t.D_LI:
                    self.AttackMove(targetpos, target=self.curtarget)
                else:
                    self.MoveOrder(targetpos, target=self.curtarget)
        except:
            PrintWarning('GroupCaptureControlPoint group contains an invalid unit: %s\n' % (unit))
            traceback.print_exc()


class GroupControlPoints(GroupBase):
    ''' Upgrades owned control points when appropriate.
        All owned control points are always put in one group.
    '''
    matchunithints = set(['sai_controlpoint'])

    def Update(self):
        if not self.Validate():
            return

        # Update production rules (check buildings and decide on what to produce)
        self.FindRulesForUnits(random.sample(self.units, min(3, len(self.units))))


class AbilityFortifyRule(AbilityRuleBase):
    priority = 0

    #: Hints for matching an unit to this rule.
    matchunithints = set(['sai_controlpoint'])

    ability = None

    name = 'fortifyupgrade'

    # def MatchesUnit(self, unit):
    #    return super().MatchesUnit(unit)

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def UpdatePriority(self):
        # Increase priority if we have no fortified control points yet
        # Lower if we have little combat units in relation to the number of cp points
        # Lower if we fortified something in the last minute
        lastfortifytime = getattr(self.sai, 'lastfortifytime', 0)
        cpcount = self.sai.hintunitcounts['sai_controlpoint']
        unfortifiedcount = len(unitlistpertype[self.sai.ownernumber]['control_point'])
        fortifiedcount = cpcount - unfortifiedcount
        if unfortifiedcount == cpcount:
            self.priority = 6
        elif lastfortifytime and gpGlobals.curtime - lastfortifytime < (180.0 + (fortifiedcount * 40.0)):
            self.priority = -12
        else:
            self.priority = 0

    def FindRuleAction(self):
        # Only add one of this type per think step
        if self.name in self.sai.executerulestypes:
            return None

        unit = self.unit

        cpcount = self.sai.hintunitcounts['sai_controlpoint']
        unfortifiedcount = len(unitlistpertype[self.sai.ownernumber]['control_point'])
        fortifiedcount = cpcount - unfortifiedcount
        combatunitcount = self.sai.hintunitcounts['sai_unit_combat']

        # Skip rule if having little combat units in relation to control points
        if combatunitcount < fortifiedcount * 3:
            return None

        # Don't do upgrades when an enemy player is capturing
        if unit.playercapturing is not None:
            return None

        # Don't do upgrades if enemy players are attacking the control point
        if gpGlobals.curtime - unit.lasttakedamage < 10.0:
            return None

        # Pick a random ability
        fortifyabies = self.FilterAbilitiesWithHint('sai_fortifyupgrade')
        if not fortifyabies:
            return None
        ability = random.choice(fortifyabies)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return None

        self.ability = ability

        return self

    def ExecuteRuleAction(self):
        abi = self.unit.DoAbility(self.ability.name, mouse_inputs=[])
        if abi:
            self.sai.lastfortifytime = gpGlobals.curtime
        return abi is not None


class AbilityThrowGrenade(AbilityRuleBase):
    priority = 0

    ability = None
    target = None

    name = 'throwgrenade'

    def MatchesUnit(self, unit):
        ''' Tests if unit can be used for this ability rule. '''
        for ability in unit.abilities.values():
            if 'sai_grenade' in ability.sai_hint:
                return True
        return False

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def FindRuleAction(self):
        if self.sai.ruletypelastexecuted[self.name] + 1.5 > gpGlobals.curtime and self.sai.difficulty <= self.sai.difficulty_easy:
            return None
        elif self.sai.ruletypelastexecuted[self.name] + 0.5 > gpGlobals.curtime and self.sai.difficulty >= self.sai.difficulty_hard:
            return None

        unit = self.unit

        enemy = unit.enemy
        if not enemy:
            return None

        # Buildings: just throw
        # Units: throw if surrounded by at least 2 other units (not enemies)
        isbuilding = getattr(enemy, 'isbuilding', False)
        if not isbuilding:
            senses = getattr(enemy, 'senses', None)
            if not senses:
                return None
            if senses.CountOthersInRange(128.0) < 2:
                return None

        # Pick the available fortify ability
        grenadeabies = self.FilterAbilitiesWithHint('sai_grenade')
        if not grenadeabies:
            return None
        ability = random.choice(grenadeabies)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return None

        self.target = unit.enemy
        self.ability = ability

        return self

    def ExecuteRuleAction(self):
        position = self.target.GetAbsOrigin()

        # Execute action
        leftpressed = MouseTraceData()
        leftpressed.endpos = position
        leftpressed.groundendpos = position
        leftpressed.ent = self.target

        mouse_inputs = [
            ('leftpressed', leftpressed),
            # ('leftreleased', leftpressed),
        ]
        return self.unit.DoAbility(self.ability.name, mouse_inputs=mouse_inputs) is not None


class AbilityCombineBall(AbilityRuleBase):
    priority = 0

    ability = None
    target = None

    name = 'ai_combineball'

    def MatchesUnit(self, unit):
        ''' Tests if unit can be used for this ability rule. '''
        for ability in unit.abilities.values():
            if 'sai_combine_ball' in ability.sai_hint:
                return True
        return False

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def FindRuleAction(self):
        if self.sai.ruletypelastexecuted[self.name] + 1.5 > gpGlobals.curtime and self.sai.difficulty <= self.sai.difficulty_easy:
            return None
        elif self.sai.ruletypelastexecuted[self.name] + 0.5 > gpGlobals.curtime and self.sai.difficulty >= self.sai.difficulty_hard:
            return None

        unit = self.unit

        enemy = unit.enemy
        if not enemy:
            return None

        # Units: throw if surrounded by at least 2 other units (not enemies) [old, changed it to 1 single unit for combine ball]
        senses = getattr(enemy, 'senses', None)
        if not senses:
            return None
        if senses.CountOthersInRange(128.0) == 0:
            return None

        # Pick the available fortify ability
        grenadeabies = self.FilterAbilitiesWithHint('sai_combine_ball')
        if not grenadeabies:
            return None
        ability = random.choice(grenadeabies)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return None

        self.target = unit.enemy
        self.ability = ability

        return self

    def ExecuteRuleAction(self):
        position = self.target.GetAbsOrigin()

        # Execute action
        leftpressed = MouseTraceData()
        leftpressed.endpos = position
        leftpressed.groundendpos = position
        leftpressed.ent = self.target

        mouse_inputs = [
            ('leftpressed', leftpressed),
            # ('leftreleased', leftpressed),
        ]
        return self.unit.DoAbility(self.ability.name, mouse_inputs=mouse_inputs) is not None


class AbilityDeployUnits(AbilityRuleBase):
    priority = 0

    ability = None
    target = None

    name = 'deployminions'

    def MatchesUnit(self, unit):
        ''' Tests if unit can be used for this ability rule. '''
        for ability in unit.abilities.values():
            if 'sai_deploy' in ability.sai_hint:
                return True
        return False

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def FindRuleAction(self):
        if self.sai.ruletypelastexecuted[self.name] + 0.0 > gpGlobals.curtime:
            return None

        unit = self.unit

        enemy = unit.enemy
        if not enemy:
            return None

        # Buildings: just throw
        # Units: throw if surrounded by at least 2 other units (not enemies)
        isbuilding = getattr(enemy, 'isbuilding', False)
        if not isbuilding:
            senses = getattr(enemy, 'senses', None)
            if not senses:
                return None

        # Pick the available fortify ability
        deployables = self.FilterAbilitiesWithHint('sai_deploy')
        if not deployables:
            return None
        ability = random.choice(deployables)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return None

        self.target = unit.enemy
        self.ability = ability

        return self

    def ExecuteRuleAction(self):
        return self.unit.DoAbility(self.ability.name) is not None


class AbilityGrenadeUnlock(AbilityRuleBase):
    priority = 0

    ability = None
    target = None

    name = 'grenadeunitunlock'

    def MatchesUnit(self, unit):
        ''' Tests if unit can be used for this ability rule. '''
        for ability in unit.abilities.values():
            if 'sai_grenade_unit_unlock' in ability.sai_hint:
                return True
        return False

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def FindRuleAction(self):
        if self.sai.ruletypelastexecuted[self.name] + 0.0 > gpGlobals.curtime:
            return None

        unit = self.unit

        enemy = unit.enemy
        if not enemy:
            return None

        # Buildings: just throw
        # Units: throw if surrounded by at least 2 other units (not enemies)
        isbuilding = getattr(enemy, 'isbuilding', False)
        if not isbuilding:
            senses = getattr(enemy, 'senses', None)
            if not senses:
                return None

        # Pick the available fortify ability
        deployables = self.FilterAbilitiesWithHint('sai_grenade_unit_unlock')
        if not deployables:
            return None
        ability = random.choice(deployables)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return None

        self.ability = ability

        return self

    def ExecuteRuleAction(self):
        return self.unit.DoAbility(self.ability.name) is not None


class AbilityPlaceBuildingRuleHintBasedCombine(AbilityPlaceBuildingRuleHintBased):
    ''' Combine base place building rules.

        Modifies default to remove all buildings required to be placed near a power gen.
    '''
    priority = 7

    def GetBuildingList(self):
        return unitlistpertype[self.sai.ownernumber]['build_comb_powergenerator']

    def GetAbilities(self):
        ''' Get ability list. Filter them here if needed.

            Basically this removes all buildings requiring power, so they
            don't end up in AbilityPlaceBuildingRuleHintBased.
        '''
        abilities = set()
        for abi in self.unit.sai_abilities:
            if 'sai_building_powered' in abi.sai_hint:
                abilities.add(abi)
        self.RemoveAbilities(abilities)
        return abilities


class AbilityPlaceBuildingRuleHintBasedCombinePowerGen(AbilityPlaceBuildingRuleRandom):
    priority = 5

    def GetBuildingList(self):
        ''' Filter power generators. Silly to place more power generators next to power generators '''
        buildinglist = super().GetBuildingList()
        buildinglist = [b for b in buildinglist if b.GetUnitType() != 'build_comb_powergenerator']
        return buildinglist

    def GetAbilities(self):
        ''' Get ability list. Filter them here if needed.'''
        abilities = set()
        for abi in self.unit.sai_abilities:
            if 'sai_building_powergen' in abi.sai_hint:
                abilities.add(abi)
        self.RemoveAbilities(abilities)
        return abilities

    def UpdatePriority(self):
        # The number of power gens should be about equal to half the number of other buildings and we should have at
        # least one power generator
        # Do always keep this action, in case the Combine cpu player gets stuck. Just lower the priority
        hintunitcounts = self.sai.hintunitcounts
        nonpowergens = hintunitcounts['sai_building'] - hintunitcounts['sai_building_powergen']
        if hintunitcounts['sai_building_powergen'] < 1 or math.ceil(nonpowergens / 2.0) > hintunitcounts[
            'sai_building_powergen']:
            self.priority = 5
        else:
            self.priority = -13

    def GetBuildingHints(self):
        return set(['sai_building_powergen'])


class AbilityPlaceBuildingRuleHintBasedCombinePowerGenScrap(AbilityPlaceBuildingRuleRandom):
    ''' Places Scrap Power Generators. '''
    name = 'placescrappowergen'
    priority = 7
    testdirections = [Vector(0, 0, 0)]

    def GetBuildingHints(self):
        # Anything common with these hints will be considered
        return set(['sai_building_powergenscrap'])

    def FindPosition(self, ability):
        fntestvalid = lambda cur: cur.IsSolid()  # Non Solid ones are already taken
        scrapmarker = self.sai.FindNearest(['scrap_marker', 'scrap_marker_small'], self.unit.GetAbsOrigin(),
                                           filter=fntestvalid)
        if scrapmarker:
            return scrapmarker.GetAbsOrigin()
        return vec3_origin

    def GetAbilities(self):
        ''' Get ability list. Filter them here if needed.'''
        abilities = set()
        for abi in self.unit.sai_abilities:
            if 'sai_building_powergenscrap' in abi.sai_hint:
                abilities.add(abi)
        self.RemoveAbilities(abilities)
        return abilities

    def UpdatePriority(self):
        # Up priority depending on number of fortified control points
        lastplacesrappowergentime = getattr(self.sai, 'lastplacesrappowergentime', 0)
        cpcount = self.sai.hintunitcounts['sai_controlpoint']
        unfortifiedcount = len(unitlistpertype[self.sai.ownernumber]['control_point'])
        fortifiedcount = cpcount - unfortifiedcount
        combatunitcount = self.sai.hintunitcounts['sai_unit_combat']
        scrappowercount = self.sai.hintunitcounts['sai_building_powergenscrap']

        if scrappowercount < fortifiedcount and combatunitcount > scrappowercount * 2 and gpGlobals.curtime > lastplacesrappowergentime + 60.0:
            self.priority = 9
        else:
            self.priority = -12

    def ExecuteRuleAction(self):
        abi = super().ExecuteRuleAction()
        if abi:
            self.sai.lastplacesrappowergentime = gpGlobals.curtime
        return abi is not None


class AbilityPlaceBuildingRuleHintBasedRebelJunkyard(AbilityPlaceBuildingRuleRandom):
    ''' Places junkyards. '''
    name = 'placejunkyard'
    priority = 17

    # testdirections = [Vector(1, 0, 0),Vector(1, 1, 0),Vector(1, 0, 0)]

    def GetBuildingHints(self):
        # Anything common with these hints will be considered
        return set(['sai_building_junkyard'])

    def FindPosition(self, ability):
        scrapmarker = self.sai.FindNearest(['scrap_marker', 'scrap_marker_small'], self.unit.GetAbsOrigin())
        if not scrapmarker:
            return vec3_origin  # there is no scrap on the map!

        # Prevent from growing too much
        if len(self.testedspotsgrid) > 1000:
            self.testedspotsgrid.clear()

        # Randomize test directions
        random.shuffle(self.testdirections)

        mins = Vector(ability.mins)
        maxs = Vector(ability.maxs)

        maxs.z -= mins.z
        mins.z = 0.0

        buildingradius = (maxs - mins).Length2D() / 2.0
        scrapradius = scrapmarker.CollisionProp().BoundingRadius2D()

        maxtries = 3
        for i in range(0, maxtries):
            for dir in self.testdirections:
                testpos = scrapmarker.GetAbsOrigin() + dir * (
                buildingradius + scrapradius + random.uniform(32.0, 150.0)) * (i + 1)  # a potential building position
                testpos.z += 320.0
                testpos = NavMeshGetPositionNearestNavArea(testpos, beneathlimit=1024.0)  # project to nav mesh

                #ndebugoverlay.Box(testpos, -Vector(32, 32, 32), Vector(32, 32, 32), 0, 255, 0, 255, 30.0)

                if testpos == vec3_origin:
                    continue

                # Don't test at same spot again. This is done to prevent multiple builders from trying the same spot
                # Note: testedspotsgrid is shared with other units
                key = (round(testpos.x / self.testedspotsgridsize), round(testpos.y / self.testedspotsgridsize))
                if self.testedspotsgrid[key] and gpGlobals.curtime - self.testedspotsgrid[key] < 25.0:
                    continue

                # Test position. Bloat it so CPU Player does not build buildings too cloes to each other
                if ability.placeatmins:
                    testpos.z += -ability.mins.z

                ability.mins = ability.mins - Vector(32.0, 32.0, 0)
                ability.maxs = ability.maxs + Vector(32.0, 32.0, 0)
                if not ability.IsValidPosition(testpos):
                    # Only don't test again for a while if it failed!
                    self.testedspotsgrid[key] = gpGlobals.curtime
                    continue
                # Success!
                return testpos

        return vec3_origin
        # fntestvalid = lambda cur: cur.IsSolid() # Non Solid ones are already taken

        # if scrapmarker:
        # return scrapmarker.GetAbsOrigin()
        # return vec3_origin

    def GetAbilities(self):
        ''' Get ability list. Filter them here if needed.'''
        abilities = set()
        for abi in self.unit.sai_abilities:
            if 'sai_building_junkyard' in abi.sai_hint:
                abilities.add(abi)
        self.RemoveAbilities(abilities)
        return abilities

    def UpdatePriority(self):
        # Up priority depending on number of fortified control points
        junkyardcount = self.sai.hintunitcounts['sai_building_junkyard']
        if junkyardcount <= 0:
            self.priority = 17
        else:
            self.priority = -30 * junkyardcount

    def ExecuteRuleAction(self):
        abi = super().ExecuteRuleAction()
        return abi is not None


class GroupScrapSalvagers(GroupGeneric):
    mincountunits = 1
    maxcountunits = 1
    maxcountunitshardlimit = True

    priority = 0

    matchunithints = set(['sai_unit_salvager'])

    category = 'economy'

    targetscrapmarker = None

    def MatchesUnit(self, unit):
        if 'salvage' not in unit.abilitiesbyname:
            return False
        count = self.sai.groupcounts[self.name]
        junkyardcount = self.sai.hintunitcounts['sai_building_junkyard']
        if junkyardcount > 0:
            if count > 10 * junkyardcount:
                return False
            if count <= 4 * junkyardcount:
                self.priority = 12  # We should have some salvagers
            elif count <= 7 * junkyardcount:
                self.priority = 6
            ret = super().MatchesUnit(unit)
            if not ret:
                return False
        else:
            self.priority = 0
            return False

        self.targetscrapmarker = self.FindTargetScrapMarker(unit.GetAbsOrigin())
        return self.targetscrapmarker is not None

    def FindTargetScrapMarker(self, origin):
        return self.FindNearest(['scrap_marker', 'scrap_marker_small'], origin)

    def StateActive(self):
        unit = random.sample(self.units, 1)[0]

        if unit.orders:
            return

        if not self.targetscrapmarker:
            self.DisbandGroup()
            return

        position = self.targetscrapmarker.GetAbsOrigin()

        leftpressed = MouseTraceData()
        leftpressed.endpos = position
        leftpressed.groundendpos = position
        leftpressed.ent = self.targetscrapmarker
        mouse_inputs = [('leftpressed', leftpressed)]
        simulatedplayer = SimulatedPlayer(self.sai.ownernumber, selection=self.units)
        DoAbilitySimulated(simulatedplayer, 'salvage', mouse_inputs=mouse_inputs)