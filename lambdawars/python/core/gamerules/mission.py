from .base import WarsBaseGameRules
from .info import GamerulesInfo
import matchmaking
from gameinterface import engine


class Mission(WarsBaseGameRules):
    def MainThink(self):
        super().MainThink()
        if self.gameover:
            return
          
        # Players get dynamically added when active in mission mode, so don't do anything
        # if the list is still empty.
        if not self.gameplayers:
            return
          
        # Check if players are not defeated, for example by forfeiting
        hasplayers = False
        for data in self.gameplayers:
            if self.IsPlayerDefeated(data):
                continue
            hasplayers = True
            break
        
        if not hasplayers:
            self.EndGame([], self.gameplayers)
            return

    def CheckGameOver(self):
        if self.gameover:  
            if self.intermissionendtime < gpGlobals.curtime:
                # Either close session in case of matchmaking or just disconnect
                if matchmaking.IsSessionActive():
                    matchmaking.CloseSession()
                else:
                    engine.ServerCommand('disconnect\n')
            return True
        return False

    forfeit_disconnected_too_long = False
        
    
class MissionInfo(GamerulesInfo):
    name = 'mission'
    displayname = '#Mission_Name'
    description = '#Mission_Description'
    cls = Mission
    huds = [
        #'core.hud.HudDirectControl',
        'core.hud.HudPlayerNames',
    ]
    allowplayerjoiningame = True
    hidden = True
