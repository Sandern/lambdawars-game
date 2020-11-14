from srcbase import *
from vmath import *
from core.buildings import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK, DENSITY_NONE
#from _navmesh import CreateNavAreaByCorners, DestroyNavArea, NavMeshAvailable, SplitAreasAtBB, GetNavAreasAtBB
from fields import StringField

@entity('build_bridge',
        studio='models/props/brick_bridge.mdl')
class BuildBridge(BaseClass):
    def __init__(self):
        super().__init__()
        
        self.navids = []
        
    def CreateVPhysics( self ):
        if self.VPhysicsGetObject() != None:
            self.VPhysicsDestroyObject()
                
        self.VPhysicsInitStatic()

        return True
        
    if isserver:
        def Precache(self):
            super().Precache()
            
            self.PrecacheModel(self.MODEL_BROKEN)
            self.PrecacheModel(self.MODEL_HEALTHY)
            
        def Spawn(self):
            super().Spawn()
            
            self.SetUnitType('build_bridge')
            
            self.Repair()
            
            self.SetCollisionGroup(COLLISION_GROUP_NONE)
            self.AddFlag(FL_STATICPROP)
            
            self.CreateVPhysics()
            
        def BlockAreas(self):
            self.SetDensityMapType(DENSITY_NONE)
            
        #def OnNavMeshLoaded(self, **kwargs):
        #    if self.repaired:
        #        self.CreateNavAreas()

        #def UpdateOnRemove(self):
        #    # ALWAYS CHAIN BACK!
        #    super().UpdateOnRemove()
        #    
        #    self.DestroyNavAreas()
        
        # TODO: Update in case we want to use this entity again...
        '''
        def SwapCorners(self, c1, c2):
            return Vector(c2), Vector(c1)
            
        def FixCorners(self, cornernw, cornerne, cornersw, cornerse):
            # Find NW corner
            if cornernw.x > cornerne.x: cornernw, cornerne = self.SwapCorners(cornernw, cornerne)
            if cornernw.x > cornerse.x: cornernw, cornerse = self.SwapCorners(cornernw, cornerse)
            if cornernw.y > cornersw.y: cornernw, cornersw = self.SwapCorners(cornernw, cornersw)
            if cornernw.y > cornerse.y: cornernw, cornerse = self.SwapCorners(cornernw, cornerse)
            
            # Find NE corner
            if cornerne.x < cornersw.x: cornerne, cornersw = self.SwapCorners(cornerne, cornersw)
            if cornerne.y > cornersw.y: cornerne, cornersw = self.SwapCorners(cornerne, cornersw)
            if cornerne.y > cornerse.y: cornerne, cornerse = self.SwapCorners(cornerne, cornerse)
            
            # Find SW corner
            if cornersw.x > cornerse.x: cornersw, cornerse = self.SwapCorners(cornersw, cornerse)

            assert(cornernw.x < cornerne.x)
            assert(cornersw.x < cornerse.x)
            assert(cornernw.y < cornersw.y)
            assert(cornerne.y < cornerse.y)
            
            return cornernw, cornerne, cornersw, cornerse
            
        def CreateNavAreas(self):
            if not NavMeshAvailable():
                return
                
            origin = self.GetAbsOrigin()
            mins = self.CollisionProp().OBBMins()
            maxs = self.CollisionProp().OBBMaxs()
            
            # Destroy old areas if we are rebuilding it
            if self.navids:
                self.DestroyNavAreas()
                
            # Make sure there are no nav areas stuck in the bridge (otherwise the new nav areas won't connect properly)
            dmins, dmaxs = self.GetNavBlockBB()
            dmins.z = dmaxs.z - 64.0 # Don't test all the way down, otherwise we would be removing areas on the ground
            bloat = -Vector(0, 0, 0)
            selbloat = -Vector(16, 16, 0)
            SplitAreasAtBB(dmins - bloat, dmaxs + bloat)
            areasids = GetNavAreasAtBB(dmins - selbloat, dmaxs + selbloat)
            [DestroyNavArea(id) for id in areasids]
        
            # Create the nav areas on the bridge
            # Split into two nav areas
            zmid = 48.0
            zedge = 76.0
            yaw = self.GetAbsAngles().y
            wedge = 32.0
            
            # Area 1
            cornernw = Vector(mins.x, mins.y+wedge, maxs.z-zedge)
            cornerne = Vector(0.0, mins.y+wedge, maxs.z-zmid)
            cornerse = Vector(0.0, maxs.y-wedge, maxs.z-zmid)
            cornersw = Vector(mins.x, maxs.y-wedge, maxs.z-zedge)
            
            VectorYawRotate(cornernw, yaw, cornernw)
            VectorYawRotate(cornerne, yaw, cornerne)
            VectorYawRotate(cornerse, yaw, cornerse)
            VectorYawRotate(cornersw, yaw, cornersw)
            
            cornernw += origin
            cornerne += origin
            cornerse += origin
            cornersw += origin
            
            # Fix corners due rotation
            cornernw, cornerne, cornersw, cornerse = self.FixCorners(cornernw, cornerne, cornersw, cornerse)

            id = CreateNavAreaByCorners(cornernw, cornerne, cornerse, cornersw)
            assert(id != -1)
            self.navids.append(id)
            
            # Area 2
            cornernw = Vector(0.0, mins.y+wedge, maxs.z-zmid)
            cornerne = Vector(maxs.x, mins.y+wedge, maxs.z-zedge)
            cornerse = Vector(maxs.x, maxs.y-wedge, maxs.z-zedge)
            cornersw = Vector(0.0, maxs.y-wedge, maxs.z-zmid)
            
            VectorYawRotate(cornernw, yaw, cornernw)
            VectorYawRotate(cornerne, yaw, cornerne)
            VectorYawRotate(cornerse, yaw, cornerse)
            VectorYawRotate(cornersw, yaw, cornersw)
            
            cornernw += origin
            cornerne += origin
            cornerse += origin
            cornersw += origin
            
            cornernw, cornerne, cornersw, cornerse = self.FixCorners(cornernw, cornerne, cornersw, cornerse)
            
            id = CreateNavAreaByCorners(cornernw, cornerne, cornerse, cornersw)
            assert(id != -1)
            self.navids.append(id)
            
        def DestroyNavAreas(self):
            [DestroyNavArea(id) for id in self.navids]
            self.navids = []
        '''
        
        def Repair(self):
            self.SetModel(self.MODEL_HEALTHY)
            self.lifestate = LIFE_ALIVE
            self.repaired = True
            #self.CreateNavAreas()
            
        def Broken(self):
            self.SetModel(self.MODEL_BROKEN)
            self.lifestate = LIFE_DEAD
            #self.DestroyNavAreas()
            self.repaired = False
            
        def Event_Killed(self, info):
            self.Broken()
            
        def OnHealed(self):
            self.Repair()

    MODEL_BROKEN = 'models/props/brick_bridge_broken.mdl'
    MODEL_HEALTHY = 'models/props/brick_bridge.mdl'
    blocknavareas = False
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    repaired = False

class BaseControlPointInfo(WarsBuildingInfo):
    name = "build_bridge"
    cls_name = "build_bridge"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = BuildBridge.MODEL_HEALTHY
    displayname = '#Bridge_Name'
    description = '#Bridge_Description'
    minimaphalfwide = 0
    minimaphalftall = 0
    health = 500
    placemaxrange = 320.0
    exclude_from_testsuites = {'placebuildings'}
            