from .instant import AbilityInstant

class AbilityHoldPosition(AbilityInstant):
    # Info
    name = "holdposition"
    image_name = 'vgui/abilities/holdposition.vmt'
    rechargetime = 0
    displayname = "#AbilityHoldPosition_Name"
    description = "#AbilityHoldPosition_Description"
    hidden = True
    activatesoundscript = '#holdposition'
    activatesoundscript_force_play = False
    cloakallowed = True
    
    # Ability
    def Init(self):
        self.SelectGroupUnits()
        
        super().Init()
    
    def DoAbility(self):
        if isserver:
            from core.units import BehaviorGeneric # FIXME
            self.behaviorgeneric_action = BehaviorGeneric.ActionHoldPosition

        for unit in self.units:
            if unit.in_cover:
                # Units in cover are already holding positions, with an added bonus
                continue
            self.AbilityOrderUnits(unit, ability=self)
        
        if isserver:
            self.Completed()
