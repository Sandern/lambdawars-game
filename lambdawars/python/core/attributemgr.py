''' Small system for setting attributes of classes containing fields in Sandbox mode.

    Not to be confused with attributes of units!
'''

from srcbase import Color
from core.units import GetUnitInfo, UnitBase
from core.abilities import GetAbilityInfo
from core.attributemgr_shared import IsAttributeFiltered
import playermgr
from entities import GetClassByClassname
from gamerules import GameRules
from fields import BaseField, GetField, HasField
import types
import traceback
import inspect
from gameinterface import ConVarRef, concommand, FCVAR_CHEAT
import filesystem
from core.usermessages import usermessage, SendUserMessage, CSingleUserRecipientFilter

if isserver:
    from utils import UTIL_GetCommandClient
else:
    from vgui.tools import attributemodifiertool#, playermodifiertool
    
sv_cheats = ConVarRef('sv_cheats')

# Client messages
@usermessage(usesteamp2p=True)
def AbilityInfoClear(**kwargs):
    attributemodifiertool.ClearAttributes('Info')
    
@usermessage(usesteamp2p=True)
def AbilityInfoSetAttr(apply, unitname, fieldname, default, **kwargs):
    if apply:
        ApplyAbilityAttribute(unitname, fieldname, default)
    attributemodifiertool.SetAttribute('Info', fieldname, GetStringValue(unitname, fieldname, default))
    
@usermessage(usesteamp2p=True)
def ClassInfoClearAttr(**kwargs):
    attributemodifiertool.ClearAttributes('Class')
    
@usermessage(usesteamp2p=True)
def ClassInfoSetAttr(apply, unitname, fieldname, default, **kwargs):
    attributemodifiertool.SetAttribute('Class', fieldname, GetStringClassValue(unitname, fieldname, default))
    
@usermessage(usesteamp2p=True)
def PlayerInfoSetAttr(apply, name, fieldname, default, **kwargs):
    if apply:
        ApplyPlayerAttribute(name, fieldname, default)
    playermodifiertool.playerpanel.SetAttribute(name, fieldname, default)
    
# Apply attribute types
def GetStringValue(unitname, keyname, value):
    info = GetAbilityInfo(unitname)
    if not info:
        return ''

    if not HasField(info, keyname):
        return str(value)
        
    field = GetField(info, keyname)
    return field.ToString(value)
    
def GetStringClassValue(unitname, keyname, value):
    info = GetAbilityInfo(unitname)
    if not info:
        return ''
    cls = GetClassByClassname(info.cls_name)
    if not cls:
        PrintWarning( 'GetStringClassValue: no such class name %s\n' % (info.cls_name) )
        return ''
        
    if not HasField(info, keyname):
        return str(value)
        
    field = GetField(cls, keyname)
    return field.ToString(value)

def ApplyAbilityAttribute(unitname, keyname, rawvalue):
    info = GetAbilityInfo(unitname)
    if not info:
        return False, None

    field = GetField(info, keyname)
    if not field:
        PrintWarning( 'No field for %s in %s' % (keyname, unitname) )
        return False, None
    try:
        field.Set(info, rawvalue)
    except ValueError:
        PrintWarning('Invalid value for field %s in %s:\n' % (keyname, unitname))
        traceback.print_exc()
    return True, field.Get(info, allowdefault=True)
    
def ApplyClassAttribute(unitname, keyname, rawvalue):
    info = GetAbilityInfo(unitname)
    if not info:
        return False, None
    cls = GetClassByClassname(info.cls_name)
    if not cls:
        PrintWarning( 'ApplyClassAttribute: no such class name %s\n' % (info.cls_name) )
        return False, None
    field = GetField(cls, keyname)
    if not field:
        PrintWarning( 'No field for %s' % (keyname) )
        return False, None
        
    try:
        field.Set(cls, rawvalue)
    except ValueError:
        PrintWarning('Invalid value:\n')
        traceback.print_exc()
    return True, field.Get(cls, allowdefault=True)
    
def ApplyPlayerAttribute(ownernumber, keyname, rawvalue):
    playerinfo = playermgr.dbplayers[ownernumber]
    SetAttribute(playerinfo, keyname, rawvalue)
        
# Attribute edit commands
if isserver:
    def SendFilepathAttribute(fnsetter, obj, unitname, sendfilter):
        try:
            # Get source file path
            path = inspect.getsourcefile(obj)
            path = filesystem.FullPathToRelativePath(path, defaultvalue=path)
            sourcelines, linenumber = inspect.getsourcelines(obj)
            fnsetter(False, unitname, '__filepath__', '%s (line %d)' % (path, linenumber), filter=sendfilter)
        except TypeError:
            fnsetter(False, unitname, '__filepath__', '<unknown>', filter=sendfilter)

    # Method that sends all attributes of an obj + baseclasses
    def SendAllAttributes(fnsetter, obj, unitname, filterflags, sendfilter, stopbasecls, done):
        for name, field in obj.__dict__.items():
            if not isinstance(field, BaseField):
                continue
            if IsAttributeFiltered(name, field, filterflags):
                continue
            if name in done:
                continue
            done.append(name)
            
            try:
                fnsetter(False, unitname, field.name, field.Get(obj, allowdefault=True), filter=sendfilter)
            except:
                # Probably an unsupported value:
                traceback.print_exc()

        if obj in stopbasecls:
            return
            
        # Recursive call all bases
        for base in obj.__bases__:
            SendAllAttributes(fnsetter, base, unitname, filterflags, sendfilter, stopbasecls, done)

    # ================ Unit info ================
    @concommand('abiinfo_requestall')
    def cc_abiinfo_requestall(args):
        # Get requesting player
        player = UTIL_GetCommandClient()
        if not player:
            return
            
        # Check. Can only use if cheats are on or if we are in the sandbox gamemode
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command abiinfo_requestall in multiplayer, unless the server has sv_cheats set to 1.")
            return
        
        # Grab the info
        info = GetAbilityInfo(args[1])
        if not info:
            PrintWarning("abiinfo_requestall: Invalid ability %s" % (args[1]))
            return
            
        # Filter flags
        filterflags = int(args[2])
            
        # Make a filter
        filter = CSingleUserRecipientFilter(player)
        filter.MakeReliable()
        
        # Tell player to clear old
        AbilityInfoClear(filter=filter)
        
        # Send each attribute. Cannot happen in one message, since it easily goes over the max 256 bytes
        SendFilepathAttribute(AbilityInfoSetAttr, info, info.name, filter)
        SendAllAttributes(AbilityInfoSetAttr, info, info.name, filterflags, filter, [], [])

    @concommand('abiinfo_setattr')
    def cc_abiinfo_setattr(args):
        # Get requesting player
        player = UTIL_GetCommandClient()
        if not player:
            return
            
        # Check. Can only use if cheats are on or if we are in the sandbox gamemode
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command abiinfo_setattr in multiplayer, unless the server has sv_cheats set to 1.")
            return
            
        # Grab the info
        info = GetAbilityInfo(args[1])
        if not info:
            PrintWarning("abiinfo_setattr: Invalid unit %s" % (args[1]))
            return
            
        # Apply
        success, updatedvalue = ApplyAbilityAttribute(args[1], args[2], args[3])
        if success:
            AbilityInfoSetAttr(True, info.name, args[2], updatedvalue)
        else:
            PrintWarning('ApplyAbilityAttribute for %s, attr %s and value %s failed\n' % (args[1], args[2], args[3]))
    
    # ================ Class info ================ 
    @concommand('classinfo_requestall')
    def cc_classinfo_requestall(args):
        # Get requesting player
        player = UTIL_GetCommandClient()
        if not player:
            return
            
        # Check. Can only use if cheats are on or if we are in the sandbox gamemode
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command classinfo_requestall in multiplayer, unless the server has sv_cheats set to 1.")
            return
            
        # Grab the info
        info = GetAbilityInfo(args[1])
        if not info:
            PrintWarning("classinfo_requestall: Invalid ability %s" % (args[1]))
            return
            
        if not hasattr(info, 'cls_name'):
            return
            
        # Grab the class
        cls = GetClassByClassname(info.cls_name)
        if not cls:
            PrintWarning("classinfo_requestall: Invalid ability class %s" % (info.cls_name))
            return
            
        # Filter flags
        filterflags = int(args[2])
        
        # Make a filter
        filter = CSingleUserRecipientFilter(player)
        filter.MakeReliable()
        
        # Tell player to clear old
        ClassInfoClearAttr(filter=filter) 
        
        # Send each attribute. Cannot happen in one message, since it easily goes over the max 256 bytes
        SendFilepathAttribute(ClassInfoSetAttr, cls, info.name, filter)
        SendAllAttributes(ClassInfoSetAttr, cls, info.name, filterflags, filter, [UnitBase], [])
    
    @concommand('classinfo_setattr')
    def cc_classinfo_setattr(args):
        # Get requesting player
        player = UTIL_GetCommandClient()
        if not player:
            return
            
        # Check. Can only use if cheats are on or if we are in the sandbox gamemode
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command classinfo_setattr in multiplayer, unless the server has sv_cheats set to 1.")
            return
            
        # Grab the info
        info = GetAbilityInfo(args[1])
        if not info:
            PrintWarning("classinfo_settattr: Invalid ability %s" % (args[1]))
            return
        
        # Apply
        success, updatedvalue = ApplyClassAttribute(args[1], args[2], args[3])
        if success:
            ClassInfoSetAttr(True, info.name, args[2], updatedvalue)  
        else:
            PrintWarning('ApplyClassAttribute for %s, attr %s and value %s failed\n' % (args[1], args[2], args[3]))
            
    # ================ Player info ================
    @concommand('playerinfo_setattr')
    def cc_playerinfo_setattr(args):
        # Get requesting player
        player = UTIL_GetCommandClient()
        if not player:
            return
            
        # Check. Can only use if cheats are on or if we are in the sandbox gamemode
        if not sv_cheats.GetBool() and not GameRules().info.name == 'sandbox':
            print("Can't use cheat command playerinfo_setattr in multiplayer, unless the server has sv_cheats set to 1.")
            return
            
        # Apply
        ApplyPlayerAttribute(int(args[1]), args[2], args[3])
        PlayerInfoSetAttr(True, int(args[1]), args[2], args[3])
