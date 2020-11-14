import re
from gameinterface import concommand, FCVAR_CHEAT
from gamemgr import dblist, BaseInfo, BaseInfoMetaclass
from fields import LocalizedStringField
from core.dispatch import receiver
from core.signals import postlevelshutdown, saverestore_save, saverestore_restore

# Strategic AI db of different types (for custom implementations)
dbid = 'strategicai'
dbstrategicai = dblist[dbid]

# Map of AI players
strategicplayers = {}

@receiver(postlevelshutdown)
def LevelShutdown(sender, **kwargs):
    ShutdownAllStrategicAI()
    
# Creation
def CreateAIForFaction(owner, cputype='cpu_wars_default', difficulty=None):
    ''' Creates a new cpu player. 
    
        Args:
            owner (int): Player slot for which to create the cpu player.
            
        Kwargs:
            cputype (str): type of cpu player to create. Can be used by game packages
                           to load another custom player.
            difficulty (object): string identifying the difficulty level of the cpu player.
    '''
    if owner in strategicplayers:
        strategicplayers[owner].Shutdown()
        del strategicplayers[owner]
        
    info = dbstrategicai.get(cputype, None)
    if info == None:
        PrintWarning('Missing cpu for type %s\n' % (cputype))
        return None

    sai = info(owner, difficulty=difficulty)
    strategicplayers[sai.ownernumber] = sai
    sai.Initialize()
    return sai
    
def ShutdownAllStrategicAI():
    ''' Shutdowns all cpu players. '''
    for sai in strategicplayers.values():
        sai.Shutdown()
    strategicplayers.clear()
        
class StrategicAIInfoMetaClass(BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        # Make sure difficulty keys are lower cased
        if 'supporteddifficulties' in dct:
            supporteddifficulties = {}
            for k, v in dct['supporteddifficulties'].items():
                k = k.lower()
                supporteddifficulties[k] = v
            dct['supporteddifficulties'] = supporteddifficulties
    
        newcls = BaseInfoMetaclass.__new__(cls, name, bases, dct)

        for k, v in newcls.supporteddifficulties.items():
            setattr(newcls, 'difficulty_%s' % (k), v)
        
        return newcls

class StrategicAIInfo(BaseInfo, metaclass=StrategicAIInfoMetaClass):
    id = dbid
    displayname = LocalizedStringField(value='')
    
    supporteddifficulties = {
        'easy' : 0,
        'medium' : 2,
        'hard' : 4,
    }

    @classmethod
    def IsValidAI(cls, sai):
        return sai.ownernumber in strategicplayers
    
    @classmethod
    def ShutdownAI(cls, sai):
        ownernumber = sai.ownernumber
        if ownernumber in strategicplayers:
            strategicplayers[ownernumber].Shutdown()
            del strategicplayers[ownernumber]
            return True
        return False
        
    @classmethod 
    def OnUnLoaded(info):
        super().OnUnLoaded()
        
        ShutdownAllStrategicAI()
        
    def OnRestore(self):
        ''' Called after restoring the cpu player from a save file. '''
        pass
        
def EnableStrategicAI(owner, cputype='cpu_wars_default', difficulty=None):
    return CreateAIForFaction(owner, cputype=cputype, difficulty=difficulty)
    
def DisableStrategicAI(owner):
    ownernumber = int(args[1])
    if ownernumber in strategicplayers:
        strategicplayers[ownernumber].Shutdown()
        del strategicplayers[ownernumber]
        return True
    return False
    
# Save/restore of cpu players
@receiver(saverestore_save)
def SaveActiveCPUPlayers(fields, *args, **kwargs):
    for owner, sai in strategicplayers.items():
        fields['saicpuplayer_%d_%s' % (owner, sai.difficulty)] = str(sai.name)
        #print('Saving cpu player %s=%s' % (('saicpuplayer_%d_%d' % (owner, sai.difficulty)), str(sai.name)))
        
@receiver(saverestore_restore)
def RestoreActiveCPUPlayers(fields, *args, **kwargs):
    cpuplayer = re.compile('saicpuplayer_(?P<owner>\d+)_(?P<difficulty>\d+)')
    
    for name, value in fields.items():
        match = cpuplayer.match(name)
        if not match:
            continue
        
        sai = EnableStrategicAI(int(match.group('owner')), cputype=value, difficulty=int(match.group('difficulty')))
        if sai:
            sai.OnRestore()
    
@concommand('wars_strategicai_enable', flags=FCVAR_CHEAT)
def CCEnableStrategicAI(args):
    CreateAIForFaction(int(args[1]))

@concommand('wars_strategicai_disable', flags=FCVAR_CHEAT)
def CCDisableStrategicAI(args):
    ownernumber = int(args[1])
    if not DisableStrategicAI(ownernumber):
        print('No strategic AI for %d' % (ownernumber))
        
@concommand('wars_strategicai_debugprint', flags=FCVAR_CHEAT)
def DebugPrintStrategicAI(args):
    if args.ArgC() > 1:
        owners = [int(args[1])]
        if owners[0] not in strategicplayers:
            print('No strategic AI for %d' % (owners[0]))
            return
    else:
        owners = strategicplayers.keys()
        
    for owner in owners:
        strategicplayers[owner].PrintDebug()
        