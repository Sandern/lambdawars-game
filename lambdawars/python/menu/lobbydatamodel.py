from steam import steamapicontext

class LobbyDataModel(object):
    """ Controls the data in the lobby.
    
        Performs conversions where needed.
        Does not check if values are valid, which is up to the lobby owner.
    """
    def __init__(self, steamidlobby, offline=False):
        """ Initializes (Steam) lobby data model.

            Args:
                steamidlobby (CSteamID): ID of lobby

            Kwargs:
                offline (bool): Indicates it's an offline lobby, not using the Steam back-end.
                                Will store everything locally in a dictionary.
        """
        super().__init__()
        
        self.offline = offline
        self.steamidlobby = steamidlobby
        self.lobby_data = {}
        self.commit_data_pending = False
        self.commit_changed_keys = set()
        
        self.changecallbacks = {
        }

    def GetLobbyData(self, key, converter=None, default=None):
        data = self.lobby_data.get(key, None)
        if not data:
            return default
        if not converter:
            return data
        return converter(data)
        
    def SetLobbyData(self, key, value):
        self.lobby_data[key] = value
        fncallback = self.changecallbacks.get(key, None)
        if fncallback:
            fncallback()
        self.commit_changed_keys.add(key)
        self.commit_data_pending = True

    def CommitData(self):
        """ Sends the data to the Steam back-end.
            No-op for offline lobby, just returns True or False depending on if there
            was data to commit.

            Returns:
                set: changed keys
        """
        if not self.offline:
            steam_matchmaking = steamapicontext.SteamMatchmaking()
            steamid_lobby = self.steamidlobby
            for key in self.commit_changed_keys:
                value = self.lobby_data[key]
                if not steam_matchmaking.SetLobbyData(steamid_lobby, key, value):
                    # TODO: Does this ever happen?
                    PrintWarning('Failed to update lobby data (%s=%s)\n' % (key, value))

        changed_keys = self.commit_changed_keys
        self.commit_changed_keys = set()
        self.commit_data_pending = False
        return changed_keys

    def ReadData(self):
        """ Reads data from Steam lobby.

            Returns:
                set: contains the changed keys of data since last call.
        """
        if self.offline:
            return set()

        # Update the data
        changed_keys = set()
        steam_matchmaking = steamapicontext.SteamMatchmaking()
        steamid_lobby = self.steamidlobby
        for i in range(0, steam_matchmaking.GetLobbyDataCount(steamid_lobby)):
            success, key, value = steam_matchmaking.GetLobbyDataByIndex(steamid_lobby, i)
            # Seems some keys get capitalized!? For example, 'map' becomes 'Map'. Why Steamworks? Always use lower here.
            key = key.lower()
            if success and self.lobby_data.get(key, None) != value:
                self.lobby_data[key] = value
                changed_keys.add(key)

        # Only trigger changed callbacks until all data is stored
        for key in changed_keys:
            fncallback = self.changecallbacks.get(key, None)
            if fncallback:
                fncallback()

        return changed_keys

    # Access only: number of members
    @property
    def nummembers(self):
        if self.offline:
            return 1
        steammatchmaking = steamapicontext.SteamMatchmaking()
        steamidlobby = self.steamidlobby
        if not steammatchmaking or not steamidlobby:
            return 1
        return steammatchmaking.GetNumLobbyMembers(steamidlobby)
    
    # Game product version
    @property
    def version(self):
        return self.GetLobbyData('version')

    @version.setter
    def version(self, value):
        self.SetLobbyData('version', value)

    # Game dir
    @property
    def game_dir(self):
        return self.GetLobbyData('game:dir')

    @game_dir.setter
    def game_dir(self, value):
        self.SetLobbyData('game:dir', value)
        
    # The name of the lobby
    @property
    def name(self):
        return self.GetLobbyData('name')

    @name.setter
    def name(self, value):
        self.SetLobbyData('name', value)
        
    # The state of the lobby
    @property
    def lobbystate(self):
        return self.GetLobbyData('lobbystate')

    @lobbystate.setter
    def lobbystate(self, value):
        self.SetLobbyData('lobbystate', value)
    
    # The Steam lobby type
    @property
    def lobbytype(self):
        return self.GetLobbyData('lobbytype')

    @lobbytype.setter
    def lobbytype(self, value):
        self.SetLobbyData('lobbytype', value)
    
    # The Game lobby type
    @property
    def type(self):
        return self.GetLobbyData('type')

    @type.setter
    def type(self, value):
        self.SetLobbyData('type', value)
