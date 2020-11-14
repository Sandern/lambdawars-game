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
    
def CreateBehaviorDropshipDrop(BaseClass):
    class BehaviorDropship(BaseClass):
        class ActionIdle(BaseAction):
            def Update(self):
                outer = self.outer
                path = outer.navigator.path
                if path.pathcontext != self or not path.success:
                    return self.SuspendFor(self.behavior.ActionMoveTo, 'Moving to deploy point', outer.targetdeploypos,
                                           pathcontext=self)
                return self.ChangeTo(self.behavior.ActionLand, 'Landing dropship')
            
        class ActionLand(BaseAction):
            def OnStart(self):
                self.outer.Land()
                
            def Update(self):
                if self.outer.locomotion.currentheight < 32.0:
                    return self.ChangeTo(self.behavior.ActionDeployTroops, 'Changing to deploying troops')
                return self.Continue()
                
        class ActionDeployTroops(BaseAction):
            def OnStart(self):
                self.outer.DeploySoldiers()
                return self.ChangeTo(self.behavior.ActionAscend, 'Ascending')
                
        class ActionAscend(BaseAction):
            def OnStart(self):
                self.outer.Ascend()
                
            def Update(self):
                if self.outer.locomotion.currentheight >= self.outer.locomotion.desiredheight:
                    return self.ChangeTo(self.behavior.ActionExitMap, 'Moving to exit point')
                return self.Continue()
                
        class ActionExitMap(BaseAction):
            def Update(self):
                outer = self.outer
                path = outer.navigator.path
                if path.pathcontext != self or not path.success:
                    return self.SuspendFor(self.behavior.ActionMoveTo, 'Moving to exit point', outer.exitpos,
                                           pathcontext=self)
                outer.SetThink(outer.SUB_Remove, gpGlobals.curtime)
                return self.Continue()

            def Remove(self):

                UTIL_Remove(self)
                
    return BehaviorDropship

class AbilityDropSoldiersUpgradeLvl2(AbilityUpgradeValue):
    name = 'dropsoldiers_upgrade_lvl2'
    displayname = '#AbilityDropsoldiersUpgrade_Name'
    description = '#AbilityDropsoldiersUpgrade_Description'
    upgradevalue = 2

class AbilityDropSoldiersUpgradeLvl3(AbilityDropSoldiersUpgradeLvl2):
    name = 'dropsoldiers_upgrade_lvl3'
    upgradevalue = 3

class AbilityDropSoldiers(AbilityTarget):
    name = "dropsoldiers"
    displayname = '#AbilityDropsoldiers_Name'
    description = '#AbilityDropsoldiers_Description'
    image_name = "VGUI/combine/abilities/ability_combine_dropship"
    rechargetime = 360.0
    set_initial_recharge = True
    population = 15
    techrequirements = ['build_comb_garrison', 'build_comb_armory', 'build_comb_specialops', 'build_comb_synthfactory', 'build_comb_mech_factory']
    costs = [('requisition', 200)]

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
        def CreateDropship(self, dropposition):
            #dropposition = self.mousedata.endpos

            # Find a suitable entry position
            unitinfo = GetUnitInfo('unit_combinedropship')



            dropshipspawnpos = Vector(random.uniform(-MAX_COORD_FLOAT + 1024, MAX_COORD_FLOAT - 1024),
                                      random.uniform(-MAX_COORD_FLOAT + 1024, MAX_COORD_FLOAT) - 1024, 0)
            dropshipexitpos = Vector(random.uniform(-MAX_COORD_FLOAT + 1024, MAX_COORD_FLOAT - 1024),
                                     random.uniform(-MAX_COORD_FLOAT + 1024, MAX_COORD_FLOAT - 1024), 2048)
            bloat = Vector(128, 128, 128)
            CBaseFuncMapBoundary.SnapToNearestBoundary(dropshipspawnpos, unitinfo.mins - bloat, unitinfo.maxs + bloat,
                                                       True)
            CBaseFuncMapBoundary.SnapToNearestBoundary(dropshipexitpos, unitinfo.mins - bloat, unitinfo.maxs + bloat,
                                                       True)

            # Create the dropship
            def SetupDropship(dropship):
                dropship.targetdeploypos = dropposition
                dropship.exitpos = dropshipexitpos
                dropship.uncontrollable = True
                #dropship.summoned = True
                dropship.lifetime = 50.0
                dropship.BehaviorGenericClass = CreateBehaviorDropshipDrop(dropship.BehaviorGenericClass)
            dropship = CreateUnit('unit_combinedropship', dropshipspawnpos, owner_number=self.ownernumber,
                                  fnprespawn=SetupDropship)
            dropship.MoveOrder(dropposition)



        def DoAbility(self):
            #dropposition = self.mousedata.endpos

            dropposition = self.mousedata.endpos
            owner = self.ownernumber

            adjustedtargetpos = NavMeshGetPositionNearestNavArea(dropposition, beneathlimit=2048.0)
            if adjustedtargetpos != vec3_origin:
                dropposition = adjustedtargetpos

            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            if FogOfWarMgr().PointInFOW(dropposition, owner):
                self.Cancel(cancelmsg='#Ability_NoVision', debugmsg='Player has no vision at target point')
                return

            if self.dropshipcount == 1:
                self.CreateDropship(dropposition)
            elif self.dropshipcount == 2:
                self.CreateDropship(dropposition+Vector(256,256,0))
                self.CreateDropship(dropposition+Vector(-256,256,0))
            elif self.dropshipcount == 3:
                self.CreateDropship(dropposition+Vector(256,256,0))
                self.CreateDropship(dropposition+Vector(256,-256,0))
                self.CreateDropship(dropposition+Vector(-256,256,0))

            self.SetRecharge(self.unit)

            self.Completed()

    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos + self.particleoffset)
        inst.SetControlPoint(2, Vector(512, 512, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))

    infoparticles = ['range_radius_radar']



    allowmulitpleability = True
    dropshipcount = UpgradeField(value=3, abilityname='dropsoldiers_upgrade_lvl3')

class AbilityDropSoldiersDestroyHQ(AbilityDropSoldiers):
    name = 'dropsoldiers_destroyhq'
    techrequirements = ['build_comb_garrison_destroyhq', 'build_comb_armory_destroyhq', 'build_comb_specialops_destroyhq', 'build_comb_synthfactory_destroyhq', 'build_comb_mech_factory_destroyhq']
