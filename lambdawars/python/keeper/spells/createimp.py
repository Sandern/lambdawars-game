from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget
from core.units import CreateUnit
from core.hud import InsertResourceIndicator
from gamerules import gamerules

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    
# Spawns a helicopter bomb
class AbilityCreateImp(AbilityTarget):
    name = "createimp"
    displayname = 'Create Imp'
    costs = [('gold', 50)]
    description = 'Spawns an Imp. Each additional Imp increases the cost price of this spell by 150 gold.'
    requireunits = False

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
        def StartAbility(self):
            super(AbilityCreateImp, self).StartAbility()
            
            self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), 'Spells.CreateImp')
    
        def DoAbility(self):
            data = self.mousedata
            
            pos = data.endpos
            tile = gamerules.keeperworld.GetTileFromPos(pos)
            if tile.GetOwnerNumber() != self.player.GetOwnerNumber():
                DevMsg(1, 'Target tile does not match player owner number\n')
                return
                
            self.costs = [[('gold', gamerules.GetCreateImpCost(self.ownernumber))]] # Dynamic costs for create imp
            if not self.TakeResources(refundoncancel=False):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            unit = CreateUnit('unit_imp', tile.GetAbsOrigin(), owner_number=2)  
            unit.SetAbsOrigin(unit.GetAbsOrigin() + Vector(0, 0, 96.0))
            self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), 'Spells.Generic')
            
            if self.costs:
                InsertResourceIndicator(pos, '-%s' % (str(self.costs[0][0][1])))

            # Don't call Complete; Ability keeps going until the user cancels
            