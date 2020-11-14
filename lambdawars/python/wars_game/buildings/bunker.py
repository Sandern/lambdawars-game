from vmath import Vector, AngleVectors
from core.buildings import GarrisonableBuildingInfo


class BunkerInfo(GarrisonableBuildingInfo):
    name = 'bunker_test'
    modelname = 'models/structures/combine/barracks.mdl'
    health = 500
    attackpriority = 0
    sound_select = 'build_comb_garrison'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'building_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    
    requirerotation = True
    
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(1216, 0, 0))
        forward = Vector()
        AngleVectors(self.targetangle, forward)
        inst.SetControlPoint(3, targetpos + forward * 32.0)
        
    infoparticles = ['cone_of_fire']