from srcbase import TEAM_INVALID, TEAM_UNASSIGNED, TEAM_SPECTATOR
from playermgr import OWNER_LAST
from core.gamerules import GamerulesInfo, WarsBaseGameRules
from utils import UTIL_GetPlayers
from core.buildings.base import priobuildinglist, constructedlistpertype
from core.resources import SetResource, ResourceInfo
from wars_game.resources import ResRequisitionInfo

class Annihilation(WarsBaseGameRules):
    def CheckGameOver(self):
        if self.gameover:   # someone else quit the game already
            # check to see if we should change levels now
            if self.intermissionendtime < gpGlobals.curtime:
                self.ChangeToGamelobby()  # intermission is over
            return True
        return False
        
    def MainThink(self):
        super().MainThink()
        if self.gameover:
            return
          
        # Check winning conditions (only one player or team left alive)
        # Only check the gamelobby players
        counts = set()
        for data in self.gameplayers:
            if self.IsPlayerDefeated(data):
                continue
            ownernumber = data['ownernumber']

            # count important buildings, including the HQ
            countunitscombhq = len([b for b in constructedlistpertype[ownernumber]['build_comb_hq'] if b.IsAlive()])
            countunitsrebhq = len([b for b in constructedlistpertype[ownernumber]['build_reb_hq'] if b.IsAlive()])
            countunitscombgar = len([b for b in constructedlistpertype[ownernumber]['build_comb_garrison'] if b.IsAlive()])
            countunitsrebbar = len([b for b in constructedlistpertype[ownernumber]['build_reb_barracks'] if b.IsAlive()])
            countunitscombmech = len([b for b in constructedlistpertype[ownernumber]['build_comb_mech_factory'] if b.IsAlive()])
            countunitsrebspecops = len([b for b in constructedlistpertype[ownernumber]['build_reb_specialops'] if b.IsAlive()])
            countunitscombspecops = len([b for b in constructedlistpertype[ownernumber]['build_comb_specialops'] if b.IsAlive()])
            countunitsrebvortden = len([b for b in constructedlistpertype[ownernumber]['build_reb_vortigauntden'] if b.IsAlive()])
            countunitscombsynth = len([b for b in constructedlistpertype[ownernumber]['build_comb_synthfactory'] if b.IsAlive()])
            countunitsrebscrapyard = len([b for b in constructedlistpertype[ownernumber]['build_reb_junkyard'] if b.IsAlive()])
            squadwarsbase = len([b for b in constructedlistpertype[ownernumber]['build_sw_beacon'] if b.IsAlive()])
            countunits = countunitscombhq + countunitsrebhq + countunitscombgar + countunitsrebbar + countunitscombmech + countunitsrebspecops + countunitscombspecops + countunitsrebvortden + countunitscombsynth + countunitsrebscrapyard + squadwarsbase
            #countunits = len([b for b in priobuildinglist[ownernumber] if b.IsAlive()])
            if not countunits:
                self.PlayerDefeated(data)
                continue
            if data['team'] is not TEAM_INVALID and data['team'] is not TEAM_UNASSIGNED and data['team'] is not TEAM_SPECTATOR:
                counts.add(data['team'])
            else:
                counts.add(data) 
                
        if len(counts) == 1:
            # We got a winner!
            winners, losers = self.CalculateWinnersAndLosers(list(counts)[0])
            self.EndGame(winners, losers)
            
    def StartGame(self):
        super().StartGame()
        
        for data in self.gameplayers:
            SetResource(data['ownernumber'], self.GetMainResource(), 100)
            
    def ClientUpdateEndGameStats(self, playersteamid, stats, winners, losers):
        ''' Update Annihilation game mode Steam stats. '''
        super().ClientUpdateEndGameStats(playersteamid, stats, winners, losers)
    
        stats.annihilation_games += 1
        if self.GetPlayerGameData(steamid=playersteamid, gameplayers=winners) != None:
            stats.annihilation_wins += 1

class SquadWars(WarsBaseGameRules):
    def CheckGameOver(self):
        if self.gameover:  # someone else quit the game already
            # check to see if we should change levels now
            if self.intermissionendtime < gpGlobals.curtime:
                self.ChangeToGamelobby()  # intermission is over
            return True
        return False

    def MainThink(self):
        super().MainThink()
        if self.gameover:
            return

        # Check winning conditions (the first team to reach 1500)
        # Only check the gamelobby players
        counts = set()
        for data in self.gameplayers:
            if self.IsPlayerDefeated(data):
                continue
            ownernumber = data['ownernumber']

            # count important buildings, including the HQ
            countunitscombhq = len([b for b in constructedlistpertype[ownernumber]['build_comb_hq'] if b.IsAlive()])
            countunitsrebhq = len([b for b in constructedlistpertype[ownernumber]['build_reb_hq'] if b.IsAlive()])
            countunitscombgar = len(
                [b for b in constructedlistpertype[ownernumber]['build_comb_garrison'] if b.IsAlive()])
            countunitsrebbar = len(
                [b for b in constructedlistpertype[ownernumber]['build_reb_barracks'] if b.IsAlive()])
            countunitscombmech = len(
                [b for b in constructedlistpertype[ownernumber]['build_comb_mech_factory'] if b.IsAlive()])
            countunitsrebspecops = len(
                [b for b in constructedlistpertype[ownernumber]['build_reb_specialops'] if b.IsAlive()])
            countunitscombspecops = len(
                [b for b in constructedlistpertype[ownernumber]['build_comb_specialops'] if b.IsAlive()])
            countunitsrebvortden = len(
                [b for b in constructedlistpertype[ownernumber]['build_reb_vortigauntden'] if b.IsAlive()])
            countunitscombsynth = len(
                [b for b in constructedlistpertype[ownernumber]['build_comb_synthfactory'] if b.IsAlive()])
            countunitsrebscrapyard = len(
                [b for b in constructedlistpertype[ownernumber]['build_reb_junkyard'] if b.IsAlive()])
            squadwarsbase = len([b for b in constructedlistpertype[ownernumber]['build_sw_beacon'] if b.IsAlive()])
            countunits = countunitscombhq + countunitsrebhq + countunitscombgar + countunitsrebbar + countunitscombmech + countunitsrebspecops + countunitscombspecops + countunitsrebvortden + countunitscombsynth + countunitsrebscrapyard + squadwarsbase
            # countunits = len([b for b in priobuildinglist[ownernumber] if b.IsAlive()])
            if not countunits:
                self.PlayerDefeated(data)
                continue
            if data['team'] is not TEAM_INVALID and data['team'] is not TEAM_UNASSIGNED and data[
                'team'] is not TEAM_SPECTATOR:
                counts.add(data['team'])
            else:
                counts.add(data)

        if len(counts) == 1:
            # We got a winner!
            winners, losers = self.CalculateWinnersAndLosers(list(counts)[0])
            self.EndGame(winners, losers)

    def StartGame(self):
        super().StartGame()

        for data in self.gameplayers:
            SetResource(data['ownernumber'], self.GetMainResource(), 100)

    def ClientUpdateEndGameStats(self, playersteamid, stats, winners, losers):
        ''' Update Annihilation game mode Steam stats. '''
        super().ClientUpdateEndGameStats(playersteamid, stats, winners, losers)

        stats.annihilation_games += 1
        if self.GetPlayerGameData(steamid=playersteamid, gameplayers=winners) != None:
            stats.annihilation_wins += 1


class AnnihilationInfo(GamerulesInfo):
    name = 'annihilation'
    displayname = '#Annihilation_Name'
    description = '#Annihilation_Description'
    cls = Annihilation
    supportcpu = True
    mappattern = '^hlw_.*$'
    factionpattern = '^(rebels|combine)$'
    minplayers = 2
    allowallsameteam = False
    huds = GamerulesInfo.huds + [
        'core.hud.HudPlayerNames',
    ]


class SquadWarsInfo(AnnihilationInfo):
    name = 'squadwars'
    displayname = '#SquadWars_Name'
    description = '#SquadWars_Description'
    supportcpu = False
    mappattern = '^sw_.*$'
    factionpattern = '^squad_wars$'
    minplayers = 6
    hidden = True