from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity

@entity('build_reb_billet', networked=True)
class RebelsBillet(BaseClass):
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    customeyeoffset = Vector(0,0,60)
    
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_FINISHED',
    ])
    
# Register unit
class BilletInfo(WarsBuildingInfo):
    name = "build_reb_billet" 
    cls_name = "build_reb_billet"
    displayname = '#BuildRebBillet_Name'
    description = '#BuildRebBillet_Description'
    image_name  = 'vgui/rebels/buildings/build_reb_billet'
    modelname = 'models/structures/resistance/billet.mdl'
    idleactivity = 'ACT_FINISHED'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    costs = [('requisition', 15)]
    #costs = [('requisition', 20)]
    health = 200
    buildtime = 20.0
    population = 0 # Billet itself does not take population
    providespopulation = 5
    viewdistance = 896
    abilities   = {
        8 : 'cancel',
    }
    sound_select = 'build_reb_billet'
    sound_death = 'build_reb_billet_destruction'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_population'])
	
class DestroyHQBilletInfo(BilletInfo):
    name = "build_reb_billet_destroyhq"
    costs = [('requisition', 15)]
    providespopulation = 5