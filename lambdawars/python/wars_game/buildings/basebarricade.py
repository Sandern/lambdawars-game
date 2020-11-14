from vmath import Vector, AngleVectors
from core.units import GroupMoveOrder
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity, DENSITY_GAUSSIANECLIPSE

@entity('build_barricade', networked=True)
class BaseBarricade(BaseClass):
    autoconstruct = False
    #blocknavareas = False
    #blockdensitytype = DENSITY_GAUSSIANECLIPSE
    
    def TargetOverrideGroupOrder(self, player, data):
        """ Allows overriding the default group order.
        
            Args:
                player (entity): the player executing the group order
                data (MouseTraceData): Mouse data containing the target position + other information
        
            Returns a new group order instance to override the default.
        """
        groupmoveorder = GroupMoveOrder(player, data.groundendpos, findhidespot=True)
        groupmoveorder.coverspotsearchradius = 300.0
        return groupmoveorder
    
class BaseBarricadeInfo(WarsBuildingInfo):
    cls_name = 'build_barricade'
    abilities = {
        8: 'cancel',
    }
    resource_category = 'defense'
    population = 0
    viewdistance = 64.0
