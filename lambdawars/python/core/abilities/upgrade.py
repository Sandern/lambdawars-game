from .info import GetTechNode, BaseTechNode
from .base import AbilityBase
from fields import UpgradeField
    
class AbilityUpgrade(AbilityBase):
    """ Generic upgrade ability.
    
        Add derived upgrade abilities to the ability list of a building.
        This building can then research this ability.
        Such an upgrade can then be used as a technology requirement for 
        other abilities or units.
    """
    #: Resource category (match statistics)
    resource_category = 'technology'
    #: This ability replaces the upgrade after research. Usually this is another upgrade (tier1, tier2, etc)
    successorability = None 
    
    producedfactionsound = 'announcer_research_completed'
    
    sai_hint = AbilityBase.sai_hint | set(['sai_upgrade'])
    
    class TechNode(BaseTechNode):
        def Initialize(self):
            """ Initialize our tech. Find out if we should be available """
            self.techenabled = False
            super().Initialize()
        
        if isserver:
            def RecomputeAvailable(self):
                if self.researching:
                    self.available = False
                    return
                if self.techenabled:
                    self.available = False
                    return
                super().RecomputeAvailable()
            researching = False
    
    # Ability
    def Init(self):
        if self.ischeat:
            self.Completed()
            return
        
        self.SelectSingleUnit()
        if self.unit:
            technode = GetTechNode(self.info.name, self.ownernumber)
            technode.researching = True
            technode.RecomputeAvailable()
            if not self.TakeResources(refundoncancel=True):
                self.Cancel()
                return
                
            self.PlayActivateSound()
                
            # Directly call completed in case it has no buildtime
            # Saves a small delay
            if not self.buildtime:
                self.Completed()
                return
            self.unit.AddAbility(self)
        else:
            self.Cancel()
        
    def Cancel(self):
        super().Cancel()
        technode = GetTechNode(self.info.name, self.ownernumber)
        technode.researching = False
        technode.RecomputeAvailable()
        
    def Completed(self):
        super().Completed()
        technode = GetTechNode(self.info.name, self.ownernumber)
        technode.researching = False
        technode.showonunavailable = False
        technode.successorability = self.info.successorability
        technode.techenabled = True # Changing techenabled calls RecomputeAvailable
        self.OnUpgraded()
        
    def OnUpgraded(self): pass
        
    def ProduceAbility(self, producer):
        self.Completed()
        return True        
        
    serveronly = True
    
class AbilityUpgradeValue(AbilityUpgrade):
    """ Behaves the same as AbilityUpgrade, except if can change an
        attribute ("upgrade") to another value.
        
        Add fields.UpgradeField to an unit or ability.
        Then initialize the field with the name of this ability.
        When you upgrade this ability it will then upgrade the value.
        It will automatically replace all values of the active units in the map.
    """
    class TechNode(AbilityUpgrade.TechNode):
        def __init__(self, info, ownernumber):
            super().__init__(info, ownernumber)
            
            # UpgradeField will read out the value from the technode, so copy into here
            # The advantage is that we can modify upgrade values per player, even if they have
            # the same upgrade ability. This is useful to mess around in Overrun.
            self.upgradevalue = info.upgradevalue
            
    def OnUpgraded(self):
        from core.units import unitlist # FIXME
        for unit in unitlist[self.ownernumber]:
            for field in unit.fields.values():
                if isinstance(field, UpgradeField) and field.abilityname == self.name:
                    field.InitField(unit) # Reinit
    
    #: The upgraded value
    upgradevalue = None

class AbilityUpgradePopCap(AbilityUpgrade):
    """ Increases the population cap."""
    def OnUpgraded(self):
        """ Adds population to a player when researched. """
        from core.units import AddPopulation # FIXME
        AddPopulation(self.ownernumber, self.providespopulation)
        
    #: The amount of population to add when you research this ability.
    providespopulation = 10
    
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_upgrade_population'])
