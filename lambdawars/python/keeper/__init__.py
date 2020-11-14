''' Defines The Keeper Wars Game package.

    This is a small bonus mode, which is a remake of Dungeon Keeper in Source Engine.
'''

from gamemgr import RegisterGamePackage, LoadGamePackage, UnLoadGamePackage
from core.dispatch import receiver
from core.signals import postlevelinit
from core.factions import FactionInfo
from gameinterface import concommand, engine, FCVAR_CHEAT

if isserver:
    from core.signals import clientactive

RegisterGamePackage(
    name=__name__,
    dependencies=['core'],
    modules = [
        'signals',
        'common',
        'light',
        'taskqueue',
        'player',
        'levelloader',
            
        'blockhovereffect',
        'tiles',
        'block',
            
        'rooms.createroom',
        'rooms.lair',
        'rooms.treasureroom',
        'rooms.hatchery',
        'rooms.training',
        'rooms',
            
        'keeperworld',
        'pickupableobject',
        'gold',
        'game',

        'portal',
        'heart',
        
        'spells.*',
         
        '#units.behavior',
        'units.basekeeper',
        'units.imp',
        'units.parasite',
        'units.drone',
        'units.buzzer',
        'units.grub',
        'units.marine',
        'units',
            
        '$hud.*',
    ]
)  

def LoadFactions():
    class FactionKeeperInfo(FactionInfo):
        name = 'keeper'
        displayname = 'Keeper'
        hud_name = 'keeper_hud'
        startbuilding = ''
        startunit = 'unit_imp'
        resources = []
        
def LoadGame(*args, **kwargs):
    LoadFactions()
        
def ReloadGame(*args, **kwargs):
    LoadGame()
    
    print('Reloading keeper package (client: %s)' % (str(isclient)))
    
    # FIXME
    #import keeperworld
    #currentlevel = keeperworld.lastlevel
        
    LoadFactions()
    
    #if currentlevel:
    #    import keeperworld
    #    keeperworld.nextlevel = currentlevel
    #    print('Setting keeperworld back to current level %s' % (currentlevel))
    
if isserver:
    @receiver(postlevelinit)
    def PostLevelInit(sender, **kwargs):
        import srcmgr
        from core.gamerules import SetGamerules

        if srcmgr.levelname.startswith('dk_'):
            LoadGamePackage('keeper')
            SetGamerules('keeper')
        else:
            UnLoadGamePackage('keeper')
    
    @receiver(clientactive)
    def ClientActive(sender, client, **kwargs):
        import srcmgr
        if srcmgr.levelname.startswith('dk_'):
            client.ChangeFaction('keeper')
            
    def ApplyGameSettings(settings):
        game = settings['game']
        mode = game['mode']
        map = settings.get('map', {'mapcommand' : 'map'})
        
        mapcommand = map['mapcommand']
        
        if mode == 'swarmkeeper':
            mission = game['mission']
            
            from . import keeperworld
            keeperworld.nextlevel = mission
            
            engine.ServerCommand('%s dk_map reserved\n' % (mapcommand))
            
            return True

    @concommand('sk_loadmap', flags=0)#flags=FCVAR_CHEAT)
    def SKLoadMap(args):
        from . import keeperworld
        keeperworld.nextlevel = args.ArgS()
        print('sk_loadmap: Loading %s' % (keeperworld.nextlevel))
        engine.ServerCommand('map dk_map\n')
