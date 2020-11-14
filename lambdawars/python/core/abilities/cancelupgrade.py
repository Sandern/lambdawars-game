from .instant import AbilityInstant

class AbilityCancel(AbilityInstant): 
    name = 'cancelupgrade'
    displayname = '#AbilityCancelUpgrade_Name'
    description = '#AbilityCancelUpgrade_Desc'
    image_name = 'vgui/abilities/cancel'

    if isserver:
        def DoAbility(self): 
            self.SelectGroupUnits()
            if not self.units:
                self.Cancel()
                return
            for unit in self.units:
                if hasattr(unit, 'CancelUpgrade'):
                    unit.CancelUpgrade()
                else:
                    PrintWarning('AbilityCancel: %s - Unit has no CancelUpgrade method!\n' % (unit))
            self.Completed()
        
    @classmethod
    def ShouldShowAbility(info, unit):
        if unit.constructionstate != unit.BS_UPGRADING:
            return False
        return True