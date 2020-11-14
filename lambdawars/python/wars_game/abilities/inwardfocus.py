from core.abilities import AbilityInstant
if isserver:
    from core.units import BaseBehavior
        
    class ActionInwardFocus(BaseBehavior.ActionAbility):
        def Update(self):
            energy = min(self.outer.energy, self.order.ability.healrate)
            self.outer.health = min(int(self.outer.health + energy), self.outer.maxhealth)
            self.outer.TakeEnergy(energy)
            
            if round(self.outer.energy) == 0:
                return self.ChangeTo(self.behavior.ActionIdle, 'Out of energy')
            if self.outer.health == self.outer.maxhealth:
                return self.ChangeTo(self.behavior.ActionIdle, 'Fully healed')
            return self.Continue()
            
        def OnEnd(self):
            self.order.Remove(dispatchevent=False)

class AbilityInwardFocus(AbilityInstant):
    # Info
    name = "inwardfocus"
    displayname = "#RebInwardFocus_Name"
    description = "#RebInwardFocus_Description"
    image_name = 'vgui/rebels/abilities/inwardfocus'
    healrate = 20.0
    energy = 1
    
    # Ability
    def DoAbility(self):
        self.SelectGroupUnits()
        for unit in self.units:
            if unit.health == unit.maxhealth:
                continue
            unit.AbilityOrder(ability=self)
        self.Completed()
        
    if isserver:
        behaviorgeneric_action = ActionInwardFocus
    serveronly = True
    