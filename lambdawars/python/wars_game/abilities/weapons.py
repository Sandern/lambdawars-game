from core.abilities import AbilityUpgrade
from core.units.abilities import AbilitySwitchWeapon


# Unlock upgrades for ar2 and sg weapons
class WeaponAr2Unlock(AbilityUpgrade):
    name = 'weaponar2_unlock'
    displayname = '#WeaponAr2Unlock_Name'
    description = '#WeaponAr2Unlock_Description'
    image_name = "vgui/abilities/weaponar2_unlock"
    #techrequirements = ['rebel_upgrade_tier_mid']
    buildtime = 72.0
    costs = [[('kills', 5)], [('requisition', 20), ('scrap', 25)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])


class WeaponAr2CombUnlock(WeaponAr2Unlock):
    name = 'weaponar2_comb_unlock'
    #techrequirements = ['combine_upgrade_tier_mid']
    costs = [[('kills', 5)], [('requisition', 20), ('power', 20)]]


class WeaponSGUnlock(AbilityUpgrade):
    name = 'weaponsg_unlock'
    displayname = '#WeaponSGUnlock_Name'
    description = '#WeaponSGUnlock_Description'
    image_name = "vgui/abilities/weaponsg_unlock"
    #techrequirements = ['rebel_upgrade_tier_mid']
    buildtime = 45.0
    costs = [[('kills', 5)], [('requisition', 25), ('scrap', 15)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])

class WeaponSGCombUnlock(WeaponSGUnlock):
    name = 'weaponsg_comb_unlock'
    #techrequirements = ['combine_upgrade_tier_mid']
    costs = [[('kills', 5)], [('requisition', 25), ('power', 10)]]


# Switch abilities that require the above abilities
class WeaponSwitchAr2Info(AbilitySwitchWeapon):
    name = 'weaponswitch_ar2'
    displayname = '#WeaponAR2Switch_Name'
    description = '#WeaponAR2Switch_Description'
    image_name = 'vgui/abilities/weaponswitch_ar2'
    weapon = 'weapon_ar2'
    switch_weapon_time = 1.0
    #techrequirements = ['weaponar2_unlock']

class WeaponSwitchAR2CharInfo(WeaponSwitchAr2Info):
    name = 'weaponswitch_ar2_char'
    techrequirements = []
    switch_weapon_time = 1.0


class WeaponSwitchSGInfo(AbilitySwitchWeapon):
    name = 'weaponswitch_shotgun'
    displayname = '#WeaponSGSwitch_Name'
    description = '#WeaponSGSwitch_Description'
    image_name = 'vgui/abilities/weaponswitch_shotgun'
    weapon = 'weapon_shotgun'
    switch_weapon_time = 1.0
    techrequirements = ['weaponsg_comb_unlock']

class WeaponsSwitchSGCharInfo(WeaponSwitchSGInfo):
    name = 'weaponswitch_shotgun_char'
    techrequirements = []
    switch_weapon_time = 1.0

class WeaponSwitchSGInfoOverrun(AbilitySwitchWeapon):
    name = 'weaponswitch_shotgun_overrun'
    displayname = '#WeaponSGSwitch_Name'
    description = '#WeaponSGSwitch_Description'
    image_name = 'vgui/abilities/weaponswitch_shotgun'
    weapon = 'weapon_shotgun'
    switch_weapon_time = 2.0
    techrequirements = []
