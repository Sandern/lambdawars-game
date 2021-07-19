from srcbase import SOLID_NONE
from core.units import CoverSpot
from vmath import Vector, AngleVectors
from core.buildings import CreateDummy
from wars_game.buildings.dynmountableturret import UnitDynMountableTurret, WarsDynMountTurretInfo
from entities import entity, DENSITY_NONE, DENSITY_GAUSSIANECLIPSE
#, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS

# TODO: Make different from the combine one
@entity('rebels_mountableturret', networked=True)
class UnitRebelsMountableTurret(UnitDynMountableTurret):
    def __init__(self):
        super(UnitRebelsMountableTurret, self).__init__()

        #was true
        #self.bodytargetoriginbased = False
        self.SetEnterOffset(Vector(-64, 0, 0))
        #self.SetEnterOffset(Vector(-90, 0, 0))

    #if isserver:
        #def Spawn(self):
		#	super().Spawn()
			#self.SetSolid(SOLID_NONE)
			# Turn off unit collision, because it's a pain in the ass for this collision model
			# Bullets will still be blocked and units still try to avoid based on the density
			#self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup()) 
			#self.SetCollisionGroup(WARS_COLLISION_GROUP_IGNORE_ALL_UNITS)
			
    def GetTracerType(self): return "AR2Tracer"
    autoconstruct = False
    aimtype = UnitDynMountableTurret.AIMTYPE_POSE
    barrelattachmentname = 'muzzle'
    ammotype = 'AR2'
    firesound = 'Weapon_FuncTank.Single'
    muzzleoptions = 'COMBINE muzzle'
    customeyeoffset = Vector(0, 0, 24)
    #blocknavareas = False
    blockdensitytype = DENSITY_NONE
    #blockdensitytype = DENSITY_GAUSSIANECLIPSE
    #buildingsolidmode = SOLID_NONE
    
class MountableTurretInfo(WarsDynMountTurretInfo):
    # Info
    name = "rebels_mountableturret"
    cls_name = "rebels_mountableturret"
    displayname = "#BuildRebMountTurret_Name"
    description = "#BuildRebMountTurret_Description"
    #Rebel Version ####
    modelname = 'models/props_combine/bunker_gun01.mdl'
    image_name  = "vgui/rebels/buildings/build_reb_mountgun.vmt"
    image_dis_name = "vgui/rebels/buildings/build_reb_mountgun_dis.vmt"
    #Combine version ####
    #modelname = 'models/props_combine/bunker_gun01.mdl'
    #image_name  = 'vgui/combine/buildings/build_comb_mountgun.vmt'
    #image_dis_name = 'vgui/combine/buildings/build_comb_mountgun_dis.vmt'
    health = 200
    buildtime = 24.0
    costs = [[('requisition', 20)], [('kills', 4)]]
    techrequirements = ['build_reb_munitiondepot']
    attributes = ['defence', 'ar1']
    zoffset = 28.0
    population = 0
    # Manpoint dictates how far away the rebel needs to be to man the gun. The greater the x val,
    # The farther the rebel has to be to enter it.
    #manpoint = Vector(-42, 0, 0)
    manpoint = Vector(-42, 0, 0)
    #ignoreunitmovement = True
    #customeyeoffset = Vector(0, 0, 12.0)
    #customyeoffset = Vector(0, 0, )
    sound_death = 'build_reb_mturret_explode'
    viewdistance = 192
	
    abilities = {
        8: 'cancel',
    }
    # This controls the models positioning and highlighting
    dummies = [
        CreateDummy(
            # This offset controls model position.
            # The Models positioning affects the ability of the gun firing and must be changed accordingly
            #-32 was the original height, -48 is the height which the gun fires correctly...
            # The smallest problem free value is -43

            #offset=Vector(4, 0, -32),
            offset=Vector(6, -2.5, -39.5),
            #Rebel model
            modelname='models/pg_props/pg_buildings/rebels/pg_rebel_mountableturret.mdl',
            #Combine Model
            #modelname = 'models/props_combine/combine_barricade_short01a.mdl',
            idleactivity='ACT_IDLE',
            constructionactivity='ACT_CONSTRUCTION',
            explodeactivity='ACT_EXPLODE',
            # This is the size of the the hitbox when highlighted
            # X controls the models depth dimension
            # Y Controls the width dimension
            # Z Contols the height dimension
            #### MINS ######################
            #Default Min ###
            #mins=Vector(-29.137079, -68.622986, -2.941891),
            #Custom Min ###
            mins=Vector(-29, -40, -2),
            viewdistance = 192,
            #### MAXS #######
            #Default Max ###
            #maxs=Vector(17.928478, 55.692348, 77.737030),
            #Custom Maxs ###
            maxs=Vector(10, 50, 50),
            ################################
			
            #blocknavareas = False,
            #blockdensitytype = DENSITY_GAUSSIANECLIPSE,
            #ignoreunitmovement = True,
			
            # This vars control if units can go inside hitbox
            blocknavareas = False,
            blockdensitytype = DENSITY_GAUSSIANECLIPSE,
        ),
    ]
    cover_spots = [
        CoverSpot(offset=Vector(-50, -48, 24)),
        CoverSpot(offset=Vector(-44, 48, 24)),
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
		
    class AttackTurret(WarsDynMountTurretInfo.AttackTurret):
        damage = 20
        attackspeed = 0.1
        attributes = ['ar1']
        maxrange = 1152.0
    attacks = 'AttackTurret'
	
class DestroyHQMountableTurretInfo(MountableTurretInfo):
    name = "destroyhq_reb_mountableturret"
    techrequirements = ['build_reb_munitiondepot_destroyhq']
    
class OverrunMountableTurretInfo(MountableTurretInfo):
    name = "overrun_reb_mountableturret"
    techrequirements = ['or_tier2_research']
    hidden = True
    costs = [('kills', 30)]

# ======================================================================================================================
# ============================================ Squad Wars Barricade ====================================================
# ======================================================================================================================

class MountableTurretCharInfo(MountableTurretInfo):
    name = 'char_mountableturret'
    techrequirements = []
    costs = []
    rechargetime = 90.0