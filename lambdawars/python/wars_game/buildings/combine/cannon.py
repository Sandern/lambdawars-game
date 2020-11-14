from srcbase import MASK_SHOT, COLLISION_GROUP_NONE, MAX_TRACE_LENGTH
from vmath import Vector, QAngle, AngleVectors, VectorNormalize, DotProduct, vec3_angle
from core.buildings import UnitBaseAutoTurret, WarsTurretInfo
from particles import DispatchParticleEffect
from utils import trace_t, UTIL_TraceLine
from entities import FireBulletsInfo_t, entity
import random

if isserver:
    from entities import CBeam
    from particles import PrecacheParticleSystem
    from utils import UTIL_Remove
    
@entity('build_combinecannon', networked=True)
class CombineCannon(UnitBaseAutoTurret):
    def Precache(self):
        if isserver:
            PrecacheParticleSystem( "Weapon_Combine_Ion_Cannon" )
        
        super().Precache()
        
    def Spawn(self):
        super().Spawn()

        if isserver:
            self.timebeamon = gpGlobals.curtime
            self.CreateBeam()

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

    s_pUpdateBeamThinkContext = "UpdateBeamThinkContext"
    COMBINE_CANNON_BEAM = "effects/blueblacklargebeam.vmt"
    
    beam = None     

# Register unit
class CombineCannonInfo(WarsTurretInfo):
    name        = "build_combinecannon"                            # unit_create name
    cls_name    = "build_combinecannon"                            # This entity is spawned and can be retrieved in the unit instance by GetUnitType()
    image_name  = "vgui/abilities/ability_rebelhq.vmt"      # Displayed in unit panel
    health      = 1000
    buildtime = 5.0
    modelname = 'models/combine_turrets/combine_cannon_gun.mdl'
    
    class AttackTurret(WarsTurretInfo.AttackTurret):
        damage = 150
        attackspeed = 1.0
    attacks = 'AttackTurret'
    