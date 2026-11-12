"""Temporary migration of all the squad wars jank.

Uses all the main data from factions.py
"""
from vmath import Vector
from wars_game.factions import SquadWarsRebelInfo, SquadWarsCombineInfo


class SquadWarsRebelSoldier(SquadWarsRebelInfo):
    name = "swf_rebel_soldier"
    displayname = '#CharRebSoldier_Name'
    startunit = 'char_rebel_soldier'
    color = Vector(1.0, 0.509, 0.129)


class SquadWarsRebelFlamer(SquadWarsRebelInfo):
    name = 'swf_rebel_flamer'
    displayname = '#CharRebFlamer_Name'
    startunit = 'char_rebel_flamer'
    color = Vector(1.0, 0.161, 0.321)


class SquadWarsRebelMedic(SquadWarsRebelInfo):
    name = 'swf_rebel_medic'
    displayname = '#CharRebMedic_Name'
    startunit = 'char_rebel_medic'
    color = Vector(0.596, 0.941, 0.301)


class SquadWarsRebelEngineer(SquadWarsRebelInfo):
    name = 'swf_rebel_engineer'
    displayname = '#CharRebEngineer_Name'
    startunit = 'char_rebel_engineer'
    color = Vector(0.955, 0.878, 0.156)


class SquadWarsRebelVeteran(SquadWarsRebelInfo):
    name = 'swf_rebel_veteran'
    displayname = '#CharRebVeteran_Name'
    startunit = 'char_rebel_veteran'
    color = Vector(0.454, 0.423, 0.227)


class SquadWarsRebelScout(SquadWarsRebelInfo):
    name = 'swf_rebel_scout'
    displayname = '#CharRebScout_Name'
    startunit = 'char_rebel_scout'
    color = Vector(0.478, 0.552, 0.227)


class SquadWarsRebelRPG(SquadWarsRebelInfo):
    name = 'swf_rebel_rpg'
    displayname = '#CharRebRPG_Name'
    startunit = 'char_rebel_rpg'
    color = Vector(0.882, 0.568, 0.227)


class SquadWarsCombineSoldier(SquadWarsCombineInfo):
    name = 'swf_combine_soldier'
    displayname = '#CharCombAssault_Name'
    startunit = 'char_combine_soldier'
    color = Vector(0.533, 0.713, 1.0)


class SquadWarsCombineEliteSoldier(SquadWarsCombineInfo):
    name = 'swf_combine_elite'
    displayname = '#CharCombElite_Name'
    startunit = 'char_combine_elite'
    color = Vector(0.921, 0.921, 1.0)


class SquadWarsMetropoliceSupport(SquadWarsCombineInfo):
    name = 'swf_metropolice_support'
    displayname = '#CharMetroSupport_Name'
    startunit = 'char_metropolice_support'
    color = Vector(0.784, 0.784, 1.0)


class SquadWarsMetropoliceScout(SquadWarsCombineInfo):
    name = 'swf_metropolice_scout'
    displayname = '#CharMetroScout_Name'
    startunit = 'char_metropolice_scout'
    color = Vector(0.588, 0.941, 0.804)


class SquadWarsMetropoliceTank(SquadWarsCombineInfo):
    name = 'swf_metropolice_tank'
    displayname = '#CharMetroTank_Name'
    startunit = 'char_metropolice_tank'  # Don't forget about char_metropolice_tank_smg1
    color = Vector(0.807, 0.392, 1.0)
