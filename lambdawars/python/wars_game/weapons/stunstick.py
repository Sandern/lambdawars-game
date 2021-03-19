from srcbase import DMG_CLUB
from vmath import Vector, QAngle
from core.weapons import WarsWeaponMelee
from entities import entity, D_HT
from utils import UTIL_ImpactTrace
from te import CEffectData, DispatchEffect, te
from gameinterface import CPVSFilter
from wars_game.statuseffects import StunnedEffectInfo
from fields import FloatField

import random

if isserver:
    from utils import UTIL_Remove

# Client side effect
if isclient:
    from te import FX_AddQuad, FX_Sparks, ClientEffectRegistration

    def StunstickImpactCallback(data):
        scale = random.uniform(16, 32)

        FX_AddQuad(data.origin,
                   data.normal,
                   scale,
                   scale*2.0,
                   1.0,
                   1.0,
                   0.0,
                   0.0,
                   random.randint(0, 360),
                   0,
                   Vector(1.0, 1.0, 1.0),
                   0.1,
                   "sprites/light_glow02_add",
                   0)

        FX_Sparks(data.origin, 1, 2, data.normal, 6, 64, 256)

    StunstickImpactEffect = ClientEffectRegistration('StunstickImpact', StunstickImpactCallback)

@entity('weapon_stunstick', networked=True)
class WeaponStunStick(WarsWeaponMelee):
    clientclassname = 'weapon_stunstick' 
    
    STUNSTICK_BEAM_MATERIAL = "sprites/lgtning.vmt"
    STUNSTICK_GLOW_MATERIAL = "sprites/light_glow02_add"
    STUNSTICK_GLOW_MATERIAL2 = "effects/blueflare1"
    STUNSTICK_GLOW_MATERIAL_NOZ = "sprites/light_glow02_add_noz"

    stun_chance = FloatField(value=1.0)
    stun_duration = FloatField(value=0.45)
    
    class AttackPrimary(WarsWeaponMelee.AttackPrimary):
        damage = 15.0
        maxrange = 55.0
        attackspeed = 1
        attributes = ['shock']
    
    def __init__(self):
        super().__init__()
        
        self.minrange2 = 0
        self.maxrange2 = 75.0
        
    def Precache(self):
        super().Precache()
        
        self.PrecacheScriptSound("Weapon_StunStick.Activate")
        self.PrecacheScriptSound("Weapon_StunStick.Deactivate")

        self.PrecacheModel(self.STUNSTICK_BEAM_MATERIAL)

    def Hit(self, traceHit, nHitActivity):
        super().Hit(traceHit, nHitActivity)
        owner = self.GetOwner()
        hit_entity = traceHit.ent
        if hit_entity and hit_entity.IsUnit() and random.random() <= self.stun_chance and owner.IRelationType(hit_entity) == D_HT:
            StunnedEffectInfo.CreateAndApply(hit_entity, attacker=self, duration=self.stun_duration)
        
    def ImpactEffect(self, traceHit):
        data = CEffectData()

        data.normal = traceHit.plane.normal
        data.origin = traceHit.endpos + (data.normal * 4.0)

        DispatchEffect("StunstickImpact", data)

        #FIXME: need new decals
        UTIL_ImpactTrace(traceHit, DMG_CLUB)

    def SetStunState(self, state):
        """ Sets the state of the stun stick """
        self.active = state

        if self.active:
            #FIXME: START - Move to client-side

            vecAttachment = Vector()
            vecAttachmentAngles = QAngle()

            self.GetAttachment(1, vecAttachment, vecAttachmentAngles)

            filter = CPVSFilter(vecAttachment)
            if not te.SuppressTE(filter):
                te.Sparks(filter, 0.0, vecAttachment, 1, 1, None)

            # FIXME: END - Move to client-side

            self.EmitSound("Weapon_StunStick.Activate")
        else:
            self.EmitSound("Weapon_StunStick.Deactivate")

    def Deploy(self):
        """ Returns true on success, false on failure. """
        self.SetStunState(True)
        #if isclient:
            #SetupAttachmentPoints()

        return super().Deploy()

    def Holster(self, switching_to=None):
        if not super().Holster(switching_to):
            return False

        self.SetStunState(False)
        self.SetWeaponVisible(False)

        return True

    def Drop(self, vecVelocity):
        self.SetStunState(False)

        if isserver:
            UTIL_Remove(self)