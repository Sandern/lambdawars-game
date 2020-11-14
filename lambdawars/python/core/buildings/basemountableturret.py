from vmath import vec3_origin, Vector, VectorYawRotate
from .baseturret import UnitBaseTurret, WarsTurretInfo

class UnitBaseMountableTurret(UnitBaseTurret):
    def Precache(self):
        super().Precache()
        
        if self.startcontrolsound:
            self.PrecacheScriptSound(self.startcontrolsound)
    
    if isserver:
        def Spawn(self):
            super().Spawn()
            
            self.manpoint = Vector(self.unitinfo.manpoint)
            VectorYawRotate(self.manpoint, self.GetAbsAngles().y, self.manpoint)
            self.manpoint += self.GetAbsOrigin()

    def OnUnitTypeChanged(self, oldunittype):
        super().OnUnitTypeChanged(oldunittype)
        
        self.realattackpriority = self.unitinfo.attackpriority
        if not self.controller:
            self.attackpriority = -2
        
    def OnStartControl(self, unit):
        self.controller = unit.GetHandle()
        
        if self.startcontrolsound:
            self.EmitSound(self.startcontrolsound)
            
        self.attackpriority = self.realattackpriority
        
    def OnLeftControl(self):
        self.controller = None
        
        self.attackpriority = -2
        
    # Variables
    startcontrolsound = 'Func_Tank.BeginUse'
    manpoint = vec3_origin
    ismountableturret = True # Temp
    controller = None

class WarsMountableTurretInfo(WarsTurretInfo):
    manpoint = vec3_origin
    targetatgroundonly = True