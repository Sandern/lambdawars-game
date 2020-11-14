from core.abilities import AbilityTarget
from gamerules import gamerules
from particles import *
    
class AbilitySKHeal(AbilityTarget):
    name = "skheal"
    displayname = "Heal"
    description = "Heal a creature"
    requireunits = False
    costs = [('gold', 100)]
    
    def DoAbilityInternal(self):
        # Copy the target position and angle
        self.targetpos = self.GetTargetPos(self.mousedata)
    
        # Cleanup
        self.cancelonmouselost = False
        #self.ClearMouse() # Don't remove mouse input from the player
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
            super(AbilitySKHeal, info).Precache()
            
            PrecacheParticleSystem('pg_heal')
    
        def StartAbility(self):
            pass
        
        def DoAbility(self):
            data = self.player.GetMouseData()
            targetpos = data.endpos
            target = data.ent
            
            if not target or target.GetOwnerNumber() != self.player.GetOwnerNumber():
                return
            
            tile = gamerules.keeperworld.GetTileFromPos(targetpos)
            if tile.GetOwnerNumber() != self.player.GetOwnerNumber():
                return
                
            if not self.TakeResources(refundoncancel=False):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            DispatchParticleEffect("pg_heal", PATTACH_ABSORIGIN_FOLLOW, target)
            target.TakeHealth(25.0, 0)
            
            
