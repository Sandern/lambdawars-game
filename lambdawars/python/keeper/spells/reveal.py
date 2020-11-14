from vmath import Vector
from core.abilities import AbilityTarget
from fields import FloatField
from core.units import CreateUnit
#import ndebugoverlay
    
class AbilityReveal(AbilityTarget):
    name = "reveal"
    displayname = "Reveal"
    description = r"Reveals target area"
    requireunits = False
    costs = [('gold', 100)]
    
    scanduration = FloatField(value=10.0)
    scanrange = FloatField(value=320.0)
    
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
        def StartAbility(self):
            pass
        
        def DoAbility(self):
            data = self.player.GetMouseData()
            targetpos = data.endpos
                
            if not self.TakeResources(refundoncancel=False):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return
                
            pos = data.endpos
            pos.z += 512.0
            #ndebugoverlay.Box(pos, -Vector(8,8,8), Vector(8,8,8), 255, 0, 0, 255, 10.0)
            unit = CreateUnit('unit_scan', pos, owner_number=self.player.GetOwnerNumber())
            unit.viewdistance = self.scanrange
            unit.SetScanDuration(self.scanduration)
            self.Completed()
            
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, targetpos + self.particleoffset)
        inst.SetControlPoint(2, Vector(self.scanrange, self.scanrange, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
        
    infoparticles = ['range_radius_radar']