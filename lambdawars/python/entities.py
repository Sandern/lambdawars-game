from _entitiesmisc import *
from _entities import *
from fields import SetupClassFields, SetupInputMethods

# Alias for entity list
if isserver:
    gEntList = entlist
    entitylist = entlist
else:
    entlist = entitylist = None
    
# Lists of all entity classes
if isclient:
    list_ents = [ 
        C_BaseEntity,
        C_BaseAnimating,
        C_BaseAnimatingOverlay,
        C_BaseFlex,
        C_BaseCombatCharacter,
        C_BaseGrenade,
        C_BasePlayer,
        C_HL2WarsPlayer,
        C_UnitBase,
        C_FuncUnit,
        C_PlayerResource,
        C_Sprite,
        C_Beam,
        C_BaseCombatWeapon,
        C_WarsWeapon,
        C_FuncBrush,
        C_BaseFuncMapBoundary,
        C_BaseToggle,
        C_BaseTrigger,
        C_BreakableProp,
    ]
    
    # List of aliases
    CBaseEntity = C_BaseEntity
    CBaseAnimating = C_BaseAnimating
    CBaseAnimatingOverlay = C_BaseAnimatingOverlay
    CBaseFlex = C_BaseFlex
    CBaseCombatCharacter = C_BaseCombatCharacter
    CBaseGrenade = C_BaseGrenade
    CBasePlayer = C_BasePlayer
    CHL2WarsPlayer = C_HL2WarsPlayer
    CUnitBase = C_UnitBase
    CFuncUnit = C_FuncUnit
    CPlayerResource = C_PlayerResource
    CSprite = C_Sprite
    CBeam = C_Beam
    CBaseCombatWeapon = C_BaseCombatWeapon
    CWarsWeapon = C_WarsWeapon
    CFuncBrush = C_FuncBrush
    CBaseFuncMapBoundary = C_BaseFuncMapBoundary
    CBaseToggle = C_BaseToggle
    CBaseTrigger = C_BaseTrigger
    CBreakableProp = C_BreakableProp
    
    # Server only, add an alias anyway (for convenience)
    CPointEntity = CBaseEntity
    
else:
    list_ents = [ 
        CBaseEntity, 
        CBaseAnimating, 
        CBaseAnimatingOverlay, 
        CBaseFlex, 
        CBaseCombatCharacter,
        CBaseGrenade,
        CBasePlayer,
        CHL2WarsPlayer,
        CUnitBase,
        CFuncUnit,
        CGib,
        CSprite,
        CSpriteTrail,
        CBeam,
        CPointEntity,
        CServerOnlyEntity,
        CServerOnlyPointEntity,
        CLogicalEntity,
        CFuncBrush,
        CBaseToggle,
        CBaseTrigger,
        CTriggerMultiple,
        CBaseCombatWeapon,
        CWarsWeapon,
        CBaseFuncMapBoundary,
        CBaseFilter,
        CBaseProp,
        CBreakableProp,
        CPhysicsProp,
        CRagdollProp,
        CEntityFlame,
    ]

# Friendly aliases
eventqueue = g_EventQueue if isserver else None
    
@classmethod    
def InitEntityClass(cls):
    """ Entity Class initializer, could be seen as a metaclass.
        It is called when the class is created and when a new map is loaded.
        Used for one time initializations per map.
    """
    SetupClassFields(cls)
    SetupInputMethods(cls)
    
# Bind the following methods to each entity class
for cls in list_ents:
    # InitEntityClass: Called on level initialization and on the first time the entity factory is initialized.
    cls.InitEntityClass = InitEntityClass
    
clstoclstype = {
    'CBaseEntity' : ('@PointClass', ['Targetname', 'Origin', 'Wars']),
    'CBaseAnimating' : ('@PointClass', ['prop_dynamic_base', 'Wars']),
    'CUnitBase' : ('@NPCClass', ['BaseUnit']),
    'CFuncUnit' : ('@SolidClass', ['Targetname', 'Origin', 'Wars', 'Parentname', 'RenderFields', 'Global', 'Inputfilter', 'EnableDisable', 'Shadow']),
    'CFuncBrush' : ('@SolidClass', ['Targetname', 'Parentname', 'Origin', 'RenderFields', 'Global', 'Inputfilter', 'EnableDisable', 'Shadow', 'Wars']),
    'CBaseFuncMapBoundary' : ('@SolidClass', ['Targetname', 'Parentname', 'Origin', 'RenderFields', 'Global', 'Inputfilter', 'EnableDisable', 'Shadow', 'Wars']),
    'CBaseTrigger' : ('@SolidClass', ['Targetname', 'Parentname', 'Origin', 'RenderFields', 'Global', 'Inputfilter', 'EnableDisable', 'Shadow', 'Wars']),
    'CBaseFilter' : ('@FilterClass', ['BaseFilter', 'Wars']),
}
def DetermineClsType(cls):
    if cls.__name__ in clstoclstype:
        return clstoclstype[cls.__name__]
    for basecls in cls.__bases__:
        rs = DetermineClsType(basecls)
        if rs: 
            return rs
    return None

def networked(cls):
    """ Makes the class networked, which can serve as a base for entities which don't need to be
        networked. """
    if 'networkinst' not in cls.__dict__:
        networkname = '%s.__%s' % (cls.__module__, cls.__name__)
        cls.networkinst = NetworkedClass(networkname, cls)
    return cls
    
def entity( clsname, 
            networked=False, 
            helpstring='',
            clstype='',
            entityextraproperties='',
            base=[],
            studio='',
            iconsprite='',
            cylinder=[],
            color='',
            size='',
            cppproperties='',
            nofgdentry=False):
    """ Decorator for turning a class into an entity.
        The class entity must be derived from CBaseEntity. """
    def wrapcls(cls):
        # FIXME: This creates a circular reference between the class and factory/network instance
        #        Although new factories will remove the old factories, it does not clean up nicely yet.
        factoryname = 'factory__%s' % (clsname)
        factory = EntityFactory(clsname, cls)
        factory.entityname = clsname
        factory.clstype = clstype
        factory.entityextraproperties = entityextraproperties
        factory.cppproperties = cppproperties
        factory.helpstring = helpstring
        factory.nofgdentry = nofgdentry
        
        factory.fgdbase = base
        factory.fgdstudio = studio
        factory.fgdiconsprite = iconsprite
        factory.fgdcylinder = cylinder
        factory.fgdcolor = color
        factory.fgdsize = size
        
        setattr(cls, factoryname, factory)
        
        if not factory.clstype:
            info = DetermineClsType(cls)
            if info: 
                factory.clstype = info[0]
        else: 
            info = None
        
        if not factory.fgdbase:
            if info: 
                factory.fgdbase = info[1]

        if networked and 'networkinst' not in cls.__dict__:
            networkname = '%s.__%s' % (cls.__module__, cls.__name__)
            cls.networkinst = NetworkedClass(networkname, cls)
            
        # Initialize the class so the fields are setup
        cls.InitEntityClass()
            
        return cls
    return wrapcls

# Entity Flags
EFL_KILLME = (1<<0) # This entity is marked for death -- This allows the game to actually delete ents at a safe time
EFL_DORMANT = (1<<1) # Entity is dormant no updates to client
EFL_NOCLIP_ACTIVE = (1<<2) # Lets us know when the noclip command is active.
EFL_SETTING_UP_BONES = (1<<3) # Set while a model is setting up its bones.
EFL_KEEP_ON_RECREATE_ENTITIES = (1<<4) # This is a special entity that should not be deleted when we restart entities only

#Tony; BUG?? I noticed this today while performing stealz on flag 16! look at the definition of the flag above...
EFL_HAS_PLAYER_CHILD= (1<<4) # One of the child entities is a player.

EFL_DIRTY_SHADOWUPDATE = (1<<5) # Client only- need shadow manager to update the shadow...
EFL_NOTIFY = (1<<6) # Another entity is watching events on this entity (used by teleport)

# The default behavior in ShouldTransmit is to not send an entity if it doesn't
# have a model. Certain entities want to be sent anyway because all the drawing logic
# is in the client DLL. They can set this flag and the engine will transmit them even
# if they don't have a model.
EFL_FORCE_CHECK_TRANSMIT = (1<<7)

EFL_BOT_FROZEN = (1<<8) # This is set on bots that are frozen.
EFL_SERVER_ONLY = (1<<9) # Non-networked entity.
EFL_NO_AUTO_EDICT_ATTACH = (1<<10) # Don't attach the edict; we're doing it explicitly

# Some dirty bits with respect to abs computations
EFL_DIRTY_ABSTRANSFORM = (1<<11)
EFL_DIRTY_ABSVELOCITY = (1<<12)
EFL_DIRTY_ABSANGVELOCITY = (1<<13)
EFL_DIRTY_SURROUNDING_COLLISION_BOUNDS = (1<<14)
EFL_DIRTY_SPATIAL_PARTITION = (1<<15)
EFL_PLUGIN_BASED_BOT = (1<<16)  #this is set on plugin bots so that if any games include their own bot code they won't affect plugin bots.
EFL_IN_SKYBOX = (1<<17) # This is set if the entity detects that it's in the skybox.
       # This forces it to pass the "in PVS" for transmission.
EFL_USE_PARTITION_WHEN_NOT_SOLID = (1<<18) # Entities with this flag set show up in the partition even when not solid
EFL_TOUCHING_FLUID = (1<<19) # Used to determine if an entity is floating

# FIXME: Not really sure where I should add this...
EFL_IS_BEING_LIFTED_BY_BARNACLE = (1<<20)
EFL_NO_ROTORWASH_PUSH = (1<<21)  # I shouldn't be pushed by the rotorwash
EFL_NO_THINK_FUNCTION = (1<<22)
EFL_NO_GAME_PHYSICS_SIMULATION = (1<<23)

EFL_CHECK_UNTOUCH = (1<<24)
EFL_DONTBLOCKLOS = (1<<25)  # I shouldn't block NPC line-of-sight
EFL_DONTWALKON = (1<<26)  # NPC;s should not walk on this entity
EFL_NO_DISSOLVE = (1<<27)  # These guys shouldn't dissolve
EFL_NO_MEGAPHYSCANNON_RAGDOLL = (1<<28) # Mega physcannon can't ragdoll these guys.
EFL_NO_WATER_VELOCITY_CHANGE = (1<<29) # Don't adjust this entity's velocity when transitioning into water
EFL_NO_PHYSCANNON_INTERACTION = (1<<30) # Physcannon can't pick these up or punt them
EFL_NO_DAMAGE_FORCES = (1<<31) # Doesn't accept forces from physics damage

# Transmit flags
FL_EDICT_FULLCHECK = (0<<0) # call ShouldTransmit() each time, this is a fake flag
FL_EDICT_ALWAYS = (1<<3)    # always transmit this entity
FL_EDICT_DONTSEND = (1<<4)  # don't transmit this entity
FL_EDICT_PVSCHECK = (1<<5)  # always transmit entity, but cull against PVS

# FOW Flags
FOWFLAG_HIDDEN = ( 1 << 0 ) # Do not draw when in the fog of war
FOWFLAG_NOTRANSMIT = ( 1 << 1 ) # Do not send data to the clients when in the fog of war (buildings are drawn but not updated for clients when in the fog of war) 
FOWFLAG_UPDATER = ( 1 << 2 )
FOWFLAG_INITTRANSMIT = ( 1 << 3 ) # Sends the initial location of the entity to each player (for neutral buildings)
FOWFLAG_KEEPCOLINFOW = ( 1 << 4 ) # Keep collision on client side even when in the fog of war (specified for neutral buildings)

FOWFLAG_UNITS_MASK = (FOWFLAG_HIDDEN|FOWFLAG_NOTRANSMIT|FOWFLAG_UPDATER)
FOWFLAG_BUILDINGS_MASK = (FOWFLAG_NOTRANSMIT|FOWFLAG_UPDATER)
FOWFLAG_BUILDINGS_NEUTRAL_MASK = (FOWFLAG_NOTRANSMIT|FOWFLAG_UPDATER|FOWFLAG_INITTRANSMIT|FOWFLAG_KEEPCOLINFOW)
FOWFLAG_ALL_MASK = (FOWFLAG_HIDDEN|FOWFLAG_NOTRANSMIT|FOWFLAG_UPDATER)

# Entity disolve types
ENTITY_DISSOLVE_NORMAL = 0
ENTITY_DISSOLVE_ELECTRICAL = 1
ENTITY_DISSOLVE_ELECTRICAL_LIGHT = 2
ENTITY_DISSOLVE_CORE = 3

# Density map constants (Use with SetDensityType)
DENSITY_GAUSSIAN = 0 # Use a 2d gaussian function. Sigma based on BoundingRadius. Use for simply objects.
DENSITY_GAUSSIANECLIPSE = 1 # Uses mins/maxs, for rectangle shaped objects (buildings, rectangle shaped crap).
DENSITY_NONE = 2

# BaseAnimating flags
BCF_NO_ANIMATION_SKIP = ( 1 << 0 ) # Do not allow PVS animation skipping (mostly for attachments being critical to an entity)
BCF_IS_IN_SPAWN = ( 1 << 1 ) # Is currently inside of spawn, always evaluate animations

# Beam flags
FBEAM_STARTENTITY = 0x00000001
FBEAM_ENDENTITY = 0x00000002
FBEAM_FADEIN = 0x00000004
FBEAM_FADEOUT = 0x00000008
FBEAM_SINENOISE = 0x00000010
FBEAM_SOLID = 0x00000020
FBEAM_SHADEIN = 0x00000040
FBEAM_SHADEOUT = 0x00000080
FBEAM_ONLYNOISEONCE = 0x00000100  # Only calculate our noise once
FBEAM_NOTILE = 0x00000200
FBEAM_USE_HITBOXES = 0x00000400  # Attachment indices represent hitbox indices instead when this is set.
FBEAM_STARTVISIBLE = 0x00000800  # Has this client actually seen this beam's start entity yet?
FBEAM_ENDVISIBLE = 0x00001000  # Has this client actually seen this beam's end entity yet?
FBEAM_ISACTIVE = 0x00002000
FBEAM_FOREVER = 0x00004000
FBEAM_HALOBEAM = 0x00008000  # When drawing a beam with a halo, don't ignore the segments and endwidth
FBEAM_REVERSED = 0x00010000
NUM_BEAM_FLAGS = 17 # KEEP THIS UPDATED!

# Tracer types
TRACER_NONE = 0
TRACER_LINE = 1
TRACER_RAIL = 2
TRACER_BEAM = 3
TRACER_LINE_AND_WHIZ = 4

# Density
DENSITY_GAUSSIAN = 0 # Use a 2d gaussian function. Sigma based on BoundingRadius.
DENSITY_GAUSSIANECLIPSE = 1 # Uses mins/maxs, for rectangle shaped objects (buildings).
DENSITY_NONE = 2 # Disables density map (default)

# Observer modes
OBS_MODE_NONE = 0	# not in spectator mode
OBS_MODE_DEATHCAM = 1	# special mode for death cam animation
OBS_MODE_FREEZECAM = 2	# zooms to a target, and freeze-frames on them
OBS_MODE_FIXED = 3		# view from a fixed camera position
OBS_MODE_IN_EYE = 4	# follow a player in first person view
OBS_MODE_CHASE = 5		# follow a player in third person view
OBS_MODE_ROAMING = 6	# free roaming

if isclient:
    # Transmit flags
    SHOULDTRANSMIT_START = 0  # The entity is starting to be transmitted (maybe it entered the PVS).
    
    SHOULDTRANSMIT_END = 1    # Called when the entity isn't being transmitted by the server.
                              # This signals a good time to hide the entity until next time
                              # the server wants to transmit its state.

# Trigger spawn flags
SF_TRIGGER_ALLOW_CLIENTS = 0x01 # Players can fire this trigger
SF_TRIGGER_ALLOW_NPCS = 0x02 # NPCS can fire this trigger
SF_TRIGGER_ALLOW_PUSHABLES = 0x04 # Pushables can fire this trigger
SF_TRIGGER_ALLOW_PHYSICS = 0x08 # Physics objects can fire this trigger
SF_TRIGGER_ONLY_PLAYER_ALLY_NPCS = 0x10 # *if* NPCs can fire this trigger, this flag means only player allies do so
SF_TRIGGER_ONLY_CLIENTS_IN_VEHICLES = 0x20 # *if* Players can fire this trigger, this flag means only players inside vehicles can 
SF_TRIGGER_ALLOW_ALL = 0x40 # Everything can fire this trigger EXCEPT DEBRIS!
SF_TRIGGER_ONLY_CLIENTS_OUT_OF_VEHICLES = 0x200 # *if* Players can fire this trigger, this flag means only players outside vehicles can 
SF_TRIG_PUSH_ONCE = 0x80 # trigger_push removes itself after firing once
SF_TRIG_PUSH_AFFECT_PLAYER_ON_LADDER = 0x100 # if pushed object is player on a ladder, then this disengages them from the ladder (HL2only)
SF_TRIG_TOUCH_DEBRIS = 0x400 # Will touch physics debris objects
SF_TRIGGER_ONLY_NPCS_IN_VEHICLES = 0X800 # *if* NPCs can fire this trigger, only NPCs in vehicles do so (respects player ally flag too)
SF_TRIGGER_PUSH_USE_MASS = 0x1000 # Correctly account for an entity's mass (CTriggerPush::Touch used to assume 100Kg)

#-----------------------------------------------------------------------------
# These are the various partition lists. Note some are server only, some
# are client only
#-----------------------------------------------------------------------------
PARTITION_ENGINE_SOLID_EDICTS = (1 << 0) # every edict_t that isn't SOLID_TRIGGER or SOLID_NOT (and static props)
PARTITION_ENGINE_TRIGGER_EDICTS = (1 << 1) # every edict_t that IS SOLID_TRIGGER
PARTITION_CLIENT_SOLID_EDICTS = (1 << 2)
PARTITION_CLIENT_RESPONSIVE_EDICTS = (1 << 3) # these are client-side only objects that respond to being forces, etc.
PARTITION_ENGINE_NON_STATIC_EDICTS = (1 << 4) # everything in solid & trigger except the static props, includes SOLID_NOTs
PARTITION_CLIENT_STATIC_PROPS = (1 << 5)
PARTITION_ENGINE_STATIC_PROPS = (1 << 6)
PARTITION_CLIENT_NON_STATIC_EDICTS = (1 << 7) # everything except the static props
PARTITION_CLIENT_TRIGGER_ENTITIES = (1 << 8) # client side prediction related triggers
PARTITION_CLIENT_IK_ATTACHMENT = (1 << 9) # Can be used as an IK attachment

# Helper functions
def FClassnameIs(entity, classname):
    if not entity:
        return False
    return entity.GetClassname() == classname

if isclient:
    # Send proxy stubs for on client
    class SendProxyBase(object): 
        pass
    class SendProxyOwnerOnly(SendProxyBase): 
        pass
    class SendProxyAlliesOnly(SendProxyBase): 
        pass
