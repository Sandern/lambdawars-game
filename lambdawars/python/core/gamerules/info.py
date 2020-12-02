from srcbase import *

from fields import StringField, LocalizedStringField, BooleanField
from gamerules import InstallGameRules, GameRules
from core.usermessages import usermessage
from core.dispatch import receiver
from core.signals import preinitgamerules, postlevelinit, saverestore_save, saverestore_restore
if isserver:
    from core.usermessages import CSingleUserRecipientFilter
    from gameinterface import concommand, FCVAR_CHEAT, AutoCompletion, servergamedll
    from utils import UTIL_SayTextAll
    
    from core.signals import clientactive
    
if isclient:
    from vgui import localize
    
import gamemgr
import re
    
prev_gamerules_name = None
cur_gamerules_name = None   
next_gamerules_name = "sandbox"
next_gamedata = None
 
# Gamerules db
dbid = 'gamerules'
dbgamerules = gamemgr.dblist[dbid]

# Gamerules entry
class GamerulesInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = gamemgr.BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        newcls.mapfilter = re.compile(newcls.mappattern)
        newcls.factionfilter = re.compile(newcls.factionpattern)
        
        return newcls

class GamerulesInfo(gamemgr.BaseInfo, metaclass=GamerulesInfoMetaClass):
    id = dbid
    
    #: Reference to the gamerules class
    cls = None
    
    #: Name shown in hud.
    #: In case the name starts with #, it is considered a localized string.
    displayname = LocalizedStringField(value='')
    #: Description shown in hud.
    #: In case the name starts with #, it is considered a localized string.
    description = LocalizedStringField(value='Put some description here')
    
    #: Package + class name of huds that are created when this gamerule becomes active. Only for WarsBaseGameRules derived classes.
    huds = [
        'core.ui.topbar.CefTopBar',
        'core.ui.waitingforplayers.CefWaitingForPlayers',
        'core.ui.postgame.CefPostGamePlayers',
        'core.ui.HudTimer',
    ]
    
    #: Players may join in the middle of an active game.
    allowplayerjoiningame = False

    # REGEX patterns to control options in the gamelobby
    #: REGEX pattern to restrict the map choices
    mappattern = StringField(value='^.*$', noreset=True) # By default allow all maps
    #: REGEX pattern to restrict the faction choices
    factionpattern = StringField(value='^.*$', noreset=True)
    #: If True, allow teams in the gamelobby
    useteams = BooleanField(value=True)
    #: If True, support cpu
    supportcpu = BooleanField(value=True)
    #: If True, support factions
    supportfactions = BooleanField(value=True)
    #: If True, hide start spots in the gamelobby
    hidestartspots = BooleanField(value=False)
    #: Minimum number of players required to start a game with this rules from the gamelobby
    minplayers = 0
    #: Allow all players to be on the same team.
    allowallsameteam = BooleanField(value=True)
    #: Hidden from gamelobby
    hidden = BooleanField(value=False)
    
    @classmethod
    def BuildSettingsErrorVariables(cls):
        """ Returns a dictionary with possible error variable for game mode
            validation error strings. """
        return {
            'name' : cls.displayname,
            'minplayers' : cls.minplayers,
        }
        
    @classmethod
    def ConstructErrorString(cls, unlocalizedMsg):
        """ Helper method to create a localized error msg for game mode settings validation. """
        msg = localize.Find(unlocalizedMsg)
        if not msg:
            return '<Unknown Error>'
        return msg % cls.BuildSettingsErrorVariables()
    
    @classmethod
    def ValidateGameSettings(cls, gamedata):
        """ Validates the game mode settings.
        
            Args:
                gamedata (dict): game settings (map, mode, players, etc)
        
            Returns True, None if succeeded.
            Returns False, errorMsg if not valid. The errorMsg is already localized.
        """
        game = gamedata.get('game', None)
        if not game:
            return False, cls.ConstructErrorString('#Gamerules_InvalidSettings')
            
        # Check if game mode needs at least a minimum number of players
        numplayers = game.get('numplayers', 0)
        if numplayers < cls.minplayers:
            return False, cls.ConstructErrorString('#Gamemode_MinPlayers')
            
        # Check if game mode does not allow all players on the same team
        if not cls.allowallsameteam:
            teams = set()
            allsameteam = True
            
            players = game.get('player', [])
            if type(players) != list:
                players = [players]
            
            for player in players:
                team = player.get('team', TEAM_UNASSIGNED)
                if team == TEAM_UNASSIGNED:
                    allsameteam = False
                    break
                teams.add(team)
                if len(teams) > 1:
                    allsameteam = False
                    break
                
            if allsameteam:
                return False, cls.ConstructErrorString('#Gamemode_AllSameteam')
            
        return True, None

class GameRulesFallBackInfo(GamerulesInfo):
    name = 'gamerules_unknown'
    hidden = True

def GetGamerulesInfo(gamerules_name):
    return dbgamerules.get(gamerules_name, None)         

def _LevelInitInstallGamerules():
    global next_gamerules_name
    gamerulesname = next_gamerules_name if next_gamerules_name else 'sandbox'
    DevMsg(1, 'LevelInitInstallGamerules: %s\n' % (gamerulesname))
    SetGamerules(gamerulesname)
    
    next_gamerules_name = None

@receiver(postlevelinit)
def PostLevelInitGameRules(*args, **kwargs):
    global next_gamedata
    if next_gamedata:
        if hasattr(GameRules(), 'ApplyGameSettings'):
            GameRules().ApplyGameSettings(next_gamedata)
        next_gamedata = None

def SetGamerules(gamerulesname):
    global prev_gamerules_name, cur_gamerules_name, next_gamerules_name
    if gamerulesname is None:
        ClearGamerules()
        return

    info = GetGamerulesInfo(gamerulesname)
    if not info:
        PrintWarning("core.gamerules.info.SetGamerules: No registered gamerule named %s\n" % (gamerulesname))
        return
    
    prev_gamerules_name = cur_gamerules_name
    cur_gamerules_name = gamerulesname
    InstallGameRules(info.cls)
    
    if GameRules() == None:
        ClearGamerules()
        return

def SetNextLevelGamerules(gamerulesname, gamedata=None):
    global next_gamerules_name, next_gamedata
    next_gamerules_name = gamerulesname
    next_gamedata = gamedata
    DevMsg(1, 'SetNextLevelGamerules: %s\n' % (gamerulesname))

@receiver(preinitgamerules)
def PreInitGamerules(sender, gamerules, *args, **kwargs):
    # Bind info object to gamerules to make it easy to retrieve
    info = GetGamerulesInfo(cur_gamerules_name)
    if info:
        gamerules.info = info
    
    if isserver and not servergamedll.IsRestoring():
        # Inform clients about the change
        ClientSetGamerules(cur_gamerules_name)

def ClearGamerules():    
    InstallGameRules(None)
    #GameRules().info = GameRulesFallBackInfo
    cur_gamerules_name = None        
    
    if isserver:
        # Inform clients about the change
        ClientClearGamerules()

# Save/restore of gamerules
@receiver(saverestore_save)
def SaveGamerules(fields, *args, **kwargs):
    fields['gamerules_name'] = cur_gamerules_name

@receiver(saverestore_restore)
def RestoreGamerules(fields, *args, **kwargs):
    global next_gamerules_name
    gamerules_name = fields.get('gamerules_name', None)
    if not gamerules_name:
        return
    SetGamerules(gamerules_name)
    
#
# Set gamerules
#
if isserver:
    @concommand('wars_setgamerules', 'Set the gamerules', FCVAR_CHEAT, completionfunc=AutoCompletion(lambda: dbgamerules.keys()))
    def cc_wars_setgamerules(args):
        SetGamerules(args[1])
        UTIL_SayTextAll('Gamerules changed to %s' % (args[1]))
    
    @concommand('wars_cleargamerules', 'Clear the gamerules', FCVAR_CHEAT)
    def cc_wars_cleargamerules(args):
        ClearGamerules()
        
# Give a full update
if isserver:
    @receiver(clientactive)
    def NewClientActive(sender, client, **kwargs):
        if cur_gamerules_name != None:
            filter = CSingleUserRecipientFilter(client)
            filter.MakeReliable()
            ClientSetGamerules(cur_gamerules_name, filter=filter)

@usermessage()
def ClientSetGamerules(gamerulesname, **kwargs):
    SetGamerules(gamerulesname)

@usermessage()
def ClientClearGamerules(**kwargs):
    ClearGamerules()
