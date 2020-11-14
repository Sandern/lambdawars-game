from srcbase import *
from vmath import Vector, QAngle, anglemod, ApproachAngle, AngleDiff, VectorAngles, AngleVectors, DotProduct, VectorNormalize
from .base import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from entities import networked, FireBulletsInfo_t, Activity
from gamerules import GetAmmoDef
import ndebugoverlay
from core.units import UnitBaseAnimState
if isserver:
    from core.units import UnitCombatSense
else:
    from entities import DataUpdateType_t
    
class WarsTurretInfo(WarsBuildingInfo):
    attackpriority = 0
    sensedistance = 1024.0
    ispriobuilding = False # Not important for game modes logic
    
    attributes = ['building', 'bullet']
    resource_category = 'defense'
    
    # Target ability setting
    targetatgroundonly = False
    requirerotation = True
    requirenavmesh = False
    
    class AttackTurret(WarsBuildingInfo.AttackRange):
        cone = 0.99862953475 # 3 degrees
        damage = 12
        attackspeed = 1.0
        maxrange = 1024.0
    attacks = 'AttackTurret'
    
class TurretFallBackInfo(WarsTurretInfo):
    name = 'turret_unknown'
    displayname = 'Unknown Turret'
    attributes = []
    hidden = True
    
class UnitBaseTurretAnimState(UnitBaseAnimState):
    def Update(self, eyeyaw, eyepitch):
        outer = self.outer
        enemy = outer.enemy
        
        # GetAnimTimeInterval returns gpGlobals.frametime on client, and interval between main think (non context) on server
        interval = self.GetAnimTimeInterval()

        # NOTE: If you update pose parameters, then always update them.
        #       Otherwise the interpolation will mess them up.
        if enemy:
            dir = enemy.WorldSpaceCenter() - outer.WorldBarrelPosition()
            VectorNormalize(dir)
            outer.UpdateAim(dir, interval)
        else:
            dir = Vector()
            AngleVectors(QAngle(outer.aimpitch, outer.aimyaw, 0.0), dir)
            outer.UpdateAim(dir, interval)

@networked
class UnitBaseTurret(BaseClass):
    def __init__(self):
        super().__init__()

        if isserver:
            self.UseClientSideAnimation()
            
            self.senses = UnitCombatSense(self)
            self.senses.testlos = True
            
            if self.aimtype == self.AIMTYPE_POSE:
                self.senses.SetUseLimitedViewCone(True)
                self.senses.SetViewCone(0.500000001) # DOT_60DEGREE
                
        self.animstate = self.CreateAnimState()
        
    def CreateAnimState(self):
        return UnitBaseTurretAnimState(self)
                
    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()

        self.senses = None
        self.animstate = None
                
    def Precache(self):
        super().Precache()
        
        if self.firesound:
            self.PrecacheScriptSound(self.firesound)
            
    def Spawn(self):
        super().Spawn()

        self.ammotypeidx = GetAmmoDef().Index(self.ammotype)
        self.SetBlocksLOS(False)
        
        if isserver:
            angles = self.GetAbsAngles()
            self.aimpitch = angles.x
            self.aimyaw = angles.y

    def WorldBarrelPosition(self):
        """ Barrel position """
        if self.barrelattachment == 0:
            return self.WorldSpaceCenter()

        vecOrigin = self.WorldSpaceCenter()
        vecAngles = QAngle()
        self.GetAttachment(self.barrelattachment, vecOrigin, vecAngles)
        return vecOrigin
            
    def UpdateAim(self, aimdir, time):
        angles = self.GetAbsAngles()
        
        angdir = QAngle()
        VectorAngles(aimdir, angdir)
        
        # Approach ideal
        self.aimpitch = ApproachAngle(angdir.x, self.aimpitch, self.pitchturnspeed*time)
        self.aimyaw = ApproachAngle(angdir.y, self.aimyaw, self.yawturnspeed*time)
        
        # In case of abs and pose type, set angles or pose parameters + clamp
        if self.aimtype == self.AIMTYPE_POSE:
            # Set new pose parameters
            self.SetPoseParameter(self.aimposepitch, AngleDiff(self.aimpitch, angles.x))
            self.SetPoseParameter(self.aimposeyaw, AngleDiff(self.aimyaw, angles.y))
            
            # Clamp within specified or pose limits 
            if self.aimpitch_limitlo == 0 and self.aimpitch_limithi == 0:
                self.aimpitch = anglemod(angles.x + self.GetPoseParameter(self.aimposepitch))
            else:
                self.aimpitch = max(self.aimpitch_limitlo, min(self.aimpitch_limithi, self.aimpitch))
                
            if self.aimyaw_limitlo == 0 and self.aimyaw_limithi == 0:
                self.aimyaw = anglemod(angles.y + self.GetPoseParameter(self.aimposeyaw))
            else:
                self.aimyaw = max(self.aimyaw_limitlo, min(self.aimyaw_limithi, self.aimyaw))
                
        elif self.aimtype == self.AIMTYPE_ABS:
            self.SetAbsAngles( QAngle(self.aimpitch, self.aimyaw, 0.0) )

    def OnNewModel(self):
        super().OnNewModel()
        
        angles = self.GetAbsAngles()
        self.aimpitch = angles.x
        self.aimyaw = angles.y

        if self.barrelattachmentname:
            self.barrelattachment = self.LookupAttachment(self.barrelattachmentname)
        
        self.aimposepitch = self.LookupPoseParameter('aim_pitch')
        self.aimposeyaw = self.LookupPoseParameter('aim_yaw')
        
        if self.aimposepitch != -1:
            self.SetPoseParameter(self.aimposepitch, 0.0)
            success, self.posepitchmin, self.posepitchmax = self.GetPoseParameterRange(self.aimposepitch)
        if self.aimposeyaw != -1:
            self.SetPoseParameter(self.aimposeyaw, 0.0)
            success, self.poseyawmin, self.poseyawmax = self.GetPoseParameterRange(self.aimposeyaw)
            
        if self.idleact:
            self.idleact = Activity(self.LookupActivity(self.idleact))
        if self.fireact:
            self.fireact = Activity(self.LookupActivity(self.fireact))
            
        if self.idleact:
            self.SetSequence( self.SelectWeightedSequence(self.idleact) )

        if isclient:
            self.ResetLatched()
            
    def OnDataChanged(self, type):
        super().OnDataChanged(type)
        
        if type == DataUpdateType_t.DATA_UPDATE_CREATED:
            angles = self.GetAbsAngles()
            self.aimpitch = angles.x
            self.aimyaw = angles.y
            
    def InTurretAimCone(self, spot, mindot):
        if type(spot) != Vector:
            spot = spot.BodyTarget(self.WorldBarrelPosition(), False) - self.WorldBarrelPosition()
            spot.z = 0.0
            VectorNormalize(spot)

        forward = Vector()
        angles = QAngle(0.0, self.aimyaw, 0.0)
        AngleVectors(angles, forward)
        
        dot = DotProduct(spot, forward)

        if dot > mindot:
            return True
        return False

    def FireTurret(self, data):
        #self.ResetEventsParity() # reset event parity so the animation events will occur on the weapon. 
        #self.DoAnimationEvents( self.GetModelPtr() )
        if isclient:
            self.Fire(1, self)
            if self.fireact:
                self.SetSequence(self.SelectWeightedSequence(self.fireact))
            if self.muzzleoptions:
                self.DispatchMuzzleEffect(self.muzzleoptions, False)

    def Fire(self, bulletcount, attacker=None, ingorespread=False):
        assert(bulletcount)
        
        attackinfo = self.GetAttack('AttackTurret')
        if not attackinfo:
            return
        
        forward = Vector()
        angles = QAngle(self.aimpitch, self.aimyaw, 0.0)
        AngleVectors(angles, forward)
    
        barrelend = self.WorldBarrelPosition()
    
        vecAdjustedForward = Vector(forward)
        
        if self.enemy:
            if isclient:
                vecToTarget = self.enemy.WorldSpaceCenter() - barrelend
            else:
                vecToTarget = self.enemy.BodyTarget( barrelend, False ) - barrelend
            VectorNormalize( vecToTarget )

            flDot = DotProduct( vecToTarget, forward )
            if flDot >= 0.97:
                vecAdjustedForward = vecToTarget
                
        info = FireBulletsInfo_t()
        info.shots = 1
        info.vecsrc = barrelend
        info.vecdirshooting = forward
        info.vecspread = self.bulletspread

        info.distance = attackinfo.maxrange + 256.0 # slight increase in bullet travel range for guaranteed hits
        info.tracerfreq = 1
        info.damage = attackinfo.damage
        info.playerdamage = attackinfo.damage
        info.attacker = attacker
        info.attributes = attackinfo.attributes
        
        if self.ammotypeidx != -1:
            for i in range(0, bulletcount):
                info.ammotype = self.ammotypeidx
                super().FireBullets(info)

        self.DoMuzzleFlash()
        
        if self.firesound:
            self.EmitSound(self.firesound)
            
        if isserver:
            self.DoAnimation(self.ANIM_FIRE)
            
            #ndebugoverlay.Line(barrelend, barrelend + forward * MAX_TRACE_LENGTH, 0, 255, 0, False, 0.25)
                    
    if isserver:
        def OnUnitTypeChanged(self, oldunittype):
            super().OnUnitTypeChanged(oldunittype)
            
            self.RebuildAttackInfo()
            self.UpdateSensingDistance()
    
        def UpdateSensingDistance(self):
            if self.senses:
                if self.unitinfo.sensedistance != -1:
                    self.senses.sensedistance = self.unitinfo.sensedistance
                else:
                    self.senses.sensedistance = self.unitinfo.viewdistance
    
        def BuildThink(self):
            eyeangles = self.EyeAngles()
            self.animstate.Update(eyeangles.y, eyeangles.x)
        
            self.StudioFrameAdvance()
            self.DispatchAnimEvents(self)
    
            attackinfo = self.unitinfo.AttackTurret
            self.SetNextThink(gpGlobals.curtime + attackinfo.attackspeed)
    else:
        def OnUnitTypeChanged(self, oldunittype):
            super().OnUnitTypeChanged(oldunittype)
            
            self.RebuildAttackInfo()
        
    # Show a custom panel when this is the only selected building    
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            from core.hud import BaseHudSingleUnitCombat, HudBuildConstruction
            if self.constructionstate != self.BS_CONSTRUCTED:
                self.unitpanelclass = HudBuildConstruction
            else:
                self.unitpanelclass = BaseHudSingleUnitCombat
                
    events = dict(BaseClass.events)
    events.update({
        'ANIM_FIRE' : FireTurret,
    })
                
    senses = None
                
    # Parameters
    ammotype = 'SMG1' # Pistol, SMG1, AR2, CombineHeavyCannon
    ammotypeidx = -1
    barrelattachment = 0
    barrelattachmentname = None
    bulletspread = Vector(0.02618, 0.02618, 0.02618) # VECTOR_CONE_3DEGREES
    
    spritesmoke = "Smoke Sprite"
    spriteflash = "Flash Sprite"
    firesound = None
    
    idleact = None
    fireact = None
    muzzleoptions = None # Used to directly cause a muzzle event, in case no fire animations are played
    
    pitchturnspeed = 360.0
    yawturnspeed = 360.0
    
    aimtype = 0
    aimposepitch = -1
    aimposeyaw = -1
    
    aimpitch = 0 
    aimyaw = 0
    aimpitch_limitlo = 0
    aimyaw_limitlo = 0
    aimpitch_limithi = 0
    aimyaw_limithi = 0
    
    # Aim types
    AIMTYPE_NONE = 0 # Does not rotate the model, just changes aim
    AIMTYPE_ABS = 1  # Rotate model to aim
    AIMTYPE_POSE = 2 # Use pose parameters to aim
    
    # Fallback
    unitinfofallback = TurretFallBackInfo
    unitinfovalidationcls = WarsTurretInfo

    