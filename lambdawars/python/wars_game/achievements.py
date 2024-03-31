from srcbuiltins import RegisterTickMethod, IsTickMethodRegistered
from core.dispatch import receiver
from core.signals import endgame, map_endgame, unitkilled_by_attacker, abilitycompleted_by_name
from core.units import unitlistpertype
from wars_game.gamerules import AnnihilationInfo, DestroyHQInfo, OverrunInfo
from core.gamerules.mission import MissionInfo

from achievements import *
from gamerules import gamerules

from collections import defaultdict

# Some common methods to test if we allow testing for the achievement
__competitivemodes = set([AnnihilationInfo.name, DestroyHQInfo.name])
__commonmodes = set([AnnihilationInfo.name, DestroyHQInfo.name, OverrunInfo.name])
__missionmodes = set([MissionInfo.name])

def IsCompetitiveGameMode():
    return gamerules.info.name in __competitivemodes

def IsCommonGameMode():
    return gamerules.info.name in __commonmodes

def IsMissionGameMode():
    return gamerules.info.name in __missionmodes

def IsAbilityValid(ability):
    # Not executed in the regular way. For example, spawning an unit in Sandbox.
    if ability.ischeat:
        return False
    return True

if isserver:
    from playermgr import ListPlayersForOwnerNumber

    # Achievements for completing single player maps
    @receiver(map_endgame['tutorial_annihilation_rebels'])
    def OnEndTutorial(gamerules, winners, losers, *args, **kwargs):
        if not IsMissionGameMode():
            return

        for player in gamerules.GetGamePlayers(winners):
            player.AwardAchievement(ACHIEVEMENT_WARS_GRADUATED)

    @receiver(map_endgame['sp_radio_tower'])
    def OnEndGameRadioTower(gamerules, winners, losers, *args, **kwargs):
        if not IsMissionGameMode():
            return

        for player in gamerules.GetGamePlayers(winners):
            player.AwardAchievement(ACHIEVEMENT_WARS_MISSION_RADIO_TOWER)

    @receiver(map_endgame['sp_abandoned'])
    def OnEndGameAbandoned(gamerules, winners, losers, *args, **kwargs):
        if not IsMissionGameMode():
            return

        for player in gamerules.GetGamePlayers(winners):
            player.AwardAchievement(ACHIEVEMENT_WARS_MISSION_ABANDONED)
            
    @receiver(map_endgame['sp_valley'])
    def OnEndGameValley(gamerules, winners, losers, *args, **kwargs):
        if not IsMissionGameMode():
            return

        for player in gamerules.GetGamePlayers(winners):
            player.AwardAchievement(ACHIEVEMENT_WARS_MISSION_VALLEY)

    @receiver(map_endgame['sp_waste'])
    def OnEndGameWaste(gamerules, winners, losers, *args, **kwargs):
        if not IsMissionGameMode():
            return

        for player in gamerules.GetGamePlayers(winners):
            player.AwardAchievement(ACHIEVEMENT_WARS_MISSION_WASTE)

    # The clash achievement. Check if it was a 4vs4 game, and one team was rebels and 
    # other team combine. The winning team is awarded with an achievement.
    @receiver(endgame)
    def OnEndGameTheClashAchievement(gamerules, winners, losers, *args, **kwargs):
        if not IsCommonGameMode():
            return
            
        # Must be a 4 vs 4 match
        if len(winners) != 4 or len(losers) != 4:
            return
            
        # One team must be all rebels, one team must be all combine
        winnersfactions = list(set([playerdata.get('faction', None) for playerdata in winners]))
        losersfactions = list(set([playerdata.get('faction', None) for playerdata in losers]))
        
        allcombine = (len(winnersfactions) == 1 and winnersfactions[0] == 'combine') or (len(losersfactions) == 1 and losersfactions[0] == 'combine')
        allrebels = (len(winnersfactions) == 1 and winnersfactions[0] == 'rebels') or (len(losersfactions) == 1 and losersfactions[0] == 'rebels')
        if not allcombine or not allrebels:
            return
        
        # Award the achievement
        for player in gamerules.GetGamePlayers(winners):
            player.AwardAchievement(ACHIEVEMENT_WARS_THECLASH)
            
    # Suppression Of Dark Energy Achievement
    darkenergysuppressor_killcount = defaultdict(lambda: 0)
    
    @receiver(unitkilled_by_attacker['build_comb_mortar'])
    def KilledByDarkEnergySupressor(unit, dmginfo, *args, **kwargs):
        if not IsCommonGameMode():
            return
    
        attacker = dmginfo.GetAttacker()
        owner = attacker.GetOwnerNumber()
        darkenergysuppressor_killcount[owner] += 1
        
        if not IsTickMethodRegistered(ProcessKilledByDarkEnergySupressor):
            RegisterTickMethod(ProcessKilledByDarkEnergySupressor, 0.1, looped=False)

    def ProcessKilledByDarkEnergySupressor():
        global darkenergysuppressor_killcount
        
        # Process kill counts
        # Each AwardAchievement call sends an usermessage to the client, so
        # we don't send per killed unit (since you can kill a lot in one shot).
        for owner, killcount in darkenergysuppressor_killcount.items():
            #print('Submitting kill count %d to owner %d' % (killcount, owner))
            for player in ListPlayersForOwnerNumber(owner):
                player.AwardAchievement(ACHIEVEMENT_WARS_SUPPRESSION, killcount)
        
        # Reset
        darkenergysuppressor_killcount = defaultdict(lambda: 0)
        
    # Build 20 Strider's achievement (progress)
    @receiver(abilitycompleted_by_name['unit_strider'])
    def BuildStridersAchievement(ability, *args, **kwargs):
        if not IsCommonGameMode():
            return
        if not IsAbilityValid(ability):
            return
        for player in ListPlayersForOwnerNumber(ability.ownernumber):
            player.AwardAchievement(ACHIEVEMENT_WARS_STRIDERS)
            
    # Build 20 Dog's achievement (progress)
    @receiver(abilitycompleted_by_name['unit_dog'])
    def BuildDogsAchievement(ability, *args, **kwargs):
        if not IsCommonGameMode():
            return
        if not IsAbilityValid(ability):
            return
        for player in ListPlayersForOwnerNumber(ability.ownernumber):
            player.AwardAchievement(ACHIEVEMENT_WARS_DOG)
            
    # C4 explosive achievement. Kill off 100 buildings.
    @receiver(unitkilled_by_attacker['c4explosive_ent'])
    def KilledByC4Explosive(unit, dmginfo, *args, **kwargs):
        if not IsCommonGameMode():
            return
        if not getattr(unit, 'isbuilding', False):
            return
    
        attacker = dmginfo.GetAttacker()
        owner = attacker.GetOwnerNumber()
        
        if unit.GetOwnerNumber() == owner:
            return
        
        for player in ListPlayersForOwnerNumber(owner):
            player.AwardAchievement(ACHIEVEMENT_WARS_C4)
            
    # Friendly fire achievement
    @receiver(unitkilled_by_attacker['floor_turret'])
    def KilledByFloorTurret(unit, dmginfo, *args, **kwargs):
        if not IsCommonGameMode():
            return
        attacker = dmginfo.GetAttacker()
        if not attacker or not getattr(attacker, 'reprogrammed', False):
            return
        owner = attacker.GetOwnerNumber()
        if unit.GetOwnerNumber() == owner:
            return
        for player in ListPlayersForOwnerNumber(owner):
            player.AwardAchievement(ACHIEVEMENT_WARS_FRIENDLYFIRE)
            
    # Partisan achievement. Collect 50 partisan units in one game.
    @receiver(abilitycompleted_by_name['unit_rebel_partisan'])
    @receiver(abilitycompleted_by_name['unit_rebel_partisan_molotov'])
    @receiver(abilitycompleted_by_name['unit_citizen_barricade'])
    def CollectPartisanAchievement(ability, *args, **kwargs):
        if not IsCommonGameMode():
            return
        owner = ability.ownernumber
        if len(unitlistpertype[owner]['unit_rebel_partisan_molotov'] + unitlistpertype[owner]['unit_rebel_partisan'] + unitlistpertype[owner]['unit_citizen_barricade']) >= 50:
            for player in ListPlayersForOwnerNumber(owner):
                player.AwardAchievement(ACHIEVEMENT_WARS_PARTISAN)
