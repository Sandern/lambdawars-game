"""Utility functions for computing jump trajectories and simulation traces."""
import math
from vmath import vec3_origin, vec3_angle
from srcbase import MASK_SOLID, MASK_SOLID_BRUSHONLY
from gameinterface import ConVarRef
from utils import trace_t, UTIL_TraceHull

if isserver:
    import ndebugoverlay

sv_gravity = ConVarRef('sv_gravity')
g_debug_checkthrowtolerance = ConVarRef('g_debug_checkthrowtolerance')


def CalcJumpVelocity(startpos, endpos, minheight, maxheight, clampspeed, grav_modifier=1.0):
    """ Calculates velocity for a jump without checking collisions. This is the most simple version and
        does not validate if the jump is possible.

    Args:
        startpos (Vector): Start position.
        endpos (Vector): End position.
        minheight (float): Minimum height for the jump (units).
        maxheight (float): Maximum height for the jump (units).
        clampspeed (float): Maximum speed allowed for the final vector (clamped speed).
        grav_modifier (float, optional): Gravity modifier applied on top of
            ``sv_gravity``. Defaults to ``1.0``.

    Returns:
        Vector: Velocity vector that will reach ``endpos`` in a perfect arc.
    """
    gravity = sv_gravity.GetFloat()
    if gravity <= 1:
        gravity = 1

    if grav_modifier:
        gravity *= grav_modifier

    #
    # How fast does the unit need to travel to reach my enemy's eyes given gravity?
    #
    height = (endpos.z - startpos.z)

    height = max(minheight, min(maxheight, height))

    speed = math.sqrt(2 * gravity * height)
    time = speed / gravity

    #
    # Scale the sideways velocity to get there at the right time
    #
    jumpdir = endpos - startpos
    jumpdir /= time

    #
    # Speed to offset gravity at the desired height.
    #
    jumpdir.z = speed

    #
    # Don't jump too far/fast.
    #
    distance = jumpdir.Length()
    if distance > clampspeed:
        jumpdir = jumpdir * (clampspeed / distance)
    return jumpdir

def PerformJump(unit, endpos, minheight, maxheight, clampspeed):
    """Apply the computed jump velocity to a unit's physics state."""
    unit.SetAbsVelocity(CalcJumpVelocity(unit.GetAbsOrigin(), endpos, minheight, maxheight, clampspeed))


def CalcJumpVelocityChecked(entity, spot1, spot2, speed, tolerance, collisiongroup):
    """Calculate a jump velocity between two spots and validate if it's a valid jump for the given entity.

    Args:
        entity: Entity/unit performing the jump.
        spot1 (Vector): Start position.
        spot2 (Vector): End position.
        speed (float): Desired jump speed.
        tolerance (float): Tolerance (Allowed distance) when trace does not fully reach the end spot from the end position.
        collisiongroup (int): Collision group used for traces.

    Returns:
        Vector: Velocity vector (jump direction) if the jump is valid; ``vec3_origin`` otherwise.
    """
    speed = max(1.0, speed)
    hullmins = entity.CollisionProp().OBBMins()
    hullmaxs = entity.CollisionProp().OBBMaxs()

    ent_gravity = entity.GetGravity() if entity and entity.GetGravity() else 1.0

    flGravity = sv_gravity.GetFloat() * ent_gravity

    vecGrenadeVel = (spot2 - spot1)

    # throw at a constant time
    time = vecGrenadeVel.Length( ) / speed
    vecGrenadeVel = vecGrenadeVel * (1.0 / time)

    # adjust upward toss to compensate for gravity loss
    vecGrenadeVel.z += flGravity * time * 0.5

    vecApex = spot1 + (spot2 - spot1) * 0.5
    vecApex.z += 0.5 * flGravity * (time * 0.5) * (time * 0.5)

    tr = trace_t()
    UTIL_TraceHull(spot1, vecApex, hullmins, hullmaxs, MASK_SOLID, entity, collisiongroup, tr)
    if tr.fraction != 1.0:
        # fail!
        if isserver and g_debug_checkthrowtolerance.GetBool():
            ndebugoverlay.Line(spot1, vecApex, 255, 0, 0, True, 5.0)

        return vec3_origin

    if isserver and g_debug_checkthrowtolerance.GetBool():
        ndebugoverlay.Line(spot1, vecApex, 0, 255, 0, True, 5.0)

    UTIL_TraceHull(vecApex, spot2, hullmins, hullmaxs, MASK_SOLID_BRUSHONLY, entity, collisiongroup, tr)
    if tr.fraction != 1.0:
        bFail = True

        # Didn't make it all the way there, but check if we're within our tolerance range
        if tolerance > 0.0:
            flNearness = (tr.endpos - spot2).LengthSqr()
            if flNearness < math.pow(tolerance, 2):
                if isserver and g_debug_checkthrowtolerance.GetBool():
                    ndebugoverlay.Sphere( tr.endpos, vec3_angle, tolerance, 0, 255, 0, 0, True, 5.0 )

                bFail = False

        if bFail:
            if isserver and g_debug_checkthrowtolerance.GetBool():
                ndebugoverlay.Line( vecApex, spot2, 255, 0, 0, True, 5.0 )
                ndebugoverlay.Sphere( tr.endpos, vec3_angle, tolerance, 255, 0, 0, 0, True, 5.0 )
            return vec3_origin

    if isserver and g_debug_checkthrowtolerance.GetBool():
        ndebugoverlay.Line(vecApex, spot2, 0, 255, 0, True, 5.0)

    return vecGrenadeVel