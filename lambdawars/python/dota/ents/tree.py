from srcbase import *
from vmath import *
from entities import entity, CBaseAnimating, DENSITY_GAUSSIAN, EFL_SERVER_ONLY
from utils import *
from gameinterface import concommand
from navmesh import RecastMgr
from core.usermessages import usermessage_shared

from collections import defaultdict

dotatrees = set()
treesgrid = defaultdict(set)

@entity('ent_dota_tree')
class DotaTree(CBaseAnimating):
    GRID_CELL_SIZE = 64.0
    
    destroyed = False

    def __init__(self):
        super().__init__()
        
        dotatrees.add(self)
        
        self.SetDoNotRegisterEntity()
        
        if isserver:
            self.AddEFlags(EFL_SERVER_ONLY)

    def Precache(self):
        super().Precache()
        
        self.PrecacheModel(self.GetModelName())
        
    def Spawn(self):
        self.Precache()
        super().Spawn()
        if isserver:
            self.SetModel(self.GetModelName())
        self.SetSolid(SOLID_BBOX)
        #self.SetMoveType(MOVETYPE_NONE)
        self.SetCollisionBounds(-Vector(16, 16, 0), Vector(16, 16, 150))
        #self.CollisionProp().MarkPartitionHandleDirty()
        
        #if isserver:
        #    self.SetDensityMapType(DENSITY_GAUSSIAN)
        #else:
            #POSITION_CHANGED = 0x1
            #ANGLES_CHANGED = 0x2
            #VELOCITY_CHANGED = 0x4
            #self.InvalidatePhysicsRecursive(POSITION_CHANGED | ANGLES_CHANGED | VELOCITY_CHANGED)
            #self.UpdatePartitionListEntry()
            
        #self.CollisionProp().UpdatePartition()
        
        origin = self.GetAbsOrigin()
        self.key = self.CalcKey(origin)
        treesgrid[self.key].add(self)
            
    def UpdateOnRemove(self):
        dotatrees.discard(self)
        treesgrid[self.key].discard(self)
        
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
    @classmethod
    def CalcKey(cls, pos):
        return (round(pos.x / cls.GRID_CELL_SIZE), round(pos.y / cls.GRID_CELL_SIZE))
        
@usermessage_shared()
def UpdateDotaTrees(origin, radius, destroy, *args, **kwargs):
    cellsize = DotaTree.GRID_CELL_SIZE
    
    minkey = DotaTree.CalcKey(origin - Vector(radius, radius, 0))
    maxkey = DotaTree.CalcKey(origin + Vector(radius, radius, 0))
    
    bodygroup1 = 1 if destroy else 0
    bodygroup0 = 0 if destroy else 1
    for x in range(minkey[0], maxkey[0]):
        for y in range(minkey[1], maxkey[1]):
            for tree in treesgrid[(x, y)]:
                tree.destroyed = destroy
                tree.SetBodygroup(1, bodygroup1)
                tree.SetBodygroup(0, bodygroup0)

    if isserver:
        mins = origin - Vector(radius+40, radius+40, 0)
        maxs = origin + Vector(radius+40, radius+40, 0)
        RecastMgr().RebuildPartial(mins, maxs)
        
if isserver:
    @concommand('dota_trees_destroy')
    def CCTreesDestroy(args):
        player = UTIL_GetCommandClient()
        if not player:
            return
    
        origin = player.GetMouseData().endpos
        radius = float(args[1]) if len(args) > 1 else 128.0

        UpdateDotaTrees(origin, radius, True)
        
    @concommand('dota_trees_grow')
    def CCTreesGrow(args):
        player = UTIL_GetCommandClient()
        if not player:
            return
    
        origin = player.GetMouseData().endpos
        radius = float(args[1]) if len(args) > 1 else 128.0

        UpdateDotaTrees(origin, radius, False)