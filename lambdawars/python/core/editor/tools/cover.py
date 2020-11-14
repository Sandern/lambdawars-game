from srcbase import IN_DUCK
from vmath import Vector
from .placetool import PlaceTool
from core.decorators import serveronly
import random
import math
from utils import UTIL_FindPosition, FindPositionInfo
from navmesh import GetHidingSpotsInRadius
from editorsystem import EditorSystem

class CoverTool(PlaceTool):
    name = 'editor_tool_cover'
    hidden = True
    placetoolradius = 40.0
    canresizeradius = False
    
    tobeplaced = 0.0
    
    def GetPlaceOrigin(self):
        data = self.player.GetMouseData()
        placeorigin = data.endpos
        return placeorigin
    
    @property
    def placecolor(self):
        isremoving = bool(self.player.buttons & IN_DUCK)
        return Vector(1, 0, 0) if isremoving else Vector(0, 1, 0)

    @serveronly
    def DoPlace(self):
        placeorigin = self.GetPlaceOrigin()
        if self.player.buttons & IN_DUCK:
            self.tobeplaced += self.ticksignal * self.density * 10
            numplace = int(self.tobeplaced)
            self.tobeplaced -= numplace
            
            operation = EditorSystem().CreateCoverDestroyCommand(placeorigin, tolerance=self.placetoolradius + 128.0, num=numplace, excludeFlags=0x01)
            EditorSystem().QueueCommand(operation)
        else:
            self.tobeplaced += self.ticksignal * self.density * 10
            numplace = int(self.tobeplaced)
            self.tobeplaced -= numplace
            
            hidespots = GetHidingSpotsInRadius(placeorigin, self.placetoolradius, None, False)
            if len(hidespots) > 0:
                return
                
            operation = EditorSystem().CreateCoverCreateCommand(placeorigin)
            EditorSystem().QueueCommand(operation)
                