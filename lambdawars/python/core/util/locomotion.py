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
    """ Calculates velocity for a jump. This is the most simple version and
        does not validate if the jump is possible.

        Args:
            startpos (Vector): Starting position
            endpos (Vector): end position
            minheight (float): Min height for jump
            maxheight (float): Max height for jump
            clampspeed (float): Max speed at which the velocity is clamped

        Kwargs:
            grav_modifier (float): Gravity modifier
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
    unit.SetAbsVelocity(CalcJumpVelocity(unit.GetAbsOrigin(), endpos, minheight, maxheight, clampspeed))

def CalcJumpVelocityChecked(entity, spot1, spot2, speed, tolerance, collisiongroup):
    """ Calculates jump velocity from spot1 and spot2 and checks if it's a valid jump for the given entity.

        Args:
            entity (entity): Entity/unit going to perform the jump
            spot1 (Vector): Start spot
            spot2 (Vector): End spot
            speed (float): Speed of jump
            tolerance (float): Tolerance when trace does not fully reach the end spot
            collisiongroup (int): Collision group for tracing

        Returns: jump direction/velocity (Vector)
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