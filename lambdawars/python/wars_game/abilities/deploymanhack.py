from core.abilities import AbilityInstant
from core.units import unitpopulationcount, GetMaxPopulation
import math

if isserver:
    from core.units import BaseBehavior

class AbilityDeployManhack(AbilityInstant):
    # Info
    name = 'deploymanhack'
    displayname = '#CombDepManhack_Name'
    description = '#CombDepManhack_Description'
    image_name = 'vgui/combine/abilities/deploymanhack'
    rechargetime = 30.0
    population = 1
    costs = [('requisition', 10)]
    techrequirements = ['build_comb_armory']
    activatesoundscript = '#deploymanhacks'
    hidden = True
    sai_hint = AbilityInstant.sai_hint | set(['sai_deploy'])
    
    @classmethod 
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        owner = unit.GetOwnerNumber()

        if info.population:
            # Check population count
            if unitpopulationcount[owner]+info.population > GetMaxPopulation(owner):
                requirements.add('population')
        return requirements
        
    # Ability
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()
            
            n = self.TakeResources(refundoncancel=True, count=len(self.units))
            if not n:
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            # Determine max manhacks we can deploy
            ownernumber = self.player.GetOwnerNumber()
            maxdeploy = GetMaxPopulation(ownernumber) - unitpopulationcount[ownernumber]
            maxdeploy /= self.population
            maxdeploy = int(math.floor(maxdeploy))
            n = min(maxdeploy, n)
                
            units = self.units[0:n]
                
            for unit in units:
                unit.DoAnimation(unit.ANIM_DEPLOYMANHACK)
                unit.AbilityOrder(ability=self)
            self.SetRecharge(units)
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectGroupUnits()
            self.PlayActivateSound()
        
    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbilityWaitForActivity
        
class AbilityDeployManhackOverrun(AbilityDeployManhack):
    name = 'overrun_deploymanhack'
    costs = [('kills', 1)]
    techrequirements = []

class AbilityDeployManhackChar(AbilityDeployManhack):
    name = 'char_deploymanhack'
    costs = []
    techrequirements = []
    rechargetime = 10.0
    population = 0

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        owner = unit.GetOwnerNumber()

        if info.population:
            # Check population count
            if unitpopulationcount[owner] < GetMaxPopulation(owner):
                requirements.add('population')
        return requirements

    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()

            n = self.TakeResources(refundoncancel=True, count=len(self.units))
            if not n:
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            units = self.units[0:n]
            ownernumber = self.player.GetOwnerNumber()

            # Determine max manhacks we can deploy
            '''maxdeploy = GetMaxPopulation(ownernumber) - unitpopulationcount[ownernumber]
            maxdeploy /= self.population
            maxdeploy = int(math.floor(maxdeploy))
            n = min(maxdeploy, n)'''

            for unit in units:
                unit.DoAnimation(unit.ANIM_DEPLOYMANHACK)
                unit.AbilityOrder(ability=self)
            self.SetRecharge(units)
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectGroupUnits()
            self.PlayActivateSound()

    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbilityWaitForActivity

class AbilityDeployScannerChar(AbilityInstant):
    name = 'deployscanner'
    displayname = '#CharDepScanner_Name'
    description = '#CharDepScanner_Description'
    image_name = 'vgui/combine/units/unit_observer'
    rechargetime = 120.0
    population = 0
    costs = []
    techrequirements = []
    activatesoundscript = '#deploymanhacks'
    hidden = True

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        owner = unit.GetOwnerNumber()

        if info.population:
            # Check population count
            if unitpopulationcount[owner] < GetMaxPopulation(owner):
                requirements.add('population')
        return requirements

    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()

            n = self.TakeResources(refundoncancel=True, count=len(self.units))
            if not n:
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return

            units = self.units[0:n]
            ownernumber = self.player.GetOwnerNumber()

            for unit in units:
                unit.DoAnimation(unit.ANIM_DEPLOYSCANNER)
                unit.AbilityOrder(ability=self)
            self.SetRecharge(units)
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectGroupUnits()
            self.PlayActivateSound()

    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbilityWaitForActivity