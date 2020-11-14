from srcbase import SOLID_BSP, MOVETYPE_NONE, FL_WORLDBRUSH
from core.units import UnitBaseShared
from .base import UnitBaseBuildingShared
from .basefactory import UnitBaseFactoryShared
from .basegarrisonable import UnitBaseGarrisonableShared, GarrisonableBuildingInfo
from fields import IntegerField

from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK, FOWFLAG_ALL_MASK
if isserver:
    from entities import CFuncUnit as BaseClass
else:
    from entities import C_FuncUnit as BaseClass

class FuncBaseSimple(UnitBaseShared, BaseClass):
    def Spawn(self):
        super().Spawn()

        if isserver:
            self.SetThink( self.BuildThink )
            self.SetNextThink( gpGlobals.curtime )

    # TODO: Make this nice
    BS_PRECONSTRUCTION = 0
    BS_UNDERCONSTRUCTION = 1
    BS_CONSTRUCTED = 2
    autoconstruct = True
    constructionstate = BS_CONSTRUCTED
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    scaleprojectedtexture = 1.2  # By default, scale it up for brush based buildings

    health = IntegerField(value=0, keyname='health', cppimplemented=True,
                           displayname='Health', helpstring='Health of unit')

    # Stubs
    activeweapon = None
    lasttakedamage = 0
    enemy = None


@entity('func_brush_building', networked=True)
class FuncBaseBuilding(UnitBaseBuildingShared, FuncBaseSimple):
    def Spawn(self):
        super().Spawn()
        self.constructedlisthandle.Enable()
    fowflags = FOWFLAG_ALL_MASK # Set back to FOWFLAG_BUILDINGS_NEUTRAL_MASK once reliable overflow error is fixed again. Test on sp_abandoned.


@entity('func_brush_factory', networked=True)
class FuncBaseFactory(UnitBaseFactoryShared, FuncBaseBuilding):
    def Spawn(self):
        super().Spawn()
        self.constructedlisthandle.Enable()
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK


@entity('func_brush_garrisonable', networked=True)
class FuncBaseGarrisonable(UnitBaseGarrisonableShared, FuncBaseBuilding):
    def Spawn(self):
        super().Spawn()
        self.constructedlisthandle.Enable()
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK


class FuncGarrisonableInfo(GarrisonableBuildingInfo):
    name = 'func_garrisonable'
    cls_name = 'func_brush_garrisonable'
    hidden = True
    health = 1000
    attackpriority = 0
    sound_select = 'build_comb_garrison'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
