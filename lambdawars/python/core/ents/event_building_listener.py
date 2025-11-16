"""Building event listener entity for Lambda Wars.

Listens for building started/finished signals and fires map outputs
that can be hooked up in Hammer/logic scripts.
"""
from entities import CPointEntity, entity
from fields import input, OutputField, BooleanField, FloatField, IntegerField, StringField, FlagsField, fieldtypes, input
if isserver:
    from core.signals import buildingstarted, buildingfinished

@entity('event_building_listener',
        base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
        iconsprite='editor/logic_script.vmt')
class EventBuildingListener(CPointEntity):
    """Entity that translates building start/finish events into map outputs.
    
    Hooks into the global building signals and fires Hammer outputs so map
    logic can react when construction begins or completes.
    """
    def __init__(self):
        super().__init__()
        
        buildingstarted.connect(self.OnBuildingStarted)
        buildingfinished.connect(self.OnBuildingFinished)
        
    def UpdateOnRemove(self):
        """Disconnect from building signals when the entity is removed."""
        super().UpdateOnRemove()
        
        buildingstarted.disconnect(self.OnBuildingStarted)
        buildingfinished.disconnect(self.OnBuildingFinished)
        
    def OnBuildingStarted(self, building, *args, **kwargs):
        """Signal handler for building-started; fires `OnBuildingStarted`."""
        self.onbuildingstarted.Set('', building, self)
        
    def OnBuildingFinished(self, building, *args, **kwargs):
        """Signal handler for building-finished; fires `OnBuildingFinished`."""
        self.onbuildingfinished.Set('', building, self)
        
    onbuildingstarted = OutputField(keyname='OnBuildingStarted', fieldtype=fieldtypes.FIELD_STRING)
    onbuildingfinished = OutputField(keyname='OnBuildingFinished', fieldtype=fieldtypes.FIELD_STRING)