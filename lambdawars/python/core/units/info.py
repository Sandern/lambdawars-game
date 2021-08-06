from srcbase import *
from vmath import *
import random
import weakref
import re
from collections import defaultdict
from utils import UTIL_FindPosition, FindPositionInfo, UTIL_ListPlayersForOwnerNumber
from gameinterface import modelinfo, FCVAR_NOTIFY, FCVAR_REPLICATED, ConVar, ConVarRef, AutoCompletion, concommand
from animation import ExtractBbox, SelectWeightedSequence
from entities import GetClassByClassname, Activity

import gamemgr
from gamemgr import BaseInfoMetaclass, BaseInfo

from gamerules import GameRules, gamerules
from fields import IntegerField, FloatField, StringField, ListField, DictField, VectorField, BooleanField, GetField, ObjSetField
from core.usermessages import usermessage
from core.dispatch import receiver
from core.signals import postlevelshutdown, prelevelinit, playerchangedcolor, saverestore_save, saverestore_restore
from core.abilities import AbilityTargetGroup, GetAbilityInfo, GetTechNode
from core.abilities.info import dbid as abilitydbid, AbilityInfoMetaClass
import core.attributes # Ensure base attributes are loaded
from . import hull

if isclient:
    from vgui import HudIcons
else:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_GetCommandClient, UTIL_DropToFloor, UTIL_RemoveImmediate
    from core.signals import clientactive, playerchangedownernumber
    from core.usermessages import CRecipientFilter, CSingleUserRecipientFilter
    
# Keeps track of the available units
dbid = 'units'
dbunits = gamemgr.dblist[dbid]

# Attacks db
dbattacksid = 'attacks'
dbattacks = gamemgr.dblist[dbattacksid]
dbattacks.priority = 1  # Increase priority to ensure it registered before the units, but after attributes

# Convars
sv_unitlimit = ConVar('sv_unitlimit', '100', FCVAR_NOTIFY|FCVAR_REPLICATED)
sv_cheats = ConVarRef('sv_cheats')

# Keeps track of precached units for PrecacheUnit method
isunitprecached = defaultdict(lambda : False)

# Predefined accuracies
accuracymap = {
    'very_low': 0.25,
    'low': 0.5,
    'medium': 1.0,
    'normal': 1.0,
    'high': 1.5,
    'very_high': 2.0,
}

# For representing damage types as string
dmgtypes = {
    DMG_GENERIC: 'DMG_GENERIC',
    DMG_CRUSH: 'DMG_CRUSH',
    DMG_BULLET: 'DMG_BULLET',
    DMG_SLASH: 'DMG_SLASH',
    DMG_BURN: 'DMG_BURN',
    DMG_VEHICLE: 'DMG_VEHICLE',
    DMG_FALL: 'DMG_FALL',
    DMG_BLAST: 'DMG_BLAST',
    DMG_CLUB: 'DMG_CLUB',
    DMG_SHOCK: 'DMG_SHOCK',
    DMG_SONIC: 'DMG_SONIC',
    DMG_ENERGYBEAM: 'DMG_ENERGYBEAM',
    DMG_PREVENT_PHYSICS_FORCE: 'DMG_PREVENT_PHYSICS_FORCE',
    DMG_NEVERGIB: 'DMG_NEVERGIB',
    DMG_ALWAYSGIB: 'DMG_ALWAYSGIB',
    DMG_DROWN: 'DMG_DROWN',
    DMG_PARALYZE: 'DMG_PARALYZE',
    DMG_NERVEGAS: 'DMG_NERVEGAS',
    DMG_POISON: 'DMG_POISON',
    DMG_RADIATION: 'DMG_RADIATION',
    DMG_DROWNRECOVER: 'DMG_DROWNRECOVER',
    DMG_ACID: 'DMG_ACID',
    DMG_SLOWBURN: 'DMG_SLOWBURN',
    DMG_REMOVENORAGDOLL: 'DMG_REMOVENORAGDOLL',
    DMG_PHYSGUN: 'DMG_PHYSGUN',
    DMG_PLASMA: 'DMG_PLASMA',
    DMG_AIRBOAT: 'DMG_AIRBOAT',
    DMG_DISSOLVE: 'DMG_DISSOLVE',
    DMG_BLAST_SURFACE: 'DMG_BLAST_SURFACE',
    DMG_DIRECT: 'DMG_DIRECT',
    DMG_BUCKSHOT: 'DMG_BUCKSHOT',
}


def BuildDamageTypeString(ent_dmg_types):
    s = ''
    for k, v in dmgtypes.items():
        if k & ent_dmg_types:
            if s:
                s += '|'
            s += v
    return s


class AbilitiesDictField(DictField):
    def Parse(self, cls, name):
        self.default = dict(self.default)

        for i in range(0, 12):
            abi_slot = 'ability_%d' % i
            if hasattr(cls, abi_slot):
                # None can be used to delete an ability from the parent unit definition
                abi_name = getattr(cls, abi_slot)
                if abi_name is not None:
                    self.default[i] = abi_name
                elif i in self.default:
                    del self.default[i]

        return super().Parse(cls, name)


class UnitInfoMetaClass(AbilityInfoMetaClass):
    def __new__(cls, name, bases, dct):
        # Replace accuracy if a string
        # Do before call to base __new__, because it initializes the fields.
        if 'accuracy' in dct:
            if type(dct['accuracy']) == str:
                dct['accuracydesc'] = dct['accuracy']
                dct['accuracy'] = accuracymap[dct['accuracy']]

        newcls = AbilityInfoMetaClass.__new__(cls, name, bases, dct)
        
        # Remove from precache register if in it
        if newcls.name in isunitprecached:
            del isunitprecached[newcls.name]

        # Set mins/maxs from hulltype if specified
        # If not, and mins is also not defined, use model mins/maxs
        if newcls.name:
            if newcls.hulltype:
                newcls.mins = hull.Mins(newcls.hulltype) * newcls.scale * newcls.scalebounds
                newcls.maxs = hull.Maxs(newcls.hulltype) * newcls.scale * newcls.scalebounds
            elif not newcls.mins:
                if newcls.modelname or newcls.modellist:
                    newcls.requiresetup = True # Mins/maxs are retrieved when needed
                else:
                    newcls.mins = hull.Mins('HULL_HUMAN') * newcls.scale * newcls.scalebounds
                    newcls.maxs = hull.Maxs('HULL_HUMAN') * newcls.scale * newcls.scalebounds

        # Configurate unit info specific stuff
        if isclient:
            if newcls.minimapicon_name is not None:
                newcls.minimapicon = HudIcons().GetIcon(newcls.minimapicon_name)
                
        # If "attacks" is not a list, make it a list.
        if type(newcls.attacks) != list:
            newcls.attacks = [newcls.attacks]
        # If list contains strings, use it as a way to access the class by name.
        # The advantage is that a derived class can override it.
        for i, attack in enumerate(newcls.attacks):
            if type(attack) == str:
                newcls.attacks[i] = getattr(newcls, attack)

        # Might be a 'fallback' info object that is not registered
        if newcls.modname is not None:
            modname = newcls.modname.split('.')[0]
            
            # Add to our gamepackage for loading/unloading
            # Overwrite old one
            # Register as Unit AND ability
            gamemgr.dbgamepackages[modname].db[dbid][newcls.name] = newcls
            gamemgr.dbgamepackages[modname].db[abilitydbid][newcls.name] = newcls
            
            # Add to the active list if our gamepackage is loaded   
            if gamemgr.dbgamepackages[modname].loaded:
                gamemgr.dblist[dbid][newcls.name] = newcls
                gamemgr.dblist[abilitydbid][newcls.name] = newcls
                newcls.OnLoaded()
        
        if newcls.cls_name:
            entcls = GetClassByClassname(newcls.cls_name)
            
            # Remove default sai_hint if not a combat unit
            # TODO: Do a better test
            if newcls.name:
                if not hasattr(entcls, 'curorder') or (not newcls.attacks and not newcls.weapons):
                    newcls.sai_hint = set(newcls.sai_hint)
                    newcls.sai_hint.discard('sai_unit_combat')
            
            # Generate fgd info
            factory = getattr(entcls, 'factory__%s' % (newcls.cls_name), None)
            if factory:
                # Use model of this unit if assigned as default
                if not factory.fgdstudio or newcls.defaultfgd:
                    if newcls.modellist:
                        factory.fgdstudio = newcls.modellist[0]
                    else:
                        factory.fgdstudio = newcls.modelname
                        
                # Add unittype to choices in case it is not yet
                try:
                    unittype = GetField(entcls, 'unittype')
                except AttributeError:
                    unittype = None
                    
                if unittype and newcls.name and unittype.choices:
                    if unittype not in entcls.__dict__.values():
                        unittype = unittype.Copy()
                        unittype.choices = []
                        ObjSetField(entcls, 'unittype', unittype)
                        
                    if newcls.name not in unittype.choices:
                        unittype.choices.append((newcls.name, newcls.name))
                        
                        if newcls.defaultfgd or unittype.default == 'unit_unknown':
                            unittype.default = newcls.name
                
        return newcls


class NoSuchAbilityError(Exception):
    pass


def ParseAttributes(info, parseattributes):
    """ Convert attributes names to refs to the info class of that attribute.

        Args:
            info (object): unit or attack info, for debugging purposes
            parseattributes (list): Attributes to be parsed.
    """
    attributes = []
    if parseattributes:
        for attr in parseattributes:
            if type(attr) == str:
                try:
                    attributes.append(gamemgr.dblist['attributes'][attr])
                except KeyError:
                    PrintWarning('Unknown attribute "%s" while registering unit or attack %s (%s)\n' %
                                 (attr, str(info.name), ('Client' if isclient else 'Server')))
                    PrintWarning('\tAvailable attributes: %s\n' % (', '.join(gamemgr.dblist['attributes'].keys())))
            else:
                attributes.append(attr)
    return attributes


class MetaAttackBase(BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        cls = BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        return cls

    def __str__(self):
        return self.GetDescription()
        
    def GetDescription(self, accuracy=1.0):
        damage = self.damage * accuracy
        desc = '%s - %d dmg - %.2f speed - %.2f range' % (self.name, 
            damage, self.attackspeed, self.maxrange)
        try:
            if self.usesbursts:
                avgburst = (self.minburst + self.maxburst) / 2.0
                avgresttime = (self.minresttime + self.maxresttime) / 2.0
                desc += ' - %d burst - %.2f rest time' % (avgburst, avgresttime)
                dps = (damage * avgburst) / (avgburst * self.attackspeed + avgresttime)
            else:
                dps = (damage / self.attackspeed)
        except ZeroDivisionError:
            dps = float('inf')
            
        desc += ' - dps %.2f' % dps
            
        return desc


class UnitInfo(AbilityTargetGroup, metaclass=UnitInfoMetaClass):
    """ Base definition for units.
    
        This definition defines all kind of properties for a unit.
        A derived class is automatically registered if a valid name
        is specified.
        
        Usage:
        class MyUnitInfo(UnitInfo):
            name = 'myunit'
            cls_name = 'myunit_entity'
            
    """
    name = None

    #: Entity class that is spawned when you create this unit.
    cls_name = StringField(value='')
    #: Resource category (match statistics)
    resource_category = 'army'
    #: Dictionary of abilities.
    abilities = AbilitiesDictField(value={})
    #: Amount of population this unit takes.
    population = IntegerField(value=1)
    #: Dictionary of keyvalues inserted before spawning the unit entity class.
    keyvalues = {}
    #: Selection priority. Units with a higher priority are showed first in the hud and unit selection array.
    selectionpriority = IntegerField(value=0)
    #: Attack priority. Units prefer to attack enemies with higher priorities.
    attackpriority = IntegerField(value=0)
    #: Path to portrait video (bik file).
    portrait = StringField(value='')
    #: Material path to unit icon.
    image_name = 'vgui/units/unit_unknown.vmt'
    #: The tier of the unit, lower tier units do less damage against higher tier units. Tier 0 isn't effected by it and does normal damage.
    tier = 0
    
    #: Portrait camera offset
    portraitoffset = VectorField(value=Vector(-50, 0, 12))
    #: Portrait field of view
    portraitfov = IntegerField(value=20)
    
    # Model settings. Leave modelname empty if you want to use the modellist.
    # If a model list is specified, it will randomly pick a  model.
    #: Path to model the unit will use
    modelname = StringField(value='')
    #: If modelname is none, a modelname from this list will be randomly picked
    modellist = ListField(value=[])
    
    # Unit size information
    # If hulltype is not None, it will use the specified hull type from the hull module (overrides mins/maxs)
    # If mins/maxs are left None the model mins/maxs are used.
    # In the other case it will simply use the specified mins/maxs.
    #: Specifies the unit size using a predefined hull type.
    hulltype = None 
    mins = None 
    maxs = None 
    
    #: Clamps the mins. This option is for buildings, which can have weird bounding boxes.
    #: This only does something if placeatmins is False
    clampminsz = False
    
    #: Spawn offset in CreateUnit methods
    zoffset = 0.0 
    #: Whether to place the unit at the mins of the model bounds, or at the origin.
    #: Defaults to the origin.
    placeatmins = False
    #: Whether to drop the unit to the floor when created using "CreateUnitFancy".
    #: For buildings this is disabled.
    oncreatedroptofloor = True
    
    # Health, damage and attacks
    #: Health and MaxHealth the unit will have at Spawn
    health = IntegerField(value=1)
    #: Energy and MaxEnergy the unit will have at Spawn.
    #: Leave 0 to not use energy. In case greater than 0 the unit will get an energy bar.
    unitenergy = IntegerField(value=0)
    #: The initial energy the unit will have. Leave -1 to make it the same as max energy.
    unitenergy_initial = IntegerField(value=-1)
    #: Movement speed. Leave 0 to use the entity default.
    maxspeed = FloatField(value=0)
    #: Turn speed. Leave 0 to use the entity default.
    turnspeed = FloatField(value=200)
    #: Unit view distance
    viewdistance = FloatField(value=1024.0)
    #: Unit sensing distance. If -1, copy viewdistance as sensing distance.
    #: Sensing is used by the AI to choose an enemy.
    sensedistance = FloatField(value=-1)
    #: Distance at which units engage the enemy if no fighting is going on yet.
    #: Leave zero to make it equal to the max attack range.
    engagedistance = FloatField(value=0)
    #: Weapon list of the unit. Each entry refers to the entity classname of the weapon. 
    #: Last weapon in the list is the default active weapon.
    weapons = ListField(value=[])
    #: Can this unit take cover?
    cantakecover = BooleanField(value=False)
    #: Armor type of the unit
    #armortype = StringField(value='default')
    #: Accuracy when using a weapon. Implemented as a simple damage modifier.
    accuracy = FloatField(value=1.0)
    accuracydesc = ''
    #: Attributes of this unit. 
    attributes = ListField(value=[], noreset=True)
    #: Scales the unit model and collision box
    scale = FloatField(value=1)
    #: Only scales the bounds of the unit. Can be used in addition to scale.
    scalebounds = FloatField(value=1)
    #: Overrides model eye offset of unit. Takes priority over class defined customeyeoffset.
    customeyeoffset = None
    
    # Scrap settings
    #: Scrap drop chance
    scrapdropchance = FloatField(value=0.5)

    # Sounds Scripts
    #: Soundscript played when you select the unit
    sound_select = StringField(value='')
    #: Soundscript played when give a move order to the unit
    sound_move = StringField(value='')
    #: Soundscript played when give an attack order to the unit
    sound_attack = StringField(value='')
    #: Soundscript played when the unit dies
    sound_death = StringField(value='')
    #: Soundscript played when the unit jumps
    sound_jump = StringField(value='')
    #: Soundscript played when the unit attack moves
    sound_attackmove = StringField(value='')
    #: Soundscript played when the unit holds position
    sound_holdposition = StringField(value='')
    #: Soundscript played when unit gets hurt
    sound_hurt = StringField(value='')

    #: Misc sounds
    sound_flamer_ignited = StringField(value='')
    
    # Faction sounds
    producedfactionsound = 'announcer_unit_completed'
                
    # Minimap settings
    #: Name of the hud texture that should be used as icon on the minimap for this unit.
    #: Leave this field 'None' to show up as a pixel on the minimap.
    minimapicon_name = None 
    minimapicon = None
    #: Half wide of pixel representation on the minimap (does not apply to icons)
    minimaphalfwide = 1 
    #: Half tall of pixel representation on the minimap (does not apply to icons)
    minimaphalftall = 1
    # Minimap layer. Lower layers are drawn before higher layers
    minimaplayer = 0
    
    # Strategic AI settings
    #: Hints for strategic AI (e.g. unit is a builder). Default is combat unit.
    sai_hint = set(['sai_unit_combat'])
    
    #: Fill color graph generation
    fillcolor = 'white'
    
    #: Used by fgd generator to auto select properties for an entity used by this unit
    defaultfgd = False
    
    #: Used by test suites to filter out units. Provides the names of the test suites from
    #: which to exclude.
    exclude_from_testsuites = set()

    @classmethod 
    def OnLoaded(info):
        super().OnLoaded()
        
        # Convert attributes names to refs to the info class of that attribute
        info.attributes = ParseAttributes(info, info.attributes)
                
    # Attack system. Each unit has a list of attacks.
    #: List of attacks
    attacks = []

    class AttackBase(BaseInfo, metaclass=MetaAttackBase):
        id = dbattacksid
        autogenname = True

        damage = 0
        damagetype = DMG_GENERIC
        minrange = 0.0
        maxrange = 820.0
        #: Allowed cone in which this attack can be executed
        cone = 2.0
        #: Attacks per second. In case of guns this is the firerate. Note that this is the time it takes before you can
        #: do a new attack.
        attackspeed = 0.0
        #: Moves the unit when doing the attack. Skipped when doing hold position.
        requiresmovement = False
        #: If this attack uses bursts (weapon only)
        usesbursts = False
        # burst settings
        minburst = 3
        maxburst = 5
        minresttime = 0.4
        maxresttime = 0.6
        #: Unit handle owning the attack
        unit = None
        #: Weapon handle of active attack instance (if any)
        weapon = None
        #: Can be used to override the attributes of the attacker
        attributes = None

        @classmethod
        def OnLoaded(info):
            super().OnLoaded()

            # Convert attributes names to refs to the info class of that attribute
            info.attributes = ParseAttributes(info, info.attributes)

        def ShouldUpdateAttackInfo(self, unit):
            return True

        def CanAttack(self, enemy):
            """ Tests if unit can attack enemy.

                Args:
                    enemy (entity): enemy to test against.

                Returns (bool): true if attackable
            """
            return True

        def Attack(self, enemy, action):
            """ Executes an attack.

                Args:
                    enemy (entity): enemy to attack. Is None when the player controls the unit.
                    action (BaseAction): action executing the attack. Can be used to change the action. Is None when the
                                         player controls the unit.
            """
            pass

        def __init__(self, unit=None):
            super().__init__()

            self.unit = unit

            # Build dictionary for attributes if any
            if self.attributes != None:
                attributes = {}
                for attr in self.attributes:
                    if type(attr) == str:
                        try:
                            attr = gamemgr.dblist['attributes'][attr]
                        except KeyError:
                            PrintWarning('Unknown attribute "%s" while registering attack %s (%s)\n' %
                                         (attr, str(self), ('Client' if isclient else 'Server')))

                    attributes[attr.name] = attr(unit)
                self.attributes = attributes

        # Useful defaults for cone attribute
        DOT_1DEGREE = 0.9998476951564
        DOT_2DEGREE = 0.9993908270191
        DOT_3DEGREE = 0.9986295347546
        DOT_4DEGREE = 0.9975640502598
        DOT_5DEGREE = 0.9961946980917
        DOT_6DEGREE = 0.9945218953683
        DOT_7DEGREE = 0.9925461516413
        DOT_8DEGREE = 0.9902680687416
        DOT_9DEGREE = 0.9876883405951
        DOT_10DEGREE = 0.9848077530122
        DOT_15DEGREE = 0.9659258262891
        DOT_20DEGREE = 0.9396926207859
        DOT_25DEGREE = 0.9063077870367
        DOT_30DEGREE = 0.866025403784
        DOT_45DEGREE = 0.707106781187
            
    class AttackRange(AttackBase):
        cone = 0.7
        attackspeed = 1.0
        
        def CanAttack(self, enemy):
            return self.unit.CanRangeAttack(enemy)

        def Attack(self, enemy, action):
            return self.unit.StartRangeAttack(enemy)
        
    class AttackMelee(AttackBase):
        maxrange = 64.0
        cone = 0.7
        attackspeed = 1.0
        
        def CanAttack(self, enemy):
            return self.unit.CanMeleeAttack(enemy)

        def Attack(self, enemy, action):
            return self.unit.StartMeleeAttack(enemy)
  
    @classmethod 
    def GetAbilityInfo(info, abilityname, ownernumber):
        """ Get Ability info for a slot. Checks tech upgrades.

        Throws NoSuchAbilityError when it does not have the ability.
        """
        info = GetAbilityInfo(abilityname)
        if not info:
            raise NoSuchAbilityError
        technode = GetTechNode(info, ownernumber)
        while technode.successorability:
            info = GetAbilityInfo(technode.successorability)
            technode = GetTechNode(info, ownernumber)
        return info
        
    @classmethod 
    def GetAbilityInfoAndPrev(info, abilityname, ownernumber):
        """ Get Ability info for a slot. Checks tech upgrades. """
        info = GetAbilityInfo(abilityname)
        if not info:
            return None, None
        prev = None
        technode = GetTechNode(info, ownernumber)
        while technode.successorability:
            prev = info
            info = GetAbilityInfo(technode.successorability)
            technode = GetTechNode(info, ownernumber)
        return info, prev
        
    @classmethod 
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        owner = player.GetOwnerNumber()

        if info.population:
            # Check population count
            if unitpopulationcount[owner]+info.population > GetMaxPopulation(owner):
                requirements.add('population')

        unit_limit = getattr(getattr(GameRules(), 'info', object), 'unit_limits', {}).get(info.name, None)
        if unit_limit is not None:
            if len(unitlistpertype[owner][info.name]) >= unit_limit:
                requirements.add('unit_limit')

        return requirements

    requiresetup = False

    @classmethod
    def Setup(info):
        info.requiresetup = False
        
        modelname = None
        if info.modelname:
            modelname = info.modelname
        elif info.modellist:
            modelname = info.modellist[0]
            
        if modelname:
            model = modelinfo.FindOrLoadModel(modelname)

            info.mins, info.maxs = modelinfo.GetModelBounds(model, Activity.ACT_IDLE)
                
            if info.clampminsz is not False and not info.placeatmins and info.mins.z < info.clampminsz:
                info.mins.z = info.clampminsz

        if info.mins:
            info.mins *= info.scale * info.scalebounds
        if info.maxs:
            info.maxs *= info.scale * info.scalebounds

    # Default ability code for units
    # If used as "cheat" it will show a preview and be placed at the mouse pointer
    # In case executed for an unit it will assume it's a building and it to the production queue
    def Init(self):
        if self.requiresetup:
            self.Setup()

        super().Init()

    if isserver:
        @classmethod           
        def Precache(info):
            PrecacheUnit(info.name)
        
        def StartAbility(self): 
            """ In case this ability is not executed as a cheat, it is added to the build queue 
                of the unit executing this ability."""
            if self.ischeat:
                return
            # Find best unit/building to produce this unit.
            # For the moment simply pick the one with the smallest queue.
            bestunit = None
            smallestqueue = -1
            for unit in self.units:
                n = unit.GetTotalQueuedUnits()
                if not bestunit or n < smallestqueue:
                    smallestqueue = n
                    bestunit = unit
                    
            if not bestunit:
                self.ClearMouse()
                return
                
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            bestunit.AddAbility(self)
            self.cancelonmouselost = False
            self.ClearMouse()
            
        def ProduceAbility(self, producer):
            """ Spawns the unit. Returns the unit on success, None on failure."""
            self.producedunit = producer.ProduceUnit(self.name)
            if self.producedunit:
                self.SetRecharge(self.unit)
                self.Completed()
                return self.producedunit
            return None
            
        def DoAbility(self):
            """ DoAbiltiy is only used as the cheat version of this ability.
                It directly spawns the unit at the target location. """
            if not self.ischeat:
                return
            try:
                owner = int(self.kwarguments.get('owner', self.ownernumber))
            except ValueError:
                owner = self.ownernumber
            CreateUnit(self.name, self.targetpos - Vector(0, 0, self.mins.z), self.targetangle, owner)
            self.Completed()
            
    else:
        def PreCreateVisuals(self):
            #super().PreCreateVisuals()
            if self.ischeat:
                if self.modelname:
                    self.infomodels = [{'modelname' : self.modelname, 'scale' : self.scale}]
                elif self.modellist:
                    self.infomodels = [{'modelname' : self.modellist[0], 'scale' : self.scale}]
                    
        def StartAbility(self): 
            if not self.ischeat:
                self.cancelonmouselost = False
                if self.player and self.player.IsActiveAbility(self):
                    self.player.RemoveActiveAbility(self)
    def ClientUpdateAbilitiesMenu(self):
        pass

    defaultrendercolor = Color(0, 255, 0, 255)        
    
    requirerotation = True
    setrecharge = False
    cancelonunitscleared = False


class UnitFallBackInfo(UnitInfo):
    name = 'unit_unknown'
    displayname = 'Unknown Unit'
    description = ''
    population = 0
    hidden = True
    sai_hint = set()


def CreateUnitNoSpawn(name, owner_number=0):
    """ Creates an unit without spawning the unit into the world.
    
        Use this method in case you want to control the spawning process yourself.
        
        Args:
            name (str): Unit name (i.e. UnitInfo.name)
            
        Kwargs:
            owner_number (int): The owner of the unit
    """
    # Get info
    try:
        info = dbunits[name]
    except KeyError:
        PrintWarning("core.units.info.CreateUnit: No registered unit named %s\n" % name)
        return None
        
    # Setup if needed
    if info.requiresetup:
        info.Setup()
            
    # Create unit
    unit = CreateEntityByName(info.cls_name)
    if not unit:
        return None # CreateEntityByName will print the warning
    for k, v in info.keyvalues.items():
        unit.KeyValue(k, v)
    unit.SetOwnerNumber(owner_number)
    unit.SetUnitType(name)
    return unit

def CreateUnit(name, position=vec3_origin, angles=None, owner_number=0, keyvalues=None, fnprespawn=None):
    """ Creates an unit at the specified position.
    
        Args:
            name (str): Unit name (i.e. UnitInfo.name)
            position (Vector): Position around which the unit will be spawned
            
        Kwargs:
            angles (QAngle): The spawning angle of the unit. When None, the unit is spawned at 
              a random angle.
            owner_number (int): The owner of the unit
            keyvalues (KeyValues): Optional KeyValues to be applied to the unit
            fnprespawn (method): Optional method to be called before spawning the unit
    """
    unit = CreateUnitNoSpawn(name, owner_number)
    if not unit:
        return None # CreateEntityByName will print the warning
    if keyvalues:
        for k, v in keyvalues.items():
            unit.KeyValue(k, v)
    if fnprespawn:
        fnprespawn(unit)
    unit.SetAbsOrigin(position)
    if angles is None or not unit.unitinfo.requirerotation:
        angles = QAngle(0, 0, 0)
    unit.SetAbsAngles(angles)
    DispatchSpawn(unit)
    unit.Activate() 
    if unit.unitinfo.oncreatedroptofloor:
        # Must float above the ground a bit, otherwise we might fall through the ground
        unit.SetAbsOrigin(unit.GetAbsOrigin() + Vector(0, 0, 64))
        UTIL_DropToFloor(unit, MASK_NPCSOLID_BRUSHONLY)
    if unit.unitinfo.zoffset:
        unit.SetAbsOrigin(unit.GetAbsOrigin() + Vector(0, 0, unit.unitinfo.zoffset))
    return unit


def CreateUnitFancy(name, position, owner_number=0, startradius=0, maxradius=None, angles=None, keyvalues=None, fnprespawn=None):
    """ Creates an unit around the specified position in a fancy way.
    
        This method will automatically try to find a nice and valid position for the unit.
        Furthermore the unit is spawned with random angles.
        
        This method is used in the *unit_create* command.
        
        Args:
            name (str): Unit name (i.e. UnitInfo.name)
            position (Vector): Position around which the unit will be spawned
            
        Kwargs:
            owner_number (int): The owner of the unit
            startradius (float): Start search radius for placing the unit around the position
            maxradius (float): The max radius from position at which the unit can be spawned
            angles (QAngle): The spawning angle of the unit. When None, the unit is spawned at 
                             a random angle.
            keyvalues (KeyValues): Optional KeyValues to be applied to the unit
            fnprespawn (method): Optional method to be called before spawning the unit
    """
    if not angles:
        angles = QAngle(0, 0, 0)
        angles.y = random.uniform(0, 360)
    unit = CreateUnitNoSpawn(name, owner_number)
    if not unit:
        return
    if keyvalues:
        for k, v in keyvalues.items():
            unit.KeyValue(k, v)
    if fnprespawn:
        fnprespawn(unit)
    unitinfo = unit.unitinfo
    if unitinfo.requirerotation: unit.SetAbsAngles(angles)
    position = Vector(position)
    if unitinfo.placeatmins:
        position.z += -unitinfo.mins.z + unitinfo.zoffset
        mins = unitinfo.mins
        maxs = unitinfo.maxs
    else:
        position.z += unitinfo.zoffset
        mins = Vector(unitinfo.mins.x, unitinfo.mins.y, 0)
        maxs = unitinfo.maxs
    info = UTIL_FindPosition(FindPositionInfo(position, mins, maxs, startradius, maxradius, ignore=unit))
    if not info.success:
        unit.Remove()
        PrintWarning('CreateUnitFancy: failed to place unit\n')
        return
    position = info.position
    unit.SetAbsOrigin(position) 
    DispatchSpawn(unit)
    unit.Activate() 
    if unit.unitinfo.oncreatedroptofloor:
        unit.SetAbsOrigin(unit.GetAbsOrigin() + Vector(0,0,64)) # Must float above the ground a bit, otherwise we might fall through the ground
        UTIL_DropToFloor(unit, MASK_NPCSOLID_BRUSHONLY)
    if unitinfo.zoffset:
        unit.SetAbsOrigin(unit.GetAbsOrigin()+Vector(0,0,unit.unitinfo.zoffset))
    return unit


def PlaceUnit(unit, testposition, startradius=0, maxradius=None):
    unitinfo = unit.unitinfo
    position = Vector(testposition)
    if unitinfo.placeatmins:
        position.z += -unitinfo.mins.z + unitinfo.zoffset
        mins = unitinfo.mins
        maxs = unitinfo.maxs
    else:
        position.z += unitinfo.zoffset
        mins = Vector(unitinfo.mins.x, unitinfo.mins.y, 0)
        maxs = unitinfo.maxs
    info = UTIL_FindPosition(FindPositionInfo(position, mins, maxs, startradius, maxradius, ignore=unit))
    if not info.success:
        PrintWarning('PlaceUnit: failed to place unit\n')
        return False
        
    # Set position, drop to floor if needed
    if unit.unitinfo.oncreatedroptofloor:
        unit.SetAbsOrigin(info.position + Vector(0,0,64)) # Must float above the ground a bit, otherwise we fall through the ground
        UTIL_DropToFloor(unit, MASK_NPCSOLID_BRUSHONLY)
    else:
        unit.SetAbsOrigin(info.position)
        
    # Add zoffset if specified
    if unitinfo.zoffset:
        unit.SetAbsOrigin(unit.GetAbsOrigin()+Vector(0,0,unit.unitinfo.zoffset))
    return True


def CreateUnitsInArea(unit_name, origin, mins, maxs, z, amount, ownernumber):
    """ Creates the given number of units in an area specified by origin, mins and maxs.
    
        Uses the method CreateUnitFancy for unit creation. The positions are random.
    """
    ul = []
    mins = origin + mins
    maxs = origin + maxs
    for i in range(0, amount):
        un = unit_name if type(unit_name) != list else random.choice(unit_name)
        position = Vector(random.uniform(mins.x, maxs.x), random.uniform(mins.y, maxs.y), z)
        ul.append(CreateUnitFancy(un, position, ownernumber))
    return ul

    
if isserver:
    def PrecacheUnit(name):
        """ Precaches an unit. """
        if isunitprecached[name]:
            return

        unit = CreateUnitNoSpawn(name)
        if not unit:
            return
        unit.Precache()
        UTIL_RemoveImmediate(unit)
        isunitprecached[name] = True
else:
    def PrecacheUnit(name):
        pass


@receiver(postlevelshutdown)
def LevelInit(sender, **kwargs):
    global isunitprecached, unitlist, unitlistpertype
    # Reset precached
    isunitprecached.clear()
    
    # Ensure unitlist is empty
    unitlist.clear()
    unitlistpertype.clear()
    unitpopulationcount.clear()


def GetUnitInfo(unit_name, fallback=UnitFallBackInfo):
    """ Returns the information object for a given unit. """
    return dbunits.get(unit_name, fallback)

#       
# Unit create command
#
if isserver:
    @concommand('unit_create', 'Create an unit at the mouse cursor', 
                completionfunc=AutoCompletion(lambda: dbunits.keys()))
    def cc_unit_create(args):
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command unit_create in multiplayer, unless the server has sv_cheats set to 1.")
            return
        if args.ArgC() < 2:
            print('unit_create: not enough arguments')
            return
        player = UTIL_GetCommandClient()
        owner = int(args[2]) if len(args) > 2 else player.GetOwnerNumber()
        if owner == -1:
            owner = player.GetOwnerNumber()
        n = int(args[3]) if len(args) > 3 else 1
        for i in range(0, n):
            CreateUnitFancy(args[1], player.GetMouseData().groundendpos, owner) 

#
# List classes
#        
class UnitList(list):
    def __getitem__(self, index):
        return super().__getitem__(index)()
        
    def __iter__(self):
        for ref in list.__iter__(self):
            yield ref()
            
    def copy(self):
        # De-weakref them
        return [unit for unit in self]


def CreateUnitList():
    """ Creates a list of the format: [owner][units]. """
    return defaultdict(UnitList)


def CreateUnitListPerType():
    """ Creates a list of the format: [owner][type][units]. """
    return defaultdict(lambda : defaultdict(UnitList))


class UnitListHandle(object):
    def __init__(self, unit, unitlist, startdisabled=True):
        super().__init__()
        self.unitlist = unitlist
        self.disabled = startdisabled
        self.wrunit = weakref.ref(unit)
        
    def Update(self, ownernumber):
        if self.disabled:
            self.ownernumber = ownernumber
            return
        
        if self.ownernumber == ownernumber:
            return
        
        # Remove from old list if it doesn't matches
        if self.ownernumber != -1 and self.ownernumber != ownernumber:
            self.unitlist[self.ownernumber].remove(self.wrunit)
        
        # Add to new list
        self.ownernumber = ownernumber
        self.unitlist[self.ownernumber].append(self.wrunit)
        
    def Disable(self):
        if self.disabled:
            return
        self.disabled = True
        
        if self.ownernumber != -1:
            self.unitlist[self.ownernumber].remove(self.wrunit)
        self.ownernumber = -1
        
    def Enable(self):
        if not self.disabled:
            return
        self.disabled = False
        ownernumber = self.ownernumber
        self.ownernumber = -1
        self.Update(ownernumber)
        
    disabled = BooleanField(value=True)
    ownernumber = IntegerField(value=-1)


class UnitListPerTypeHandle(object):
    def __init__(self, unit, unitpertypelist, startdisabled=True):
        super().__init__()
        self.unitpertypelist = unitpertypelist
        self.disabled = startdisabled
        self.wrunit = weakref.ref(unit)
        
    def Update(self, ownernumber, unittype):
        if self.disabled:
            self.ownernumber = ownernumber
            self.unittype = unittype
            return
            
        if self.unittype == unittype and self.ownernumber == ownernumber:
            return
            
        # Remove from old list if it doesn't matches
        if (self.unittype != '' or self.ownernumber != -1) and (self.unittype != unittype or self.ownernumber != ownernumber):
            self.unitpertypelist[self.ownernumber][self.unittype].remove(self.wrunit)
        
        # Add to new list
        self.unittype = unittype
        self.ownernumber = ownernumber
        self.unitpertypelist[self.ownernumber][self.unittype].append(self.wrunit)
        
    def Disable(self):
        if self.disabled:
            return
        self.disabled = True
        
        if self.unittype != '' or self.ownernumber != -1:
            self.unitpertypelist[self.ownernumber][self.unittype].remove(self.wrunit)
        self.unittype = ''
        self.ownernumber = -1
        
    def Enable(self):
        if not self.disabled:
            return
        self.disabled = False
        unittype = self.unittype
        ownernumber = self.ownernumber
        self.unittype = ''
        self.ownernumber = -1
        self.Update(ownernumber, unittype)
        
    disabled = BooleanField(value=True)
    ownernumber = IntegerField(value=-1)
    unittype = StringField(value='')


#
# The global list of units for each player
#        
unitlist = defaultdict(list)
unitlistpertype = defaultdict(lambda : defaultdict(list))
unitpopulationcount = defaultdict(lambda : 0)


def AddUnit(unit):
    h = unit.GetHandle()
    unitlist[unit.GetOwnerNumber()].append(h)
    unitlistpertype[unit.GetOwnerNumber()][unit.GetUnitType()].append(h)
    unitpopulationcount[unit.GetOwnerNumber()] += unit.population


def RemoveUnit(unit):
    try:
        h = unit.GetHandle()
        unitlist[unit.GetOwnerNumber()].remove(h)
        unitlistpertype[unit.GetOwnerNumber()][unit.GetUnitType()].remove(h)
        unitpopulationcount[unit.GetOwnerNumber()] -= unit.population
    except ValueError:
        PrintWarning('%s.RemoveUnit: Failed to remove %s from unit list %d (idx %d, serial %d)\n' % 
            ('CLIENT' if isclient else 'SERVER', unit, unit.GetOwnerNumber(), h.GetEntryIndex(), h.GetSerialNumber()))


def ChangeUnit(unit, oldownernumber):
    h = unit.GetHandle()
    try:
        unitlist[oldownernumber].remove(h)
        unitlist[unit.GetOwnerNumber()].append(h)
       
        unitlistpertype[oldownernumber][unit.GetUnitType()].remove(h)
        unitlistpertype[unit.GetOwnerNumber()][unit.GetUnitType()].append(h)
        
        unitpopulationcount[oldownernumber] -= unit.population
        unitpopulationcount[unit.GetOwnerNumber()] += unit.population
    except ValueError:
        PrintWarning('%s.ChangeUnit: Failed to remove %s from unit list %d (idx %d, serial %d)\n' % (
            'CLIENT' if isclient else 'SERVER', unit, oldownernumber, h.GetEntryIndex(), h.GetSerialNumber()))


def CountUnits(ownernumber):
    return len(unitlist[ownernumber])


def ChangeUnitType(unit, oldtype):
    h = unit.GetHandle()
    if oldtype:
        unitlistpertype[unit.GetOwnerNumber()][oldtype].remove(h)
    unitlistpertype[unit.GetOwnerNumber()][unit.GetUnitType()].append(h)


def RefreshUnitList():
    """ Fixes the global unit list when it contains invalid unit handles. 
        Only for development (used after the class def of an entity changed). """
    newunitlist = defaultdict(set)
    newunitpopulationcount = defaultdict(lambda : 0)
    for ownernumber, ul in unitlist.items():
        for unit in ul:
            if unit:
                newunitlist[unit.GetOwnerNumber()].append(unit.GetHandle())
                newunitpopulationcount[unit.GetOwnerNumber()] += unit.population
    unitlist.clear()
    unitlist.update(newunitlist)
    unitpopulationcount.clear()
    unitpopulationcount.update(newunitpopulationcount)


def VerifyUnitList():
    for ownernumber, ul in unitlist.items():
        for unit in ul:
            assert(unit != None)


def KillAllUnits():
    for ownernumber, ul in unitlist.items():
        for unit in list(ul):
            unit.Remove()
    RefreshUnitList()

#
# Per player population cap
#
playerpopulationcap = defaultdict(lambda : 0)


def AddPopulation(ownernumber, pop):
    """ Adds population to the specified ownernumber. """
    assert(isserver)
    playerpopulationcap[ownernumber] += pop
    SendPopToClient(ownernumber)


def RemovePopulation(ownernumber, pop):
    """ Removes population from the specified ownernumber. """
    assert(isserver)
    playerpopulationcap[ownernumber] -= pop
    SendPopToClient(ownernumber)


def GetMaxPopulation(ownernumber):
    """ Returns the max population for the specified ownernumber. """
    pop = playerpopulationcap[ownernumber]
    return min(pop, sv_unitlimit.GetInt())


@usermessage(messagename='cupdpop')
def ClientUpdatePopulation(ownernumber, pop, **kwargs):
    playerpopulationcap[ownernumber] = pop


def SendPopToClient(ownernumber):
    players = UTIL_ListPlayersForOwnerNumber(ownernumber)
    filter = CRecipientFilter()
    filter.MakeReliable()
    [filter.AddRecipient(player) for player in players]
    ClientUpdatePopulation(ownernumber, playerpopulationcap[ownernumber], filter=filter)


# Save/restore of resources
@receiver(saverestore_save)
def SavePopulationCap(fields, *args, **kwargs):
    for owner, popcap in playerpopulationcap.items():
        fields['popcap_%d' % (owner)] = str(popcap)


@receiver(saverestore_restore)
def RestorePopulationCap(fields, *args, **kwargs):
    popcapmatcher = re.compile('popcap_(?P<owner>\d+)')
    
    for name, value in fields.items():
        match = popcapmatcher.match(name)
        if not match:
            continue
        owner = int(match.group('owner'))
        playerpopulationcap[owner] = int(value)
        DevMsg(1, 'Restoring population of owner %d to value %d\n' % (owner, int(value)))


if isserver:
    @receiver(prelevelinit)
    def ResetPopulation(**kwargs):
        DevMsg(1, 'Resetting population cap\n')
        playerpopulationcap.clear()


    @receiver(clientactive)
    def NewClient(client, **kwargs):
        filter = CSingleUserRecipientFilter(client)
        filter.MakeReliable()
        ClientUpdatePopulation(client.GetOwnerNumber(), playerpopulationcap[client.GetOwnerNumber()], filter=filter)


    @receiver(playerchangedownernumber)
    def PlayerChangedOwnerNumber(player, oldownernumber, **kwargs):
        if player.IsConnected():
            filter = CSingleUserRecipientFilter(player)
            filter.MakeReliable()
            ClientUpdatePopulation(player.GetOwnerNumber(), playerpopulationcap[player.GetOwnerNumber()], filter=filter)


if isclient:
    @receiver(playerchangedcolor)
    def PlayerColorChanged(ownernumber, oldcolor, **kwargs):
        for unit in unitlist[ownernumber]:
            # Wrap in try/catch in case it contains invalid/dead units
            try:
                unit.OnTeamColorChanged()
            except:
                pass
