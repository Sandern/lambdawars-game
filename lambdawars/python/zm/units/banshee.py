from entities import entity
from wars_game.units.fastzombie import UnitFastZombie, FastZombieInfo

@entity('unit_banshee')
class UnitBanshee(UnitFastZombie):
    pass

class BansheeInfo(FastZombieInfo):
    name = 'unit_banshee'
    cls_name = 'unit_banshee'
    modelname = 'models/Zombie/zm_fast.mdl'
    
class BansheeInfoAlias(BansheeInfo):
    name = 'npc_fastzombie'
    hidden = True