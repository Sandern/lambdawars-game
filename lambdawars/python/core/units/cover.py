""" Cover related code.
"""
from vmath import vec3_origin
from fields import SerializableObject, IntegerField, VectorField, FloatField


class CoverSpot(SerializableObject):
    def __init__(self, type=1, offset=vec3_origin, angle=0):
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
