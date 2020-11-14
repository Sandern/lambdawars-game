from core.abilities import AbilityInstant
if isserver:
    from core.units import BaseBehavior

class AbilityPullGrenade(AbilityInstant):
    # Info
    name = "pullgrenade"
    rechargetime = 2.5
    displayname = "#ZombPullGrenade_Name"
    description = "#ZombPullGrenade_Description"
    #image_name = 'vgui/rebels/abilities/dispel'
    hidden = True
    
    defaultautocast = True
    checkautocastinenemyrange = 300.0
    autocastcheckonenemy = True
    
    # Ability
    def DoAbility(self):
        self.SelectGroupUnits()
        units = self.TakeEnergy(self.units)
        for unit in units:
            if unit.grenade:
                continue
            unit.DoAnimation(unit.ANIM_ZOMBINE_PULLGRENADE)
            self.AbilityOrderUnits(unit, ability=self)
        self.SetRecharge(units)
        self.Completed()
        
    @classmethod
    def CheckAutoCast(info, unit):
        if not info.CanDoAbility(None, unit=unit):
            return False
        if unit.senses.CountEnemiesInRange(320.0) > 3:
            unit.DoAbility(info.name, autocasted=True)
            return True
        return False
        
    if isserver:
        behaviorgeneric_action = BaseBehavior.ActionAbilityWaitForActivity
        
    # This ability object won't be created on the executing client
    serveronly = True