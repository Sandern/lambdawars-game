from srcbase import *
from vmath import Vector
from entities import entity, CBaseEntity
from fields import BooleanField, input
from core.signals import navmeshloaded
from navmesh import NavMeshAvailable
from _recast import RecastMgr
if isserver:
    from entities import FL_EDICT_ALWAYS
else:
    from entities import DATA_UPDATE_CREATED
    
@entity('func_nav_blocker', 
        networked=True,
        clstype='@SolidClass',
        base=['Targetname', 'Parentname', 'Origin', 'RenderFields', 'Global', 'Inputfilter', 'EnableDisable', 'Shadow', 'Wars'])
class FuncNavBlocker(CBaseEntity):
    def __init__(self):
        super().__init__()
        
        navmeshloaded.connect(self.OnNavMeshLoaded)
    
        if isclient:
            self.SetOverrideClassname('func_nav_blocker')
            
    if isserver:
        def UpdateTransmitState(self):
            return self.SetTransmitState(FL_EDICT_ALWAYS)

        def Spawn(self):
            super().Spawn()
            
            self.SetMoveType(MOVETYPE_NONE)
            self.SetModel(self.GetModelName())
            self.AddEffects(EF_NODRAW)
            self.SetCollisionGroup(COLLISION_GROUP_NONE)
            self.SetSolid(SOLID_NONE)
            self.AddSolidFlags(FSOLID_NOT_SOLID)
            
        def Activate(self):
            super().Activate()
        
            self.UpdateBlockedAreas()
    else:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if type == DATA_UPDATE_CREATED:
                self.UpdateBlockedAreas()
                
        def OnDisabledChanged(self):
            self.UpdateBlockedAreas()
            
    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
        self.disabled = False
        self.UpdateBlockedAreas()
        navmeshloaded.disconnect(self.OnNavMeshLoaded)
            
    def OnNavMeshLoaded(self, **kwargs):
        self.UpdateBlockedAreas()
            
    def UpdateBlockedAreas(self):
        if not NavMeshAvailable():
            return
    
        shouldblock = not self.disabled
    
        if self.areasblocked == shouldblock:
            return
            
        # Get bounding box
        mins = self.CollisionProp().OBBMins()
        maxs = self.CollisionProp().OBBMaxs()
            
        mins -= Vector(0, 0, 1)
        maxs += Vector(0, 0, 1)
        
        # If we should block: split areas to make a good fit and get the areas
        # When unblocking: just input the areas ids
        if shouldblock:
            RecastMgr().AddEntBoxObstacle(self, mins, maxs, maxs.z - mins.z)
        else:
            RecastMgr().RemoveEntObstacles(self)
        
        self.areasblocked = shouldblock
        
    @input(inputname='BlockNav', helpstring='Blocks the intersecting navigation areas')
    def InputBlockNav(self, inputdata):
        self.disabled = False
        self.UpdateBlockedAreas()
        
    @input(inputname='UnblockNav', helpstring='Unblocks the intersecting navigation areas')
    def InputUnblockNav(self, inputdata):
        self.disabled = True
        self.UpdateBlockedAreas()
        
    areasblocked = False
    disabled = BooleanField(value=False, keyname='StartDisabled', displayname='Start Disabled', networked=True, clientchangecallback='OnDisabledChanged')
    