from core.abilities import AbilityAsAnimation
from fields import FloatField


class AbilityDispel(AbilityAsAnimation):
    # Info
    name = "dispel"
    rechargetime = 3.0
    energy = 80
    displayname = "#RebDispel_Name"
    description = "#RebDispel_Description"
    image_name = 'vgui/rebels/abilities/dispel'
    hidden = True

    dispel_anim_speed = FloatField(value=1.75)
    
    supportsautocast = True
    defaultautocast = False
    autocastcheckonenemy = True

    sai_hint = AbilityAsAnimation.sai_hint | set(['sai_deploy']) # doesn't work as ability that can be used as grenade

    # Ability
    def DoAnimation(self, unit):
        unit.DoAnimation(unit.ANIM_VORTIGAUNT_DISPEL, data=round(self.dispel_anim_speed * 255))

    @classmethod
    def CheckAutoCast(info, unit):
        if not info.CanDoAbility(None, unit=unit):
            return False
        if unit.senses.CountEnemiesInRange(unit.DISPELRANGE_SENSE) > 4:
            unit.DoAbility(info.name)
            return True
        return False
