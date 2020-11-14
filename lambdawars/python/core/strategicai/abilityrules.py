import random
import math
from collections import defaultdict

from srcbase import MASK_NPCSOLID, COLLISION_GROUP_NONE
from vmath import Vector, vec3_origin
from utils import trace_t, UTIL_TraceHull
from entities import MouseTraceData
from navmesh import NavMeshGetPositionNearestNavArea
import ndebugoverlay

from gamemgr import dblist, BaseInfo, BaseInfoMetaclass
from core.buildings import priobuildinglist
from core.units import unitpopulationcount, GetMaxPopulation, sv_unitlimit, unitlistpertype
from core.dispatch import receiver
from core.signals import postlevelshutdown
from core.abilities.info import active_abilities

dbid = 'strategicai_abilityrules'
dbabilityrules = dblist[dbid]


@receiver(postlevelshutdown)
def LevelShutdown(sender, **kwargs):
    for name, info in dbabilityrules.items():
        info.OnLevelShutdown()


class AbilityRuleMetaClass(BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = BaseInfoMetaclass.__new__(cls, name, bases, dct)

        # For convenience, allow defining the hint as a single set
        if type(newcls.matchunithints) == set:
            newcls.matchunithints = [newcls.matchunithints]

        return newcls


class AbilityRuleBase(BaseInfo, metaclass=AbilityRuleMetaClass):
    id = dbid
    autogenname = True
    priority = 0

    executed = False
    expectedcosts = None

    STOPSEARCH = 'STOPSEARCH'

    #: Hints for matching an unit to this rule.
    matchunithints = []

    debugreasonfailed = ''

    @classmethod
    def OnLevelShutdown(cls):
        pass

    def __init__(self, sai, unit):
        super().__init__()

        self.sai = sai
        self.unit = unit.GetHandle()

    def MatchesUnit(self, unit):
        ''' Tests if unit can be used for this ability rule.

            Args:
                unit (entity): The unit to be tested.
        '''
        hints = unit.unitinfo.sai_hint
        for testhints in self.matchunithints:
            if testhints <= hints:
                return True
        return False

    def UpdatePriority(self):
        ''' Called on all rules of the unit before finding a rule.

            Can be used to change the order in which the rules are called.
        '''
        pass

    def PreFindRuleAction(self):
        ''' Called before FindRuleAction. '''
        self.debugreasonfailed = ''

    def FindRuleAction(self):
        ''' Find out if we can do something using this rule
            and return the cost for doing so.
        '''
        return None

    def ExecuteRuleAction(self):
        ''' Execute this rule action previous found in FindRuleAction '''
        return False

    def RemoveAbilitiesWithHints(self, hints):
        ''' Removes abilities with the specified hints

            Args:
                hints (set): set of strings representing hints.
        '''
        for abi in list(self.unit.sai_abilities):
            if hints & abi.sai_hint:
                self.unit.sai_abilities.discard(abi)

    def RemoveAbilities(self, abilities):
        self.unit.sai_abilities -= abilities

    def HasAbilityWithHint(self, hint):
        ''' Tests if ability has hint.

            Args:
                hint (str): String representing the hint.
        '''
        for abi in list(self.unit.sai_abilities):
            if hint in abi.sai_hint:
                return True
        return False

    def FilterAbilitiesWithHint(self, hint):
        ''' Filters abilities with hint.

            Args:
                hint (str): String representing the hint.
        '''

        abies = []
        for abi in list(self.unit.sai_abilities):
            if hint in abi.sai_hint:
                abies.append(abi)
        return abies

    def DebugReasonFailed(self):
        ''' Called when wars_strategicai_debug_rules is on and execution of rule failed.
            Allows for custom reasons in logging. '''
        return self.debugreasonfailed


class AbilityProdRuleRandom(AbilityRuleBase):
    ''' Matches all buildings, picks a random entry.'''
    priority = -20
    ability = None

    name = 'production'

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def MatchesUnit(self, unit):
        buildqueue = getattr(unit, 'buildqueue', None)
        return buildqueue is not None

    def FindRuleAction(self):
        unit = self.unit

        # Don't do anything if we already got stuff in the build queue
        if unit.buildqueue:
            return None

        # Pick a random ability
        if not unit.sai_abilities:
            return None
        ability = random.choice(unit.sai_abilities)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return None

        self.ability = ability

        return self

    def ExecuteRuleAction(self):
        return self.unit.DoAbility(self.ability.name, mouse_inputs=[]) is not None


class AbilityProdRuleHintBased(AbilityProdRuleRandom):
    ''' Matches all buildings, chooses based on hints and current counts.'''
    priority = -10

    name = 'production'

    def FindAbilityBasedOnHints(self, unit, hints):
        abilities = []
        for abi in unit.sai_abilities:
            if abi.sai_hint & hints:
                abilities.append(abi)

        # Pick a random ability
        if not abilities:
            return self.STOPSEARCH
        ability = random.choice(abilities)

        # Can we do this ability?
        if not ability.CanDoAbility(self.sai.player, unit):
            return self.STOPSEARCH

        # Found an ability, return us and remember ability
        self.ability = ability
        return self

    def FindRuleAction(self):
        unit = self.unit
        sai = self.sai
        ownernumber = sai.ownernumber
        hintunitcounts = sai.hintunitcounts

        # Up priority if we have a small army
        barcount = hintunitcounts['sai_building_barracks']
        combatunitcount = hintunitcounts['sai_unit_combat']
        self.priority = 10 if barcount * 2 > combatunitcount else 0

        if self.sai.difficulty <= self.sai.difficulty_easy and combatunitcount >= 8:
            return self.STOPSEARCH

        needpopulation = unitpopulationcount[ownernumber] + 5 > GetMaxPopulation(ownernumber)

        if needpopulation and self.HasAbilityWithHint('sai_upgrade_population'):
            if unit.buildqueue and 'sai_upgrade_population' not in unit.buildqueue[0].abilities[0].sai_hint:
                unit.CancelAll()
            hints = set(['sai_upgrade_population'])
            self.priority = 1
            #return self.FindAbilityBasedOnHints(unit.hints)
        else:
            # Don't do anything if we already got stuff in the build queue
            if unit.buildqueue:
                return self.STOPSEARCH

            # Build desired hint set for units
            hints = set()
            if hintunitcounts['sai_unit_builder'] == 0:
                hints.add('sai_unit_builder')
                self.priority = 20
            elif hintunitcounts['sai_building_research'] == 0 and combatunitcount > 5:
                return self.FindAbilityBasedOnHints(unit, hints)  # save money for research
            else:
                hints.add('sai_unit_combat')


                if hintunitcounts['sai_unit_builder'] > 0 and hintunitcounts['sai_unit_scout'] < 2:
                    hints.add('sai_unit_scout')

                if hintunitcounts['sai_unit_combat'] < 8:
                    hints.add('sai_unit_combat')

                if hintunitcounts['sai_unit_builder'] < 2:
                    hints.add('sai_unit_builder')
                elif hintunitcounts['sai_unit_combat'] > 7 and hintunitcounts['sai_unit_builder'] < 5:
                    hints.add('sai_unit_builder')

                if hintunitcounts['sai_building_synth'] > 0:
                    hints.add('sai_unit_super')
                elif hintunitcounts['sai_building_vortden'] > 0:
                    hints.add('sai_unit_super')

                # We usually place 5 scrap points around control points, and each scrap point can have 2 workers
                cpcount = hintunitcounts['sai_controlpoint']
                unfortifiedcount = len(unitlistpertype[ownernumber]['unit_controlpoint'])
                fortifiedcount = cpcount - unfortifiedcount
                salvagercount = hintunitcounts['sai_unit_salvager']
                if salvagercount < fortifiedcount * 4:
                    hints.add('sai_unit_salvager')

                # Add upgrade hints
                # TODO: base on what it unlocks or does
                #       for now just support grenade upgrade
                # for ability in unit.abilities:
                #    if 'sai_upgrade' in ability.sai_hints:
                #        ....
                hints.add('sai_grenade_upgrade')
                # Allow unit unlock upgrades
                hints.add('sai_unit_unlock')

        abilities = []
        for abi in unit.sai_abilities:
            if abi.sai_hint & hints:
                abilities.append(abi)

        # Pick a random ability
        if not abilities:
            return self.STOPSEARCH
        ability = random.choice(abilities)

        # Can we do this ability?
        if not ability.CanDoAbility(sai.player, unit):
            return self.STOPSEARCH

        # Found an ability, return us and remember ability
        self.ability = ability
        return self


class AbilityPlaceBuildingRuleRandom(AbilityRuleBase):
    priority = -5
    ability = None

    name = 'placebuilding'

    nexttryplace = 0.0
    testdirections = [Vector(-1, 0, 0), Vector(0, -1, 0), Vector(1, 0, 0), Vector(0, 1, 0)]

    testedspotsgrid = defaultdict(lambda: 0)
    testedspotsgridsize = 64.0

    matchunithints = set(['sai_unit_builder'])

    @classmethod
    def OnLevelShutdown(cls):
        super().OnLevelShutdown()

        cls.testedspotsgrid.clear()

    @property
    def expectedcosts(self):
        return self.ability.costs if self.ability else None

    def GetBuildingList(self):
        return priobuildinglist[self.sai.ownernumber]

    def FindPosition(self, ability):
        """ Loop through our building list and find a position.

            Returns:
                position (Vector): either a position, or vec3_origin for invalid/not found.
        """
        mins = Vector(ability.mins)
        maxs = Vector(ability.maxs)

        maxs.z -= mins.z
        mins.z = 0.0

        testradius = (maxs - mins).Length2D() / 2.0

        # Prevent from growing too much
        if len(self.testedspotsgrid) > 1000:
            self.testedspotsgrid.clear()

        # Randomize test directions
        random.shuffle(self.testdirections)

        foundpos = False
        pos = vec3_origin
        for building in self.GetBuildingList():
            if foundpos:
                break

            # Get building position
            radius = building.CollisionProp().BoundingRadius2D()
            origin = building.GetAbsOrigin()
            origin.z += building.WorldAlignMins().z

            maxtries = 3

            for i in range(0, maxtries):
                if foundpos:
                    break
                for dir in self.testdirections:
                    # Get a test position around the building on the nav mesh
                    testpos = origin + dir * (radius + testradius + random.uniform(32.0, 150.0))
                    testpos.z += 320.0

                    testpos = NavMeshGetPositionNearestNavArea(testpos, beneathlimit=1024.0)
                    if testpos == vec3_origin:
                        # ndebugoverlay.Box(testpos, -Vector(32, 32, 32), Vector(32, 32, 32), 255, 0, 255, 255, 5.0)
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
                        # ndebugoverlay.Box(testpos, -Vector(32, 32, 32), Vector(32, 32, 32), 255, 0, 0, 255, 5.0)
                        # Only don't test again for a while if it failed!
                        self.testedspotsgrid[key] = gpGlobals.curtime
                        continue

                    # Success!
                    # ndebugoverlay.Box(testpos, -Vector(32, 32, 32), Vector(32, 32, 32), 0, 255, 0, 255, 5.0)
                    pos = testpos
                    foundpos = True
                    break

        return pos

    def GetAbilities(self):
        # Get ability list. Filter them here if needed.
        abilities = set(self.unit.sai_abilities)
        self.unit.sai_abilities.clear()  # Grab all.
        return abilities

    def GetBuildingHints(self):
        # Anything common with these hints will be considered
        return set(['sai_building'])

    def FindRuleAction(self):
        if self.nexttryplace > gpGlobals.curtime:
            self.debugreasonfailed = 'waiting for next place try'
            return None

        unit = self.unit
        sai = self.sai

        hints = self.GetBuildingHints()

        abilities = []
        for abi in self.GetAbilities():
            # Should match hint and we should be able to do it.
            # For example, some abilities may not be available yet due tech restrictions.
            if abi.sai_hint & hints and abi.CanDoAbility(self.sai.player, unit):
                abilities.append(abi)

        if not abilities:
            self.debugreasonfailed = 'all abilities are filtered'
            return None

        # Pick a random ability
        ability = random.choice(abilities)

        # Can we find a valid position?
        abiinst = self.unit.DoAbility(ability.name, mouse_inputs=[])
        self.position = self.FindPosition(abiinst)
        abiinst.Cancel()
        if self.position == vec3_origin:
            # print('%s: Invalid position found for hints %s ability %s, debugvalidposition: %s' % (self.name, str(hints), str(ability), getattr(abiinst, 'debugvalidposition', 'none')))
            # self.debugreasonfailed = 'invalid position found for hints %s ability %s, debugvalidposition: %s' % (str(hints), str(ability), getattr(abiinst, 'debugvalidposition', 'none'))
            self.debugreasonfailed = 'invalid position'
            return None

        # Found an ability, return us and remember ability
        self.ability = ability
        return self

    def CheckNeedPopulation(self):
        owner = self.sai.ownernumber
        curmaxpop = GetMaxPopulation(owner) + self.sai.pendingpopulationcount
        # Add in active abilities of billets still need to be placed
        myactivabilities = filter(lambda abi: abi.ownernumber == owner, active_abilities)
        for abi in myactivabilities:
            curmaxpop += getattr(abi, 'providespopulation', 0)

        globalmaxpop = sv_unitlimit.GetInt()
        return curmaxpop < globalmaxpop and unitpopulationcount[owner] + 5 > curmaxpop

    def ExecuteRuleAction(self):
        self.nexttryplace = gpGlobals.curtime + random.uniform(10.0, 20.0)

        if 'sai_building_population' in self.ability.sai_hint:
            if not self.CheckNeedPopulation():
                # Do nothing, but do keep executing rules if there are more
                return True

        # Execute action
        leftpressed = MouseTraceData()
        leftpressed.endpos = self.position
        leftpressed.groundendpos = self.position
        # leftpressed1 = leftpressed
        # leftpressed2 = leftpressed

        mouse_inputs = [
            ('leftpressed', leftpressed),
            # ('leftreleased', leftpressed),
        ]
        return self.unit.DoAbility(self.ability.name, mouse_inputs=mouse_inputs) is not None


class AbilityPlaceBuildingRuleHintBased(AbilityPlaceBuildingRuleRandom):
    priority = 0

    name = 'placebuilding'

    def GetBuildingHints(self):
        hintunitcounts = self.sai.hintunitcounts

        # Filter based on building hint counts
        # The following hints are in use:
        # sai_building_hq: Produces builders + a few other things. Usually only one required
        # sai_building_barracks: anything that produces units for combat. Pretty much the default building.
        # sai_building_research: Provides upgrades, usually one is enough
        # sai_building_population: increases the population of the player
        # sai_building_aid: Heals nearby units, a few should be enough
        hints = set([])
        if not hintunitcounts['sai_building_hq']:
            hints.add('sai_building_hq')

        if self.CheckNeedPopulation():
            hints.add('sai_building_population')
        else:
            barcount = hintunitcounts['sai_building_barracks']
            combatunitcount = hintunitcounts['sai_unit_combat']
            reqincomerate = self.sai.incomerates['requisition']
            researchCount  = hintunitcounts['sai_building_research']
            junkyardCount = hintunitcounts['sai_building_junkyard']
            shouldBuildBarracks = (combatunitcount > barcount*1.5 and math.pow(max(0, (reqincomerate/60.0)-0.2), 1.4) > barcount)
            if barcount < 1: # or (combatunitcount > barcount * 1.5 and math.pow(max(0, (reqincomerate / 60.0) - 0.2), 1.4) > barcount):
                hints.add('sai_building_barracks')
            elif researchCount > 0 and shouldBuildBarracks:
                hints.add('sai_building_barracks')

            if junkyardCount < 1:
                hints.add('sai_building_junkyard')
            elif junkyardCount >= 1 and barcount < 1:
                hints.add('sai_building_barracks')

            if barcount > 0:
                if hintunitcounts['sai_building_research'] < 1:
                    hints.add('sai_building_research')
                elif hintunitcounts['sai_building_research'] > 0:
                    if barcount < 2:
                        hints.add('sai_building_barracks')
                elif hintunitcounts['sai_building_aid'] < 1:
                    hints.add('sai_building_aid')
                else:
                    hints.add('sai_building_specops')

            if hintunitcounts['sai_building_research'] > 0 and hintunitcounts['sai_tp_defense'] < 2:
                hints.add('sai_tp_defense')

            if hintunitcounts['sai_building_mech_factory'] < 1:
                hints.add('sai_building_mech_factory')

            if hintunitcounts['sai_building_research'] > 0 and hintunitcounts['sai_building_specops'] < 1:
                hints.add('sai_building_specops')

            if hintunitcounts['sai_building_aid'] < 1:
                hints.add('sai_building_aid')

            if hintunitcounts['sai_building_synth'] < 2:
                hints.add('sai_building_synth')

            if hintunitcounts['sai_building_research'] > 0 and hintunitcounts['sai_building_aid'] > 0:
                if hintunitcounts['sai_building_specops'] < 1:
                    hints.add('sai_building_specops')
                elif hintunitcounts['sai_building_vortden'] < 1:
                    hints.add('sai_building_vortden')

            if hintunitcounts['sai_building_specops'] < 2:
                hints.add('sai_building_specops')
            elif hintunitcounts['sai_building_vortden'] < 2:
                hints.add('sai_building_vortden')

            # keep Rebels longer in the game (rebel CPU gives up early)
            if hintunitcounts['sai_building_barracks'] > 2 and hintunitcounts['sai_building_specops'] > 1 and hintunitcounts['sai_building_vortden'] > 1:
                if hintunitcounts['sai_building_specops'] < 3:
                    hints.add('sai_building_specops')
                elif hintunitcounts['sai_building_vortden'] < 4:
                    hints.add('sai_building_vortden')
                '''if hintunitcounts['sai_building_barracks'] < 3:
                    hints.add('sai_building_barracks')'''

            # keep Combine longer in the game
            if hintunitcounts['sai_building_barracks'] > 2 and hintunitcounts['sai_building_specops'] > 1 and hintunitcounts['sai_building_synth'] > 1:
                """if hintunitcounts['sai_building_barracks'] < 4:
                    hints.add('sai_building_barracks')
                if hintunitcounts['sai_building_specops'] < 4:
                    hints.add('sai_building_specops')"""
                if hintunitcounts['sai_building_synth'] < 4:
                    hints.add('sai_building_synth')

            # As a general rule, keep the number of energy cells about the same as the number of power generators
            # TODO: This shouldn't be here, but in wars_game
            cellCount = hintunitcounts['sai_building_energycell']
            scrapGensCount = hintunitcounts['sai_building_powergenscrap']
            allEnergyGensCount = (hintunitcounts['sai_building_powergen'] + scrapGensCount)
            if barcount > 0 and cellCount == 0 and allEnergyGensCount > 0:
                hints.add('sai_building_energycell')
            elif scrapGensCount > 0 and cellCount < 5:
                hints.add('sai_building_energycell')
            elif scrapGensCount > 2 and cellCount < 7:
                hints.add('sai_building_energycell')

        return hints