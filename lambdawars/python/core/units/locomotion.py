from srcbase import *
from vmath import *
from math import sqrt

import srcmgr
from utils import UTIL_TraceHull, UTIL_TraceRay, trace_t, Ray_t, ClampYaw
from unit_helper import UnitBaseLocomotion, UnitBaseMoveCommand, UnitBaseAirLocomotion as BaseAirClass, UnitAirMoveCommand, UnitVPhysicsLocomotion
from gameinterface import ConVarRef

sv_gravity = ConVarRef('sv_gravity')

class UnitCombatLocomotion(UnitBaseLocomotion):
    def HandleJump(self):
        """ Jump if needed """ 
        if not self.GetGroundEntity():
            if (self.supportdoublejump and not self.doublejumped and 
                    self.outer.mv.jump and self.doublejumpallowtime < gpGlobals.curtime):
                grav = sv_gravity.GetFloat()
                mul = sqrt(2 * grav * self.outer.mv.jumpheight)
                groundfactor = 1.0
                self.outer.mv.velocity.Zero()
                if self.outer.mv.sidemove > 0:
                    right = Vector()
                    self.outer.GetVectors(None, right, None)
                    self.outer.mv.velocity += right * groundfactor * mul
                elif self.outer.mv.sidemove < 0:
                    right = Vector()
                    self.outer.GetVectors(None, right, None)
                    self.outer.mv.velocity -= right * groundfactor * mul
                else:
                    self.outer.mv.velocity.z += groundfactor * mul
                self.doublejumped = True
            return
        
        self.SetGroundEntity(None)
        
        self.outer.DoAnimation( self.outer.ANIM_JUMP )
        
        grav = sv_gravity.GetFloat()
        
        mul = sqrt(2 * grav * self.outer.mv.jumpheight)
        groundfactor = 1.0
        self.outer.mv.velocity.z += groundfactor * mul
        
        self.outer.JumpSound()
        self.doublejumped = False # Reset
        self.doublejumpallowtime = gpGlobals.curtime + 0.5
        
    supportdoublejump = False
    doublejumped = False
    doublejumpallowtime = 0.0
        
class UnitBaseAirLocomotion(BaseAirClass):
    pass
