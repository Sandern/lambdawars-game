import traceback
import ast

from core.dispatch import receiver
from core.signals import FireSignalRobust, prelevelshutdown
from core.usermessages import usermessage

from gameinterface import ConVar, ConVarRef, concommand, FCVAR_CHEAT

if isclient:
    from vgui import images
    from core.signals import refreshhud
else:
    from core.signals import clientactive
    from gameinterface import CSingleUserRecipientFilter, servergamedll
    
import gamemgr
from gamedb import dbgamepackages
from core.resources import FindFirstCostSet, C
from fields import BooleanField, FloatField, StringField, LocalizedStringField, ListField
from collections import defaultdict

wars_ability_debug = ConVar('wars_ability_debug' if isserver else 'cl_wars_ability_debug', '0', FCVAR_CHEAT)

# Message types
MSG_TECH_SETAVAILABLE = 3
MSG_TECH_SETNOTAVAILABLE = 4
MSG_TECH_SETTECHENABLED = 5
MSG_TECH_SETTECHDISABLED = 6
MSG_TECH_SETSHOWONUNAVAILABLE = 7
MSG_TECH_SETNOTSHOWONUNAVAILABLE = 8
MSG_TECH_SETSUCCESSORABILITY = 9

# The available abilities
dbid = 'abilities'
dbabilities = gamemgr.dblist[dbid]

# List with all active abilities in the map
active_abilities = set()

# Tech system
def GetTechNode(info, ownernumber):
    if isinstance(info, str):
        abiname = info
        info = GetAbilityInfo(abiname)
        if not info:
            PrintWarning('GetTechNode: Invalid ability "%s"\n' % abiname)
            assert(0)
            return fallbacktechnode

    if ownernumber in info.techinfo:
        return info.techinfo[ownernumber]
        
    technode = info.TechNode(info, ownernumber)
    info.techinfo[ownernumber] = technode
    technode.Initialize()
    return technode

class BaseTechNode(object):
    # Default values changed if this is False. Used for deciding if to send data to a newly connected client.
    pristine = True

    def __init__(self, info, ownernumber):
        super().__init__()
        
        self.info = info
        self.name = info.name
        self.ownernumber = ownernumber
        self.oldtechrequirements = []
        self.requiredby = []  # Names of other abilities that require us
        
    def Initialize(self):
        """ Initialize our tech. Find out if we should be available """
        self.RebuildRequiredBy()
        
        if isserver:
            self.RecomputeAvailable()
            
    def RebuildRequiredBy(self):
        """ Adds this technode to lists of other technodes which we require. 
            This technode will then be notified in OnTechEnabledChanged when
            their tech state changes. This method should be called again if
            the tech requirements change.
        """
        if not self.info:
            return
            
        for techrequirement in self.oldtechrequirements:
            technode = GetTechNode(techrequirement, self.ownernumber)
            if self.name in technode.requiredby:
                technode.requiredby.remove(self.name)
        self.oldtechrequirements = list(self.info.techrequirements)
            
        for techrequirement in self.info.techrequirements:
            technode = GetTechNode(techrequirement, self.ownernumber)
            technode.requiredby.append(self.name)
            
    # Server only methods. 
    if isserver:
        def RecomputeAvailable(self):
            if not self.info:
                return
            
            if self.locked:
                available = False
            else:
                available = True
                for techrequirement in self.info.techrequirements: 
                    technode = GetTechNode(techrequirement, self.ownernumber)
                    if not technode.techenabled:
                        available = False
                        break
            self.available = available
            
        def OnRequiredNodeChanged(self, technode):
            self.RecomputeAvailable()
            
        def FullUpdateClient(self, client):
            filter = CSingleUserRecipientFilter(client)
            filter.MakeReliable()
            ClientFullUpdateTechState(self.name, self.ownernumber, self.available, self.techenabled,
                                      self.showonunavailable, self.successorability, filter=filter)
            
    def OnTechEnabledChanged(self):
        from core.units import unitlist
        
        for unit in unitlist[self.ownernumber]:
            unit.UpdateAbilities()
            
    # The variables available and techenabled define a tech node.
    # Available tells use if we can use this ability.
    # Techenabled tells if other abilities that require us should be made available.
    # For example, an upgrade might be available. After researching it, it becomes
    # techenabled, but not available anymore.
    # A building might always be available, but becomes techenabled if we have at least
    # one building.
    _available = True

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, available):
        if self._available == available:
            return
        self._available = available
        self.pristine = False
        
        if isclient:
            FireSignalRobust(refreshhud)
            
        if isserver and not servergamedll.IsRestoring():
            ClientUpdateTechState(MSG_TECH_SETAVAILABLE if available else MSG_TECH_SETNOTAVAILABLE, self.name, self.ownernumber)

    _techenabled = True

    @property
    def techenabled(self):
        return self._techenabled

    @techenabled.setter
    def techenabled(self, techenabled):
        if self._techenabled == techenabled:
            return
        self._techenabled = techenabled
        self.pristine = False
        
        self.OnTechEnabledChanged()
        
        if isclient:
            FireSignalRobust(refreshhud)
            
        if isserver:
            self.RecomputeAvailable()
            
            for rb in self.requiredby:
                technode = GetTechNode(rb, self.ownernumber)
                technode.OnRequiredNodeChanged(technode)

            if not servergamedll.IsRestoring():
                ClientUpdateTechState(MSG_TECH_SETTECHENABLED if techenabled else MSG_TECH_SETTECHDISABLED, self.name, self.ownernumber)

    _showonunavailable = True

    @property
    def showonunavailable(self):
        return self._showonunavailable

    @showonunavailable.setter
    def showonunavailable(self, showonunavailable):
        if self._showonunavailable == showonunavailable:
            return
        self._showonunavailable = showonunavailable
        self.pristine = False
        
        if isclient:
            FireSignalRobust(refreshhud)
        
        if isserver and not servergamedll.IsRestoring():
            ClientUpdateTechState(MSG_TECH_SETSHOWONUNAVAILABLE if showonunavailable else MSG_TECH_SETNOTSHOWONUNAVAILABLE, self.name, self.ownernumber)

    _successorability = None

    @property
    def successorability(self):
        return self._successorability

    @successorability.setter
    def successorability(self, successorability):
        if self._successorability == successorability:
            return
        self._successorability = successorability
        self.pristine = False
        
        if isserver and not servergamedll.IsRestoring():
            ClientUpdateTechState(MSG_TECH_SETSUCCESSORABILITY, self.name, self.ownernumber, successorability)
    
    # For "wars_ability_manager": lock the ability, making the ability unavailable even if requirements are fulfilled
    _locked = False

    @property
    def locked(self):
        """ Whether this ability is locked for the player, even when researched. """
        return self._locked
    
    @locked.setter
    def locked(self, locked):
        """ Changes if this ability is locked for the player, even when researched. """
        if self._locked == locked:
            return
        self._locked = locked
        self.pristine = False
        
        if isserver and not servergamedll.IsRestoring():
            self.RecomputeAvailable()
            ClientSetTechNodeLocked(self.name, self.ownernumber, self._locked)
            
    # For "wars_ability_manager": make an ability free of costs for a player
    _nocosts = False
    
    @property
    def nocosts(self):
        return self._nocosts
    
    @nocosts.setter
    def nocosts(self, nocosts):
        if self._nocosts == nocosts:
            return
        self._nocosts = nocosts
        self.pristine = False
        
        if isclient:
            FireSignalRobust(refreshhud)
        
        if isserver and not servergamedll.IsRestoring():
            ClientSetTechNodeNoCosts(self.name, self.ownernumber, self._nocosts)


class FallbackTechNode(BaseTechNode):
    def __init__(self):
        super(BaseTechNode, self).__init__() # Skip BaseTechNode
        
        self.info = None
        self.name = 'fallbacktechnode'
        self.ownernumber = 0
        self.oldtechrequirements = []
        self.requiredby = []
        
    @property
    def available(self):
        return True
    
    @property
    def techenabled(self):
        return True
    
    @property
    def showonunavailable(self):
        return False
    
    @property
    def successorability(self):
        return None


fallbacktechnode = FallbackTechNode()


#
# Base entry for ability info
#
class AbilityInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __c_mul(a, b):
        return ast.literal_eval(hex((a * b) & 0xFFFFFFFF)[:-1])
    
    def __create_ability_uid(cls, name):
        # From: http://effbot.org/zone/python-hash.htm
        if not name:
            return 0 # empty
        value = ord(name[0]) << 7
        for char in name:
            value = cls.__c_mul(1000003, value) ^ ord(char)
        value = value ^ len(name)
        if value == -1:
            value = -2
        return value

    def __new__(cls, name, bases, dct):
        # If defaultautocast autocast is specified, then supportsautocast must be true!
        if dct.get('defaultautocast', False) is True:
            dct['supportsautocast'] = True

        newcls = gamemgr.BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        # Unique integer identifier for this ability, based on the name
        newcls.uid = cls.__create_ability_uid(cls, newcls.name)

        # Copy disabled image from normal image if no disabled image is specified
        if 'image_name' in dct and 'image_dis_name' not in dct:
            newcls.image_dis_name = newcls.image_name
                    
        if isclient:
            newcls.image = images.GetImage(newcls.image_name)
            newcls.image_dis = images.GetImage(newcls.image_dis_name)
            
            # If displayname is not set, just use name
            if not newcls.displayname:
                newcls.displayname = newcls.name
                    
        # Tech 
        if newcls.TechNode and newcls.techglobal:
            newcls.techinfo = defaultdict(lambda: newcls.TechNode())
            
        return newcls


class CostListField(ListField):
    def ToValue(self, rawvalue):
        if type(rawvalue) == str:
            rawvalue = ast.literal_eval(rawvalue)
        if type(rawvalue) != C:
            # Costs defined as a single list. Put the list in a list.
            if rawvalue and type(rawvalue[0]) != list:
                rawvalue = [rawvalue]
                
            # Create a C object
            costs = C()
            costs.extend(rawvalue)
            rawvalue = costs
        return rawvalue


class TechReqListField(ListField):
    def Set(self, clsorinst, value):
        oldtechinfo = clsorinst.techinfo
    
        super().Set(clsorinst, value)
        
        if oldtechinfo:
            for k, v in oldtechinfo.items():
                v.RebuildRequiredBy()
                if isserver:
                    v.RecomputeAvailable()
                    
        if clsorinst.techinfo:
            for k, v in clsorinst.techinfo.items():
                v.RebuildRequiredBy()
                if isserver:
                    v.RecomputeAvailable()


class AbilityInfo(gamemgr.BaseInfo, metaclass=AbilityInfoMetaClass):
    id = dbid
    
    #: List of costs. Each cost is defined as a tuple consisting of the resource name and amount.
    #: You may also define multiple lists of costs. Examples:
    #: costs = [('requisition', 5), ('scrap',2)]
    #: costs = [[('requisition', 5)], [('kills', 2)]]
    costs = CostListField()

    #: Resource category, for match statistics purposes
    resource_category = 'uncategorized'
    
    #: Cooldown/recharge time after executing an ability successfully.
    rechargetime = FloatField(value=0.0)

    #: Additional abilities on which to apply the cooldown/recharge time.
    #: Useful for linked abilities
    recharge_other_abilities = ListField()

    #: Set recharge for ability on unit when spawned
    set_initial_recharge = BooleanField(value=False)
    
    #: Time it takes to produce/research this ability or unit at a building.
    buildtime = FloatField(value=0.0)
    
    #: Required energy for executing this ability
    energy = FloatField(value=0.0)
    
    #: Name shown in hud.
    #: In case the name starts with #, it is considered a localized string.
    displayname = LocalizedStringField(value='', encoding='ascii')
    
    #: Description shown in hud.
    #: In case the name starts with #, it is considered a localized string.
    description = LocalizedStringField(value='Put some description here', encoding='ascii')
    
    #: If True, do not show in the ability/unit panel
    hidden = False 

    #: Ability/unit icon shown in hud
    image_name = 'vgui/abilities/ability_unknown.vmt'
    
    #: Ability/unit icon shown in hud when disabled
    image_dis_name = 'vgui/abilities/ability_unknown_dis.vmt'
    
    #: List of abilities names of which we should check the tech nodes
    techrequirements = TechReqListField()
    
    #: Whether this ability supports autocast. If "defaultautocast" is True, then this is set to True automatically.
    supportsautocast = BooleanField(value=False)
    
    #: Whether by default autocast is on for this ability
    defaultautocast = BooleanField(value=False)
    
    #: Enemy range at which an extra auto cast check is performed (0 for no check)
    checkautocastinenemyrange = FloatField(value=0)

    #: List of abilities which can't be autocasted at the same time as this ability.
    #: For example two abilities could be autocasted as main attack. Only one can be active.
    autocast_exclude = ListField(value=[])
    
    #: This ability cannot be executed, but provides a bonus.
    passive = BooleanField(value=False)
    
    #: Hotkey in case the semantic hotkey system is used.
    hotkey = StringField(value='')
    
    #: Soundscript played on ability activation.
    activatesoundscript = StringField(value='')

    #: Force play of activate sound. If off, limits these sounds to once per x seconds
    activatesoundscript_force_play = BooleanField(value=True)
    
    #: Faction sound played when this ability is produced at a building (e.g. unit, upgrade)
    producedfactionsound = ''
    
    #: Hints for strategic AI (e.g. ability is an upgrade). Default is no hint.
    sai_hint = set([])
    
    #: Fill color, used by core.utils to color code the ability.
    fillcolor = '#FAF4D4'
    
    #: Overrides default rally line when specific and this ability is associated with an Order
    rallylinemat = None
    
    techglobal = True
    TechNode = BaseTechNode
    techinfo = None
    
    def __str__(self):
        return '<%s>' % (self.DebugPrint().replace('\n', ','))
    
    def DebugPrint(self):
        return '#%d ability %s\n' % (self.abilityid, self.name)
    
    @staticmethod
    def FilterSelection(abiname, units):
        newunits = []
        for unit in units:
            if abiname in unit.abilitiesbyname:
                newunits.append(unit)
        return newunits
    
    @classmethod
    def GetRequirementsUnits(info, player, units=None):
        if units is None:
            units = info.FilterSelection(info.name, player.GetSelection())
            
        if not units:
            return set()

        # Start with first unit, then keep taking the intersection with the requirements of the other units.
        requirements = info.GetRequirements(player, units[0])
        for unit in units[1:]:
            requirements &= info.GetRequirements(player, unit)
        return requirements
        
    @classmethod    
    def GetRequirements(info, player, unit):
        """ Returns the set of requirements for this ability.
        
            Args:
                player (entity): The player doing this ability
                unit (entity): Do checks for a specific unit.
        """
        requirements = set()
        
        # TODO: Should it be allowed for the player to be None?
        #       This can be the case when a unit autocasts an ability
        unitowner = unit.GetOwnerNumber()
        playerowner = player.GetOwnerNumber() if player else unitowner 
        
        # The player should own the unit
        if player:
            if not unit.CanPlayerControlUnit(player):
                requirements.add('uncontrollable')
        
        # Should not be recharging this ability
        if info.rechargetime and info.uid in unit.abilitynexttime:
            if unit.abilitynexttime[info.uid] > gpGlobals.curtime:
                requirements.add('recharging')

        # Sohould have enough energy
        if info.energy > unit.energy:
            requirements.add('energy')
            
        # The unit should not have another uninterruptible ability active
        activeability = unit.activeability
        if activeability and not activeability.interruptible:
            requirements.add('notinterruptible')
            
        # Get additional requirements from the unit entity class
        unit.GetRequirements(requirements, info, player)
        
        # The ability should be available and not locked for the owner of the unit
        technode = GetTechNode(info.name, unitowner)
        if not technode.available:
            requirements.add('available')
        if technode.locked:
            requirements.add('locked')
        
        if not technode.nocosts:
            # Player should have enough resources to perform this ability
            if info.costs and not FindFirstCostSet(info.costs, playerowner):
                requirements.add('resources')
                
        return requirements 
        
    @classmethod    
    def ShouldShowAbility(info, unit):
        """ Allows to hide an ability for a specific unit. """
        # Don't show if technode says so
        technode = GetTechNode(info.name, unit.GetOwnerNumber())
        if not technode.available and not technode.showonunavailable:
            return False
        
        # By default do not show an ability if the unit is being constructed (building only)
        if hasattr(unit, 'constructionstate') and unit.constructionstate != unit.BS_CONSTRUCTED:
            return False
        return True
    
    @classmethod    
    def CanDoAbility(info, player, unit):
        """ Check for the given unit if it can do this ability.
            This is mainly done by calling GetRequirements and check if
            the returned set is empty."""
        requirements = info.GetRequirements(player, unit)
        return len(requirements) == 0
        
    @staticmethod
    def GetTechNode(*args, **kwargs):
        return GetTechNode(*args, **kwargs)


#
# Misc
#
def GetAbilityInfo(abi_name):
    """ Returns the ability info class. Returns None if the ability does not exists. """
    return dbabilities.get(abi_name, None)

# Shutdown/new clients
@receiver(prelevelshutdown)
def AbilitiesShutdown(sender, **kwargs):
    """ Clears all tech info of all abilities in each game package.
        Clears the list of active abilities on shutdown. 
        Calls cleanup on each active ability. 
        Also clears the precache table."""
    for name, pkg in dbgamepackages.items():
        for abi_name, abi in pkg.db[dbid].items():
            abi.techinfo.clear()
            
    cleanupabilities = set(active_abilities) # Create a copy, cleanup might already remove from the list
    [abi.Cleanup() for abi in cleanupabilities]
    active_abilities.clear()

if isserver:
    @receiver(clientactive)
    def AbilitiesClientActive(sender, client, **kwargs):
        """ Gives a full update of the tech tree to the new client. """
        for info in dbabilities.values():
            if info.TechNode and info.techglobal:
                for ti in info.techinfo.values():
                    if ti.pristine:
                        continue
                    ti.FullUpdateClient(client)

#
# Global power ability test command
#
if isserver:
    @concommand('wars_abi_clearall', 'Clear all abilities in a forceful way', FCVAR_CHEAT)
    def cc_wars_abi_clearall(args):
        for abi in active_abilities:
            try:
                abi.Cancel()
            except:
                traceback.print_exc()     
        active_abilities.clear()
        
    @concommand('wars_abi_printactive', 'Prints all active abilities', FCVAR_CHEAT)
    def wars_abi_printactive(args):
        global active_abilities
        print('Active abilities at time %f' % (gpGlobals.curtime))
        for abi in active_abilities:
            print(abi.DebugPrint())
            
@usermessage(messagename='_uts')
def ClientUpdateTechState(type, info, ownernumber, *args, **kwargs):
    """ Updates a single property of a technode. """
    technode = GetTechNode(info, ownernumber)
    if type == MSG_TECH_SETAVAILABLE:
        technode.available = True
    elif type == MSG_TECH_SETNOTAVAILABLE:
        technode.available = False
    elif type == MSG_TECH_SETTECHENABLED:
        technode.techenabled = True
    elif type == MSG_TECH_SETTECHDISABLED:
        technode.techenabled = False
    elif type == MSG_TECH_SETSHOWONUNAVAILABLE:
        technode.showonunavailable = True
    elif type == MSG_TECH_SETNOTSHOWONUNAVAILABLE:
        technode.showonunavailable = False
    elif type == MSG_TECH_SETSUCCESSORABILITY:
        technode.successorability = args[0]
    else:
        PrintWarning("core.abilities.info.ClientUpdateTechState: invalid message type\n")
        
@usermessage(messagename='_futs')
def ClientFullUpdateTechState(name, ownernumber, available, techenabled, showonunavailable, successorability, *args, **kwargs):
    """ Intended for usage when client (re)connects. """
    technode = GetTechNode(name, ownernumber)
    technode.available = available
    technode.techenabled = techenabled
    technode.showonunavailable = showonunavailable
    technode.successorability = successorability
    
@usermessage()
def ClientSetTechNodeLocked(info, ownernumber, state, *args, **kwargs):
    technode = GetTechNode(info, ownernumber)
    technode.locked = state
        
@usermessage()
def ClientSetTechNodeNoCosts(info, ownernumber, state, *args, **kwargs):
    technode = GetTechNode(info, ownernumber)
    technode.nocosts = state