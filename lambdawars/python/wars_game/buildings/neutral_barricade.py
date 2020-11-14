''' Base for neutral building usually blocking the path somewhere.'''

from vmath import Vector
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity
from entities import FOWFLAG_BUILDINGS_NEUTRAL_MASK

@entity('build_neutral_barricade', networked=True)
class NeutralBarricade(BaseClass):
    autoconstruct = False
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    customeyeoffset = Vector(0,0,64)
    
    def PassesDamageFilter(self, info):
        return True
    
    def TargetOverrideOrder(self, unit, data, selection, angle=None, player=None):
        ''' Overrides the default order of the unit targeting 
            this barricade to always attack it. 
        '''
        return unit.AttackMove(data.endpos, target=self, player=player, selection=selection)
    
class NeutralBarricadeInfo(WarsBuildingInfo):
    cls_name = "build_neutral_barricade"
    image_name  = 'vgui/neutral/buildings/neutral_rock_barricade'
    population = 0 
    providespopulation = 0
    abilities   = {
        8 : 'cancel',
    }
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius