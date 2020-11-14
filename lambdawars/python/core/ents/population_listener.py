from entities import CPointEntity, entity
from fields import input, OutputField, BooleanField, FloatField, IntegerField, StringField, FlagsField, fieldtypes, input
from core.signals import unitspawned, unitremoved
from core.units import unitlist, unitpopulationcount
from core.buildings import buildinglist

@entity('wars_population_listener',
        base=['Targetname', 'Parentname', 'Angles', 'Wars'],
        iconsprite='editor/wars_population_listener.vmt')
class PopulationListener(CPointEntity):
    ''' Listens to population count changes for the owner of this entity.
        Provides outputs for when the total population or just the building count changed.
    '''
    def __init__(self):
        super().__init__()
        
        unitspawned.connect(self.OnUnitSpawned)
        unitremoved.connect(self.OnUnitRemoved)
        
    def UpdateOnRemove(self):
        super().UpdateOnRemove()
        
        unitspawned.disconnect(self.OnUnitSpawned)
        unitremoved.disconnect(self.OnUnitRemoved)
        
    def CheckCountsChanged(self, unit=None):
        if self.disabled:
            return
            
        owner = self.GetOwnerNumber()
            
        # Check if population changed
        popcount = unitpopulationcount[owner]
        if popcount != self.lastpopcount:
            self.onpopulationchanged.Set(popcount, unit, self)
            self.lastpopcount = popcount
            
        # Check if building count changed
        buildcount = len(buildinglist[owner])
        if buildcount != self.lastbuildingcount:
            self.onbuildingcountchanged.Set(buildcount, unit, self)
            self.lastbuildingcount = buildcount
            
    def OnUnitSpawned(self, unit, *args, **kwargs):
        owner = self.GetOwnerNumber()
        if unit.GetOwnerNumber() != owner:
            return
            
        self.CheckCountsChanged(unit)
        
    def OnUnitRemoved(self, unit, *args, **kwargs):
        owner = self.GetOwnerNumber()
        if unit.GetOwnerNumber() != owner:
            return
            
        self.CheckCountsChanged(unit)
        
    @input(inputname='Enable')
    def InputEnable(self, inputdata):
        self.disabled = False
        
    @input(inputname='Disable')
    def InputDisable(self, inputdata):
        self.disabled = True
        
    onpopulationchanged = OutputField(keyname='OnPopulationChanged', fieldtype=fieldtypes.FIELD_FLOAT)
    onbuildingcountchanged = OutputField(keyname='OnBuildingCountChanged', fieldtype=fieldtypes.FIELD_FLOAT)
    disabled = BooleanField(value=False, keyname='StartDisabled', displayname='Start Disabled') 
    
    lastpopcount = -1
    lastbuildingcount = -1