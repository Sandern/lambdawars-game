'''
A central module for dealing with hotkeys.
The main goal is how to deal with hotkeys for abilities 
since they change dynamically based on the unit selection.

The available hotkeys are bound in the default config, for example:
bind "a" "+hotkey_a"
bind "c" "+hotkey_c"
bind "d" "+hotkey_d"
bind "e" "+hotkey_e"
bind "f" "+hotkey_f"
bind "q" "+hotkey_q"
bind "r" "+hotkey_r"
bind "s" "+hotkey_s"
bind "v" "+hotkey_v"
bind "w" "+hotkey_w"
bind "x" "+hotkey_x"
bind "z" "+hotkey_z"
'''
import srcmgr
srcmgr.VerifyIsClient() # Only on client, sends commands to the server

from srcbuiltins import RegisterTickMethod
from entities import C_HL2WarsPlayer
from gameinterface import ConCommand, engine, ConVar, FCVAR_ARCHIVE, ConVarRef
from core.abilities import DoAbility, ClientDoAbility
from core.units import GetUnitInfo, NoSuchAbilityError
from core.signals import clientconfigchanged

import traceback 
import os

cl_active_config = ConVarRef('cl_active_config')

class BaseHotkeySystem(object):
    #: List of characters which are potentially bound to a hotkey.
    hotkeys_characters = [
        'q', 'w', 'e', 'r',
        'a', 's', 'd', 'f',
        'z', 'x', 'c', 'v',
    ]

    def __init__(self):
        # Create a ConCommand for each character
        self.hotkeys = {}
        for char in self.hotkeys_characters:
            down = ConCommand( "+hotkey_%s" % (char), self.HandleHotKeyIntern, "Hotkey %s" % (char) )
            up = ConCommand( "-hotkey_%s" % (char), self.HandleHotKeyIntern, "Hotkey %s" % (char) )
            self.hotkeys[char] = (down, up)
        
        clientconfigchanged.connect(self.ClientConfigChanged)
        
    def Destroy(self):
        self.hotkeys = {} # Release references to the system
        clientconfigchanged.disconnect(self.ClientConfigChanged)
        
    def ClientConfigChanged(self, *args, **kwargs):
        pass
            
    def HandleHotKeyIntern(self, args):
        command = args[0]
        char = command.split('_')[1]
        keydown = command[0] == '+'
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        # Hotkey is going to change, so clear old if any
        oldabi = self.activeability
        if self.activeability:
            self.activeability.hotkeysystem = None
            self.activeability = None
            
        self.ishotkeydown = keydown
            
        if not keydown:
            self.activehotkey = None
            self.activeabiinfo = None
            self.activeunittype = None
            if oldabi:
                oldabi.OnHotkeyReleased()
            return
        else:
            self.activehotkey = char
            self.activeabiinfo, self.activeunittype = self.GetAbilityForActiveHotkey()
                
        self.HandleHotKey(player, char)
            
    def HandleHotKey(self, player, char):
        print('Handling hotkey: %s' % (char))
        
    def GetHotkeyForAbility(self, abi_info, slot):
        return None
        
    def GetAbilityForActiveHotkey(self):
        return None, None
    
    activeability = None
    activehotkey = None
    activeabiinfo = None
    activeunittype = None
    ishotkeydown = False
    
class GridHotkeySystem(BaseHotkeySystem):
    """ Like in the SC2 grid option, hotkeys/abiltiies are mapped into a grid."""
    gridhotkeys_char_to_slot = {
        'q' : 0, 'w' : 1, 'e' : 2, 'r' : 3,
        'a' : 4, 's' : 5, 'd' : 6, 'f' : 7, 
        'z' : 8, 'x' : 9, 'c' : 10, 'v' : 11, 
    }
    gridhotkeys_slot_to_char = dict(list(zip(list(gridhotkeys_char_to_slot.values()), list(gridhotkeys_char_to_slot.keys()))))
    
    def HandleHotKey(self, player, char):
        if char in self.gridhotkeys_char_to_slot.keys():
            self.HandleGridHotkey(player, char)
        
    def HandleGridHotkey(self, player, char):
        if not self.activeabiinfo or not self.activeunittype:
            return
            
        self.activeability = ClientDoAbility(player, self.activeabiinfo, self.activeunittype.name)
        if self.activeability:
            self.activeability.hotkeysystem = self
            
    def GetAbilityForActiveHotkey(self):
        ''' Returns the ability and unitinfo for the active hotkey.
            Returns (None, None) if no active hotkey is found. '''
        
        if not self.ishotkeydown:
            return None, None
            
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return None, None
            
        unittype = player.GetSelectedUnitType()
        if not unittype:
            return None, None
        
        unitinfo = GetUnitInfo(unittype, fallback=None)
        if not unitinfo:
            return None, None
        
        abislot = self.gridhotkeys_char_to_slot[self.activehotkey]
        
        # Retrieve the active hud abilities map
        abilitiesmap = player.hudabilitiesmap[-1] if getattr(player, 'hudabilitiesmap', None) else unitinfo.abilities
            
        # Must be in the map
        if abislot not in abilitiesmap:
            return None, None
        
        # Get ability info
        try:
            abiinfo = unitinfo.GetAbilityInfo(abilitiesmap[abislot], player.GetOwnerNumber())
        except NoSuchAbilityError:
            return None, None
            
        return abiinfo, unitinfo
            
    def GetHotkeyForAbility(self, abiinfo, slot):
        return self.gridhotkeys_slot_to_char[slot]
        
class SemanticHotkeySystem(BaseHotkeySystem):
    def __init__(self):
        super(SemanticHotkeySystem, self).__init__()
        
# The current hotkey system. Do not import directly (since it might change due the convar below).
hotkeysystem = None

def HotKeyConvarChanged(var, old_value, f_old_value):
    global hotkeysystem
    newsystem = var.GetString()
    
    try:
        if newsystem == 'grid':
            hotkeysystem = GridHotkeySystem()
        elif newsystem == 'semantic':
            hotkeysystem = SemanticHotkeySystem()
        else:
            print('HotKeyConvarChanged: Invalid system %s, defaulting to grid' % (newsystem))
            hotkeysystem = GridHotkeySystem()
    except:
        PrintWarning('Failed to install the hotkey system.\n')
        traceback.print_exc()
        
hotkeysystemvar = ConVar('hotkeysystem', 'grid', FCVAR_ARCHIVE, "Hotkey system", HotKeyConvarChanged)

HotKeyConvarChanged(hotkeysystemvar, '-', 0.0)
