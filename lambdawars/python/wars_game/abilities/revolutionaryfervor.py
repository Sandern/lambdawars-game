from core.abilities import AbilityBase
from particles import *

class AbilityRevolutionaryFervor(AbilityBase):
    name = 'revolutionaryfervor'
    displayname = "#RebRevFervor_Name"
    description = "#RebRevFervor_Description"
    image_name = 'vgui/rebels/abilities/revolutionaryfervor'
    hidden = True # Hidden from abilitypanel
    accuracybonus = 0.1
    
    @classmethod
    def SetupOnUnit(info, unit):
        super().SetupOnUnit(unit)
        
        if not hasattr(unit, 'revolutionaryfervornextcheck'):
            unit.revolutionaryfervoractive = False
            unit.revolutionaryfervornextcheck = gpGlobals.curtime + 0.5
    
    @classmethod
    def OnUnitThink(info, unit):
        active = unit.revolutionaryfervoractive
            
        if unit.revolutionaryfervornextcheck > gpGlobals.curtime:
            return
            
        #if len(unit.senses.GetOthers(unit.unitinfo.name)) < 4:
        if len([unit for unit in unit.senses.GetOthers() if 'revolutionaryfervor' in unit.unitinfo.abilities.values()]) < 4:
            if unit.revolutionaryfervoractive:
                unit.accuracy -= info.accuracybonus
                unit.overrideaccuracy = unit.accuracy # Let client know
                unit.revolutionaryfervoractive = False
                unit.revolutionaryfervornextcheck = gpGlobals.curtime + 0.5
            return
        
        if not unit.revolutionaryfervoractive:
            unit.accuracy += info.accuracybonus
            unit.overrideaccuracy = unit.accuracy # Let client know
            unit.revolutionaryfervoractive = True
            unit.revolutionaryfervornextcheck = gpGlobals.curtime + 0.5
            