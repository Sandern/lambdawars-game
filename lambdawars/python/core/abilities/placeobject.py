""" General ability for placing objects. """
from srcbase import Color, MASK_NPCSOLID, COLLISION_GROUP_NONE, RenderMode_t
from vmath import Vector
from .target import AbilityTarget
from gameinterface import modelinfo
from utils import UTIL_TraceHull, trace_t, CTraceFilterSimple, UTIL_EntitiesInBox
from navmesh import NavMeshGetPathDistance, NavTestAreaWalkable
from entities import PARTITION_ENGINE_TRIGGER_EDICTS, PARTITION_CLIENT_TRIGGER_ENTITIES

import ndebugoverlay

if isserver:
    from entities import DispatchSpawn


class PlaceObjectTraceFilter(CTraceFilterSimple):
    def __init__(self, passentity, collisiongroup, ownernumber, tellmoveaway):
        super().__init__(passentity, collisiongroup)
        
        self.ownernumber = ownernumber
        self.tellmoveaway = tellmoveaway
        
    def ShouldHitEntity(self, entity, contentsmask):
        if not super().ShouldHitEntity(entity, contentsmask):
            return False
        
        # Base rules tell we should hit. Check if we can tell the unit to move away.
        if entity.IsUnit() and entity.GetOwnerNumber() == self.ownernumber:
            if hasattr(entity, 'DispatchEvent'):
                self.tellmoveaway.append(entity)
                return False
        return True


class AbilityPlaceObjectShared(object):
    """ Base for placable units. """
    debugvalidposition = ''
    cancelmsg_invalidposition = ''
    
    #: Max range in which a builder can place this building
    placemaxrange = 0
    
    def Init(self):
        super().Init()
        
        self.tellmoveaway = []

        # Retrieve model bounds
        if self.modelname:
            model = modelinfo.FindOrLoadModel(self.modelname)
            self.mins, self.maxs = modelinfo.GetModelBounds(model)
            
    def SelectUnits(self): 
        return self.SelectSingleUnit()
            
    def IsValidPosition(self, pos):
        """ Tests if position is valid for placing.
        
            Args:
                pos (Vector): The position to test. Usually at the ground.
                              if placeatmins is set for the object, it's corrected by
                              the bounds of the building/unit.
        """
    
        maxs = self.maxs
        # Most buildings are placed at their origin of the model.
        # In some cases we want to place at the "min" bounds of the model and the place
        # code should account for that. For the ones that place at origin, cut off the negative part
        # of the mins. The bounds will intentionally go into the ground.
        if self.placeatmins:
            mins = self.mins
            testreachpos = Vector(pos.x, pos.y, pos.z + mins.z)
        else:
            mins = Vector(self.mins.x, self.mins.y, 0)
            testreachpos = pos

        # Must be placed on the navigation mesh
        if self.requirenavmesh:
            # Must have an area beneath
            if self.require_walkable_navmesh and not NavTestAreaWalkable(testreachpos, self.mins, self.maxs):
                self.debugvalidposition = 'area not walkable at target position'
                return False

            # Must be reachable by the builder
            if self.unit:
                dist = NavMeshGetPathDistance(self.unit.GetAbsOrigin(), testreachpos, unit=self.unit, beneathlimit=64.0)
                if dist < 0:
                    self.debugvalidposition = 'builder cannot reach target position'
                    return False
                
        # Test if triggers are prohibiting us from placing the object here
        triggerents = UTIL_EntitiesInBox(512, pos + mins, pos + maxs, 0, PARTITION_ENGINE_TRIGGER_EDICTS if isserver else PARTITION_CLIENT_TRIGGER_ENTITIES)
        for ent in triggerents:
            if ent.GetClassname() == 'trigger_nobuildings':
                self.debugvalidposition = 'invalid location'
                return False
    
        # Test potentially blocking entities, trace downwards for a small part
        tr = trace_t()
        self.tellmoveaway = []
        tracefilter = PlaceObjectTraceFilter(None, COLLISION_GROUP_NONE, self.ownernumber, self.tellmoveaway)
        UTIL_TraceHull(pos + Vector(0, 0, 10),
                       pos,
                       mins,
                       maxs,
                       MASK_NPCSOLID,
                       tracefilter,
                       tr)
        
        # Just need to know if we didn't start solid, like in a wall or other building
        if tr.startsolid or tr.allsolid:
            self.debugvalidposition = 'trace failed (fraction: %f)' % (tr.fraction)
            #ndebugoverlay.SweptBox(pos, tr.endpos, mins, maxs, vec3_angle, 255, 0, 0, 150, 1.0)
            return False
        #ndebugoverlay.SweptBox(pos, tr.endpos, mins, maxs, vec3_angle, 0, 255, 0, 150, 1.0)
        if self.ischeat and self.tellmoveaway:
            self.debugvalidposition = 'units in the way'
            return False
        self.debugvalidposition = ''
        return True
        
    def PlaceObject(self):
        from core.units import CreateUnitNoSpawn # FIXME
        
        try:
            owner = int(self.kwarguments.get('owner', self.ownernumber))
        except ValueError:
            owner = self.ownernumber
        
        object = CreateUnitNoSpawn(self.name, owner)
        if not object:
            return None
           
        origin = self.targetpos
        if object.unitinfo.zoffset:
            origin.z += object.unitinfo.zoffset
            
        object.SetAbsOrigin(origin)
        object.SetAbsAngles(self.targetangle)
        DispatchSpawn(object)
        object.Activate()

        return object
        
    def DoPlaceObject(self):
        object = self.PlaceObject()
        if object:
            object.purchasecosts = self.resourcestaken
        return object
        
    if isclient:
        def PreCreateVisuals(self):
            previewinfo = {}
            if self.modelname:
                previewinfo['modelname'] = self.modelname
            elif self.modellist:
                previewinfo['modelname'] = self.modellist[0]
            previewinfo['scale'] = self.scale
            self.infomodels = [previewinfo]
    
        def GetPreviewPosition(self, groundpos):
            origin = Vector(groundpos)
            if self.placeatmins:
                origin.z += -self.mins.z + self.zoffset
            else:
                origin.z += self.zoffset
            return origin
        
        def Frame(self):
            if self.stopupdating:
                return
            super().Frame()
            
            valid_position = self.ischeat or self.IsValidPosition(self.GetPreviewPosition(
                self.GetTargetPos(self.player.GetMouseData())))
            for instance in self.infomodelsinst:
                if not instance:
                    continue
                if valid_position:
                    instance.SetRenderColor(0, 255, 0)
                    instance.SetRenderAlpha(200)
                else:
                    instance.SetRenderColor(255, 0, 0)
                    instance.SetRenderAlpha(200)
                    
        def StartAbility(self): pass
                    
        def DoAbility(self): 
            self.stopupdating = True
            for instance in self.infomodelsinst:
                if not instance:
                    continue
                instance.SetRenderMode(RenderMode_t.kRenderTransTexture)
                instance.SetRenderColor(0, 255, 0)
                instance.SetRenderAlpha(120)

    if isserver:
        @classmethod           
        def Precache(info):
            from core.units import PrecacheUnit
            PrecacheUnit(info.name)
            
        def StartAbility(self): pass
        
        def GetPlaceAction(self, unit):
            return unit.behaviorgeneric.ActionPlaceObject
            
        def DoAbility(self): 
            """ In case executed by an unit it is added to this unit's building queue.
                Otherwise if executed as cheat: directly place at the target location. """
            if self.placeatmins:
                self.targetpos.z += -self.mins.z
                
            #ndebugoverlay.Box(self.targetpos, -Vector(16, 16, 0), Vector(16, 16, 16), 0, 255, 0, 255, 15.0)
                
            if self.ischeat:
                self.DoPlaceObject()
                self.Completed()
                return
                
            if not self.unit:
                self.Cancel(cancelmsg='Unit died while executing the place action')
                return
            
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(notification='not_enough_resources')
                return
            self.cancelmsg_invalidposition = '#Ability_InvalidPosition'
            validposition = self.IsValidPosition(self.targetpos)
            if not validposition:
                self.Cancel(cancelmsg=self.cancelmsg_invalidposition, debugmsg=self.debugvalidposition)
                return
            
            self.behaviorgeneric_action = self.GetPlaceAction(self.unit)
            self.AbilityOrderUnits(self.unit, position=self.targetpos, ability=self)
            
    defaultrendercolor = Color(0, 255, 0, 255)  
    
    requirerotation = True
    requirenavmesh = False
    require_walkable_navmesh = False
    setrecharge = False
    clearvisualsonmouselost = False
    clearprojtexonmouselost = True
    serveronly = False

    stopupdating = False
    
    #: Whether to place the object at the mins of the model bounds, or at the origin.
    #: Defaults to the origin.
    placeatmins = False
    
    tellmoveaway = None

class AbilityPlaceObject(AbilityPlaceObjectShared, AbilityTarget):
    pass
