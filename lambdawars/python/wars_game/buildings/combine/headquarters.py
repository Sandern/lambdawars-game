#  from srcbase import SOLID_BBOX
from vmath import Vector
from core.abilities import AbilityUpgradePopCap, SubMenu
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass, constructedlistpertype
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem


@entity('build_comb_hq', networked=True)
class CombineHQ(BaseClass):
    def CanGenerateResources(self, resourcetype, amount):
        owner = self.GetOwnerNumber()
        hqunits = constructedlistpertype[owner][self.GetUnitType()]
        if not hqunits or not hqunits[0] == self:
            return False
        return super().CanGenerateResources(resourcetype, amount)
        
    if isclient:
        def OnBuildStateChanged(self):
            super().OnBuildStateChanged()
            
            if self.isproducing:
                self.StartWorkParticals()
            else:
                self.StopWorkParticals()
                
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.StopWorkParticals()

        def StartWorkParticals(self):
            if not self.workparticalsfx:
                self.workparticalsfx = self.ParticleProp().Create("pg_blue_flash", PATTACH_POINT_FOLLOW, 'light')
            if not self.workparticalsfx2:
                self.workparticalsfx2 = self.ParticleProp().Create("pg_blue_strom02", PATTACH_POINT_FOLLOW, 'top')
            
        def StopWorkParticals(self):
            if self.workparticalsfx:
                self.ParticleProp().StopEmission(self.workparticalsfx)
                self.workparticalsfx = None
            if self.workparticalsfx2:
                self.ParticleProp().StopEmission(self.workparticalsfx2)
                self.workparticalsfx2 = None
            
    else:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem( "pg_blue_flash" )
            PrecacheParticleSystem( "pg_blue_strom02" )
    
    # Settings
    autoconstruct = False
    customeyeoffset = Vector(0, 0, 150)
    
    workparticalsfx = None
    workparticalsfx2 = None
    #buildingsolidmode = SOLID_BBOX
    
    
# Normal gamemode
class CombineHQInfo(WarsBuildingInfo):
    name = 'build_comb_hq'
    displayname = '#BuildComHQ_Name'
    description = '#BuildComHQ_Description'
    cls_name = "build_comb_hq"
    image_name = 'vgui/combine/buildings/build_comb_hq'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_hq.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_hq_des.mdl'
    minimapicon_name = 'hud_minimap_hq'
    minimaphalfwide = 5
    minimaphalftall = 5
    minimaplayer = -1  # Draw earlier than units to avoid overlapping
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    costs = [('requisition', 300)]
    health = 2000
    buildtime = 100.0
    abilities = {
        0: 'unit_stalker',
        1: 'unit_combine_citizen',
        3: SubMenu(name='combine_faction_abilities',
                   displayname='#AbilityHQCombineFactionMenu_Name',
                   description='#AbilityHQCombineFactionMenu_Description',
                   image_name="VGUI/combine/abilities/combine_faction_abilities",
                   abilities={0: 'dropsoldiers',
                              11: 'menuup',
                              }),
        8: 'cancel',
        11: 'comb_popupgrade1',
    }
    population = 0
    providespopulation = 9
    generateresources = {'type' : 'requisition', 'amount' : 1.0, 'interval' : 1.0}
    sound_select = 'build_comb_hq'
    sound_death = 'build_comb_hq_destroy'
    explodeparticleeffect = 'pg_combine_HQ_explosion'
    explodeshake = (10, 100, 5, 6000) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_hq','sai_scrap_collection'])
    
    placerestrictions = [
        {'unittype' : 'scrap_marker', 'radius' : 180.0},
        {'unittype' : 'scrap_marker_small', 'radius' : 180.0},
    ]

class CombPopUpgrade1(AbilityUpgradePopCap):
    name = 'comb_popupgrade1'
    displayname = '#CombPopUpgr1_Name'
    description = '#CombPopUpgr1_Description'
    image_name = 'vgui/combine/abilities/comb_popupgrade1'
    successorability = 'comb_popupgrade2'
    buildtime = 10.0
    providespopulation = 11
    costs = [('requisition', 40)]

class CombPopUpgrade2(AbilityUpgradePopCap):
    name = 'comb_popupgrade2'
    displayname = '#CombPopUpgr2_Name'
    description = '#CombPopUpgr2_Description'
    image_name = 'vgui/combine/abilities/comb_popupgrade2'
    successorability = 'comb_popupgrade3'
    buildtime = 12.0
    providespopulation = 20
    costs = [('requisition', 70)]

class CombPopUpgrade3(AbilityUpgradePopCap):
    name = 'comb_popupgrade3'
    displayname = '#CombPopUpgr3_Name'
    description = '#CombPopUpgr3_Description'
    image_name = 'vgui/combine/abilities/comb_popupgrade3'
    successorability = 'comb_popupgrade4'
    buildtime = 15.0
    providespopulation = 30
    costs = [('requisition', 125)]

class CombPopUpgrade4(AbilityUpgradePopCap):
    name = 'comb_popupgrade4'
    displayname = '#CombPopUpgr4_Name'
    description = '#CombPopUpgr4_Description'
    image_name = 'vgui/combine/abilities/comb_popupgrade4'
    buildtime = 19.0
    providespopulation = 30
    costs = [('requisition', 125)]
    
# OVERRUN version
class OverrunCombineHQInfo(WarsBuildingInfo):
    name = 'build_comb_hq_overrun'
    displayname = '#BuildComHQ_Name'
    description = '#BuildComHQ_Description'
    cls_name = 'build_comb_hq'
    image_name = 'vgui/combine/buildings/build_comb_hq'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_hq.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_hq_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    minimapicon_name = 'hud_minimap_hq'
    health = 2000
    abilities = {
        0: 'overrun_unit_combine',
        1: 'overrun_unit_combine_sg',
        2: 'overrun_unit_combine_ar2',
        3: 'overrun_unit_combine_elite',
        4: 'overrun_unit_combine_sniper',
        5: 'overrun_unit_hunter',
        6: 'overrun_unit_mortar_synth',
        8: 'or_tier2_research',
        9: 'overrun_unit_metropolice_riot',
        10: 'overrun_unit_metropolice',
        11: 'overrun_unit_stalker',
    }
    population = 0
    providespopulation = 25
    generateresources = {'type' : 'kills', 'amount' : 1.0, 'interval' : 20.0}
    hidden = True
    sound_select = 'build_comb_hq'
    sound_death = 'build_comb_hq_destroy'
    explodeparticleeffect = 'pg_combine_HQ_explosion'
    explodeshake = (10, 100, 5, 6000) # Amplitude, frequence, duration, radius