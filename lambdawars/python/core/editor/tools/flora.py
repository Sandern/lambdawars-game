from srcbase import IN_DUCK, MASK_NPCSOLID, MASK_SOLID_BRUSHONLY, KeyValues
from vmath import Vector, QAngle
from .placetool import PlaceTool
from gameinterface import engine, modelinfo
from core.decorators import serveronly
import random
import math
from utils import UTIL_FindPosition, FindPositionInfo
from entities import CWarsFlora
import filesystem

class FloraTool(PlaceTool):
    name = 'editor_tool_flora'
    hidden = True
    
    tobeplaced = 0.0
    
    @property
    def placecolor(self):
        isremoving = bool(self.player.buttons & IN_DUCK)
        return Vector(1, 0, 0) if isremoving else Vector(0, 1, 0)
    
    def IsValidAsset(self, asset):
        return filesystem.FileExists(asset) and not filesystem.IsDirectory(asset)
        
    def FindFloraPosition(self, flora):
        placeorigin = self.GetPlaceOrigin()
        
        success, mins, maxs = flora.ComputeEntitySpaceHitboxSurroundingBox()
        if not success:
            mins = flora.CollisionProp().OBBMins()
            maxs = flora.CollisionProp().OBBMaxs()
    
        randomdegree = random.uniform(0.0, 2 * math.pi)
        randomradius = random.uniform(0.0, self.placetoolradius)
        randomposoffset = Vector(math.cos(randomdegree) * randomradius, math.sin(randomdegree) * randomradius, 48.0)
        
        try:
            placemask = MASK_NPCSOLID if not self.ignoreclips else MASK_SOLID_BRUSHONLY
            info = UTIL_FindPosition(FindPositionInfo(placeorigin + randomposoffset, mins, maxs, 0.0, self.placetoolradius, 
                                     usenavmesh=self.usenavmesh, testposition=False, mask=placemask))
            if not info.success:
                raise Exception('FloraTool.DoPlace: failed to place flora')
        except ValueError:
            raise Exception('FloraTool.DoPlace: failed to place flora')
            
        flora.SetAbsOrigin(info.position)
    
    @serveronly
    def DoPlace(self):
        placeorigin = self.GetPlaceOrigin()
        if self.player.buttons & IN_DUCK:
            self.tobeplaced += self.ticksignal * self.density * 10
            numplace = int(self.tobeplaced)
            self.tobeplaced -= numplace
                
            CWarsFlora.RemoveFloraInRadius(placeorigin, self.placetoolradius, max=numplace)
        else:
            if isserver and self.assets:
                self.tobeplaced += self.ticksignal * self.density * 10
                numplace = int(self.tobeplaced)
                self.tobeplaced -= numplace
            
                for i in range(0, numplace):
                    floramodel = random.sample(self.assets, 1)[0]

                    extravalues = KeyValues('Data')
                    extravalues.SetString('rendercolor', '%d %d %d' % (self.color.r(), self.color.g(), self.color.b()))
                
                    angles = QAngle(0, random.uniform(0, 360), 0)
                    CWarsFlora.SpawnFlora(floramodel, placeorigin, angles, extravalues, fnpostspawn=self.FindFloraPosition)
                