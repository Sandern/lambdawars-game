
import srcmgr
from gamemgr import LoadGamePackage
from gameinterface import HasApp, APP_L4D1, APP_DOTA

if isclient:
    import hotkeymgr

LoadGamePackage('core')
LoadGamePackage('srctests')

LoadGamePackage('wars_game')
LoadGamePackage('asw')

if HasApp(APP_L4D1):
    LoadGamePackage('l4d')
if HasApp(APP_DOTA):
    LoadGamePackage('dota')
