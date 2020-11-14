from gamemgr import RegisterGamePackage
from gameinterface import AddSearchPath

RegisterGamePackage(
    name=__name__,
    dependencies=['core'],
    modules=[
        'player.*',
        'gamerules.*',
        'units.*',
        'ents.*',
        '$hud.*',
    ],
)  


def LoadGame(*args, **kwargs):
    """ Called on 'load_gamepackage zm' """
    AddSearchPath('zmcontent', 'GAME')

    # TODO:
    #resource_types['zombiepool']
    
    
'''
if isserver:
    from gameinterface import concommand
    from utils import UTIL_GetCommandClient
    @concommand('zm_test')
    def Test(args):
        from entities import RespawnPlayer
        
        RespawnPlayer(UTIL_GetCommandClient(), 'zm_player_survivor')
'''