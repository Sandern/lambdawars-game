from .instant import AbilityInstant

class AbilityCancel(AbilityInstant): 
    name = 'cancel'
    displayname = '#AbilityCancel_Name'
    description = '#AbilityCancel_Desc'
    image_name = 'vgui/abilities/cancel'

    if isserver:
        def DoAbility(self): 
            self.SelectGroupUnits()
            if not self.units:
                self.Cancel()
                return
            # Create copy of list, as canceled buildings being constructed will destroy
            # the entity, which will modify the units list in place
            for unit in list(self.units):
                if hasattr(unit, 'Cancel'):
                    unit.Cancel()
                else:
                    PrintWarning('AbilityCancel: %s - Unit has no Cancel method!\n' % unit)
            self.Completed()
        
    @classmethod
    def ShouldShowAbility(info, unit):
        if unit.constructionstate == unit.BS_CONSTRUCTED:
            return False
        return True