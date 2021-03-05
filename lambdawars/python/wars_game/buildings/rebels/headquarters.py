from srcbase import SOLID_BBOX
from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass, constructedlistpertype
from core.abilities import SubMenu
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_reb_hq', networked=True)
class RebelsHeadquarters(BaseClass):
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
                self.StartChimneySmoke()
            else:
                self.StopChimneySmoke()
                
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            self.StopChimneySmoke()
            
        def ExplodeHandler(self, event):
            self.StopChimneySmoke()
            super().ExplodeHandler(event)           
            
        def StartChimneySmoke(self):
            if not self.chimneyfx:
                self.chimneyfx = self.ParticleProp().Create("pg_chimney", PATTACH_POINT_FOLLOW, 'chimney')
            if not self.chimneyfx2:
                self.chimneyfx2 = self.ParticleProp().Create("pg_chimney_small", PATTACH_POINT_FOLLOW, 'chimney_crane')
            
        def StopChimneySmoke(self):
            if self.chimneyfx:
                self.ParticleProp().StopEmission(self.chimneyfx)
                self.chimneyfx = None
            if self.chimneyfx2:
                self.ParticleProp().StopEmission(self.chimneyfx2)
                self.chimneyfx2 = None
            
    else:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem( "pg_chimney" )
            PrecacheParticleSystem( "pg_chimney_small" )


    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)

    chimneyfx = None
    chimneyfx2 = None
    scaleprojectedtexture = 1.2
    #buildingsolidmode = SOLID_BBOX

# Register unit
class RebelHQInfo(WarsBuildingInfo):
    name = "build_reb_hq"
    cls_name = "build_reb_hq"
    displayname = '#BuildRebHQ_Name'
    description = '#BuildRebHQ_Description'
    image_name = 'vgui/rebels/buildings/build_reb_hq'
    modelname = 'models/pg_props/pg_buildings/pg_rebel_hq.mdl'
    explodemodel = 'models/pg_props/pg_buildings/pg_rebel_hq_des.mdl'
    minimapicon_name = "hud_minimap_hq"
    minimaphalfwide = 5
    minimaphalftall = 5
    minimaplayer = -1  # Draw earlier than units to avoid overlapping
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    costs = [('requisition', 300)]
    #techrequirements = ['build_reb_triagecenter']
    buildtime = 100.0
    health = 2000
    abilities = {
        #0: 'unit_vortigaunt',
        #1: 'unit_dog',
        0: 'unit_rebel_engineer',
        1: 'unit_rebel_scout',
        #2: 'unit_rebel_partisan',
        8: 'cancel',
    }
    population = 0
    providespopulation = 7
    generateresources = {'type' : 'requisition', 'amount' : 1.0, 'interval' : 1.0}
    sound_select = 'build_reb_hq'
    sound_death = 'build_reb_hq_destroy'
    #explodeparticleeffect = 'building_explosion'
    explodeparticleeffect = 'pg_rebel_HQ_explosion'
    explodeshake = (10, 100, 5, 6000) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_hq'])
    placerestrictions = [
        {'unittype' : 'scrap_marker', 'radius' : 180.0},
        {'unittype' : 'scrap_marker_small', 'radius' : 180.0},
    ]
    
class DestroyHQRebelHQInfo(RebelHQInfo):
    name = 'build_reb_hq_destroyhq'
    costs = [('requisition', 300)]
    health = 2000
    buildtime = 100
    unitenergy = 0
    techrequirements = []
    abilities = {
        0: 'destroyhq_unit_rebel_engineer',
        1: 'unit_rebel_scout',
        8: 'cancel',
    }
    population = 0
    providespopulation = 7
    #generateresources = {'type' : 'requisition', 'amount' : 1.0, 'interval' : 1.0}
    
# OVERRUN version
class OverrunRebelHQInfo(RebelHQInfo):
    name = 'build_reb_hq_overrun'
    #cls_name    = "build_reb_hq"
    #displayname = '#BuildRebHQ_Name'
    #description = '#BuildRebHQ_Description'
    #image_name  = 'vgui/rebels/buildings/build_reb_hq'
    #modelname = 'models/structures/resistance/hq.mdl'
    #costs = [('requisition', 20)]
    #health = 2000
    #buildtime = 100.0
    unitenergy = 0
    abilities   = {
        0 : 'overrun_unit_rebel_engineer',
        8 : 'or_tier2_research',
        3: SubMenu(name='rebel_t1_units',
                   displayname='#Tier1MenuUnits_Name',
                   description='#Tier1MenuUnits_Description',
                   image_name="VGUI/combine/abilities/tier_1_menu",
                   abilities={
                              0: 'overrun_unit_rebel_partisan_molotov',
                              1: 'overrun_unit_rebel',
                              #2: 'overrun_unit_rebel_partisan',
                              11: 'menuup',
                              }),
        7: SubMenu(name='rebel_t2_units',
                   displayname='#Tier2MenuUnits_Name',
                   description='#Tier2MenuUnits_Description',
                   image_name="VGUI/combine/abilities/tier_2_menu",
                   abilities={
								 0: 'overrun_unit_rebel_sg',
								 1: 'overrun_unit_rebel_ar2',
								 2: 'overrun_unit_rebel_medic',
								 3: 'overrun_unit_rebel_flamer',
								 4: 'overrun_unit_rebel_heavy',
								 5: 'overrun_unit_rebel_tau',
								 11: 'menuup',
                              }),
        11: SubMenu(name='rebel_t3_units',
                   displayname='#Tier3MenuUnits_Name',
                   description='#Tier3MenuUnits_Description',
                   image_name="VGUI/combine/abilities/tier_3_menu",
                   abilities={
                              0: 'overrun_unit_vortigaunt',
                              1: 'overrun_unit_rebel_veteran',
                              2: 'overrun_unit_rebel_rpg',
                              3: 'overrun_unit_dog',
                              11: 'menuup',
                              }),
    }
    population = 0
    providespopulation = 25
    generateresources = {'type' : 'kills', 'amount' : 1.0, 'interval' : 20.0}
    #sound_select = 'build_reb_hq'
    #sound_death = 'build_generic_explode1'
    #explodeparticleeffect = 'building_explosion'
    #explodeshake = (10, 100, 5, 6000) # Amplitude, frequence, duration, radius

@entity('build_sw_beacon', networked=True)
class BuildBeaconSW(BaseClass):
    def Spawn(self):
        super().Spawn()

        self.SetCanBeSeen(False)

class BeaconSW(RebelHQInfo):
    name = 'build_sw_beacon'
    cls_name = 'build_sw_beacon'
    modelname = 'models/pg_props/pg_buildings/pg_toilet_hut.mdl'
    sound_select = 'build_reb_billet'
    sound_death = ''
    explodemodel = ''
    costs = []
    buildtime = 0.0
    health = 99999
    viewdistance = 256
    providescaps = [('power_sw', 1500)]
    providespopulation = 1
    generateresources = {}
    placerestrictions = []
    idleactivity = ''
    explodeactivity = ''
    constructionactivity = ''
    workactivity = ''
    minimapicon_name = 'hud_minimap_hq'
    abilities = {
        0: 'char_rebel_soldier',
        1: 'char_rebel_scout',
        2: 'char_rebel_veteran',
        3: 'char_metropolice_scout',
        4: 'char_rebel_flamer',
        5: 'char_rebel_rpg',
        6: 'char_combine_elite',
        7: 'char_combine_soldier',
        8: 'char_rebel_medic',
        9: 'char_metropolice_support',
        10: 'char_rebel_engineer',
        #11: SubMenu(name='beacon_supportmenu_char', displayname='#CharSupportMenu_Name', description='#CharSupportMenu_Description',
                   #image_name='vgui/abilities/building_menu.vmt', abilities={
                        #11: 'menuup',
                   #})
        11: 'char_metropolice_tank',
    }
    recharge_other_abilities = [
        'char_rebel_soldier',
        'char_rebel_scout',
        'char_rebel_veteran',
        'char_metropolice_scout',
        'char_rebel_flamer',
        'char_rebel_rpg',
        'char_combine_elite',
        'char_combine_soldier',
        'char_rebel_medic',
        'char_metropolice_support',
        'char_rebel_engineer',
        'char_metropolice_tank',
    ]


