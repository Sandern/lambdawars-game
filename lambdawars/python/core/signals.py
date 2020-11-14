"""
Game signals.
"""
from .dispatch import Signal
from collections import defaultdict
from srcbuiltins import RegisterPerFrameMethod

def FireSignalRobust(s, **kwargs):
    """ Fires the signal directly with the provided arguments.
    
        Prints any exception as a warning.
    """
    responses = s.send_robust(None, **kwargs)
    for r in responses:
        if isinstance(r[1], Exception):
            PrintWarning('Error in receiver %s (module: %s): %s\n' % (r[0], r[0].__module__, r[1]))
            
            
__delayedsignals = set()
def ScheduleFireSignalRobust(s):
    """ Delays firing the signal to the next frame, bundling the
        same signals. The signal can't have arguments.
    """
    __delayedsignals.add(s)
    
def FireScheduledSignals():
    """ Fires any signal pending. """
    try:
        for s in __delayedsignals:
            FireSignalRobust(s)
        __delayedsignals.clear()
    except e:
        __delayedsignals.clear()
        PrintWarning('%s\n' % (e))
RegisterPerFrameMethod(FireScheduledSignals)

LevelInitSignal = Signal
            
# The level signals are send from src_python.cpp.
# Send at level initialization before entities are spawned
prelevelinit = LevelInitSignal()
map_prelevelinit = defaultdict(lambda : LevelInitSignal())

# Send at level initialization after entities are spawned
postlevelinit = LevelInitSignal()
map_postlevelinit = defaultdict(lambda : LevelInitSignal())

# Send at level shutdown before entities are removed
prelevelshutdown = Signal()
map_prelevelshutdown = defaultdict(lambda : Signal())

# Send at level shutdown after entities are removed
postlevelshutdown = Signal()
map_postlevelshutdown = defaultdict(lambda : Signal())

# Called before shutting down
preshutdown = Signal()

if isserver:
    # Send when a new client connected
    clientactive = Signal(providing_args=['client'])
    map_clientactive = defaultdict(lambda : Signal(providing_args=['client']))
else:
    # Fired after changing the config in the keyboard page
    clientconfigchanged = Signal(providing_args=[])
    # Fired when client receives chat
    receiveclientchat = Signal(providing_args=['playerindex', 'filter', 'msg'])
    # Fire when a client wants to start chat. Only the main chat hud element should really respond to this.
    startclientchat = Signal(providing_args=['mode'])
    
# Save restore system
saverestore_save = Signal(providing_args=['fields'])
saverestore_restore = Signal(providing_args=['fields'])

# A player spawned
playerspawned = Signal(providing_args=["player"])
    
# Called before initializing new gamerules
preinitgamerules = Signal(providing_args=['gamerules'])
# Called after initializing new gamerules
postinitgamerules = Signal(providing_args=['gamerules'])
# Called when a game ends (Annihilation, Mission, etc)
endgame = Signal(providing_args=['gamerules', 'winners', 'losers'])
map_endgame = defaultdict(lambda : LevelInitSignal(providing_args=['gamerules', 'winners', 'losers']))
# Called when a game starts
startgame = Signal(providing_args=['gamerules'])

# Send when a player changed owner number
playerchangedownernumber = Signal(providing_args=["player", "oldownernumber"])
map_playerchangedownernumber = defaultdict(lambda : Signal(providing_args=["player", "oldownernumber"]))

# Send when the player changes faction
playerchangedfaction = Signal(providing_args=["player", "oldfaction"])

# Send when player team color changes
playerchangedcolor = Signal(providing_args=["ownernumber", "oldcolor"])

# Gamepackage load/unload
gamepackageloaded = Signal(providing_args=["packagename"])
gamepackageunloaded = Signal(providing_args=["packagename"])

# List of button signals
keyspeed = Signal(providing_args=["player", "state"])
keyduck = Signal(providing_args=["player", "state"])

# Unit/selection/order related signals
pre_orderunits = Signal(providing_args=["player"])
post_orderunits = Signal(providing_args=["player"])
selectionchanged = Signal(providing_args=["player"])

unitselected = Signal(providing_args=["player", "unit"])
unitdeselected = Signal(providing_args=["player", "unit"])

# Killed signals. One general signal, and two signals by the unit type of killed unit and by unit type of attacker
# The specific ones are mainly used by achievements.
unitkilled = Signal(providing_args=['unit', 'dmginfo'])
unitkilled_by_victim = defaultdict(lambda: Signal(providing_args=['unit', 'dmginfo']))
unitkilled_by_inflictor = defaultdict(lambda: Signal(providing_args=['unit', 'dmginfo']))
unitkilled_by_attacker = defaultdict(lambda: Signal(providing_args=['unit', 'dmginfo']))

# Unit spawned (any type, always fired on creation)
unitspawned = Signal(providing_args=['unit'])
# Called on unit entity being removed (not the same as killed)
unitremoved = Signal(providing_args=['unit'])

groupchanged = Signal(providing_args=["player", "group"])

garrisonchanged = Signal(providing_args=['building'])

# Hud signals
if isclient:
    # Indicates the player went into a sub menu of abilities
    abilitymenuchanged = Signal(providing_args=[])
    # General signal that indicates the units or abilities changed.
    refreshhud = Signal(providing_args=[])
    # A player fired a ping signal on the minimap
    firedping = Signal(providing_args=['pos', 'color'])
    # Removes unit from minimap, rechecks conditions and reinserts if allowed
    minimapupdateunit = Signal(providing_args=['unit'])

# Send when player changes unit control
playercontrolunit = Signal(providing_args=["player", "unit"])
playerleftcontrolunit = Signal(providing_args=["player", "unit"])

if isserver:
    # Fired when the player resources changed (which means resource might be added or removed)
    resourceupdated = Signal(providing_args=['ownernumber', 'type', 'amount'])

    # Fired when the player collected resources. 
    # Examples: control points adds resource or scrap is collected
    # Excludes refunds
    resourcecollected = Signal(providing_args=['owner', 'type', 'amount'])

    # Fired when a player spent resources.
    # Examples: producing units, placing buildings
    resourcespent = Signal(providing_args=['owner', 'type', 'amount', 'resource_category'])
    
    # Construction of a building started, canceled or finished
    buildingstarted = Signal(providing_args=['building'])
    buildingcanceled = Signal(providing_args=['building'])
    buildingfinished = Signal(providing_args=['building'])
    
    # Unit changed owner
    unitchangedownernumber = Signal(providing_args=["unit", "oldownernumber"])
    
    # Control point was fortified
    # TODO: Move to wars_game package and define CPU player from there
    cp_fortified = Signal(providing_args=['building'])
    cp_fortificationdestroyed = Signal(providing_args=['building'])
    
    # Production of an ability started at a building factory
    productionstarted = Signal(providing_args=['building', 'info'])
    
    # On player defeated
    playerdefeated = Signal(providing_args=['ownernumber'])
    
    # Stub
    resourceset = None
else:
    # Fired when the player resources changed
    resourceset = Signal(providing_args=['ownernumber', 'type', 'amount'])
    
# Fired just before loading the nav mesh. Can be used to build a custom nav mesh.
navmesh_preload = Signal(providing_args=[])
# Fired when the nav mesh is loaded
navmeshloaded = Signal(providing_args=[])
# A way to post process the map mesh for nav mesh constructions ingame
recast_mapmesh_postprocess = Signal(providing_args=['mapmesh', 'bounds'])

# Called on ability completion
abilitycompleted = Signal(providing_args=['ability'])
# Called on ability completion, but fired by name
abilitycompleted_by_name = defaultdict(lambda : Signal(providing_args=['ability']))
# Called on ability cancel
abilitycanceled = Signal(providing_args=['ability'])
# Called on ability cancel, but fired by name
abilitycanceled_by_name = defaultdict(lambda : Signal(providing_args=['ability']))

# Editor map load event
editormapchanged = Signal()
# Editor selection changed
editorselectionchanged = Signal()

# Client lobby game server accept/denied signals
lobby_gameserver_accept = Signal(providing_args=['publicip', 'gameport', 'serversteamid'])
lobby_gameserver_denied = Signal()
# Fired by gamerules (client) after a Steam lobby started game has ended
lobby_gameended = Signal('lobbysteamid')
# Receiving pong from other client after sending a ping message
lobby_received_pong = Signal(providing_args=['steamidremote'])
# Received the match uuid. Store it in the lobby data
lobby_match_uuid = Signal(providing_args=['match_uuid'])

# Steam
steam_serversdisconnected = Signal()
steam_serverconnectfailure = Signal()
steam_serversconnected = Signal()

steam_p2p_connectfail = Signal(providing_args=['steamidremote', 'p2psessionerror'])

mm_error = Signal(providing_args=['event'])

if isclient:
    # Game UI
    gameui_inputlanguage_changed = Signal()

'''
# Examples of several signals:
from core.dispatch import receiver

@receiver(prelevelinit)
def on_prelevelinit(sender, **kwargs):
    print "Pre Level init callback!"
    
@receiver(map_prelevelinit['wmp_forest'])
def on_prelevelinit(sender, **kwargs):
    print "Pre Level init callback wmp_forest!"
    
@receiver(postlevelinit)
def on_postlevelinit(sender, bla, **kwargs):
    print "Post Level init callback!"
    
@receiver(prelevelshutdown)
def on_prelevelshutdown(sender, **kwargs):
    print "Pre Level shutdown callback!"
    
@receiver(postlevelshutdown)
def on_postlevelshutdown(sender, **kwargs):
    print "Post Level shutdown callback!"
    
if isserver:
    @receiver(clientactive)
    def on_clientactive(sender, client, **kwargs):
        print "client active %s" % (client)
    
@receiver(playerchangedownernumber)
def on_playerchangedownernumber(sender, player, oldownernumber, **kwargs):
    print "on_playerchangedownernumber %s %s" % (player, oldownernumber)
'''