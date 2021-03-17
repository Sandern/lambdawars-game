from srcbase import *
from vmath import Vector, vec3_origin, vec3_angle, VectorYawRotate
from core.units import UnitBase as BaseClass
from ..abilities.placeobject import AbilityPlaceObjectShared

from math import ceil, floor

from playermgr import OWNER_LAST, ListAlliesOfOwnerNumber
from core.resources import GiveResources, MessageResourceIndicator, GetResourceInfo, resources, resourcecaps

from fields import (FloatField, IntegerField, StringField, VectorField, SetField, OutputField, BooleanField, DictField,
                    ListField)
from core.units import (PrecacheUnit, UnitInfo, CreateUnitNoSpawn, AddPopulation, RemovePopulation,
                        GetUnitInfo, unitlist, CreateUnitList, CreateUnitListPerType, UnitListObjectField,
                        UnitListPerTypeObjectField, CoverSpot)
from core.units.info import UnitInfoMetaClass
from core.abilities import GetTechNode, BaseTechNode
from core.signals import navmeshloaded
from core.decorators import serveronly_assert

from particles import PrecacheParticleSystem, PATTACH_ABSORIGIN_FOLLOW, DispatchParticleEffect
from gamerules import gamerules
from entities import (entity, FOWFLAG_BUILDINGS_MASK, Activity, DENSITY_GAUSSIAN, DENSITY_NONE, D_LI, CTakeDamageInfo,
                      GetClassByClassname, CWarsFlora)
from gameinterface import modelinfo, CPVSFilter
from navmesh import NavMeshAvailable
from physics import GetCollideAABB
from utils import UTIL_EntitiesInSphere
import ndebugoverlay
from _recast import RecastMgr

if isserver:
    from entities import DispatchSpawn
    from utils import UTIL_Remove, UTIL_ScreenShake, SHAKE_START
    from core.signals import FireSignalRobust, buildingstarted, buildingfinished
else:
    from entities import C_HL2WarsPlayer
    from utils import GetVectorInScreenSpace
    from vgui import scheme, surface, FontDrawType_t
    from vgui.entitybar import UnitBarScreen
    
class BuildingInfoMetaClass(UnitInfoMetaClass):
    def __new__(cls, name, bases, dct):
        newcls = UnitInfoMetaClass.__new__(cls, name, bases, dct)
        
        # Parse dummies for this unit
        dummies = newcls.dummies
        newcls.dummies = []
        for i, d in enumerate(dummies):
            class NewDummyInfo(d):
                hidden = True
                name = '%s_dummy_%d' % (newcls.name, i)
            newcls.dummies.append(NewDummyInfo)

        # Auto calculate place range if not specified.
        if newcls.placemaxrange == None:
            if newcls.mins and newcls.maxs:
                newcls.placemaxrange = (newcls.maxs - newcls.mins).Length2D() + 48.0
        
        return newcls
      
class WarsBuildingInfo(AbilityPlaceObjectShared, UnitInfo, metaclass=BuildingInfoMetaClass):
    displayname = '#Building_Unknown'

    #: Resource category (match statistics)
    resource_category = 'economy'

    minimaphalfwide = 2
    minimaphalftall = 2
    
    selectpriority = 2
    attackpriority = -2
    
    clampminsz = -35.0
    oncreatedroptofloor = False # For CreateUnitFancy, don't use UTIL_DropToFloor
    
    #: Max range in which a builder can place this building (default auto calculated based on building size).
    placemaxrange = None
    
    #: Start health in percentage of maxhealth when construction of a building is started
    constructstarthp = 0.25
    
    #: Attributes of this building (default 'building').
    attributes = ['building']
    
    # Default is to not take population
    population = 0
    
    #: Population provided by the building (default 0).
    providespopulation = IntegerField(value=0)
    
    #: Generates resource. Dictionary with the following keys: type, amount, interval, maxgenerate.
    generateresources = None
    #: Controls if generated resources are split between allies
    splitgeneratedresources = BooleanField(value=False)
    #: Controls if generated resources are reduced when splitled between allies
    reducesplittedresources = BooleanField(value=True)
    
    #: Increases the cap/maximum of a resource (if applicable). List of tuples of the following format: (type, amount).
    #: The cap increase is applied when the building is constructed.
    providescaps = ListField(value=[])
    
    # Buildings don't need to drop scrap (not really all that interesting)
    scrapdropchance = 0
    
    #: Whether or not the building is important for game modes. By default true. See priobuildinglist.
    ispriobuilding = BooleanField(value=True)
    
    # Target ability setting
    targetatgroundonly = True
    requirerotation = False
    requirenavmesh = True
    require_walkable_navmesh = True
    cancelonunitscleared = True
    allowcontinueability = True
    
    # Strategic AI settings
    #: Hints for strategic AI (e.g. unit is a builder). Default is building.
    sai_hint = set(['sai_building'])
    
    #: Fill color
    fillcolor = '#C5DFE4'
    
    #: Default animation played (activity name)
    idleactivity = StringField(value='')
    #: Construction animation played (activity name)
    constructionactivity = StringField(value='')
    #: Disables construction trans texture if no construction activity is specified
    constructionnotranstexture = BooleanField(value=False)
    #: Work animation
    workactivity = StringField(value='')
    #: Work sound
    sound_work = StringField(value='')
    #: Model used during exploding
    explodemodel = StringField(value='')
    #: Lighting Offset for explode model
    explodemodel_lightingoffset = VectorField(value=vec3_origin)
    #: Animation played when destroyed (activity name)
    explodeactivity = StringField(value='')
    #: Particle effect dispatched when destroyed.
    explodeparticleeffect = StringField(value='')
    #: Particle offset for destruction effect
    explodeparticleoffset = VectorField(value=vec3_origin)
    #: Shake parameters when destroyed (default None).
    explodeshake = None # (amplitude, frequency, duration, radius)
    
    # List of dummy buildings to create
    # Dictionaries containing:
    # modelname -
    # offset - 
    # angle -
    dummies = []
    
    #: List of cover spots (Vector offsets around the building, defined in core.units.cover.CoverSpot)
    #: Not saved, as these spots are build when the navigation mesh is loaded.
    cover_spots = ListField(value=[], restrict_type=CoverSpot, save=False)
    
    #: List of unit types to which this building must be placed near or not
    #: Each entry is a dictionary containing keys for unittype and radius.
    placerestrictions = []
    
    # Ignored by unit movement
    ignoreunitmovement = BooleanField(value=False)

    @classmethod
    def Setup(info):
        super().Setup()
        
        # Auto calculate place range if not specified.
        if info.placemaxrange == None:
            if info.mins and info.maxs:
                info.placemaxrange = (info.maxs - info.mins).Length2D() / 2.0 + 48.0
            else:
                info.placemaxrange = 0.0
                
        # Auto calculate a default eye offset
        # Always override, they usually have no eye offset in the model
        if not info.customeyeoffset and info.cls_name and info.mins and info.maxs:
            cls = GetClassByClassname(info.cls_name)
            if cls and not cls.customeyeoffset:
                info.customeyeoffset = Vector(0, 0, (info.maxs.z + info.mins.z) / 2.0)
        
    if isclient:
        def PreCreateVisuals(self):
            previewinfo = {}
            if self.modelname:
                previewinfo['modelname'] = self.modelname
            elif self.modellist:
                previewinfo['modelname'] = self.modellist[0]
            previewinfo['scale'] = self.scale
            if self.idleactivity:
                previewinfo['activity'] = self.idleactivity
            self.infomodels = [previewinfo]

            for d in self.dummies:
                previewinfo = {
                    'modelname' : d.modelname,
                    'offset' : d.dummyinfo.get('offset', vec3_origin),
                    'angle' : d.dummyinfo.get('angle', vec3_angle),
                }
                    
                if self.idleactivity:
                    previewinfo['activity'] = self.idleactivity
                    
                self.infomodels.append(previewinfo)
                    
    # Need to set the construction state
    def PlaceObject(self):
        """ Places the building."""
        try:
            owner = int(self.kwarguments.get('owner', self.ownernumber))
        except ValueError:
            owner = self.ownernumber
        
        object = CreateUnitNoSpawn(self.name, owner)
        if not object:
            return None
        object.SetAbsOrigin(self.targetpos)
        object.SetAbsAngles(self.targetangle)
        if not self.ischeat:
            object.constructionstate = object.BS_UNDERCONSTRUCTION
        DispatchSpawn(object)
        object.Activate()
        if object.unitinfo.zoffset:
            object.SetAbsOrigin(object.GetAbsOrigin()+Vector(0,0,object.unitinfo.zoffset))
        #ndebugoverlay.Box(self.targetpos, -Vector(16, 16, 0), Vector(16, 16, 16), 0, 255, 0, 255, 15.0)
        object.purchasecosts = self.resourcestaken
        return object
        
    def GetPlaceAction(self, unit):
        return unit.behaviorgeneric.ActionPlaceBuilding
        
    def IsValidPosition(self, pos):
        for placerestr in self.placerestrictions:
            targets = UTIL_EntitiesInSphere(1024, pos, placerestr['radius'], 0)
            for target in targets:
                if not target or not target.IsUnit():
                    continue
                if target.unitinfo.name == placerestr['unittype']:
                    self.debugvalidposition = 'invalid location'
                    return False
        return super().IsValidPosition(pos)
        
    class TechNode(BaseTechNode):
        _techenabled = False

class BuildingFallBackInfo(WarsBuildingInfo):
    name = 'build_unknown'
    displayname = 'Unknown Building'
    attributes = []
    hidden = True
    
buildinglist = CreateUnitList()
constructedlistpertype = CreateUnitListPerType()

# A list of buildings important for game modes. Mainly used to detect if the game should end.
# This list excludes turrets, control points and dummies
priobuildinglist = CreateUnitList()
    
if isclient:
    class UnitProgressBarScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super().__init__(unit,
                Color(136, 209, 215, 250), Color(60, 60, 60, 250), Color(150, 150, 150, 0), offsety=-4.0)
            
        def Draw(self):
            if not self.unit or not self.unit.IsAlive() or self.unit.IsDormant():
                return
            panel = self.GetPanel()
            panel.weight = self.unit.GetBuildProgress()
            super().Draw()

class UnitBaseBuildingShared(object):
    def __init__(self):
        super().__init__()
        
        if isserver:
            self.viewdistance = 1024.0
            self.SetShadowCastDistance(2048.0) # Use a much higher shadow cast distance
            
            self.areasids = []
            self.dummies = []
        self.hidespots = [] 
            
        # Buildings block LOS and attacks/bullets
        self.neverignoreattacks = True
        # Body target is based on origin + eye offset (instead of world space center + eye offset)
        self.bodytargetoriginbased = True
        
        navmeshloaded.connect(self.OnNavMeshLoaded)

    if isserver:
        def Spawn(self):
            super().Spawn()
            
            self.buildinglisthandle.Enable()
            if self.unitinfo.ispriobuilding:
                self.priobuildinglisthandle.Enable()
            
            self.CheckTech()

            self.AddFlag(FL_AIMTARGET | FL_NPC) 
        
            # Buildings can't be ignored, so don't use a "unit owner" collision group
            self.SetCollisionGroup(WARS_COLLISION_GROUP_BUILDING) 
        
            self.lifestate = LIFE_ALIVE
            self.takedamage = DAMAGE_YES
            self.SetBlocksLOS(True)

        areasblocked = False

        def GetNavBlockBB(self):
            # Prefer collide bounds. Fallback to manual or model bounds.
            mins, maxs = GetCollideAABB(self)
            if mins != None:
                pass #TransformAABB(self.CollisionProp().CollisionToWorldTransform(), physmins, physmaxs, mins, maxs)
            else:
                if not self.unitinfo.mins:
                    mins = Vector(); maxs = Vector()
                    self.CollisionProp().WorldSpaceSurroundingBounds(mins, maxs)
                else:
                    mins = self.unitinfo.mins
                    maxs = self.unitinfo.maxs
                    #return self.unitinfo.mins, self.unitinfo.maxs #TransformAABB(self.CollisionProp().CollisionToWorldTransform(), self.unitinfo.mins, self.unitinfo.maxs, mins, maxs)
            mins.z -= 64.0
            return mins, maxs
        
        def BlockAreas(self):
            """ Blocks the navigation areas beneath the building.
            """
            if not self.IsSolid():
                return
            if not NavMeshAvailable() or not self.blocknavareas:
                self.SetDensityMapType(self.blockdensitytype)
                return
            if self.areasblocked:
                return

            self.SetDensityMapType(DENSITY_NONE)

            if not self.nav_radius_obstacle_mode:
                mins, maxs = self.GetNavBlockBB()
                RecastMgr().AddEntBoxObstacle(self, mins, maxs, maxs.z - mins.z)
            else:
                radius = self.CollisionProp().BoundingRadius2D() * self.nav_radius_obstacle_scale
                RecastMgr().AddEntRadiusObstacle(self, radius, self.CollisionProp().OBBSize().z)

            self.areasblocked = True
            
        def UnblockAreas(self):
            """ Unblocks the navigation areas beneath the building.
            """
            if not self.areasblocked:
                return
            RecastMgr().RemoveEntObstacles(self)

            self.areasblocked = False
    else:
        def Spawn(self):
            super().Spawn()
            self.buildinglisthandle.Enable()
            if self.unitinfo.ispriobuilding:
                self.priobuildinglisthandle.Enable()
            self.SetBlocksLOS(True)
            
    def OnNavMeshLoaded(self, **kwargs):
        if isserver:
            self.BlockAreas()
        self.CreateCoverSpots()

    def CreateCoverSpots(self):
        super().CreateCoverSpots(self.unitinfo.cover_spots)

    def OnChangeOwnerNumber(self, oldownernumber):
        super().OnChangeOwnerNumber(oldownernumber)

        owner = self.GetOwnerNumber()
        
        if isserver:
            # Update dummy buildings to new owner
            for dummy in self.dummies:
                dummy.SetOwnerNumber(owner)

        if self.GetUnitType():
            self.CheckTech()
            
            # TODO: FIXME -> should provide a different fallback
            try:
                if isserver and self.addpopulation and self.unitinfo.providespopulation:
                    RemovePopulation(oldownernumber, self.unitinfo.providespopulation)
                    AddPopulation(owner, self.unitinfo.providespopulation)
            except AttributeError:
                pass 
                
            if self.addedrescaps:
                self.UpdateResourceCaps(True)
                    
        if self.health < self.maxhealth:
            self.OnLostFullHealth()
                    
    def OnUnitTypeChanged(self, oldunittype):
        super().OnUnitTypeChanged(oldunittype)

        self.RebuildSelectionBounds()
        
        unitinfo = self.unitinfo
        
        if oldunittype:
            self.CheckTech()
            if isserver:
                oldinfo = GetUnitInfo(oldunittype, fallback=None)
                if oldinfo and hasattr(oldinfo, 'providespopulation'):
                    RemovePopulation(self.GetOwnerNumber(), oldinfo.providespopulation)
                    
        # Create a copy to allow modification
        self.generateresources = dict(unitinfo.generateresources) if unitinfo.generateresources else None
        if self.generateresources and 'maxgenerate' in self.generateresources:
            if self.generateresources['type'] not in self.resourcesleft:
                self.resourcesleft[self.generateresources['type']] = self.generateresources['maxgenerate']
        
        self.SetAlwaysNavIgnore(unitinfo.ignoreunitmovement)

        if self.addedrescaps:
            self.UpdateResourceCaps(True)
                    
        if self.GetUnitType():
            self.CheckTech()
            
            if isserver and self.addpopulation and unitinfo.providespopulation:
                AddPopulation(self.GetOwnerNumber(), unitinfo.providespopulation)
                
            if self.handlesactive:
                if self.unitinfo.ispriobuilding:
                    self.priobuildinglisthandle.Enable()
                else:
                    self.priobuildinglisthandle.Disable()

    def OnDataUpdateCreated(self):
        super().OnDataUpdateCreated()

        self.flora_flatten_radius = self.CollisionProp().BoundingRadius2D() * 0.75
        CWarsFlora.FlattenFloraInRadius(self.GetAbsOrigin(), self.flora_flatten_radius, True)

    def UnFlattenFlora(self):
        if not isclient or not self.flora_flatten_radius:
            return
        CWarsFlora.FlattenFloraInRadius(self.GetAbsOrigin(), self.flora_flatten_radius, False)
        self.flora_flatten_radius = None

    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
        if self.GetUnitType():
            if isserver:
                if self.addpopulation and self.unitinfo.providespopulation:
                    RemovePopulation(self.GetOwnerNumber(), self.unitinfo.providespopulation)
                self.UpdateResourceCaps(False)
                
        self.buildinglisthandle.Disable()
        self.constructedlisthandle.Disable()
        self.priobuildinglisthandle.Disable()
        self.CheckTech()
        
        if isserver:
            self.UnblockAreas()
        navmeshloaded.disconnect(self.OnNavMeshLoaded)

        self.UnFlattenFlora()
            
    def OnHealed(self):
        """ Trigger when repairing finished completely. """
        pass
                
    def OnLostFullHealth(self):
        if isclient:
            return
        # Check for units with construct ability
        origin = self.GetAbsOrigin()
        maxdistsqr = 1024.0*1024.0
        for unit in unitlist[self.GetOwnerNumber()]:
            info = unit.abilitiesbyname.get('construct', None)
            if not info:
                continue
            if not unit.AllowAutoCast():
                continue
            if not unit.abilitycheckautocast[info.uid]:
                continue
            if origin.DistToSqr(unit.GetAbsOrigin()) > maxdistsqr:
                continue
            unit.senses.ForcePerformSensing()
            info.CheckAutoCast(unit)

    def UpdateTech(self, ownernumber, unittype):
        if not isserver or unittype == 'unit_unknown':
            return
        technode = GetTechNode(unittype, ownernumber)
        if technode:
            technode.techenabled = bool(len(constructedlistpertype[ownernumber][unittype]) > 0)
            
    def CheckTech(self):
        if not isserver:
            return
        
        # Update old tech because their state might have changed
        if self.techunittype and self.techunittype != self.GetUnitType():
            self.UpdateTech(self.techownernumber, self.techunittype)
        elif self.techownernumber and self.techownernumber != self.GetOwnerNumber():
            self.UpdateTech(self.techownernumber, self.techunittype)
            
        # Update new tech because their state might have changed too
        self.techunittype = self.GetUnitType()
        self.techownernumber = self.GetOwnerNumber()
        self.UpdateTech(self.techownernumber, self.techunittype)
            
    def IsSelectableByPlayer(self, player, target_selection):
        """ All other buildings must be of the same type """    
        unit_type = self.GetUnitType()
        for unit in target_selection:
            if unit.GetUnitType() != unit_type:
                return False
        return super().IsSelectableByPlayer(player, target_selection)
        
    # Show selection circle when the mouse hovers on us
    def OnCursorEntered(self, player):
        super().OnCursorEntered(player)
        self.drawselection += 1
        self.CheckDrawSelection()
        
    def OnCursorExited(self, player):
        super().OnCursorExited(player)
        self.drawselection -= 1
        self.CheckDrawSelection()
        
    def BuildThink(self):
        # Update abilities if they want to be updated
        for abi in self.checkabilities:
            abi.OnUnitThink(self)

        self.StatusEffectsThink(0.5)
    
        self.SetNextThink(gpGlobals.curtime + 0.5)
        
    def DestructThink(self):
        ''' Think function that is supposed to destruct/explode us in some cool way.'''
        self.SUB_Remove()
        
    _tookdamageinfos = None
    _tookdamagelasttickcount = None
    def OnTakeDamage(self, dmginfo):
        # Specific fix/hack for RadiusDamage and dummy buildings
        # Dummy buildings redirect their damage to the main building
        # Because Radius damage applies the damage to all entities in a sphere, the main
        # building takes damage multiple times. Here we filter on this damage. Assume
        # it's always BLAST type, to limit the side effects.
        if dmginfo.GetDamageType() & DMG_BLAST:
            # Reset when tick count changes. Unlikely RadiusDamage is applied multiple times 
            # with the same inflictor within the same frame
            if not self._tookdamageinfos or self._tookdamagelasttickcount != gpGlobals.tickcount:
                self._tookdamageinfos = set()
                self._tookdamagelasttickcount = gpGlobals.tickcount
                
            inflictor = dmginfo.GetInflictor()
            if inflictor in self._tookdamageinfos:
                return 0
            self._tookdamageinfos.add(inflictor)
        
        return super().OnTakeDamage(dmginfo)
        
    def Event_Killed(self, info):
        """ Killed :) """
        self.lifestate = LIFE_DYING
        
        super().Event_Killed(info)
        
        self.UpdateResourceCaps(False)

        self.UnblockAreas()
        
        # TODO: Move to UnitBaseBuilding only?
        self.DestroyDummies()
        
        # Clear from any list
        self.buildinglisthandle.Disable()
        self.constructedlisthandle.Disable()
        self.priobuildinglisthandle.Disable()
            
        # Destruct think will take care of the rest
        self.SetNextThink(gpGlobals.curtime)
        self.SetThink(self.DestructThink)
        
        # Fire destruction event
        self.ondestroyed.FireOutput(self, self)
        
    def DestroyDummies(self):
        pass
        
    def CanBecomeRagdoll(self):
        return False
        
    def RepairStep(self, intervalamount, repairhpps):
        if self.health >= self.maxhealth:
            return True
            
        # Cap speed at four or more workers
        n = len(self.constructors)
        if n > 1:
            intervalamount *= (1 + ((n - 1) ** 0.5)) / n
            
        self.health += int(ceil(intervalamount*repairhpps))
        self.health = min(self.health, self.maxhealth)
        if self.health >= self.maxhealth:
            self.OnHealed()
            return True
        return False
        
    def UpdateResourceCaps(self, addcaps=False):
        providescaps = getattr(self.unitinfo, 'providescaps', None)

        owner = self.GetOwnerNumber()
    
        # Don't need to do anything if nothing changed
        if addcaps and (not providescaps or (self.addedrescaps == providescaps and owner == self.addrescapsowner)):
            return

        # Remove caps from previous owner if any
        if self.addrescapsowner is not None:
            for res_type, amount in self.addedrescaps:
                res_info = GetResourceInfo(res_type)
                if not res_info:
                    continue
                res_info.UpdateResourceCap(self.addrescapsowner, -amount)
            self.addrescapsowner = None
            self.addedrescaps = []
            
        # Add caps to new owner
        if addcaps:
            self.addrescapsowner = owner
            self.addedrescaps = providescaps
            for res_type, amount in providescaps:
                res_info = GetResourceInfo(res_type)
                if not res_info:
                    PrintWarning('UpdateResourceCaps: Invalid resource type %s in providescaps of %s\n' % (res_type, self.unitinfo.name))
                    continue
                res_info.UpdateResourceCap(self.addrescapsowner, amount)
        
    def SetSelectionParticleCornerCP(self, particle, cp, origin, offset, yaw):
        VectorYawRotate(offset, yaw, offset)
        point = origin + offset
        particle.SetControlPoint(cp, point)
        
    def RebuildSelectionBounds(self):
        unitinfo = self.unitinfo
        self.selectionmins = self.CollisionProp().OBBMins() if not unitinfo.mins else unitinfo.mins
        self.selectionmaxs = self.CollisionProp().OBBMaxs() if not unitinfo.maxs else unitinfo.maxs
        
    def CreateParticleSelectionEffect(self):
        unitinfo = self.unitinfo
        projorigin = self.GetAbsOrigin()
        angles = self.GetAbsAngles()
        mins = self.selectionmins
        maxs = self.selectionmaxs
        offsetz = 64.0
        yaw = angles.y
        
        offset1 = Vector(mins.x, mins.y, offsetz)
        VectorYawRotate(offset1, yaw, offset1)
        
        self.selectionparticle = self.ParticleProp().Create(self.selectionparticlename, PATTACH_ABSORIGIN_FOLLOW, -1, offset1)
        self.selectionparticle.SetControlPoint(self.selectionparticlecolorcp, self.GetTeamColor())
        radius = self.CollisionProp().BoundingRadius2D() * self.scaleprojectedtexture
        
        projorigin += offset1
        #ndebugoverlay.Box(projorigin, -Vector(16, 16, 0), Vector(16, 16, 16), 0, 255, 0, 255, 15.0)
        self.SetSelectionParticleCornerCP(self.selectionparticle, 1, projorigin, Vector(maxs.x - mins.x, 0, 0), yaw)
        self.SetSelectionParticleCornerCP(self.selectionparticle, 2, projorigin, Vector(0, maxs.y - mins.y, 0), yaw)
        self.SetSelectionParticleCornerCP(self.selectionparticle, 3, projorigin, Vector(maxs.x - mins.x, maxs.y - mins.y, 0), yaw)
        
    def GetBuildProgress(self):
        ''' Returns build/construct progress for UnitProgressBarScreen. '''
        return 0
        
    # Selection texture
    scaleprojectedtexture = 1.2
    # Selection particle
    selectionparticlename = 'unit_square'
    # Control point for color of selection particle
    selectionparticlecolorcp = 4
    # Selection mins bounds
    selectionmins = vec3_origin
    # Selection maxs bounds
    selectionmaxs = vec3_origin
    # Radius used for flattening flora
    flora_flatten_radius = None
    
    # Building Lists
    buildinglisthandle = UnitListObjectField(buildinglist)
    constructedlisthandle = UnitListPerTypeObjectField(constructedlistpertype)
    priobuildinglisthandle = UnitListObjectField(priobuildinglist)

    # Nav mesh obstacle modes
    nav_radius_obstacle_mode = BooleanField(value=False)
    nav_radius_obstacle_scale = FloatField(value=0.75)
    
    # Outputs
    ondestroyed = OutputField(keyname='OnDestroyed', displayname='OnDestroyed', helpstring='Triggered when this building is destroyed')
        
    # Tech vars (used in CheckTech)
    techunittype = None
    techownernumber = None
 
    # Settings
    isbuilding = True
    isconstructed = True # By default constructed
    repairable = True
    fowflags = FOWFLAG_BUILDINGS_MASK
    addpopulation = BooleanField(value=False)
    
    #: Whether the building increased caps (ref to providescaps of the unitinfo class)
    addedrescaps = []
    #: Current owner for which the building increased/decreases the resource caps
    addrescapsowner = None
    
    #: Block navigation areas on constructed.
    blocknavareas = True
    #: If not blocking nav areas, the density type to be used
    blockdensitytype = DENSITY_GAUSSIAN

    unitinfofallback = BuildingFallBackInfo
    unitinfovalidationcls = WarsBuildingInfo
    
@entity('build_base', networked=True)
class UnitBaseBuilding(UnitBaseBuildingShared, BaseClass):
    def __init__(self):
        super().__init__()
        
        #self.dummies = []
        self.SetBloodColor(DONT_BLEED)
        
        if isserver:
            self.UseClientSideAnimation()
            self.SetAlwaysSendFullSelectionData(True) # Always send Health/Energy at full resolution for buildings
        
    def RebuildSelectionBounds(self):
        unitinfo = self.unitinfo
        mins = self.CollisionProp().OBBMins() if not unitinfo.mins else unitinfo.mins
        maxs = self.CollisionProp().OBBMaxs() if not unitinfo.maxs else unitinfo.maxs
        
        for dunitinfo in unitinfo.dummies:
            if dunitinfo.decorative:
                continue
                
            modelname = dunitinfo.modellist[0] if dunitinfo.modellist else dunitinfo.modelname
            if dunitinfo.mins and dunitinfo.maxs:
                dmins = dunitinfo.mins
                dmaxs = dunitinfo.maxs
            else:
                model = modelinfo.FindOrLoadModel(modelname)
                dmins, dmaxs = modelinfo.GetModelBounds(model)
            
            mins.x = min(mins.x, dmins.x)
            mins.y = min(mins.y, dmins.y)
            mins.z = min(mins.z, dmins.z)
        
            maxs.x = max(maxs.x, dmaxs.x)
            maxs.y = max(maxs.y, dmaxs.y)
            maxs.z = max(maxs.z, dmaxs.z)
        
        self.selectionmins = mins
        self.selectionmaxs = maxs
        
    if isserver:
        def UpdateOnRemove(self):
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
            
            self.RemoveDummies()
            
        def Precache(self):
            super().Precache()
            
            info = self.unitinfo
            
            if info.explodemodel:
                self.PrecacheModel(info.explodemodel)
            
            self.PrecacheDummies(info.dummies)
            
            if info.explodeparticleeffect:
                PrecacheParticleSystem(info.explodeparticleeffect)
                
        def GetDummies(self):
            return getattr(self.unitinfo, 'dummies', [])
            
        def Spawn(self):
            super().Spawn()
     
            self.CreateDummies(self.GetDummies(), activate=False)
            self.SetConstructionState(self.BS_CONSTRUCTED if self.constructionstate == self.BS_UNKNOWN else self.constructionstate)

        def Activate(self):
            super().Activate()
            
            if self.constructionstate == self.BS_CONSTRUCTED:
                self.BlockAreas()
                
            # IsPrecacheAllowed means we are being spawned during map load
            # Activate is still going to be called on all spawned entities
            if not self.IsPrecacheAllowed():
                for d in self.dummies:
                    d.Activate()
    else:
        def OnDataUpdateCreated(self):
            super().OnDataUpdateCreated()
            
            self.OnConstructionStateChanged()
            
        hfontsmall = None
        def OnHoverPaint(self):
            if self.constructionstate != self.BS_UNDERCONSTRUCTION:
                return
            if self.autoconstruct:
                return
        
            if not self.hfontsmall:
                schemeid = scheme().LoadSchemeFromFile("resource/GameLobbyScheme.res", "GameLobbyScheme")
                schemeobj = scheme().GetIScheme(schemeid)
                self.hfontsmall = schemeobj.GetFont("HeadlineLarge")

            pos = self.GetAbsOrigin()
            pos.z += self.CollisionProp().OBBMaxs().z + 64.0
            success, x, y = GetVectorInScreenSpace(pos)
            if not success:
                return
            s = surface()
            
            if self.maxconstructors > 0:
                constlabel = '%d / %d' % (len(self.constructors), self.maxconstructors)
            else:
                constlabel = '%d' % (len(self.constructors))
            wide, tall = s.GetTextSize(self.hfontsmall, constlabel)
            
            s.DrawSetTextFont(self.hfontsmall)
            s.DrawSetTextColor(255, 255, 255, 255)
            s.DrawSetTextPos(int(x - wide/2.0), y)
            s.DrawUnicodeString(constlabel, FontDrawType_t.FONT_DRAW_DEFAULT)
                
    def OnNewModel(self):
        super().OnNewModel()
        
        model = modelinfo.GetModel(self.GetModelIndex())
        isexplodemodel = modelinfo.GetModelName(model) == self.unitinfo.explodemodel
        
        if not isexplodemodel:
            self.UpdateBuildingActivity()
        
        if isclient and isexplodemodel:
            # Fix lighting origin for explosion model
            offsetorigin = self.GetAbsOrigin() - self.WorldSpaceCenter()
            self.customlightingoffset = offsetorigin + self.unitinfo.explodemodel_lightingoffset
        
    def UpdateBuildingActivity(self):
        """ Main method for updating building main activity.
        """
        info = self.unitinfo
        if self.constructionstate == self.BS_UNDERCONSTRUCTION and info.constructionactivity:
            self.ChangeToActivity(info.constructionactivity, updateclientanimations=False)
        elif self.constructionstate == self.BS_UPGRADING and self.activeupgrade:
            self.ChangeToActivity(self.activeupgrade.upgradeactivity, updateclientanimations=False)
        elif info.idleactivity:
            self.ChangeToActivity(info.idleactivity)
                
    def ChangeToActivity(self, act, updateclientanimations=True, forcechange=False):
        """ Changes the activity of the building to the specified activity.

            Args:
                act (Activity): the animation

            Kwargs:
                updateclientanimations (bool): Whether to update the animations.
                                               In some cases we manually trigger the progress (construction).
                                               default true.
                forcechange (bool): Force changing activity, if current activity is the same.
        """
        actname = ''
        if type(act) == str:
            actname = act
            act = Activity(self.LookupActivity(act))
        curact = self.GetSequenceActivity(self.GetSequence())
        if act != curact or forcechange:
            seq = self.SelectWeightedSequence(act)
            if seq != -1:
                self.SetCycle(0.0)
                self.ResetSequence(seq)
                self.updateclientanimations = updateclientanimations
                return True
            else:
                PrintWarning('%s ChangeToActivity: Could not find sequence for activity %s (%s)!\n' % ('Server ' if isserver else 'Client', str(act), actname))
                return False
        return False
                
    def CreateDummy(self, d, activate=False):
        """ Creates and attaches a dummy building from the provided definition.

            Args:
                d (dict): dummy configuration

            Kwargs:
                activate (bool): Calls Activate on the dummy entity
        """
        dummy = CreateUnitNoSpawn(d.name, owner_number=self.GetOwnerNumber())
        dummy.SetParent(self)
        dummy.SetLocalOrigin(d.dummyinfo.get('offset', vec3_origin))
        dummy.SetLocalAngles(d.dummyinfo.get('angle', vec3_angle))
        dummy.SetMousePassEntity(self)
        dummy.SetOwnerEntity(self)
        dummy.blocknavareas = d.dummyinfo.get('blocknavareas', True)
        dummy.blockdensitytype = d.dummyinfo.get('blockdensitytype', DENSITY_GAUSSIAN)
        dummy.constructionstate = self.constructionstate
        dummy.viewdistance = self.viewdistance
            
        DispatchSpawn(dummy)
        if activate: 
            dummy.Activate()
        self.dummies.append(dummy)
        
    @classmethod
    def PrecacheDummy(cls, d):
        """ Precaches a single dummy definition. """
        PrecacheUnit(d.name)
            
    @classmethod
    def PrecacheDummies(cls, dummies):
        """ Precaches dummies from dummy info list. """
        for dummy in dummies:
            cls.PrecacheDummy(dummy)
            
    def CreateDummies(self, dummies, activate=False):
        """ Creates dummies from dummy info list.

            Args:
                dummies (list): list of dummies to create.

            Kwargs:
                activate (bool): Call Activate on each dummy entity.
        """
        for d in dummies:
            self.CreateDummy(d, activate=activate)
            
    def DestroyDummies(self, info=None):
        """ Destroys attached dummy buildings.

            Kwargs:
                info (CTakeDamageInfo): Optional damage info to pass to each dummy.
        """
        if not info:
            info = CTakeDamageInfo(self, self, 0, 0)
        for d in self.dummies:
            d.SetParent(None)
            d.Event_Killed(info)
        self.dummies = []
        
    def RemoveDummies(self):
        """ Remove dummy buildings instantly. """
        for d in self.dummies:
            d.SetParent(None)
            UTIL_Remove(d)
        self.dummies = []
                
    def CreateVPhysics(self):
        if self.GetSolid() == SOLID_NONE or ((self.GetSolidFlags() & FSOLID_NOT_SOLID)):
            if self.VPhysicsGetObject() is not None:
                self.VPhysicsDestroyObject()
            return True

        if self.VPhysicsGetObject() is not None:
            self.VPhysicsDestroyObject()
                
        self.VPhysicsInitStatic()

        return True
        
    def UpdateClientConstructionProgress(self, basebuilding):
        if self.unitinfo.constructionactivity:
            curcycle = self.GetCycle()
            targetcycle = basebuilding.constructprogress
            cyclerate = 0.1 * gpGlobals.frametime 
            curcycle += min(cyclerate, targetcycle - curcycle)
            self.SetCycle(curcycle)
            self.SetNextClientThink(gpGlobals.curtime) 
        elif not self.unitinfo.constructionnotranstexture:
            self.SetRenderMode(RenderMode_t.kRenderTransTexture)
            self.SetRenderAlpha( 40 + int(basebuilding.constructprogress*215) )
            self.SetNextClientThink(gpGlobals.curtime + 0.2) 
             
    def ClientThink(self):
        super().ClientThink()
        
        if self.constructionstate == self.BS_UNDERCONSTRUCTION:
            # This will set the next client think time
            self.UpdateClientConstructionProgress(self)
        
    def Cancel(self):
        if self.constructionstate == self.BS_CONSTRUCTED:
            return
            
        if isserver:
            if self.purchasecosts:
                # try:
                #     resourcetype = gamerules.GetMainResource()
                #
                # except:
                #     resourcetype = 'requisition'

                resourcetype = {
                    'requisition': 'requisition',
                    'scrap': 'scrap',
                    'power': 'power',
                    'kills': 'kills',
                }

                # Give back half of the requisition costs
                assert(len(self.purchasecosts) == 1)
                req = 0
                scr = 0
                pwr = 0
                kll = 0
                for c in self.purchasecosts[0]:
                    if c[0] == resourcetype['requisition']:
                        req = c[1]
                    elif c[0] == resourcetype['scrap']:
                        scr = c[1]
                    elif c[0] == resourcetype['power']:
                        pwr = c[1]
                    elif c[0] == resourcetype['kills']:
                        kll = c[1]
                        break
                halfreq = int(req/2)
                halfscr = int(scr/2)
                halfpwr = int(pwr/2)
                halfkll = int(kll/2)

                #TODO: Make it so messages display separately from each other and not in one line.

                if halfreq > 0:
                    GiveResources(self.GetOwnerNumber(), [(resourcetype['requisition'], halfreq)])
                    MessageResourceIndicator(self.GetOwnerNumber(), self.GetAbsOrigin() + self.resourcemessageoffset,
                                             '%s +%d' % (resourcetype['requisition'], halfreq), resourcetype['requisition'])

                if halfscr > 0:
                    GiveResources(self.GetOwnerNumber(), [(resourcetype['scrap'], halfscr)], gpGlobals.curtime + 0.7)
                    MessageResourceIndicator(self.GetOwnerNumber(), (self.GetAbsOrigin() + Vector(0,0,80)) + self.resourcemessageoffset,
                                             '%s +%d' % (resourcetype['scrap'], halfscr), resourcetype['scrap'])

                if halfpwr > 0:
                    GiveResources(self.GetOwnerNumber(), [(resourcetype['power'], halfpwr)], gpGlobals.curtime + 0.7)
                    MessageResourceIndicator(self.GetOwnerNumber(), (self.GetAbsOrigin() + Vector(0,0,80)) + self.resourcemessageoffset,
                                             '%s +%d' % (resourcetype['power'], halfpwr), resourcetype['power'])

                if halfkll > 0:
                    GiveResources(self.GetOwnerNumber(), [(resourcetype['kills'], halfkll)])
                    MessageResourceIndicator(self.GetOwnerNumber(), self.GetAbsOrigin() + self.resourcemessageoffset,
                                             '%s +%d' % (resourcetype['kills'], halfkll), resourcetype['kills'])

            self.Remove()
            
    def CancelUpgrade(self):
        if not self.activeupgrade:
            return
            
        if isserver:
            self.activeupgrade.CancelUpgrade(self)
            self.activeupgrade = None

    if isclient:
        def OnUnitTypeChanged(self, oldunittype):
            super().OnUnitTypeChanged(oldunittype)
            
            self.UpdateBuildingActivity()
            
            if self.isconstructed:
                self.CreateCoverSpots()

        def OnConstructionStateChanged(self):
            state = self.constructionstate
            if state == self.BS_UNDERCONSTRUCTION:
                self.SetRenderMode(RenderMode_t.kRenderTransTexture)
                self.SetNextClientThink(gpGlobals.curtime + 0.2)
                self.UpdateVisibility()
                self.constructedlisthandle.Disable()
                self.UpdateBuildingActivity()
            elif state == self.BS_PRECONSTRUCTION:
                self.SetRenderMode(RenderMode_t.kRenderTransTexture)
                self.SetRenderAlpha(40)
                self.UpdateVisibility()
            elif state == self.BS_UPGRADING:
                self.SetRenderMode(RenderMode_t.kRenderNormal)
                self.SetNextClientThink(gpGlobals.curtime + 0.2)
                self.UpdateVisibility()
                self.UpdateBuildingActivity()
            elif state == self.BS_CONSTRUCTED:
                self.SetRenderMode(RenderMode_t.kRenderNormal)
                self.UpdateVisibility()
                self.constructedlisthandle.Enable()
                self.UpdateBuildingActivity()
                self.OnConstructed()
                #self.BlockAreas()  # TODO: Maybe block on client too?
            self.UpdateAbilities()
            
    @serveronly_assert
    def SetConstructionState(self, state):
        # Don't allow to change the state from constructed to something else unless upgrading
        if self.constructstateinitialized and self.constructionstate == self.BS_CONSTRUCTED and state != self.BS_UPGRADING:
            return
    
        self.constructstateinitialized = True
        self.constructionstate = state
        unitinfo = self.unitinfo
        blockareas = False
        
        if state == self.BS_PRECONSTRUCTION:
            self.SetSolid(SOLID_NONE)
            self.constructedlisthandle.Disable()
            for d in self.dummies:
                d.SetSolid(SOLID_NONE)
        elif state == self.BS_UNDERCONSTRUCTION:
            self.SetSolid(self.buildingsolidmode)
            self.constructprogress = 0.0
            self.health = int(unitinfo.constructstarthp*self.maxhealth) # start construct, interpolate from 1 to maxhealth
            self.constructhpmax = self.maxhealth - self.health
            self.constructhpbuildup = 0.0
            self.viewdistance = int(unitinfo.viewdistance*0.5) 
            self.SetThink(self.ConstructThink)
            #for d in self.dummies:
            #    d.SetSolid(self.buildingsolidmode)
            self.OnLostFullHealth() # Grabs nearby workers
            blockareas = True
            
            FireSignalRobust(buildingstarted, building=self)
        elif state == self.BS_UPGRADING:
            assert self.activeupgrade or self.GetOwnerEntity(), \
                'Expecting building activeupgrade or owner entity to be set'
            self.SetSolid(self.buildingsolidmode)
            self.constructprogress = 0.0
            self.constructhpmax = 0
            self.constructhpbuildup = 0.0
            self.viewdistance = int(unitinfo.viewdistance*0.75)
            self.SetThink(self.ConstructThink)
            #for d in self.dummies:
            #    d.SetSolid(self.buildingsolidmode)
            self.OnLostFullHealth() # Grabs nearby workers
        else: # BS_CONSTRUCTED
            self.constructprogress = 1.0
            self.SetSolid(self.buildingsolidmode)
            self.SetThink(self.BuildThink)
            
            self.viewdistance = int(unitinfo.viewdistance)
            if self.activeupgrade:
                self.activeupgrade.CallFinishUpgrade(self)
                self.activeupgrade = None
            else:
                self.constructedlisthandle.Enable()
                blockareas = True
                self.OnConstructed()
                #for d in self.dummies:
                #    d.SetSolid(self.buildingsolidmode)
                    
                FireSignalRobust(buildingfinished, building=self)
        
        self.UpdateAbilities()
        if state == self.BS_CONSTRUCTED:
            self.SetInitialAbilityRechargeTimes()
        self.SetNextThink(gpGlobals.curtime)
        self.CreateVPhysics()
        if blockareas:
            self.BlockAreas()
        for d in self.dummies:
            d.SetConstructionState(state)
        
    def OnConstructed(self):
        if isserver:
            self.addpopulation = True
            if self.unitinfo.providespopulation:
                AddPopulation(self.GetOwnerNumber(), self.unitinfo.providespopulation)
                
            self.UpdateResourceCaps(True)
            self.UpdateResourceThink()
            self.UpdateEnergyThink()
            self.CheckTech()
            
            self.onconstructed.FireOutput(self, self)
        
        self.CreateCoverSpots()

    def CheckTech(self):
        if not isserver:
            return
        # Don't do any tech checks until we are constructed
        # TODO: Maybe add something to clear the current tech, but shouldn't be needed
        #       since it's only one way (from not constructed to constructed)
        if not self.constructstateinitialized or self.constructionstate != self.BS_CONSTRUCTED:
            return
        super().CheckTech()
        
    def UpdateResourceThink(self):
        if not self.generateresources or self.constructionstate != self.BS_CONSTRUCTED or not self.IsAlive():
            self.SetThink(None, 0.0, 'ResourceThink')
            return
        self.SetThink(self.ResourceThink, gpGlobals.curtime + self.generateresources['interval'], 'ResourceThink')

    def CanGenerateResources(self, resourcetype, amount):
        """ Optional hook to skip resource generation for this interval.

            Args:
                resourcetype (str): Resource type for which to check (requisition, scrap, power, etc)
                amount (float): the amount to be generated

            Returns:
                bool: True to generate, False to prevent it.
        """
        owner = self.GetOwnerNumber()
            
        if owner < OWNER_LAST:
            return False
         
        resinfo = GetResourceInfo(resourcetype)
        if resinfo and resinfo.iscapped:
            owner = self.GetOwnerNumber()
            if resources[owner][resourcetype] + amount > resourcecaps[owner][resourcetype]:
                MessageResourceIndicator(owner, self.resourcemessageorigin, 'Capped', resourcetype)
                return False
        
        return True
       
    @property
    def resourcemessageorigin(self):
        origin = self.GetAbsOrigin() + self.resourcemessageoffset
        if not self.resourcemessageatorigin:
            origin.z += self.unitinfo.maxs.z
        return origin
        
    def ResourceThink(self):
        info = self.unitinfo
        if not self.generateresources:
            return
            
        resourcetype = self.generateresources['type']
        amount = self.generateresources['amount']
            
        resourceislimited = resourcetype in self.resourcesleft

        if resourceislimited:
            amount = min(amount, self.resourcesleft[resourcetype])
            
        if not self.CanGenerateResources(resourcetype, amount):
            self.SetNextThink(gpGlobals.curtime + self.generateresources['interval'], 'ResourceThink')
            return
            
        owner = self.GetOwnerNumber()
        
        if resourceislimited:
            self.resourcesleft[resourcetype] -= amount
            
            if amount <= 0:
                # Nothing to generate, stop thinking
                return
        
        if info.splitgeneratedresources:
            owners = ListAlliesOfOwnerNumber(owner)
            splitfactor = 1.0 / float(len(owners)) if info.reducesplittedresources else 1
            for owner in owners:
                GiveResources(owner, [(resourcetype, amount*splitfactor)], firecollected=True)
            MessageResourceIndicator(owners, self.resourcemessageorigin, '+%.2f' % (amount*splitfactor), resourcetype)
        else:
            MessageResourceIndicator(owner, self.resourcemessageorigin, '+%.2f' % (amount), resourcetype)
            GiveResources(owner, [(resourcetype, amount)], firecollected=True)
        self.OnGenerateResource(resourcetype, amount)

        self.SetNextThink(gpGlobals.curtime+self.generateresources['interval'], 'ResourceThink')
        
    def OnGenerateResource(self, resourcetype, amount):
        ''' Called on resource being generated by building. '''
        pass

    def UpdateEnergyThink(self):
        if self.maxenergy <= 0 or self.constructionstate != self.BS_CONSTRUCTED:
            return
        self.SetThink(self.EnergyThink, gpGlobals.curtime + 0.2, 'EnergyThink')
        
    def EnergyThink(self):
        self.UpdateEnergy(0.2)
        self.SetNextThink(gpGlobals.curtime + 0.2, 'EnergyThink')
        
    def NeedsUnitConstructing(self, unit=None):
        ''' Tests if the building needs construction.
            Optional may pass an unit for testing.
        
            Kwargs:
               unit (entity): Entity to be tested.
        '''
        if self.autoconstruct:
            return False
        if not self.constructionstate in [self.BS_UNDERCONSTRUCTION, self.BS_UPGRADING]:
            return False
        return self.maxconstructors == 0 or (len(self.constructors) < self.maxconstructors)
        
    def ConstructThink(self):
        ''' Main think during construction or upgrading the building. 
        
            When autoconstruct is active, this method is responsible for performing the
            construction steps.
        '''
        if self.autoconstruct:
            self.ConstructStep(self.constructthinktime)
        self.StatusEffectsThink(self.constructthinktime)
        self.SetNextThink(gpGlobals.curtime + self.constructthinktime)

    def ConstructStep(self, intervalamount):
        """ Construct method. Advances construction by the specified time interval.
        
            Args:
               intervalamount (float): Time interval to add.
        """
        if self.constructprogress >= 1.0: 
            return True
            
        # Cap speed at four or more workers
        n = len(self.constructors)
        if n > 1:
            intervalamount *= 0.695 #(1 + ((n - 1) ** 0.5)) / n
            
        if self.activeupgrade:
            if not self.activeupgrade.upgradetime:
                advanceamount = 1.0
            else:
                advanceamount = intervalamount / self.activeupgrade.upgradetime
        else:
            if not self.unitinfo.buildtime:
                advanceamount = 1.0
            else:
                advanceamount = intervalamount / self.unitinfo.buildtime
            
        self.constructprogress += advanceamount
        
        self.constructhpbuildup += advanceamount * self.constructhpmax
        if self.constructhpbuildup > 1:
            addhp = floor(self.constructhpbuildup)
            self.constructhpbuildup -= addhp
            
            self.health += int(addhp)
            self.health = min(self.health, self.maxhealth)

        if self.constructprogress >= 1.0:
            if self.maxhealth - self.health < 20:
                self.health = self.maxhealth # Snap to maxhealth is difference is less than 20
            self.SetConstructionState(self.BS_CONSTRUCTED)
            return True
        return False
        
    # Animation
    def ExplodeHandler(self, event):
        """ Client side explosion handler during building destruction.

            Args:
                event (int): Event data
        """
        info = self.unitinfo
        
        if isclient:
            # Clear the cover spots on the client side
            self.DestroyCoverSpots()
            # Make sure hp/progress bars are hidden
            self.HideBars()

        # Swap model if specified
        if info.explodemodel:
            self.SetModel(info.explodemodel)
            #offsetorigin = self.GetAbsOrigin() - self.WorldSpaceCenter()
            #self.customlightingoffset = offsetorigin + info.explodemodel_lightingoffset
        
        # Own explode activity, if any
        if info.explodeactivity:
            act = Activity(self.LookupActivity(info.explodeactivity))
            self.SetCycle(0.0)
            self.ResetSequence(self.SelectWeightedSequence(act))

        self.UnFlattenFlora()

    def DoAnimation(self, animevent, data=0):
        """ Use the data argument for anything you like.

            Args:
                animevent (int): the event

            Kwargs:
                data (int): event data
        """
        if isserver:
            filter = CPVSFilter(self.GetAbsOrigin())
            filter.UsePredictionRules()
            self.SendEvent(filter, animevent, data)
        self.ReceiveEvent(animevent, data)
        
    def GetSequenceDestructionTime(self):
        maxtime = max(3.0, self.SequenceDuration()) # Use 3 second minimum
        for d in self.dummies:
            maxtime = max(maxtime, d.SequenceDuration())
        return maxtime + 2.0
        
    def DestructThink(self):
        """ Think function that is supposed to destruct/explode us in some cool way."""
        self.UpdateResourceThink()
        
        info = self.unitinfo
        
        # Don't block units or their LOS after being destroyed (destruction is just an effect)
        self.SetSolid(SOLID_NONE) 
        
        if info.explodeparticleeffect:
            DispatchParticleEffect(info.explodeparticleeffect, self.GetAbsOrigin() + info.explodeparticleoffset, self.GetAbsAngles())
            
        if info.explodeshake:
            UTIL_ScreenShake(self.GetAbsOrigin(), info.explodeshake[0], info.explodeshake[1], 
                info.explodeshake[2], info.explodeshake[3], SHAKE_START, True)
                
        if info.sound_death:
            self.EmitSound(info.sound_death)
            
        # Prefer explode animation if available. Otherwise use sink as fallback.
        if info.explodeactivity:
            self.DoAnimation(self.ANIM_EXPLODE)
            self.SetThink(self.SUB_Remove, gpGlobals.curtime+self.GetSequenceDestructionTime())
        else:
            self.Sink()
            self.SetThink(self.SUB_Remove, gpGlobals.curtime+5.0)
            
    def Sink(self):
        self.SetMoveType(MOVETYPE_PUSH) # Required when using SetMoveDoneTime
        self.SetSolidFlags(FSOLID_NOT_SOLID)
        vAbsMins = Vector(); vAbsMaxs = Vector();
        self.CollisionProp().WorldSpaceAABB(vAbsMins, vAbsMaxs)
        destination = self.GetAbsOrigin() + (Vector(0,0,-1) * (vAbsMaxs.z - vAbsMins.z + 32.0))
        self.LinearMove(destination, 250.0)
        
    def LinearMove(self, vecDest, flSpeed):
        """ Calculate m_vecVelocity and m_flNextThink to reach vecDest from
            GetOrigin() traveling at flSpeed. """
        # Already there?
        if vecDest == self.GetLocalOrigin():
            self.MoveDone()
            return
            
        # set destdelta to the vector needed to move
        vecDestDelta = vecDest - self.GetLocalOrigin()
        
        # divide vector length by speed to get time to reach dest
        flTravelTime = vecDestDelta.Length() / flSpeed

        # set m_flNextThink to trigger a call to LinearMoveDone when dest is reached
        self.SetMoveDoneTime(flTravelTime)

        # scale the destdelta vector by the time spent traveling to get velocity
        self.SetLocalVelocity(vecDestDelta / flTravelTime)
        
    if isclient:
        def GetBuildProgress(self):
            """ Returns build/construct progress for UnitProgressBarScreen.
            
                Production progress is returned by the UnitBaseFactoryShared.
            """
            state = self.constructionstate
            if state in [self.BS_UNDERCONSTRUCTION, self.BS_UPGRADING]:
                return self.constructprogress
            return 0
        
        # Progress bar on hover
        def UpdateProgressBar(self):
            if self.ShouldShowProgressBar():
                self.ShowProgressBar()
            else:
                self.HideProgressBar()
                
        def ShouldShowProgressBar(self):
            localplayer = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
            if not localplayer or self.IRelationType(localplayer) != D_LI:
                return False
            if not localplayer.IsMouseHoveringEntity(self) and not self.ShouldAlwaysShowBars():
                return False
            state = self.constructionstate
            return state in [self.BS_UNDERCONSTRUCTION, self.BS_UPGRADING]
            
        def ShowProgressBar(self):
            if self.progressbarscreen:
                return
            self.progressbarscreen = UnitProgressBarScreen(self)
            
        def HideProgressBar(self):
            if not self.progressbarscreen:
                return
            self.progressbarscreen.Shutdown()
            self.progressbarscreen = None
            
        progressbarscreen = None
        def ShowBars(self):
            self.UpdateProgressBar()
                
            super().ShowBars()
            
        def HideBars(self):
            self.UpdateProgressBar()
            
            super().HideBars()

    events = dict(BaseClass.events)
    events.update({
        'ANIM_EXPLODE' : 'ExplodeHandler',
    })
        
    # Show a custom panel when this is the only selected building    
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            from core.hud import HudBuildSingleUnit, HudBuildConstruction
            if self.constructionstate != self.BS_CONSTRUCTED:
                self.unitpanelclass = HudBuildConstruction
            else:
                self.unitpanelclass = HudBuildSingleUnit  
                
    @property
    def isconstructed(self):
        return self.constructionstate == self.BS_CONSTRUCTED
                
    # States
    BS_UNKNOWN = -1
    BS_PRECONSTRUCTION = 0
    BS_UNDERCONSTRUCTION = 1
    BS_CONSTRUCTED = 2
    BS_UPGRADING = 3 # Indicates a building upgrade is being performed, allowing builders to construct the building again

    # Default variables
    constructthinktime = 0.1
    #: Time it takes to construct to full health when a single unit is building.
    constructtime = FloatField(value=5.0, keyname='constructtime', displayname='Construct Time', helpstring='Time it takes to construct this building.')
    #: If False, this building requires a builder to be constructed.
    autoconstruct = BooleanField(value=True, keyname='autoconstruct', displayname='Auto Construct', 
                                 helpstring='Automatically construct this building without the need of a worker.')
    constructability = StringField(value='construct', displayname='Construct Ability',
                                 helpstring='Allows overriding the default construct ability. Can be used to restrict constructing this building to certain units.')
                                 
    #: Current building state
    constructionstate = IntegerField(value=BS_UNKNOWN, 
                                     keyname='constructed', 
                                     displayname='Construction State',
                                     helpstring='Initial state of building',
                                     networked=True,
                                     clientchangecallback='OnConstructionStateChanged',
                                     choices=[(BS_PRECONSTRUCTION, 'Pre-Construction'), 
                                              (BS_UNDERCONSTRUCTION, 'Under Construction'), 
                                              (BS_CONSTRUCTED, 'Constructed')]
                                    )
    constructstateinitialized = BooleanField(value=False)
    #: Construction progress (if not constructed yet)
    constructprogress = FloatField(0.0, networked=True, keyname='constructprogress', 
                                   displayname='Construct Progress', helpstring='Construct progress, ranging from 0.0 to 1.0')
    #: Maximum number of constructors (0 for unlimited)
    maxconstructors = IntegerField(value=2)
    #: Active constructors
    # TODO: Support saving this field.
    constructors = SetField(networked=True, save=False)
    #: Reference to building upgrade ability
    activeupgrade = None
    #: The solid mode used when constructed
    buildingsolidmode = SOLID_VPHYSICS
    # Do resource message from origin
    resourcemessageatorigin = False
    # Offset for resource ui messages from unit origin
    resourcemessageoffset = vec3_origin
    # Resources left
    resourcesleft = DictField(networked=True, default=0)
    
    # Outputs
    onconstructed = OutputField(keyname='OnConstructed', displayname='OnConstructed', helpstring='Triggered when this building is constructed')
    
    constructhpmax = IntegerField(value=1)
    constructhpbuildup = FloatField(value=0.0)
    purchasecosts = None

    # Base activity list for buildings
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_CONSTRUCTION',
        'ACT_EXPLODE',
        'ACT_WORK',
    ])