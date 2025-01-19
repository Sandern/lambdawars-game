from .lobby import WebLobby
from .gamelobby import WebGameLobby
from .settings import WebVideoSettings
from .savedgames import WebSavedGames
try:
    from .workshop import WebWorkshop
except ImportError:
    DevMsg(1, 'Update steam api')
    WebWorkshop = None

from srcbase import KeyValues
from cef import WebView, jsbind, NT_ONLYFILEPROT
from vgui import surface, localize
from gameui import GameUICommand, GameUIOpenWindow, WINDOW_TYPE, OpenGammaDialog
from gameinterface import engine, concommand, Plat_FloatTime, ConVar, FCVAR_HIDDEN
from steam import (steamapicontext, NumberOfCurrentPlayersCallResult, PersonaStateChangeCallback,
                    EPersonaChange, GameLobbyJoinRequestedCallback)
from entities import PlayerResource
from playermgr import MAX_PLAYERS
from core.signals import (steam_serversdisconnected, steam_serverconnectfailure, steam_serversconnected, 
                            mm_error, gameui_inputlanguage_changed)
import matchmaking
import filesystem
from kvdict import LoadFileIntoDictionaries
import gameui
#from srcbuiltins import KeyValuesDumpAsDevMsg

import srcmgr
import settings

import os
import weakref
import pprint

# Reference to main menu for game code
mainmenuref = None

connect_lobby = ConVar("connect_lobby", "", FCVAR_HIDDEN, "Sets the lobby ID to connect to on start.")


class MainMenuNumberOfCurrentPlayersCallResult(NumberOfCurrentPlayersCallResult):
    def OnNumberOfCurrentPlayers(self, data, iofailure):
        self.webview.SendCallback(self.callbackid, [data.players if (data.success and not iofailure) else None])


class MainMenuNumberOfCurrentPlayersBroadcastCallResult(NumberOfCurrentPlayersCallResult):
    def OnNumberOfCurrentPlayers(self, data, iofailure):
        # Num players from Steam updates at a lower rate, so use the chat lobby as indication if it has a higher
        # number of players
        numcurplayers = max(1, data.players if data.success and not iofailure else 1,
                            self.webview.chatlobby.numlobbymembers)
        self.webview.AngularJsBroadcast('menu:numcurrentplayers', [numcurplayers])


class MainMenuPersonaStateChangeCallback(PersonaStateChangeCallback):
    def OnPersonaStateChange(self, data):
        steamuser = steamapicontext.SteamUser()
        steamfriends = steamapicontext.SteamFriends()
        if steamuser.GetSteamID() != data.steamid:
            return
        
        if data.changeflags & EPersonaChange.k_EPersonaChangeName:
            self.AngularJsBroadcast('user:name', [steamfriends.GetFriendPersonaName(data.steamid)])
        if data.changeflags & EPersonaChange.k_EPersonaChangeAvatar:
            self.AngularJsBroadcast('user:steamid', [str(data.steamid)])


class WebChatLobby(WebLobby):
    defaultobjectname = 'globalchat'


class CefMainMenu(WebView, MainMenuPersonaStateChangeCallback, GameLobbyJoinRequestedCallback):
    angularjs_rootscope = None
    levelloading = False
    
    rooturl = None

    gameui_obj_name = 'interface'
    
    def __init__(self, parent):
        global mainmenuref

        self.rooturl = 'local://localhost/ui/menu_next/dist/'
        
        wide, tall = surface().GetScreenSize()
        WebView.__init__(self, "Main Menu", self.rooturl, renderframerate=30, wide=wide,
                         tall=tall, navigationbehavior=NT_ONLYFILEPROT)
        
        MainMenuPersonaStateChangeCallback.__init__(self)
        GameLobbyJoinRequestedCallback.__init__(self)
        
        mainmenuref = weakref.ref(self)
        #self.GetPanel().SetParent(parent)

        # Create components
        self.chatlobby = WebChatLobby(self)
        self.gamelobby = WebGameLobby(self)
        
        self.components.append(self.chatlobby)
        self.components.append(self.gamelobby)
        self.components.append(WebVideoSettings(self))
        self.components.append(WebSavedGames(self))
        if WebWorkshop:
            self.components.append(WebWorkshop(self))
        
        steam_serversconnected.connect(self.OnSteamServersConnected)
        steam_serversdisconnected.connect(self.OnSteamServersDisconnected)
        steam_serverconnectfailure.connect(self.OnSteamServerConnectFailure)
        
        mm_error.connect(self.OnMMError)
        
        gameui_inputlanguage_changed.connect(self.OnInputLanguageChanged)
        
    def OnDestroy(self):
        super().OnDestroy()
        
        steam_serversconnected.disconnect(self.OnSteamServersConnected)
        steam_serversdisconnected.disconnect(self.OnSteamServersDisconnected)
        steam_serverconnectfailure.disconnect(self.OnSteamServerConnectFailure)
        
        mm_error.disconnect(self.OnMMError)
        
        gameui_inputlanguage_changed.disconnect(self.OnInputLanguageChanged)
        
    def OnAfterCreated(self):
        super().OnAfterCreated()
        
        self.SetMouseInputEnabled(True)

    def OnLoadError(self, frame, errorcode, errortext, failedurl):
        PrintWarning('CefMainMenu: Failed to load %s!\n\t%s:%s\n' % (failedurl, errorcode, errortext))

    def OnLoadEnd(self, frame, httpStatusCode):
        if frame != self.GetMainFrame():
            return
    
        super().OnLoadEnd(frame, httpStatusCode)
        
        self.SetVisible(True)
        self.SetMouseInputEnabled(True)
        self.SetGameInputEnabled(True)
        self.SetUseMouseCapture(False)
        self.Focus()
        
        steamfriends = steamapicontext.SteamFriends()
        if steamfriends:
            steamfriends.SetRichPresence("status", "In Main menu")

        self.curversion = self.GetVersion()

        self.angular = self.ExecuteJavaScriptWithResult("angular", '')
        self.document = self.ExecuteJavaScriptWithResult("document", '')

        self.angularjs_rootscope = self.ExecuteJavaScriptWithResult(
            "angular.element(document.body).injector().get('$rootScope')", '')

        steamapps = steamapicontext.SteamApps()
        steamuser = steamapicontext.SteamUser()
        steamfriends = steamapicontext.SteamFriends()
        steamid = steamuser.GetSteamID() if steamuser else '12345678'

        if not steamuser:
            self.AngularJsBroadcast('steam:not_available', [])

        self.AngularJsBroadcast('user:name', [steamfriends.GetFriendPersonaName(steamid) if steamfriends else '<Unknown>'])
        self.AngularJsBroadcast('user:steamid', [str(steamid)])
        
        self.OnInputLanguageChanged()  # Show correct input language in chat boxes
        
        if steamapps:
            try:
                success, beta = steamapps.GetCurrentBetaName() if not srcmgr.DEVVERSION else (True, 'dev')
            except UnicodeDecodeError:
                success, beta = (True, '')
                
            if success:
                self.AngularJsBroadcast('menu:beta', [beta, srcmgr.DEVVERSION if srcmgr.DEVVERSION else ''])
        
        # if we were launched with "+connect_lobby <lobbyid>" on the command line, join that lobby immediately
        # else try if we still had an active lobby, but exited the game without leaving it (e.g. crash or something else)
        connectlobbyid = connect_lobby.GetString()
        if connectlobbyid:
            self.gamelobby.joinlobby([connectlobbyid])
            self.CallServiceMethod('gamelobbymanager', 'setStateWithApply', ['joining'])
        else:
            self.gamelobby.StartTestActiveLobby()
    
    def InitializeObjects(self):
        super().InitializeObjects()
        
        # Create global interface object
        self.interfaceobj = self.CreateGlobalObject("gameui")
        
    def OnInitializedBindings(self):
        super().OnInitializedBindings()

        ui_settings = {
            'LAMBDAWARS_API_URL': settings.LAMBDAWARS_API_URL,
        }
        
        self.Invoke(None, 'init_mainmenu', [self.GetGameUITranslations(), ui_settings])
        
    def OnSteamServersConnected(self, *args, **kwargs):
        print('OnSteamServersConnected')

    def OnSteamServersDisconnected(self, *args, **kwargs):
        print('OnSteamServersDisconnected')

    def OnSteamServerConnectFailure(self, *args, **kwargs):
        print('OnSteamServerConnectFailure')
        
    def PerformLayout(self):
        screenwide, screentall = surface().GetScreenSize()
        self.SetSize(screenwide, screentall)

    def CalcPlayerCount(self):
        """ Purpose: Returns the # of teammates of the local player. """
        count = 0
        if PlayerResource():
            for playerindex in range(1, MAX_PLAYERS+1):
                # find all players who are on the local player's team
                if PlayerResource().IsConnected(playerindex):
                    count += 1
        return count

    __nextupdatenumcurplayers = 0
    __nextupdateingameinfo = 0

    numplayers = 0

    def OnThink(self):
        self.chatlobby.OnThink()
        self.gamelobby.OnThink()

        if not self.IsFullyVisible():
            return

        if engine.IsClientLocalToActiveServer() and self.__nextupdateingameinfo < Plat_FloatTime():
            self.__nextupdateingameinfo = Plat_FloatTime() + 1.0

            numplayers = self.CalcPlayerCount()
            if self.numplayers != numplayers:
                self.numplayers = numplayers
                self.AngularJsBroadcast('menu:host_numplayers', [numplayers])
            
        if self.__nextupdatenumcurplayers < Plat_FloatTime():
            self.__nextupdatenumcurplayers = Plat_FloatTime() + 5.0
            
            steamuserstats = steamapicontext.SteamUserStats()
            self.currentplayersresult = MainMenuNumberOfCurrentPlayersBroadcastCallResult(
                steamuserstats.GetNumberOfCurrentPlayers() if steamuserstats else 1
            )
            self.currentplayersresult.webview = self
        
    # Common
    def GoToPage(self, page):
        self.LoadURL('%s#%s' % (self.rooturl, page))
        
    def GoToGameLobby(self):
        self.GoToPage('Gamelobby')
        
    # Angularjs functions
    def CallServiceMethod(self, servicename, methodname, args):
        """ Calls a function on an AngularJS service with the provided arguments. """
        injector = self.InvokeWithResult(self.InvokeWithResult(self.angular, 'element', [self.ObjectGetAttr(self.document, 'body')]), 'injector', [])
        service = self.InvokeWithResult(injector, 'get', [servicename])
        return self.InvokeWithResult(service, methodname, args)
        
    def AngularJsBroadcast(self, broadcastname, args):
        if self.angularjs_rootscope:
            self.Invoke(self.angularjs_rootscope, '$broadcast', [broadcastname] + args)
            self.Invoke(self.angularjs_rootscope, '$apply', [])

    def ShowGenericDialog(self, msg_translation_key):
        self.AngularJsBroadcast('show_generic_dialog', [msg_translation_key])
            
    def GetVersion(self):
        revision = srcmgr.get_svn_revision()
        if revision != 'SVN-unknown':
            srcmgr.DEVVERSION = revision
                
        if srcmgr.DEVVERSION:
            return srcmgr.DEVVERSION
            
        if filesystem.FileExists('gamerevision'):
            return 'BUILD-%s' % (filesystem.ReadFile('gamerevision', None).decode('utf-8'))
            
        return '%d.%d.%d' % (srcmgr.VERSION[0], srcmgr.VERSION[1], srcmgr.VERSION[2])
        
    def GetMissions(self):
        """ Builds the list of single player missions. """
        missionresourcedefault = {
            'name': 'Unknown map',
            'description': 'No description',
        }
    
        missions = []
        for filename in filesystem.ListDir(path="maps/", wildcard="*.bsp"):
            root, ext = os.path.splitext(filename)
            if root.startswith('sp_') and ext == '.bsp':
                mission_info = dict(missionresourcedefault)
                path = os.path.join('maps', '%s.res' % root)
                mission_info.update(LoadFileIntoDictionaries(path, default={}))
                mission_info['mapname'] = root

                if mission_info['description'] and mission_info['description'][0] == '#':
                    localized_value = localize.Find(mission_info['description'])
                    if localized_value is not None:
                        mission_info['description'] = localized_value

                # Correct image path
                if 'image' in mission_info:
                    mission_info['image'] = 'images/%s' % mission_info['image']
                
                missions.append(mission_info)
        return missions
        
    # GameUI Events
    def OnGameUIActivated(self):
        """ Called when the game ui is going to be shown, for example when starting the
            game or when pressing escape to go to the ingame main menu. """
        #print('Game UI is actived')
        
        if engine.IsConnected() or self.levelloading:
            # Switch to ingame main menu view
            # Second argument indicates the player is hosting the server
            # Third argument means the game is played offline
            self.AngularJsBroadcast('user:ingame', [True, engine.IsClientLocalToActiveServer(), gpGlobals.maxClients == 1])
        else:
            # Make sure the regular main menu view is shown
            self.AngularJsBroadcast('user:ingame', [False, False, False])
      
    def OnGameUIHidden(self):
        """ Called when the gameui is being hidden. """
        #print('Game UI is hidden')
        
    def OnLevelLoadingStarted(self, levelname, showprogressdialog):
        """ Called when a level starts loading.
        
            Args:
                levelname (str): name of level
                showprogressdialog (bool): show the progress dialog?
        """
        self.levelloading = True
        
    def OnLevelLoadingFinished(self, error, failurereason, extendedreason):
        """ Called when a level finished loading (either success or canceled).
            
            Args:
                error (bool): True if loading failed.
                failurereason (str): message containing reason.
                extendedreason (str): Extended reason
        """
        self.levelloading = False
        
    # Steam callbacks
    __pendinggamelobbyjoinid = None

    def OnGameLobbyJoinRequested(self, data):
        targetsteamidlobby = str(data.steamidlobby)
        print('Request to join steam lobby %s' % (targetsteamidlobby))
        #self.gamelobby.joinlobby([str(targetsteamidlobby)])
        self.__pendinggamelobbyjoinid = targetsteamidlobby
        
    def OnMMError(self, event, *args, **kwargs):
        """ Big hack around inviting ingame. Can't disable Alien Swarm's matchmaking invite, so the session
            join will fail. After that we should be able to join the lobby properly. 
            
            Due this there is a big delay in joining though...
        """
        #print('mm error: ', event)
        #KeyValuesDumpAsDevMsg(event)
        
        if self.__pendinggamelobbyjoinid:
            print('OnMMJoinSessionFailed, but has pending lobby join id %s' % (self.__pendinggamelobbyjoinid))
            self.CallServiceMethod('gamelobbymanager', 'setStateWithApply', ['joining'])
            self.gamelobby.joinlobby([self.__pendinggamelobbyjoinid])
            self.__pendinggamelobbyjoinid = None
            return
            
        error = event.GetString('error', '')
        if error == 'n/a':
            self.gamelobby.OnNAError()
        
    def OnInputLanguageChanged(self, *args, **kwargs):
        self.AngularJsBroadcast('user:inputlanguage', [gameui.GetCurrentKeyboardLangId()])
        
    # Javascript methods
    @jsbind('gameui')
    def clientcommand(self, methodargs):
        #print('Received client command %s' % (methodargs[0]))
        engine.ClientCommand(methodargs[0])
        
    @jsbind('gameui')
    def servercommand(self, methodargs):
        #print('Received server command %s' % (methodargs[0]))
        engine.ServerCommand(methodargs[0])
        
    @jsbind('gameui', hascallback=True)
    def getUserSteamID(self, methodargs):
        steamuser = steamapicontext.SteamUser()
        if not steamuser:
            return ['<no steam id>']
        return [str(steamapicontext.SteamUser().GetSteamID().ConvertToUint64())]
    
    @jsbind('gameui')
    def openurl(self, methodargs):
        if len(methodargs) > 0:
            url = methodargs[0]
            steamfriends = steamapicontext.SteamFriends()
            if steamfriends:
                steamapicontext.SteamFriends().ActivateGameOverlayToWebPage(url)
                
    @jsbind('gameui', hascallback=True)
    def gettranslations(self, methodargs):
        return self.GetGameUITranslations()
            
    @jsbind('gameui', hascallback=True)
    def retrieveversion(self, methodargs):
        return [self.curversion]
        
    @jsbind('gameui', hascallback=True)
    def retrievemissions(self, methodargs):
        return [self.GetMissions()]
        
    #@jsbind('gameui')
    #def clientcommand(self, methodargs):
    #    engine.ClientCommand('%s' % (methodargs[0]))
        
    @jsbind('gameui')
    def launchmission(self, methodargs):
        sessiondata = KeyValues("Session")

        sessiondata.SetString('system/network', 'offline')
        #sessiondata.SetString('system/access', 'public')

        sessiondata.SetString('game/mode', 'mission')
        sessiondata.SetString('game/mission', methodargs[0])
        sessiondata.SetString('game/difficulty',methodargs[1]);

        matchmaking.CreateSession(sessiondata)
        matchmaking.matchsession.Command(KeyValues("Start"))
        
    @jsbind('gameui')
    def launchbonus(self, methodargs):
        sessiondata = KeyValues("Session")

        sessiondata.SetString('system/network', 'offline')

        sessiondata.SetString('game/mode', 'swarmkeeper')
        sessiondata.SetString('game/mission', 'random_100_100')

        matchmaking.CreateSession(sessiondata)
        matchmaking.matchsession.Command(KeyValues("Start"))
        
    @jsbind('gameui')
    def gameuicommand(self, methodargs):
        GameUICommand(methodargs[0])
        
    # Statistics
    currentplayersresult = None

    @jsbind('gameui', hascallback=True, manuallycallback=True)
    def getNumberOfPlayers(self, methodargs, callbackid):
        steamuserstats = steamapicontext.SteamUserStats()
        self.currentplayersresult = MainMenuNumberOfCurrentPlayersCallResult(
            steamuserstats.GetNumberOfCurrentPlayers() if steamuserstats else 0
        )
        self.currentplayersresult.callbackid = callbackid
        self.currentplayersresult.webview = self
        
    # Matchmaking
    @jsbind('gameui')
    def creategamelobby(self, methodargs):
        sessiondata = KeyValues("Session")

        sessiondata.SetString('system/network', 'LIVE')
        sessiondata.SetString('system/access', 'public')

        sessiondata.SetString('game/mode', 'gamelobbyrules')
        sessiondata.SetString('game/mission', 'gamelobby')

        matchmaking.CreateSession(sessiondata)
        
    @jsbind('gameui')
    def findfriendgames(self, methodargs):
        settings = KeyValues.FromString(
            "settings",
            " game { " + \
                " mode = " + \
            " } " 
        )

        settings.SetString( "game/mode", "" );

        GameUIOpenWindow(WINDOW_TYPE.WT_ALLGAMESEARCHRESULTS, True, settings );
        
    @jsbind('gameui')
    def findpublicgame(self, methodargs):
        settings = KeyValues.FromString(
            "settings",
            " system { " + \
                " network LIVE " + \
            " } " + \
            " game { " + \
                " mode = " + \
            " } " + \
            " options { " + \
                " action custommatch " + \
            " } "
        )

        settings.SetString("game/mode", '')

        GameUIOpenWindow(
            WINDOW_TYPE.WT_FOUNDPUBLICGAMES, #ui_play_online_browser.GetBool() ? WT_FOUNDPUBLICGAMES : WT_GAMESETTINGS,
           True, settings );
        
    @jsbind('gameui')
    def createsoloplay(self, methodargs):
        settings = KeyValues.FromString(
        "settings",
        " system { " + \
        " network offline " + \
        " } " + \
        " game { " + \
        " mode sdk " + \
        " mission gamelobby " + \
        " } "
        )

        settings.SetString("Game/difficulty", '')

        matchmaking.CreateSession(settings)

        # Automatically start the credits session, no configuration required
        matchmaking.matchsession.Command(KeyValues("Start"))
            
    @jsbind('gameui')
    def creategametutorial(self, methodargs):
        settings = KeyValues.FromString(
        "settings",
        " system { " + \
        " network offline " + \
        " } " + \
        " game { " + \
        " mode mission " + \
        " mission " + methodargs[0] + " " + \
        " } "
        )

        settings.SetString("Game/difficulty", '')

        # Create Session and DIRECTLY start the game
        matchmaking.CreateSession(settings)
        matchmaking.matchsession.Command(KeyValues("Start"))
        
    # Options
    @jsbind('gameui')
    def openvideo(self, methodargs):
        GameUIOpenWindow(WINDOW_TYPE.WT_VIDEO)
        
    @jsbind('gameui')
    def openbrightness(self, methodargs):
        OpenGammaDialog(self.GetVPanel())
        
    @jsbind('gameui')
    def openaudio(self, methodargs):
        GameUIOpenWindow(WINDOW_TYPE.WT_AUDIO)
        
    @jsbind('gameui')
    def openkeyboardmouse(self, methodargs):
        GameUIOpenWindow(WINDOW_TYPE.WT_KEYBOARDMOUSE)
        
    @jsbind('gameui')
    def openmultiplayersettings(self, methodargs):
        GameUIOpenWindow(WINDOW_TYPE.WT_MULTIPLAYER)

@concommand('mainmenu_reload')
def ReloadMainMenu(args):
    ref = mainmenuref()
    if not ref:
        PrintWarning('No active main menu!\n')
        return
    
    ref.Reload()
    ref.LoadURL(ref.rooturl)

@concommand('mainmenu_showdevtools')
def ShowDevToolsMainMenu(args):
    mainmenuref().ShowDevTools()

@concommand('mainmenu_url')
def PrintMainMenuURL(args):
    print(mainmenuref().GetURL())

@concommand('mainmenu_kickmsg_test')
def MainMenuKickDialogTest(args):
    ref = mainmenuref()
    if not ref:
        PrintWarning('No active main menu!\n')
        return
    
    ref.AngularJsBroadcast('user:kicked', [])

@concommand('mainmenu_print_gl_state')
def PrintMainMenuURL(args):
    lobby = mainmenuref().gamelobby
    settings = lobby.BuildSettingsInfo(lobby.steamidlobby)
    del settings['availablemaps']  # Prints too much
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(settings)

@concommand('mainmenu_gamelobby_show_scores')
def GamelobbyShowScores(args):
    ref = mainmenuref()
    if not ref:
        PrintWarning('No active main menu!\n')
        return
    ref.gamelobby.webview.AngularJsBroadcast('gamelobby:show_scores', [])