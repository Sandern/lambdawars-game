""" Contains some variables and methods that are shared between various components """
from srcbase import *
from vmath import *


# Goal types
class GoalType:
    NONE = 0
    INVALID = 1
    LOCATION = 2
    TARGETENT = 3
    LOCATION_INRANGE = 4
    TARGETENT_INRANGE = 5


def ComputePathDirection(start, end, onground=True):
    """ Move information """
    if onground:
        dir = end - start
        dir.z = 0.0
        dist = VectorNormalize(dir)
    else:
        dir = end - start
        dist = VectorNormalize(dir)   
    return dist, dir


class WayPoint(object):
    """ A waypoint """
    def __init__(self, pos, tolerance):
        self.pos = pos
        self.tolerance = tolerance
        
    def GetLast(self):
        wp = self
        while wp.__next__:
            wp = wp.__next__
        return wp
        
    next = None
