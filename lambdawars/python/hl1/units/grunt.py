from srcbase import MAX_TRACE_LENGTH
from vmath import Vector, QAngle, AngleVectors
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity, FireBulletsInfo_t
from gamerules import GetAmmoDef
import random
if isserver:
    from utils import UTIL_Remove
    from animation import Animevent
    from unit_helper import BaseAnimEventHandler
    
@entity('unit_grunt', networked=True)
class UnitGrunt(BaseClass):
    """ Half-life 1 grunt """
    def Precache(self):
        super(UnitGrunt, self).Precache()
    
        self.PrecacheScriptSound('Weapon_SMG1.Single')
    
    def Spawn(self):
        self.Precache()
        
        super(UnitGrunt, self).Spawn()
        
    def StartRangeAttack(self, enemy):
        self.DoAnimation(self.ANIM_ATTACK_PRIMARY)
        
        # Get origin and direction
        # Attachment "0" is the muzzle attachment
        vecShootOrigin = Vector()
        vecShootDir = Vector()
        self.GetAttachment('0', vecShootOrigin)
        vecShootAngle = QAngle(self.eyepitch, self.eyeyaw, 0.0)
        AngleVectors(vecShootAngle, vecShootDir)
        
        attackinfo = self.unitinfo.AttackRange
    
        # Just fire bullets
        info = FireBulletsInfo_t()
        info.shots = 7
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        #info.vecspread = self.bulletspread # Not used right now
        info.distance = MAX_TRACE_LENGTH
        info.ammotype = GetAmmoDef().Index('SMG1')
        info.tracerfreq = 2
        info.damage = attackinfo.damage
        
        self.FireBullets(info)
        
        # Use the smg1 fire sound for now
        self.EmitSound('Weapon_SMG1.Single')
        
    def EventHandlerPrimaryAttack(self, data=0):
        # Muzzle flash
        if isclient:
            self.DoMuzzleFlash()
            self.DispatchMuzzleEffect('SMG1 0', False)
        
    # Vars
    maxspeed = 220.0
    yawspeed = 40.0
    jumpheight = 40.0 
    
    # Activity list
    activitylist = list( BaseClass.activitylist )
    activitylist.extend( [
        'ACT_GRUNT_LAUNCH_GRENADE',
        'ACT_GRUNT_MP5_CROUCHING',
        'ACT_GRUNT_MP5_STANDING',
        'ACT_GRUNT_SHOTGUN_CROUCHING',
        'ACT_GRUNT_SHOTGUN_STANDING',
        'ACT_GRUNT_TOSS_GRENADE',
    ] )
    
    # Animation translation table
    acttables = {
        Activity.ACT_IDLE : 'ACT_GRUNT_MP5_STANDING',
        Activity.ACT_MP_JUMP : Activity.ACT_JUMP,
        Activity.ACT_RANGE_ATTACK1 : 'ACT_GRUNT_MP5_STANDING',
    }
    
    if isserver:
        # Animation Events
        aetable = {
            Animevent.AE_NPC_BODYDROP_HEAVY : BaseAnimEventHandler(),
            Animevent.AE_NPC_SWISHSOUND : BaseAnimEventHandler(),
            Animevent.AE_NPC_180TURN : BaseAnimEventHandler(),
        }
        
    # Anims Events
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_ATTACK_PRIMARY' : EventHandlerPrimaryAttack,
    } )
        
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=0.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,#LegAnimType_t.LEGANIM_GOLDSRC,
        useaimsequences=False,
        invertposeparameters=True,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super(UnitGrunt.AnimStateClass, self).__init__(outer, animconfig)
            self.newjump = False
        
        def OnNewModel(self):
            super(UnitGrunt.AnimStateClass, self).OnNewModel()

            # Grunt only has an aim pitch (and only works with ACT_GRUNT_MP5_STANDING)
            self.bodypitch = self.outer.LookupPoseParameter("XR")

# Register unit
class GruntInfo(UnitInfo):
    name = "unit_grunt"
    cls_name = "unit_grunt"
    displayname = "#ASW_Grunt_Name"
    description = "#ASW_Grunt_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/hgrunt.mdl'
    hulltype = 'HULL_HUMAN'
    health = 95
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    class AttackRange(UnitInfo.AttackRange):
        damage = 3
    attacks = 'AttackRange'
    