"""Cover related code for Lambda Wars.

Provides cover spot system for units to take cover behind objects.
"""
from vmath import vec3_origin
from fields import SerializableObject, IntegerField, VectorField, FloatField


class CoverSpot(SerializableObject):
    """Represents a cover spot where units can take cover.
    
    Cover spots can provide protection from all directions or only
    from a specific direction.
    """
    def __init__(self, type=1, offset=vec3_origin, angle=0):
        """Initialize a cover spot.
        
        Args:
            type (int): 1 for cover from all directions (cover attribute),
                        2 for directional cover.
            offset (Vector): Creation offset for dynamic cover spots used by units/buildings.
            angle (float): Direction from which to receive directional cover.
        """
        super().__init__()

        #: 1 for cover from all directions (cover attribute), 2 for directional cover.
        self.type = type
        #: Creation offset for dynamic cover spots used by units/buildings
        self.offset = offset
        #: Direction from which to receive directional cover
        self.angle = angle

    #: Spot ID
    id = -1

    type = IntegerField()
    offset = VectorField()
    angle = FloatField()
