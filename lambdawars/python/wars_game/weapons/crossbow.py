from srcbase import *
from vmath import *
from entities import entity, WeaponSound, CSprite, CBaseCombatCharacter, CreateEntityByName, MOVECOLLIDE_FLY_CUSTOM
from core.weapons import WarsWeaponBase, VECTOR_CONE_6DEGREES
from core.abilities import AttackAbilityAsAttack, AbilityAsAttack
from core.units import UnitInfo, UnitDamageControllerInfo, CreateUnit
from core.decorators import serveronly
from core.ents.homingprojectile import HomingProjectile
from wars_game.abilities.steadyposition import RebelAbilitySteadyPosition
from utils import UTIL_SetOrigin, UTIL_PrecacheOther, UTIL_Remove, UTIL_ImpactTrace, trace_t, UTIL_TraceLine
from te import CEffectData, DispatchEffect
from particles import PrecacheParticleSystem, DispatchParticleEffect, PATTACH_ABSORIGIN_FOLLOW
from fields import FloatField

if isserver:
    from utils import UTIL_SetSize, UTIL_DecalTrace, UTIL_BubbleTrail
    from entities import (ClearMultiDamage, ApplyMultiDamage, CalculateMeleeDamageForce, CTakeDamageInfo, RadiusDamage,
                          CLASS_NONE)

@entity('crossbow_bolt', networked=True)
class CrossbowBolt(HomingProjectile):
    glowsprite = None
    particletrailname = 'crossbow_tracer_BASE'
    # particleeffect = 'crossbow_tracer_BASE'
    modelname = "models/crossbow_bolt.mdl"
    BOLT_SKIN_GLOW = 1
    damage = 10
    # explodetolerance = 4.0

    BOLT_AIR_VELOCITY = 2000

    @classmethod
    def BoltCreate(cls, origin, direction, enemy, damage, owner, clsname='crossbow_bolt', attributes=None):
        angles = QAngle()
        VectorAngles(direction, angles)

        # Create a new entity with CCrossbowBolt private data
        bolt = CreateEntityByName(clsname)
        bolt.attackattributes = attributes
        bolt.dietime = gpGlobals.curtime + 2.5
        UTIL_SetOrigin(bolt, origin)
        bolt.SetAbsAngles(angles)
        bolt.SetOwnerEntity(owner)
        bolt.SetOwnerNumber(owner.GetOwnerNumber())
        bolt.Spawn()
        bolt.SetTargetAndFire(enemy)

        bolt.velocity = cls.BOLT_AIR_VELOCITY
        bolt.damage = damage

        return bolt

    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)

            if type == DATA_UPDATE_CREATED:
                self.ParticleProp().Create(self.particletrailname, PATTACH_ABSORIGIN_FOLLOW)

    def CreateSprites(self):
        # Start up the eye glow
        self.glowsprite = CSprite.SpriteCreate("sprites/light_glow02_noz.vmt", self.GetLocalOrigin(), False)

        if self.glowsprite is not None:
            self.glowsprite.FollowEntity(self)
            self.glowsprite.SetTransparency(kRenderGlow, 255, 255, 255, 128, kRenderFxNoDissipation)
            self.glowsprite.SetScale(0.2)
            self.glowsprite.TurnOff()

        return True

    def DestroySprites(self):
        if self.glowsprite:
            UTIL_Remove(self.glowsprite)
            self.glowsprite = None

    if isserver:
        def Spawn(self):
            self.Precache()

            super().Spawn()

            self.CreateSprites()

            # Make us glow until we've hit the wall
            self.skin = self.BOLT_SKIN_GLOW

        def Precache(self):
            super().Precache()

            self.PrecacheModel("sprites/light_glow02_noz.vmt")

            PrecacheParticleSystem(self.particletrailname)

    def UpdateOnRemove(self):
        super().UpdateOnRemove()

        self.DestroySprites()

    def ProjectileImpact(self, projectile_target):
        """ Called when the homing projectile is within impact tolerance. """
        other = projectile_target

        if not other or not other.IsSolid() or other.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS):
            self.ProjectileDie()
            return

        dmginfo = CTakeDamageInfo(self, self.GetOwnerEntity(), self.damage, DMG_BULLET | DMG_NEVERGIB)
        dmginfo.attributes = self.attackattributes
        other.TakeDamage(dmginfo)

        # play body "thwack" sound
        self.EmitSound("Weapon_Crossbow.BoltHitBody")

        vForward = Vector()
        AngleVectors(self.GetAbsAngles(), vForward)
        VectorNormalize(vForward)

        tr2 = trace_t()
        UTIL_TraceLine(self.GetAbsOrigin(), self.GetAbsOrigin() + vForward * 128, MASK_OPAQUE, None,
                       COLLISION_GROUP_NONE, tr2)

        if tr2.fraction != 1.0:
            # NDebugOverlay.Box( tr2.endpos, Vector( -16, -16, -16 ), Vector( 16, 16, 16 ), 0, 255, 0, 0, 10 )
            # NDebugOverlay.Box( GetAbsOrigin(), Vector( -16, -16, -16 ), Vector( 16, 16, 16 ), 0, 0, 255, 0, 10 )

            if tr2.ent is None or (tr2.ent and tr2.ent.GetMoveType() == MOVETYPE_NONE):
                data = CEffectData()
                data.origin = tr2.endpos
                data.normal = vForward
                data.entindex = tr2.fraction != 1.0

                DispatchEffect("BoltImpact", data)

        self.RemoveCrossbowBolt()

    def ProjectileDie(self):
        """ Called when the projectile exceeds its lifetime. """
        UTIL_Remove(self)

    def RemoveCrossbowBolt(self):
        # Do not directly remove, so the particle effect has some extra time for playing out
        self.SetMoveType(MOVETYPE_FLYGRAVITY, MOVECOLLIDE_FLY_CUSTOM)
        UTIL_SetSize(self, -Vector(1, 1, 1), Vector(1, 1, 1))
        self.SetSolid(SOLID_BBOX)
        self.DestroySprites()
        self.SetNextThink(gpGlobals.curtime + 2.0)
        self.SetThink(self.SUB_Remove)

class UnitExplosiveBoltDamageInfo(UnitDamageControllerInfo):
    name = 'explosivebolt_damage'
    attributes = ['explosive']
    cls_name = 'unit_damage_controller_all'

# TODO: should also become a homing projectile, but that version currently does not support targeting an origin
@entity('crossbow_explosivebolt', networked=True)
class ExplosiveCrossbowBolt(CBaseCombatCharacter):
    glowsprite = None

    # BOLT_MODEL = "models/crossbow_bolt.mdl"
    BOLT_MODEL = "models/weapons/w_missile_closed.mdl"
    BOLT_SKIN_GLOW = 1

    damage = 100
    dmgradius = 64.0
    damagecontroller = None
    attackattributes = None

    particletrailname = 'crossbow_tracer_BASE'

    BOLT_AIR_VELOCITY = 3500
    BOLT_WATER_VELOCITY = 1500

    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)

            if type == DATA_UPDATE_CREATED:
                self.ParticleProp().Create(self.particletrailname, PATTACH_ABSORIGIN_FOLLOW)

    @classmethod
    def BoltCreate(cls, origin, direction, enemy, damage, owner, clsname='crossbow_explosivebolt', attributes=None):
        angles = QAngle()
        VectorAngles(direction, angles)

        # Create a new entity with CCrossbowBolt private data
        bolt = CreateEntityByName(clsname)
        bolt.attackattributes = attributes
        UTIL_SetOrigin(bolt, origin)
        bolt.SetAbsAngles(angles)
        if owner:
            bolt.SetOwnerNumber(owner.GetOwnerNumber())
        bolt.Spawn()
        bolt.SetOwnerEntity(owner)

        bolt.damage = damage

        if owner.GetWaterLevel() == 3:
            bolt.SetAbsVelocity(direction * cls.BOLT_WATER_VELOCITY)
        else:
            bolt.SetAbsVelocity(direction * cls.BOLT_AIR_VELOCITY)

        return bolt

    def CreateVPhysics(self):
        # Create the object in the physics system
        self.VPhysicsInitNormal(SOLID_BBOX, FSOLID_NOT_STANDABLE, False)

        return True

    def PhysicsSolidMaskForEntity(self):
        return (super().PhysicsSolidMaskForEntity() | CONTENTS_HITBOX) & ~CONTENTS_GRATE

    def CreateSprites(self):
        # Start up the eye glow
        self.glowsprite = CSprite.SpriteCreate("sprites/light_glow02_noz.vmt", self.GetLocalOrigin(), False)

        if self.glowsprite is not None:
            self.glowsprite.FollowEntity(self)
            self.glowsprite.SetTransparency(kRenderGlow, 255, 255, 255, 128, kRenderFxNoDissipation)
            self.glowsprite.SetScale(0.2)
            self.glowsprite.TurnOff()

        return True

    if isserver:
        def Spawn(self):
            self.Precache()

            self.damagecontroller = CreateUnit(UnitExplosiveBoltDamageInfo.name, owner_number=self.GetOwnerNumber())

            self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
            self.SetModel("models/crossbow_bolt.mdl")
            self.SetMoveType(MOVETYPE_FLYGRAVITY, MOVECOLLIDE_FLY_CUSTOM)
            UTIL_SetSize(self, -Vector(1, 1, 1), Vector(1, 1, 1))
            self.SetSolid(SOLID_BBOX)
            self.SetGravity(0.05)

            # Make sure we're updated if we're underwater
            self.UpdateWaterState()

            self.SetTouch(self.BoltTouch)

            self.CreateSprites()

            # Make us glow until we've hit the wall
            self.skin = self.BOLT_SKIN_GLOW

        def Precache(self):
            self.PrecacheModel(self.BOLT_MODEL)

            # self is used by C_TEStickyBolt, despte being different from above!!!
            self.PrecacheModel("models/crossbow_bolt.mdl")

            self.PrecacheModel("sprites/light_glow02_noz.vmt")

            PrecacheParticleSystem(self.particletrailname)

            self.indexfireball = self.PrecacheModel('sprites/zerogxplode.vmt')
            self.indexwaterfireball = self.PrecacheModel('sprites/WXplo1.vmt')

            self.PrecacheScriptSound("BaseGrenade.Explode")
            PrecacheParticleSystem("explosion_turret_break")

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            if self.damagecontroller:
                self.damagecontroller.Remove()

            if self.glowsprite:
                UTIL_Remove(self.glowsprite)

    def BoltTouch(self, other):
        if not other.IsSolid() or other.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS):
            return

        origin = self.GetAbsOrigin()

        dmgradius = self.dmgradius

        DispatchParticleEffect("explosion_turret_break", origin, self.GetAbsAngles())

        vecReported = Vector(vec3_origin)
        blastforce = Vector(vec3_origin)

        self.EmitSound("BaseGrenade.Explode")
        self.EmitSound("BaseExplosionEffect.Sound")

        # Notes about the RadiusDamage function:
        # It will have falloff damage if the inflictor (first argument CTakeDamageInfo) is not directly visible through a trace.
        # The second argument (attacker) is used in the damage taking function for attributes (core.units.base.UnitBaseShared.OnTakeDamage)
        info = CTakeDamageInfo(self, self.damagecontroller, None, blastforce, origin, self.damage, DMG_BLAST, 0,
                               vecReported)

        RadiusDamage(info, origin, dmgradius, CLASS_NONE, None)

        UTIL_DecalTrace(super().GetTouchTrace(), "Scorch")

        self.SetTouch(None)
        self.SetThink(None)

        self.RemoveCrossbowBolt()

    def RemoveCrossbowBolt(self):
        # Do not directly remove, so the particle effect has some extra time for playing out
        self.SetMoveType(MOVETYPE_NONE)
        self.SetTouch(None)
        self.SetThink(self.SUB_Remove)
        self.SetNextThink(gpGlobals.curtime + 0.25)
    
@entity('weapon_crossbow', networked=True)
class WeaponCrossbow(WarsWeaponBase):
    BOLT_SKIN_NORMAL = 0
    BOLT_SKIN_GLOW = 1
    
    CROSSBOW_GLOW_SPRITE = "sprites/light_glow02_noz.vmt"
    CROSSBOW_GLOW_SPRITE2 = "sprites/blueflare1.vmt"
    
    # Charger states
    CHARGER_STATE_START_LOAD = 0
    CHARGER_STATE_START_CHARGE = 1
    CHARGER_STATE_READY = 2
    CHARGER_STATE_DISCHARGE = 3
    CHARGER_STATE_OFF = 4
    
    chargersprite = None
    chargestate = CHARGER_STATE_OFF

    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_6DEGREES
        
    def Precache(self):
        super().Precache()
        
        if isserver:
            UTIL_PrecacheOther("crossbow_bolt")
            UTIL_PrecacheOther("crossbow_explosivebolt")

        self.PrecacheScriptSound( "Weapon_Crossbow.BoltHitBody" )
        self.PrecacheScriptSound( "Weapon_Crossbow.BoltHitWorld" )
        self.PrecacheScriptSound( "Weapon_Crossbow.BoltSkewer" )

        self.PrecacheModel(self.CROSSBOW_GLOW_SPRITE)
        self.PrecacheModel(self.CROSSBOW_GLOW_SPRITE2)

    def StartRangeAttack(self, enemy):
        super().StartRangeAttack(enemy)

        owner = self.GetOwner()

        owner.DoMuzzleFlash()

        self.SendWeaponAnim(self.GetPrimaryAttackActivity())

        self.FireBolt(damage=self.AttackPrimary.damage, attributes=self.AttackPrimary(unit=owner).attributes, enemy=enemy)

        if isserver:
            owner.DispatchEvent('OnOutOfClip')
        
    def PrimaryAttack(self):
        pass
            
    def SecondaryAttack(self):
        # Prevent firing during delay
        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + self.secondaryfiredelay + 0.1

        self.SendWeaponAnim(Activity.ACT_VM_FIDGET)
        self.WeaponSound(WeaponSound.SPECIAL1)
        
        # Delay fire using SetThink
        self.SetThink(self.DelayedAttack, self.nextprimaryattack, "DelayedFire")
    
    def DelayedAttack(self):
        owner = self.GetOwner()

        owner.DoMuzzleFlash()
        
        self.SendWeaponAnim(Activity.ACT_VM_SECONDARYATTACK)
        
        self.FireBolt(damage=150, bolt_factory=ExplosiveCrossbowBolt.BoltCreate, clsname='crossbow_explosivebolt', attributes=self.AttackExplosiveBolt(unit=owner).attributes, enemy=owner.enemy)
        
        if isserver:
            owner.DispatchEvent('OnOutOfClip')
        
    def FireBolt(self, enemy, damage=100, bolt_factory=CrossbowBolt.BoltCreate, clsname='crossbow_bolt', attributes=None):
        '''if self.clip1 <= 0:
            if not m_bFireOnEmpty:
                Reload()
            else:
                WeaponSound( WeaponSound.EMPTY )
                self.nextprimaryattack = 0.15
            return'''

        owner = self.GetOwner()
        
        if owner is None:
            return

        if isserver:
            vec_src, vec_aiming = self.GetShootOriginAndDirection()

            bolt_factory(vec_src, vec_aiming, enemy, damage, owner.garrisoned_building or owner,
                                             clsname=clsname, attributes=attributes)

        self.clip1 -= 1

        if owner.IsPlayer():
            owner.ViewPunch(QAngle( -2, 0, 0 ))

        self.WeaponSound( WeaponSound.SINGLE )
        self.WeaponSound( WeaponSound.SPECIAL2 )

        self.SendWeaponAnim(self.GetPrimaryAttackActivity())

        '''if not self.clip1 and owner.GetAmmoCount( m_iPrimaryAmmoType ) <= 0:
            # HEV suit - indicate out of ammo condition
            owner.SetSuitUpdate("!HEV_AMO0", False, 0)'''

        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + self.AttackPrimary.attackspeed

        self.DoLoadEffect()
        self.SetChargerState(self.CHARGER_STATE_DISCHARGE)
        
    def Deploy(self):
        if self.clip1 <= 0:
            return self.DefaultDeploy(self.GetViewModel(), self.GetWorldModel(), ACT_CROSSBOW_DRAW_UNLOADED, self.GetAnimPrefix())

        self.skin = self.BOLT_SKIN_GLOW

        return super().Deploy()

    def Holster(self, switching_to=None):
        #if m_bInZoom:
        #    ToggleZoom()

        self.SetChargerState(self.CHARGER_STATE_OFF)

        return super().Holster(switching_to)

    BOLT_TIP_ATTACHMENT = 2

    @serveronly
    def CreateChargerEffects(self):
        owner = self.GetOwner()
        if not owner.IsPlayer():
            return

        if self.chargersprite is not None:
            return

        self.chargersprite = CSprite.SpriteCreate(self.CROSSBOW_GLOW_SPRITE, self.GetAbsOrigin(), False)

        if self.chargersprite:
            self.chargersprite.SetAttachment( owner.GetViewModel(), self.BOLT_TIP_ATTACHMENT )
            self.chargersprite.SetTransparency( kRenderTransAdd, 255, 128, 0, 255, kRenderFxNoDissipation )
            self.chargersprite.SetBrightness( 0 )
            self.chargersprite.SetScale( 0.1 )
            self.chargersprite.TurnOff()

    def SetSkin(self, skinNum):
        owner = self.GetOwner()
        
        if not owner or not owner.IsPlayer():
            return

        pViewModel = owner.GetViewModel()
        if pViewModel is None:
            return

        pViewModel.skin = skinNum

    def DoLoadEffect(self):
        self.SetSkin(self.BOLT_SKIN_GLOW)

        owner = self.GetOwner()
        if not owner or not owner.IsPlayer():
            return

        pViewModel = owner.GetViewModel()
        if pViewModel is None:
            return

        data = CEffectData()

        if isclient:
            data.entity = pViewModel.GetRefEHandle()
        else:
            data.entindex = pViewModel.entindex()

        data.attachmentindex = 1

        DispatchEffect( "CrossbowLoad", data )

        if isserver:
            pBlast = CSprite.SpriteCreate(self.CROSSBOW_GLOW_SPRITE2, self.GetAbsOrigin(), False)

            if pBlast:
                pBlast.SetAttachment( owner.GetViewModel(), 1 )
                pBlast.SetTransparency( kRenderTransAdd, 255, 255, 255, 255, kRenderFxNone )
                pBlast.SetBrightness( 128 )
                pBlast.SetScale( 0.2 )
                pBlast.FadeOutFromSpawn()
        
    def SetChargerState(self, state):
        # Make sure we're setup
        self.CreateChargerEffects()

        # Don't do self twice
        if state == self.chargestate:
            return

        self.chargestate = state

        if self.chargestate == self.CHARGER_STATE_START_LOAD:
            self.WeaponSound(WeaponSound.SPECIAL1)
            
            # Shoot some sparks and draw a beam between the two outer points
            self.DoLoadEffect()

        if self.chargestate == self.CHARGER_STATE_START_CHARGE:
            if self.chargersprite is not None:
                self.chargersprite.SetBrightness( 32, 0.5 )
                self.chargersprite.SetScale( 0.025, 0.5 )
                self.chargersprite.TurnOn()
        elif self.chargestate == self.CHARGER_STATE_READY:
                # Get fully charged
                if self.chargersprite is not None:
                    self.chargersprite.SetBrightness( 80, 1.0 )
                    self.chargersprite.SetScale( 0.1, 0.5 )
                    self.chargersprite.TurnOn()
        elif self.chargestate == self.CHARGER_STATE_DISCHARGE:
                self.SetSkin( self.BOLT_SKIN_NORMAL )
                
                if self.chargersprite is not None:
                    self.chargersprite.SetBrightness( 0 )
                    self.chargersprite.TurnOff()
        elif self.chargestate == self.CHARGER_STATE_OFF:
            self.SetSkin( self.BOLT_SKIN_NORMAL )

            if self.chargersprite is not None:
                self.chargersprite.SetBrightness( 0 )
                self.chargersprite.TurnOff()

    clientclassname = 'weapon_crossbow'
    #muzzleoptions = 'SHOTGUN MUZZLE'
    secondaryfiredelay = FloatField(value=0.5)

    class AttackPrimary(AttackAbilityAsAttack):
        abi_attack_name = 'crossbow_attack'
        #minrange = 128.0
        maxrange = 1152.0
        attackspeed = 1.99
        damage = 50
        cone = UnitInfo.AttackRange.DOT_3DEGREE
        attributes = ['crossbow']

        def CanAttack(self, enemy):
            unit = self.unit
            if not unit.CanRangeAttack(enemy):
                return False

            if not unit.insteadyposition:
                abi = unit.abilitiesbyname[RebelAbilitySteadyPosition.name]
                return unit.abilitycheckautocast[abi.uid] and abi.CanDoAbility(None, unit=unit)

            abi = unit.abilitiesbyname[self.abi_attack_name]
            target_is_enemy = (unit.curorder and unit.curorder.type == unit.curorder.ORDER_ENEMY and
                                unit.curorder.target == enemy)
            return (target_is_enemy or unit.abilitycheckautocast[abi.uid]) and abi.CanDoAbility(None, unit=unit)

        def Attack(self, enemy, action):
            unit = self.unit
            if action and not unit.insteadyposition and not unit.garrisoned:
                ability = unit.DoAbility(RebelAbilitySteadyPosition.name, [], autocasted=True, direct_from_attack=True)
                return action.SuspendFor(ability.ActionDoSteadyPosition, 'Changing to steady position', ability, None)
            return super().Attack(enemy, action)

    class AttackExplosiveBolt(WarsWeaponBase.AttackRange):
        damage = 100
        attributes = ['crossbow']

class AbilityCrossbowAttack(AbilityAsAttack):
    name = 'crossbow_attack'
    displayname = '#RebCrossbowAttack_Name'
    description = '#RebCrossbowAttack_Description'
    image_name = 'vgui/rebels/abilities/crossbow_attack'
    rechargetime = 1.99

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        # If unit is garrisoned then ability still should be controllable
        if unit.garrisoned:
            requirements.discard('uncontrollable')
            
        if not getattr(unit, 'insteadyposition', False) and not unit.garrisoned:
            requirements.add('rebel_steadyposition')
        return requirements

class AbilityCrossbowCharAttack(AbilityCrossbowAttack):
    name = 'crossbow_attack_char'
    displayname = '#RebCrossbowAttack_Name'
    description = '#RebCrossbowAttack_Description'
    image_name = 'vgui/rebels/abilities/crossbow_attack'
    rechargetime = 1.99

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        # If unit is garrisoned then ability still should be controllable
        if unit.garrisoned:
            requirements.discard('uncontrollable')

        if not getattr(unit, 'insteadyposition', False) and not unit.garrisoned:
            requirements.add('rebel_steadyposition')
        return requirements