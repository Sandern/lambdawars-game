from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity
from particles import PATTACH_POINT_FOLLOW
    
@entity('build_reb_techcenter', networked=True)
class RebelsTechCenter(BaseClass):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    rallylineenabled = False
    customeyeoffset = Vector(0,0,60)
    
# Register unit
class TechCenterInfo(WarsBuildingInfo):
    name = "build_reb_techcenter"
    displayname = "#BuildRebTechCenter_Name"
    description = "#BuildRebTechCenter_Description"
    cls_name = "build_reb_techcenter"
    image_name = 'vgui/rebels/buildings/build_reb_tech_center'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_rebel_tech_center.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_rebel_tech_center_destruction.mdl'
    costs = [('requisition', 50), ('scrap', 50)]
    resource_category = 'technology'
    health = 800
    buildtime = 80.0
    scale = 0.85
    techrequirements = ['build_reb_specialops']
    abilities = {
        0: 'fireexplosivebolt_unlock',
        1: 'tau_alt_fire_unlock',
        8: 'cancel',
    } 
    idleactivity = 'ACT_IDLE'
    #workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    sound_work = 'rebel_munitions_working' #'ATV_engine_idle'
    sound_select = 'build_reb_techcenter'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'pg_rebel_barracks_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_research'])