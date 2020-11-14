import os
from collections import defaultdict
import json
from datetime import datetime
import zipfile
import operator
import copy

from srcbuiltins import RegisterTickMethod, UnregisterTickMethod
from core.signals import (resourcecollected, resourcespent, buildingstarted, buildingfinished, productionstarted,
                          endgame, unitspawned, unitkilled)
from core.resources import resources
from core.units import unitpopulationcount, GetMaxPopulation
from steam import EAccountType
from gamerules import gamerules
import srcmgr
import filesystem


class StatisticsCollector(object):
    """ Records the statistics during a match.
        Hooks up to many events to do so.

        Provides ways of writing the statistics to a file or send it to the match server.

        The gamerules creates a new StatisticsCollector and calls StartRecord to begin recording events.
        When the match is done, it calls EndRecord followed by WriteToFile if it should be saved to disk.
    """
    enabled = False

    recording = False
    record_start_time = 0.0

    _written_to_path = None

    matches_folder = 'matches'

    def __init__(self):
        super().__init__()

        # Owners recorded for statistics
        self._valid_owners = set()
        # Generic match info
        self.match_info = {}
        # Periodically recorded events. Basically anything that does not generate events to which we can listen or
        # which generates too many events.
        self._events = []
        # Chronicle list of build events, like start of constructing a building or start of producing a unit
        self._build_events = defaultdict(list)
        # Tracks number of units and buildings killed/lost per owner
        self._units_killed = defaultdict(int)
        self._buildings_killed = defaultdict(int)
        self._units_lost = defaultdict(int)
        self._buildings_lost = defaultdict(int)
        # Tracks number of units and buildings produced per owner
        self._units_produced = defaultdict(int)
        self._buildings_constructed = defaultdict(int)
        # Total resources collected per owner: [owner][type]
        self._collected_resources = defaultdict(lambda: defaultdict(lambda: 0))
        # Total resources spent per owner: [owner][type]
        self._spent_resources = defaultdict(lambda: defaultdict(lambda: 0))
        # Total resources spent per category: [owner][type][category]
        self._spent_resources_per_category = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))

    def Clear(self):
        """ Clears recorded data. """
        self._valid_owners.clear()
        self.match_info.clear()
        self._events = []
        self._build_events.clear()
        self._units_killed.clear()
        self._buildings_killed.clear()
        self._units_lost.clear()
        self._buildings_lost.clear()
        self._units_produced.clear()
        self._buildings_constructed.clear()
        self._collected_resources.clear()
        self._spent_resources.clear()
        self._spent_resources_per_category.clear()

    def StartRecord(self):
        """ Starts recording the match statistics.

            Connects to all game events needed for statistics at this point.

            Noop when recording already started.
        """
        if self.recording:
            return

        self.recording = True

        # Save start, might have started this gamerules in the middle of a map
        self.record_start_time = gpGlobals.curtime

        # Reset any previous stats
        self.Clear()

        # Register signals
        endgame.connect(self.OnEndGame)
        resourcecollected.connect(self.OnResourcesCollected)
        resourcespent.connect(self.OnResourcesSpent)
        buildingstarted.connect(self.OnBuildingStarted)
        buildingfinished.connect(self.OnBuildingFinished)
        productionstarted.connect(self.OnProductionStarted)
        unitspawned.connect(self.OnUnitSpawned)
        unitkilled.connect(self.OnUnitKilled)

        for data in gamerules.gameplayers:
            self._valid_owners.add(data['ownernumber'])

        # Register UpdateStats to sample the current stats once per x seconds
        RegisterTickMethod(self.UpdateStats, 10.0)

        # Build dictionary with the info, events and statistics of this match
        # This will later be written away
        match_info = self.match_info
        match_info['ended'] = False
        match_info['map'] = srcmgr.levelname
        match_info['mode'] = gamerules.info.name
        match_info['type'] = gamerules.game_type
        match_info['events'] = self._events
        match_info['build_events'] = self._build_events
        match_info['collected_resources'] = self._collected_resources
        match_info['spent_resources'] = self._spent_resources
        match_info['spent_resources_per_category'] = self._spent_resources_per_category

        match_info['units_killed'] = self._units_killed
        match_info['buildings_killed'] = self._buildings_killed
        match_info['units_lost'] = self._units_lost
        match_info['buildings_lost'] = self._buildings_lost
        match_info['buildings_constructed'] = self._buildings_constructed
        match_info['units_produced'] = self._units_produced

        # Record start date/time
        utc_datetime = datetime.utcnow()
        match_info['start_date'] = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

        match_info['game_version'] = srcmgr.DEVVERSION if srcmgr.DEVVERSION else ','.join(map(str, srcmgr.VERSION))

        # Match format version
        match_info['version'] = '1.0.0'

        match_info['players'] = {}
        for data in gamerules.gameplayers:
            owner = data['ownernumber']
            color = data['color']
            match_info['players'][owner] = {
                'name': data['playername'].encode("ascii", "replace").decode('ascii'),
                'color': '#%02x%02x%02x' % (color[0], color[1], color[2]),
                'team': data['team'],
            }
            if data['steamid']:
                match_info['players'][owner]['steamid'] = self.RenderSteamID(data['steamid'])

        # Record start resources
        for owner in self._valid_owners:
            for res_type, amount in resources[owner].items():
                self._collected_resources[owner][res_type] = amount

        # Record initial stats
        self.UpdateStats()

    def EndRecord(self):
        """ Stops recording the match.

            Disconnects all game events from this object.
            Records the end time of the match.

            Noop when not recording.
        """
        if not self.recording:
            return

        self.recording = False

        # Disconnect signals
        endgame.disconnect(self.OnEndGame)
        resourcecollected.disconnect(self.OnResourcesCollected)
        resourcespent.disconnect(self.OnResourcesSpent)
        buildingstarted.disconnect(self.OnBuildingStarted)
        buildingfinished.disconnect(self.OnBuildingFinished)
        productionstarted.disconnect(self.OnProductionStarted)
        unitspawned.disconnect(self.OnUnitSpawned)
        unitkilled.disconnect(self.OnUnitKilled)

        # Stop updating
        UnregisterTickMethod(self.UpdateStats)

        # Record the end date/time
        match_info = self.match_info
        utc_datetime = datetime.utcnow()
        match_info['end_date'] = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Do a final record
        self.UpdateStats()

    def WriteToFile(self):
        """ Writes the recorded statistics to a match file. """
        if self._written_to_path:
            return self._written_to_path

        match_info = self.match_info
        if 'uuid' not in match_info:
            return None

        if not os.path.exists(self.matches_folder):
            os.mkdir(self.matches_folder)

        # Dump statistics as json and zip it
        path = self.GenerateMatchPath()

        try:
            stats_json = json.dumps(match_info)
        except TypeError as e:
            PrintWarning('Could not json dump match info: %s\n' % e)
            str_match_info = str(match_info)
            x = 0
            l = len(str_match_info)
            while x < l:
                PrintWarning(str_match_info[x:min(l, x+1024)])
                x += 1024
            PrintWarning('\n')
            return None

        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('stats.json', stats_json)

        self._written_to_path = filesystem.RelativePathToFullPath(path)
        return self._written_to_path

    @property
    def timestamp(self):
        """ Returns match timestamp (from start) as string with 2 decimal precision. """
        return '%.2f' % (gpGlobals.curtime - self.record_start_time)

    def UpdateStats(self):
        """ Creates a new event entry. """
        new_event = self.GetCurrentStats()
        self._events.append(new_event)

        # Update the current duration of the match
        match_info = self.match_info
        match_info['duration'] = self.timestamp

    def GetCurrentStats(self):
        """ Returns a dictionary with statistics of all players for the current timestamp. """
        event = {
            'timestamp': self.timestamp
        }

        for owner in self._valid_owners:
            # Save the current state
            event[owner] = {
                # Log current amount of resources and total collected so far
                'current_resources': dict(resources[owner]),
                'collected_resources': dict(self._collected_resources[owner]),
                'spent_resources': dict(self._spent_resources[owner]),
                'spent_resources_per_category': copy.deepcopy(self._spent_resources_per_category[owner]),

                # Log population
                'population': unitpopulationcount[owner],
                'max_population': GetMaxPopulation(owner),
            }

        return event

    def OnResourcesCollected(self, owner, type, amount, *args, **kwargs):
        if owner not in self._valid_owners:
            return
        self._collected_resources[owner][type] += amount

    def OnResourcesSpent(self, owner, type, amount, resource_category, *args, **kwargs):
        if owner not in self._valid_owners:
            return
        self._spent_resources[owner][type] += amount
        self._spent_resources_per_category[owner][type][resource_category] += amount

    def OnBuildingStarted(self, building, **kwargs):
        owner = building.GetOwnerNumber()
        self._build_events[owner].append((self.timestamp, building.unitinfo.name))

    def OnBuildingFinished(self, building, **kwargs):
        owner = building.GetOwnerNumber()
        self._buildings_constructed[owner] += 1

    def OnProductionStarted(self, building, info, **kwargs):
        owner = building.GetOwnerNumber()
        self._build_events[owner].append((self.timestamp, info.name))

    def OnUnitSpawned(self, unit, **kwargs):
        if getattr(unit, 'isbuilding', False):
            return

        owner = unit.GetOwnerNumber()
        self._units_produced[owner] += 1

    def OnUnitKilled(self, unit, dmginfo, **kwargs):
        attacker = dmginfo.GetAttacker()

        owner = unit.GetOwnerNumber()

        self._units_lost[owner] += 1
        if unit.isbuilding:
            self._buildings_lost[owner] += 1

        if attacker and attacker.IsUnit():
            attacker_owner = attacker.GetOwnerNumber()
            self._units_killed[attacker_owner] += 1
            if unit.isbuilding:
                self._buildings_killed[attacker_owner] += 1

    def OnEndGame(self, gamerules, winners, losers, *args, **kwargs):
        match_info = self.match_info
        match_info['ended'] = True
        match_info['winners'] = list(map(operator.itemgetter('ownernumber'), winners))
        match_info['losers'] = list(map(operator.itemgetter('ownernumber'), losers))

    def RenderSteamID(self, steamid):
        type = steamid.GetEAccountType()
        if type == EAccountType.k_EAccountTypeInvalid or type == EAccountType.k_EAccountTypeIndividual:
            return 'STEAM_0:%u:%u' % (1 if (steamid.GetAccountID() % 2) else 0, steamid.GetAccountID()/2)
        return '%llu' % (steamid.ConvertToUint64())

    def GenerateMatchPath(self):
        """ Generates a path name for the match statistics file.

            returns:
                str: path for non existing file
        """
        now = datetime.now()
        basename = '%s_%s-%s-%s' % (self.match_info['map'], now.day, now.month, now.year)
        test_name = os.path.join(self.matches_folder, '%s.lwmatch' % basename)
        i = 1
        while os.path.exists(test_name):
            test_name = os.path.join(self.matches_folder, '%s (%d).lwmatch' % (basename, i))
            i += 1
        return test_name
