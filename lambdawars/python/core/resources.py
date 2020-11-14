""" Resource management WARS game """
from collections import defaultdict
import copy
from math import floor
import re

from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from core.dispatch import receiver
from core.signals import (prelevelinit, postlevelshutdown, playerchangedownernumber, saverestore_save,
                          saverestore_restore, FireSignalRobust)
from core.usermessages import usermessage
from utils import UTIL_ListPlayersForOwners, UTIL_GetPlayers
from fields import LocalizedStringField, StringField, BooleanField
from gamerules import GameRules

if isserver:
    from core.usermessages import SendUserMessage, CRecipientFilter, CSingleUserRecipientFilter, CPVSFilter
    from utils import UTIL_PlayerByIndex, UTIL_GetCommandClient
    from gameinterface import concommand, AutoCompletion, ConVarRef
    from core.signals import clientactive, resourceupdated, resourcecollected, resourcespent
else:
    from core.signals import resourceset
    from vgui import images
    
import gamemgr

# resources is the true state
# resourcesaccumlated is used to keep non rounded amounts of resources. 
# Only rounded resource amounts are stored, but the code may send fractions
# resourceslast is used for determining if the resources changed and need to be transmitted to the players
resources = defaultdict(lambda : defaultdict(lambda : 0)) # [owner][resourcetype]
resourcesaccumlated = defaultdict(lambda : defaultdict(lambda : 0)) # [owner][resourcetype]
resourceslast = defaultdict(lambda : defaultdict(lambda : 0)) # Use by update function

resourcecaps = defaultdict(lambda : defaultdict(lambda : 0)) # [owner][resourcetype]
resourcecapslast = defaultdict(lambda : defaultdict(lambda : 0)) # Use by update function


# Resources db
dbid = 'resources'
dbresources = gamemgr.dblist[dbid]

def GetResourceInfo(name):
    return dbresources.get(name, None)

class ResourceInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = gamemgr.BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        if isclient:
            if not newcls.displayname:
                newcls.displayname = newcls.name
                
            if newcls.iconname:
                newcls.icon = images.GetImage(newcls.iconname)
                
        return newcls
    
class ResourceInfo(gamemgr.BaseInfo, metaclass=ResourceInfoMetaClass):
    id = dbid
    
    #: Name for display
    displayname = LocalizedStringField(value='')
    #: Icon path of this resource
    iconname = StringField(value='')
    #: Icon of this resource
    icon = None
    #: Whether this resource has a maximum.
    iscapped = BooleanField(value=False)
    #: Don't allow resources to exceed the cap/maximum
    nocapoverflow = BooleanField(value=False)
    
    # Resource amount method
    @classmethod
    def TakeResources(cls, owner, amount):
        """ Default implementation for taking resources.

            Args:
                owner (int): The owner from who the resource is taken.
                amount (float): Amount being taken.
        """
        UpdateResource(owner, cls.name, -amount)
        
    @classmethod
    def GiveResources(cls, ownernumber, amount):
        """ Default implementation for giving resources.

            Args:
                owner (int): Receiver of resource
                amount (float): Amount being received.
        """
        if cls.iscapped:
            amount = min(resourcecaps[ownernumber][cls.name] - resources[ownernumber][cls.name], amount)
            if amount <= 0:
                return
        UpdateResource(ownernumber, cls.name, amount)
        
    @classmethod
    def GetResourceAmount(cls, ownernumber):
        return resources[ownernumber][cls.name]
        
    # Resource max methods (if used)
    @classmethod
    def GetResourceCap(cls, ownernumber):
        return resourcecaps[ownernumber][cls.name]

    @classmethod
    def UpdateResourceCap(cls, ownernumber, capchange):
        """ Updates the resource cap/maximum. Only used if "iscapped" is True! """
        resourcecaps[ownernumber][cls.name] +=  capchange
        if cls.nocapoverflow:
            if resourcecaps[ownernumber][cls.name] < resources[ownernumber][cls.name]:
                resources[ownernumber][cls.name] = resourcecaps[ownernumber][cls.name]


@usermessage(messagename='_ur')
def ClientUpdateResource(ownernumber, resourcetype, amount, **kwargs):
    """ Updates the resource amount of a player.

        Args:
            ownernumber (int): Owner
            resourcetype (str): Resource type (from dbresources)
            amount (int): Resource number (rounded numbers).
    """
    resources[ownernumber][resourcetype] = amount
    FireSignalRobust(resourceset, ownernumber=ownernumber, type=resourcetype, amount=amount)


@usermessage(messagename='_urc')
def ClientUpdateResourceCap(ownernumber, resourcetype, amount, **kwargs):
    """ Update the resource cap.

        Args:
            ownernumber (int): Owner
            resourcetype (str): Resource type (from dbresources)
            amount (int): New resource cap
    """
    resourcecaps[ownernumber][resourcetype] = amount


def CheckClientResources():
    for ownernumber, ownresources in resources.items():
        for type, amount in ownresources.items():
            if resourceslast[ownernumber][type] != amount:
                UpdateClientsResource(ownernumber, type)
                resourceslast[ownernumber][type] = amount
                
    for ownernumber, ownresourcecaps in resourcecaps.items():
        for type, amount in ownresourcecaps.items():
            if resourcecapslast[ownernumber][type] != amount:
                UpdateClientsResourceCap(ownernumber, type)
                resourcecapslast[ownernumber][type] = amount
    
if isserver:
    @receiver(prelevelinit)
    def LevelInit(sender, **kwargs):
        InitializeResources()
        if not IsTickMethodRegistered(CheckClientResources):
            RegisterTickMethod(CheckClientResources, 0.2)

    @receiver(postlevelshutdown)
    def LevelShutdown(sender, **kwargs):
        if IsTickMethodRegistered(CheckClientResources):
            UnregisterTickMethod(CheckClientResources)

if isserver:
    @receiver(clientactive)
    def ClientActive(sender, client, **kwargs):
        UpdateAllClientResources(client)
    
# Resource methods    
def InitializeResources():
    global resources
    # Usage: resources[OWNER_NUMBER][RESOURCE_TYPE]
    resources.clear()
    resourcesaccumlated.clear()
    resourceslast.clear()
    
def ResetResource(type):
    for ownernumber in resources.keys():
        resources[ownernumber][type] = 0
        resourcesaccumlated[ownernumber][type] = 0
        resourceslast[ownernumber][type] = 0
    
def UpdateResource(ownernumber, type, amount):
    resourcesaccumlated[ownernumber][type] += amount
    
    if resourcesaccumlated[ownernumber][type] < 0:
        remove = int(floor(resourcesaccumlated[ownernumber][type]))
        resources[ownernumber][type] += remove
        resourcesaccumlated[ownernumber][type] -= remove
    else:
        add = int(floor(resourcesaccumlated[ownernumber][type]))
        resources[ownernumber][type] += add
        resourcesaccumlated[ownernumber][type] -= add

    FireSignalRobust(resourceupdated, ownernumber=ownernumber, type=type, amount=amount)
    
def SetResource(ownernumber, type, amount):
    resources[ownernumber][type] = amount
    resourcesaccumlated[ownernumber][type] = 0
    
def HasEnoughResources(costs, ownernumber):
    """ Returns if the player has enough resources by checking
        the list of costs
        
        Input:
        costs - a list containing tuples of the form (cost, amount)
    """
    for resource in costs:
        if resource[1] > resources[ownernumber][resource[0]]:
            return False
    return True
    
def FindFirstCostSet(c, ownernumber):
    """ Returns the first list of costs in the Cost class satisfying
        the resources the player has.
        
        Input:
        c - an instance of C.
    """
    for l in c:
        if HasEnoughResources(l, ownernumber):
            return l
    return None
    
def TakeResources(ownernumber, costs, fire_spent=True, resource_category=''):
    """ Takes resources for the player.
    
        Args:
            costs (list): a list containing tuples of the form (cost, amount)

        Kwargs:
            fire_spent (bool): Fire resource spent signal
            resource_category (str): Resource category, used for match statistics

    """
    if not costs:
        return
    for resource in costs:
        info = GetResourceInfo(resource[0]) if type(resource[0]) == str else resource[0]
        if resource[1] > 0 and info: 
             info.TakeResources(ownernumber, resource[1])
             if fire_spent:
                FireSignalRobust(resourcespent, owner=ownernumber, type=info.name, amount=resource[1],
                                 resource_category=resource_category)
            
def GiveResources(ownernumber, costs, firecollected=False):
    """ Gives resources to the player.
    
        Args:
            costs (list): a list containing tuples of the form (cost, amount)
            firecollected (bool): Fire resource collected signal
    """
    if not costs:
        return
    for resource in costs:
        info = GetResourceInfo(resource[0]) if type(resource[0]) == str else resource[0]
        if resource[1] > 0 and info: 
            info.GiveResources(ownernumber, resource[1])
            if firecollected:
                FireSignalRobust(resourcecollected, owner=ownernumber, type=info.name, amount=resource[1])
            
if isserver:
    def FullResourceUpdatePlayers():
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if player is None:
                continue    
            UpdateAllClientResources(player)
        
    def UpdateAllClientResources(client):
        filter = CSingleUserRecipientFilter(client)
        filter.MakeReliable()        
        for type, value in dbresources.items():
            SendResourceInfo(filter, client.GetOwnerNumber(), type)        
        
    def UpdateClientsResource(ownernumber, type):
        """ For each player with this ownernumber update resource of the given type """
        filter = CRecipientFilter()
        filter.MakeReliable() 
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if player is None:
                continue
            if player.GetOwnerNumber() == ownernumber:
                filter.AddRecipient(player)
        SendResourceInfo(filter, ownernumber, type)
        
    def UpdateClientsResourceCap(ownernumber, type):
        filter = CRecipientFilter()
        filter.MakeReliable() 
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if not player:
                continue
            if player.GetOwnerNumber() == ownernumber:
                filter.AddRecipient(player)
        SendResourceCapInfo(filter, ownernumber, type)
        
    def SendResourceInfo(filter, ownernumber, type):
        ClientUpdateResource(ownernumber, type, resources[ownernumber][type], filter=filter)   
        
    def SendResourceCapInfo(filter, ownernumber, type):
        ClientUpdateResourceCap(ownernumber, type, resourcecaps[ownernumber][type], filter=filter)   

    @receiver(playerchangedownernumber)
    def PlayerChangedOwnerNumber(sender, player, oldownernumber, **kwargs):
        # If the old owner number is the same as the new one, we just spawned
        # In this case we use ClientActive already, so don't send again.
        if player.IsConnected() and player.GetOwnerNumber() != oldownernumber:
            UpdateAllClientResources(player)
    
    def MessageResourceIndicator(owners, origin, text='', resourcetype=''):
        """ Displays resource message above generating building/unit for given owners.

            Args:
                owners (list|int): Either a list or a single owner.

            Kwargs:
                text (str): Message to display (e.g. +1 Req)
                resoucetype (str): Resource type (from dbresources)
        """
        if type(owners) == int:
            owners = [owners]
            
        msg_filter = CPVSFilter(origin)
        players = set(UTIL_GetPlayers()) - set(UTIL_ListPlayersForOwners(owners))
        for player in players:
            msg_filter.RemoveRecipient(player)
            
        msg = [origin]
        if text: 
            msg.append(text)
        if resourcetype: 
            msg.append(resourcetype)
        
        SendUserMessage(msg_filter, '_rind', msg)
else:
    FullResourceUpdatePlayers = None
    UpdateAllClientResources = None
    UpdateClientsResource = None
    SendResourceInfo = None
    PlayerChangedOwnerNumber = None
    MessageResourceIndicator = None

# Defines costs
class C(list):
    def __init__(self, costname=None, value=None):
        super(C, self).__init__()
        if costname:
            self.append([(costname, value)])
        
    def __and__(self, other):
        if not isinstance(other, C):
            raise TypeError(other)
        c = copy.deepcopy(self)
        if other:
            c[-1].extend(other[0])
            if len(other) > 1:
                c.extend(other[1:len(other)])
        return c
        
    def __or__(self, other):
        if not isinstance(other, C):
            raise TypeError(other)
        c = copy.deepcopy(self)
        c.extend(other)
        return c
        
# Save/restore of resources
@receiver(saverestore_save)
def SaveResources(fields, *args, **kwargs):
    for owner, resourcespertype in resources.items():
        for type, amount in resourcespertype.items():
            fields['resource_%d_%s' % (owner, type)] = str(amount)
            fields['resourceacc_%d_%s' % (owner, type)] = str(resourcesaccumlated[owner][type])
            
    for owner, resourcespertype in resourcecaps.items():
        for type, amount in resourcespertype.items():
            fields['resourcecap_%d_%s' % (owner, type)] = str(amount)
            
@receiver(saverestore_restore)
def RestoreResources(fields, *args, **kwargs):
    resource = re.compile('resource_(?P<owner>\d+)_(?P<type>[a-zA-Z]+)')
    resourceacc = re.compile('resourceacc_(?P<owner>\d+)_(?P<type>[a-zA-Z]+)')
    resourcecap = re.compile('resourcecap_(?P<owner>\d+)_(?P<type>[a-zA-Z]+)')
    
    for name, value in fields.items():
        match = resource.match(name)
        if match:
            resources[int(match.group('owner'))][match.group('type')] = int(value)
            continue
        match = resourceacc.match(name)
        if match:
            resourcesaccumlated[int(match.group('owner'))][match.group('type')] = float(value)
            continue
        match = resourcecap.match(name)
        if match:
            resourcecaps[int(match.group('owner'))][match.group('type')] = int(value)
            continue
            
# Commands for testing
if isserver:
    sv_cheats = ConVarRef('sv_cheats')

    @concommand('wars_giveresource', 'Give resource', 0,
                                    completionfunc=AutoCompletion(lambda: list(dbresources.keys())))
    def cc_wars_giveresource(args):
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command wars_giveresource in multiplayer, unless the server has sv_cheats set to "
                  "1 or game is in sandbox mode.")
            return
    
        try:
            name = args[1]
            amount = int(args[2])
        except:
            print('Usage: wars_giveresource [resourcetype] [amount]')
            return
        player = UTIL_GetCommandClient()
        
        info = GetResourceInfo(name)
        if info: 
            info.GiveResources(player.GetOwnerNumber(), amount)
        else: 
            print('Unknown resource type %s' % (name))
