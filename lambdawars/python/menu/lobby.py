""" Provides a minimal lobby webview component.

Provides methods for creating, joining and destroying lobbies on the Steam back-end.
Manages the users, and callbacks for chat and enter/leave events.
"""

import srcmgr
from cef import WebViewComponent, jsbind
from steam import (steamapicontext, CSteamID, LobbyMatchListCallResult, ELobbyDistanceFilter, ELobbyComparison,
                   k_uAPICallInvalid, ELobbyType, EResult, EChatEntryType, LobbyCreatedCallResult, LobbyCreated_t,
                   LobbyEnterCallResult, LobbyChatMsgCallback, LobbyChatUpdateCallback, LobbyDataUpdateCallback,
                   EChatMemberStateChange)
from .lobbydatamodel import LobbyDataModel
from gameinterface import engine


class WebLobbyMatchListCallResult(LobbyMatchListCallResult):
    def OnLobbyMatchList(self, lobbymatchlist, iofailure):
        self.webview.OnLobbyMatchListCallResult(lobbymatchlist, iofailure, self.callbackid)


class WebLobbyCreatedCallResult(LobbyCreatedCallResult):
    def OnLobbyCreated(self, lobbycreated, iofailure):
        if self.webview.callback_lobby_create != self:
            return
        self.webview.OnLobbyCreated(lobbycreated, iofailure)


class WebLobbyEnterCallResult(LobbyEnterCallResult):
    def OnLobbyEnter(self, data, iofailure):
        if self.webview.callback_lobby_join != self:
            return
        self.webview.OnLobbyJoined(data, iofailure)


class WebLobby(WebViewComponent, LobbyChatMsgCallback, LobbyChatUpdateCallback, LobbyDataUpdateCallback):
    steamidlobby = None
    lobbyname = 'Default lobby name'
    lobbytype = None
    jshandler = None
    datamodel = None
    pending_post_read_data = False
    read_data_changed_keys = None

    # Callbacks
    callback_lobby_create = None
    callback_lobby_join = None

    defaultlobbytype = 'invisible'
    lobbystr2type = {
        'private': ELobbyType.k_ELobbyTypePrivate,  # only way to join the lobby is to invite to someone else
        'friendsonly': ELobbyType.k_ELobbyTypeFriendsOnly,  # shows for friends or invitees, but not in lobby list
        'public': ELobbyType.k_ELobbyTypePublic,  # visible for friends and in lobby list
        'invisible': ELobbyType.k_ELobbyTypeInvisible,  # returned by search, but not visible to other friends
                                                        # useful if you want a user in two lobbies, for example matching groups together
                                                        # a user can be in only one regular lobby, and up to two invisible lobbies
    }
    type2lobbystr = {v: k for k, v in lobbystr2type.items()}

    #: Max number of lobby members
    max_members = 240
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Boost python bug: does not chain correctly
        LobbyChatUpdateCallback.__init__(self)
        LobbyDataUpdateCallback.__init__(self)
        
        self.lobbychathandlers = self.BuildLobbyChatMsgHandlers()
        
        self.gamedir = srcmgr.GetModDirectory()
        
    def OnDestroy(self):
        super().OnDestroy()
        
        #print('OnDestroy lobby called. Steam id lobby active? %s' % (str(self.steamidlobby)))
        
        # If there is no mm interface, the steam api has been shutdown already
        # In that case any active lobby has been left
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if not steammatchmaking:
            return 
        
        if self.steamidlobby:
            steammatchmaking.LeaveLobby(self.steamidlobby)
            self.steamidlobby = None
        
    def BuildUserInfo(self, steamid):
        """ Builds info entry for a given user steam id. """
        return {
            'steamid': str(steamid),  # Send full ID as string
            'username': steamapicontext.SteamFriends().GetFriendPersonaName(steamid),
            'isLobbyLeader': steamid == self.GetLobbyOwner(),
        }
        
    def BuildLobbyMembersInfoList(self):
        members = {}
        if self.isofflinelobby:
            userinfo = self.BuildUserInfo(steamapicontext.SteamUser().GetSteamID())
            members[userinfo['steamid']] = userinfo
        else:
            steammatchmaking = steamapicontext.SteamMatchmaking()
            if not steammatchmaking:
                return members
            for i in range(0, steammatchmaking.GetNumLobbyMembers(self.steamidlobby)):
                userinfo = self.BuildUserInfo(steammatchmaking.GetLobbyMemberByIndex(self.steamidlobby, i))
                members[userinfo['steamid']] = userinfo
        return members
        
    @property
    def numlobbymembers(self):
        if self.isofflinelobby:
            return 1
        if not self.steamidlobby:
            return 0
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if not steammatchmaking:
            return 0
        return steammatchmaking.GetNumLobbyMembers(self.steamidlobby)
        
    @property
    def islobbyowner(self):
        if not self.steamidlobby:
            return False
        if self.isofflinelobby:
            return True
        return self.GetLobbyOwner() == steamapicontext.SteamUser().GetSteamID()
        
    @property
    def isofflinelobby(self):
        return self.lobbytype == 'offline'
        
    def AddLobbyTypeFilters(self, limitversion=True):
        """ Adds lobby filters which should be added to every lobby list query call.
        
            This filters on lobby type and version.

            Kwargs:
                limitversion (bool): Filters out lobby for a different game version.
        """
        steammatchmaking = steamapicontext.SteamMatchmaking()
        # For now, search on lobbies everywhere
        steammatchmaking.AddRequestLobbyListDistanceFilter(ELobbyDistanceFilter.k_ELobbyDistanceFilterWorldwide)
        # There are currently two types: "global chat" and "game lobby". Obviously you don't want a game lobby in the
        # global chat
        steammatchmaking.AddRequestLobbyListStringFilter('type', self.defaultobjectname,
                                                         ELobbyComparison.k_ELobbyComparisonEqual)
        # Prevent matching dev against public
        steammatchmaking.AddRequestLobbyListStringFilter('game:dir', self.gamedir,
                                                         ELobbyComparison.k_ELobbyComparisonEqual)
        if limitversion:
            # You can only connect to servers with the same version, so it makes no sense to join lobbies made for a
            # different version
            steammatchmaking.AddRequestLobbyListStringFilter('version', engine.GetProductVersionString(),
                                                             ELobbyComparison.k_ELobbyComparisonEqual)
            
    def AddLobbyListFilters(self):
        """ Adds filters for list lobbies Steam call. """
        self.AddLobbyTypeFilters()
        
    # Matchmaking/chat rooms methods
    @jsbind(hascallback=True, manuallycallback=True)
    def listlobbies(self, methodargs, callbackid):
        matchmaking = steamapicontext.SteamMatchmaking()
        if not matchmaking:
            return
        
        self.AddLobbyListFilters()
        
        steamapicall = matchmaking.RequestLobbyList()
        if steamapicall != k_uAPICallInvalid:
            callback = WebLobbyMatchListCallResult(steamapicall)
            callback.webview = self
            callback.callbackid = callbackid
            self.lobbycallback = callback
        else:
            PrintWarning('listchatlobbies: Failed to make lobby list request\n')
            
    @jsbind()
    def createlobby(self, methodargs):
        if self.steamidlobby is not None:
            PrintWarning('Active lobby still exists! Leave it first.\n')
            return
            
        self.lobbyname = methodargs[0]
        strlobbytype = methodargs[1] if len(methodargs) > 1 and methodargs[1] else self.defaultlobbytype
        
        if strlobbytype == 'offline':
            # Offline: simulate lobby creation call
            self.lobbytype = strlobbytype
            
            data = LobbyCreated_t()
            data.result = EResult.k_EResultOK
            data.steamidlobby = 1
            self.OnLobbyCreated(data, False)
        else:
            if strlobbytype not in self.lobbystr2type:
                PrintWarning('createlobby: invalid lobby type "%s". Valid options are: %s' % (strlobbytype, ', '.join(self.lobbystr2type.keys())))
                return
                
            self.lobbytype = strlobbytype
            lobbytype = self.lobbystr2type[strlobbytype]
            
            steammatchmaking = steamapicontext.SteamMatchmaking()
            if not steammatchmaking:
                return
                
            steamapicall = steammatchmaking.CreateLobby(lobbytype, self.max_members)
            self.callback_lobby_create = WebLobbyCreatedCallResult(steamapicall)
            self.callback_lobby_create.webview = self
            
    @jsbind()
    def joinlobby(self, methodargs):
        steamidlobby = CSteamID(int(methodargs[0]))
        if self.steamidlobby:
            if self.steamidlobby == steamidlobby:
                self.OnLobbyJoined(None, None)
                return
            
            self.leavelobby()
            #PrintWarning('Active lobby still exists! Leave it first.\n')
            #return
            
        self.steamidlobby = steamidlobby
        self.lobbytype = None
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if not steammatchmaking:
            return
        steamapicall = steammatchmaking.JoinLobby(self.steamidlobby)
        self.callback_lobby_join = WebLobbyEnterCallResult(steamapicall)
        self.callback_lobby_join.webview = self
        
    @jsbind()
    def leavelobby(self, methodargs):
        if not self.steamidlobby:
            return
            
        steamidlobby = self.steamidlobby
        if not self.isofflinelobby:
            steammatchmaking = steamapicontext.SteamMatchmaking()
            if not steammatchmaking:
                return
            steammatchmaking.LeaveLobby(steamidlobby)
        self.steamidlobby = None
        self.lobbytype = None
        self.OnLeftLobby(steamidlobby)
        
    @jsbind()
    def setlobbyname(self, methodargs):
        datamodel = self.datamodel
        if not datamodel:
            return
        self.lobbyname = methodargs[0]
        datamodel.name = self.lobbyname
        
    @jsbind()
    def setlobbytype(self, methodargs):
        if self.isofflinelobby:
            return # Not changable in offline mode
        if not self.steamidlobby or not self.islobbyowner:
            return
        datamodel = self.datamodel
        if not datamodel:
            return
        lobbytype = methodargs[0]
        if lobbytype not in self.lobbystr2type:
            PrintWarning('setlobbytype: invalid lobby type "%s". Valid options are: %s' % (lobbytype, ', '.join(self.lobbystr2type.keys())))
            return
            
        self.lobbytype = lobbytype
        datamodel.lobbytype = lobbytype
        
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if steammatchmaking and self.steamidlobby:
            steammatchmaking.SetLobbyType(self.steamidlobby, self.lobbystr2type[self.lobbytype])
        
    @jsbind()
    def sendchatmessage(self, methodargs):
        self.SendLobbyChatMsg('chat %s' % (methodargs[0]))
        
    def SendLobbyChatMsg(self, msgtype, msg=''):
        """ Sends a lobby chat message (communication and changing player/settings data).
        
            Online this sends it through Steam, offline it directly handles the message.

            Args:
                msgtype (str): Type of message to send
                msg (str): Data to send
        """
        if self.isofflinelobby:
            self.OnOfflineLobbyChatMsg('%s %s' % (msgtype, msg))
        else:
            steammatchmaking = steamapicontext.SteamMatchmaking()
            if not steammatchmaking:
                return
            steammatchmaking.SendLobbyChatMsg(self.steamidlobby, '%s %s' % (msgtype, msg))
            
    def GetLobbyOwner(self):
        """ Retrieves the lobby owner steamid
        
            In Online mode, this comes from Steam backend. In offline mode this is the local user.
        """
        if self.isofflinelobby:
            steam_user = steamapicontext.SteamUser()
            if not steam_user:
                return CSteamID()
            return steam_user.GetSteamID()
        
        steammatchmaking = steamapicontext.SteamMatchmaking()
        if not steammatchmaking:
            return None
        return steammatchmaking.GetLobbyOwner(self.steamidlobby)
        
    @jsbind()
    def sethandler(self, methodargs):
        self.jshandler = methodargs[0]
        
    # Steam callbacks
    errormessages = {
        EResult.k_EResultNoConnection : 'Steam_NoConnection',
        EResult.k_EResultTimeout : 'Steam_Timeout',
        EResult.k_EResultFail : 'Steam_Fail',
        EResult.k_EResultAccessDenied : 'Steam_AccessDenied',
        EResult.k_EResultLimitExceeded : 'Steam_LimitExceeded',
    }
    
    def OnLobbyCreated(self, lobbycreated, iofailure):
        self.callback_lobby_create = None

        if iofailure:
            PrintWarning('OnLobbyCreated failed (io failure)\n')
            if self.jshandler:
                self.Invoke(self.jshandler, 'OnCreateLobbyFailed', [-1, 'Steam_IOFailure'])
            return False

        if lobbycreated.result != EResult.k_EResultOK:
            if self.jshandler:
                self.Invoke(self.jshandler, 'OnCreateLobbyFailed', [int(lobbycreated.result),
                                                                    self.errormessages.get(lobbycreated.result,
                                                                                           'Steam_Unknown')])
            return False
            
        steamid = CSteamID(lobbycreated.steamidlobby)
        self.steamidlobby = steamid
        self.datamodel = self.CreateLobbyDataModel(steamid)
            
        datamodel = self.datamodel
        
        # Set some data used by filters
        datamodel.version = engine.GetProductVersionString()
        datamodel.name = self.lobbyname
        datamodel.lobbytype = self.lobbytype
        datamodel.type = self.defaultobjectname
        datamodel.game_dir = self.gamedir

        if not self.isofflinelobby:
            matchmaking = steamapicontext.SteamMatchmaking()
            if matchmaking and steamid:
                matchmaking.SetLobbyJoinable(steamid, True)
        else:
            # Trigger an update
            datamodel.datadirty = True
        
        lobbymembers = self.BuildLobbyMembersInfoList()
        DevMsg(1, 'Created Lobby. Users: %s\n' % (str(lobbymembers)))
        return self.OnJoinOrCreateLobby(lobbymembers)
        
    def OnLobbyJoined(self, data, iofailure):
        self.callback_lobby_join = None

        if iofailure:
            PrintWarning('OnLobbyJoined failed (io failure)\n')
            if self.jshandler:
                self.Invoke(self.jshandler, 'OnCreateLobbyFailed', [-1, 'OnLobbyJoined failed (io failure)'])
            return False
            
        self.datamodel = self.CreateLobbyDataModel(self.steamidlobby)
            
        lobbymembers = self.BuildLobbyMembersInfoList()
        DevMsg(1, 'Joined Lobby. Users: %s\n' % (str(lobbymembers)))
        return self.OnJoinOrCreateLobby(lobbymembers)
            
    def CreateLobbyDataModel(self, steamidlobby):
        return LobbyDataModel(steamidlobby, offline=bool(self.lobbytype == 'offline'))
            
    def OnJoinOrCreateLobby(self, lobbymembers):
        # Make sure the datamodel reflects the data in the lobby
        self.ReadData()

        if self.jshandler:
            self.Invoke(self.jshandler, 'OnJoinOrCreateLobby', [lobbymembers])
        return True
            
    def OnLeftLobby(self, steamidlobby):
        #print('Left lobby %s' % (self.defaultobjectname))
        self.datamodel = None
            
    def BuildLobbyChatMsgHandlers(self):
        return {
            'chat': self.HandleLobbyChatMsg,
        }
    
    def ShouldFilterLobbyChatMsg(self, data):
        return False
    
    def OnLobbyChatMsg(self, data):
        """ Online lobby chat msg handling.
        
            Args:
                data (LobbyChatMsg): the message received from the steam backend, containing:
                                     teamidlobby # the lobby id this is in
                                     steamiduser # steamID of the user who has sent this message
                                     chatentrytype # type of message
                                     chatid # index of the chat entry to lookup
        """
        if self.ShouldFilterLobbyChatMsg(data):
            return
    
        # data contains lobby steam id and index for chat entry
        if data.steamidlobby != self.steamidlobby:
            return # Not for us
            
        matchmaking = steamapicontext.SteamMatchmaking()
        if not matchmaking:
            return
        steamiduser = CSteamID(data.steamiduser)
        data, type = matchmaking.GetLobbyChatEntry(CSteamID(data.steamidlobby), data.chatid, steamiduser)
        
        if not data:
            PrintWarning('game lobby: invalid lobby chat msg\n')
            return
            
        self.DoHandleLobbyChatMsg(data, steamiduser, type)

    def OnOfflineLobbyChatMsg(self, data):
        """ Offline lobby chat msg handling.
        
            Args:
                data (str): the message
        """
        steamiduser = steamapicontext.SteamUser().GetSteamID()
        type = EChatEntryType.k_EChatEntryTypeChatMsg
        self.DoHandleLobbyChatMsg(data, steamiduser, type)
        
    def DoHandleLobbyChatMsg(self, data, steamiduser, type):
        """ Handles lobby chat msg. Data is already retrieved.
            Shared function for offline and online lobby.
        
            Args:
                data (str): chat data
                steamiduser (CSteamID): steam id of the user sending the message
                type (EChatEntryType): type of message
        """
        try:
            msgtype, msg = data.split(' ', 1)
        except ValueError:
            msgtype = data
            msg = ''
            
        handler = self.lobbychathandlers.get(msgtype, None)
        if not handler:
            PrintWarning('Invalid chat msg type %s\n' % (msgtype))
            return
            
        handler(steamiduser, type, msg)
        
    def HandleLobbyChatMsg(self, steamiduser, type, msg):
        #userinfo = self.BuildUserInfo(steamiduser)
        DevMsg(1, 'OnLobbyChatMsg -> Text: %s, type: %s, steamid: %s\n' % (msg, type, str(steamiduser)))
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnLobbyChatMsg', [str(steamiduser), msg])
            
    def OnLobbyUserEntered(self, steamiduser):
        userinfo = self.BuildUserInfo(steamiduser)
        DevMsg(1, 'User %s entered chat room\n' % (userinfo['username']))
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnLobbyChatUserEntered', [userinfo])
            
    def OnLobbyUserLeft(self, steamiduser):
        userinfo = self.BuildUserInfo(steamiduser)
        DevMsg(1, 'User %s left chat room\n' % (userinfo['username']))
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnLobbyChatUserLeft', [userinfo])
    
    def OnLobbyChatUpdate(self, data):
        if data.steamidlobby != self.steamidlobby:
            return  # Not for us
            
        steamiduserchanged = data.steamiduserchanged
        changetype = data.chatmemberstatechange
        if changetype == EChatMemberStateChange.k_EChatMemberStateChangeEntered:
            self.OnLobbyUserEntered(steamiduserchanged)
        elif changetype in [EChatMemberStateChange.k_EChatMemberStateChangeLeft, EChatMemberStateChange.k_EChatMemberStateChangeLeft]:
            self.OnLobbyUserLeft(steamiduserchanged)
            
    def OnLobbyDataUpdate(self, data):
        steamidlobby = CSteamID(data.steamidlobby)
        steamidmember = CSteamID(data.steamidmember)
        if not data.success or steamidlobby != self.steamidlobby or steamidmember != self.steamidlobby:
            return

        # The lobby owner already has all data, so no need to read it
        if not self.islobbyowner:
            self.ReadData()

    def ReadData(self):
        datamodel = self.datamodel
        if not datamodel:
            return

        self.read_data_changed_keys = datamodel.ReadData()
        self.pending_post_read_data = True

    def PostReadData(self, read_data_changed_keys):
        pass

    def OnThink(self):
        if not self.steamidlobby:
            return
        # Check for dirty data
        datamodel = self.datamodel
        if self.islobbyowner and datamodel:
            self.read_data_changed_keys = datamodel.CommitData()
            if self.read_data_changed_keys:
                # Lobby owner does not read back data from lobbydata update callback, but directly updates the lobby
                self.pending_post_read_data = True

        if self.pending_post_read_data:
            self.pending_post_read_data = False
            self.PostReadData(self.read_data_changed_keys)
            self.read_data_changed_keys = set()

    def BuildSettingsInfo(self, steamidlobby):
        datamodel = self.datamodel
        if not datamodel:
            return None
            
        return {
            'steamid': str(steamidlobby.ConvertToUint64() if steamidlobby else 'offline'),
            'name': datamodel.name,
            'num_members': datamodel.nummembers,
            'lobbytype': datamodel.lobbytype,
        }

    def FilterLobbyFromList(self, steamid):
        """ Filter method for not showing lobbies in lobby list.

            Args:
                steamid (CSteamID): lobby steam id

            Returns:
                bool: False for not filtering the lobby
        """
        return False
        
    def OnLobbyMatchListCallResult(self, lobbymatchlist, iofailure, callbackid):
        if iofailure:
            PrintWarning('OnLobbyMatchListCallResult: io failure\n')
            self.SendCallback(callbackid, [[], True])
            return
            
        matchmaking = steamapicontext.SteamMatchmaking()
        
        lobbies = []
        
        for i in range(0, lobbymatchlist.lobbiesmatching):
            steamid = matchmaking.GetLobbyByIndex(i)
            
            gamedir = matchmaking.GetLobbyData(steamid, 'game:dir')
            if gamedir != self.gamedir:
                continue

            if self.FilterLobbyFromList(steamid):
                continue
                
            olddatamodel = self.datamodel
            self.datamodel = self.CreateLobbyDataModel(steamid)
            self.datamodel.ReadData()  # Only read data into model

            lobbies.append(self.BuildSettingsInfo(steamid))
            
            self.datamodel = olddatamodel
                
        self.SendCallback(callbackid, [lobbies])
