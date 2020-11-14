from gamemgr import RegisterGamePackage

RegisterGamePackage(
    name=__name__,
    dependencies=[],
    modules = [
        'excepthook',
        'gametestcase',
        'gametestsuite',
        'gamerunner',
        'collision',
        'converters',
        'srctests',
        'tickframemethods',
        'gamerules',
        'gamesystems',
        'enthandles',
        '#ent_circular_reference',
        'translations',
        'pathing',
    ]
)

def UnloadGame(gp, *args, **kwargs):
    from . import excepthook
    excepthook.UninstallCustomExceptHook()