from gamemgr import RegisterGamePackage
from srcbase import DMG_BULLET
from gamerules import GetAmmoDef, BULLET_IMPULSE

RegisterGamePackage(
    name=__name__,
    dependencies=['core'],
    modules = [
        'units.*',
    ],
)