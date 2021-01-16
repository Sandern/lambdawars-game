from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem

@entity('build_reb_barracks', networked=True)
class RebelsBarracks(BaseClass):
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
            if self.chimneyfx:
                return
            self.chimneyfx = self.ParticleProp().Create("pg_chimney", PATTACH_POINT_FOLLOW, 'chimney')
            
        def StopChimneySmoke(self):
            if not self.chimneyfx:
                return
            self.ParticleProp().StopEmission(self.chimneyfx)
            self.chimneyfx = None
            
    else:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem("pg_chimney")

    # Settings     
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0, 0, 75)
    
    chimneyfx = None

class RebelBarInfo(WarsBuildingInfo):
    name = "build_reb_barracks"
    displayname = '#BuildRebBarracks_Name'
    description = '#BuildRebBarracks_Description'
    cls_name = "build_reb_barracks"
    image_name = 'vgui/rebels/buildings/build_reb_barracks'
    modelname = 'models/pg_props/pg_buildings/pg_rebel_barracks.mdl'
    explodemodel = 'models/pg_props/pg_buildings/pg_rebel_barracks_des.mdl'
    techrequirements = ['build_reb_billet']
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    zoffset = 0.0
    costs = [('requisition', 50)]
    health = 700
    buildtime = 45.0
    abilities = {
        0: 'unit_rebel_partisan_molotov',
        1: 'unit_rebel_partisan',
        4: 'unit_rebel',
        5: 'unit_rebel_sg',
        6: 'unit_rebel_ar2',
        8: 'unit_rebel_medic',
        9: 'unit_rebel_veteran',
        11: 'cancel',
    } 
    sound_work = 'rebel_barracks_working'
    sound_select = 'build_reb_barracks'
    sound_death = 'build_reb_bar_destroy'
    explodeparticleeffect = 'pg_rebel_barracks_explosion'
    explodeshake = (2, 10, 2, 512)  # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks'])

class TutorialRebelBarInfo(RebelBarInfo):
    name = "build_reb_barracks_tutorial"
    displayname = '#BuildRebBarracks_Name'
    description = '#BuildRebBarracks_Description'
    cls_name = "build_reb_barracks"
    image_name = 'vgui/rebels/buildings/build_reb_barracks'
    modelname = 'models/pg_props/pg_buildings/pg_rebel_barracks.mdl'
    explodemodel = 'models/pg_props/pg_buildings/pg_rebel_barracks_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    zoffset = 0.0
    techrequirements = ['build_reb_hq_tutorial']
    costs = [('requisition', 50)]
    health = 600
    buildtime = 45.0
    abilities = {
        0: 'unit_rebel_partisan_molotov',
        1: 'unit_rebel_partisan',
        4: 'tutorial_rebel',
        5: 'unit_rebel_sg',
        6: 'unit_rebel_ar2',
        8: 'unit_rebel_medic',
        9: 'unit_rebel_veteran',
        11: 'cancel',
    } 
    sound_work = 'rebel_barracks_working'
    sound_select = 'build_reb_barracks'
    sound_death = 'build_reb_bar_destroy'
    explodeparticleeffect = 'pg_rebel_barracks_explosion'
    explodeshake = (2, 10, 2, 512)  # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks'])

class DestroyHQRebelBarInfo(RebelBarInfo):
    name = "build_reb_barracks_destroyhq"
    displayname = '#BuildRebBarracks_Name'
    description = '#BuildRebBarracks_Description'
    cls_name = "build_reb_barracks"
    image_name = 'vgui/rebels/buildings/build_reb_barracks'
    modelname = 'models/pg_props/pg_buildings/pg_rebel_barracks.mdl'
    explodemodel = 'models/pg_props/pg_buildings/pg_rebel_barracks_des.mdl'
    explodemodel_lightingoffset = Vector(0, 0, 100)
    idleactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    workactivity = 'ACT_WORK'
    zoffset = 0.0
    techrequirements = ['build_reb_billet_destroyhq']
    costs = [('requisition', 50)]
    health = 600
    buildtime = 45.0
    abilities = {
        0: 'unit_rebel_partisan_molotov_destroyhq',
        1: 'unit_rebel_partisan_destroyhq',
        4: 'unit_rebel_destroyhq',
        8: 'destroyhq_unit_rebel_medic',
        9: 'destroyhq_unit_rebel_veteran',
        5: 'unit_rebel_sg_destroyhq',
        6: 'unit_rebel_ar2_destroyhq',
        11: 'cancel',
    } 
    sound_select = 'build_reb_barracks'
    sound_death = 'build_reb_bar_destroy'
    explodeparticleeffect = 'pg_rebel_barracks_explosion'
    explodeshake = (2, 10, 2, 512)  # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks'])