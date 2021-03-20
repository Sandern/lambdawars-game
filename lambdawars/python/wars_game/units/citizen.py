from srcbase import DMG_GENERIC
from vmath import Vector
from core.units import (UnitInfo, UnitBaseCombatHuman as BaseClass, EventHandlerAnimation, UnitBaseShared,
                        EventHandlerAnimationMisc)
from fields import UpgradeField, BooleanField, FloatField
from entities import entity, Activity
from unit_helper import UnitAnimConfig, LegAnimType_t
from gameinterface import CPASAttenuationFilter, modelinfo
from core.units.abilities import AbilityTransformUnit

if isserver:
    from entities import SpawnBlood

from particles import *

from vmath import *
import re

if isserver:
    from unit_helper import BaseAnimEventHandler, TossGrenadeAnimEventHandler
    from animation import Animevent

@entity('unit_citizen', networked=True)
class UnitCitizen(BaseClass):    
    """ Citizen """
    if isserver:
        def Precache(self):
            super().Precache() 
            
            self.PrecacheScriptSound("NPC_Citizen.FootstepLeft")
            self.PrecacheScriptSound("NPC_Citizen.FootstepRight")
            self.PrecacheScriptSound("NPC_Citizen.Die")
            self.PrecacheScriptSound('HealthKit.Touch')
            
            PrecacheParticleSystem('pg_partisan_revolution')
            #PrecacheParticleSystem('pg_heal')

            for s in self.abilitysounds_f.values():
                self.PrecacheScriptSound(s)
        
    def Spawn(self):
        super().Spawn() 
        
        self.animstate.usecombatstate = True
        
    def Event_Killed(self, info):
        super().Event_Killed(info)
        
        # Kill scrap, if carrying anything
        if self.carryingscrap:
            self.carryingscrap.AttachTo(None)
            self.carryingscrap.Event_Gibbed(info)
            self.carryingscrap = None
        
    def Heal(self, event=None):
        if not self.curorder or not self.curorder.ability:
            return
        target = self.curorder.target
        if not target:
            return
            
        if target.health == target.maxhealth:
            return
            
        if not self.curorder.ability.TakeEnergy(self):
            return
    
        timefullheal = 2.0
        timerecharge = 0.5
        #maximumhealamount = self.maxheal
        healamt = self.maxheal #(maximumhealamount * (1.0 - ( timefullheal - gpGlobals.curtime) / timerecharge))

        #print 'healamt: %f, energyregenrate: %f, maxenergy: %f' % (healamt, self.energyregenrate, self.maxenergy)
        
        #if healamt > maximumhealamount:
        #    healamt = maximumhealamount
        #else:
        healamt = int(round(healamt))
            
        filter = CPASAttenuationFilter(target, "HealthKit.Touch")
        self.EmitSoundFilter(filter, target.entindex(), "HealthKit.Touch")

        target.TakeHealth(healamt, DMG_GENERIC)
        target.RemoveAllDecals()
        
        #DispatchParticleEffect("pg_heal", PATTACH_ABSORIGIN_FOLLOW, target)
        target.DoAnimation(target.EFFECT_DOHEAL)
        
    def OnRevolutionaryFervorChanged(self):
        if self.revolutionaryfervoractive:
            if not self.revolutionaryfervorfx:
                self.revolutionaryfervorfx = self.ParticleProp().Create("pg_partisan_revolution", PATTACH_ABSORIGIN_FOLLOW)
                self.revolutionaryfervorfx.SetControlPoint(1, self.GetTeamColor())
                self.revolutionaryfervorfx.SetControlPoint(2, Vector(self.CollisionProp().BoundingRadius2D(), 1.0, 0.0))
        else:
            if self.revolutionaryfervorfx:
                self.ParticleProp().StopEmission(self.revolutionaryfervorfx, False, False, True)
                self.revolutionaryfervorfx = None
        
    @classmethod
    def PrecacheUnitType(cls, info):
        """ Precaches the unit type.
            This is only once in a level for unit type per entity class.
            It's called on both server and clients.
        """
        super().PrecacheUnitType(info)
        
        # Precache sounds (if any)
        if hasattr(info, 'sound_select_f'):
            cls.PrecacheScriptSound(info.sound_select_f)
        if hasattr(info, 'sound_move_f'):
            cls.PrecacheScriptSound(info.sound_move_f)
        if hasattr(info, 'sound_attack_f'):
            cls.PrecacheScriptSound(info.sound_attack_f)
        if hasattr(info, 'sound_death_f'):
            cls.PrecacheScriptSound(info.sound_death_f)
        
    if isclient:
        citizenmodelname = None
        citizenfmatcher = re.compile('models/Humans/.+/female_\d+.mdl')
        
        @property
        def isfemale(self):
            if not self.citizenmodelname:
                self.citizenmodelname = modelinfo.GetModelName(modelinfo.GetModel(self.GetModelIndex()))
            return bool(self.citizenfmatcher.match(self.citizenmodelname))
    
        def PlaySelectedSound(self):
            """ Plays selected soundscript using the setting from the info class. """
            soundscript = self.unitinfo.sound_select_f if self.isfemale else self.unitinfo.sound_select
            if not soundscript or self.order_sounds_disabled:
                return

            if UnitBaseShared.nextplayselectsound < gpGlobals.curtime:
                self.EmitAmbientSound(-1, self.GetAbsOrigin(), soundscript)
                UnitBaseShared.nextplayselectsound = gpGlobals.curtime + 6.0
        
        def MoveSound(self):
            self.PlayOrderSound(self.unitinfo.sound_move_f if self.isfemale else self.unitinfo.sound_move)
            
        def AttackSound(self):
            self.PlayOrderSound(self.unitinfo.sound_attack_f if self.isfemale else self.unitinfo.sound_attack)

        def DeathSound(self):
            self.PlayOrderSound(self.unitinfo.sound_death_f if self.isfemale else self.unitinfo.sound_death)
            
    def GetAbilitySound(self, soundscriptdesired):
        """ Translates soundscript symbol to desired soundscript.
            This is used in case different units should use a different soundscript. 
        """
        abilitysounds = self.abilitysounds_f if self.isfemale else self.abilitysounds
        return abilitysounds.get(soundscriptdesired, '')
            
    # Anim event handlers
    if isserver:
        def GrenadeInRangeLOSCheck(self, testpos, target=None):
            startpos = Vector()
            self.GetAttachment("anim_attachment_LH", startpos)
            targetpos = self.curorder.position
            
            handler = self.aetable[self.REBEL_AE_GREN_TOSS]
            
            tossvel = Vector()
            if not handler.GetTossVector(self, startpos, targetpos, self.CalculateIgnoreOwnerCollisionGroup(), tossvel):
                return False
                
            return True
            
        class RebelThrowGrenade(TossGrenadeAnimEventHandler):
            def HandleEvent(self, unit, event):
                throwability = unit.throwability
                if throwability:
                    throwability.ThrowObject(unit)
                    return
            
                abi = unit.grenadeability
                if not abi:
                    return
                    
                if abi.grenadeclsname:
                    self.SetGrenadeClass(abi.grenadeclsname)

                startpos = Vector()
                unit.GetAttachment("anim_attachment_LH", startpos)

                targetpos = abi.throwtarget.GetAbsOrigin() if abi.throwtarget else abi.throwtargetpos

                #UTIL_PredictedPosition(enemy, 0.5, targetpos) 

                grenade = self.TossGrenade(unit, startpos, targetpos, unit.CalculateIgnoreOwnerCollisionGroup())

                if grenade:
                    abi.OnGrenadeThrowed(unit, grenade)
                    grenade.SetVelocity(grenade.GetAbsVelocity(), Vector(0, 0, 0))
                    grenade.SetTimer( 2.5, 2.5 - grenade.FRAG_GRENADE_WARN_TIME ) #grenade detonation time (gtime)
                    
    revolutionaryfervoractive = BooleanField(value=False, networked=True, clientchangecallback='OnRevolutionaryFervorChanged')
    revolutionaryfervorfx = None
    insteadyposition = BooleanField(value=False, networked=True)

    maxheal = UpgradeField(value=50.0, abilityname='medic_healrate_upgrade') # TODO: Make this function more available

    REBEL_GRENADE_THROW_SPEED = 950
    
    throwability = None
    grenadeability = None
    carryingscrap = None


    # Ability sounds
    abilitysounds = {
        'attackmove': 'ability_reb_attackmove',
        'holdposition': 'ability_reb_holdposition',
    }
    abilitysounds_f = {
        'attackmove': 'ability_reb_attackmove_f',
        'holdposition': 'ability_reb_holdposition_f',
    }
    
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend([
        'ACT_CIT_HANDSUP',
        'ACT_CIT_BLINDED', # Blinded by scanner photo
        'ACT_CIT_SHOWARMBAND',
        'ACT_CIT_HEAL',
        'ACT_CIT_STARTLED', # Startled by sneaky scanner
        'ACT_RANGE_ATTACK_THROW',
        'ACT_WALK_AR2',
        'ACT_RUN_AR2',
        'ACT_IDLE_AR2_RELAXED',
        'ACT_NEUTRAL_AR2_RELAXED',
        'ACT_WALK_AIM_AR2_STIMULATED',
        'ACT_RUN_AIM_AR2_STIMULATED',
        'ACT_WALK_AIM_AR2',
        'ACT_IDLE_SMG1_RELAXED',
        'ACT_IDLE_SHOTGUN_RELAXED',
        'ACT_IDLE_AR2',
        'ACT_FLAMER_IDLE',
        'ACT_RELOAD_AR2',
    ])
    
    # Events
    events = dict(BaseClass.events)
    events.update({
        'ANIM_HEAL': EventHandlerAnimation('ACT_CIT_HEAL'),
        'ANIM_THROWGRENADE': EventHandlerAnimation('ACT_RANGE_ATTACK_THROW'),
        'ANIM_RELOAD_LOW': EventHandlerAnimationMisc('reloadact_low', onlywhenstill=True, miscplaybackrate=1.35),
    })
    
    REBEL_AE_GREN_TOSS = 3005

    if isserver:
        aetable = {
            'AE_CITIZEN_HEAL': Heal,
            REBEL_AE_GREN_TOSS: RebelThrowGrenade('grenade_frag', REBEL_GRENADE_THROW_SPEED),
            Animevent.AE_NPC_LEFTFOOT: BaseAnimEventHandler(),
        }
    
    # Activity translation table
    acttables = dict(BaseClass.acttables)
    acttables.update({
        'default': {
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_IDLE_ANGRY,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN,
        },
        'weapon_default': {
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
        },
        'weapon_hammer': {
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_IDLE_ANGRY,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN,
        },
        'weapon_smg1': {
            Activity.ACT_IDLE: 'ACT_IDLE_SMG1_RELAXED',
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
        },
        'weapon_shotgun': {
            Activity.ACT_IDLE: 'ACT_IDLE_SHOTGUN_RELAXED',
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
        },
        'weapon_tau': {
            Activity.ACT_IDLE: 'ACT_IDLE_SHOTGUN_RELAXED',
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
        },
        'weapon_ar2': {
            Activity.ACT_IDLE: 'ACT_IDLE_AR2_RELAXED',
            Activity.ACT_WALK: 'ACT_WALK_AR2',
            Activity.ACT_RUN: 'ACT_RUN_AR2',
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,

            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,

            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_WALK_AIM: 'ACT_WALK_AIM_AR2',
            Activity.ACT_RUN_AIM: 'ACT_RUN_AIM_AR2_STIMULATED',
        },
        'weapon_winchester1886': {
            Activity.ACT_IDLE: 'ACT_IDLE_AR2_RELAXED',
            Activity.ACT_WALK: 'ACT_WALK_AR2',
            Activity.ACT_RUN: 'ACT_RUN_AR2',
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,

            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,

            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_WALK_AIM: 'ACT_WALK_AIM_AR2',
            Activity.ACT_RUN_AIM: 'ACT_RUN_AIM_AR2_STIMULATED',
        },
        'weapon_rpg': {
            Activity.ACT_IDLE: Activity.ACT_IDLE_RPG,
            Activity.ACT_WALK: Activity.ACT_WALK_RPG,
            Activity.ACT_RUN: Activity.ACT_RUN_RPG,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_RPG,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_RPG,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_RPG,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_RPG,
            
            Activity.ACT_RELOAD: Activity.ACT_RELOAD_SMG1,
        },
        'wars_weapon_flamer': {
            Activity.ACT_IDLE: 'ACT_FLAMER_IDLE',
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
        },
        'weapon_rebel_heavy_gun': {
            Activity.ACT_IDLE: 'ACT_IDLE_AR2_RELAXED',
            Activity.ACT_WALK: 'ACT_WALK_AR2',
            Activity.ACT_RUN: 'ACT_RUN_AR2',
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,

            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,

            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_AR2,
            Activity.ACT_WALK_AIM: 'ACT_WALK_AIM_AR2',
            Activity.ACT_RUN_AIM: 'ACT_RUN_AIM_AR2_STIMULATED',
        },
        'weapon_crossbow': {
            Activity.ACT_IDLE: 'ACT_IDLE_SHOTGUN_RELAXED',
            Activity.ACT_WALK: Activity.ACT_WALK_RIFLE,
            Activity.ACT_RUN: Activity.ACT_RUN_RIFLE,
            Activity.ACT_RANGE_ATTACK1: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_MP_JUMP_START: Activity.ACT_JUMP,
            Activity.ACT_MP_JUMP_FLOAT: Activity.ACT_GLIDE,
            Activity.ACT_MP_JUMP_LAND: Activity.ACT_LAND,
            
            Activity.ACT_CROUCH: Activity.ACT_COVER_LOW,
            Activity.ACT_RUN_CROUCH: Activity.ACT_RUN_CROUCH_RIFLE,
            Activity.ACT_WALK_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_RUN_CROUCH_AIM: Activity.ACT_RUN_CROUCH_AIM_RIFLE,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED: Activity.ACT_RANGE_AIM_SMG1_LOW,
            
            Activity.ACT_IDLE_AIM_AGITATED: Activity.ACT_RANGE_ATTACK_SMG1,
            Activity.ACT_WALK_AIM: Activity.ACT_WALK_AIM_RIFLE,
            Activity.ACT_RUN_AIM: Activity.ACT_RUN_AIM_RIFLE,
            
            Activity.ACT_RELOAD: 'ACT_RELOAD_AR2',
            Activity.ACT_RELOAD_LOW: Activity.ACT_RELOAD_SMG1_LOW,
        },
    })
    
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=60.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )

    if isserver:
        def StartMeleeAttack(self, enemy):
            # Do melee damage
            self.MeleeAttack(self.unitinfo.AttackMelee.maxrange, self.unitinfo.AttackMelee.damage, QAngle(20.0, 0.0, -12.0), Vector(-250.0, 1.0, 1.0))

            return super().StartMeleeAttack(enemy)

    def MeleeAttack(self, distance, damage, viewpunch, shove):
        enthurt = self.CheckTraceHullAttack( distance, -Vector(16,16,32), Vector(16,16,32), damage, self.unitinfo.AttackMelee.damagetype, 5.0 )
        if enthurt != None:     # hitted something
            # Play a random attack hit sound
            #self.EmitSound("NPC_Antlion.MeleeAttack")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), enthurt.BloodColor(), damage)

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

    attackmelee1act = Activity.ACT_MELEE_ATTACK_SWING
    SCOUT_STAB_RANGE = 64.0
    STRIDER_STOMP_RANGE = 128.0

randomheads = [
    "male_01.mdl",
    "male_02.mdl",
    "female_01.mdl",
    "male_03.mdl",
    "female_02.mdl",
    "male_04.mdl",
    "female_03.mdl",
    "male_05.mdl",
    "female_04.mdl",
    "male_06.mdl",
    "female_06.mdl",
    "male_07.mdl",
    "female_07.mdl",
    "male_08.mdl",
    "male_09.mdl",
]

randomheads_scout = [
    "male_01.mdl",
    "female_01.mdl",
]

modellocs = {
    'DEFAULT': 'Group01',
    'DOWNTRODDEN': 'Group01',
    'REFUGEE': 'Group02',
    'REBEL': 'Group03',
    'MEDIC': 'Group03m',
    'COMBINE': 'Group01_combine',
    'SCOUT': 'scouts',
}

def GenerateModelList(type):
    modellist = []
    if type == 'SCOUT':
        for head in randomheads_scout:
            modellist.append( 'models/Humans/%s/%s' % (modellocs[type], head) )
        return modellist
    for head in randomheads:
        modellist.append( 'models/Humans/%s/%s' % (modellocs[type], head) )
    return modellist
    
# Register unit
class CitizenInfo(UnitInfo):
    name = 'unit_citizen'
    cls_name = 'unit_citizen'
    displayname = '#Citizen_Name'
    description = '#Citizen_Description'
    image_name = 'VGUI/rebels/units/unit_rebel_citizen.vmt'
    costs = [[('requisition', 5)], [('kills', 1)]]
    buildtime = 8.0
    health = 50
    maxspeed = 209.0
    attributes = ['light']
    modellist = GenerateModelList('DEFAULT')
    hulltype = 'HULL_HUMAN'
    #tier = 1
    abilities = {
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    viewdistance = 800
    scrapdropchance = 0.0
    cantakecover = False

    sound_select_f = ''
    sound_move_f = ''
    sound_attack_f = ''
    sound_death_f = ''

class Bullseye(CitizenInfo):
    name = 'unit_bullseye'
    health = 99999

class CombineCitizenInfo(CitizenInfo):
    name = 'unit_combine_citizen'
    displayname = '#CombCitizen_Name'
    description = '#CombCitizen_Description'
    image_name = 'VGUI/combine/units/unit_combine_citizen.vmt'
    attributes = ['light', 'shock']
    costs = [[('requisition', 5)], [('kills', 1)]]
    buildtime = 7.0
    health = 50
    modellist = GenerateModelList('COMBINE')
    viewdistance = 768
    maxspeed = 240
    sai_hint = set(['sai_unit_scout'])
    weapons = []
    sound_attack = "unit_combine_citizen_attack"
    sound_attack_f = "unit_combine_citizen_f_attack"
    sound_move = "unit_combine_citizen_move"
    sound_move_f = "unit_combine_citizen_f_move"
    sound_select = "unit_combine_citizen_select"
    sound_select_f = "unit_combine_citizen_f_select"
    sound_death = 'unit_rebel_death'
    sound_death_f = 'unit_rebel_f_death'

    class AttackMelee(CitizenInfo.AttackMelee):
        maxrange = 55.0
        damage = 4
        #damagetype = DMG_SLASH
        attackspeed = 2.0
    attacks = 'AttackMelee'

class MissionTransformToRebelSMG(AbilityTransformUnit):
    name = 'rebel_mission_transform_smg'
    displayname = '#CombTransMPSMG1_Name'
    description = '#CombTransMPSMG1_Name'
    transform_type = 'unit_rebel_partisan'
    replaceweapons = True
    image_name = 'vgui/combine/abilities/combine_transform_smg'
    activatesoundscript = 'ability_combine_smg1_upgrade'

class MissionCitizenInfo(CitizenInfo):
    name = 'unit_mission_citizen'
    image_name = 'VGUI/rebels/units/unit_rebel_citizen_mission.vmt'
    abilities = {
        5: 'rebel_mission_transform_smg',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    viewdistance = 900
    maxspeed = 217
    #scrapdropchance = 0.0

class BarricadeCitizenInfo(CitizenInfo):
    name = 'unit_citizen_barricade'
    health = 90
    costs = [[('requisition', 7)], [('kills', 1)]]
    buildtime = 3.0
    abilities = {
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_hammer']
    viewdistance = 900
    maxspeed = 217
    sai_hint = set(['sai_unit_builder', 'sai_unit_salvager', 'sai_unit_combat'])