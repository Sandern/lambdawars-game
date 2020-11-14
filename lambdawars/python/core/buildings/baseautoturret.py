from srcbase import *
from vmath import Vector, QAngle, AngleVectors, DotProduct, VectorNormalize
from .baseturret import UnitBaseTurret, UnitBaseTurretAnimState
from entities import networked
from utils import UTIL_PlayerByIndex

class UnitAutoTurretAnimState(UnitBaseTurretAnimState):
    def Update(self, eyeyaw, eyepitch):
        if not self.outer.controllerplayer:
            return super().Update(eyeyaw, eyepitch)
            
        # GetAnimTimeInterval returns gpGlobals.frametime on client, and interval between main think (non context) on server
        interval = self.GetAnimTimeInterval()
        
        player = self.outer.controllerplayer
        end = player.GetMouseData().endpos
        dir = end - self.outer.WorldBarrelPosition()
        dist = VectorNormalize(dir)
        
        VectorNormalize(dir)
        self.outer.UpdateAim(dir, interval)
            
@networked
class UnitBaseAutoTurret(UnitBaseTurret):
    def CreateAnimState(self):
        return UnitAutoTurretAnimState(self)
        
    if isserver:
        def BuildThink(self):
            attackinfo = self.unitinfo.AttackTurret
            if self.controllerplayer is None:
                self.senses.PerformSensing()
                self.UpdateEnemy(self.senses)
                
                if self.enemy:
                    dir = self.enemy.WorldSpaceCenter() - self.WorldBarrelPosition()
                    dist = VectorNormalize(dir)
                    self.UpdateAim(dir, attackinfo.attackspeed)
                    
                    vecToTarget = self.enemy.BodyTarget(self.WorldBarrelPosition(), False) - self.WorldBarrelPosition()
                    vecToTarget.z = 0.0
                    VectorNormalize(vecToTarget)
                    
                    forward = Vector()
                    angles = QAngle(0.0, self.aimyaw, 0.0)
                    AngleVectors(angles, forward)
                    
                    dot = DotProduct(vecToTarget, forward)

                    if dist < attackinfo.maxrange and dot > attackinfo.cone: # DOT_3DEGREE
                        self.Fire(1, self)
                else:
                    dir = Vector()
                    AngleVectors(QAngle(self.aimpitch, self.aimyaw, 0.0), dir)
                    self.UpdateAim(dir, attackinfo.attackspeed)
            else:
                self.enemy = None
                
                eyeangles = self.EyeAngles()
                self.animstate.Update(eyeangles.y, eyeangles.x)
            
                player = self.controllerplayer
                if (player.buttons & IN_ATTACK) or (player.buttons & IN_ATTACK2):
                    self.Fire(1, self)
            
            self.StudioFrameAdvance()
            self.DispatchAnimEvents(self)
    
            self.SetNextThink(gpGlobals.curtime + attackinfo.attackspeed)    

    