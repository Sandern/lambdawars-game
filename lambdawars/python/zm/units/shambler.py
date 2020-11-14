from entities import entity
from wars_game.units.zombie import UnitZombie, ZombieInfo

@entity('unit_shambler')
class UnitShambler(UnitZombie):
    pass

class ShamblerInfo(ZombieInfo):
    name = 'unit_shambler'
    cls_name = 'unit_shambler'
    modelname = 'models/Zombie/zm_classic_01.mdl'
    
class ShamblerInfoAlias(ShamblerInfo):
    name = 'npc_zombie'
    hidden = True