from steam import steamapicontext, CSteamID
from ..lobbydatamodel import LobbyDataModel

from core.factions import GetFactionInfo
import random

def _customfield(fieldname):
    return '__custom_%s' % (fieldname)

def _playerfield(steamid, fieldname):
    return 'player_%s_%s' % (steamid, fieldname)

def _slotfield(slotidx, fieldname):
    return 'slot_%s%s' % (slotidx, fieldname)

class LobbyGameDataModel(LobbyDataModel):
    """ Controls the game data in the lobby.
    
        Performs conversions where needed.
        Does not check if values are valid, which is up to the lobby owner.
    """
    defaultmapselection = [
        'hlw_village',
        'hlw_abandoned',
        'hlw_metro',
        'hlw_washedaway',
        'hlw_woodland',
        'hlw_city16',
        'hlw_waste',
        'hlw_synth',
        'hlw_jungle',
        'hlw_outland',
    ]
    defaultgameruleselection = [
        'annihilation',
        'destroyhq',
        'overrun',
    ]

    def InitSettingsInfoCallbacks(self, lobby, islobbyowner):
        settingsinfo = lobby.settingsinfo

        # Not nice, but this class no longer exists in newer csgo build version.
        self.lobby = lobby

        if islobbyowner:
            # Set the default values (TODO: shouldn't really be set from here)
            self.lobbystate = 'lobbying'
            self.mode = random.sample(self.defaultgameruleselection, 1)[0]
            self.map = random.sample(self.defaultmapselection, 1)[0]
    
        self.changecallbacks.update({
            'mode': settingsinfo.OnModeChanged,
            'map': settingsinfo.OnMapChanged,
            'teamsetup': settingsinfo.OnTeamSetupChanged,
            'slots': settingsinfo.OnSlotsChanged,
            'version': lobby.OnVersionReceived,
        })
        
        if islobbyowner:
            settingsinfo.OnModeChanged()
            settingsinfo.OnMapChanged()
            
    def SetCustomLobbyData(self, fieldname, value):
        self.SetLobbyData(_customfield(fieldname), value)

    def GetCustomLobbyData(self, fieldname):
        return self.GetLobbyData(_customfield(fieldname))
        
    def SetPlayerLobbyData(self, steamid, key, value):
        self.SetLobbyData(_playerfield(steamid, key), value)
        
    def SetSlotLobbyData(self, idx, key, value):
        self.SetLobbyData(_slotfield(idx, key), value)
        
    # Kicking
    def MarkPlayerKicked(self, steamid):
        self.SetLobbyData('kicked_%s' % (str(steamid)), '1')

    def IsPlayerKicked(self, steamid):
        val = self.GetLobbyData('kicked_%s' % (str(steamid)))
        if not val:
            return False
        try:
            return bool(int(val))
        except ValueError:
            return False

    def ClearPlayerKicked(self, steamid):
        self.SetLobbyData('kicked_%s' % (str(steamid)), '0')
        
    # Connect state
    def SetPlayerConnectState(self, hoststeamid, othersteamid, state):
        self.SetLobbyData('connectstate_%s_%s' % (str(hoststeamid), str(othersteamid)), '1' if state else '0')
        
    def GetPlayerConnectState(self, hoststeamid, othersteamid):
        if hoststeamid == othersteamid:
            return True
        val = self.GetLobbyData('connectstate_%s_%s' % (str(hoststeamid), str(othersteamid)))
        if not val:
            return None
        try:
            return bool(int(val))
        except ValueError:
            return None
        
    # The state of the lobby
    @property
    def lobbystate(self):
        return self.GetLobbyData('lobbystate', default='lobbying')

    @lobbystate.setter
    def lobbystate(self, value):
        self.SetLobbyData('lobbystate', value)

    @property
    def match_uuid(self):
        return self.GetLobbyData('match_uuid', default='')

    @match_uuid.setter
    def match_uuid(self, value):
        self.SetLobbyData('match_uuid', value)
        
    # The game mode
    @property
    def mode(self):
        return self.GetLobbyData('mode')

    @mode.setter
    def mode(self, value):
        if self.mode == value:
            return
        self.SetLobbyData('mode', value)
        
    # The map
    @property
    def map(self):
        return self.GetLobbyData('map')

    @map.setter
    def map(self, value):
        if self.map == value:
            return
        self.SetLobbyData('map', value)
        
    # The team setup
    @property
    def teamsetup(self):
        return self.GetLobbyData('teamsetup')

    @teamsetup.setter
    def teamsetup(self, value):
        if self.teamsetup == value:
            return
        self.SetLobbyData('teamsetup', value)
        
    # Reservation ticket, only used when a player is self hosting a server
    @property
    def reservationticket(self):
        return self.GetLobbyData('reservationticket')

    @reservationticket.setter
    def reservationticket(self, value):
        if self.reservationticket == value:
            return
        self.SetLobbyData('reservationticket', value)

    # Public IP send by server accept message
    @property
    def publicip(self):
        return self.GetLobbyData('publicip', converter=int, default=0)

    @publicip.setter
    def publicip(self, value):
        if self.publicip == value:
            return
        self.SetLobbyData('publicip', str(value))

    @property
    def gameport(self):
        return self.GetLobbyData('gameport', converter=int, default=0)

    @gameport.setter
    def gameport(self, value):
        if self.gameport == value:
            return
        self.SetLobbyData('gameport', str(value))

        
    # The slot layout and their attached player configurations
    @property
    def numslots(self):
        return self.GetLobbyData('numslots', converter=int, default=0)

    @property
    def numtakenslots(self):
        return self.GetLobbyData('numtakenslots', converter=int, default=0)
        
    @property
    def slots(self):
        localsteamid = str(steamapicontext.SteamUser().GetSteamID())
        numslots = self.numslots
        slots = []
        for i in range(0, numslots):
            entry = {
                'slotid': i,
                'type': self.GetLobbyData(_slotfield(i, 'type'), default='open'),
                'team': self.GetLobbyData(_slotfield(i, 'team'), converter=int, default=0),
                'availablepositions': self.GetLobbyData(_slotfield(i, 'availablepositions'), converter=lambda x: set(map(int, x.split(','))), default=set(['2'])),
                'iscpu': self.GetLobbyData(_slotfield(i, 'iscpu'), converter=lambda x: bool(int(x)), default=False),
                'cputype': self.GetLobbyData(_slotfield(i, 'cputype'), default='cpu_wars_default'),
                'difficulty': self.GetLobbyData(_slotfield(i, 'difficulty'), default='easy'),
                'player': None,
            }
            playersteamid = self.GetLobbyData(_slotfield(i, 'steamid'), default='')
            iscpu = entry['iscpu']
            if playersteamid or iscpu:
                if iscpu:
                    fnfield = _slotfield
                    playerdataid = i
                else:
                    fnfield = _playerfield
                    playerdataid = playersteamid
                    
                playerdata = {
                    'steamid': playersteamid,
                    'name': steamapicontext.SteamFriends().GetFriendPersonaName(CSteamID(int(playersteamid))) if not iscpu else 'CPU #%d' % (i),
                    'faction': self.GetLobbyData(fnfield(playerdataid, 'faction'), default=''),
                    'color': self.GetLobbyData(fnfield(playerdataid, 'color'), default=''),
                    'ready': self.GetLobbyData(fnfield(playerdataid, 'ready'), converter=lambda x: bool(int(x)), default=False),
                    'islocaluser': localsteamid == playersteamid and not iscpu,
                    'isLobbyLeader': playersteamid == str(self.lobby.GetLobbyOwner()),
                }
                
                # Do some enriching for the js code
                if playerdata['faction'] == '__random__':
                    playerdata['factionname'] = 'Random'
                else:
                    faction_info = GetFactionInfo(playerdata['faction'])
                    playerdata['factionname'] = faction_info.displayname if faction_info else playerdata['faction']

                entry['player'] = playerdata
                
            slots.append(entry)
        
        return slots
        
    @slots.setter
    def slots(self, slots):
        # Updated slots configuration by the lobby owner
        self.SetLobbyData('numslots', str(len(slots)))
        numtakenslots = 0
        for i, slot in enumerate(slots):
            if slot['type'] == 'player':
                numtakenslots += 1
        
            self.SetLobbyData(_slotfield(i, 'type'), slot['type'])
            self.SetLobbyData(_slotfield(i, 'team'), str(slot['team']))
            self.SetLobbyData(_slotfield(i, 'availablepositions'), ','.join(map(str,slot['availablepositions'])))
            
            self.SetLobbyData(_slotfield(i, 'iscpu'), str(int(slot['iscpu'])))
            self.SetLobbyData(_slotfield(i, 'cputype'), slot['cputype'])
            self.SetLobbyData(_slotfield(i, 'difficulty'), slot['difficulty'])
            
            playerdata = slot.get('player', None)
            if playerdata:
                # For CPUs, this information is stored in the slot, while for players it's in their own corner
                # This is useful for remember the last choices of a player
                steamid = playerdata['steamid']
                if slot.get('iscpu', False):
                    fnfield = _slotfield
                    playerdataid = i
                else:
                    fnfield = _playerfield
                    playerdataid = steamid
                    
                self.SetLobbyData(_slotfield(i, 'steamid'), playerdata['steamid'])
                self.SetLobbyData(fnfield(playerdataid, 'faction'), playerdata['faction'])
                self.SetLobbyData(fnfield(playerdataid, 'color'), playerdata['color'])
                self.SetLobbyData(fnfield(playerdataid, 'ready'), str(int(playerdata['ready'])))
            else:
                self.SetLobbyData(_slotfield(i, 'steamid'), '')
                
        self.SetLobbyData('numtakenslots', str(numtakenslots))
        
        self.changecallbacks['slots']()
        
    def FindPlayerSlot(self, playersteamid, slots=None):
        """ Finds existing slot of player. None if not found. """

        if slots == None:
            slots = self.slots
        
        for slot in slots:
            if slot['player'] and slot['player']['steamid'] == str(playersteamid):
                return slot
        return None

