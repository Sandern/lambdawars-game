from srcbase import DAMAGE_NO, DAMAGE_YES, Color, SOLID_BBOX
from vmath import Vector
from gamerules import gamerules
from playermgr import OWNER_NEUTRAL, OWNER_LAST, dbplayers, relationships
from core.units import UnitInfo, CreateUnit, GetUnitInfo, CreateUnitList, UnitListObjectField
from core.factions import GetFactionInfo
from core.notifications import DoNotificationEnt, GetNotifcationFilterForOwnerAndAllies
from core.abilities import AbilityBuildingUpgrade, AbilityTargetBuildingUpgrade
from core.decorators import clientonly
from entities import entity, networked, Disposition_t, FOWFLAG_BUILDINGS_NEUTRAL_MASK
from core.buildings import UnitBaseBuilding as BaseClass, WarsBuildingInfo, BuildingInfoMetaClass, CreateDummy
from fields import StringField, OutputField, GenericField, FloatField, FlagsField, IntegerField, ListField, BooleanField, fieldtypes
from utils import UTIL_ListPlayersForOwnerNumber, UTIL_ListForOwnerNumberWithDisp
from particles import PrecacheParticleSystem, ParticleAttachment_t
from collections import defaultdict

if isserver:
    from entities import CTriggerMultiple, entitylist
    from gameinterface import GameEvent, FireGameEvent
    from core.signals import FireSignalRobust, cp_fortified, cp_fortificationdestroyed, prelevelinit
    from core.dispatch import receiver
else:
    from vgui import cursors
    from vgui.entitybar import UnitBarScreen
    from entities import CLIENT_THINK_ALWAYS, CLIENT_THINK_NEVER

if isserver:
    # Used by lessons
    started_fortification_once = defaultdict(lambda: False)

    @receiver(prelevelinit)
    def CPPreLevelInit(*args, **kwargs):
        started_fortification_once.clear()


class AbilityFortifyControlPoint(AbilityBuildingUpgrade):
    hidden = True
    resource_category = 'economy'
    sai_hint = AbilityBuildingUpgrade.sai_hint | set(['sai_fortifyupgrade'])
    refundmodifier = 0.75
    
    if isserver:
        def StartUpgrade(self, building):
            building.OnStartFortifcationUpgrade()
            
        def FinishUpgrade(self, building):
            building.PerformFortifcationUpgrade()
            self.Completed()
            
        def CancelUpgrade(self, building):
            building.CancelFortifying()
            self.Cancel()
        
    @classmethod 
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        if unit.playercapturing:
            requirements.add('playercapturing')
        return requirements


class AbilityTargetFortifyControlPoint(AbilityTargetBuildingUpgrade, UnitInfo):
    hidden = True
    resource_category = 'economy'
    targetunitinfo = 'control_point'
    targetupgradelevel = IntegerField(value=-1)
    refundmodifier = 0.75
    
    def StartUpgrade(self, building):
        building.OnStartFortifcationUpgrade()
        
    def FinishUpgrade(self, building):
        building.PerformFortifcationUpgrade()
        self.Completed()
        
    def CancelUpgrade(self, building):
        building.CancelFortifying()
        self.Cancel()
        
    def IsValidBuildingTarget(self, building):
        return building.upgradelevel == (self.targetupgradelevel-1)


# Fortify upgrades
class AbilityFortifyControlPointLvl1Reb(AbilityFortifyControlPoint):  #scrap to level 1
	name = 'fortify_control_point_lvl1'
	image_name = 'vgui/rebels/buildings/build_reb_flaglevelup.vmt'
	displayname = '#RebFortifyControlPointLvl1_Name'
	description = '#RebFortifyControlPointLvl1_Description'
	upgradetime = 50.0
	costs = [('requisition', 50)]
	#costs = [[('scrap', 15), ('requisition', 25)], [('power', 15), ('requisition', 25)]]
	targetupgradelevel = 1


class AbilityAltFortifyControlPointLvl1Reb(AbilityFortifyControlPoint):    #power to level 1
	name = 'fortify_control_point_lvl1_power'
	image_name = 'vgui/rebels/buildings/build_reb_flaglevelup.vmt'
	displayname = '#RebFortifyControlPointLvl1_Name'
	description = '#RebFortifyControlPointLvl1_Description'
	upgradetime = 50.0
	costs = [('requisition', 50)]
	#costs = [[('scrap', 15), ('requisition', 25)], [('power', 15), ('requisition', 25)]]
	targetupgradelevel = 1


class AbilityFortifyControlPointLvl2Reb(AbilityFortifyControlPoint):    #scrap to level 2
	name = 'fortify_control_point_lvl2_reb_scrap'
	image_name = 'vgui/rebels/buildings/build_reb_flaglevelup.vmt'
	displayname = '#RebFortifyControlPointLvl2_Name'
	description = '#RebFortifyControlPointLvl2_Description'
	upgradetime = 50.0
	costs = [('requisition', 100)]
	#costs = [[('scrap', 30), ('requisition', 35)], [('power', 30), ('requisition', 35)]]
	targetupgradelevel = 2

# Comb flag upgrades

class AbilityFortifyControlPointLvl2Comb(AbilityFortifyControlPoint):   # power to level 2
	name = 'fortify_control_point_lvl2_comb_power'
	image_name = 'vgui/combine/buildings/build_comb_flaglevelup.vmt'
	displayname = '#CombFortifyControlPointLvl2_Name'
	description = '#CombFortifyControlPointLvl2_Description'
	upgradetime = 50.0
	costs = [('requisition', 100)]
	#costs = [[('scrap', 30), ('requisition', 35)], [('power', 30), ('requisition', 35)]]
	targetupgradelevel = 2

# Base definition for Control Point
class ControlPointInfoMetaClass(BuildingInfoMetaClass):
    def __new__(cls, name, bases, dct):
        newcls = BuildingInfoMetaClass.__new__(cls, name, bases, dct)
        
        # Parse construction dummy
        if newcls.constructiondummy:
            class NewDummyInfo(newcls.constructiondummy):
                hidden = True
                name = '%s_constr_dummy' % (newcls.name)
                customeyeoffset = Vector(0, 0, 100)
                decorative = True
            newcls.constructiondummy = NewDummyInfo

        return newcls
        
CP_MAXGENERATE = 2000


class BaseControlPointInfo(WarsBuildingInfo, metaclass=ControlPointInfoMetaClass):
    name = "control_point"
    cls_name = "control_point"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_wood.mdl'
    explodemodel = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_wood_des.mdl'
    displayname = '#ControlPoint_Name'
    description = '#ControlPoint_Description'
    minimaphalfwide = 4
    minimaphalftall = 4
    minimaplayer = -1 # Draw earlier than units to avoid overlapping
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    minimapicon_name = 'hud_minimap_flag'
    viewdistance = 704
    generateresources = {'type': 'requisition', 'amount': 1, 'interval': 4, 'maxgenerate': CP_MAXGENERATE}
    splitgeneratedresources = True
    reducesplittedresources = False
    ispriobuilding = False # Excludes this building from Annihilation victory conditions
    sai_hint = set(['sai_controlpoint'])
    sound_select = 'unit_controlpoint_select'
    
    mins = Vector(-55, -55, 0)
    maxs = Vector(55, 55, 75)
    
    dummies = [
        CreateDummy(
            modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_wood_base_0.mdl',
            offset=Vector(0, 0, 0),
            decorative=True,
        )
    ]
    
    particles = []
    
    constructiondummy = None
    constructionparticles = [
        {'name': 'pg_combine_flag_progress'}
    ]
    
    ability_0 = 'fortify_control_point_lvl1'
    #ability_1 = 'fortify_control_point_lvl1_power'
    ability_8 = 'cancelupgrade'


# Rebel Control Points
class RebControlPointLvl1Info(BaseControlPointInfo):
    name = "control_point_reb_lvl1"
    displayname = '#ControlPointFortL1_Name'
    description = '#ControlPointFortL1_Description'
    health = 400
    viewdistance = 1024
    ability_0 = 'fortify_control_point_lvl2_reb_scrap'
    ability_8 = 'cancelupgrade'
    generateresources = {'type': 'requisition', 'amount': 1.0, 'interval': 2.0, 'maxgenerate': CP_MAXGENERATE}
    modelname = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_rebels.mdl'
    dummies = [
        CreateDummy(
            offset=Vector(0, 0, 0),
            modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebel_base_0.mdl',
            decorative=True,
        ),
    ]
    
    constructiondummy = CreateDummy(
        offset=Vector(0, 0, 0),
        modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebels_base_construction.mdl',
        explodemodel='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebels_base_construction_des.mdl',
        explodeactivity='ACT_EXPLODE',
        constructionnotranstexture=True,
    )


class RebControlPointLvl2Info(BaseControlPointInfo):
    name = "control_point_reb_lvl2"
    displayname = '#ControlPointFortL2_Name'
    description = '#ControlPointFortL2_Description'
    health = 700
    viewdistance = 1280
    ability_0 = None
    ability_1 = None
    generateresources = {'type': 'requisition', 'amount': 2.0, 'interval': 1, 'maxgenerate': CP_MAXGENERATE}
    modelname = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_rebels.mdl'
    dummies = [
        CreateDummy(
            offset=Vector(0, 0, 0),
            modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebel_base_2.mdl',
            decorative=True,
        ),
    ]
    
    constructiondummy = CreateDummy(
        offset=Vector(0, 0, 0),
        modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebels_base_construction.mdl',
        explodemodel='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_rebels_base_construction_des.mdl',
        explodeactivity='ACT_EXPLODE',
        constructionnotranstexture=True,
    )

# Combine Control Points
class CombControlPointLvl1Info(BaseControlPointInfo):
    name = "control_point_comb_lvl1"
    displayname = '#ControlPointFortL1_Name'
    description = '#ControlPointFortL1_Description'
    health = 400
    viewdistance = 1024
    ability_0 = 'fortify_control_point_lvl2_comb_power'
    ability_8 = 'cancelupgrade'
    generateresources = {'type': 'requisition', 'amount': 1.0, 'interval': 2.0, 'maxgenerate': CP_MAXGENERATE}
    modelname = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_combine.mdl'
    particles = [
        {'name': 'pg_combine_flag'},
    ]

class CombControlPointLvl2Info(BaseControlPointInfo):
    name = "control_point_comb_lvl2"
    displayname = '#ControlPointFortL2_Name'
    description = '#ControlPointFortL2_Description'
    health = 700
    viewdistance = 1280
    ability_0 = None
    ability_1 = None
    generateresources = {'type': 'requisition', 'amount': 2.0, 'interval': 1, 'maxgenerate': CP_MAXGENERATE}
    modelname = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_combine.mdl'
    dummies = [
        CreateDummy(
            offset=Vector(0, 0, 0),
            modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_combine_base_0.mdl',
            decorative=True,
        ),
    ]
    particles = [
        {'name': 'pg_combine_flag'},
    ]
    
controlpointlist = CreateUnitList()

if isserver:
    @entity('trigger_capture_area')
    class CaptureArea(CTriggerMultiple):
        def FindControlPoint(self):
            if self.controlpoint:
                return
                
            if not self.controlpointname:
                PrintWarning('CaptureArea: No control point name set!\n')
                return
            self.controlpoint = entitylist.FindEntityByName(None, self.controlpointname)
            if not self.controlpoint:
                PrintWarning('CaptureArea: No control point named %s!\n' % (self.controlpointname))
                return
             
            try:
                self.controlpoint.capturearea = self.GetHandle()
            except AttributeError:
                PrintWarning('CaptureArea: Invalid control point named %s!\n' % (self.controlpointname))
                return
    
        def Spawn(self):
            super().Spawn()
            
            self.FindControlPoint()
                    
        def OnRestore(self):
            super().OnRestore()
            
            self.FindControlPoint()
                    
        controlpoint = None
                
        controlpointname = StringField(value='', keyname='control_point')
        spawnflags = FlagsField(keyname='spawnflags', flags=[
                ('TRIGGER_ALLOW_CLIENTS', 0x01, True), # Players can fire this trigger
                ('TRIGGER_ALLOW_NPCS', 0x02, True), # NPCS can fire this trigger
                ('TRIGGER_ALLOW_PUSHABLES', 0x04, False), # Pushables can fire this trigger
                ('TRIGGER_ALLOW_PHYSICS', 0x08, False), # Physics objects can fire this trigger
                ('TRIGGER_ONLY_PLAYER_ALLY_NPCS', 0x10, False), # *if* NPCs can fire this trigger, this flag means only player allies do so
                ('TRIGGER_ONLY_CLIENTS_IN_VEHICLES', 0x20, False), # *if* Players can fire this trigger, this flag means only players inside vehicles can 
                ('TRIGGER_ALLOW_ALL', 0x40, False), # Everything can fire this trigger EXCEPT DEBRIS!
                ('TRIGGER_ONLY_CLIENTS_OUT_OF_VEHICLES', 0x200, False), # *if* Players can fire this trigger, this flag means only players outside vehicles can 
                ('TRIG_PUSH_ONCE', 0x80, False), # trigger_push removes itself after firing once
                ('TRIG_PUSH_AFFECT_PLAYER_ON_LADDER', 0x100, False), # if pushed object is player on a ladder, then this disengages them from the ladder (HL2only)
                ('TRIG_TOUCH_DEBRIS', 0x400, False), # Will touch physics debris objects
                ('TRIGGER_ONLY_NPCS_IN_VEHICLES', 0X800, False), # *if* NPCs can fire this trigger, only NPCs in vehicles do so (respects player ally flag too)
                ('TRIGGER_PUSH_USE_MASS', 0x1000, False), # Correctly account for an entity's mass (CTriggerPush::Touch used to assume 100Kg)
            ],
        )
        
if isclient:
    class ControlCaptureBarScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super(ControlCaptureBarScreen, self).__init__(unit,
                Color(), Color(40, 40, 40, 250), Color(150, 150, 150, 0), 
                offsety=16.0, worldsizey=16.0, worldbloatx=128.0)
            
        def Draw(self):
            if self.unit.IsInFOW():
                return
                
            panel = self.GetPanel()
            panel.weight = self.unit.clientcaptureprogress
            
            owner = self.unit.GetOwnerNumber()
            if owner != OWNER_NEUTRAL:
                panel.barcolor = dbplayers[OWNER_NEUTRAL].color
            else:
                panel.barcolor = dbplayers[self.unit.playercapturing].color
                    
            super(ControlCaptureBarScreen, self).Draw()

@networked
class BaseControlPoint(BaseClass):
    def __init__(self):
        super().__init__()

        if isserver:
            self.viewdistance = 1024.0

    if isclient:
        oldplayercapturing = None
        showingcapturebar = False
        flagpose = -1
        
        SKIN_DEFAULT = 0
        SKIN_REBELS = 1
        SKIN_COMBINE = 2
        
        def UpdateOnRemove(self):
            self.HideCaptureBar()
            self.areas = []

            self.DestroyControlPointParticles()
        
            super().UpdateOnRemove()
            
            self.controlpointlisthandle.Disable()

        def ShowCaptureBar(self):
            if self.showingcapturebar:
                return
                
            self.capturebarscreen = ControlCaptureBarScreen(self)
                
            self.showingcapturebar = True
            
        def HideCaptureBar(self):
            if not self.showingcapturebar:
                return
                
            self.capturebarscreen.Shutdown()
            self.capturebarscreen = None
                
            self.showingcapturebar = False

        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if self.oldplayercapturing != self.playercapturing:
                if self.playercapturing:
                    self.ShowCaptureBar()
                    self.SetNextClientThink(CLIENT_THINK_ALWAYS)
                else:
                    self.UpdateTeamColorAndSkin(self.GetOwnerNumber())
                    self.HideCaptureBar()
                self.oldplayercapturing = self.playercapturing
                
            if self.clientcaptureprogress != self.captureprogress:
                # Make sure the pose parameter + team color is correct
                self.SetNextClientThink(CLIENT_THINK_ALWAYS)
                
        __lastteamcolorowner = -1

        def UpdateTeamColorAndSkin(self, owner):
            if self.__lastteamcolorowner == owner or owner == None:
                return
                
            c = dbplayers[owner].color
            self.SetTeamColor(Vector( c.r()/255.0, c.g()/255.0, c.b()/255.0 )) 
            
            if owner < OWNER_LAST:
                self.skin = self.SKIN_DEFAULT
            elif dbplayers[owner].faction == 'rebels':
                self.skin = self.SKIN_REBELS
            elif dbplayers[owner].faction == 'combine':
                self.skin = self.SKIN_COMBINE
            else:
                self.skin = self.SKIN_DEFAULT
                
            self.__lastteamcolorowner = owner
                
        def ClientThink(self):
            super().ClientThink()
            
            if self.flagpose == -1:
                return
                
            # Move in one second to 100.0 if nobody is capturing
            # Don't change skin/owner, should already be correct
            '''if not self.playercapturing:
                delta = gpGlobals.frametime * 100.0
                cur = self.GetPoseParameter(self.flagpose)
                new = min(100.0, cur + delta)
                self.SetPoseParameter(self.flagpose, new)
                if new == 100.0:
                    self.SetNextClientThink(CLIENT_THINK_NEVER)
                return'''
                
            # Stop thinking if no player is capturing
            if self.playercapturing is None and self.playerholding is None and self.captureprogress == self.clientcaptureprogress:
                self.SetNextClientThink(CLIENT_THINK_NEVER)
                return
            
            # Update client progress
            progressdelta = gpGlobals.frametime / self.capturetime if self.capturetime > 0 else 1
            if self.clientcaptureprogress < self.captureprogress:
                self.clientcaptureprogress += progressdelta
                if self.clientcaptureprogress > self.captureprogress:
                    self.captureprogress = self.clientcaptureprogress
            elif self.clientcaptureprogress > self.captureprogress:
                self.clientcaptureprogress -= progressdelta
                if self.clientcaptureprogress < self.captureprogress:
                    self.captureprogress = self.clientcaptureprogress
                    
            if abs(self.clientcaptureprogress - self.captureprogress) > 0.2:
                self.clientcaptureprogress = self.captureprogress
                
            curowner = self.GetOwnerNumber()
            
            # Update pose parameter of flag position
            progress = self.clientcaptureprogress
            
            # This code first descends the flag at halway (0 - 0.5) and then raises it again with the new owner (0.5 - 1.0)
            '''if progress > 0.5:
                progress = (progress - 0.5) / 0.5
                # Ascending the flag
                self.SetPoseParameter(self.flagpose, progress * 100.0)
                self.UpdateTeamColorAndSkin(self.playercapturing if self.playercapturing else curowner)
            else:
                progress = progress / 0.5
                # Raising the flag
                self.SetPoseParameter(self.flagpose, 100.0 * (1.0 - progress))
                self.UpdateTeamColorAndSkin(curowner)'''
                
            # The following code either raises the flag when capturing from neutral to a player or descends when uncapturing
            if curowner == OWNER_NEUTRAL:
                # Raise flag
                self.SetPoseParameter(self.flagpose, progress * 100.0)
                self.UpdateTeamColorAndSkin(self.playercapturing if self.playercapturing else curowner)
            else:
                # Descend flag
                self.SetPoseParameter(self.flagpose, 100.0 * (1.0 - progress))
                #self.UpdateTeamColorAndSkin(OWNER_NEUTRAL)
            
        def OnNewModel(self):
            super().OnNewModel()

            studio_hdr = self.GetModelPtr()
            
            self.flagpose = self.LookupPoseParameter(studio_hdr, "flag")
            if self.flagpose < 0:
                return
            self.SetPoseParameter(self.flagpose, 100.0)
            
        def GetCursor(self):
            return cursors.GetCursor("resource/arrows/capture_cursor.ani")
            
        def OnUnitTypeChanged(self, oldunittype):
            super().OnUnitTypeChanged(oldunittype)
        
            self.UpdateControlPointParticles()
            
        def OnConstructionStateChanged(self):
            super().OnConstructionStateChanged()
            
            state = self.constructionstate
            
            # Remove old upgrade particles if any
            prop = self.ParticleProp()
            for particle_fx in self.constructionparticles:
                prop.StopEmission(particle_fx, False, False, True)
            self.constructionparticles = []
        
            if state == self.BS_UPGRADING:
                # Create upgrade particles
                for particle_info in self.unitinfo.constructionparticles:
                    particle_name = particle_info.get('name', None)
                    if not particle_name:
                        continue
                        
                    particle_fx = prop.Create(particle_name, ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW)
                    if particle_fx:
                        particle_fx.SetControlPoint(2, Vector(1.5, 1, 1)) # Animation related
                        particle_fx.SetControlPoint(4, self.GetTeamColor()) # Team color
                        self.constructionparticles.append(particle_fx)
                        
        def Spawn(self):
            super().Spawn()
            
            self.controlpointlisthandle.Enable()
            
    def CanPlayerControlUnit(self, player):
        # Shared control between allies
        return relationships[(self.GetOwnerNumber(), player.GetOwnerNumber())] == Disposition_t.D_LI
            
    if isserver:
        def Enable(self):
            self.enabled = True
            
        def Disable(self):
            self.enabled = False

        def Spawn(self):
            if self.GetUnitType() == 'unit_unknown':
                self.SetUnitType('control_point')
        
            super().Spawn()
            
            self.controlpointlisthandle.Enable()
            
            self.takedamage = DAMAGE_NO
            self.SetCanBeSeen(False)
            
            self.SetThink(self.CaptureThink, gpGlobals.curtime + 0.25, self.CAPTURE_THINK_CONTEXT)
            
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.controlpointlisthandle.Disable()
              
        def CaptureThink(self):
            if not self.capturearea or not self.enabled:
                self.SetNextThink(gpGlobals.curtime + 1.0, self.CAPTURE_THINK_CONTEXT)
                return
                
            ownernumber = self.GetOwnerNumber()
                
            # get the teamid capturing, update if necessary
            self.playerholding = self.UpdatePlayerCapturing()

            thinkrate = 0.2
            progressdelta = thinkrate / self.capturetime if self.capturetime > 0 else 1

            if self.playercapturing or self.playerholding:
                self.UpdateUnderAttack(ownernumber)
                    
                # Considering "capturing" as damage taking. This way it can be used by the cpu player to determine what needs attention.
                self.lasttakedamage = gpGlobals.curtime
                
                if self.playercapturing != self.playerholding:
                    if self.playerholding != ownernumber:
                        # Either nobody is capturing or a different player is capturing
                        # In this case the progress is being decreased
                        self.captureprogress = max(0.0, self.captureprogress - progressdelta)
                        if self.playercapturing is None or self.captureprogress <= 0.0:
                            self.playercapturing = self.playerholding
                            self.captureprogress = 0.0
                elif self.playercapturing:
                    self.captureprogress = min(1.0, self.captureprogress + progressdelta)
                    if self.captureprogress >= 1.0:
                        # Note: Player first "uncaptures" the point to neutral
                        if ownernumber == OWNER_NEUTRAL:
                            self.SetOwnerNumber(self.playercapturing)
                        else:
                            self.SetOwnerNumber(OWNER_NEUTRAL)
                        self.captureprogress = 0.0
                        self.playercapturing = None
                        
                self.captureprogressrate = progressdelta
                self.SetNextThink(gpGlobals.curtime + thinkrate, self.CAPTURE_THINK_CONTEXT)
            else:
                self.SetNextThink(gpGlobals.curtime + 0.5, self.CAPTURE_THINK_CONTEXT)
            
        def UpdatePlayerCapturing(self):
            team_capturing = None
            capturearea = self.capturearea
            if not capturearea:
                return team_capturing
            # Can't capture while the control point is fortified
            if self.upgradelevel > 0:
                return team_capturing
            # Can't capture when the control point is being fortified
            if self.activeupgrade:
                return team_capturing
            
            for entity in capturearea.GetTouchingEntities():
                if not entity or not entity.IsUnit() or entity == self or not entity.IsAlive():
                    continue
                    
                # Ignore entities we own
                if entity.GetOwnerEntity() == self:
                    continue
                    
                # Cloaked units cannot capture a control point
                if getattr(entity, 'cloaked', False):
                    continue
                    
                # Ignore other buildings
                if getattr(entity, 'isbuilding', False):
                    continue
                    
                # Check if we are allowed to capture the point
                try:
                    cancappcontrolpoint = entity.cancappcontrolpoint
                except AttributeError:
                    cancappcontrolpoint = True
                if not cancappcontrolpoint:
                    continue
                    
                # Must be a player (not a special ownernumber like neutral or enemy)
                if entity.GetOwnerNumber() < OWNER_LAST:
                    continue
                    
                # we are already capturing it
                if entity.GetOwnerNumber() == team_capturing:
                    continue

                # owners need to be removed before this point can be captured
                if entity.GetOwnerNumber() == self.GetOwnerNumber():
                    return None

                # Don't capture a point of somebody we like or against we are neutral
                if relationships[(entity.GetOwnerNumber(), self.GetOwnerNumber())] == Disposition_t.D_LI:
                    continue

                # Nobody is capturing it, so we are going to capture it
                if not team_capturing:
                    team_capturing = entity.GetOwnerNumber()
                    continue

                # this means multiple npcs of different owner numbers are on the point and we must hate the other owner number
                if team_capturing != entity.GetOwnerNumber() and relationships[(entity.GetOwnerNumber(), team_capturing)] == Disposition_t.D_HT:
                    return None

            return team_capturing
            
        def OnPlayerDefeated(self):
            # Become neutral if the defeated player owns us
            self.SetOwnerNumber(0)
            
        def OnChangeOwnerNumber(self, oldownernumber):
            super().OnChangeOwnerNumber(oldownernumber)
            
            # The control point might become neutral while fortified when a player is defeated
            # Just destroy the fortification when changing owner.
            self.DestroyFortification()
            
            # Reset last take damage (used for notifications and AI)
            self.lasttakedamage = 0
            
            newowner = self.GetOwnerNumber()
            
            fncaptured = getattr(self, 'oncaptured_%d' % (newowner), None)
            fnlost = getattr(self, 'onlost_%d' % (oldownernumber), None)
            
            if fncaptured: 
                fncaptured.FireOutput(self, self)
            self.oncapturedall.FireOutput(self, self)
            if fnlost: 
                fnlost.FireOutput(self, self)
            self.onlostall.FireOutput(self, self)
            
            # Notify new and old owner players
            DoNotificationEnt('cp_captured', self, filter=GetNotifcationFilterForOwnerAndAllies(newowner))
            DoNotificationEnt('cp_lost', self, filter=GetNotifcationFilterForOwnerAndAllies(oldownernumber))
            
            # Keep showing the control point for some seconds for old player (avoid bug that control point still shows as owned by old player)
            unit = CreateUnit('unit_scan', self.GetAbsOrigin() + Vector(0, 0, 128.0), owner_number=oldownernumber)
            unit.viewdistance = 256.0
            unit.SetScanDuration(5.0)
            
            # Push one update for old players (otherwise the control point might keep showing up as "theirs")
            players = UTIL_ListForOwnerNumberWithDisp(oldownernumber, d=Disposition_t.D_LI)
            for player in players:
                self.FOWForceUpdate(player.entindex()-1)

            if not started_fortification_once[newowner]:
                for player in UTIL_ListPlayersForOwnerNumber(newowner):
                    event = GameEvent('wars_nofortifications')
                    event.SetInt("userid", player.GetUserID())
                    event.SetInt("entindex", self.entindex())
                    FireGameEvent(event)
                
    def Event_Killed(self, info):
        self.DestroyFortification()
        
    def OnTakeDamage(self, dmginfo):
        self.UpdateUnderAttack(self.GetOwnerNumber())
        self.lasttakedamage = gpGlobals.curtime
        return super().OnTakeDamage(dmginfo)
        
    def UpdateUnderAttack(self, ownernumber):
        # Don't show new notification until the control point hasn't been under attack for 10 seconds
        if gpGlobals.curtime - self.lasttakedamage > 10.0:
            DoNotificationEnt('cp_underattack', self, filter=GetNotifcationFilterForOwnerAndAllies(ownernumber))
        
    @classmethod
    def PrecacheUnitType(cls, info):
        """ Precaches the unit type.
            This is only called one time per unit type in a level.
            It's called on both server and client one time.

            Args:
                info (core.units.info.UnitInfo): info structure of unit type
        """
        super(BaseControlPoint, cls).PrecacheUnitType(info)

        for particleinfo in (info.particles + info.constructionparticles):
            PrecacheParticleSystem(particleinfo.get('name', ''))
            
        if info.constructiondummy:
            cls.PrecacheDummy(info.constructiondummy)

    @clientonly
    def DestroyControlPointParticles(self):
        """ Stops and removes any control point particle effect. """
        prop = self.ParticleProp()
        for particlefx in self.upgradeparticles:
            prop.StopEmission(particlefx, False, False, True)
        self.upgradeparticles = []

    @clientonly
    def UpdateControlPointParticles(self):
        """ Applies client side effects related to control point building upgrades. """
        self.DestroyControlPointParticles()

        prop = self.ParticleProp()

        for particleinfo in self.unitinfo.particles:
            particlename = particleinfo.get('name', None)
            if not particlename:
                continue
                
            particlefx = prop.Create(particlename, ParticleAttachment_t.PATTACH_ABSORIGIN_FOLLOW)
            if particlefx:
                particlefx.SetControlPoint(2, Vector(1.5, 1, 1)) # Animation related
                particlefx.SetControlPoint(4, self.GetTeamColor()) # Team color
                self.upgradeparticles.append(particlefx)
                
    def UpdateControlPointState(self):
        """ Updates properties of control point based on current state. """
        unitinfo = self.unitinfo
        if self.isconstructed:
            self.maxhealth = unitinfo.health
            self.health = min(self.health, self.maxhealth)
            if self.upgradelevel > 0:
                # Fortified, so damageable
                self.takedamage = DAMAGE_YES
                self.SetCanBeSeen(True)
            else:
                # Unfortified. Can't be damaged.
                self.takedamage = DAMAGE_NO
                self.SetCanBeSeen(False)
        else:
            # Must be upgrading
            self.takedamage = DAMAGE_YES
            self.SetCanBeSeen(True)
    
    def OnStartFortifcationUpgrade(self):
        """ Starts the fortification upgrade process.
            Makes the control point attackable, sets health and initializes upgrade effects.
        """
        owner = self.GetOwnerNumber()
        faction = dbplayers[owner].faction
        targetupgradelevel = min(self.maxupgradelevel, self.upgradelevel + 1)
        
        factioninfo = GetFactionInfo(faction)
        if not factioninfo:
            return
            
        fortifyunittypes = getattr(factioninfo, 'fortifyunittypes', None)
        if not fortifyunittypes:
            return
            
        unittype = fortifyunittypes.get(targetupgradelevel, 'control_point')
        unitinfo = GetUnitInfo(unittype)
        if not unitinfo:
            return
    
        self.takedamage = DAMAGE_YES
        self.SetCanBeSeen(True)
        self.maxhealth = unitinfo.health
        self.health = max(self.health, int(unitinfo.constructstarthp*self.maxhealth))
        self.constructhpmax = self.maxhealth - self.health
        self.constructhpbuildup = 0.0
        
        if unitinfo.constructiondummy:
            self.CreateDummy(unitinfo.constructiondummy)
        
        self.onstartfortifying.Set(targetupgradelevel, self, self)

        # Game event for fortification lessons
        started_fortification_once[owner] = True
        for player in UTIL_ListPlayersForOwnerNumber(owner):
            event = GameEvent('wars_start_fortification_cp')
            event.SetInt("userid", player.GetUserID())
            event.SetInt("entindex", self.entindex())
            FireGameEvent(event)
                
    def PerformFortifcationUpgrade(self):
        """ Finalizes the fortification upgrade process. """
        owner = self.GetOwnerNumber()
        faction = dbplayers[owner].faction
        
        self.upgradelevel = min(self.maxupgradelevel, self.upgradelevel + 1)
        
        unittype = 'control_point'
        factioninfo = GetFactionInfo(faction)
        if factioninfo:
            fortifyunittypes = getattr(factioninfo, 'fortifyunittypes', {})
            unittype = fortifyunittypes.get(self.upgradelevel, 'control_point')
            
        self.SetUnitType(unittype)
        self.SetUnitModel()
        self.DestroyDummies()
        self.CreateDummies(self.unitinfo.dummies)
        healthfraction = self.HealthFraction()
        self.maxhealth = self.unitinfo.health
        self.health = int(healthfraction * self.maxhealth)
        
        self.onfortified.Set(self.upgradelevel, self, self)
        
        FireSignalRobust(cp_fortified, building=self)

        # Game event for fortification lessons
        for player in UTIL_ListPlayersForOwnerNumber(owner):
            event = GameEvent('wars_fortified_cp')
            event.SetInt("userid", player.GetUserID())
            event.SetInt("entindex", self.entindex())
            FireGameEvent(event)
        
    def CancelFortifying(self):
        """ Cancels an active fortification upgrade. """
        if not self.activeupgrade:
            return
        self.activeupgrade = None
        self.SetConstructionState(self.BS_CONSTRUCTED)
        self.UpdateControlPointState()
        self.DestroyDummies()
        self.CreateDummies(self.GetDummies())
        
    def DestroyFortification(self):
        """ Destroys any fortification. """
        if self.upgradelevel == 0 and not self.activeupgrade:
            return
        self.activeupgrade = None
        self.upgradelevel = 0
        self.SetConstructionState(self.BS_CONSTRUCTED)
        self.SetUnitType(BaseControlPointInfo.name)
        self.UpdateControlPointState()
        self.DestroyDummies()
        self.SetUnitModel()
        self.CreateDummies(self.GetDummies())
        FireSignalRobust(cp_fortificationdestroyed, building=self)
            
    enabled = BooleanField(value=True)   
    capturearea = None
    clientcaptureprogress = 0.0
    autoconstruct = True
    customeyeoffset = Vector(0,0,200)
    buildingsolidmode = SOLID_BBOX
    barsoffsetz = 225.0
    
    controlpointlisthandle = UnitListObjectField(controlpointlist)
    
    oncapturedall = OutputField(keyname='OnCapturedAll')
    onlostall = OutputField(keyname='OnLostAll')
    playercapturing = GenericField(value=None, networked=True, helpstring='Player capturing the point. Does not need to be the same as the one holding the point.')
    playerholding = GenericField(value=None, networked=True, helpstring='Player holding the point')
    captureprogress = FloatField(0.0, networked=True, propname='propfloat1')
    capturetime = FloatField(15.0, networked=True, keyname='CaptureTime')
    
    upgradelevel = IntegerField(value=0, networked=True, helpstring='The current upgrade level of this control point')
    maxupgradelevel = 2
    upgradeparticles = ListField()
    constructionparticles = ListField()
    onstartfortifying = OutputField(keyname='OnStartFortifying', fieldtype=fieldtypes.FIELD_INTEGER)
    onfortified = OutputField(keyname='OnFortified', fieldtype=fieldtypes.FIELD_INTEGER)
    
    oncaptured_2 = OutputField(keyname='OnCaptured_Player0')
    oncaptured_3 = OutputField(keyname='OnCaptured_Player1')
    oncaptured_4 = OutputField(keyname='OnCaptured_Player2')
    oncaptured_5 = OutputField(keyname='OnCaptured_Player3')
    oncaptured_6 = OutputField(keyname='OnCaptured_Player4')
    oncaptured_7 = OutputField(keyname='OnCaptured_Player5')
    oncaptured_8 = OutputField(keyname='OnCaptured_Player6')
    oncaptured_9 = OutputField(keyname='OnCaptured_Player7')
    oncaptured_10 = OutputField(keyname='OnCaptured_Player8')
    oncaptured_11 = OutputField(keyname='OnCaptured_Player9')
    oncaptured_12 = OutputField(keyname='OnCaptured_Player10')
    oncaptured_13 = OutputField(keyname='OnCaptured_Player11')

    onlost_2 = OutputField(keyname='OnLost_Player0')
    onlost_3 = OutputField(keyname='OnLost_Player1')
    onlost_4 = OutputField(keyname='OnLost_Player2')
    onlost_5 = OutputField(keyname='OnLost_Player3')
    onlost_6 = OutputField(keyname='OnLost_Player4')
    onlost_7 = OutputField(keyname='OnLost_Player5')
    onlost_8 = OutputField(keyname='OnLost_Player6')
    onlost_9 = OutputField(keyname='OnLost_Player7')
    onlost_10 = OutputField(keyname='OnLost_Player8')
    onlost_11 = OutputField(keyname='OnLost_Player9')
    onlost_12 = OutputField(keyname='OnLost_Player10')
    onlost_13 = OutputField(keyname='OnLost_Player11')

    CAPTURE_THINK_CONTEXT = "CaptureThinkContext"
    
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    
    unitinfofallback = BaseControlPointInfo
    unitinfovalidationcls = BaseControlPointInfo


@entity('capturetheflag_point',
        studio='models/pg_props/pg_obj/pg_flagpole.mdl')
class CaptureTheFlagPoint(BaseControlPoint):
    def Spawn(self):
        super(CaptureTheFlagPoint, self).Spawn()
        
    def OnChangeOwnerNumber(self, oldownernumber):
        super(CaptureTheFlagPoint, self).OnChangeOwnerNumber(oldownernumber)
        
        gamerules.OnFlagOwnerChanged(self.GetOwnerNumber(), oldownernumber)
    enabled = False


@entity('control_point',
        studio='models/pg_props/pg_obj/pg_flagpole.mdl')
class ControlPoint(BaseControlPoint):
    resourcemessageatorigin = True
    resourcemessageoffset = Vector(32.0, 0, 256.0)
    
    def CanGenerateResources(self, resourcetype, amount):
        if self.activeupgrade:
            return False
        return super().CanGenerateResources(resourcetype, amount)
        
    '''def ResourceThink(self):
        if not self.generateresources:
            return
        
        ownernumber = self.GetOwnerNumber()
        if ownernumber >= OWNER_LAST:
            owners = ListAlliesOfOwnerNumber(ownernumber)

            resourcetype = self.generateresources[0]
            
            origin = self.GetAbsOrigin()
            origin.x += 32.0
            origin.z += 256.0
            
            for owner in owners:
                GiveResources(owner, [(resourcetype, self.generateresources[1]/float(len(owners)))], firecollected=True)
                
            MessageResourceIndicator(owners, origin, '+%.2f' % (self.generateresources[1]), resourcetype)
    
        self.SetNextThink(gpGlobals.curtime + self.generateresources[2], 'ResourceThink')'''

# ======================================================================================================================
# ================================================== Squad Wars Flags ==================================================
# ======================================================================================================================

class BaseControlPointCharInfo(BaseControlPointInfo):
    name = "control_point_char"
    cls_name = "control_point"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_wood.mdl'
    explodemodel = 'models/pg_props/pg_buildings/other/pg_flagpole/pg_flagpole_wood_des.mdl'
    displayname = '#ControlPoint_Name'
    description = '#ControlPoint_Description'
    minimaphalfwide = 4
    minimaphalftall = 4
    minimaplayer = -1  # Draw earlier than units to avoid overlapping
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    minimapicon_name = 'hud_minimap_flag'
    viewdistance = 720
    generateresources = {'type': 'power_sw', 'amount': 1.0, 'interval': 5.0, 'maxgenerate': CP_MAXGENERATE}
    splitgeneratedresources = True
    reducesplittedresources = False
    ispriobuilding = False  # Excludes this building from Annihilation victory conditions
    #sai_hint = set(['sai_controlpoint'])
    sound_select = 'unit_controlpoint_select'

    mins = Vector(-55, -55, 0)
    maxs = Vector(55, 55, 75)

    dummies = [
        CreateDummy(
            modelname='models/pg_props/pg_buildings/other/pg_flagpole_base/pg_flagpole_wood_base_0.mdl',
            offset=Vector(0, 0, 0),
            decorative=True,
        )
    ]

    particles = []

    constructiondummy = None

    ability_0 = None
    ability_8 = None