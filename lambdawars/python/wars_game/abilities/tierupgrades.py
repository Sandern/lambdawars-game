from core.abilities import AbilityUpgrade, AbilityUpgradePopCap

class Tier2UpgradeInfo(AbilityUpgradePopCap):
    name = 'or_tier2_research'
    displayname = '#AbilityTier2Research_Name'
    description = '#AbilityTier2Research_Description'
    image_name = "vgui/abilities/tier2combine.vmt"
    buildtime = 0.0
    costs = [('kills', 100)]
    successorability = 'or_tier3_research'
    providespopulation = 25
    
class Tier3UpgradeInfo(AbilityUpgradePopCap):
    name = 'or_tier3_research'
    displayname = '#AbilityTier3Research_Name'
    description = '#AbilityTier3Research_Description'
    image_name  = "vgui/abilities/tier3combine.vmt"
    buildtime = 0.0
    costs = [('kills', 200)]
    providespopulation = 50