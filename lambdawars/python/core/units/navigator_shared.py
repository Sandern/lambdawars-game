"""Shared navigation utilities for Lambda Wars units.

Contains variables and methods that are shared between various navigation components.
"""
from srcbase import *
from vmath import *


# Goal types
class GoalType:
    """Goal types for navigation system."""
    NONE = 0
    INVALID = 1
    LOCATION = 2
    TARGETENT = 3
    LOCATION_INRANGE = 4
    TARGETENT_INRANGE = 5


def ComputePathDirection(start, end, onground=True):
    """Compute direction and distance for path movement.
    
    Args:
        start (Vector): Start position.
        end (Vector): End position.
        onground (bool): Whether movement is on ground (ignores Z).
        
    Returns:
        tuple: (distance, direction) tuple.
    """
    if onground:
        dir = end - start
        dir.z = 0.0
        dist = VectorNormalize(dir)
    else:
        dir = end - start
        dist = VectorNormalize(dir)   
    return dist, dir


class WayPoint(object):
    """A waypoint in a navigation path."""
    def __init__(self, pos, tolerance):
        """Initialize a waypoint.
        
        Args:
            pos (Vector): Waypoint position.
            tolerance (float): Position tolerance for reaching waypoint.
        """
        self.pos = pos
        self.tolerance = tolerance
        
    def GetLast(self):
        """Get the last waypoint in the chain.
        
        Returns:
            WayPoint: Last waypoint in the linked list.
        """
        wp = self
        while wp.__next__:
            wp = wp.__next__
        return wp
        
    next = None
