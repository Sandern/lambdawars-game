from core.abilities import AbilityAsAnimation
from fields import FloatField

class AbilitySlamGround(AbilityAsAnimation):
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

    sai_hint = AbilityAsAnimation.sai_hint | set(['sai_deploy'])
    
    # Ability
    def DoAnimation(self, unit):
        unit.DoAnimation(unit.ANIM_SLAMGROUND, data=round(1.5 * 255))
        
    @classmethod
    def CheckAutoCast(info, unit):
        if not info.CanDoAbility(None, unit=unit):
            return False
        if unit.senses.CountEnemiesInRange(info.autocast_slamgroundrange) > 2:
            unit.DoAbility(info.name)
            return True
        return False