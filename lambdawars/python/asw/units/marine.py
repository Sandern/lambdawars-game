from vmath import Vector
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity
import random
if isserver:
    from utils import UTIL_SetSize, UTIL_Remove
    
@entity('unit_marine', networked=True)
class UnitMarine(BaseClass):
    def Spawn(self):
        #self.Precache()

        super(UnitMarine, self).Spawn()
        
        if isserver:
            UTIL_SetSize(self, Vector(-13,-13,   0), Vector(13, 13, 72))
            
            self.skin = random.randint(0, 4)

    # Vars
    maxspeed = 190.0
    yawspeed = 40.0
    jumpheight = 40.0 
    
    # Animation translation table
    acttables = {
        'default' : {
            Activity.ACT_IDLE : Activity.ACT_IDLE_RIFLE,
            Activity.ACT_WALK : Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN : Activity.ACT_RUN_AIM_RIFLE,
            Activity.ACT_MP_JUMP : Activity.ACT_JUMP,
            #Activity.ACT_RANGE_ATTACK1 : Activity.ACT_WALK_AIM_RIFLE,
        }
    }
    
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=45.0,
        leganimtype=LegAnimType_t.LEGANIM_9WAY,
        #useaimsequences=True,
        invertposeparameters=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super(UnitMarine.AnimStateClass, self).__init__(outer, animconfig)
            self.newjump = False
        
        def OnNewModel(self):
            super(UnitMarine.AnimStateClass, self).OnNewModel()

            self.movex = self.outer.LookupPoseParameter("move_x")
            self.movey = self.outer.LookupPoseParameter("move_y")
            
            self.bodyyaw = self.outer.LookupPoseParameter("aim_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("aim_pitch")

# Register unit
class UnitMarineInfo(UnitInfo):
    name = "unit_marine"
    cls_name = "unit_marine"
    displayname = "#ASW_Marine_Name"
    description = "#ASW_Marine_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/swarm/marine/marine.mdl'
    health = 220
    weapons = ['asw_weapon_rifle']
    attributes = ['heavy']
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
class UnitMarineFlamerInfo(UnitMarineInfo):
    name = "unit_marine_flamer"
    displayname = "#ASW_Marine_Name"
    description = "#ASW_Marine_Description"
    weapons = ['asw_weapon_flamer']
    attributes = ['heavy', 'fire']
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }