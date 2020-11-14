from gameinterface import ConVar, FCVAR_NONE, FCVAR_REPLICATED, FCVAR_NOTIFY, FCVAR_ARCHIVE

# ConVars
if isserver:
    zm_trap_triggerrange = ConVar( "zm_trap_triggerrange", "96", FCVAR_NONE, "The range trap trigger points have.")
    zm_ambush_triggerrange = ConVar( "zm_ambush_triggerrange", "96", FCVAR_REPLICATED, "The range ambush trigger points have.")

    zm_spawndelay = ConVar("zm_spawndelay", "0.75", FCVAR_NOTIFY, "Delay between creation of zombies at zombiespawn.")

    zm_loadout_disable = ConVar("zm_loadout_disable", "0", FCVAR_NOTIFY, "If set to 1, any info_loadout entity will not hand out weapons. Not recommended unless you're intentionally messing with game balance and playing on maps that support self move.")

    zm_popcost_banshee = ConVar("zm_popcost_banshee", "4", FCVAR_NOTIFY | FCVAR_REPLICATED, "Population points taken up by banshees")
    zm_popcost_hulk = ConVar("zm_popcost_hulk", "3", FCVAR_NOTIFY | FCVAR_REPLICATED, "Population points taken up by hulks")
    zm_popcost_shambler = ConVar("zm_popcost_shambler", "1", FCVAR_NOTIFY | FCVAR_REPLICATED, "Population points taken up by shamblers")
    zm_popcost_immolator = ConVar("zm_popcost_immolator", "5", FCVAR_NOTIFY | FCVAR_REPLICATED, "Population points taken up by immolators")
    zm_popcost_drifter = ConVar("zm_popcost_drifter", "2", FCVAR_NOTIFY | FCVAR_REPLICATED, "Population points taken up by drifters")
    
    zm_zombiemax = ConVar("zm_zombiemax", "50", FCVAR_ARCHIVE|FCVAR_NOTIFY|FCVAR_REPLICATED, "Sets maximum population count the ZM is allowed to have active at once. Certain zombies count for more pop than others, see zm_popcost_shambler etc.")

# Global lists
zombietraps = []
zombiemastervisible = []

# Points    
HUMAN_WIN_SCORE = 50
HUMAN_LOSE_SCORE = 50

# Owner numbers
ON_SURVIVOR = 2
ON_ZOMBIEMASTER = 3

# Resource
RESOURCE_ZOMBIEPOOL = 'zombiepool'

# Models
ENTITY_MODEL_Z = "models/zombiespawner.mdl"
MANIPULATE_MODEL = "models/manipulatable.mdl"
TRAP_MODEL = "models/trap.mdl"

# Constants
# STODO: Remove these, shouldn't be needed
TYPE_SHAMBLER = 0,
TYPE_BANSHEE = 1,
TYPE_HULK = 2,
TYPE_DRIFTER = 3,
TYPE_IMMOLATOR = 4,

TYPE_TOTAL = 5,
TYPE_INVALID = 6

LO_IMPROVISED = 0
LO_SLEDGEHAMMER = 1
LO_PISTOL = 2
LO_SHOTGUN = 3
LO_RIFLE = 4
LO_MAC10 = 5
LO_REVOLVER = 6 
LO_MOLOTOV = 7
LO_WEAPONS_TOTAL = 8

TypeToName = [
    "npc_zombie",
    "npc_fastzombie",
    "npc_poisonzombie",
    "npc_dragzombie",
    "npc_burnzombie",
]

class ZombieCost:
    def __init__(self, a, b):
        self.resources = a
        self.population = b
