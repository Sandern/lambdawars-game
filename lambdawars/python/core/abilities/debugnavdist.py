from navmesh import NavMeshGetPathDistance
from .base import AbilityBase

class AbilityDebugNavDist(AbilityBase):
    name = 'debug_navmeshdist'
    serveronly = True

    point1 = None
    point2 = None
    
    def Init(self):
        self.player.SetSingleActiveAbility(self)
  
        super().Init()

    def OnLeftMouseButtonPressed(self):
        player = self.player
        selection = player.GetSelection()
        unit = selection[0] if selection else None
        
        if not self.point1:
            if not unit:
                self.point1 = player.GetMouseData().endpos
                return
            else:
                self.point1 = unit.GetAbsOrigin()
                
        if not self.point2:
            self.point2 = player.GetMouseData().endpos

        print('%s to %s, navdist: %s' % (self.point1, self.point2, NavMeshGetPathDistance(self.point1, self.point2, unit=unit)))
            
        self.Completed()
        return True
        
    def OnRightMouseButtonPressed(self):
        if not self.point1:
            self.point1 = self.player.GetMouseData().endpos
            return
                
        if not self.point2:
            self.point2 = self.player.GetMouseData().endpos

        print('%s to %s, navdist: %s' % (self.point1, self.point2, NavMeshGetPathDistance(self.point1, self.point2, unit=unit)))
            
        self.Completed()
        return True