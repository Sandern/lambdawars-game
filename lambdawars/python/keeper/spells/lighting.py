from srcbase import FL_NPC, DMG_ENERGYBEAM
from vmath import QAngle, Vector, VectorNormalize, RemapValClamped
from core.abilities import AbilityTarget
from entities import CBaseEntity
from gamerules import gamerules
from particles import PrecacheParticleSystem, DispatchParticleEffect

if isserver:
    from entities import CTakeDamageInfo
    from utils import UTIL_EntitiesInBox
    
class AbilityLighting(AbilityTarget):
    name = "lighting"
    displayname = "Lighting"
    description = "Strike a bolt of lighting"
    requireunits = False
    costs = [('gold', 250)]
    
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
            super(AbilityLighting, info).Precache()
            
            PrecacheParticleSystem('Blink')
            PrecacheParticleSystem('electric_weapon_beam')
            
            CBaseEntity.PrecacheSound('ASW_Blink.Blink')
    
        def StartAbility(self):
            #self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), 'Spells.PossessCreature')
            pass
        
        def DoAbility(self):
            data = self.player.GetMouseData()
            targetpos = data.endpos
            
            tile = gamerules.keeperworld.GetTileFromPos(targetpos)
            if tile.GetOwnerNumber() != self.player.GetOwnerNumber():
                return
                
            if not self.TakeResources(refundoncancel=False):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            DispatchParticleEffect("Blink", targetpos, QAngle() )
            self.player.EmitSound( "ASW_Blink.Blink" )
            
            # Do damage
            radius = 32.0
            units = UTIL_EntitiesInBox(32, targetpos-Vector(radius,radius,radius), targetpos+Vector(radius,radius,radius), FL_NPC)
            for unit in units:
                if unit.isbuilding:
                    continue
                vecdir = (unit.GetAbsOrigin() - targetpos)
                vecdir[2] = 0.0
                dist = VectorNormalize(vecdir)

                falloff = RemapValClamped(dist, 0, radius*0.75, 1.0, 0.1)
            
                vecdir[2] += 400.0 * falloff
                dmgInfo = CTakeDamageInfo(self.player, self.player, vecdir, unit.GetAbsOrigin() , 15, DMG_ENERGYBEAM)
                unit.TakeDamage(dmgInfo)
            
            # Don't call Complete; Ability keeps going until the user cancels
            #self.Completed()  