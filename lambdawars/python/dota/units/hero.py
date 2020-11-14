from .basedota import UnitDotaInfo, UnitDota as BaseClass
from entities import entity

@entity('npc_dota_hero')
class DotaHero(BaseClass):
    pass
    
class DotaHeroInfo(UnitDotaInfo):
    pass