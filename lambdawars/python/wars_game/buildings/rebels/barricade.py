from vmath import Vector, AngleVectors
from core.units import CoverSpot
from wars_game.buildings.basebarricade import BaseBarricadeInfo, BaseBarricade as BaseClass
from entities import WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, entity

@entity('build_barricade_rebels')
class RebelsBarricade(BaseClass):
    def Spawn(self):
        super().Spawn()
        
        # Turn off unit collision, because it's a pain in the ass for this collision model
        # Bullets will still be blocked and units still try to avoid based on the density 
        #self.SetCollisionGroup(WARS_COLLISION_GROUP_IGNORE_ALL_UNITS)
            
class RebelsBarricadeInfo(BaseBarricadeInfo):
    name = 'build_reb_barricade'
    cls_name = 'build_barricade_rebels'
    displayname = '#BuildRebBarricade_Name'
    description = '#BuildRebBarricade_Description'
    image_name = 'vgui/rebels/buildings/build_reb_barricade.vmt'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_rebel_barricade.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_rebel_barricade_des.mdl'
    costs = [[('requisition', 5)], [('kills', 2)]]
    techrequirements = ['build_reb_barracks']
    health = 125
    buildtime = 8.0
    ispriobuilding = False
    placemaxrange = 96.0
    targetatgroundonly = False
    requirerotation = True
    idleactivity = 'ACT_IDLE'
    constructionactivity = 'ACT_CONSTRUCTION'
    explodeactivity = 'ACT_EXPLODE'
    sound_death = 'build_reb_mturret_explode'
    attributes = ['defence']
    viewdistance = 192
    abilities = {
        8: 'cancel',
    } 
    cover_spots = [
        CoverSpot(offset=Vector(-50, -48, 24)),
        CoverSpot(offset=Vector(-47, 0, 24)),
        CoverSpot(offset=Vector(-44, 48, 24)),
    ]
    
    #mins = Vector(-15, -75, 0)
    #maxs = Vector(25, 75, 60)
    
    #ignoreunitmovement = True
    
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(128, 0, 0))
        forward = Vector()
        AngleVectors(self.targetangle, forward)
        inst.SetControlPoint(3, targetpos + forward * 32.0)
        
    infoparticles = ['direction_indicator']
	
class DestroyHQRebelsBarricadeInfo(RebelsBarricadeInfo):
    name = 'build_reb_barricade_destroyhq'
    techrequirements = ['build_reb_barracks_destroyhq']
    
class OverrunRebelsBarricadeInfo(RebelsBarricadeInfo):
    name = 'overrun_build_reb_barricade'
    techrequirements = []
    costs = [('kills', 1)]

# ======================================================================================================================
# ============================================ Squad Wars Barricade ====================================================
# ======================================================================================================================

class RebelsBarricadeCharInfo(RebelsBarricadeInfo):
    name = 'build_char_barricade'
    costs = []
    rechargetime = 30.0
    techrequirements = []