from core.abilities import AbilityInstant
from fields import FloatField
if isserver:
    from core.units import BaseBehavior

class AbilitySlamGround(AbilityInstant):
    # Info
    name = "slamground"
    rechargetime = 4.5
    energy = 25
    displayname = "#RebSlamGround_Name"
    description = "#RebSlamGround_Description"
    image_name = 'vgui/rebels/abilities/rebel_dog_ground_slam'
    hidden = True
    
    defaultautocast = True
    autocastcheckonenemy = True
    
    autocast_slamgroundrange = FloatField(value=192.0)

    sai_hint = AbilityInstant.sai_hint | set(['sai_deploy'])
    
    # Ability
    def DoAbility(self):
        self.SelectGroupUnits()
        units = self.TakeEnergy(self.units)
        for unit in units:
            unit.DoAnimation(unit.ANIM_SLAMGROUND)
            unit.AbilityOrder(ability=self)
        self.SetRecharge(units)
        self.Completed()
        
    @classmethod
    def CheckAutoCast(info, unit):
        if not info.CanDoAbility(None, unit=unit):
            return False
        if unit.senses.CountEnemiesInRange(info.autocast_slamgroundrange) > 2:
            unit.DoAbility(info.name)
            return True
        return False
        
    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbilityWaitForActivity
        
    # This ability object won't be created on the executing client
    serveronly = True