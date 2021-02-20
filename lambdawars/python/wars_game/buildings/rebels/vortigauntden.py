from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity

@entity('build_reb_vortigauntden', networked=True)
class RebelsVortigauntDen(BaseClass):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0,0,96)
    
# Register unit
class VortigauntDenInfo(WarsBuildingInfo):
    name        = "build_reb_vortigauntden" 
    cls_name    = "build_reb_vortigauntden"
    image_name  = 'vgui/rebels/buildings/build_reb_vortigauntden'
    displayname = '#BuildRebVortigauntDen_Name'
    description = '#BuildRebVortigauntDen_Description'
    modelname = 'models/structures/resistance/vortden.mdl'
    costs = [('requisition', 50), ('scrap', 50)]
    health = 800
    buildtime = 54.0
    techrequirements = ['build_reb_triagecenter']
    abilities   = {
        0 : 'unit_vortigaunt',
        #1 : 'unit_antlion', # -> Use bugbait ability of Vortigaunt instead
        8 : 'cancel',
    } 
    sound_select = 'build_reb_vortigauntden'
    sound_work = 'rebel_vortden_working'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_barracks', 'sai_building_vortden'])
    
# Register unit
class DestroyHQVortigauntDenInfo(VortigauntDenInfo):
    name        = "build_reb_vortigauntden_destroyhq"
    techrequirements = ['build_reb_triagecenter_destroyhq']
    abilities   = {
        0 : 'unit_vortigaunt',
        8 : 'cancel',
    } 