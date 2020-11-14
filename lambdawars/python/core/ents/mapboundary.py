from srcbase import FL_WORLDBRUSH
from entities import entity, CBaseFuncMapBoundary, SOLID_BSP

@entity('func_map_boundary', 
        cppproperties='bloat(float) : "Bloat" : "-32.0" : "Shrinks the bounds of brush by this amount. Set this to the thickness you used."')
class FuncMapBoundary(CBaseFuncMapBoundary):
    def Spawn(self):
        super().Spawn()
        
        self.SetModel(self.GetModelName())
        self.AddFlag(FL_WORLDBRUSH)
        self.SetSolid(SOLID_BSP)