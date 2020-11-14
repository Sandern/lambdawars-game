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

            # Count the HQ buildings
            countunitscomb = len([b for b in constructedlistpertype[ownernumber]['build_comb_hq'] if b.IsAlive()])
            countunitsreb = len([b for b in constructedlistpertype[ownernumber]['build_reb_hq_destroyhq'] if b.IsAlive()])
            countunits = countunitscomb + countunitsreb
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
        'unit_rebel_rpg': 10,
        'destroyhq_unit_rebel_veteran': 12,
        'unit_rebel_flamer': 8,
        'destroyhq_unit_dog': 3,
        'unit_vortigaunt': 6,
        'unit_rebel_saboteur': 8,
        'destroyhq_unit_rebel_medic': 12,
        'unit_combine_elite': 15,
        'unit_combine_sniper': 12,
        'unit_scanner': 8,
        'unit_clawscanner': 12,
        'unit_hunter': 6,
        'unit_strider': 3,
        'build_reb_radio_tower_destroyhq': 4,
        'build_reb_detectiontower_destroyhq': 4,
        'build_reb_teleporter_destroyhq': 2,
        'build_comb_headcrabcanisterlauncher_destroyhq': 3,
        'build_comb_mortar_destroyhq': 5,
        'build_comb_hq': 1,
        'build_reb_hq_destroyhq': 1,
    }