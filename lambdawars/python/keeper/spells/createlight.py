from vmath import *
from core.abilities import AbilityTarget

from keeper.light import CreateDungeonLight
        
class AbilityControlUnit(AbilityTarget):
    name = "createlight"
    requirerotation = True
    requireunits = False

    if isserver:
        def DoAbility(self):
            data = self.mousedata
            
            CreateDungeonLight

            pos = data.endpos + Vector(0, 0, 140)
            CreateDungeonLight(pos)
            
            self.Completed()    
        