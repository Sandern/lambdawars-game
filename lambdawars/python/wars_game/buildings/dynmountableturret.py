from srcbase import *
from vmath import Vector, QAngle
from core.buildings import WarsMountableTurretInfo, UnitBaseMountableTurret
from core.units import CreateUnitNoSpawn, hull
from utils import UTIL_TraceHull, trace_t
if isserver:
    from entities import DispatchSpawn


class UnitDynMountableTurret(UnitBaseMountableTurret):
    """ Mountable turret version that allows placement on the walls.
        Basically means the dummies are filtered out if dynamic, so
        the main model must be the turret. """
    dynamicplacement = False
    
    def GetDummies(self):
        if self.dynamicplacement:
            return []
        return super(UnitDynMountableTurret, self).GetDummies()


class WarsDynMountTurretInfo(WarsMountableTurretInfo):
    def TestDynPlace(self, pos):
        mins = hull.Mins('HULL_HUMAN')
        maxs = hull.Maxs('HULL_HUMAN')
        for i in range(0, 360, 45):
            testoffset = self.TransformOffset(self.manpoint, QAngle(0, i, 0))

            manpoint = pos + testoffset - Vector(0, 0, self.zoffset)

            # Test if there is room to stand
            tr = trace_t()
            UTIL_TraceHull(manpoint,
                           manpoint + Vector(0, 0, 1),
                           mins,
                           maxs,
                           MASK_NPCSOLID,
                           None,
                           COLLISION_GROUP_NONE,
                           tr)
            if tr.startsolid or tr.fraction != 8.0:
                continue
        
            # Test if there is ground beneath the point
            tr = trace_t()
            UTIL_TraceHull(manpoint,
                           manpoint - Vector(0, 0, 24.0),
                           mins,
                           maxs,
                           MASK_NPCSOLID,
                           None,
                           COLLISION_GROUP_NONE,
                           tr)
            if tr.DidHit() and not tr.startsolid and 0.7 < tr.fraction < 1.0:
                return True
        return False
        
    # Need to set the construction state
    def PlaceObject(self):
        """ Places the building."""
        object = CreateUnitNoSpawn(self.name, self.ownernumber)
        if not object:
            return None
        object.SetAbsOrigin(self.targetpos)
        object.SetAbsAngles(self.targetangle)
        if not self.ischeat:
            object.constructionstate = object.BS_UNDERCONSTRUCTION
        object.dynamicplacement = self.dynamicplacement
        DispatchSpawn(object)
        object.Activate()
        if not self.dynamicplacement:
            if object.unitinfo.zoffset:
                object.SetAbsOrigin(object.GetAbsOrigin()+Vector(0, 0, object.unitinfo.zoffset))
        else:
            object.SetAbsOrigin(object.GetAbsOrigin()+Vector(0, 0, -8.0))
        
        return object
        
    def DoAbility(self): 
        data = self.player.GetMouseData()
        self.dynamicplacement = self.TestDynPlace(self.rotatepoint if self.rotatepoint else data.endpos)
        super().DoAbility()
        
    if isclient:
        def GetPreviewPosition(self, groundpos):
            if self.dynamicplacement:
                origin = Vector(groundpos)
                origin.z -= 8.0
                #origin.z += -self.mins.z
                return origin
            return super().GetPreviewPosition(groundpos)
                    
        def Frame(self):
            if self.stopupdating:
                return
                
            # Change preview models depending on whether it is dynamic placement (like on a wall)
            data = self.player.GetMouseData()
            if self.TestDynPlace(self.rotatepoint if self.rotatepoint else data.endpos):
                if not self.dynamicplacement:
                    self.dynamicplacement = True
                    self.ClearTempModel()
                    self.realinfomodels = list(self.infomodels)
                    self.infomodels = [{'modelname' : self.modelname}]
                    self.CreateTempModel(data.endpos)
            else:
                if self.dynamicplacement:
                    self.dynamicplacement = False
                    self.ClearTempModel()
                    self.infomodels = self.realinfomodels
                    self.CreateTempModel(data.endpos)
              
            super().Frame()
            
    dynamicplacement = False
