from srcbase import MASK_NPCSOLID_BRUSHONLY
from vmath import Vector, VectorNormalize, DotProduct
from utils import UTIL_FindPosition, FindPositionInfo

from operator import itemgetter


class UnitProjector(object):
    """ Project a set of units to around another spot.
    """
    def __init__(self, position, units):
        """ Creates a new unit projector.

            Args:
                position (Vector): target position
                units (iterable): units to be projected to target position
        """
        super().__init__()

        self.position = position
        self.units = units if units is not None else []
        self.positions = []

    def ComputePositions(self, positions_out, center_pos, number_of_positions):
        """ Computes the positions around the target positions for our units.

            Args:
                positions_out (list): out list of positions
                center_pos (Vector): Center pos for positions
                number_of_positions (int): Number of positions needed
        """
        testposition = isserver and number_of_positions < 15
        info = FindPositionInfo(center_pos + self.offset, -Vector(18, 18, 0), Vector(18, 18, 18), 0, 2048.0,
                                mask=MASK_NPCSOLID_BRUSHONLY, testposition=testposition)
        while len(positions_out) < number_of_positions:
            UTIL_FindPosition(info)
            if not info.success:
                break
            positions_out.append(info.position)

        # Fill remaining with center. Shouldn't really ever happen.
        while len(positions_out) < number_of_positions:
            positions_out.append(self.position)

    def ComputePositionsMidPoint(self):
        """ Computes the middle position of the found target positions.

            Returns middle point (Vector)
        """
        midpoint = Vector(0, 0, 0)
        for position in self.positions:
            midpoint += position
        midpoint /= len(self.positions)
        return midpoint

    def GetUnitTestPosition(self, unit):
        """ Gets the unit expected position at the point of executing this order.
            If the unit has no orders, then it's the unit origin.
            If the unit has orders, it's the last queued order position.

            Downside: the order position is not always the move position!

            Args:
                unit (entity): Unit of which to get the expected position
        """
        for o in reversed(unit.orders):
            if not o.position:
                continue

            return o.position

        return unit.GetAbsOrigin()

    def ComputeMidPointUnits(self):
        """ Computes the average position of the units in this group move order. """
        midpoint = Vector(0, 0, 0)
        for unit in self.units:
            midpoint += self.GetUnitTestPosition(unit)
        midpoint /= len(self.units)
        return midpoint

    def Project(self, point1, point2, toproject):
        """ Projects toproject onto the line between point1 and point2

            Args:
                point1 (Vector):
                point2 (Vector):
                toproject (Vector):

            returns projected point.
        """
        m = (point2.y - point1.y) / (point2.x - point1.x)
        b = point1.y - (m * point1.x)

        x = (m * toproject.y + toproject.x - m * b) / (m * m + 1)
        y = (m * m * toproject.y + m * toproject.x + b) / (m * m + 1)

        return Vector(x, y, toproject.z)

    def ProjectAndSortUnits(self, unitmidpoint, formationmidpoint):
        """ Projects all units.
        """
        values = []

        for unit in self.units:
            unitposition = self.GetUnitTestPosition(unit)
            projected = self.Project(unitmidpoint, formationmidpoint, unitposition)
            ratio = (projected-unitmidpoint).Length2D() / (formationmidpoint-unitmidpoint).Length2D()
            values.append([unit, ratio, unitposition])

        values.sort(key=itemgetter(1))

        return values

    def ProjectAndSortPositions(self, unitmidpoint, formationmidpoint):
        """ Projects all positions.
        """
        values = []

        for position in self.positions:
            projected = self.Project(unitmidpoint, formationmidpoint, position)
            ratio = (projected-unitmidpoint).Length2D() / (formationmidpoint-unitmidpoint).Length2D()
            values.append([position, ratio])

        values.sort(key=itemgetter(1))

        return values

    def Execute(self):
        if not self.units:
            return
        if len(self.units) == 1:
            self.ExecuteUnitForPosition(self.units[0], self.position)
            return

        # Compute the positions around the target position. Needs valid spots for our units.
        self.ComputePositions(self.positions, self.position, len(self.units))

        try:
            # Second we are going to decide who is going to move where
            # First calculate the midpoints of each group (the units and the target positions)
            unitmidpoint = self.ComputeMidPointUnits()
            formationmidpoint = self.ComputePositionsMidPoint()
            dir = unitmidpoint - formationmidpoint
            dir.z = 0.0
            VectorNormalize(dir)
            unitmidpoint = unitmidpoint + dir*16000.0
            formationmidpoint = formationmidpoint + -dir*16000.0
            lenline = (unitmidpoint-formationmidpoint).Length2D()

        # if isserver:
            # #ndebugoverlay.Cross3D(unitmidpoint, 32.0, 255, 0, 0, False, 10.0)
            # #ndebugoverlay.Cross3D(formationmidpoint, 32.0, 0, 255, 0, False, 10.0)
            # ndebugoverlay.Line(unitmidpoint, formationmidpoint, 0, 0, 255, False, 10.0)

            # for unit in self.units:
                # projected = self.Project(unitmidpoint, formationmidpoint, unit.GetAbsOrigin())
                # ndebugoverlay.Line(projected, unit.GetAbsOrigin(), 0, 255, 255, False, 10.0)
                # ratio = (projected-unitmidpoint).Length2D() / (formationmidpoint-unitmidpoint).Length2D()
                # ndebugoverlay.Text(projected, '%f' % (ratio), True, 10.0)

            # Then project the units and positions on the line formed by the midpoints
            # Sort these values
            unitratios = self.ProjectAndSortUnits(unitmidpoint, formationmidpoint)
            positionratios = self.ProjectAndSortPositions(unitmidpoint, formationmidpoint)
        except ZeroDivisionError:
            # TODO: Solve this nicer
            return

        # Finally order each unit
        # We look ahead a bit for better positions
        # We do this by looking at the dot product between the target position-unit and the midpoints line
        # If aligned closer with the midpoint line, then that position is better for the unit.
        for i in range(0, len(unitratios)):
            unit, ratio1, unittestpos1 = unitratios[i]

            position, ratio2 = positionratios[0]
            bestj = 0
            dirpos = unittestpos1 - position
            dirpos.z = 0.0
            VectorNormalize(dirpos)
            bestdot = DotProduct(dir, dirpos)
            bestratio = ratio2

            for j in range(0, min(20, len(positionratios))):
                position, ratio2 = positionratios[j]

                # Do not swap when the position is much further along the line.
                if abs(bestratio - ratio2) * lenline > 48.0:
                    break

                # Now swap if this position-unit line is more aligned with the midline
                dirpos = unittestpos1 - position
                dirpos.z = 0.0
                VectorNormalize(dirpos)
                dot = DotProduct(dir, dirpos)
                if dot > bestdot:
                    bestj = j
                    bestdot = dot
                    bestratio = ratio2

            position, ratio2 = positionratios.pop(bestj)
            self.ExecuteUnitForPosition(unit, position)

        def ExecuteUnitForPosition(self, unit, position):
            """ To be implemented by derived classes. """
            pass

    # TODO: Must have an offset when generating positions from the ground mouse position.
    offset = Vector(0, 0, 48.0)
