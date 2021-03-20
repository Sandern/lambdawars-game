from srcbase import MASK_SHOT, COLLISION_GROUP_NONE, MAX_TRACE_LENGTH
from vmath import Vector, QAngle, AngleVectors, VectorNormalize, DotProduct, vec3_angle
from core.buildings import UnitBaseAutoTurret, WarsTurretInfo, CreateDummy
from particles import DispatchParticleEffect
from utils import trace_t, UTIL_TraceLine
from entities import FireBulletsInfo_t, entity, DENSITY_NONE, DENSITY_GAUSSIANECLIPSE
from .basepowered import PoweredBuildingInfo
from fields import StringField
from core.abilities import AbilityAsAttack, AttackAbilityAsAttack
from core.units import CoverSpot
import random

if isserver:
    from entities import CBeam
    from particles import PrecacheParticleSystem
    from utils import UTIL_Remove
    
@entity('build_combinecannon', networked=True)
class CombineCannon(UnitBaseAutoTurret):
    def __init__(self):
        super(CombineCannon, self).__init__()
        
        self.SetEnterOffset(Vector(-64, 0, 0))
    def Precache(self):
        if isserver:
            PrecacheParticleSystem( "Weapon_Combine_Ion_Cannon" )
        
        super().Precache()
        
    def Spawn(self):
        super().Spawn()

        if isserver:
            self.timebeamon = gpGlobals.curtime
            self.CreateBeam()
        self.SetCanBeSeen(True)
    def UpdateOnRemove(self):
        if isserver:
            self.DestroyBeam()
        super().UpdateOnRemove()

    def CreateBeam(self):
        if not self.beam and gpGlobals.curtime >= self.timebeamon:
            self.beam = CBeam.BeamCreate( self.COMBINE_CANNON_BEAM, 1.0 )
            self.beam.SetColor( 255, 255, 255 )
            self.SetThink( self.UpdateBeamThink, gpGlobals.curtime, self.s_pUpdateBeamThinkContext )
        else:
            # Beam seems to be on, or I'm not supposed to have it on at the moment.
            return

        vecInitialAim = Vector()

        AngleVectors( QAngle(self.aimpitch, self.aimyaw, 0.0), vecInitialAim, None, None )

        self.beam.PointsInit( self.WorldBarrelPosition(), self.WorldBarrelPosition() + vecInitialAim )
        self.beam.SetBrightness( 255 )
        self.beam.SetNoise( 0 )
        self.beam.SetWidth( 3.0 )
        self.beam.SetEndWidth( 0 )
        self.beam.SetScrollRate( 0 )
        self.beam.SetFadeLength( 60 ) # five feet to fade out
        #self.beam.SetHaloTexture( sHaloSprite )
        self.beam.SetHaloScale( 4.0 )
    
    def DestroyBeam(self):
        if self.beam:
            UTIL_Remove( self.beam )
            self.beam = None
            
    COMBINE_CANNON_BEAM_MAX_DIST = 1900.0
    def UpdateBeamThink(self):
        self.SetThink( self.UpdateBeamThink, gpGlobals.curtime + 0.025, self.s_pUpdateBeamThinkContext )

        # Always try to create the beam.
        self.CreateBeam()
        
        if not self.beam:
            return

        trBeam = trace_t()
        #trShot = trace_t()
        #trBlockLOS = trace_t()

        vecBarrel = self.WorldBarrelPosition()
        vecAim = Vector()
        AngleVectors( QAngle(self.aimpitch, self.aimyaw, 0.0), vecAim, None, None )

        UTIL_TraceLine( vecBarrel, vecBarrel + vecAim * self.COMBINE_CANNON_BEAM_MAX_DIST, MASK_SHOT, self, COLLISION_GROUP_NONE, trBeam )

        self.beam.SetStartPos( trBeam.startpos )
        self.beam.SetEndPos( trBeam.endpos )
        self.beam.AddFOWFlags(self.GetFOWFlags())
        
        
        #if( !(m_spawnflags & SF_TANK_AIM_AT_POS) )
        #    SetTargetPosition( trBeam.endpos )
        
    def GetTracerType(self): return "HelicopterTracer"
    
    def MakeTracer(self, vecTracerSrc, tr, iTracerType):
        # NOTE: Ignore vecTracerSrc. It gets set to Vector(999, 999, 999) in MP
        # If the shot passed near the player, shake the screen.
        # if( AI_IsSinglePlayer() )
        
            # Vector vecPlayer = AI_GetSinglePlayer().EyePosition()

            # Vector vecNearestPoint = PointOnLineNearestPoint( vecTracerSrc, tr.endpos, vecPlayer )

            # float flDist = vecPlayer.DistTo( vecNearestPoint )

            # if( flDist >= 10.0f && flDist <= 120.0f )
            
                # # Don't shake the screen if we're hit (within 10 inches), but do shake if a shot otherwise comes within 10 feet.
                # UTIL_ScreenShake( vecNearestPoint, 10, 60, 0.3, 120.0f, SHAKE_START, False )

        # Send the railgun effect
        DispatchParticleEffect( "Weapon_Combine_Ion_Cannon", self.WorldBarrelPosition(), tr.endpos, vec3_angle, None )
            
    def Fire(self, bulletcount, attacker=None, ingorespread=False):
        forward = Vector()
        angles = QAngle(self.aimpitch, self.aimyaw, 0.0)
        AngleVectors(angles, forward)
    
        vecAdjustedForward = Vector(forward)
        
        barrelend = self.WorldBarrelPosition()
        
        attackinfo = self.unitinfo.AttackTurret

        if self.enemy != None:
            vecToTarget = self.enemy.BodyTarget( barrelend, False ) - barrelend
            VectorNormalize( vecToTarget )

            flDot = DotProduct( vecToTarget, forward )

            if flDot >= 0.97:
                vecAdjustedForward = vecToTarget
                
            if self.enemy.IsNPC():
                self.lasttargetwasnpc = True
            else:
                self.lasttargetwasnpc = False

            #if( self.enemy.IsPlayer() )
            #    m_OnShotAtPlayer.FireOutput( this, this )
        
        info = FireBulletsInfo_t()
        info.shots = 1
        info.vecsrc = barrelend
        info.vecdirshooting = forward
        info.vecspread = Vector( 0, 0, 0 )

        info.distance = MAX_TRACE_LENGTH
        info.tracerfreq = 1
        info.damage = attackinfo.damage
        info.playerdamage = attackinfo.damage
        info.attacker = attacker
        #info.additionalignoreent = self.GetParent()          
        if self.ammotypeidx != -1:
            for i in range(0, bulletcount):
                info.ammotype = self.ammotypeidx
                super().FireBullets( info )

        self.DoMuzzleFlash()

        # Play the cannon sound
        self.EmitSound(self.firesound)
    
        # Turn off the beam and tell it to stay off for a bit. We want it to look like the beam became the
        # ion cannon 'rail gun' effect.
        self.DestroyBeam()
        self.timebeamon = gpGlobals.curtime + 0.2

        self.timenextsweep = gpGlobals.curtime + random.randint( 1.0, 2.0 )

    aimtype = UnitBaseAutoTurret.AIMTYPE_POSE
    barrelattachmentname = 'muzzle'
    ammotype = 'CombineHeavyCannon'
    firesound = "NPC_Combine_Cannon.FireBullet"
    #idleact = 'ACT_FLOOR_TURRET_OPEN_IDLE'
    #fireact = 'ACT_FLOOR_TURRET_FIRE'
    blockdensitytype = DENSITY_NONE
    customeyeoffset = Vector(0,0,24)

    s_pUpdateBeamThinkContext = "UpdateBeamThinkContext"
    COMBINE_CANNON_BEAM = "effects/blueblacklargebeam.vmt"
    
    beam = None     
    autoconstruct = False

# Register unit
class CombineCannonInfo(WarsTurretInfo):
    name = "build_combine_cannon"
    cls_name = "build_combinecannon"
    displayname = '#BuildCombLaserTur_Name'
    description = '#BuildCombLaserTur_Description'
    image_name  = 'vgui/combine/buildings/build_comb_cannon.vmt'
    image_dis_name = 'vgui/combine/buildings/build_comb_cannon_dis.vmt'
    health = 300
    attributes = ['building', 'pulse', 'fire']
    buildtime = 50.0
    viewdistance = 1024
    sensedistance = 1280
    costs = [('requisition', 75), ('power', 25)]
    techrequirements = ['build_comb_tech_center']
    modelname = 'models/combine_turrets/combine_cannon_gun.mdl'
    selectionpriority = 1
    zoffset = 32.0
    sound_death = 'build_comb_mturret_explode'
    
    class AttackTurret(WarsTurretInfo.AttackTurret):
        damage = 120
        maxrange = 1152
        attackspeed = 0.8
        cone = 0.99862953475 
    attacks = 'AttackTurret'
    abilities = {
        8: 'cancel',
    }
    dummies = [
        CreateDummy(
            offset=Vector(0, 0, -2),
            modelname = 'models/props_combine/combine_barricade_short01a.mdl',
            blocknavareas = False,
            blockdensitytype = DENSITY_GAUSSIANECLIPSE,
        ),
    ]
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos)
        inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        inst.SetControlPoint(2, Vector(1216, 0, 0))
        forward = Vector()
        AngleVectors(self.targetangle, forward)
        inst.SetControlPoint(3, targetpos + forward * 32.0)
        
    infoparticles = ['cone_of_fire']
    cover_spots = [
        CoverSpot(offset=Vector(-40, -24, 0)),
        CoverSpot(offset=Vector(-40, 24, 0)),
    ]