import os
from collections import defaultdict
import operator

from srcbase import TEAM_UNASSIGNED, FIRST_GAME_TEAM
from srcbuiltins import Color, KeyValuesToDictFromFile, DictToKeyValues, WriteKeyValuesToFile
from vgui import localize
from gameinterface import GetMapHeader
from steam import steamapicontext
import filesystem
import readmap
import kvdict
import traceback

from core.gamerules.info import dbgamerules
from core.factions import dbfactions

class SettingsInfo(object):
    """ Responsible for providing settings information based on the current state of the game lobby,
        such as the available maps for the selected game modes. 
        
        Also updates the selection if the current one is not valid.
    """
    usemaplistfile = False
    islobbyowner = False

    #: Valid colors for players
    allcolors = {
        '9orange': {'name': '9orange', 'color': Color(251, 126, 20, 255)},
        '12blue': {'name': '12blue', 'color': Color(20, 100, 200, 255)},
        #'13cyan': {'name': '13cyan', 'color': Color(0, 255, 255, 255)},
        '11teal': {'name': '11teal', 'color': Color(0, 128, 128, 255)},
        '6green': {'name': '6green', 'color': Color(0, 255, 0, 255)},
        '2darkred': {'name': '2darkred', 'color': Color(128, 0, 0, 255)},
        '8gold': {'name': '8gold', 'color': Color(221, 204, 0, 255)},
        '1brown': {'name': '1brown', 'color': Color(128, 75, 0, 255)},
        '4twilightblue': {'name': '4twilightblue', 'color': Color(136, 102, 204, 255)},
        '10skyblue': {'name': '10skyblue', 'color': Color(0, 255, 255, 255)},
        '7dimgreen': {'name': '7dimgreen', 'color': Color(153, 204, 153, 255)},
        '3pink': {'name': '3pink', 'color': Color(255, 128, 128, 255)},
        '5purple': {'name': '5purple', 'color': Color(255, 0, 255, 255)},
    }
    
    #: CPU difficulties
    availabledifficulties = [
        {'id': 'easy', 'displayname': 'Mission_Easy'},
        {'id': 'normal', 'displayname': 'Mission_Normal'},
        {'id': 'hard', 'displayname': 'Mission_Hard'},
    ]
    
    #: Prefix added for start spots without grouphints. Indicates they don't have a team setup. 
    free_start_spot_prefix = '_free_start_spot_'
    
    def __init__(self, lobby):
        super().__init__()
        
        self.lobby = lobby
        
        self.RebuildMapList()
        self.RebuildAvailableFactions()
        self.RebuildSlots()
        self.RebuildAvailableColors()

    def BuildMapInfoCacheEntry(self, header, mappath):
        entry = {
            'maprevision': header.maprevision,
            'positioninfo': {},
            'supportedmodes': {'FFA': '0'},
        }

        try:
            blocks, blocksbyclass = readmap.ParseMapEntitiesToBlocks(mappath)
        except ValueError:
            PrintWarning('BuildMapInfoCacheEntry: Invalid map %s in maplist.txt\n' % mappath)
            traceback.print_exc()
            return None

        teamhintcounts = defaultdict(lambda: 0)

        numplayers = 0
        for startent in blocksbyclass['info_start_wars']:
            if len(startent['ownernumber']) == 0: # there are no info_start_wars on the map!
                continue
            numplayers += 1
            position = startent['ownernumber'][0]
            if position not in entry['positioninfo']:
                teamhint = startent['groupname'][0] if 'groupname' in startent else '%s%d' % (
                    self.free_start_spot_prefix, int(position))
                entry['positioninfo'][position] = {
                    'origin': startent['origin'][0],
                    'grouphint': teamhint,
                }
                teamhintcounts[teamhint] += 1

        # Calc supported modes
        # TODO: Move this out of the map info/cache and calculate per game mode. OK for now, but this code
        # may make things too complicated.
        teamhintcountsitems = list(teamhintcounts.items())
        teamhintcountsitems.sort(key=operator.itemgetter(1), reverse=True)

        while len(teamhintcountsitems) > 1:
            teamsetup = ''
            invalid_mode = False
            all_one = True
            total_count = 0
            for teamgroup, count in teamhintcountsitems:
                if count <= 0:
                    invalid_mode = True
                    break
                if count > 1:
                    all_one = False
                if teamsetup:
                    teamsetup += 'vs'
                teamsetup += str(count)
                total_count += count

            if invalid_mode:
                break
            # When all is one, and total count is same as num players, it's just FFA
            if not all_one or total_count != numplayers:
                entry['supportedmodes'][teamsetup] = '0'

            newteamhintcountsitems = []
            for teamgroup, count in teamhintcountsitems:
                new_count = count - 1
                if new_count > 0:
                    newteamhintcountsitems.append((teamgroup, new_count))
            teamhintcountsitems = newteamhintcountsitems

        # TODO: Make this nicer if there are more cases
        if '2vs2vs2vs2' in entry['supportedmodes']:
            entry['supportedmodes']['1vs1'] = '0'
            entry['supportedmodes']['2vs2'] = '0'
            entry['supportedmodes']['3vs3'] = '0'
            entry['supportedmodes']['4vs4'] = '0'

        entry['numplayers'] = numplayers

        return entry

    mapinfocache_version = 3

    def __ReadMapInfoCacheFile(self, path):
        """ Helper to read map info cache file from path.
            If file not exists, returns None.
            Converts contents to dictionary. If version does not match, also returns None.
        """
        if not filesystem.FileExists(path):
            return None

        mapinfocache = KeyValuesToDictFromFile(path)
        # Maybe changed the version format
        if mapinfocache.get('version', None) != self.mapinfocache_version or 'maps' not in mapinfocache:
            return None

        return mapinfocache

    def RebuildMapList(self):
        """ Builds list of maps available on this client.
        
            Each entry also contains additional information, such as the positions.
        """
        self.allmaps = {}
        
        # Make a list of all maps
        maplist = []
        if self.usemaplistfile:
            try:
                with open('maplist.txt', mode='rt') as f:
                    maplist = f.readlines()
                    maplist = list(map(str.rstrip, maplist))
            except IOError:
                PrintWarning('ReBuildMapList: Failed to open maplist.txt\n')
                return
        else:
            for f in os.listdir("maps"):
                if os.path.isdir(f):
                    continue
                base, ext = os.path.splitext(f)
                if ext != '.bsp':
                    continue
                maplist.append(base)

        # Read map info cache, or create one if empty
        mapinfocache_path = 'lobbymapinfo.cache'
        mapinfocache_path_default = 'lobbymapinfo_default.cache'
        mapinfocache_changed = False

        mapinfocache = self.__ReadMapInfoCacheFile(mapinfocache_path)
        if not mapinfocache:
            DevMsg(1, 'Info map cache: %s does not exists. Trying default...\n' % (mapinfocache_path))
            mapinfocache = self.__ReadMapInfoCacheFile(mapinfocache_path_default)
            if mapinfocache:
                # Write default to disk
                mapinfocache_changed = True
            else:
                DevMsg(1, 'Info map cache: Default %s does not exists. Creating empty new one.\n'
                       % (mapinfocache_path_default))
                mapinfocache = {'version': self.mapinfocache_version, 'maps': {}}
                mapinfocache_changed = True

        # For each found map, find available start positions
        mapinfocache_maps = mapinfocache['maps']
        for mapname in maplist:
            mapname = mapname.rstrip()

            entry = {}

            # Get entities and parse the locations
            maplocation = 'maps/%s.bsp' % (mapname)

            try:
                header = GetMapHeader(maplocation)
            except ValueError as e:
                PrintWarning('Skipping map %s: %s\n' % (mapname, e))
                continue

            # Get from cache, fill if needed
            if mapname not in mapinfocache_maps or mapinfocache_maps[mapname].get('maprevision', 'invalid') != header.maprevision:
                mapinfocache_maps[mapname] = self.BuildMapInfoCacheEntry(header, maplocation)
                mapinfocache_changed = True
            mapinfocache_entry = mapinfocache_maps[mapname]

            positioninfo = mapinfocache_entry.get('positioninfo', {})
            entry['positioninfo'] = {}
            for position_key, value in positioninfo.items():
                position = int(position_key)
                entry['positioninfo'][position] = dict(value)

            entry['supportedmodes'] = []
            supportedmodes = mapinfocache_entry.get('supportedmodes', {'FFA': '0'})
            for mode in supportedmodes.keys():
                entry['supportedmodes'].append(mode)
            entry['supportedmodes'].sort()
            numplayers = mapinfocache_entry.get('numplayers', 0)

            # Parse resource info for overview file
            maprespath = 'maps/%s.res' % (mapname)
            if filesystem.FileExists(maprespath):
                kvres = kvdict.LoadFileIntoDictionaries(maprespath)
                overviewpath = kvres.get('material', '')
                entry['overviewsrc'] = 'vtf://%s' % (overviewpath)
                
                # Normalize positions in a range from 0 to 1
                try:
                    scale = float(kvres.get('scale', 1.0))
                    pos_x = float(kvres.get('pos_x', -512.0))
                    pos_y = float(kvres.get('pos_y', -512.0))
                    end_x = pos_x + (scale * 1024.0)
                    end_y = pos_y + (-scale * 1024.0)
                    
                    for key, positioninfo in entry['positioninfo'].items():
                        origin = list(map(float, positioninfo['origin'].split(' ')))
                        origin[0] = (origin[0] - pos_x) / (end_x - pos_x)
                        origin[1] = (origin[1] - pos_y) / (end_y - pos_y)
                        positioninfo['origin'] = (origin[0], origin[1])
                except ValueError:
                    PrintWarning('Bad values for scale, pos_x, pos_y or start positions in map res %s\n' % (maprespath))
            else:
                entry['overviewsrc'] = ''
                    
            entry['id'] = mapname
            entry['mapname'] = mapname
            entry['displayname'] = '%s (%d)' % (mapname, numplayers)
            self.allmaps[mapname] = entry

        if mapinfocache_changed:
            kv = DictToKeyValues(mapinfocache, name='mapinfo_cache', keys_sorted=True)
            if kv:
                WriteKeyValuesToFile(kv, mapinfocache_path, pathid='MOD')
            
        self.RebuildAvailableMapList()
            
    def RebuildAvailableMapList(self):
        self.availablemaps = {}
        
        info = dbgamerules.get(self.lobby.datamodel.mode, None)
        if not info:
            return
        
        for name, entry in self.allmaps.items():
            if not info.mapfilter.match(entry['mapname']):
                continue
            self.availablemaps[name] = entry
            
    def __FindGroupHintFromPositionInfo(self, positioninfo, excludegrouphints):
        best = None
        for info in positioninfo.values():
            if info['grouphint'] in excludegrouphints:
                continue
            best = info['grouphint']
            if not best.startswith(self.free_start_spot_prefix):
                break
        return best
        
    def __AddAvailablePositionsForHint(self, positioninfo, posset, hint):
        for poskey, info in positioninfo.items():
            if info['grouphint'] == hint:
                posset.add(poskey)
            
    def RebuildSlots(self):
        """ Rebuilds slot based on the selected team setup.
        
            These slots have a fixed team based on the hints.
            They are returned sorted on team, so they can be easily
            displayed in the UI.
        """
        if not self.lobby.islobbyowner:
            return
            
        datamodel = self.lobby.datamodel
        oldslots = datamodel.slots
        slots = []
        
        teamsetup = self.lobby.datamodel.teamsetup
        if not teamsetup:
            return
        
        entry = self.availablemaps.get(self.lobby.datamodel.map, None)
        if not entry:
            PrintWarning('No map information available for "%s"\n' % (self.lobby.datamodel.map))
            return
        
        if teamsetup not in entry['supportedmodes']:
            teamsetup = 'FFA'
            
        availableposperteam = defaultdict(lambda: set())
        
        positioninfo = dict(entry['positioninfo'])
        if teamsetup == 'FFA':
            for poskey, info in positioninfo.items():
                availableposperteam[TEAM_UNASSIGNED].add(poskey)
                oldslot = oldslots[len(slots)] if len(slots) < len(oldslots) else None
                slots.append({
                    'type': oldslot['type'] if oldslot else 'open',
                    'team': TEAM_UNASSIGNED,
                    'availablepositions': availableposperteam[TEAM_UNASSIGNED],
                    'player': oldslot['player'] if oldslot else None,
                    'iscpu': oldslot['iscpu'] if oldslot else False,
                    'cputype': oldslot['cputype'] if oldslot else 'cpu_wars_default',
                    'difficulty': oldslot['difficulty'] if oldslot else 'normal',
                })
        else:
            usedgrouphints = set()
            curteamnumber = FIRST_GAME_TEAM
            curgrouphint = self.__FindGroupHintFromPositionInfo(positioninfo, usedgrouphints)
            teams = list(map(int, teamsetup.split('vs')))
            while teams:
                foundposkey = None
                foundentry = None
                
                while not foundentry and positioninfo:
                    for pos, info in positioninfo.items():
                        if info['grouphint'] == curgrouphint:
                            foundposkey = pos
                            foundentry = info
                            break
                    if not foundentry:
                        usedgrouphints.add(curgrouphint)
                        curgrouphint = self.__FindGroupHintFromPositionInfo(positioninfo, usedgrouphints)
                        
                if not foundentry:
                    raise Exception('Invalid team setup mode %s' % (teamsetup))
                    
                self.__AddAvailablePositionsForHint(positioninfo, availableposperteam[curteamnumber], curgrouphint)
                    
                del positioninfo[foundposkey]
                oldslot = oldslots[len(slots)] if len(slots) < len(oldslots) else None
                slots.append({
                    'type': oldslot['type'] if oldslot else 'open',
                    'team': curteamnumber,
                    'availablepositions': availableposperteam[curteamnumber],
                    'player': oldslot['player'] if oldslot else None,
                    'iscpu': oldslot['iscpu'] if oldslot else False,
                    'cputype': oldslot['cputype'] if oldslot else 'cpu_wars_default',
                    'difficulty': oldslot['difficulty'] if oldslot else 'normal',
                })
                
                teams[0] -= 1
                if teams[0] == 0:
                    teams.pop(0)
                    curteamnumber += 1
                    usedgrouphints.add(curgrouphint)
                    curgrouphint = self.__FindGroupHintFromPositionInfo(positioninfo, usedgrouphints)
            
        self.lobby.datamodel.slots = slots
        
    def CreateNewPlayerData(self, playersteamid=''):
        return {
            'steamid': str(playersteamid),
            'faction': self.FindAvailableFaction(),
            'color': self.FindFreeColor(),
            'ready': not playersteamid,
        }

    def FindSlotForPlayer(self, playersteamid):
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        
        foundslot = False
        for slot in slots:
            if slot['type'] != 'open':
                continue
                
            slot['type'] = 'player'
            slot['player'] = self.CreateNewPlayerData(playersteamid)
                
            foundslot = True
            print('Found slot for player %s' % (str(playersteamid)))
            break
            
        if foundslot:
            datamodel.slots = slots
        else:
            print('Could not find slot for player %s' % (str(playersteamid)))
            
    def FindAndRemovePlayerFromSlot(self, playersteamid, slots=None):
        updatedatamodel = False
        datamodel = self.lobby.datamodel
        if slots == None:
            slots = datamodel.slots
            updatedatamodel = True
            
        oldplayerdata = None
        
        foundslot = False
        for slot in slots:
            if slot['type'] != 'player':
                continue
            if slot['player']['steamid'] != str(playersteamid):
                continue
                
            slot['type'] = 'open'
            oldplayerdata = slot['player']
            slot['player'] = None
            foundslot = True
                
        if foundslot and updatedatamodel:
            datamodel.slots = slots
        return oldplayerdata
            
    def TryTakeSlot(self, playersteamid, slotid):
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        if slotid >= len(slots):
            return
            
        slot = slots[slotid]
        if slot['type'] != 'open':
            return
        
        playerdata = self.FindAndRemovePlayerFromSlot(playersteamid, slots=slots) or self.CreateNewPlayerData(playersteamid)
        slot['type'] = 'player'
        slot['player'] = playerdata
        
        datamodel.slots = slots
        
    def AddCPUToSlot(self, slotid):
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        if slotid >= len(slots):
            return
            
        slot = slots[slotid]
        if slot['type'] != 'open':
            return
            
        slot['type'] = 'player'
        slot['iscpu'] = True
        slot['player'] = self.CreateNewPlayerData()
        
        datamodel.slots = slots
        
    def RemoveCPUFromSlot(self, slotid):
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        if slotid >= len(slots):
            return
            
        slot = slots[slotid]
        if slot['type'] != 'player' or not slot['iscpu']:
            return
            
        slot['type'] = 'open'
        slot['iscpu'] = False
        
        datamodel.slots = slots
        
    def FindAvailableFaction(self):
        if not self.availablefactions:
            return None
        return next(iter(sorted(self.availablefactions.keys())))
            
    def RebuildAvailableFactions(self, validateslots=True):
        """ Rebuilds the available faction choices for a player, based
            on the loaded game packages and game mode. 
            
            Kwargs:
                validateslots (bool): After rebuilding the available factions,
                                      validates if the existing player choices
                                      are still valid.
        """
        self.availablefactions = {}
        
        info = dbgamerules.get(self.lobby.datamodel.mode, None)
        if not info:
            return
            
        for faction_name, faction_info in dbfactions.items():
            if not faction_info.gamerulesfilter.match(info.name):
                continue
            if not info.factionfilter.match(faction_name):
                continue
            self.availablefactions[faction_name] = {
                'name': faction_name,
                'displayname': faction_info.displayname,
            }

        # Add a random option. This will be parsed when building the game data.
        if self.availablefactions:
            name = '__random__'
            self.availablefactions[name] = {
                'name': name,
                'displayname': 'Random',
            }

        if validateslots:
            self.ValidateSlots()
        
    def FindFreeColor(self):
        for color, info in self.availablecolors.items():
            if info['available']:
                return color
        return None

    def IsColorAvailable(self, color):
        return color in self.availablecolors and self.availablecolors[color]['available']
            
    def FindHighestSupportedTeamMode(self):
        datamodel = self.lobby.datamodel
        entry = self.availablemaps.get(datamodel.map, None)
        if entry:
            bestteammode = None
            bestnumplayers = 0
            bestnumteams = 0
            for teammode in entry['supportedmodes']:
                players = teammode.split('vs')
                if len(players) == 1:
                    continue
                try:
                    numplayers = 0
                    for n in players:
                        numplayers += int(n)
                except ValueError:
                    continue
                    
                if numplayers > bestnumplayers or (numplayers == bestnumplayers and len(players) > bestnumteams):
                    bestteammode = teammode
                    bestnumplayers = numplayers
                    bestnumteams = len(players)
                    
            return bestteammode
        
        return None
            
    def RebuildAvailableColors(self):
        self.availablecolors = dict(self.allcolors)
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        
        for color in self.availablecolors.values():
            color['available'] = True
        
        for slot in slots:
            playerdata = slot['player']
            if playerdata and playerdata['color'] in self.availablecolors:
                self.availablecolors[playerdata['color']]['available'] = False
            
    @property
    def availablemodes(self):
        availablemodes = {}
        for name, info in dbgamerules.items():
            if info.hidden:
                continue
            availablemodes[name] = {
                'id': info.name,
                'name': info.displayname,
                'description': info.description,
            }
        return availablemodes
        
    def OnModeChanged(self):
        """ Called when the selected mode changed. """
        self.RebuildAvailableMapList()
        if self.availablemaps and self.lobby.islobbyowner:
            datamodel = self.lobby.datamodel
            if datamodel.map not in self.availablemaps:
                datamodel.map = next (iter (sorted(self.availablemaps.keys())))
        self.RebuildAvailableFactions()
        self.RebuildCustomFields()
        
    def OnMapChanged(self):
        """ Called when the selected map changed. """
        if self.lobby.islobbyowner:
            datamodel = self.lobby.datamodel
            entry = self.availablemaps.get(datamodel.map, None)
            if entry:
                if datamodel.teamsetup not in entry['supportedmodes'] or datamodel.teamsetup == 'FFA':
                    datamodel.teamsetup = self.FindHighestSupportedTeamMode() or 'FFA'
                    
        self.RebuildSlots()
        self.RebuildAvailableFactions()
        
    def OnTeamSetupChanged(self):
        """ Called when the selected setup changed.
        
            A team setup is for example "2vs2", "4vs4" or FFA.
        """
        self.RebuildSlots()
        
    def OnSlotsChanged(self):
        self.RebuildAvailableColors()
        
    def ValidateSlots(self):
        """ Validates the slots of all players.
        
            Prevents invalid choices.
        """
        if not self.lobby.islobbyowner:
            return
            
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        
        changed = False
        for slot in slots:
            playerdata = slot.get('player', None)
            if playerdata:
                faction = playerdata.get('faction', None)
                if faction not in self.availablefactions:
                    playerdata['faction'] = self.FindAvailableFaction()
                    changed = True
                    
        if changed:
            datamodel.slots = slots
            
    def IsEverybodyReady(self):
        if self.lobby.isofflinelobby:
            return True
            
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        
        for slot in slots:
            if slot['type'] == 'open' or slot['iscpu']:
                continue
            if slot['player'] and not slot['player']['ready']:
                return False
                
        return True
        
    def InvalidateReady(self):
        changed = False
        datamodel = self.lobby.datamodel
        slots = datamodel.slots
        
        for slot in slots:
            if slot['type'] == 'open' or slot['iscpu']:
                continue
                
            playerdata = slot['player']
            changed = True
            playerdata['ready'] = False
                
        if changed:
            datamodel.slots = slots
            
    def RebuildCustomFields(self):
        self.customfields = {}
        
        datamodel = self.lobby.datamodel
        info = dbgamerules.get(datamodel.mode, None)
        if not info or not info.cls:
            return
            
        self.customfields = info.cls.GetCustomFields()
        for key in self.customfields.keys():
            name = self.customfields[key].get('name', None)
            if not name:
                continue
            if name.startswith('#'):
                localizedname = localize.Find(name)
                if localizedname:
                    self.customfields[key]['name'] = localizedname
                else:
                    self.customfields[key]['name'] = key
        
        # Get current selection and ensure default values are set
        islobbyowner = self.lobby.islobbyowner
        
        for id, cf in self.customfields.items():
            value = datamodel.GetCustomLobbyData(id)
            if islobbyowner and value == None:
                datamodel.SetCustomLobbyData(id, cf.get('default', ''))
                value = datamodel.GetCustomLobbyData(id)
            cf['selectedvalue'] = value
