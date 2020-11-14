#from core.abilities import AbilityBase
from core.abilities import AbilityInstant

class AbilityOnHealedExit(AbilityInstant):
    name = 'onhealedexit'
    displayname = "#AbiOnHealedExit_Name"
    description = "#AbiOnHealedExit_Description"
    image_name = 'vgui/rebels/abilities/rebel_leave_on_full_health'
    hidden = True # Hidden from abilitypanel
    supportsautocast = True
    
    @classmethod
    def OnUnitThink(info, building):
        if not building.abilitycheckautocast[info.uid]:
            return
    
        for unit in list(building.units):
            if unit.health >= unit.maxhealth:
                building.UnGarrisonUnit(unit)

    def DoAbility(self):
        if isserver:
            building = self.SelectSingleUnit()
            for unit in list(building.units):
                if unit.health >= unit.maxhealth:
                    building.UnGarrisonUnit(unit)
        