
if isserver:
    from entities import CBaseFilter, entity
    from fields import IntegerField, StringField, BooleanField, TargetSrcField
    
    @entity('filter_owner',
            iconsprite='editor/filter_name.vmt')
    class OwnerFilter(CBaseFilter):
        ''' Filters on the owner of the entity.'''
        def PassesFilterImpl(self, caller, entity):
            if entity.GetOwnerNumber() != self.GetOwnerNumber():
                return False
            return True
            
    @entity('filter_unittype',
            iconsprite='editor/filter_name.vmt')
    class UnitTypeFilter(CBaseFilter):
        ''' Filters on unit type. '''
        def PassesFilterImpl(self, caller, entity):
            if not entity.IsUnit():
                return False
            if entity.unitinfo.name != self.unittype:
                return False
            return True
            
        unittype = StringField(value='', keyname='unittype',
                               displayname='Unit Type', helpstring='Unit Type')
                               
    @entity('filter_item',
            iconsprite='editor/filter_name.vmt',
            base=['BaseFilter', 'Wars', 'Targetname'])
    class ItemFilter(CBaseFilter):
        ''' Filters on the target item. '''
        def PassesFilterImpl(self, caller, entity):
            if not entity.IsUnit():
                return False
                
            # Test if the entity is the target item
            if not self.mustbecarried:
                name = entity.GetEntityName()
                if name and self.HasTarget(name):
                    return True
                
            # Test if it's an unit carrying items
            items = getattr(entity, 'items', None)
            if items == None:
                return False
            for item in items:
                name = item.GetEntityName()
                if name and self.HasTarget(name):
                    return True
            return False
            
        mustbecarried = BooleanField(value=False, keyname='mustbecarried', displayname='Must be carried', helpstring='Item must be carried by the unit (i.e. not on the floor)')
        targetitem = TargetSrcField(value='', keyname='target', displayname='Filter Item', helpstring='Name of item to filter on.', cppimplemented=True)