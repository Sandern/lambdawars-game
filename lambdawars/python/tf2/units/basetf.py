from vmath import Vector, vec3_origin
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass
from entities import networked, entity, Activity
from unit_helper import UnitAnimConfig, LegAnimType_t
import filesystem
import random
from fields import GenericField

if isserver:
    from utils import UTIL_Remove
    from entities import CBaseAnimating as BaseClassHat, CreateEntityByName, DispatchSpawn
else:
    from entities import C_BaseAnimating as BaseClassHat

@entity('hat', networked=True)
class Hat(BaseClassHat):
    """ The hat entitity. Crucial part of a team fortress 2 unit. """
    shoulddraw = True
    def ShouldDraw(self):
        return super(Hat, self).ShouldDraw() and self.shoulddraw
        
    if isserver:
        def Precache(self):
            super(Hat, self).Precache()
            
            self.PrecacheModel(self.GetModelName())
            
        def Spawn(self):
            self.Precache()
            
            super(Hat, self).Spawn()
            
            self.SetModel(self.GetModelName())
            

@networked
class UnitBaseTF(BaseClass):
    """ Team Fortress 2 base unit """
    def ShouldDraw(self):
        shoulddraw = super(UnitBaseTF, self).ShouldDraw()
        if self.hat:
            self.hat.shoulddraw = shoulddraw
            self.hat.UpdateVisibility()
        return shoulddraw
    
    def Precache(self):
        super(UnitBaseTF, self).Precache()

    def Spawn(self):
        self.Precache()
        
        super(UnitBaseTF, self).Spawn()
        
        self.skin = 0
        
        # This removes the hat and other crap.
        self.SetBodygroup(1, 1)
        self.SetBodygroup(2, 1)
            
        if isserver and self.hatmodels:
            self.hat = CreateEntityByName('hat')
            
            self.hat.SetModelName(self.hatmodels[random.randint(0,len(self.hatmodels)-1)])
            self.hat.SetOwnerEntity(self)
            self.hat.SetOwnerNumber(self.GetOwnerNumber())
            DispatchSpawn(self.hat)
            self.hat.Activate()
            self.hat.FollowEntity(self)
            
    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super(UnitBaseTF, self).UpdateOnRemove()
        
        if self.hat:
            if not self.hat.BecomeRagdollOnClient(vec3_origin):
                UTIL_Remove(self.hat)
            self.hat = None
            
    def Event_Killed(self, info):
        super(UnitBaseTF, self).Event_Killed(info)
        
        if self.hat:
            if not self.hat.BecomeRagdollOnClient(vec3_origin):
                UTIL_Remove(self.hat)
            self.hat = None
                
    hat = GenericField(value=None, networked=True)
    hatpaths = []
            
    @staticmethod    
    def InitEntityClass(cls):
        BaseClass.InitEntityClass(cls)
        
        cls.hatmodels = []
        for path in cls.hatpaths:
            modelnames = filesystem.ListDir(path, pathid='GAME', wildcard='*.mdl')
            modelnames += filesystem.ListDir(path, pathid='MOD', wildcard='*.mdl')
            for mn in modelnames:
                cls.hatmodels.append('%s/%s' % (path, mn))
        
    # Activity list
    activitylist = list( BaseClass.activitylist )
    activitylist.extend( [
        'ACT_MP_STAND_LOSERSTATE',
        'ACT_MP_RUN_LOSERSTATE',
        'ACT_MP_JUMP_START_LOSERSTATE',
    ] )
    
    # Animation translation table
    acttables = {
        'default' : {
            Activity.ACT_IDLE : 'ACT_MP_STAND_LOSERSTATE',
            Activity.ACT_RUN : 'ACT_MP_RUN_LOSERSTATE',
            Activity.ACT_MP_JUMP : 'ACT_MP_JUMP_START_LOSERSTATE',
        },
        'tf_weapon_melee' : {
            Activity.ACT_IDLE : Activity.ACT_MP_STAND_MELEE,
            Activity.ACT_RUN : Activity.ACT_MP_RUN_MELEE,
            Activity.ACT_MELEE_ATTACK1 : Activity.ACT_MP_ATTACK_STAND_MELEE,
            Activity.ACT_MP_JUMP : Activity.ACT_MP_JUMP_START_MELEE,
            Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_MP_JUMP_FLOAT_MELEE,
        },
        'tf_weapon_range' : {
            Activity.ACT_IDLE : Activity.ACT_MP_STAND_PRIMARY,
            Activity.ACT_RUN : Activity.ACT_MP_RUN_PRIMARY,
            Activity.ACT_MP_JUMP : Activity.ACT_MP_JUMP_START_PRIMARY,
            Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_MP_JUMP_FLOAT_PRIMARY,
        }
    }

    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=45.0,
        leganimtype=LegAnimType_t.LEGANIM_9WAY,
        useaimsequences=False,
        invertposeparameters=True,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super(UnitBaseTF.AnimStateClass, self).__init__(outer, animconfig)
            self.newjump = False
        
        def OnNewModel(self):
            super(UnitBaseTF.AnimStateClass, self).OnNewModel()
            
            # For some reason the default eye offset is completely wrong!?
            self.outer.SetViewOffset(Vector(0, 0, 64.0))

            self.movex = self.outer.LookupPoseParameter("move_x")
            self.movey = self.outer.LookupPoseParameter("move_y")
            
            self.bodyyaw = self.outer.LookupPoseParameter("body_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("body_pitch")
            
            