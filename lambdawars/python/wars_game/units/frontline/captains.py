"""Frontline captain unit infos (skeletons).

TODO: work with stats to balance it out for comfortable gameplay experience.
"""
from core.units.abilities import AbilityTransformUnit
from core.units import UnitBase
from wars_game.units.rebel import (UnitRebelEngineer, CharacterRebelFlamer, 
                                   CharacterRebelMedic, CharacterRebelScout, 
                                   CharacterRebelSoldier, CharacterRebelVeteran, RebelEngineerInfo)
from wars_game.units.combine import CharacterCombineSoldier, CharacterEliteSoldier
from wars_game.units.metropolice import (CharacterMetroPoliceScout, CharacterMetroPoliceSupport, 
                                        CharacterMetroPoliceTank, CharacterMetroPoliceTankSMG, UnitInfo as PoliceUnitInfo)
from wars_game.units.citizen import UnitInfo as HumanUnitInfo
from wars_game.units.stalker import StalkerShared, StalkerInfo, UnitStalker


# Avoid importing heavy unit modules at collection time until you wire clones.
# Pattern to follow (see wars_game.units.rebel / stalker):
@entity('unit_cpt_engineer', networked=True)
class UnitEngineerCaptain(UnitRebelEngineer):
    constructmaxrange = 5


@entity('unit_cpt_medic', networked=True)
class UnitMedicCaptain(CharacterRebelMedic):
    recharge_other_abilities = []
    abilities = {
        0: 'heal',
        1: 'passivehealing_indicator',
        2: 'stun_frag',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    techrequirements = ['build_reb_triagecenter']


class CptRebelEngineerInfo(RebelEngineerInfo):
    name = 'unit_cpt_engineer'
    displayname = '#CptEngineer_Name'
    hidden = True  # or False once Frontline-only
    costs = []
    attributes = ['medium']
    population = 0


class CptRebelFlamer(CharacterRebelFlamer):
    name = 'unit_cpt_flamer'
    hidden = True
    costs = []
    attributes = ['medium']
    recharge_other_abilities = []
    techrequirements = ['build_reb_specialops']
    health = 400
    population = 0


class CptRebelScout(CharacterRebelScout):
    name = 'unit_cpt_scout'
    hidden = True
    costs = []
    attributes = ['medium']
    recharge_other_abilities = []
    health = 150
    population = 0


@entity('unit_cpt_stalker')
class CptUnitStalker(UnitStalker):
    """Stalker for Frontline gamemode"""
    class AttackRange(UnitInfo.AttackRange):
        damage = 10
        damagetype = DMG_SHOCK
        attackspeed = 0.0
        maxrange = 900.0
        cone = 0.9986295347546

    constructmaxrange = 320.0


class CptStalkerInfo(StalkerInfo):
    name = 'unit_cpt_stalker'
    cls_name = 'unit_cpt_stalker'
    costs = []
    maxspeed = 112.0
    hidden = True
    population = 0


class CptMetroPoliceScout(CharacterMetroPoliceScout):
    name = 'unit_cpt_metropolice_scout'
    maxspeed = 234
    health = 300
    costs = [{'overwatch': 5}]
    population = 0
    attributes = ['light']
    tier = 0
    abilities = {
        -1: 'garrison',
        0: 'deployscanner',
        1: 'scan_char',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_smg1']
    recharge_other_abilities = []
    rechargetime = 180.0


class CptMetroPoliceTank(CharacterMetroPoliceTank):
    name = 'unit_cpt_metropolice_tank'
    displayname = '#CharMetroTank_Name'
    description = '#CharMetroTank_Description'
    maxspeed = 250
    viewdistance = 600
    health = 450
    costs = [{'overwatch': 10}]
    techrequirements = []
    population = 0
    attributes = ['medium']
    tier = 0
    abilities = {
        0: 'deploymanhack',
        1: 'cpt_mp_transform_smg1',
        2: 'defensive_mode',
        3: 'attack_mode',
        5: 'riot_station',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = []
    rechargetime = 180.0
    useshield = True


class CptMetroPoliceTankSMG(CptMetroPoliceTank):
    name = 'unit_cpt_metropolice_tank_smg1'
    maxspeed = 226
    viewdistance = 800
    health = 450
    population = 0
    attributes = ['medium']
    abilities = {
        0: 'deploymanhack',
        1: 'cpt_mp_transform_tank',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['weapon_smg1']
    useshield = True


class CptMetroPoliceSupport(CharacterMetroPoliceSupport):
    name = 'unit_cpt_metropolice_support'
    attributes = ['light']
    costs = [{'overwatch': 12}]
    population = 0
    maxspeed = 236
    health = 320
    abilities = {
        -2: 'garrison',
        -1: 'construct_floorturret',
        0: 'deploymanhack',
        1: 'floor_turret',
        2: 'cpt_combine_mine',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }


class TransformToMetropoliceTankSMG1(AbilityTransformUnit):
    name = 'cpt_mp_transform_smg1'
    displayname = '#CombTransMPSMG1_Name'
    description = '#CombTransMPSMG1_Description'
    transform_type = 'unit_cpt_metropolice_tank_smg1'
    transform_time = 6.0
    replaceweapons = True
    techrequirements = ['build_comb_armory']
    costs = []
    image_name = 'vgui/combine/units/unit_metropolice_smg'
    activatesoundscript = 'ability_combine_smg1_upgrade'


class TransformToMetropoliceTank(AbilityTransformUnit):
    name = 'cpt_mp_transform_tank'
    displayname = '#CombTransMPSMG1_Name'
    description = '#CombTransMPSMG1_Description'
    transform_type = 'unit_cpt_metropolice_tank'
    transform_time = 6.0
    replaceweapons = True
    techrequirements = ['build_comb_armory']
    costs = []
    image_name = 'vgui/combine/units/unit_riot_police'
    activatesoundscript = "Weapon_StunStick.Activate"


class CptCombineSoldier(CharacterCombineSoldier):
    name = 'unit_cpt_combine_soldier'
    costs = [{'overwatch': 13}]
    population = 0
    attributes = ['medium']
