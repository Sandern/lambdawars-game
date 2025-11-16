"""Map entity that gives or takes RTS resources from a player."""

if isserver:
    from entities import CLogicalEntity, entity
    from core.resources import TakeResources, GiveResources
    from fields import input, BooleanField, StringField, fieldtypes
    
    @entity('give_resources',
            base=['Targetname', 'Wars'],
            iconsprite='editor/give_resources.vmt')
    class EntGiveResources(CLogicalEntity):
        """Logical entity that modifies a player's resource pool.
        
        Configured with a resource type and whether to add or subtract; the
        `GiveResources` input applies the change to the owner player.
        """
        resourcetype = StringField(value='requisition', keyname='resourcetype',
                               displayname='Resource Type', helpstring='Resource Type')
        takeresources = BooleanField(value=False, keyname='takeresources',
                               displayname='Take Resources', helpstring='Take resources away from the player')
                               
        @input(inputname='GiveResources', helpstring='Give resources to a player.', fieldtype=fieldtypes.FIELD_INTEGER)
        def InputGiveResources(self, inputdata):
            """Add or remove the specified amount of the configured resource.
            
            Args:
                inputdata: Hammer input data whose integer value is the amount
                    of resources to change (positive integer).
            """
            if self.takeresources:
                TakeResources(self.GetOwnerNumber(), [(self.resourcetype, inputdata.value.Int())])
            else:
                GiveResources(self.GetOwnerNumber(), [(self.resourcetype, inputdata.value.Int())])