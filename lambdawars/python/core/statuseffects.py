""" A simple system for status effects.
    
    A status effect is some kind of effect applied to an unit, usually temporary.
    They could come from (passive) abilties or attacks of enemies.
    Examples of such effects are burning, revolutionary fervor and stun.
 """
import gamemgr
from fields import LocalizedStringField
    
# Status Effect db
dbid = 'statuseffects'
dbstatuseffects = gamemgr.dblist[dbid]
dbstatuseffects.priority = 2  # Increase priority to ensure it registered before the units

# Status Effect info entry
class StatusEffectInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = gamemgr.BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        if isclient:
            # Localize fields 
            if not newcls.displayname:
                newcls.displayname = newcls.name

            if newcls.description:
                newcls.description = newcls.name + '\n' + newcls.description
            
        return newcls


class StatusEffectInfo(gamemgr.BaseInfo, metaclass=StatusEffectInfoMetaClass):
    id = dbid
    
    #: Name shown in hud.
    #: In case the name starts with #, it is considered a localized string.
    displayname = LocalizedStringField(value='', encoding='ascii')
    
    description = ''

    #: Owning unit
    owner = None
    
    #: Whether this status effect is removed
    removed = False
    
    def __init__(self, unit, *args, **kwargs):
        super().__init__()
        
        self.owner = unit.GetHandle()
        
    def Init(self):
        return True
        
    def Remove(self):
        if self.removed:
            PrintWarning('Trying to remove status effect %s twice!\n' % self.__class__.__name__)
            return
            
        self.owner.statuseffects.remove(self)
        self.removed = True

    def Update(self, thinkfreq):
        PrintWarning('Status Effect %s has no Update implementation! Removing...\n')
        self.Remove()
        
    def TryAdd(self, *args, **kwargs):
        """ Tries to add the new effect of the same name to this effect.
            Return True if success. In this case no new effect will be 
            created."""
        return False
        
    @classmethod
    def CreateAndApply(cls, targetunit, *args, **kwargs):
        for se in targetunit.statuseffects:
            if se.name != cls.name:
                continue
            if se.TryAdd(*args, **kwargs):
                return
        effect = cls(targetunit, *args, **kwargs)
        if not effect.Init():
            return
        targetunit.statuseffects.append(effect)


class TimedEffectInfo(StatusEffectInfo):
    """ Timed based effect. The effect is removed after the specified duration. """
    #: Allow merging effects, instead of creating multiple instances on one unit
    allowmerge = True
    #: Only allow merging effects if inflictor is the same
    mergesameinflictoronly = False
    
    inflictor = None
    
    def __init__(self, *args, **kwargs):
        inflictor = kwargs.pop('inflictor', None)
        duration = kwargs.pop('duration', 1.0)
        
        super().__init__(*args, **kwargs)

        self.dietime = gpGlobals.curtime + duration
        self.inflictor = inflictor
        self.inflictors = set([inflictor] if inflictor else [])
    
    def TryAdd(self, *args, **kwargs):
        if not self.allowmerge:
            return False
    
        inflictor = kwargs.get('inflictor', None)
        
        if self.mergesameinflictoronly and inflictor != self.inflictor:
            return False
        
        duration = kwargs.get('duration', 1.0)
        self.dietime = max(self.dietime, gpGlobals.curtime + duration)
        if inflictor:
            self.inflictors.add(inflictor)
            
        return True
        
    def Update(self, thinkfreq):
        if self.dietime < gpGlobals.curtime:
            self.Remove()
