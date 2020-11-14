from _vmath import *

# Alias for Vector
AngularImpulse = Vector

# Add str methods to Vector, Vector2D and QAngle
def __vectorstr__(self):
    return '(%f, %f, %f)' % (self.x, self.y, self.z)
def __vector2dstr__(self):
    return '(%f, %f)' % (self.x, self.y)
Vector.__str__ = __vectorstr__
QAngle.__str__ = __vectorstr__
Vector2D.__str__ = __vector2dstr__

def clamp(val, min, max):
    if val > max:
        return max
    elif val < min:
        return min
    return val