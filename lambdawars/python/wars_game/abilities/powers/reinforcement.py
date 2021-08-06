from srcbase import MAX_COORD_FLOAT
from vmath import Vector, QAngle, AngleVectors, vec3_origin
from core.abilities import AbilityTarget, AbilityUpgradeValue
from core.units import GetUnitInfo, CreateUnit, unitpopulationcount, GetMaxPopulation
from entities import GetMapBoundaryList, CBaseFuncMapBoundary
from navmesh import NavMeshGetPositionNearestNavArea
from fields import UpgradeField, FloatField
from fow import FogOfWarMgr
from utils import UTIL_Remove
import random

if isserver:
    from entities import CreateEntityByName, DispatchSpawn, variant_t
    from core.units.intention import BaseAction
    

class AbilityReinforcement(AbilityTarget):
    name = "reinforcement"
    displayname = '#AbilityReinforcement_Name'
    description = '#AbilityReinforcement_Description'
    image_name = 'vgui/rebels/abilities/reinforcement'
    rechargetime = 360.0
    set_initial_recharge = True
    population = 5
    techrequirements = ['build_reb_barracks', 'build_reb_munitiondepot', 'build_reb_specialops', 'build_reb_vortigauntden', 'build_reb_triagecenter', 'build_reb_techcenter']
    
    costs = [('requisition', 100), ('scrap', 100)]

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        owner = unit.GetOwnerNumber()

        if info.population:
            # Check population count
            if unitpopulationcount[owner]+info.population > GetMaxPopulation(owner):
                requirements.add('population')
        return requirements
    
    if isserver:
        def CreateTeleport(self, position):
            def SetupTeleport(teleport):
                teleport.lifetime = 15.0
            teleport = CreateUnit('unit_teleporter_rift', position, owner_number=self.ownernumber,
                                  fnprespawn=SetupTeleport)
            teleport.SpawnUnit()

        def DoAbility(self):
            position = self.mousedata.endpos
            owner = self.ownernumber

            adjustedtargetpos = NavMeshGetPositionNearestNavArea(position, beneathlimit=2048.0)
            if adjustedtargetpos != vec3_origin:
                position = adjustedtargetpos

            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            if FogOfWarMgr().PointInFOW(position, owner):
                self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
                return

            self.CreateTeleport(position)

            self.SetRecharge(self.unit)

            self.Completed()

    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos + self.particleoffset)
        inst.SetControlPoint(2, Vector(256, 256, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))

    infoparticles = ['range_radius_radar']



    allowmulitpleability = True

class OverrunAbilityReinforcement(AbilityReinforcement):
    name = 'overrun_reinforcement'
    description = '#AbilityReinforcementOR_Description'
    techrequirements = []
    rechargetime = 60.0
    set_initial_recharge = False
    population = 10
    costs = [('kills', 20)]
    #costs = []
