"""Unit system for Lambda Wars.

Provides base classes and infrastructure for all unit types including combat
units, vehicles, buildings, and objects. Handles unit creation, navigation,
combat, abilities, and unit-specific behaviors.
"""
from .info import (UnitInfo, UnitInfoMetaClass, UnitFallBackInfo,
                     CreateUnitNoSpawn, CreateUnit, CreateUnitFancy, CreateUnitsInArea, PlaceUnit,
                     PrecacheUnit, GetUnitInfo, NoSuchAbilityError,
                  unitlist, unitlistpertype, unitpopulationcount, AddPopulation, RemovePopulation, GetMaxPopulation, sv_unitlimit,
                  UnitList, CreateUnitList, CreateUnitListPerType, UnitListHandle, UnitListPerTypeHandle, KillAllUnits)

# Base classes for units
from .cover import CoverSpot
from .base import UnitBase, UnitBaseShared, UnitListObjectField, UnitListPerTypeObjectField
from .basecombat import UnitBaseCombat, Order
from .basehuman import UnitBaseCombatHuman
from .baseobject import UnitBaseObject, UnitObjectInfo
from .basevehicle import UnitBaseVehicle, BaseVehicleInfo, UnitVehicleAnimState
from .damagecontroller import UnitDamageController, UnitDamageControllerAll, UnitDamageControllerInfo
from .animstate import (UnitBaseAnimState, UnitCombatAnimStateEx, UnitCombatAnimState, EventHandlerGesture, EventHandlerJump, 
                        EventHandlerAnimation, EventHandlerAnimationMisc, EventHandlerAnimationCustom, EventHandlerEndSpecAct, 
                        EventHandlerSound, EventHandlerMulti)
from .locomotion import UnitCombatLocomotion, UnitBaseAirLocomotion, UnitVPhysicsLocomotion
from . import hull
from .orders import GroupMoveOrder
if isserver:
    from . import navigator_shared
    from .base import unit_nodamage
    from .navigator import UnitCombatNavigator, UnitCombatAirNavigator, UnitBasePath
    from .senses import UnitCombatSense
    from .behavior_generic import BehaviorGeneric
    from .behavior_overrun import CreateBehaviorOverrun
    from .intention import BaseAction, BaseBehavior

