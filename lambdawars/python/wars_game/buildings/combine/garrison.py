from vmath import Vector, QAngle
from core.buildings import UnitBaseFactory as BaseClass
from .basepowered import PoweredBuildingInfo, BaseFactoryPoweredBuilding
from entities import entity 

@entity('build_comb_garrison', networked=True)
class CombineGarrison(BaseFactoryPoweredBuilding, BaseClass):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -210, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0, 0, 60)
    
# Register unit
class GarrisonInfo(PoweredBuildingInfo):
    name = 'build_comb_garrison'
    displayname = '#BuildCombGar_Name'
    description = '#BuildCombGar_Description'
    cls_name = 'build_comb_garrison'
    image_name = 'vgui/combine/buildings/build_comb_garrison'
    modelname = 'models/pg_props/pg_buildings/combine/pg_combine_garrison.mdl'
    explodemodel = 'models/pg_props/pg_buildings/combine/pg_combine_garrison_destruction.mdl'
    idleactivity = 'ACT_IDLE'
    #workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    techrequirements = ['build_comb_hq']
    costs = [('requisition', 50)]
    health = 700
    buildtime = 40.0
    abilities = {
		0: "unit_metropolice_riot",
		1: "unit_metropolice",
		2: "unit_metropolice_smg1",
		4: "unit_combine",
		5: "unit_combine_sg",
		6: "unit_combine_ar2",
		8: "unit_combine_heavy",
		
		11: 'cancel',
    } 
    sound_work = 'combine_garrison_working'
    sound_select = 'build_comb_garrison'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = PoweredBuildingInfo.sai_hint | set(['sai_building_barracks'])
