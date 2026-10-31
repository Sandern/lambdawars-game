"""Mountable turret building classes for Lambda Wars.

Provides base classes for turrets that can be mounted and controlled by units.
"""
from vmath import vec3_origin, Vector, VectorYawRotate
from .baseturret import UnitBaseTurret, WarsTurretInfo

class UnitBaseMountableTurret(UnitBaseTurret):
    """Base class for mountable turret building entities.
    
    Turrets that can be controlled by units mounting them.
    """
    def Precache(self):
        """Precache turret resources including control sounds."""
        super().Precache()
        
        if self.startcontrolsound:
            self.PrecacheScriptSound(self.startcontrolsound)
    
    if isserver:
        def Spawn(self):
            """Spawn the mountable turret and set up mount point."""
            super().Spawn()
            
            self.manpoint = Vector(self.unitinfo.manpoint)
            VectorYawRotate(self.manpoint, self.GetAbsAngles().y, self.manpoint)
            self.manpoint += self.GetAbsOrigin()

    def OnUnitTypeChanged(self, oldunittype):
        """Handle unit type change and update attack priority.
        
        Args:
            oldunittype (str): Previous unit type.
        """
        super().OnUnitTypeChanged(oldunittype)
        
        self.realattackpriority = self.unitinfo.attackpriority
        if not self.controller:
            self.attackpriority = -2
        
    def OnStartControl(self, unit):
        """Handle when a unit starts controlling this turret.
        
        Args:
            unit: Unit entity taking control.
        """
        self.controller = unit.GetHandle()
        
        if self.startcontrolsound:
            self.EmitSound(self.startcontrolsound)
            
        self.attackpriority = self.realattackpriority
        
    def OnLeftControl(self):
        """Handle when the controlling unit leaves the turret."""
        self.controller = None
        
        self.attackpriority = -2
        
    # Variables
    startcontrolsound = 'Func_Tank.BeginUse'
    manpoint = vec3_origin
    ismountableturret = True # Temp
    controller = None

class WarsMountableTurretInfo(WarsTurretInfo):
    """Base class for mountable turret building information.
    
    Defines properties for turrets that can be mounted by units.
    """
    manpoint = vec3_origin
    targetatgroundonly = True