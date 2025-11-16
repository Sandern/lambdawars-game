""" Building that requires power. 

Must be placed near a power generator to function.
"""
from srcbase import Color, RenderMode_t, RenderFx_t
from vmath import Vector
from utils import UTIL_EntitiesInSphere
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from core.units import CreateUnitList, UnitListObjectField, unitlistpertype, GetUnitInfo
from core.dispatch import receiver
from core.signals import prelevelinit
from core.resources import GiveResources, HasEnoughResources
from playermgr import OWNER_LAST
from fields import BooleanField
from entities import entity, networked
from particles import PATTACH_POINT_FOLLOW, PATTACH_ABSORIGIN_FOLLOW

if isclient:
    from entities import DataUpdateType_t
else:
    from core.usermessages import CRecipientFilter, SendUserMessage
    from utils import UTIL_ListPlayersForOwnerNumber
    from particles import PrecacheParticleSystem, DispatchParticleEffect

from collections import defaultdict

# List of buildings that require a nearby powergenerator
poweredlist = CreateUnitList()

# Power generator building
if isclient:
    @receiver(prelevelinit)
    def LevelInit(sender, **kwargs):
        PowerGeneratorBuilding.showpoweroverlaycount = defaultdict(lambda: 0)


@entity('build_comb_powergenerator', networked=True)
class PowerGeneratorBuilding(BaseClass):
    def UpdateOnRemove(self):
        if isclient:
            self.DisablePowerOverlay()

        if isserver:
            # Notify powered buildings in range (only needed if alive, otherwise already done in Event_Killed)
            if self.IsAlive():
                [p.UpdatePoweredState() for p in poweredlist[self.GetOwnerNumber()]]
        else:
            if self.bluestromfx:
                self.ParticleProp().StopEmission(self.bluestromfx)
                self.bluestromfx = None

        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()

    if isserver:
        def Precache(self):
            super().Precache()

            PrecacheParticleSystem('pg_blue_strom')
            PrecacheParticleSystem('pg_generator_ex')
            PrecacheParticleSystem('power_radius')

        def Spawn(self):
            super().Spawn()

        def OnConstructed(self):
            super().OnConstructed()

            # Notify powered buildings in range
            [p.UpdatePoweredState() for p in poweredlist[self.GetOwnerNumber()]]

        def DestructThink(self):
            """ Think function that is supposed to destruct/explode us in some cool way."""
            DispatchParticleEffect('pg_generator_ex', PATTACH_POINT_FOLLOW, self, 'root')

            super().DestructThink()

        def Event_Killed(self, info):
            super().Event_Killed(info)

            [p.UpdatePoweredState() for p in poweredlist[self.GetOwnerNumber()]]

        def OnChangeOwnerNumber(self, old_owner):
            super().OnChangeOwnerNumber(old_owner)

            # Update old and new owners
            [p.UpdatePoweredState() for p in poweredlist[old_owner]]
            [p.UpdatePoweredState() for p in poweredlist[self.GetOwnerNumber()]]

    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)

            if type == DataUpdateType_t.DATA_UPDATE_CREATED:
                self.bluestromfx = self.ParticleProp().Create("pg_blue_strom", PATTACH_POINT_FOLLOW, 'root')

        def ExplodeHandler(self, event):
            if self.bluestromfx:
                self.ParticleProp().StopEmission(self.bluestromfx)
                self.bluestromfx = None
            super().ExplodeHandler(event)

        # Power overlays, show the range of each power generator
        # TODO: Ensure counts are correct when the unit dies or when the owner number changes.
        poweroverlay = None
        showpoweroverlaycount = defaultdict(lambda: 0)

        def EnablePowerOverlay(self):
            if self.poweroverlay:
                return
            powerrange = self.unitinfo.powerrange
            self.poweroverlay = self.ParticleProp().Create("power_radius", PATTACH_ABSORIGIN_FOLLOW, -1, Vector(0, 0, 4))
            self.poweroverlay.SetControlPoint(1, self.GetTeamColor())
            self.poweroverlay.SetControlPoint(2, Vector(powerrange, 0, 0))

        def DisablePowerOverlay(self):
            if not self.poweroverlay:
                return
            self.ParticleProp().StopEmission(self.poweroverlay, False, False, True)
            self.poweroverlay = None

        @staticmethod
        def EnableAllPowerOverlays(ownernumber):
            if PowerGeneratorBuilding.showpoweroverlaycount[ownernumber]:
                PowerGeneratorBuilding.showpoweroverlaycount[ownernumber] += 1
                return

            PowerGeneratorBuilding.showpoweroverlaycount[ownernumber] += 1

            for powergen in unitlistpertype[ownernumber]['build_comb_powergenerator']:
                powergen.EnablePowerOverlay()

        @staticmethod
        def DisableAllPowerOverlays(ownernumber):
            PowerGeneratorBuilding.showpoweroverlaycount[ownernumber] -= 1
            if PowerGeneratorBuilding.showpoweroverlaycount[ownernumber]:
                return

            for powergen in unitlistpertype[ownernumber]['build_comb_powergenerator']:
                powergen.DisablePowerOverlay()

        def OnSelected(self, player):
            super().OnSelected(player)

            self.EnableAllPowerOverlays(self.GetOwnerNumber())

        def OnDeSelected(self, player):
            super().OnDeSelected(player)

            self.DisableAllPowerOverlays(self.GetOwnerNumber())

    autoconstruct = False
    bluestromfx = None
    customeyeoffset = Vector(0, 0, 60)
    nav_radius_obstacle_mode = True
    nav_radius_obstacle_scale = 0.65


class PoweredGeneratorInfo(WarsBuildingInfo):
    name = 'build_comb_powergenerator'
    displayname = '#BuildCombPowGen_Name'
    description = '#BuildCombPowGen_Description'
    image_name = 'vgui/combine/buildings/build_comb_powergenerator'
    cls_name = 'build_comb_powergenerator'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_power_generator.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_power_generator_des.mdl'
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    costs = [('requisition', 15)]
    resource_category = 'economy'
    health = 250
    buildtime = 10.0
    generateresources = {'type': 'power', 'amount': 1, 'interval': 20}
    powerrange = 768.0
    infoparticles = ['power_radius']
    particleradius = powerrange
    particleoffset = Vector(0, 0, 16.0)
    sound_select = 'build_comb_powergenerator'
    sound_death = 'build_comb_gen_destroy'
    # explodeparticleeffect = 'pg_generator_ex'
    abilities = {
        8: 'cancel',
    }
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_powergen'])
    requirerotation = False


class PoweredGeneratorBigInfo(PoweredGeneratorInfo):
    name = 'build_comb_powergenerator_big'
    displayname = '#BuildCombPowGenBig_Name'
    description = '#BuildCombPowGenBig_Description'
    generateresources = {'type': 'power', 'amount': 5.0, 'interval': 1.5}
    health = 350
    scale = 1.5
    buildtime = 45.0
    powerrange = 1024.0
    particleradius = powerrange
    costs = [('requisition', 40), ('power', 40)]
    techrequirements = ['build_comb_armory']
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_powergen_big'])


class PoweredGeneratorScrapInfo(WarsBuildingInfo):
    name = 'build_comb_powergenerator_scrap'
    cls_name = 'build_comb_powergen_scrap'
    displayname = '#BuildCombPowGenScrap_Name'
    description = '#BuildCombPowGenScrap_Description'
    image_name = 'vgui/combine/buildings/build_comb_scrap_energy_generator'
    modelname = 'models/pg_props/pg_buildings/combine/pg_scrap_power_generator.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_scrap_power_generator_des.mdl'
    scale = 1.0
    generateresources = {'type': 'power', 'amount': 1.0, 'interval': 2.0}
    splitgenerateresources = True
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    health = 450
    buildtime = 20.0
    costs = [('requisition', 40)]
    resource_category = 'economy'
    viewdistance = 896
    abilities = {
        8: 'cancel',
    }
    sound_work = 'combine_power_generator_working'
    sound_select = 'build_comb_energycell'
    sound_death = 'build_comb_battery_destroy'
    explodeparticleeffect = 'pg_scrap_generator_ex'
    explodeparticleoffset = Vector(0, 0, 100)
    explodeshake = (2, 10, 2, 512)  # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_powergenscrap'])
    exclude_from_testsuites = {'placebuildings'}
    requirenavmesh = False
    require_walkable_navmesh = False
    requirerotation = False

    # Placing code
    targetunitinfo = 'scrap_marker'
    lastbuildtarget = None

    def IsValidBuildingTarget(self, building):
        # Non solid scrap markers are claimed.
        return building.IsSolid()

    def GetTargetBuilding(self, pos):
        """ Tries to find a target candidate building at the specified position. """
        targetunitinfo = GetUnitInfo(self.targetunitinfo)
        if not targetunitinfo:
            return None

        foundtarget = None
        targets = UTIL_EntitiesInSphere(1024, pos, 64.0, 0)
        for target in targets:
            if not target or not target.IsUnit():
                continue

            testunitinfo = target.unitinfo
            if not issubclass(testunitinfo, targetunitinfo):
                continue

            if not self.IsValidBuildingTarget(target):
                continue

            foundtarget = target
            break

        return foundtarget

    def IsValidPosition(self, pos):
        self.lastbuildtarget = self.GetTargetBuilding(pos)
        return self.lastbuildtarget != None

    if isserver:
        def DoAbility(self):
            validposition = self.IsValidPosition(self.targetpos)
            if not validposition:
                self.Cancel(cancelmsg='#Ability_InvalidPosition', debugmsg=self.debugvalidposition)
                return
            if not self.lastbuildtarget:
                self.Cancel(cancelmsg='#Ability_InvalidTarget', debugmsg=self.debugvalidposition)
                return
            self.targetpos = self.lastbuildtarget.GetAbsOrigin()
            super().DoAbility()

    if isclient:
        def GetPreviewPosition(self, groundpos):
            self.lastbuildtarget = self.GetTargetBuilding(groundpos)
            if not self.lastbuildtarget:
                return super().GetPreviewPosition(groundpos)

            return self.lastbuildtarget.GetAbsOrigin()

    def PlaceObject(self):
        object = super().PlaceObject()
        if object:
            object.ClaimScrapMarker(self.lastbuildtarget)
        return object


# Base building for powered buildings
class BasePoweredBuilding(object):
    def Precache(self):
        super().Precache()

        self.PrecacheScriptSound("combine_power_on")
        self.PrecacheScriptSound("combine_power_off")

    def Spawn(self):
        super().Spawn()

        self.poweredlisthandle.Enable()

        if isserver:
            self.UpdatePoweredState()
            # self.SetThink(self.PowerThink, gpGlobals.curtime+0.5, 'PowerThink')
        else:
            self.OnPoweredChanged()

    def UpdateOnRemove(self):
        super().UpdateOnRemove()

        self.poweredlisthandle.Disable()

    if isserver:
        # def PowerThink(self):
        #    HasEnoughResources...
        #    self.SetNextThink(gpGlobals.curtime+0.5, 'PowerThink')

        def UpdatePoweredState(self):
            if self.health <= 0:
                return

            self.powered = self.unitinfo.IsPoweredAt(self.GetAbsOrigin(), self.GetOwnerNumber())
            self.OnPoweredChanged()

        def OnChangeOwnerNumber(self, oldownernumber):
            super().OnChangeOwnerNumber(oldownernumber)
            if self.poweredlisthandle.disabled:
                return
            self.UpdatePoweredState()

    if isclient:
        def OnConstructionStateChanged(self):
            super().OnConstructionStateChanged()

            if self.constructionstate == self.BS_CONSTRUCTED:
                self.OnPoweredChanged()

    def OnPoweredChanged(self):
        if self.oldpowered == self.powered:
            return

        self.oldpowered = self.powered

        if self.powered:
            self.SetRenderMode(RenderMode_t.kRenderNormal)
            self.SetRenderAlpha(255)
            self.SetRenderColor(255, 255, 255)
            self.EmitSound("combine_power_on")
        else:
            self.SetRenderMode(RenderMode_t.kRenderTransColor)
            self.SetRenderAlpha(255)
            self.SetRenderColor(76, 76, 76)
            self.EmitSound("combine_power_off")

    poweredlisthandle = UnitListObjectField(poweredlist)
    oldpowered = False
    powered = BooleanField(value=False, networked=True, clientchangecallback='OnPoweredChanged')


class BaseFactoryPoweredBuilding(BasePoweredBuilding):
    if isserver:
        def OnPoweredChanged(self):
            super().OnPoweredChanged()
            self.onhold = not self.powered


class PoweredBuildingInfo(WarsBuildingInfo):
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_powered'])

    @staticmethod
    def IsPoweredAt(pos, ownernumber):
        # Check nearby a power generator
        inrange = False
        for p in unitlistpertype[ownernumber]['build_comb_powergenerator']:
            if p.constructionstate != p.BS_CONSTRUCTED or p.IsMarkedForDeletion():
                continue
            if not p.IsAlive():
                continue
            if p.GetAbsOrigin().DistTo(pos) < PoweredGeneratorInfo.powerrange:
                inrange = True
                break

        return inrange

    def IsValidPosition(self, pos):
        if not self.IsPoweredAt(pos, self.ownernumber):
            self.cancelmsg_invalidposition = '#Ability_InvalidPositionNoPower'
            return False
        return super().IsValidPosition(pos)

    if isclient:
        def CreateVisuals(self):
            super().CreateVisuals()

            PowerGeneratorBuilding.EnableAllPowerOverlays(self.ownernumber)

        def ClearVisuals(self):
            super().ClearVisuals()

            PowerGeneratorBuilding.DisableAllPowerOverlays(self.ownernumber)
