from gamemgr import RegisterGamePackage

RegisterGamePackage(
    name=__name__,
    dependencies=['core'],
    modules = [
        'gamerules.*',
        'units.*',
        'abilities.*',
    ],
)
