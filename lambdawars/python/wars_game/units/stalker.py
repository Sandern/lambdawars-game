from srcbase import MASK_WATER, MASK_SHOT, COLLISION_GROUP_NONE, DMG_SHOCK, kRenderGlow, kRenderFxNoDissipation
from vmath import Vector, VectorNormalize, DotProduct, vec3_origin
from core.units import UnitInfo, UnitBaseCombatHuman as BaseClass
from core.abilities import SubMenu
from entities import entity, Activity
from unit_helper import UnitAnimConfig, LegAnimType_t
from animation import Animevent
import random
from playermgr import dbplayers

if isserver:
    from entities import CBeam, CSprite, ClearMultiDamage, CalculateMeleeDamageForce, ApplyMultiDamage, CTakeDamageInfo
    from utils import UTIL_TraceLine, trace_t, UTIL_Bubbles, UTIL_DecalTrace, UTIL_PointContents, UTIL_Smoke, UTIL_Remove, CTraceFilterSkipFriendly
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    from gameinterface import CPASAttenuationFilter
    from math import atan, sin

g_StalkerBeamThinkTime = 0.025

@entity('unit_stalker', networked=True)
class UnitStalker(BaseClass):    
    """ Combine Stalker. Hard worker. """
    def __init__(self):
        super().__init__()

        self.laserdir = Vector()
        self.lasertargetpos = Vector()
        
    def Precache(self): 
        self.PrecacheModel("sprites/laser.vmt")

        self.PrecacheModel("sprites/redglow1.vmt")
        self.PrecacheModel("sprites/orangeglow1.vmt")
        self.PrecacheModel("sprites/yellowglow1.vmt")

        self.PrecacheScriptSound("NPC_Stalker.BurnFlesh")
        self.PrecacheScriptSound("NPC_Stalker.BurnWall")
        self.PrecacheScriptSound("NPC_Stalker.FootstepLeft")
        self.PrecacheScriptSound("NPC_Stalker.FootstepRight")
        self.PrecacheScriptSound("NPC_Stalker.Hit")
        self.PrecacheScriptSound("NPC_Stalker.Ambient01")
        self.PrecacheScriptSound("NPC_Stalker.Scream")
        self.PrecacheScriptSound("NPC_Stalker.Pain")
        self.PrecacheScriptSound("NPC_Stalker.Die")
        self.PrecacheScriptSound("unit_stalker_death")
    
        super().Precache()

    if isserver:
        def UpdateOnRemove(self):
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
            self.KillAttackBeam()
        
        def Event_Killed(self, info):
            self.KillAttackBeam()
            super().Event_Killed(info)
            
        def StartRangeAttack(self, enemy):
            if not self.beam:
                self.StartAttackBeam(enemy)
            else:
                self.beamtarget = enemy
            return False
        
        def LaserThink(self):
            self.DrawAttackBeam(min(0.1, gpGlobals.curtime - self.GetLastThink('LaserThink')))
            
            if self.lasertimeout and self.lasertimeout < gpGlobals.curtime:
                self.KillAttackBeam()
                return
            
            self.SetNextThink(gpGlobals.curtime + 0.1, 'LaserThink')
        
        def DoSmokeEffect(self, position):
            if gpGlobals.curtime > self.nextsmoketime:
                self.nextsmoketime = gpGlobals.curtime + 0.5
                UTIL_Smoke(position, random.randint(5, 10), 10)

        def LaserStartPosition(self, stalkerpos):
            """ Returns position of laser for any given position of the staler """
            # Get attachment position
            vAttachPos = Vector()
            self.GetAttachment(self.STALKER_LASER_ATTACHMENT,vAttachPos)

            # Now convert to stalkerpos
            vAttachPos = vAttachPos - self.GetAbsOrigin() + stalkerpos
            return vAttachPos
            
        def UpdateAttackBeam(self, target):
            self.beamtarget = target
            if not self.beam:
                return
            
            self.lasertimeout = gpGlobals.curtime + 1.0
            
            # If not burning at a target 
            if target:
                # Recompute laser dir
                self.laserdir = target.BodyTarget(self.EyePosition()) - self.LaserStartPosition(self.GetAbsOrigin())
            
                # Note: original code aims for the head, but seems to miss a bit too much.
                self.lasertargetpos = target.BodyTarget(self.EyePosition()) 

                # ---------------------------------------------
                #	Get beam end point
                # ---------------------------------------------
                vecSrc = self.LaserStartPosition(self.GetAbsOrigin())
                targetDir = self.lasertargetpos - vecSrc
                VectorNormalize(targetDir)
                
                # --------------------------------------------------------
                #	If beam position and laser dir are way off, end attack
                # --------------------------------------------------------
                if DotProduct(targetDir,self.laserdir) < 0.5:
                    self.KillAttackBeam()
                    return

                filter = CTraceFilterSkipFriendly(self, COLLISION_GROUP_NONE, self)
                tr = trace_t()
                UTIL_TraceLine( vecSrc, vecSrc + self.laserdir * self.MAX_STALKER_FIRE_RANGE, MASK_SHOT, filter, tr)
                # ---------------------------------------------
                #  If beam not long enough, stop attacking
                # ---------------------------------------------
                if tr.fraction == 1.0:
                    #self.KillAttackBeam()
                    return

                # If we don't have a beam, create one
                #if not self.beam:
                #    self.StartAttackBeam(target)

        def CalcBeamPosition(self):
            """ Calculate position of beam """
            targetDir = self.lasertargetpos - self.LaserStartPosition(self.GetAbsOrigin())
            VectorNormalize(targetDir)

            # ---------------------------------------
            #  Otherwise if burning towards an enemy
            # ---------------------------------------
            if self.beamtarget:
                # ---------------------------------------
                #  Integrate towards target position
                # ---------------------------------------
                iRate = 0.99

                #if self.beamtarget.Classify() == CLASS_BULLSEYE:
                #    # Seek bullseyes faster
                #    iRate = 0.8

                self.laserdir.x = (iRate * self.laserdir.x + (1-iRate) * targetDir.x)
                self.laserdir.y = (iRate * self.laserdir.y + (1-iRate) * targetDir.y)
                self.laserdir.z = (iRate * self.laserdir.z + (1-iRate) * targetDir.z)
                VectorNormalize(self.laserdir)

                # -----------------------------------------
                # Add time-coherent noise to the position
                # Must be scaled with distance 
                # -----------------------------------------
                fTargetDist = (self.GetAbsOrigin() - self.lasertargetpos).Length()
                noiseScale = atan(0.2/fTargetDist) if fTargetDist != 0 else 1.0

                self.laserdir.x += 5*noiseScale*sin(self.noisemodx * gpGlobals.curtime + self.noisemodx)
                self.laserdir.y += 5*noiseScale*sin(self.noisemody * gpGlobals.curtime + self.noisemody)
                self.laserdir.z += 5*noiseScale*sin(self.noisemodz * gpGlobals.curtime + self.noisemodz)
                
        noisemodx = 5
        noisemody = 5
        noisemodz = 5
        
        def GetLaserDirAndDist(self, target):
            origin = self.GetAbsOrigin()
            if target.IsUnit():
                laserdir = target.BodyTarget(self.EyePosition()) - self.LaserStartPosition(origin)
            else:
                laserdir = target.WorldSpaceCenter() - self.LaserStartPosition(origin)
            laserdist = VectorNormalize(laserdir)
            return laserdir, laserdist

        def StartAttackBeam(self, target):
            if not target:
                return
            origin = self.GetAbsOrigin()
            self.lasertimeout = gpGlobals.curtime + 1.0
            self.beamtarget = target
            self.laserdir, lasterdist = self.GetLaserDirAndDist(target)
            
            # If I don't have a beam yet, create one
            if not self.beam:
                vecSrc = self.LaserStartPosition(self.GetAbsOrigin())
                #filter = CTraceFilterSkipFriendly(self, COLLISION_GROUP_NONE, self)
                tr = trace_t()
                UTIL_TraceLine (vecSrc, vecSrc + self.laserdir * self.MAX_STALKER_FIRE_RANGE, MASK_SHOT, self, self.CalculateIgnoreOwnerCollisionGroup(), tr)
                #if tr.fraction >= 1.0:
                    # too far
                    #self.KillAttackBeam()
                #    return

                self.beam = CBeam.BeamCreate("sprites/laser.vmt", 2.0)
                self.beam.PointEntInit(tr.endpos, self)
                self.beam.SetEndAttachment(self.STALKER_LASER_ATTACHMENT)  
                self.beam.SetBrightness(255)
                self.beam.SetNoise(0)
                self.beam.AddFOWFlags(self.GetFOWFlags())

                color = dbplayers[self.GetOwnerNumber()].color
                if self.beampower is self.STALKER_BEAM_LOW:
                    #self.beam.SetColor( 255, 0, 0 )
                    self.beam.SetColor(color.r(), color.g(), color.b())
                    self.lightglow = CSprite.SpriteCreate( "sprites/redglow1.vmt", origin, False )
                elif self.beampower is self.STALKER_BEAM_MED:
                    #self.beam.SetColor( 255, 50, 0 )
                    self.beam.SetColor(color.r(), color.g(), color.b())
                    self.lightglow = CSprite.SpriteCreate( "sprites/orangeglow1.vmt", origin, False )
                elif self.beampower is self.STALKER_BEAM_HIGH:
                    #self.beam.SetColor( 255, 150, 0 )
                    self.beam.SetColor(color.r(), color.g(), color.b())
                    self.lightglow = CSprite.SpriteCreate( "sprites/yellowglow1.vmt", origin, False )

                # ----------------------------
                # Light myself in a red glow
                # ----------------------------
                #self.lightglow.SetTransparency(kRenderGlow, 255, 200, 200, 0, kRenderFxNoDissipation)
                self.lightglow.SetTransparency(kRenderGlow, color.r(), color.g(), color.b(), 0, kRenderFxNoDissipation)
                self.lightglow.SetAttachment(self, 1)
                self.lightglow.SetBrightness(255)
                self.lightglow.SetScale(0.65)
                self.lightglow.AddFOWFlags(self.GetFOWFlags())
                
            self.SetThink(self.LaserThink, gpGlobals.curtime + g_StalkerBeamThinkTime, "LaserThink")
            self.beamendtime = gpGlobals.curtime + self.STALKER_LASER_DURATION
    
        def DrawAttackBeam(self, interval):
            """ Draw attack beam and do damage / decals 
                NOTE: Not very efficient to call in python frequently, but most of the time
                      we only got a few stalkers."""
            if not self.beam or not self.beamtarget:
                return

            origin = self.GetAbsOrigin()
                
            # Recompute laser dir
            self.laserdir, lasterdist = self.GetLaserDirAndDist(self.beamtarget)
            
            # ---------------------------------------------
            #	Get beam end point
            # ---------------------------------------------
            vecSrc = self.LaserStartPosition(origin)
            tr = trace_t()
            UTIL_TraceLine(vecSrc, vecSrc + self.laserdir * self.MAX_STALKER_FIRE_RANGE, MASK_SHOT, self, self.CalculateIgnoreOwnerCollisionGroup(), tr)

            self.CalcBeamPosition()

            
            bInWater = True if (UTIL_PointContents (tr.endpos, MASK_WATER) & MASK_WATER) else False
            # ---------------------------------------------
            #	Update the beam position
            # ---------------------------------------------
            self.beam.SetStartPos(tr.endpos)
            #self.beam.RelinkBeam() # <--- PERFORMANCE KILLER

            vAttachPos = Vector()
            self.GetAttachment(self.STALKER_LASER_ATTACHMENT,vAttachPos)

            vecAimDir = tr.endpos - vAttachPos
            VectorNormalize(vecAimDir)
            
            
            # --------------------------------------------
            #  Play burn sounds
            # --------------------------------------------
            pBCC = tr.ent
            if pBCC and (pBCC.IsUnit() or pBCC.IsPlayer()):
                if gpGlobals.curtime > self.nextdamagetime:
                    ClearMultiDamage()

                    attackinfo = self.unitinfo.AttackRange
                    damage = attackinfo.damage * interval
                    #if self.beampower is self.STALKER_BEAM_LOW:
                    #    damage = 0.1 * attackinfo.damage
                    #elif self.beampower is STALKER_BEAM_MED:
                    #    damage = 0.3 * attackinfo.damage
                    #elif self.beampower is STALKER_BEAM_HIGH:
                    #    damage = attackinfo.damage

                    info = CTakeDamageInfo( self, self, damage, attackinfo.damagetype )
                    CalculateMeleeDamageForce( info, self.laserdir, tr.endpos )
                    pBCC.DispatchTraceAttack( info, self.laserdir, tr )
                    ApplyMultiDamage()
                    self.nextdamagetime = gpGlobals.curtime + 0.1

                    # NOTE: Beam might have been destroyed due dispatching events (when the enemy dies)
                    if not self.beam:
                        return
                    
                #if pBCC.Classify() != CLASS_BULLSEYE:
                if not self.playinghitflesh:
                    filter = CPASAttenuationFilter(self.beam,"NPC_Stalker.BurnFlesh")
                    filter.MakeReliable()

                    self.EmitSoundFilter(filter, self.beam.entindex(),"NPC_Stalker.BurnFlesh")
                    self.playinghitflesh = True
                if self.playinghitwall:
                    self.StopSoundStatic(self.beam.entindex(), "NPC_Stalker.BurnWall")
                    self.playinghitwall = False

                tr.endpos.z -= 24.0
                if not bInWater:
                    self.DoSmokeEffect(tr.endpos + tr.plane.normal * 8)
            
            if not pBCC:# or pBCC.Classify() == CLASS_BULLSEYE:
                if not self.playinghitwall:
                    filter = CPASAttenuationFilter(self.beam, "NPC_Stalker.BurnWall")
                    filter.MakeReliable()

                    self.EmitSoundFilter(filter, self.beam.entindex(), "NPC_Stalker.BurnWall")
                    self.playinghitwall = True
                if self.playinghitflesh:
                    self.StopSoundStatic(self.beam.entindex(), "NPC_Stalker.BurnFlesh" )
                    self.playinghitflesh = False

                UTIL_DecalTrace(tr, "RedGlowFade")
                UTIL_DecalTrace(tr, "FadingScorch")
                
                tr.endpos.z -= 24.0
                if not bInWater:
                    self.DoSmokeEffect(tr.endpos + tr.plane.normal * 8)

            if bInWater:
                UTIL_Bubbles(tr.endpos-Vector(3,3,3),tr.endpos+Vector(3,3,3),10)

            #CBroadcastRecipientFilter filter
            #TE_DynamicLight( filter, 0.0, EyePosition(), 255, 0, 0, 5, 0.2, 0 )
            
        def KillAttackBeam(self):
            """ Kill our beam """
            if not self.beam:
                return
                
            self.beamtarget = None
            self.lasertimeout = None

            # Kill sound
            self.StopSoundStatic(self.beam.entindex(), "NPC_Stalker.BurnWall" )
            self.StopSoundStatic(self.beam.entindex(), "NPC_Stalker.BurnFlesh" )

            UTIL_Remove(self.lightglow)
            UTIL_Remove(self.beam)
            self.beam = None
            self.playinghitwall = False
            self.playinghitflesh = False

            self.SetThink( None, gpGlobals.curtime, "LaserThink" )

            # Beam has to recharge
            self.beamrechargetime = gpGlobals.curtime + self.STALKER_LASER_RECHARGE

    # Stalker AI
    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionAttack(BaseClass.BehaviorGenericClass.ActionAttack):
                def Update(self):
                    self.outer.UpdateAttackBeam(self.enemy)
                    return super().Update()
                    
                def OnEnd(self):
                    self.outer.KillAttackBeam()
                    return super().OnEnd()

            class ActionOrderAttack(BaseClass.BehaviorGenericClass.ActionOrderAttack):
                def Update(self):
                    self.outer.UpdateAttackBeam(self.enemy)
                    return super().Update()

                def OnEnd(self):
                    self.outer.KillAttackBeam()
                    return super().OnEnd()

            class ActionAttackNoMovement(BaseClass.BehaviorGenericClass.ActionAttackNoMovement):
                def Update(self):
                    self.outer.UpdateAttackBeam(self.enemy)
                    return super().Update()

                def OnEnd(self):
                    self.outer.KillAttackBeam()
                    return super().OnEnd()
                    
            class ActionConstruct(BaseClass.BehaviorGenericClass.ActionConstruct):
                def Update(self):
                    if self.outer.constructing:
                        self.outer.StartAttackBeam(self.order.target)
                        self.outer.UpdateAttackBeam(self.order.target)
                    else:
                        self.outer.KillAttackBeam()
                    return super().Update()
                    
                def OnEnd(self):
                    self.outer.KillAttackBeam()
                    return super().OnEnd()
                    
            class ActionRepair(BaseClass.BehaviorGenericClass.ActionRepair):
                def Update(self):
                    if self.outer.constructing:
                        self.outer.StartAttackBeam(self.order.target)
                        self.outer.UpdateAttackBeam(self.order.target)
                    else:
                        self.outer.KillAttackBeam()
                    return super().Update()
                    
                def OnEnd(self):
                    self.outer.KillAttackBeam()
                    return super().OnEnd()

    # Ability sounds
    abilitysounds = {
        'attackmove' : 'ability_comb_stalker_attackmove',
        'holdposition' : 'ability_comb_stalker_holdposition',
    }
    
    # Settings
    STALKER_BEAM_LOW = 0
    STALKER_BEAM_MED = 1
    STALKER_BEAM_HIGH = 2
    
    MIN_STALKER_FIRE_RANGE = 64
    MAX_STALKER_FIRE_RANGE = 1024
    STALKER_LASER_ATTACHMENT = 1
    STALKER_LASER_DURATION = 99999
    STALKER_LASER_RECHARGE = 1
    STALKER_PLAYER_AGGRESSION = 1

    constructactivity = Activity.ACT_INVALID #'ACT_STALKER_WORK'
    constructmaxrange = 320.0
    
    # Vars
    beam = None
    beampower = 0
    lightglow = None
    beamendtime = 0.0
    nextdamagetime = 0.0
    playinghitflesh = False
    playinghitwall = False
    nextsmoketime = 0.0
    lasertimeout = None
    
    # Activity translation table
    acttables = {
		Activity.ACT_RUN : Activity.ACT_WALK,
		Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_IDLE,
    }
    
    if isserver:
        # Animation events
        STALKER_AE_MELEE_HIT = 1
        aetable = {
            Animevent.AE_NPC_LEFTFOOT : EmitSoundAnimEventHandler('NPC_Stalker.FootstepLeft'),
            Animevent.AE_NPC_RIGHTFOOT : EmitSoundAnimEventHandler('"NPC_Stalker.FootstepRight'),
        }
    
    # Animation
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=60.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super(UnitStalker.AnimStateClass, self).__init__(outer, animconfig)
            self.newjump = False

class StalkerShared(UnitInfo):
    cls_name = 'unit_stalker'
    displayname = '#CombStalker_Name'
    description = '#CombStalker_Description'
    image_name = 'vgui/combine/units/unit_stalker.vmt'
    portrait = 'resource/portraits/combineStalker.bik'
    costs = [[('requisition', 20)], [('kills', 1)]]
    #tier = 1
    resource_category = 'economy'
    buildtime = 12.0
    health = 150
    maxspeed = 96.0
    viewdistance = 896
    attributes = ['light', 'burn']
    engagedistance = 500.0
    accuracy = 'low'
    sound_select = 'unit_stalker_select'
    sound_move = 'unit_stalker_move'
    sound_attack = 'unit_stalker_attack'
    sound_death = 'unit_stalker_death'
    modelname = 'models/stalker.mdl'
    hulltype = 'HULL_HUMAN'
    attackpriority = -1
    sai_hint = set(['sai_unit_builder'])
    
    class AttackRange(UnitInfo.AttackRange):
        damage = 10
        damagetype = DMG_SHOCK
        attackspeed = 0.0
        maxrange = 768.0
        # Can't move head or body, so need to be facing the target correctly.
        cone = 0.9986295347546 # DOT_3DEGREE
    attacks = 'AttackRange'
    
class StalkerInfo(StalkerShared):
    name = 'unit_stalker'
    scrapdropchance = 0.0
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
        3: SubMenu(name='stalker_defensemenu',
                     displayname='#CombDefenseMenu_Name', description='#CombDefenseMenu_Description',  image_name = 'vgui/abilities/building_defence_menu.vmt', 
                     abilities={
            0: 'build_comb_barricade',
            1: 'comb_mountableturret',
            2: 'build_comb_mortar',
            3: 'build_comb_headcrabcanisterlauncher',
            4: 'build_comb_shieldgen',
            5: 'build_comb_bunker',
            11: 'menuup',
        }),
        7: SubMenu(name='stalker_menu',
                     displayname='#CombMenu_Name', description='#CombMenu_Description',  image_name = 'vgui/abilities/building_menu.vmt', 
                     abilities={
            0: 'build_comb_hq',
            1: 'build_comb_powergenerator',
            #2: 'build_comb_factory',
            2: 'build_comb_energycell',
            #2: 'build_comb_powergenerator_scrap',
            3: 'build_comb_garrison',
            4: 'build_comb_regenerationpost',
            5: 'build_comb_armory',
            6: 'build_comb_synthfactory',
            7: 'build_comb_specialops',
            8: 'build_comb_powergenerator_scrap',
            9: 'build_comb_mech_factory',
            10: 'build_comb_tech_center',

            11: 'menuup',
        } ),
    }
    
class StalkerOverrunInfo(StalkerShared):
    name = 'overrun_unit_stalker'
    hidden = True
    tier = 0
    buildtime = 0
    abilities = {
        2: 'overrun_build_comb_regenerationpost',
        3: 'overrun_build_comb_shieldgen',
        4: 'overrun_build_comb_barricade',
        5: 'overrun_comb_mountableturret',
        6: 'overrun_build_comb_bunker',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
    }
