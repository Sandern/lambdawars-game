from srcbase import *
from vmath import Vector
import traceback
import re

from fields import StringField, LocalizedStringField, ListField
from gameinterface import ConVar, concommand, AutoCompletion, FCVAR_CHEAT
from core.dispatch import receiver
from core.signals import playerchangedfaction
from core.usermessages import usermessage
from entities import CBaseEntity
from particles import PrecacheParticleSystem
from playermgr import dbplayers
if isclient:
    from entities import C_HL2WarsPlayer
    from vgui import CHudElementHelper
    from materials import SetUITeamColor
    from particles import CNewParticleEffect
else:
    from utils import UTIL_PlayerByIndex, UTIL_GetCommandClient

import gamemgr

# Factions db
dbid = 'factions'
dbfactions = gamemgr.dblist[dbid]

# Global ref to hud
faction_hud_helper = None # VGUI version
faction_hud_cef = None # CEF version

# Factions info entry
class FactionInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = gamemgr.BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        newcls.gamerulesfilter = re.compile(newcls.gamerulespattern)
        
        return newcls
        
class FactionInfo(gamemgr.BaseInfo, metaclass=FactionInfoMetaClass):
    id = dbid
    #: Display name in gamelobby and other places.
    displayname = LocalizedStringField(value='')
    #: Faction hud.
    hud_name = StringField(value='hud_invalid')
    faction_hud_cvar = None
    #: Initial starting building.
    startbuilding = StringField(value='')
    #: Initial starting unit.
    startunit = StringField(value='')
    #: List of resources to be displayed in the hud.
    resources = ListField(value=[])
    #: REGEX pattern to restrict this faction to certain game modes. Defaults to all.
    gamerulespattern = StringField(value='^.*$', noreset=True)
    #: Screen space particle effect displayed at victory
    victoryparticleffect = StringField(value='')
    #: Screen space particle effect displayed at defeat 
    defeatparticleffect = StringField(value='')
    #: Music played when victorious
    victory_music = StringField(value='')
    #: Music played when defeated
    defeat_music = StringField(value='')

    #: Faction color, used for coloring the hud among others.
    color = Vector(1.0, 1.0, 1.0) 
    
    announcer_cp_captured = StringField(value='', helpstring='Sound script played when control point is captured')
    announcer_cp_lost = StringField(value='', helpstring='Sound script played when control point is lost')
    announcer_cp_under_attack = StringField(value='', helpstring='Sound script played when control point is under attack')
    announcer_unit_completed = StringField(value='', helpstring='Sound script played when a unit is produced')
    announcer_research_completed = StringField(value='', helpstring='Sound script played when research is completed')
    announcer_not_enough_resources = StringField(value='', helpstring='Sound script played when there is not enough resources for an ability')
    announcer_more_population_required = StringField(value='', helpstring='Sound script played more population is needed')

    @classmethod
    def Precache(info):
        # TODO: Should be precached from here
        #if isserver:
        #    from core.units import PrecacheUnit
        #    if info.startbuilding:
        #        PrecacheUnit(info.startbuilding)
    
        if info.announcer_cp_captured:
            CBaseEntity.PrecacheSound(info.announcer_cp_captured)
        if info.announcer_cp_lost:
            CBaseEntity.PrecacheSound(info.announcer_cp_lost)
        if info.announcer_cp_under_attack:
            CBaseEntity.PrecacheSound(info.announcer_cp_under_attack)
        if info.announcer_unit_completed:
            CBaseEntity.PrecacheSound(info.announcer_unit_completed)
        if info.announcer_research_completed:
            CBaseEntity.PrecacheSound(info.announcer_research_completed)
        if info.announcer_not_enough_resources:
            CBaseEntity.PrecacheSound(info.announcer_not_enough_resources)
        if info.announcer_more_population_required:
            CBaseEntity.PrecacheSound(info.announcer_more_population_required)

        if info.victoryparticleffect: 
            PrecacheParticleSystem(info.victoryparticleffect)
        if info.defeatparticleffect: 
            PrecacheParticleSystem(info.defeatparticleffect)
        
    @classmethod
    def PopulateStartSpot(info, gamerules, startspot, ownernumber, playerSteamID=None):
        if not info.startbuilding or not info.startunit:
            PrintWarning('Faction %s has no start building or unit specified! Unable to populate start spot.\n')
            return
            
        from core.units import CreateUnit, CreateUnitFancy
        # Spawn start building
        if info.startbuilding:
            CreateUnit(info.startbuilding, startspot.GetAbsOrigin(), startspot.GetAbsAngles(),
                        ownernumber, keyvalues={'rallypointname' : startspot.rallypointname})
        
        # Spawn a start unit (todo: offset?)
        if info.startunit:
            unitspawnspot = startspot.GetAbsOrigin()+Vector(270, 0, 48)
            CreateUnitFancy(info.startunit, unitspawnspot, owner_number=ownernumber, angles=startspot.GetAbsAngles())
        
    @classmethod           
    def OnLoaded(info):        
        name = info.name 
        if isclient:
            # Dynamically create a convar for the hud named like: factionname_hud
            dbfactions[name].faction_hud_cvar = ConVar(dbfactions[name].name+"_hud", dbfactions[name].hud_name, 
                0, "Faction hud", HudConvarChanged)
            
            # If the local player's faction is this hud, initialize it
            player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            if player and player.GetFaction() == name:
                CreateHud(name)
        
    @classmethod       
    def OnUnLoaded(info):
        name = info.name 
        if isclient:
            dbfactions[name].faction_hud_cvar = None
            DestroyHud()
        
def GetFactionInfo(faction_name):
    return dbfactions.get(faction_name, None)

def HudConvarChanged(var, old_value, f_old_value):
    # Retrieve the faction name
    name = var.GetName().rstrip('_hud')
    hud_name = var.GetString()

    # Make sure the old hud is destroyed
    DestroyHud()
    
    # Save the new name. Change hud helper if this faction is the players local faction
    dbfactions[name].hud_name = hud_name
    player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
    if player and player.GetFaction() == name:
        CreateHud(name)
        
# Hud create/destroy methods
def CreateHud(name):
    global faction_hud_helper, faction_hud_cef
    DestroyHud()
    
    # Get hud info
    try:
        from core.hud.info import dbhuds # TODO: FIXME, can't import at top since factions is imported before the hud
        info = dbhuds[dbfactions[name].hud_name]
    except KeyError:
        if name not in dbfactions:
            PrintWarning("Faction " + name + " missing\n")
        else:
            PrintWarning("Default hud " + dbfactions[name].hud_name + " missing. Aborting create hud faction " + name + "\n")
        return 

    try:
        # Create vgui hud if any
        if info.cls:
            faction_hud = info.cls()
            faction_hud_helper = CHudElementHelper(faction_hud)  
    except:
        traceback.print_exc()

    if type(info.cefcls) == list:
            for cefcls in info.cefcls:
                try:
                    # Create webview hud if any
                    if cefcls:
                        faction_hud_cef.append(cefcls())
                except:
                    traceback.print_exc()
    else:
        try:
            # Create webview hud if any
            if info.cefcls:
                faction_hud_cef.append(info.cefcls())
        except:
            traceback.print_exc()
        
def DestroyHud():
    global faction_hud_helper, faction_hud_cef
    
    try:
        if faction_hud_helper:
            hud = faction_hud_helper.Get()
            if hud:
                hud.SetVisible(False)
                hud.DeletePanel()
            faction_hud_helper = None
    except:
        traceback.print_exc()
        
    
    if faction_hud_cef != None:
        for hud in faction_hud_cef:
            try:
                if hud:
                    hud.visible = False
                    hud.Remove()
                    hud = None
            except:
                traceback.print_exc()
        
    faction_hud_cef = []
        
# Set of sounds for which we warning they were missing
warnedmissingsound = set()
        
# Play a sound
@usermessage(messagename='playfactionsound')
def PlayFactionSound(factionsoundname, **kwargs):
    player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
    if not player or not player.GetFaction():
        return
    info = GetFactionInfo(player.GetFaction())
    try:
        soundname = getattr(info, factionsoundname)
    except AttributeError:
        key = (factionsoundname, player.GetFaction())
        if key not in warnedmissingsound:
            PrintWarning('PlayFactionSound: missing sound %s for faction %s\n' % (factionsoundname, player.GetFaction()))
            warnedmissingsound.add(key)
        return
    
    if not soundname:
        return
    player.EmitAmbientSound(-1, player.GetAbsOrigin(), soundname)
    
# Called when player changed his faction
@receiver(playerchangedfaction)
def PlayerChangedFaction(player, oldfaction, **kwargs):
    if not player:
        return
    faction_name = player.GetFaction()
    
    info = dbfactions.get(faction_name, None)
    if not info:
        PrintWarning("Faction change failed. Invalid faction '" + faction_name+"'\n")
        return 
        
    info.Precache()
    
    # For the local player: set the correct hud and coloring
    if isclient and player == C_HL2WarsPlayer.GetLocalHL2WarsPlayer():
        SetUITeamColor(info.color)
        CreateHud(faction_name)
    
# Command to change the players faction
if isserver:
    @concommand('wars_changefaction', 'Change faction \n\tArguments: { faction name }', 
                FCVAR_CHEAT, completionfunc=AutoCompletion(lambda: list(dbfactions.keys())))
    def cc_wars_changefaction(args):
        player = UTIL_GetCommandClient()
        factionname = args[1]
        if not factionname:
            PrintWarning('wars_changefaction: must specify faction name\n')
            return
        player.ChangeFaction(factionname)
        owner = player.GetOwnerNumber()
        playerinfo = dbplayers[owner]
        playerinfo.faction = factionname
        dbplayers[owner] = playerinfo
else:
    @concommand('wars_faction_override_color', 'Overrides UI global color, for testing', FCVAR_CHEAT)
    def cc_wars_faction_override_color(args):
        SetUITeamColor(Vector(float(args[1]), float(args[2]), float(args[3])))
        
    testvictdefeffect = None

    def UpdateTestVicDefEffect(neweffect=None):
        global testvictdefeffect
        if testvictdefeffect:
            testvictdefeffect.StopEmission(False, True)
            testvictdefeffect = None
            
        if neweffect:
            player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            testvictdefeffect = CNewParticleEffect.Create(player, neweffect)
            testvictdefeffect.SetControlPoint(1, Vector(0, 0, 0))
    
    @concommand('wars_faction_test_victoryeffect', 'Displays local player victory particle effect', FCVAR_CHEAT)
    def cc_wars_faction_test_victoryeffect(args):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or not player.GetFaction():
            return
        info = GetFactionInfo(player.GetFaction())
        UpdateTestVicDefEffect(info.victoryparticleffect)
            
    @concommand('wars_faction_test_victoryeffect_stop', 'Stops local player victory particle effect', FCVAR_CHEAT)
    def cc_wars_faction_test_victoryeffect_stop(args):
        UpdateTestVicDefEffect(None)
        
    @concommand('wars_faction_test_defeateffect', 'Displays local player defeat particle effect', FCVAR_CHEAT)
    def cc_wars_faction_test_defeateffect(args):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player or not player.GetFaction():
            return
        info = GetFactionInfo(player.GetFaction())
        UpdateTestVicDefEffect(info.defeatparticleffect)
            
    @concommand('wars_faction_test_defeateffect_stop', 'Stops local player defeat particle effect', FCVAR_CHEAT)
    def cc_wars_faction_test_defeateffect_stop(args):
        UpdateTestVicDefEffect(None)
        
# When this module is reloaded we must call _changefaction for each player to reinitialize
if isclient:
    player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
    # Not ingame or initialized yet
    if player != None and player.GetFaction() != None:
        PlayerChangedFaction(player, '')
else:
    for i in range(1, gpGlobals.maxClients+1):
        player = UTIL_PlayerByIndex(i)
        if player == None:
            continue
        if player.GetFaction() != None:
            PlayerChangedFaction(player, '')
