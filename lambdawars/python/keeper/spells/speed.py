from core.abilities import AbilityTarget
from gamerules import gamerules
from particles import *

if isserver:
    from entities import CTakeDamageInfo
    from utils import UTIL_EntitiesInBox
    
class AbilityIncreaseSpeed(AbilityTarget):
    name = "increasespeed"
    displayname = "Speed"
    description = r"Increase speed of creature by 100%"
    requireunits = False
    costs = [('gold', 200)]
    
    def DoAbilityInternal(self):
        # Copy the target position and angle
        self.targetpos = self.GetTargetPos(self.mousedata)
    
        # Cleanup
        self.cancelonmouselost = False
        if isclient:
            self.DestroyArrow()
            if self.clearvisualsonmouselost:
                self.ClearVisuals()
            else:
                if self.cleartempmodonmouselost:
                    self.ClearTempModel()
        
        # Do the actual ability
        self.PlayActivateSound()
        self.DoAbility()
        
    if isserver:
        @classmethod           
        def Precache(info):
            super(AbilityIncreaseSpeed, info).Precache()
            
            PrecacheParticleSystem('body_explode')
    
        def StartAbility(self):
            pass
        
        def DoAbility(self):
            data = self.player.GetMouseData()
            targetpos = data.endpos
            target = data.ent
            
            if not target or target.GetOwnerNumber() != self.player.GetOwnerNumber():
                return
                
            if not hasattr(target, 'IncreaseSpeedTemporary'):
                return
            
            tile = gamerules.keeperworld.GetTileFromPos(targetpos)
            if tile.GetOwnerNumber() != self.player.GetOwnerNumber():
                return
                
            if not self.TakeResources(refundoncancel=False):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return
            
            target.IncreaseSpeedTemporary(2.0, 30.0)
            DispatchParticleEffect("body_explode", PATTACH_ABSORIGIN_FOLLOW, target)
            
