from srcbase import DMG_SLASH
from vmath import Vector, QAngle
from .basekeeper import UnitBaseCreature as BaseClass, UnitKeeperInfo
from entities import entity, Activity, CBaseEntity
import random
from sound import EmitSound, CSoundParameters

if isserver:
    from gameinterface import CReliableBroadcastRecipientFilter
    from .behavior import BehaviorFood
    from entities import DENSITY_NONE
    from particles import PrecacheParticleSystem, DispatchParticleEffect
    
@entity('unit_dk_grub', networked=True)
class UnitGrub(BaseClass):
    # Don't show hp/level bars
    def ShowBars(self): pass
    def HideBars(self): pass
    def OnHoverPaint(self): pass
    
    def PassesDamageFilter(self, dmginfo):
        return True
            
    if isserver:
        def __init__(self):
            super(UnitGrub, self).__init__()

            self.SetDensityMapType(DENSITY_NONE)
    
        def Precache(self):
            super(UnitGrub, self).Precache()
            
            PrecacheParticleSystem('grub_death')
            
        def Spawn(self):
            super(UnitGrub, self).Spawn()
            
            self.SetCanBeSeen(False)
            self.skin = random.randint(0, 2)
            
        def ShouldGib(self, info):
            return True
            
        def CorpseGib(self, info):
            DispatchParticleEffect("grub_death", self.GetAbsOrigin(), QAngle( 0, 0, 0 ))
        
            # make a gib sound
            filter = CReliableBroadcastRecipientFilter()
            params = CSoundParameters()
            if CBaseEntity.GetParametersForSound("ASW_Drone.GibSplatQuiet", params, None):
                ep = EmitSound(params)
                ep.origin = self.GetAbsOrigin()

                self.EmitSoundFilter(filter, 0, ep)
        
            return True

    maxspeed = 50.0
    
    hatchery = None
    
    if isserver:
        BehaviorGenericClass = BehaviorFood
    
    # Animation translation table
    acttables = {
        Activity.ACT_RUN : Activity.ACT_WALK,
    }
            
# Register unit
class UnitGrubInfo(UnitKeeperInfo):
    name = "unit_dk_grub"
    cls_name = "unit_dk_grub"
    displayname = "Grub"
    description = "Grub (aka food)"
    modelname = 'models/swarm/grubs/grub.mdl'
    health = 5
    hulltype = 'HULL_TINY'
    sound_death = 'ASW_Parasite.Death'

    