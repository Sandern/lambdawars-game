from srcbase import *
from vmath import *
from .basedota import UnitDotaInfo, UnitDota as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity, ACT_INVALID
import random
from particles import DispatchParticleEffect, PATTACH_POINT_FOLLOW
from particles import *

if isserver:
    from core.units import BaseAction
    from entities import SpawnBlood
    #from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
    
    from entities import (CSprite, gEntList, ImpulseScale, CalculateExplosiveDamageForce,
                          CTakeDamageInfo, D_HT, CalculateMeleeDamageForce)
    from utils import (UTIL_Remove, CTraceFilterMelee, CTraceFilterEntitiesOnly, CTraceFilter, trace_t, Ray_t, UTIL_TraceRay, UTIL_TraceHull, StandardFilterRules, PassServerEntityFilter,
                       UTIL_ScreenShake, SHAKE_START)
    from particles import PrecacheParticleSystem
else:
    from entities import DataUpdateType_t
    
@entity('hero_doom', networked=True)
class UnitDoom(BaseClass):
    """ Infected """
    def __init__(self):
        super(UnitDoom, self).__init__()

    def Precache(self):
        super(UnitDoom, self).Precache()
        
        if isserver:
            PrecacheParticleSystem("doom_bringer_ambient")
            PrecacheParticleSystem("doom_scorched_earth_primary")
            PrecacheParticleSystem("doom_bringer_devour")
            PrecacheParticleSystem("doom_bringer_doom")

    def Spawn(self):
        self.Precache()

        super(UnitDoom, self).Spawn()
        
        #if isserver:
            #att = self.LookupAttachment('attach_attack1')
            #att = self.LookupAttachment('attach_weapon_blur')
            #print att
            #DispatchParticleEffect('doom_bringer_ambient', PATTACH_POINT_FOLLOW, self, att)
            
    if isclient:
        def OnDataChanged(self, type):
            super(UnitDoom, self).OnDataChanged(type)
            
            if type == DataUpdateType_t.DATA_UPDATE_CREATED:
                self.CreateFlame()
                
        def CreateFlame(self):
            prop = self.ParticleProp()
            
            att = self.LookupAttachment('attach_attack1')
            #att = self.LookupAttachment('attach_weapon_blur')
           # print att
            self.flamefx = prop.Create('doom_bringer_ambient', PATTACH_POINT_FOLLOW, att)
            #print self.flamefx
            if self.flamefx:
                for i in range(0, 6):
                    prop.AddControlPoint(self.flamefx, i, self, PATTACH_POINT_FOLLOW, 'attach_attack1')
                    
        def DestroyFlame(self):
            pass
            
        def UpdateOnRemove(self):
            self.DestroyFlame()

            super(UnitDoom, self).UpdateOnRemove()
                    
    # Vars
    maxspeed = 290.0
    yawspeed = 40.0
    jumpheight = 40.0

# Register unit
class UnitDoomInfo(UnitDotaInfo):
    name = "hero_doom"
    cls_name = "hero_doom"
    displayname = "#DOTA_Doom_Name"
    description = "#DOTA_Doom_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/heroes/doom/doom.mdl'
    hulltype = 'HULL_HERO_LARGE'
    health = 500

    #sound_select = ''
    #sound_move = ''
    #sound_death = ''
    
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitDotaInfo.AttackMelee):
        maxrange = 150.0
        damage = 50
        damagetype = DMG_SLASH
        attackspeed = 1.6
    attacks = 'AttackMelee'
    