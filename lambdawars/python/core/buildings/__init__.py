"""Building system for Lambda Wars.

Provides base classes for all building types including factories, turrets,
garrisonable buildings, and functional buildings. Buildings can be constructed,
upgraded, produce units/abilities, and provide various game functions.
"""
from . base import UnitBaseBuildingShared, UnitBaseBuilding, WarsBuildingInfo, BuildingInfoMetaClass, buildinglist, constructedlistpertype, priobuildinglist
from . basefactory import UnitBaseFactoryShared, UnitBaseFactory
from . dummy import UnitDummy, CreateDummy

from . baseturret import UnitBaseTurret, WarsTurretInfo
from . baseautoturret import UnitBaseAutoTurret
from . basemountableturret import UnitBaseMountableTurret, WarsMountableTurretInfo
from . basegarrisonable import UnitBaseGarrisonableBuilding, GarrisonableBuildingInfo

from . func import FuncBaseSimple, FuncBaseBuilding, FuncBaseFactory