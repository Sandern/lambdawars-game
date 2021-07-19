from vmath import Vector, AngleVectors
from wars_game.buildings.dynmountableturret import UnitDynMountableTurret, WarsDynMountTurretInfo
from core.buildings import CreateDummy
from entities import entity, DENSITY_NONE, DENSITY_GAUSSIANECLIPSE

@entity('comb_mountableturret', networked=True)
class UnitCombMountableTurret(UnitDynMountableTurret):
    def __init__(self):
        super(UnitCombMountableTurret, self).__init__()
        
        self.SetEnterOffset(Vector(-64, 0, 0))
        
    def GetTracerType(self): return "AR2Tracer"

    autoconstruct = False
    aimtype = UnitDynMountableTurret.AIMTYPE_POSE
    barrelattachmentname = 'muzzle'
    ammotype = 'AR2'
    firesound = 'Weapon_FuncTank.Single'
    muzzleoptions = 'COMBINE muzzle'
    customeyeoffset = Vector(0,0,24)
    blockdensitytype = DENSITY_NONE

class MountableTurretInfo(WarsDynMountTurretInfo):
    # Info
    name = 'comb_mountableturret'
    cls_name = 'comb_mountableturret'
    displayname = '#BuildCombMountTur_Name'
    description = '#BuildCombMountTur_Description'
    modelname = 'models/props_combine/bunker_gun01.mdl'
    image_name  = 'vgui/combine/buildings/build_comb_mountgun.vmt'
    image_dis_name = 'vgui/combine/buildings/build_comb_mountgun_dis.vmt'
    health = 300
    buildtime = 18.0
    costs = [[('requisition', 20)], [('kills', 4)]]
    techrequirements = ['build_comb_armory']
    attributes = ['defence', 'ar1']
    zoffset = 28.0
    population = 0
    manpoint = Vector(-40, 0, 0)
    viewdistance = 192
    
    sound_death = 'build_comb_mturret_explode'
    
    dummies = [
        CreateDummy(
            offset=Vector(0, 0, -2),
            modelname = 'models/props_combine/combine_barricade_short01a.mdl',
            blocknavareas = False,
            viewdistance = 192,
            blockdensitytype = DENSITY_GAUSSIANECLIPSE,
        ),
    ]
    
    # Ability
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(1216, 0, 0))
        forward = Vector()
        AngleVectors(self.targetangle, forward)
        inst.SetControlPoint(3, targetpos + forward * 32.0)
        
    infoparticles = ['cone_of_fire']
    
    abilities = {
        8 : 'cancel',
    }
    
    class AttackTurret(WarsDynMountTurretInfo.AttackTurret):
        damage = 20
        attackspeed = 0.1
        attributes = ['ar1']
        maxrange = 1152.0
    attacks = 'AttackTurret'
    
class OverrunMountableTurretInfo(MountableTurretInfo):
    name = "overrun_comb_mountableturret"
    techrequirements = ['or_tier2_research']
    costs = [('kills', 30)]
    hidden = True
    