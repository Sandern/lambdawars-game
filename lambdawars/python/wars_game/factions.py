''' Faction definitions for Lambda Wars.

    These structures define the information of a faction, such as which HUD to display
    and which starting building and unit to spawn.
'''

from vmath import Vector
from core.factions import FactionInfo
from core.units import CreateUnitFancy, CreateUnitNoSpawn, PrecacheUnit
from core.buildings import UnitBaseBuilding, CreateDummy
from particles import PrecacheParticleSystem
if isserver: 
    from entities import DispatchSpawn

class WarsFactionInfo(FactionInfo):
    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()
            
            for fortifyunittype in info.fortifyunittypes.values():
                PrecacheUnit(fortifyunittype)
                
    #: Control point model definition.
    #: Defines model information for each possible upgrade level.
    fortifyunittypes = {}
    
    #: Overrun hud html file
    overrunhud_htmlfile = 'ui/viewport/wars/overrun_rebels.html'

class FactionAntlionInfo(WarsFactionInfo):
    name = 'antlions'
    displayname = 'Antlions'
    hud_name = 'classic_hud'
    startbuilding = 'build_ant_colony'
    startunit = 'unit_antlionguard'
    resources = ['grubs']
    
    @classmethod
    def PopulateStartSpot(info, gamerules, startspot, ownernumber, playerSteamID=None):
        if not info.startbuilding or not info.startunit:
            PrintWarning('Faction %s has no start building or unit specified! Unable to populate start spot.\n')
            return
            
        # Spawn start building
        if info.startbuilding:
            unit = CreateUnitNoSpawn(info.startbuilding)
            unit.SetAbsOrigin(startspot.GetAbsOrigin())
            unit.SetAbsAngles(startspot.GetAbsAngles())
            unit.SetOwnerNumber(ownernumber)
            unit.KeyValue('startgrubs', 10)  # TODO: move to antlion gamerules
            DispatchSpawn(unit)
            unit.Activate()  
        
        # Spawn a start unit
        if info.startunit:
            CreateUnitFancy(info.startunit, startspot.GetAbsOrigin()+Vector(270, 0, 48), owner_number=ownernumber, angles=startspot.GetAbsAngles())
        
class FactionCombineInfo(WarsFactionInfo):
    name = 'combine'
    displayname = 'Combine'
    hud_name = 'combine_hud'
    startbuilding = 'build_comb_hq'
    startunit = 'unit_stalker'
    resources = ['requisition', 'power']
    announcer_cp_captured = 'announcer_combine_control_point_captured'
    announcer_cp_lost = 'announcer_combine_control_point_lost'
    announcer_cp_under_attack = 'announcer_combine_control_point_under_attack'
    announcer_unit_completed = 'announcer_combine_unit_complete'
    announcer_research_completed = 'combine_unit_researchcomplete'
    announcer_more_population_required = 'announcer_combine_more_population_required'
    announcer_unit_under_attack = 'announcer_combine_unit_under_attack'
    announcer_building_under_attack = 'announcer_combine_building_under_attack'
    color = Vector(0.1, 0.6, 0.9) 
    victoryparticleffect = 'pg_comb_victory'
    defeatparticleffect = 'pg_comb_defeat'
    
    # Model configuration for control point fortification
    fortifyunittypes = {
        1 : 'control_point_comb_lvl1',
        2 : 'control_point_comb_lvl2',
    }
    
    overrunhud_htmlfile = 'ui/viewport/wars/overrun_combine.html'
    
class FactionRebelsInfo(WarsFactionInfo):
    name = 'rebels'
    displayname = 'Rebels'
    hud_name = 'rebels_hud'
    startbuilding = 'build_reb_hq'
    startunit = 'unit_rebel_engineer'
    resources = ['requisition', 'scrap', 'power']
    announcer_cp_captured = 'announcer_rebel_control_point_captured'
    announcer_cp_lost = 'announcer_rebel_control_point_lost'
    announcer_cp_under_attack = 'announcer_rebel_control_point_under_attack'
    announcer_research_completed = 'announcer_rebel_researchcomplete'
    announcer_more_population_required = 'announcer_rebel_more_population_required'
    announcer_unit_completed = 'announcer_rebel_unit_complete'
    announcer_unit_under_attack = 'announcer_rebel_unit_under_attack'
    announcer_building_under_attack = 'announcer_rebel_building_under_attack'
    color = Vector(0.9, 0.6, 0.1)
    victoryparticleffect = 'pg_reb_victory'
    defeatparticleffect = 'pg_reb_defeat'
    
    # Model configuration for control point fortification
    fortifyunittypes = {
        1 : 'control_point_reb_lvl1',
        2 : 'control_point_reb_lvl2',
    }
    
    overrunhud_htmlfile = 'ui/viewport/wars/overrun_rebels.html'
    
class FactionCombineOverrunInfo(FactionCombineInfo):
    name = 'overrun_combine'
    displayname = 'Combine'
    hud_name = 'combine_hud'
    startbuilding = 'overrun_build_comb_hq'
    startunit = 'overrun_unit_stalker'
    resources = ['kills']
    gamerulespattern = '^overrun$'
    
class FactionRebelsOverrunInfo(FactionRebelsInfo):
    name = 'overrun_rebels'
    displayname = 'Rebels'
    hud_name = 'rebels_hud'
    startbuilding = 'overrun_build_reb_hq'
    startunit = 'overrun_unit_rebel_engineer'
    resources = ['kills']
    gamerulespattern = '^overrun$'
    
class FactionRebelsDestroyHQInfo(FactionRebelsInfo):
    name = 'destroyhq_rebels'
    displayname = 'Rebels'
    hud_name = 'rebels_hud'
    startbuilding = 'build_reb_hq'
    startunit = 'unit_rebel_engineer'
    resources = ['requisition', 'scrap', 'power']
    
class FactionCombineDestroyHQInfo(FactionCombineInfo):
    name = 'destroyhq_combine'
    displayname = 'Combine'

class FactionSquadWarsInfo(WarsFactionInfo):
    name = 'squad_wars'
    displayname = 'Squad Wars'
    hud_name = 'classic_hud'
    startbuilding = 'build_sw_beacon'
    startunit = ''
    resources = ['power_sw']
    gamerulespattern = ['^squadwars$']


class SquadWarsRebelInfo(FactionInfo):
    #name = 'sw_rebel_soldier'
    displayname = ''
    hud_name = 'rebels_hud'
    startbuilding = 'build_reb_barricade'
    startunit = ''
    resources = ['power_sw']
    color = Vector(1.0, 1.00, 1.00)
    victoryparticleffect = 'pg_reb_victory'
    defeatparticleffect = 'pg_reb_defeat'


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


class SquadWarsCombineInfo(SquadWarsRebelInfo):
    hud_name = 'combine_hud'
    startbuilding = 'build_comb_barricade'
    victoryparticleffect = 'pg_comb_victory'
    defeatparticleffect = 'pg_comb_defeat'


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
