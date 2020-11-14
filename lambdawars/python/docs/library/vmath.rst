:mod:`vmath` --- Valve Math
===================================================

.. module:: vmath
   :synopsis: Valve Math

.. automodule:: vmath
   :members:
   
-----------------------
Vector
-----------------------
.. autoclass:: vmath.Vector
    :members:
    :inherited-members:
    
-----------------------
Vector2D
-----------------------
.. autoclass:: vmath.Vector2D
    :members:
    :inherited-members:
    
-----------------------
QAngle
-----------------------
.. autoclass:: vmath.QAngle
    :members:
    :inherited-members:
    
-----------------------
Quaternion
-----------------------
.. autoclass:: vmath.Quaternion
    :members:
    :inherited-members:
    
-----------------------
VMatrix
-----------------------
VMatrix always postmultiply vectors as in Ax = b.
Given a set of basis vectors ((F)orward, (L)eft, (U)p), and a (T)ranslation, 
a matrix to transform a vector into that space looks like this:
Fx Lx Ux Tx
Fy Ly Uy Ty
Fz Lz Uz Tz
0   0  0  1

Note that concatenating matrices needs to multiply them in reverse order.
ie: if I want to apply matrix A, B, then C, the equation needs to look like this:
C * B * A * v
ie:
v = A * v;
v = B * v;
v = C * v;

.. autoclass:: vmath.VMatrix
    :members:
    :inherited-members:
    
-----------------------
matrix3x4_t
-----------------------
.. autoclass:: vmath.matrix3x4_t
    :members:
    :inherited-members:
    
-----------------------
cplane_t
-----------------------
.. autoclass:: vmath.cplane_t
    :members:
    :inherited-members: