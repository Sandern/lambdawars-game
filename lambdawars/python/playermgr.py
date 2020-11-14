""" This module will store info about the players in the map. """
from srcbase import *
from vmath import *
import srcmgr

from core.dispatch import receiver
from core.signals import FireSignalRobust, prelevelinit, playerchangedcolor, saverestore_save, saverestore_restore
from core.usermessages import usermessage

from collections import defaultdict
import re

from fields import IntegerField, FlagsField, StringField
from entities import entity, Disposition_t, SetPlayerRelationShip, GetPlayerRelationShip, MouseTraceData
if isserver:
    from gameinterface import concommand, FCVAR_CHEAT, CSingleUserRecipientFilter, CReliableBroadcastRecipientFilter
    from entities import CPointEntity
    from utils import UTIL_PlayerByIndex, UTIL_GetCommandClient, UTIL_EntityByIndex
    from core.signals import clientactive
else:
    from entities import C_HL2WarsPlayer


#
# Ownernumber 0 and 1 are reserved for the neutral and enemy side
#
OWNER_NEUTRAL = 0
OWNER_ENEMY = 1
OWNER_LAST = 2


#
# Player info per owner number
#
class PlayerInfo(object):
    def __init__(self, 
                 color = Color(255, 255, 255, 255), 
                 faction = "rebels", 
                 reserved = False):
        super().__init__()
        
        # Defaults
        self.__color = color                # Minimap, selection circles..
        self.faction = faction              # Slam player to this faction at map start
        self.reserved = reserved
        
    def Setup(self, ownernumber):
        self.ownernumber = ownernumber
        
        FireSignalRobust(playerchangedcolor, ownernumber=ownernumber, oldcolor=None)
            
    __color = 0
    def __GetColor(self):
        return self.__color
    def __SetColor(self, color):
        oldcolor = self.__color
        self.__color = color
        
        FireSignalRobust(playerchangedcolor, ownernumber=self.ownernumber, oldcolor=oldcolor)
        
    color = property(__GetColor, __SetColor, None, "Set the color of this player")
     
class PlayerDB(defaultdict):
    def  __setitem__(self, ownernumber, playerinfo):
        super().__setitem__(ownernumber, playerinfo)
        playerinfo.Setup(ownernumber)
        if isserver and srcmgr.levelinit == True:
            SendPlayerInfo(CReliableBroadcastRecipientFilter(), ownernumber)

dbplayers = PlayerDB(PlayerInfo)

# Called by the chat hud element.
def _GetColorForOwnerNumber(ownernumber):
    return dbplayers[ownernumber].color

# Relationship info
#MAX_PLAYERS = 33
class RelationshipInfo(object):
    """ Controls the relationships between players. 
        The relationship lookup table is in the c++ code, for fast lookup in the unit sensing code.
        Relationships are automatically send to the clients. """
    def __init__(self):
        super().__init__()
        
        self.InitDefault()
        
    def InitDefault(self):
        self.changed = defaultdict(lambda : False)
        for i in range(0, MAX_PLAYERS):
            for j in range(0, MAX_PLAYERS):
                if i == j:
                    SetPlayerRelationShip(i, j, Disposition_t.D_LI)
                elif i == OWNER_NEUTRAL or j == OWNER_NEUTRAL:
                    SetPlayerRelationShip(i, j, Disposition_t.D_NU)
                else:
                    SetPlayerRelationShip(i, j, Disposition_t.D_HT)
        
    def  __setitem__(self, key, item):
        if item == GetPlayerRelationShip(key[0], key[1]):
            return # No change, avoid sending unnecessary usermessage
        SetPlayerRelationShip(key[0], key[1], item)
        self.changed[key] = True
        if isserver and srcmgr.levelinit == True:
            ClientSetRelationship(key, int(relationships[key]))
    
    def  __getitem__(self, key):
        return GetPlayerRelationShip(key[0], key[1])
        
    def clear(self):
        self.InitDefault()
        
relationships = RelationshipInfo()

@receiver(prelevelinit)
def LevelInit(sender, **kwargs):
    relationships.clear()
    
# Save/restore of player info and relationships
@receiver(saverestore_save)
def SavePlayerMgrData(fields, *args, **kwargs):
    for i in range(0, MAX_PLAYERS):
        for j in range(0, MAX_PLAYERS):
            key = (i, j)
            
            fields['relationship_%d_%d' % (i, j)] = str(relationships[key])
            
@receiver(saverestore_restore)
def RestorePlayerMgrData(fields, *args, **kwargs):
    relationshipregex = re.compile('relationship_(?P<p1>\d+)_(?P<p2>\d+)')
    
    for name, value in fields.items():
        match = relationshipregex.match(name)
        if match:
            key = (int(match.group('p1')), int(match.group('p2')))
            relationships[key] = getattr(Disposition_t, value, Disposition_t.D_HT)
            continue


#
# Inform client
#
def SendPlayerInfo(filter, ownernumber):
    ClientSetPlayerInfo(
        ownernumber,
        dbplayers[ownernumber].color.r(),
        dbplayers[ownernumber].color.g(),
        dbplayers[ownernumber].color.b(),
        dbplayers[ownernumber].color.a(),
        dbplayers[ownernumber].faction,
        filter=filter,
    )


# Give a full update
if isserver:
    @receiver(clientactive)
    def NewClientActive(sender, client, **kwargs):
        filter = CSingleUserRecipientFilter(client)
        filter.MakeReliable()
        for k, v in dbplayers.items():
            SendPlayerInfo(filter, k)
        for i in range(0, MAX_PLAYERS):
            for j in range(0, MAX_PLAYERS):
                key = (i, j)
                if relationships.changed[key]:
                    ClientSetRelationship(key, int(relationships[key]), filter=filter)


@usermessage(messagename='setpi')
def ClientSetPlayerInfo(id, r, g, b, a, faction, **kwargs):
    dbplayers[id].color = Color(r, g, b, a)
    dbplayers[id].faction = faction


@usermessage(messagename='setr')
def ClientSetRelationship(key, r, **kwargs):
    relationships[key] = Disposition_t(r)


#
# Some helper methods for on the server
#      
if isserver:
    def ListPlayersForOwnerNumber(ownernumber):
        """ Helper method. List players for an owner number """
        players = []
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if player is None:
                continue
            if player.GetOwnerNumber() == ownernumber:
                players.append(player)
        return players

    def FindFirstFreeOwnerNumber():
        """ Find the first free ownernumber without a player. Returns -1 on failure. """
        for owner_number in range(0, MAX_PLAYERS):
            if len(ListPlayersForOwnerNumber(owner_number)) == 0 and not dbplayers[owner_number].reserved:
                return owner_number
        return -1


def ListAlliesOfOwnerNumber(owner):
    ''' List all owners who are allied to the specified owner, including
        the owner self. 
        
        Args:
            owner (int): Owner for which to find allies.
    '''
    owners = set()
    for j in range(0, MAX_PLAYERS):
        key = (owner, j)
        if relationships[key] == Disposition_t.D_LI:
            owners.add(j)
    return owners


#
# Setup two defaults which are always available
# These are a neutral and enemy side
#
if isserver:
    dbplayers[OWNER_NEUTRAL] = PlayerInfo(color=Color(150, 150, 150, 255), reserved=True)
    dbplayers[OWNER_ENEMY] = PlayerInfo(color=Color(255, 0, 0, 255), reserved=True)


#       
# Change player ownernumber
#
if isserver:
    @concommand('change_ownernumber', 'Change my ownernumber', FCVAR_CHEAT)
    def cc_change_ownernumber(args):
        if args.ArgC() < 2:
            print('change_ownernumber: not enough arguments')
            return
        player = UTIL_GetCommandClient()
        owner = int(args[1])
        player.SetOwnerNumber(owner)
    
    @concommand('wars_snap_player_to_entity', 'Snap player camera to entity', FCVAR_CHEAT)
    def cc_snap_player_to_entity(args):
        if args.ArgC() < 2:
            print('wars_snap_player_to_entity: not enough arguments')
            return
        player = UTIL_GetCommandClient()
        entindex = int(args[1])
        entity = UTIL_EntityByIndex(entindex)
        if not entity:
            PrintWarning('wars_snap_player_to_entity: no such entity #%d\n' % (entindex))
            return
        player.SnapCameraTo(entity.GetAbsOrigin())


#
# Some start ents that use the player owner number
#
if isserver:
    @entity('info_player_wars',
            base=['PlayerClass', 'Angles', 'Wars'],
            studio='models/editor/playerstart.mdl')
    class InfoPlayerWars(CPointEntity):
        pass

    @entity('info_start_wars',
            base=['Targetname', 'Parentname', 'Angles', 'Wars'],
            iconsprite='editor/info_start_wars.vmt'
            )
    class InfoStartWars(CPointEntity):
        spawnflags = FlagsField(keyname='spawnflags',
                                flags=[('SF_NO_POPULATE', (1 << 0), False, 'Do not populate startspot')],
                                cppimplemented=True)
        rallypointname = StringField(value='', keyname='rallypointname', displayname='Rallypoint',
                                     helpstring='Optional rally point name, passed to the start building')
        groupname = StringField(value='', keyname='groupname', displayname='Group Hint',
                                helpstring='Hint for gamelobby for automatically assigning positions to players.', 
                                choices=[('', 'None'), ('Team 1', 'Team 1'), ('Team 2', 'Team 2'), ('Team 3', 'Team 3'), ('Team 4', 'Team 4')])


#
# Simulated player
#
class SimulatedPlayer(object):
    """ Simulated player. Wraps the real player and replaces the mouse data """
    def __init__(self, owner_number,
                 mousedata=MouseTraceData(),
                 leftmousepressed=MouseTraceData(),
                 leftmousedoublepressed=MouseTraceData(),
                 leftmousereleased=MouseTraceData(),
                 rightmousepressed=MouseTraceData(),
                 rightmousedoublepressed=MouseTraceData(),
                 rightmousereleased=MouseTraceData(),
                 selection=[],
                 buttons=0):
        super().__init__()
        self.owner_number = owner_number
        self.selection = selection
        self.buttons = buttons
        if isserver:
            players = ListPlayersForOwnerNumber(owner_number)
            self.player = players[0] if players else None
        else:
            self.player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            
        self.mousedata = mousedata
        self.leftmousepressed = leftmousepressed
        self.leftmousedoublepressed = leftmousedoublepressed
        self.leftmousereleased = leftmousereleased
        self.rightmousepressed = rightmousepressed
        self.rightmousedoublepressed = rightmousedoublepressed
        self.rightmousereleased = rightmousereleased
            
    def GetMouseData(self): return self.mousedata
    def GetMouseDataLeftPressed(self): return self.leftmousepressed
    def GetMouseDataLeftDoublePressed(self): return self.leftmousedoublepressed
    def GetMouseDataLeftReleased(self): return self.leftmousereleased
    def GetMouseDataRightPressed(self): return self.rightmousepressed
    def GetMouseDataRightDoublePressed(self): return self.rightmousedoublepressed
    def GetMouseDataRightReleased(self): return self.rightmousereleased
    
    def IsLeftPressed(self): return False
    def IsRightPressed(self): return False
    def ClearMouse(self): pass
    
    def GetSelection(self): return self.selection
    
    def GetOwnerNumber(self): return self.owner_number
    
    def AddActiveAbility(self, ability): pass
    def RemoveActiveAbility(self, ability): pass
    def IsActiveAbility(self, ability): pass
    def ClearActiveAbilities(self): pass
    def SetSingleActiveAbility(self, ability): pass
    def GetSingleActiveAbility(self): pass
    
    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return getattr(self.player, name)
