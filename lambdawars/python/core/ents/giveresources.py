
if isserver:
    from entities import CLogicalEntity, entity
    from core.resources import TakeResources, GiveResources
    from fields import input, BooleanField, StringField, fieldtypes
    
    @entity('give_resources',
            base=['Targetname', 'Wars'],
            iconsprite='editor/give_resources.vmt')
    class EntGiveResources(CLogicalEntity):
        resourcetype = StringField(value='requisition', keyname='resourcetype',
                               displayname='Resource Type', helpstring='Resource Type')
        takeresources = BooleanField(value=False, keyname='takeresources',
                               displayname='Take Resources', helpstring='Take resources away from the player')
                               
        @input(inputname='GiveResources', helpstring='Give resources to a player.', fieldtype=fieldtypes.FIELD_INTEGER)
        def InputGiveResources(self, inputdata):
            if self.takeresources:
                TakeResources(self.GetOwnerNumber(), [(self.resourcetype, inputdata.value.Int())])
            else:
                GiveResources(self.GetOwnerNumber(), [(self.resourcetype, inputdata.value.Int())])