from srcbase import FL_WORLDBRUSH
from entities import entity, CBaseFuncMapBoundary, SOLID_BSP

@entity('func_map_boundary', 
        cppproperties='bloat(float) : "Bloat" : "-32.0" : "Shrinks the bounds of brush by this amount. Set this to the thickness you used."')
class FuncMapBoundary(CBaseFuncMapBoundary):
    """Brush entity that marks the playable map bounds for out-of-bounds checks."""
    def Spawn(self):
        """Finalize the boundary brush model and collision flags."""
        super().Spawn()
        
        self.SetModel(self.GetModelName())
        self.AddFlag(FL_WORLDBRUSH)
        self.SetSolid(SOLID_BSP)