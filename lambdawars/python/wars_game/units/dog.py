from srcbase import *
from vmath import Vector, QAngle, VectorNormalize, vec3_origin, RemapValClamped
from math import ceil
from entities import entity, Activity, D_LI
from core.units import (UnitInfo, UnitBaseCombatHuman as BaseClass, EventHandlerAnimation, EventHandlerSound,
                        EventHandlerMulti)
from unit_helper import UnitAnimConfig, LegAnimType_t
from wars_game.statuseffects import StunnedEffectInfo
from core.abilities import AbilityUpgrade, AbilityJump
import random
from wars_game.attributes import DogSlamImpactAttribute
from fields import SetField

from playermgr import relationships
from achievements import ACHIEVEMENT_WARS_DOGDOG
from gamerules import gamerules
from ..gamerules import AnnihilationInfo, DestroyHQInfo

if isserver:
    from playermgr import ListPlayersForOwnerNumber
    from particles import PrecacheParticleSystem, DispatchParticleEffect, PATTACH_POINT_FOLLOW
    from utils import UTIL_Remove, UTIL_EntitiesInBox, UTIL_ScreenShake, SHAKE_START
    from entities import CBeam, CSprite, SpawnBlood, CTakeDamageInfo, RadiusDamage
    from wars_game.achievements import IsCommonGameMode


@entity('unit_dog', networked=True)
class UnitDog(BaseClass):   
    def __init__(self):
        super().__init__()
        
        self.glowsprites = [None]*self.EFFECT_COUNT
        self.beams = [None]*self.EFFECT_COUNT

    if isserver:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem('pg_dog_slam')
            
            self.PrecacheScriptSound('NPC_dog.Idlemode_loop')
            self.PrecacheScriptSound('NPC_dog.Combatmode_loop')
            
            self.PrecacheScriptSound("unit_rebel_dog_angry")
            self.PrecacheScriptSound("unit_rebel_dog_slam")
        
            self.PrecacheScriptSound("Weapon_PhysCannon.Launch")
            self.PrecacheScriptSound("NPC_dog.Throw_Car")
            
            self.PrecacheScriptSound( "Zombie.AttackHit" )
            self.PrecacheScriptSound( "Zombie.AttackMiss" )

            self.PrecacheModel("sprites/orangelight1.vmt")
            self.PrecacheModel("sprites/physcannon_bluelight2.vmt")
            self.PrecacheModel("sprites/glow04_noz.vmt")

    def Spawn(self):
        super().Spawn()
        
        self.SetBloodColor(DONT_BLEED)
        
    def UnitThink(self):
        super().UnitThink()
        
        isincombat = self.enemy != None
        if isincombat != self.isincombat:
            if isincombat:
                self.StopSound('NPC_dog.Idlemode_loop')
                self.EmitSound('NPC_dog.Combatmode_loop')
            else:
                self.EmitSound('NPC_dog.Idlemode_loop')
                self.StopSound('NPC_dog.Combatmode_loop')
            self.isincombat = isincombat

    def StopSounds(self):
        self.StopSound('NPC_dog.Idlemode_loop')
        self.StopSound('NPC_dog.Combatmode_loop')

    if isserver:
        def Event_Killed(self, info):
            super().Event_Killed(info)

            self.StopSounds()
            
            if IsCommonGameMode():
                # Dog! Dog achievement
                # Figure out if we were killed by a player who does not like us
                # To those players award the achievement
                # Only in Annihilation and Destroy HQ modes
                attacker = info.GetAttacker()
                if attacker and gamerules.info.name in [AnnihilationInfo.name, DestroyHQInfo.name]:
                    owner = attacker.GetOwnerNumber()
                    if relationships[(owner, self.GetOwnerNumber())] != D_LI:
                        for player in ListPlayersForOwnerNumber(owner):
                            player.AwardAchievement(ACHIEVEMENT_WARS_DOGDOG)
                    
            
        def DoMeleeAttack1(self, event):
            # Do melee damage
            self.MeleeAttack(self.unitinfo.AttackMelee.maxrange, self.unitinfo.AttackMelee.damage, QAngle(20.0, 0.0, -12.0), Vector(-250.0, 1.0, 1.0)) 
    
        def OnTakeDamage_Alive(self, info):
            damage = super().OnTakeDamage_Alive(info)
            
            inflictor = info.GetInflictor()
            
            if inflictor:
                # Two special cases for Combine Elite alt fire ability and Rebel rpg
                entclsname = inflictor.GetClassname()
                if entclsname == 'prop_combine_ball' and random.random() < 0.2:
                    StunnedEffectInfo.CreateAndApply(self, attacker=inflictor, duration=1, forceall=True)
                
            return damage
    
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        enthurt = self.CheckTraceHullAttack( distance, -Vector(16,16,32), Vector(16,16,32), damage, self.unitinfo.AttackMelee.damagetype, 5.0 )
        if enthurt != None:     # hitted something
            # Play a random attack hit sound
            self.EmitSound("Zombie.AttackHit")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), enthurt.BloodColor(), damage)
        else:
            self.EmitSound("Zombie.AttackMiss")
            
    def ClearBeams(self):
        self.ClearSprites()
        
        # Turn off sprites
        for i in range(0, self.EFFECT_COUNT):
            if self.beams[i] != None:
                UTIL_Remove( self.beams[i] )
                self.beams[i] = None

    def ClearSprites(self):
        # Turn off sprites
        for i in range(0, self.EFFECT_COUNT):
            if self.glowsprites[i] != None:
                UTIL_Remove( self.glowsprites[i] )
                self.glowsprites[i] = None

    def CreateSprites(self):
        #Create the glow sprites
        for i in range(0, self.EFFECT_COUNT):
            if self.glowsprites[i]:
                continue

            attachNames = [
                "physgun",
                "thumb",
                "pinky",
                "index",
            ]

            self.glowsprites[i] = CSprite.SpriteCreate( "sprites/glow04_noz.vmt", self.GetAbsOrigin(), False )

            self.glowsprites[i].SetAttachment( self, self.LookupAttachment( attachNames[i] ) )
            self.glowsprites[i].SetTransparency( kRenderGlow, 255, 128, 0, 64, kRenderFxNoDissipation )
            self.glowsprites[i].SetBrightness( 255, 0.2 )
            self.glowsprites[i].SetScale( 0.55, 0.2 )

    def CreateBeams(self):
        if self.usebeameffects == False:
            self.ClearBeams()
            return

        self.CreateSprites()

        for i in range(0, self.EFFECT_COUNT):
            if self.beams[i]:
                continue

            attachNames = [
                "physgun",
                "thumb",
                "pinky",
                "index",
            ]

            self.beams[i] = CBeam.BeamCreate( "sprites/physcannon_bluelight2.vmt", 5.0 )

            self.beams[i].EntsInit( self.physicsent, self )
            self.beams[i].SetEndAttachment( self.LookupAttachment( attachNames[i] ) )
            self.beams[i].SetBrightness( 255 )
            self.beams[i].SetColor( 255, 255, 255 )
            self.beams[i].SetNoise( 5.5 )
            self.beams[i].SetRenderMode( kRenderTransAdd )
            
    def HandleGroundSlam(self, event):
        if not isserver:
            return
        self.DoSlam()
        
    def DoSlam(self, damage=180):
        origin = self.GetAbsOrigin()
         
        #eyesPoint = Vector()
        #eyesAngle = QAngle()
        #self.GetAttachment(self.LookupAttachment('eyes'), eyesPoint, eyesAngle)


        #DispatchParticleEffect('pg_dog_slam',offset , angle)
        DispatchParticleEffect('pg_dog_slam', PATTACH_POINT_FOLLOW, self, 'physgun')

        dmg_radius = 192.0
        self.EmitSound("unit_rebel_dog_slam")

        dmg_info = CTakeDamageInfo(self, self, vec3_origin, origin, 150, 0)
        dmg_info.attributes = {DogSlamImpactAttribute.name: DogSlamImpactAttribute(self)}

        RadiusDamage(dmg_info, origin, dmg_radius, CLASS_NONE, None)

        vec_radius = Vector(dmg_radius, dmg_radius, dmg_radius)
        enemies = UTIL_EntitiesInBox(32, origin-vec_radius, origin+vec_radius, FL_NPC)
        for e in enemies:
            if not self.IsValidEnemy(e):
                continue
                
            # Throw away
            dir = (e.GetAbsOrigin() - origin)
            dir[2] = 0.0
            dist = VectorNormalize(dir)

            falloff = RemapValClamped(dist, 0, dmg_radius*0.75, 1.0, 0.1)

            dir *= (dmg_radius * 1.5 * falloff)
            dir[2] += (dmg_radius * 0.5 * falloff)

            curvel = e.GetAbsVelocity().Length()
            if curvel < 1000.0:
                e.ApplyAbsVelocityImpulse(dir)
                
        UTIL_ScreenShake(origin, 8, 50, 1.0, dmg_radius, SHAKE_START, True)
    def RepairStep(self, intervalamount, repairhpps):
        if self.health >= self.maxhealth:
            return True
            
        # Cap speed at four or more workers
        n = len(self.constructors)
        if n > 1:
            intervalamount *= (1 + ((n - 1) ** 0.5)) / n
            
        self.health += int(ceil(intervalamount*repairhpps))
        self.health = min(self.health, self.maxhealth)
        if self.health >= self.maxhealth:
            self.OnHealed()
            return True
        return False  
    def OnHealed(self):pass
    def NeedsUnitConstructing(self, unit=None):
        return True
    repairable = True
    constructors = SetField(networked=True, save=False)
    constructability = 'repair_dog'
        
    #def HandleChargeImpact(self, vecImpact, hitentity):
    #    super().HandleChargeImpact(vecImpact, hitentity)
    #    
    #    print('hitentity: %s' % (hitentity))
            
    # Animation state
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=90.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def OnNewModel(self):
            super().OnNewModel()
            
            studiohdr = self.outer.GetModelPtr()
            
            self.bodyyaw = self.outer.LookupPoseParameter("body_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("aim_pitch")
            
            aimyaw = self.outer.LookupPoseParameter(studiohdr, "aim_yaw")
            if aimyaw < 0:
                return
            self.outer.SetPoseParameter(studiohdr, aimyaw, 0.0)
            
            headpitch = self.outer.LookupPoseParameter(studiohdr, "head_pitch")
            if headpitch < 0:
                return
            headyaw = self.outer.LookupPoseParameter(studiohdr, "head_yaw")
            if headyaw < 0:
                return
            headroll = self.outer.LookupPoseParameter(studiohdr, "head_roll")
            if headroll < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, headpitch, 0.0)
            self.outer.SetPoseParameter(studiohdr, headyaw, 0.0)
            self.outer.SetPoseParameter(studiohdr, headroll, 0.0)
            
            spineyaw = self.outer.LookupPoseParameter(studiohdr, "spine_yaw")
            if spineyaw < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, spineyaw, 0.0)
            
            necktrans = self.outer.LookupPoseParameter(studiohdr, "neck_trans")
            if necktrans < 0:
                return
                
            self.outer.SetPoseParameter(studiohdr, necktrans, 0.0)

            
            
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_DOG_THROW',
        'ACT_GROUND_SLAM1',
        'ACT_IDLE02',
        'ACT_FLY_POSE',
        'ACT_BEGIN_JUMP',
    ])
    
    # Activity translation table
    acttables = dict(BaseClass.acttables)
    acttables.update({ 
        'default' : {
            Activity.ACT_IDLE : 'ACT_IDLE02',
            Activity.ACT_MP_JUMP_FLOAT : 'ACT_FLY_POSE',
        }
    })
    
    # Events
    class EventHandlerDogJumpAnimation(EventHandlerAnimation):
        def __call__(self, unit, data):
            super().__call__(unit, data)
            
            # Temporary force air animation to avoid blending back to idle animation
            unit.animstate.forceairactendtime = gpGlobals.curtime + 1.0
    
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_SLAMGROUND': EventHandlerMulti(EventHandlerAnimation('ACT_GROUND_SLAM1'), EventHandlerSound('unit_rebel_dog_angry')),
        'AE_BEING_JUMP': EventHandlerDogJumpAnimation('ACT_BEGIN_JUMP'),
        'ANIM_STARTCHARGE': EventHandlerAnimation('ACT_BEGIN_JUMP'),
        'ANIM_STOPCHARGE': EventHandlerAnimation('ACT_GROUND_SLAM1'),
        'ANIM_CRASHCHARGE': EventHandlerAnimation('ACT_GROUND_SLAM1'),
    } )
    
    if isserver:
        # Anim events
        aetable = dict(BaseClass.aetable)
        aetable.update({
            'AE_GROUND_SLAM1': 'HandleGroundSlam',
            'AE_MELEE_ATTACK1': 'DoMeleeAttack1',
        })
            
    jumpheight = 150.0
    isincombat = None
    barsoffsetz = 32.0
    canshootmove = True
    
    #attackmelee1act = 'ACT_DOG_THROW'
    
    usebeameffects = False
    physicsent = None
    
    EFFECT_COUNT = 4
    
class AbilityDogJump(AbilityJump):
    name = 'dogjump'
    displayname = '#RebDogJump_Name'
    description = '#RebDogJump_Description'
    image_name = 'vgui/rebels/abilities/rebel_dog_jump'
    hidden = True
    rechargetime = 0
    maxrange = 896
    energy = 50
    jumpstartsound = 'unit_rebel_dog_angry'
    jumpgravity = 1.2
    collision = True
    
    def OnLanded(self, unit):
        super().OnLanded(unit)
        unit.DoSlam()

    sai_hint = AbilityJump.sai_hint | set(['sai_grenade'])
    
class DogInfo(UnitInfo):
    name = 'unit_dog'
    cls_name = 'unit_dog'
    displayname = '#Dog_Name'
    description = '#Dog_Description'
    image_name = 'vgui/rebels/units/unit_dog.vmt'
    health = 1400
    maxspeed = 334
    viewdistance = 832
    turnspeed = 75.0
    buildtime = 76.0
    population = 6
    unitenergy = 200
    unitenergy_initial = 50
    costs = [('requisition', 180), ('scrap', 180)]
    attributes = ['metal', 'large']
    modelname = 'models/dog_extended.mdl'
    hulltype = 'HULL_MEDIUM_TALL'
    sound_select = 'unit_rebel_dog_select'
    sound_move = 'unit_rebel_dog_move'
    sound_attack = 'unit_rebel_dog_attack'
    sound_death = "unit_rebel_dog_death"
    techrequirements = ['build_reb_techcenter']
    #tier = 3
    abilities = {
        0: 'slamground',
        1: 'dogjump',
        #2: 'dogcharge',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    class AttackMelee(UnitInfo.AttackMelee):
        damage = 80
        damagetype = DMG_SLASH
        attackspeed = 1.14
        maxrange = 90
    attacks = 'AttackMelee'
    sai_hint = set(['sai_unit_combat', 'sai_unit_super'])
	
class DestroyHQDogInfo(DogInfo):
    name = 'destroyhq_unit_dog'
    techrequirements = ['build_reb_munitiondepot_destroyhq', 'build_reb_vortigauntden_destroyhq']

class DogUnlock(AbilityUpgrade):
    name = 'dog_unlock'
    displayname = '#RebDogUnlock_Name'
    description = '#RebDogUnlock_Description'
    image_name = "vgui/rebels/abilities/rebel_dog_unlock"
    techrequirements = ['build_reb_junkyard']
    buildtime = 120.0
    costs = [[('requisition', 180), ('scrap', 180)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])

class OverrunDogInfo(DogInfo):
    #Dog is very tanky in overrun. Having him in overrun isn't half-bad for that purpose. Goal: need to make him be spawnable with a cooldown. Ability that spawns dog as an output with cooldown?
    name = 'overrun_unit_dog'
    health = 2000
    buildtime = 0
    rechargetime = 120
    unitenergy = 120
    costs = [('kills', 10)]
    hidden = True
    techrequirements = ['or_tier3_research']
    abilities = {
        0: 'slamground',
        1: 'dogjump',
        #2: 'dogcharge',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }