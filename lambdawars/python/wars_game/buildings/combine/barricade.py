from vmath import Vector, AngleVectors
from core.units import CoverSpot
from wars_game.buildings.basebarricade import BaseBarricadeInfo

class CombineBarricadeInfo(BaseBarricadeInfo):
    name = 'build_comb_barricade'
    displayname = '#BuildCombBarricade_Name'
    description = '#BuildCombBarricade_Description'
    image_name = 'VGUI/combine/buildings/build_comb_barricade.vmt'
    modelname = 'models/props_combine/combine_barricade_short01a.mdl'
    costs = [[('requisition', 4)], [('kills', 1)]]
    techrequirements = ['build_comb_garrison']
    health = 150
    buildtime = 5.0
    ispriobuilding = False
    placeatmins = True
    placemaxrange = 96.0
    targetatgroundonly = False
    requirerotation = True
    sound_death = 'build_comb_mturret_explode'
    viewdistance = 192
    attributes = ['defence']
    abilities   = {
        8: 'cancel',
    } 
    cover_spots = [
        CoverSpot(offset=Vector(-40, -24, 0)),
        CoverSpot(offset=Vector(-40, 24, 0)),
    ]
    
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(96, 0, 0))
        forward = Vector()
        AngleVectors(self.targetangle, forward)
        inst.SetControlPoint(3, targetpos + forward * 32.0)
        
    infoparticles = ['direction_indicator']
    
class OverrunCombineBarricadeInfo(CombineBarricadeInfo):
    name = 'overrun_build_comb_barricade'
    techrequirements = []
    costs = [('kills', 1)]
