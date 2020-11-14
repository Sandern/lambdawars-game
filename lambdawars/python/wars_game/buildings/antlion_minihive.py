from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity

@entity('build_ant_minihive')
class AntlionMiniHive(BaseClass):
    # Settings     
    autoconstruct = False
    buildtarget = Vector(0, -180, 0)
    buildangle = QAngle(0, 0, 0)

# Register unit
class AntlionMiniHiveInfo(WarsBuildingInfo):
    modname     = __name__
    name        = "build_ant_minihive"
    cls_name    = "build_ant_minihive"   
    image_name  = "vgui/units/minihive.vmt"  
    abilities   = {                      
        0 : 'unit_antlion',
        1 : 'unit_antlionworker',
        2 : 'unit_antlionsuicider',
    }
    health = 650
    modelname = 'models/props_wasteland/rockcliff05a.mdl'
    displayname = "#AntlionMiniHive_Name"
    description = "#AntlionMiniHive_Description"
    costs = [('grubs', 5)]
    providespopulation = 5
    buildtime = 20.0