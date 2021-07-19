"""
A building with the ability to teleport units around the building to a spot with vision.
"""
from srcbase import SOLID_BBOX, FSOLID_NOT_STANDABLE, EF_NOSHADOW
from vmath import Vector, vec3_origin
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass, CreateDummy
from core.abilities import AbilityTarget
from core.units import UnitBase, PlaceUnit, CreateUnit, PrecacheUnit, UnitInfo, GroupMoveOrder, CreateUnitFancy
from srcbase import FL_NPC
from entities import entity, D_LI, D_HT, DENSITY_NONE, FOWFLAG_UNITS_MASK
from utils import UTIL_EntitiesInSphere, UTIL_Remove
from sound import soundengine
from fields import IntegerField, VectorField, FloatField, ListField
from particles import PrecacheParticleSystem, PATTACH_POINT_FOLLOW, PATTACH_POINT, PATTACH_ABSORIGIN, DispatchParticleEffect
from fow import FogOfWarMgr
#from gameinterface import CPASAttenuationFilter
from wars_game.statuseffects import StunnedEffectInfo
from core.abilities import AbilityUpgrade, AbilityUpgradeValue
from operator import itemgetter
from navmesh import NavMeshGetPositionNearestNavArea
from gamerules import gamerules

if isserver:
    from core.units import BaseAction

    class TeleportAction(BaseAction):
        """ Overrides the AI state of an unit and disables locomotion.
        """
        def OnStart(self):
            outer = self.outer
            outer.ClearAllOrders(dispatchevent=False)
            outer.teleporting = True
            self.old_attack_priority = outer.attackpriority
            # TODO: Not applying correctly to property when setting directly?
            outer.GetHandle().attackpriority = -4
            self.was_locomotionenabled = outer.locomotionenabled
            outer.locomotionenabled = False
            #self.was_uncontrollable = outer.uncontrollable
            #outer.uncontrollable = True

        def OnEnd(self):
            outer = self.outer
            outer.teleporting = False
            #outer.uncontrollable = self.was_uncontrollable
            outer.GetHandle().attackpriority = self.old_attack_priority
            outer.locomotionenabled = self.was_locomotionenabled

        def OnTeleportEnded(self):
            return self.ChangeTo(self.behavior.ActionIdle, 'Done teleporting')

        was_locomotionenabled = True
        #was_uncontrollable = False
        old_attack_priority = 0


class AbilityTeleportUnits(AbilityTarget):
    name = 'teleport_units'
    displayname = "#AbilityTeleportUnits_Name"
    description = "#AbilityTeleportUnits_Description"
    image_name = 'vgui/rebels/abilities/rebel_teleport_units.vmt'
    rechargetime = 10
    #costs = [('requisition', 30)]
    supportsautocast = False
    defaultautocast = False
    hidden = True

    def DoAbility(self):
        if not isserver:
            return

        if not self.SelectSingleUnit():
            self.Cancel(cancelmsg='No unit', debugmsg='no unit')
            return

        target_pos = self.mousedata.endpos
        target = self.mousedata.ent
        owner = self.ownernumber
        unit = self.unit

        target_is_teleporter = (target and target.IsUnit() and target.unitinfo.name == TeleporterInfo.name and
                                unit.IRelationType(target) != D_HT)

        # Adjust position onto navigation mesh
        target_pos = NavMeshGetPositionNearestNavArea(target_pos, beneathlimit=256.0, maxradius=512.0)
        if target_pos == vec3_origin:
            self.Cancel(cancelmsg='#Ability_InvalidPosition', debugmsg='No navigation mesh at target position')
            return

        if FogOfWarMgr().PointInFOW(target_pos, owner):
            self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
            return

        if not self.TakeResources():
            self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
            return

        unit.StartTeleport(target_pos)
        self.SetRecharge(unit)
        self.Completed()


class TeleporterInfo(WarsBuildingInfo):
    name = "build_reb_teleporter"
    cls_name = "build_reb_teleporter"
    health = 600
    buildtime = 80.0
    techrequirements = ['build_reb_triagecenter']
    costs = [('requisition', 25), ('scrap', 25)]
    displayname = '#BuildRebTeleporter_Name'
    description = '#BuildRebTeleporter_Description'
    image_name = 'vgui/rebels/buildings/build_reb_teleporter'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_teleporter.mdl'
    modelname_blocking = 'models/pg_props/pg_buildings/rebels/pg_teleporter_ringblock.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_teleporter_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 250)
    ability_0 = 'teleport_units'
    sound_select = 'build_rebel_teleporter'
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'pg_rebel_junkyard_explosion'
    explodeshake = (2, 10, 2, 512)  # Amplitude, frequence, duration, radius

    teleport_stun_duration = FloatField(value=3.0, helpstring='Stun duration of units after teleport')
    teleport_max_units_pop = IntegerField(value=15, helpstring='Max pop number of units to teleport')
    teleport_radius = FloatField(value=150.0, helpstring='Radius in which to collect units around the building '
                                                         'for teleportation')

    dummies = [
        CreateDummy(
            offset=Vector(0, 0, 0),
            modelname='models/pg_props/pg_buildings/rebels/pg_teleporter_ringblock.mdl',
            blocknavareas=False,
            blockdensitytype=DENSITY_NONE,
            attackpriority=-1,
            #ignoreunitmovement = True,
        ),
    ]
    requirerotation = False

class DestroyHQTeleporterInfo(TeleporterInfo):
    name = "build_reb_teleporter_destroyhq"
    techrequirements = ['build_reb_triagecenter_destroyhq']


@entity('unit_teleporter_rift', networked=True)
class UnitTeleporterRift(UnitBase):
    """ Represents the rift being created while teleporting, displayed at the teleport target location.
    """
    def ShouldDraw(self):
        return False

    def IsSelectableByPlayer(self, player, target_selection):
        return False

    def GetIMouse(self):
        return None

    @classmethod
    def PrecacheUnitType(cls, info):
        super().PrecacheUnitType(info)

        PrecacheParticleSystem(cls.teleport_rift_fx_name)
        PrecacheParticleSystem(cls.teleport_rift_end_fx_name)

    if isserver:
        def Spawn(self):
            super().Spawn()

            self.SetSolid(SOLID_BBOX)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE)
            self.AddEffects(EF_NOSHADOW)
            self.SetCanBeSeen(False)

    def StopAllLoopingSounds(self):
        self.StopSound('rebels_teleport_rift_loop')

    if isclient:
        def OnDataUpdateCreated(self):
            super().OnDataUpdateCreated()

            self.CreateRift()

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.DestroyRift()
    else:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.StopAllLoopingSounds()

    def CreateRift(self):
        if self.teleport_rift_fx:
            return
        self.teleport_rift_fx = self.ParticleProp().Create(self.teleport_rift_fx_name, PATTACH_ABSORIGIN)
        self.EmitSound('rebels_teleport_rift_loop')
        #DispatchParticleEffect(self.teleport_rift_fx_name, self.teleport_target_pos, self.GetAbsAngles())

    def DestroyRift(self):
        if not self.teleport_rift_fx:
            return

        self.StopSound('rebels_teleport_rift_loop')
        self.EmitSound('rebels_teleport_rift_end')
        self.ParticleProp().StopEmission(self.teleport_rift_fx)
        self.teleport_rift_fx = None

        DispatchParticleEffect(self.teleport_rift_end_fx_name, self.GetAbsOrigin(), self.GetAbsAngles())


    def SpawnUnit(self):
        self.SetThink(self.SpawnUnitThink, gpGlobals.curtime + self.lifetime, 'TeleportThink')
    def SpawnUnitThink(self):
        angle = self.GetAbsAngles()
        pos = self.GetAbsOrigin()
        for i in range(0, 10):
            if gamerules.info.name == 'overrun':
                CreateUnitFancy('overrun_unit_rebel', pos, angles=angle, owner_number=self.GetOwnerNumber())
            else:
                CreateUnitFancy('unit_rebel', pos, angles=angle, owner_number=self.GetOwnerNumber())
        
        UTIL_Remove(self)

    teleport_rift_fx = None
    teleport_rift_fx_name = 'begin_rift_BASE'

    teleport_rift_end_fx_name = 'rift_flash_BASE'

    fowflags = FOWFLAG_UNITS_MASK
    
    lifetime = 20

class UnitTeleporterRiftInfo(UnitInfo):
    name = 'unit_teleporter_rift'
    cls_name = 'unit_teleporter_rift'
    health = 0
    population = 0
    minimapicon_name = 'hud_minimap_rift'
    minimaphalfwide = 5
    minimaphalftall = 5
    minimaplayer = -1  # Draw earlier than units to avoid overlapping
    viewdistance = 200.0

class TeleporterUnlock(AbilityUpgrade):
    name = 'teleporter_unlock'
    displayname = '#RebTeleporterUnlock_Name'
    description = '#RebTeleporterUnlock_Description'
    image_name = "vgui/rebels/abilities/rebel_teleporter_unlock"
    techrequirements = ['build_reb_detectiontower']
    buildtime = 60.0
    costs = [[('requisition', 150), ('scrap', 100)], [('kills', 5)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])

@entity('build_reb_teleporter', networked=True)
class RebelsTeleporter(BaseClass):
    if isserver:
        def __init__(self):
            super().__init__()

            self.SetDensityMapType(DENSITY_NONE)

    @classmethod
    def PrecacheUnitType(cls, info):
        super().PrecacheUnitType(info)

        cls.PrecacheModel(info.modelname_blocking)

        PrecacheUnit(UnitTeleporterRiftInfo.name)

        PrecacheParticleSystem(cls.teleport_ring_fx_name)
        PrecacheParticleSystem(cls.teleport_base_fx_name)
        PrecacheParticleSystem(cls.teleport_flash_fx_name)

    def Precache(self):
        super().Precache()

        self.PrecacheScriptSound('rebels_teleport_close')
        self.PrecacheScriptSound('rebels_teleport_loop_charging1')
        self.PrecacheScriptSound('rebels_teleport_loop_charging2')
        self.PrecacheScriptSound('rebels_teleport_rift_end')
        self.PrecacheScriptSound('rebels_teleport_rift_loop')
        self.PrecacheScriptSound('rebels_teleport_windup')
        self.PrecacheScriptSound('rebels_teleport_machine_instance')
        self.PrecacheScriptSound('rebels_teleport_winddown')

    def TargetOverrideOrder(self, unit, data, selection, angle=None, player=None):
        if unit.IRelationType(self) != D_HT:
            unit.MoveOrder(data.groundendpos, angle, selection)
            return True
        return False

    def TargetOverrideGroupOrder(self, player, data):
        """ Allows overriding the default group order.

            Args:
                player (entity): the player executing the group order
                data (MouseTraceData): Mouse data containing the target position + other information

            Returns a new group order instance to override the default.
        """
        groupmoveorder = GroupMoveOrder(player, data.groundendpos)
        return groupmoveorder

    if isserver:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.ReleaseUnits()
            self.DestroyRift()
            self.DestroyRingBlocker()
            self.StopAllLoopingSounds()

    def Event_Killed(self, info):
        super().Event_Killed(info)

        self.ReleaseUnits()
        self.DestroyRift()
        self.DestroyRingBlocker()
        self.StopAllLoopingSounds()

    def ExplodeHandler(self, event):
        super().ExplodeHandler(event)

        self.DestroyTeleporterRing()

    def SelectAndLockUnits(self):
        population = 0
        teleport_max_units_pop = self.unitinfo.teleport_max_units_pop

        # Collect units in radius of teleporter
        origin = self.GetAbsOrigin()
        found_ents = []
        entities = UTIL_EntitiesInSphere(256, self.GetAbsOrigin(), self.unitinfo.teleport_radius, FL_NPC)
        for ent in entities:
            if not ent or not ent.IsUnit() or self.IRelationType(ent) != D_LI or getattr(ent, 'isbuilding', False):
                continue

            dist = (ent.GetAbsOrigin() - origin).Length2D()
            if dist > self.unitinfo.teleport_radius:
                continue
            found_ents.append((ent, dist))

        # Prefer ents closer to center
        found_ents.sort(key=itemgetter(1))

        ditched_units = []
        for entry in found_ents:
            ent = entry[0]
            if population + ent.population > teleport_max_units_pop:
                ditched_units.append(ent)
                continue

            if hasattr(ent, 'DispatchEvent'):
                ent.DispatchEvent('OnChangeToAction', TeleportAction)
                succeeded = getattr(ent, 'teleporting', False)
                if not succeeded:
                    ditched_units.append(ent)
                    continue

            self.selected_units.append(ent)
            population += ent.population

        return ditched_units

    def BlockAreas(self):
        if not self.teleporting_state:
            return
        super().BlockAreas()

    #Sequence SPINUP
    def StartTeleport(self, target_pos):
        ditched_units = self.SelectAndLockUnits()

        self.teleporting_state = self.STATE_WINDUP
        self.CreateRingBlocker()
        #self.SetModel(self.unitinfo.modelname_blocking)
        self.teleport_target_pos = target_pos
        self.SetThink(self.WindUpEndThink, gpGlobals.curtime + 5.0, self.teleport_think_context)
        self.SetPoseParameter('progress', 1)
        self.BlockAreas()
        self.EmitSound('rebels_teleport_windup')

        # Move ditched units outside the teleporter
        for unit in ditched_units:
            PlaceUnit(unit, self.GetAbsOrigin())

    #Sequence SPIN
    def WindUpEndThink(self):
        self.teleporting_state = self.STATE_TELEPORTING
        self.CreateRift()
        self.StopSound('rebels_teleport_windup')
        self.EmitSound('rebels_teleport_loop_charging2')
        self.SetPoseParameter('progress', 3)
        #for x in range(1, 3):
            #self.SetThink(self.SetPoseParameter('progress', x), gpGlobals.curtime + (self.teleport_time/4.0)*x, self.teleport_think_context)

        self.SetThink(self.TeleportUnitsThink, gpGlobals.curtime + self.teleport_time, self.teleport_think_context)

    #Sequence SPINDOWN (teleport units)
    def TeleportUnitsThink(self):
        self.StopSound('rebels_teleport_loop_charging2')
        self.EmitSound('rebels_teleport_winddown')
        self.TeleportUnits(self.teleport_target_pos)
        self.DestroyRift()
        self.teleporting_state = self.STATE_WINDDOWN
        self.SetThink(self.TeleportEnd, gpGlobals.curtime + 3.6, self.teleport_think_context)

    #Sequence IDLE
    def TeleportEnd(self):
        self.teleporting_state = self.STATE_NONE
        #self.SetModel(self.unitinfo.modelname)
        self.SetPoseParameter('progress', 0)
        self.UnblockAreas()
        self.DestroyRingBlocker()

    def StopAllLoopingSounds(self):
        self.StopSound('rebels_teleport_windup')
        self.StopSound('rebels_teleport_loop_charging2')

    def ReleaseUnits(self):
        """ Releases combat units from teleport action state.

            Mainly called to release the units when the teleporter is destroyed.
        """
        for unit in self.selected_units:
            if not unit:
                continue

            if hasattr(unit, 'DispatchEvent'):
                unit.DispatchEvent('OnTeleportEnded')

        del self.selected_units[:]

    def TeleportUnits(self, targetpos):
        """ Called when units are being teleported. Also releases the units from the teleport action state.

            Args:
                targetpos (Vector): The target position.
        """
        # Move them to the target position
        teleport_stun_duration = self.unitinfo.teleport_stun_duration
        for unit in self.selected_units:
            if not unit:
                continue
            PlaceUnit(unit, targetpos)
            unit.lastidleposition = unit.GetAbsOrigin()

            if hasattr(unit, 'DispatchEvent'):
                unit.DispatchEvent('OnTeleportEnded')

            StunnedEffectInfo.CreateAndApply(unit, attacker=self, duration=teleport_stun_duration)

        #filter = CPASAttenuationFilter(targetpos, 'rebels_teleport_loop_charging1')
        #self.EmitSoundFilter(filter, 0, 'rebels_teleport_loop_charging1', targetpos)

        del self.selected_units[:]

    def OnTeleportStateChanged(self):
        self.UpdateBuildingActivity()
        if self.teleporting_state == self.STATE_TELEPORTING:
            self.CreateTeleporterRing()
        else:
            self.DestroyTeleporterRing()

    def UpdateBuildingActivity(self):
        if self.teleporting_state == self.STATE_TELEPORTING:
            self.ChangeToActivity('ACT_SPIN')
            return
        elif self.teleporting_state == self.STATE_WINDUP:
            self.ChangeToActivity('ACT_SPINUP')
            return
        elif self.teleporting_state == self.STATE_WINDDOWN:
            self.ChangeToActivity('ACT_SPINDOWN')
            return
        super().UpdateBuildingActivity()

    def CreateTeleporterRing(self):
        if self.teleport_ring01_fx:
            return

        self.teleport_ring01_fx = self.ParticleProp().Create(self.teleport_ring_fx_name, PATTACH_POINT_FOLLOW, "ring1")
        self.teleport_ring02_fx = self.ParticleProp().Create(self.teleport_ring_fx_name, PATTACH_POINT_FOLLOW, "ring2")
        self.teleport_ring03_fx = self.ParticleProp().Create(self.teleport_ring_fx_name, PATTACH_POINT_FOLLOW, "ring3")

        if self.teleport_base_fx:
            return
        self.teleport_base_fx = self.ParticleProp().Create(self.teleport_base_fx_name, PATTACH_POINT, "root")

    def DestroyTeleporterRing(self):
        if not self.teleport_ring01_fx:
            return

        self.ParticleProp().StopEmission(self.teleport_ring01_fx,bForceRemoveInstantly=True)
        self.ParticleProp().StopEmission(self.teleport_ring02_fx,bForceRemoveInstantly=True)
        self.ParticleProp().StopEmission(self.teleport_ring03_fx,bForceRemoveInstantly=True)
        self.teleport_ring01_fx = None
        self.teleport_ring02_fx = None
        self.teleport_ring03_fx = None

        if not self.teleport_base_fx:
            return
        self.ParticleProp().StopEmission(self.teleport_base_fx)
        self.teleport_base_fx = None

        if self.teleport_flash_fx:
            return

        self.teleport_ring03_fx = self.ParticleProp().Create(self.teleport_flash_fx_name, PATTACH_POINT, "root")
        self.SetThink(self.DestroyTeleporterFlash, gpGlobals.curtime + 1.0)

    def DestroyTeleporterFlash(self):
        if not self.teleport_flash_fx:
            return

        self.ParticleProp().StopEmission(self.teleport_flash_fx)
        self.teleport_base_fx = None

    def CreateRift(self):
        if self.teleport_rift:
            return
        self.teleport_rift = CreateUnit(UnitTeleporterRiftInfo.name, position=self.teleport_target_pos,
                                        owner_number=self.GetOwnerNumber())

    def DestroyRift(self):
        if not self.teleport_rift:
            return

        UTIL_Remove(self.teleport_rift)
        self.teleport_rift = None

    def CreateDummies(self, dummies, activate=False):
        if not self.teleporting_state:
            return
        super().CreateDummies(dummies, activate)

    def CreateRingBlocker(self):
        self.CreateDummies(self.GetDummies(), True)

    def DestroyRingBlocker(self):
        self.DestroyDummies()

    #blocknavareas = False
    #blockdensitytype = DENSITY_NONE
    autoconstruct = False
    barsoffsetz = 150.0

    nav_radius_obstacle_mode = True
    nav_radius_obstacle_scale = 0.65

    selected_units = ListField()

    teleport_ring01_fx = None
    teleport_ring02_fx = None
    teleport_ring03_fx = None
    teleport_ring_fx_name = 'pg_teleporter_ring'

    teleport_base_fx = None
    teleport_base_fx_name = 'pg_teleporter_base'

    teleport_flash_fx = None
    teleport_flash_fx_name = 'pg_teleporter_flash'

    teleport_rift = None
    teleport_ring_blocker = None

    teleport_time = 10

    teleport_think_context = 'TeleportThink'

    STATE_NONE = 0
    STATE_WINDUP = 1
    STATE_TELEPORTING = 2
    STATE_WINDDOWN = 3

    teleporting_state = IntegerField(value=STATE_NONE, networked=True, clientchangecallback='OnTeleportStateChanged')
    teleport_target_pos = VectorField(networked=True)

    # Animations for teleporter
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_IDLE_CLOSED',
        'ACT_OPEN',
        'ACT_CLOSE',
        'ACT_TELEPORT',
        'ACT_SPINUP',
        'ACT_SPIN',
        'ACT_SPINDOWN',
    ])

    unitinfofallback = TeleporterInfo
    unitinfovalidationcls = TeleporterInfo

