from basetf import UnitBaseTF as BaseClass
from core.units.abilities import AbilitySwitchWeapon
from core.units import UnitInfo
from entities import entity

class BatInfo(AbilitySwitchWeapon):
    name = "bat"
    image_name = 'vgui/abilities/ability_unknown.vmt'
    weapon = 'tf_weapon_bat'
    
class ScatterGunInfo(AbilitySwitchWeapon):
    name = "scattergun"
    image_name = 'vgui/abilities/ability_unknown.vmt'
    weapon = 'tf_weapon_scattergun'

@entity('unit_scout', networked=True)
class UnitScout(BaseClass):
    """ Team Fortress 2 Scout unit """
    def ModifyOrAppendCriteria(self, critset):
        super(UnitScout, self).ModifyOrAppendCriteria(critset)

        critset.AppendCriteria('IsScout', '1')
        
    def Spawn(self):
        super(UnitScout, self).Spawn()
        
        self.locomotion.supportdoublejump = True
        
    # Vars
    maxspeed = 400.0
    yawspeed = 40.0
    jumpheight = 116.0 # 116 double, 72 normal.
    
    hatpaths = [
        'models/player/items/all_class/',
        'models/player/items/scout/',
    ]
    
    # Animation translation table
    acttables = dict(BaseClass.acttables)
    acttables.update( {
        'tf_weapon_bat' : acttables['tf_weapon_melee'],
        'tf_weapon_scattergun' : acttables['tf_weapon_range'],
    } )

# Register unit
class UnitScoutInfo(UnitInfo):
    name = "unit_scout"
    cls_name = "unit_scout"
    displayname = "#TF_Scout_Name"
    description = "#TF_Scout_Description"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/player/scout.mdl'
    hulltype = 'HULL_HUMAN'
    health = 95
    weapons = ['tf_weapon_scattergun', 'tf_weapon_bat']
    
    sound_select = 'Scout.Yes01'
    sound_move = 'Scout.Taunts01'
    sound_attack = 'Scout.BattleCry01'
    sound_jump = 'Scout.ApexofJump01'
    sound_death = 'Scout.CritDeath'
    
    abilities = {
        0 : 'bat',
        1 : 'scattergun',
        8 : 'attackmove',
        9 : 'holdposition',
    }