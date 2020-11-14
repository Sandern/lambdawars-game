from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity 

@entity('build_reb_shack', networked=True)
class RebelsShack(BaseClass):
    # Settings
    autoconstruct = False
    buildtarget = Vector(50, -50, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0,0,60)
    
# Register unit
class RebelShackInfo(WarsBuildingInfo):
    name        = "build_reb_shack" 
    displayname = "#BuildShack_Name"
    description = "#BuildShack_Description"
    cls_name    = "build_reb_shack"
    image_name  = 'vgui/rebels/buildings/build_reb_billet'
    modelname = 'models/structures/resistance/shack.mdl'
    techrequirements = []
    costs = [('requisition', 40)]
    health = 400
    buildtime = 15.0
    providespopulation = 50
    abilities   = {
        0 : 'unit_citizen_barricade',
        1 : 'unit_rebel_partisan',
        8: 'cancel',
    } 
    sound_select = 'build_reb_billet'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks'])