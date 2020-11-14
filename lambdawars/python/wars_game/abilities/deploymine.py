from core.abilities import AbilityInstant

if isserver:
    from core.units import BaseBehavior

class AbilityDeployMine(AbilityInstant):
    # Info
    name = 'deploymine'
    displayname = '#CombDepMine_Name'
    description = '#CombDepMine_Description'
    image_name = 'vgui/combine/abilities/combine_clawscanner_dropmine'
    rechargetime = 10.0
    costs = [[('power', 10)], [('kills', 1)]]
    hidden = True
        
    # Ability
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()

            n = self.TakeResources(refundoncancel=True, count=len(self.units))
            if not n:
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            for unit in self.units[0:n]:
                mine = unit.DeployMine()
                if mine:
                    mine.clear_vel_on_ground_hit = True
                unit.StartProducingMine(self.rechargetime)
                unit.DoAnimation(unit.ANIM_DEPLOYMINE)
                unit.AbilityOrder(ability=self)
                self.SetRecharge(unit)
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectGroupUnits()
            self.PlayActivateSound()
        
    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbilityWaitForActivity

class AbilityProduceMine(AbilityInstant):
    # Info
    name = 'producemine'
    displayname = '#CombProdMine_Name'
    description = '#CombProdMine_Description'
    image_name = 'vgui/combine/abilities/combine_clawscanner_producemine'
    rechargetime = 5.0
    costs = [[('power', 5)], [('kills', 1)]]
    hidden = True
    
    @classmethod    
    def ShouldShowAbility(info, unit):
        return not unit.GetEquipedMine()
        
    # Ability
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()
            
            n = self.TakeResources(refundoncancel=True, count=len(self.units))
            if not n:
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            for unit in self.units[0:n]:
                if unit.StartProducingMine(self.rechargetime):
                    self.SetRecharge(unit)
                    
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectGroupUnits()
            self.PlayActivateSound()
