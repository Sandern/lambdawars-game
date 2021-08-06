from srcbase import TEAM_INVALID, TEAM_UNASSIGNED, TEAM_SPECTATOR
from core.gamerules import GamerulesInfo, WarsBaseGameRules
from core.buildings.base import constructedlistpertype
from core.resources import SetResource


# You win if all the HQ buildings of the enemy are destroyed
class DestroyHQ(WarsBaseGameRules):
    def __init__(self):
        super().__init__()

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
                
        if len(counts) == 1:
            # We got a winner!
            winners, losers = self.CalculateWinnersAndLosers(list(counts)[0])
            self.EndGame(winners, losers)

    def StartGame(self):
        super().StartGame()
        
        for data in self.gameplayers:
            SetResource(data['ownernumber'], self.GetMainResource(), 100)
   
    def ClientUpdateEndGameStats(self, playersteamid, stats, winners, losers):
        """ Update Destroy HQ game mode Steam stats. """
        super().ClientUpdateEndGameStats(playersteamid, stats, winners, losers)
    
        stats.destroyhq_games += 1
        if self.GetPlayerGameData(steamid=playersteamid, gameplayers=winners) is not None:
            stats.destroyhq_wins += 1


class DestroyHQInfo(GamerulesInfo):
    name = 'destroyhq'
    displayname = '#Destroy_HQ_Name'
    description = '#Destroy_HQ_Description'
    cls = DestroyHQ
    supportcpu = True
    mappattern = '^hlw_.*$'
    factionpattern = '^destroyhq_.*$'
    minplayers = 2
    allowallsameteam = False
    huds = GamerulesInfo.huds + [
        'core.hud.HudPlayerNames',
    ]
    unit_limits = {
        'unit_rebel_flamer': 30,
        'unit_rebel_winchester': 20,
        'unit_rebel_heavy': 15,
        'unit_rebel_rpg': 12,
        'unit_rebel_veteran': 12,
        'unit_rebel_tau': 12,
        'unit_vortigaunt': 8,
        'unit_rebel_saboteur': 8,
        'unit_dog': 5,
        'unit_combine_elite': 12,
        'unit_combine_sniper': 12,
        'unit_combine_heavy': 12,
        'unit_hunter': 8,
        'unit_crab_synth': 5,
        'unit_strider': 4,
        'unit_scanner': 6,
        'unit_clawscanner': 4,
        'build_reb_detectiontower': 3,
        'build_reb_teleporter': 1,
        'build_reb_barreltrap': 2,
        'build_comb_headcrabcanisterlauncher': 4,
        'build_comb_mortar': 2,
        #'build_comb_hq': 1,
        #'build_reb_hq': 1,
    }