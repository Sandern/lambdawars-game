from vmath import vec3_origin, Vector
from . base import WarsWeaponBase
from . base_machinegun import WarsWeaponMachineGun
from . base_melee import WarsWeaponMelee
from . flamer import WeaponFlamer
from . flamer_projectile import FlamerProjectile

# -----------------------------------------
# Vector cones
# -----------------------------------------
# VECTOR_CONE_PRECALCULATED - this resolves to vec3_origin, but adds some
# context indicating that the person writing the code is not allowing
# FireBullets() to modify the direction of the shot because the shot direction
# being passed into the function has already been modified by another piece of
# code and should be fired as specified. See GetActualShotTrajectory(). 

# NOTE: The way these are calculated is that each component == sin (degrees/2)
VECTOR_CONE_PRECALCULATED = vec3_origin
VECTOR_CONE_1DEGREES = Vector( 0.00873, 0.00873, 0.00873 )
VECTOR_CONE_2DEGREES = Vector( 0.01745, 0.01745, 0.01745 )
VECTOR_CONE_3DEGREES = Vector( 0.02618, 0.02618, 0.02618 )
VECTOR_CONE_4DEGREES = Vector( 0.03490, 0.03490, 0.03490 )
VECTOR_CONE_5DEGREES = Vector( 0.04362, 0.04362, 0.04362 )
VECTOR_CONE_6DEGREES = Vector( 0.05234, 0.05234, 0.05234 )
VECTOR_CONE_7DEGREES = Vector( 0.06105, 0.06105, 0.06105 )
VECTOR_CONE_8DEGREES = Vector( 0.06976, 0.06976, 0.06976 )
VECTOR_CONE_9DEGREES = Vector( 0.07846, 0.07846, 0.07846 )
VECTOR_CONE_10DEGREES = Vector( 0.08716, 0.08716, 0.08716 )
VECTOR_CONE_15DEGREES = Vector( 0.13053, 0.13053, 0.13053 )
VECTOR_CONE_20DEGREES = Vector( 0.17365, 0.17365, 0.17365 )