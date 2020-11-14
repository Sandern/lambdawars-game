from gameinterface import ConVar, FCVAR_CHEAT, FCVAR_REPLICATED
import math
from core.units import unitlistpertype

cheatflags = 0 # FCVAR_CHEAT

# ConVars
if isserver:
    sk_portal_frequency = ConVar('sk_portal_frequency', '30.0', cheatflags)

    sk_creature_limit = ConVar('sk_creature_limit', '30', cheatflags)

    sk_marine_invade_init_time = ConVar('sk_marine_invade_init_time', '400.0', cheatflags)
    sk_marine_invade_interval_min = ConVar('sk_marine_invade_interval_min', '120.0', cheatflags)
    sk_marine_invade_interval_max = ConVar('sk_marine_invade_interval_max', '300.0', cheatflags)

    sk_payday_frequency = ConVar('sk_payday_frequency', '210.0', cheatflags)

# Common methods
def nearestkeybydist(origxy, listxy):
    ''' Given a list of keys and one test key, return the nearest key in the list. '''
    return min(listxy, key=(lambda x: (origxy[0]-x[0])**2+(origxy[1]-x[1])**2))
    
def keydist(key1, key2):
    return math.sqrt((key1[0]-key2[0])**2+(key1[1]-key2[1])**2)
    
        
def GetDungeonHeart(ownernumber):
    try:
        heart = unitlistpertype[ownernumber]['dk_heart'][0]
    except (IndexError, KeyError):
        heart = None
    return heart
    
def GetCreatureCount(ownernumber):
    try:
        portal = unitlistpertype[ownernumber]['dk_portal'][0]
    except (IndexError, KeyError):
        portal = None
    if portal:
        return portal.CountCreatures()
    return 0
    
def TestSwapMinMax(testkeymin, testkeymax):
    keymin = [0,0]
    keymax = [0,0]
    if testkeymin[0] <= testkeymax[0]:
        keymin[0] = testkeymin[0]
        keymax[0] = testkeymax[0] 
    else:
        keymin[0] = testkeymax[0] 
        keymax[0] = testkeymin[0] 
    if testkeymin[1] <= testkeymax[1]:
        keymin[1] = testkeymin[1]
        keymax[1] = testkeymax[1] 
    else:
        keymin[1] = testkeymax[1] 
        keymax[1] = testkeymin[1] 
        
    return tuple(keymin), tuple(keymax)