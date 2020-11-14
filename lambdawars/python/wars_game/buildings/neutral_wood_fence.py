from entities import entity
from .neutral_barricade import NeutralBarricadeInfo, NeutralBarricade as BaseClass

# Entity is here for linkage in Hammer, so don't remove
@entity('build_neutral_wood_fence')
class WoodFenceBarricade(BaseClass):
    pass
    
class WoodFenceBarricadeInfo(NeutralBarricadeInfo):
    name = "build_neutral_wood_fence" 
    cls_name = "build_neutral_wood_fence"
    displayname = '#WoodFanceBarricade_Name'
    description = '#WoodFanceBarricade_Description'
    image_name  = 'vgui/neutral/buildings/neutral_rock_barricade'
    modelname = 'models/pg_props/pg_buildings/other/pg_wood_fence_barricade.mdl'
    explodemodel = 'models/pg_props/pg_buildings/other/pg_wood_fence_barricade_des.mdl'
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_IDLE'
    explodeactivity = 'ACT_EXPLODE'
    health = 800
    population = 0 
    providespopulation = 0
    abilities   = {
        8 : 'cancel',
    }
    sound_select = 'build_neutral_rock_barricade'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius