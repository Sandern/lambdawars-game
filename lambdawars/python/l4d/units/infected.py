from srcbase import DMG_SLASH, FL_FLY
from vmath import Vector, QAngle, AngleDiff, VectorAngles
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity, ACT_INVALID
import random
if isserver:
    from core.units import BaseAction
    from entities import SpawnBlood
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    
    from core.units.intention import BaseBehavior, BaseAction, CONTINUE
    from core.units import unitlist
    from entities import gEntList, D_HT
    import playermgr

@entity('unit_infected', networked=True)
class UnitInfected(BaseClass):
    """ Infected """
    def __init__(self):
        super(UnitInfected, self).__init__()
        self.maxclimbheight = 168.0
        
    def Precache(self):
        super(UnitInfected, self).Precache()
        
        self.PrecacheScriptSound('Zombie.Sleeping')
        self.PrecacheScriptSound('Zombie.Wander')
        self.PrecacheScriptSound('Zombie.BecomeAlert')
        self.PrecacheScriptSound('Zombie.Alert')
        self.PrecacheScriptSound('Zombie.BecomeEnraged')
        self.PrecacheScriptSound('Zombie.Rage')
        self.PrecacheScriptSound('Zombie.RageAtVictim')
        self.PrecacheScriptSound('Zombie.Shoved')
        self.PrecacheScriptSound('Zombie.Shot')
        self.PrecacheScriptSound('Zombie.Die')
        self.PrecacheScriptSound('Zombie.IgniteScream')
        self.PrecacheScriptSound('Zombie.HeadlessCough')
        self.PrecacheScriptSound('Zombie.AttackMiss')
        self.PrecacheScriptSound('Zombie.BulletImpact')
        self.PrecacheScriptSound('Zombie.ClawScrape')
        self.PrecacheScriptSound('Zombie.Punch')
        self.PrecacheScriptSound('MegaMobIncoming')
        
    def Spawn(self):
        self.Precache()

        super(UnitInfected, self).Spawn()
        
        self.locomotion.acceleration = 8.5
        self.locomotion.worldfriction = 3.25
        self.locomotion.stopspeed = 85.0
        self.locomotion.airacceleration = 10.0
        
        if isserver:
            self.skin = random.randint(0, 31)
            self.SetBodygroup(self.BG_HEAD, random.randint(0, 3))
            self.SetBodygroup(self.BD_UPPERBODY, random.randint(0, 7))
            
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        attackinfo = self.unitinfo.AttackMelee
        enthurt = self.CheckTraceHullAttack(distance, -Vector(16,16,32), Vector(16,16,32), damage, attackinfo.damagetype, 1.2)
        if enthurt:
            # Play a random attack hit sound
            self.EmitSound("Zombie.Punch")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), self.BloodColor(), damage)
        else:
            self.EmitSound("Zombie.AttackMiss")
            
    # Anim event handlers
    def InfectedPunch(self, event):
        attackinfo = self.unitinfo.AttackMelee
        self.MeleeAttack(attackinfo.maxrange, attackinfo.damage, QAngle( 20.0, 0.0, -12.0 ), Vector( -250.0, 1.0, 1.0 )) 
        
    def EventHandlerClimbFromStand(self, data):
        if data in self.climbheights:
            act = 'ACT_TERROR_CLIMB_%d_FROM_STAND' % (data)
            self.animstate.specificmainactivity = Activity(self.LookupActivity(act))
            self.animstate.RestartMainSequence()
        else:
            print("invalid climb height")
                    
    # Body groups
    BG_HEAD = 0
    BD_UPPERBODY = 1
    BG_LOWERBODY = 2
        
    # Vars
    maxspeed = 270.0
    yawspeed = 40.0
    jumpheight = 40.0
    
    # Activity list
    activitylist = list( BaseClass.activitylist )
    activitylist.extend( [
        'ACT_TERROR_IDLE_NEUTRAL',
        'ACT_TERROR_IDLE_ALERT',
        'ACT_TERROR_WALK_NEUTRAL',
        'ACT_TERROR_RUN_INTENSE',
        'ACT_TERROR_ATTACK',
        'ACT_TERROR_JUMP',
        'ACT_TERROR_JUMP_OVER_GAP',
        'ACT_TERROR_FALL',
        'ACT_TERROR_JUMP_LANDING',
        'ACT_TERROR_JUMP_LANDING_HARD',
    ] )
    
    # Climb from stand activities
    climbheights = [24, 36, 48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168]
    for height in climbheights:
        activitylist.append('ACT_TERROR_CLIMB_%d_FROM_STAND' % (height))
        
    if isserver:
        # Anim events
        aetable = {
            'AE_ATTACK_HIT' : InfectedPunch,
            'AE_FOOTSTEP_RIGHT' : BaseAnimEventHandler(), #EmitSoundAnimEventHandler('Zombie.FootstepLeft'),
            'AE_FOOTSTEP_LEFT' : BaseAnimEventHandler(), #EmitSoundAnimEventHandler('Zombie.FootstepRight'),
        }
        
    # Animation translation table
    acttables = {
        Activity.ACT_IDLE : 'ACT_TERROR_IDLE_ALERT',
        Activity.ACT_RUN : 'ACT_TERROR_RUN_INTENSE',
        Activity.ACT_MELEE_ATTACK1 : 'ACT_TERROR_ATTACK',
        Activity.ACT_MP_JUMP : 'ACT_TERROR_JUMP',
        Activity.ACT_MP_JUMP_FLOAT : 'ACT_TERROR_FALL',
    }
    
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=180.0,
        leganimtype=LegAnimType_t.LEGANIM_9WAY,
        invertposeparameters=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super(UnitInfected.AnimStateClass, self).__init__(outer, animconfig)
            self.newjump = False
        
        def OnNewModel(self):
            super(UnitInfected.AnimStateClass, self).OnNewModel()

            self.movex = self.outer.LookupPoseParameter("move_x")
            self.movey = self.outer.LookupPoseParameter("move_y")
            
            self.bodyyaw = self.outer.LookupPoseParameter("body_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("body_pitch")
            
            self.leanyaw = self.outer.LookupPoseParameter("lean_yaw")
            self.leanpitch = self.outer.LookupPoseParameter("lean_pitch")
            if self.leanyaw >= 0:
                self.outer.SetPoseParameter(self.leanyaw, 0.0)
            if self.leanpitch >= 0:
                self.outer.SetPoseParameter(self.leanpitch, 0.0)
            
    # Events
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_INFECTED_CLIMB_FROM_STAND' : EventHandlerClimbFromStand,
    } )
    
    # Infected AI
    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionIdle(BaseClass.BehaviorGenericClass.ActionIdle):
                nextwandersound = 0.0
                def Update(self):
                    # Make annoying sounds
                    if self.nextwandersound < gpGlobals.curtime:
                        self.outer.EmitSound('Zombie.Wander')
                        self.nextwandersound = gpGlobals.curtime + 8.0
                    return super(UnitInfected.BehaviorGenericClass.ActionIdle, self).Update()
                    
                def OnStartClimb(self, climbheight, direction):
                    return self.ChangeTo(self.behavior.ActionStartClimbing, 'Starting climbing', 
                        climbheight, direction)

            class ActionStartClimbing(BaseAction):
                def Init(self, climbheight, direction):
                    self.climbheight = climbheight
                    self.direction = direction
                    
                def OnStart(self):
                    angles = QAngle()
                    VectorAngles(self.direction, angles)
                    if AngleDiff(angles.y, self.outer.GetAbsAngles().y) > self.tolerance:
                        return self.SuspendFor(self.behavior.ActionFaceYaw, 'Not facing climb direction', angles.y)
                    return self.StartClimbing()
                    
                def OnResume(self):
                    # Should be facing now, might want to recheck?
                    return self.StartClimbing()
                    
                def StartClimbing(self):
                    try:
                        selectedclimbheight = filter(lambda x: x >= self.climbheight, self.outer.climbheights)[0]
                    except IndexError:
                        return self.ChangeTo(self.behavior.ActionIdle, 'Returning to idle, unexpected height %f' % (self.climbheight))
                    self.outer.DoAnimation(self.outer.ANIM_INFECTED_CLIMB_FROM_STAND, selectedclimbheight)
                    return self.ChangeTo(self.behavior.ActionClimb, 'Climbing..', 
                            activity=self.outer.animstate.specificmainactivity, transitionaction=self.behavior.ActionIdle)
                            
                tolerance = 5.0
                    
            class ActionClimb(BaseClass.BehaviorGenericClass.ActionWaitForActivityTransitionAutoMovement):
                def OnStart(self):
                    self.outer.AddFlag(FL_FLY)
                    self.outer.locomotionenabled = False
                    return super(UnitInfected.BehaviorGenericClass.ActionClimb, self).OnStart()
                def OnEnd(self):
                    self.outer.RemoveFlag(FL_FLY)
                    self.outer.locomotionenabled = True
                    return super(UnitInfected.BehaviorGenericClass.ActionClimb, self).OnEnd()
                    
class UnitInfectedInfo(UnitInfo):
    name = "unit_infected"
    cls_name = "unit_infected"
    displayname = "#L4D_Infected_Name"
    description = "#L4D_Infected_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/infected/common_male01.mdl'
    #modelname = 'models/infected/common_male_dressshirt_jeans.mdl'
    hulltype = 'HULL_HUMAN'
    health = 100
    attributes = ['light', 'slash']
    
    sound_select = 'Zombie.Wander'
    sound_move = 'Zombie.Alert'
    sound_death = 'Zombie.Die'
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitInfo.AttackMelee):
        maxrange = 32.0
        damage = 40
        damagetype = DMG_SLASH
        attackspeed = 1.6
    attacks = 'AttackMelee'
    