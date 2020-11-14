from srcbase import DMG_SLASH
from vmath import Vector, QAngle
from .basekeeper import UnitBaseCreature as BaseClass, UnitKeeperInfo
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity
import random
if isserver:
    from utils import UTIL_SetSize, UTIL_Remove
    from entities import SpawnBlood, CreateEntityByName, DispatchSpawn
    from animation import AE_MELEE_DAMAGE
    from particles import PrecacheParticleSystem
    
@entity('unit_dk_marine', networked=True)
class UnitMarine(BaseClass):
    if isserver:
        def Precache(self):
            super(UnitMarine, self).Precache()
            
            self.PrecacheModel("models/swarm/shouldercone/shouldercone.mdl")
            self.PrecacheModel("models/swarm/shouldercone/lasersight.mdl")	
            self.PrecacheModel( "cable/cable.vmt" )
            self.PrecacheScriptSound( "ASW.MarineMeleeAttack" )
            self.PrecacheScriptSound( "ASW.MarineMeleeAttackFP" )
            self.PrecacheScriptSound( "ASW.MarinePowerFistAttack" )
            self.PrecacheScriptSound( "ASW.MarinePowerFistAttackFP" )
            self.PrecacheScriptSound( "ASW_Weapon_Flamer.FlameLoop" )
            self.PrecacheScriptSound( "ASW_Weapon_Flamer.FlameStop" )	
            self.PrecacheScriptSound( "ASWFlashlight.FlashlightToggle" )
            self.PrecacheScriptSound( "ASW_Flare.IgniteFlare" )
            self.PrecacheScriptSound( "ASWScanner.Idle1" )
            self.PrecacheScriptSound( "ASWScanner.Idle2" )
            self.PrecacheScriptSound( "ASWScanner.Idle3" )
            self.PrecacheScriptSound( "ASWScanner.Idle4" )
            self.PrecacheScriptSound( "ASWScanner.Idle5" )
            self.PrecacheScriptSound( "ASWScanner.Idle6" )
            self.PrecacheScriptSound( "ASWScanner.Idle7" )
            self.PrecacheScriptSound( "ASWScanner.Idle8" )
            self.PrecacheScriptSound( "ASWScanner.Idle9" )
            self.PrecacheScriptSound( "ASWScanner.Idle10" )
            self.PrecacheScriptSound( "ASWScanner.Idle11" )
            self.PrecacheScriptSound( "ASWScanner.Idle12" )
            self.PrecacheScriptSound( "ASWScanner.Idle13" )
            self.PrecacheScriptSound( "ASWScanner.Warning1" )
            self.PrecacheScriptSound( "ASWScanner.Warning2" )
            self.PrecacheScriptSound( "ASWScanner.Warning3" )
            self.PrecacheScriptSound( "ASWScanner.Warning4" )
            self.PrecacheScriptSound( "ASWScanner.Warning5" )
            self.PrecacheScriptSound( "ASWScanner.Warning6" )
            self.PrecacheScriptSound( "ASWScanner.Warning7" )
            self.PrecacheScriptSound( "ASWScanner.Warning8" )
            self.PrecacheScriptSound( "ASWScanner.Warning9" )
            self.PrecacheScriptSound( "ASWScanner.Drawing" )
            self.PrecacheScriptSound( "ASW_Weapon.Reload3" )
            self.PrecacheScriptSound( "ASWInterface.Button3" )	
            self.PrecacheScriptSound( "Marine.DeathBeep" )
            self.PrecacheScriptSound( "ASW.MarineImpactFP" )
            self.PrecacheScriptSound( "ASW.MarineImpact" )
            self.PrecacheScriptSound( "ASW.MarineImpactHeavyFP" )
            self.PrecacheScriptSound( "ASW.MarineImpactHeavy" )
            self.PrecacheScriptSound( "ASW.MarineMeleeAttack" )
            self.PrecacheScriptSound( "ASW_Weapon.LowAmmoClick" )	
            self.PrecacheScriptSound( "ASW_ElectrifiedSuit.TurnOn" )
            self.PrecacheScriptSound( "ASW_ElectrifiedSuit.Loop" )
            self.PrecacheScriptSound( "ASW_ElectrifiedSuit.LoopFP" )
            self.PrecacheScriptSound( "ASW_ElectrifiedSuit.OffFP" )
            self.PrecacheScriptSound( "ASW.MarineBurnPain_NoIgnite" )
            self.PrecacheScriptSound( "ASW_Extinguisher.OnLoop" )
            self.PrecacheScriptSound( "ASW_Extinguisher.Stop" )
            self.PrecacheScriptSound( "ASW_JumpJet.Activate" )
            self.PrecacheScriptSound( "ASW_JumpJet.Loop" )
            self.PrecacheScriptSound( "ASW_JumpJet.Impact" )
            self.PrecacheScriptSound( "ASW_Blink.Blink" )
            self.PrecacheScriptSound( "ASW_Blink.Teleport" )
            self.PrecacheScriptSound( "ASW_XP.LevelUp" )

            self.PrecacheScriptSound( "ASW_Weapon.InvalidDestination" )
            PrecacheParticleSystem( "smallsplat" )						# shot
            PrecacheParticleSystem( "marine_bloodsplat_light" )		# small shot
            PrecacheParticleSystem( "marine_bloodsplat_heavy" )		# heavy shot
            PrecacheParticleSystem( "marine_hit_blood_ff" )
            PrecacheParticleSystem( "marine_hit_blood" )
            PrecacheParticleSystem( "thorns_marine_buff" )
            PrecacheParticleSystem( "marine_gib" )
            PrecacheParticleSystem( "marine_death_ragdoll" )
            PrecacheParticleSystem( "piercing_spark" )
            PrecacheParticleSystem( "jj_trail_small" )
            PrecacheParticleSystem( "jj_ground_pound" )
            PrecacheParticleSystem( "invalid_destination" )
            PrecacheParticleSystem( "Blink" )
        
    def Spawn(self):
        super(UnitMarine, self).Spawn()
        
        if isserver:
            UTIL_SetSize(self, Vector(-13,-13,   0), Vector(13, 13, 72))
            
            self.skin = random.randint(0, 4)
            
    def DropGold(self, origin):
        # Drop gold
        gold = CreateEntityByName('dk_gold')
        gold.SetAbsOrigin(origin)
        gold.SetAbsAngles(QAngle(0, random.uniform(0,360), 0))
        DispatchSpawn(gold)
        gold.Activate()
        
    def Event_Killed(self, info):
        for i in range(0, random.randint(0,3)):
            self.DropGold(self.GetAbsOrigin())
        super(UnitMarine, self).Event_Killed(info)
            
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        attackinfo = self.unitinfo.AttackMelee
        enthurt = self.CheckTraceHullAttack(distance, -Vector(16,16,32), Vector(16,16,32), damage, attackinfo.damagetype, 1.2, False)
        if enthurt:
            # Play a random attack hit sound
            self.EmitSound("ASW.MarineMeleeAttack")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), self.BloodColor(), damage)
        else:
            pass #self.EmitSound("")
            
    # Anim event handlers
    def MarineAttack(self, event):
        attackinfo = self.unitinfo.AttackMelee
        self.MeleeAttack(attackinfo.maxrange, attackinfo.damage, QAngle( 20.0, 0.0, -12.0 ), Vector( -250.0, 1.0, 1.0 )) 
        
            
    # Vars
    maxspeed = 170.0
    yawspeed = 40.0
    jumpheight = 40.0 
    
    ishero = True
    candigblocks = True
    canexecutetasks = True
    
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
    
    if isserver:
        # Anim events
        aetable = {
            AE_MELEE_DAMAGE : MarineAttack,
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
class UnitMarineInfo(UnitKeeperInfo):
    name = "unit_dk_marine"
    cls_name = "unit_dk_marine"
    displayname = "#ASW_Marine_Name"
    description = "#ASW_Marine_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/swarm/marine/marine.mdl'
    health = 100
    viewdistance = 400
    #weapons = ['asw_weapon_rifle']
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitKeeperInfo.AttackMelee):
        maxrange = 32.0
        damage = 10
        damagetype = DMG_SLASH
    attacks = 'AttackMelee'
    