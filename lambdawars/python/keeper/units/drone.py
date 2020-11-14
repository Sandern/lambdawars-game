from srcbase import DMG_SLASH, MASK_SOLID, COLLISION_GROUP_NONE
from vmath import Vector, QAngle
from .basekeeper import UnitBaseCreature as BaseClass, UnitKeeperInfo
from entities import entity, Activity
if isserver:
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from entities import SpawnBlood
    from utils import UTIL_TraceLine, UTIL_DecalTrace, trace_t
    
@entity('unit_drone', networked=True)
class UnitDrone(BaseClass):
    if isserver:
        def Precache(self):
            super(UnitDrone, self).Precache()
            
            self.PrecacheScriptSound( "ASW_Drone.Land" )
            self.PrecacheScriptSound( "ASW_Drone.Pain" )
            self.PrecacheScriptSound( "ASW_Drone.Alert" )
            self.PrecacheScriptSound( "ASW_Drone.Death" )
            self.PrecacheScriptSound( "ASW_Drone.Attack" )
            self.PrecacheScriptSound( "ASW_Drone.Swipe" )

            self.PrecacheScriptSound( "ASW_Drone.GibSplatHeavy" )
            self.PrecacheScriptSound( "ASW_Drone.GibSplat" )
            self.PrecacheScriptSound( "ASW_Drone.GibSplatQuiet" )
            self.PrecacheScriptSound( "ASW_Drone.DeathFireSizzle" )

            self.PrecacheModel( "models/aliens/drone/ragdoll_tail.mdl" )
            self.PrecacheModel( "models/aliens/drone/ragdoll_uparm.mdl" )
            self.PrecacheModel( "models/aliens/drone/ragdoll_uparm_r.mdl" )
            self.PrecacheModel( "models/aliens/drone/ragdoll_leg_r.mdl" )
            self.PrecacheModel( "models/aliens/drone/ragdoll_leg.mdl" )
            self.PrecacheModel( "models/aliens/drone/gib_torso.mdl" )
            
    def Event_Killed(self, info):
        tr = trace_t()
        UTIL_TraceLine(self.GetAbsOrigin() + Vector(0, 0, 16), self.GetAbsOrigin() - Vector( 0, 0, 64 ), MASK_SOLID, self, COLLISION_GROUP_NONE, tr)
        UTIL_DecalTrace(tr, "GreenBloodBig")
    
        super(UnitDrone, self).Event_Killed(info)
            
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        attackinfo = self.unitinfo.AttackMelee
        enthurt = self.CheckTraceHullAttack(distance, -Vector(16,16,32), Vector(16,16,32), damage, attackinfo.damagetype, 1.2, False)
        if enthurt:
            # Play a random attack hit sound
            #self.EmitSound("ASW_Drone.Attack")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), self.BloodColor(), damage)
        else:
            self.EmitSound("ASW_Drone.Swipe")
            
    # Anim event handlers
    def DroneAttack(self, event):
        attackinfo = self.unitinfo.AttackMelee
        self.MeleeAttack(attackinfo.maxrange, attackinfo.damage, QAngle( 20.0, 0.0, -12.0 ), Vector( -250.0, 1.0, 1.0 )) 
        #self.DoAnimation(self.ANIM_ENDSPECACT) # Drone attack animation keeps looping... end it here
        
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_DRONE_RUN_ATTACKING',
        'ACT_DRONE_WALLPOUND',
    ] )
    
    # Animation translation table
    acttables = {
        Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_GLIDE,
    }
    
    if isserver:
        # Anim events
        aetable = {
            'AE_DRONE_WALK_FOOTSTEP' : None,
            'AE_DRONE_FOOTSTEP_SOFT' : None,
            'AE_DRONE_FOOTSTEP_HEAVY' : None,
            'AE_DRONE_MELEE_HIT1' : DroneAttack,
            'AE_DRONE_MELEE_HIT2' : DroneAttack,
            'AE_DRONE_MELEE1_SOUND' : EmitSoundAnimEventHandler('ASW_Drone.Attack'),
            'AE_DRONE_MELEE2_SOUND' : EmitSoundAnimEventHandler('ASW_Drone.Attack'),
            'AE_DRONE_MOUTH_BLEED' : None,
            'AE_DRONE_ALERT_SOUND' : EmitSoundAnimEventHandler('ASW_Drone.Alert'),
            'AE_DRONE_SHADOW_ON' : None,
        }
    
    maxspeed = 180
    
class DroneInfo(UnitKeeperInfo):
    name = 'unit_drone'
    cls_name = 'unit_drone'
    hulltype = 'HULL_MEDIUM'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    costs = []
    health = 300
    viewdistance = 300
    displayname = 'Parasite'
    description = 'A parasite'
    modelname = 'models/aliens/drone/drone.mdl'
    sound_death = 'ASW_Drone.Death'
    attacks = 'AttackMelee'
    
    class AttackMelee(UnitKeeperInfo.AttackMelee):
        maxrange = 32.0
        damage = 15
        damagetype = DMG_SLASH
    attacks = 'AttackMelee'
    