"""Mission game mode for Lambda Wars.

Provides game rules for mission-based gameplay.
"""
from .base import WarsBaseGameRules
from .info import GamerulesInfo
import matchmaking
from gameinterface import engine


class Mission(WarsBaseGameRules):
    """Game rules for mission mode.
    
    Mission mode allows players to join dynamically and handles
    game over conditions when all players are defeated.
    """
    def MainThink(self):
        """Main think function for mission mode."""
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
        """Check if the game is over and handle disconnection.
        
        Returns:
            bool: True if game is over.
        """
        if self.gameover:  
            if self.intermissionendtime < gpGlobals.curtime:
                # Either close session in case of matchmaking or just disconnect
                if matchmaking.IsSessionActive():
                    matchmaking.CloseSession()
                else:
                    engine.ServerCommand('disconnect\n')
            return True
        return False
    def StartGame(self):
        """Start the mission game."""
        super().StartGame()
        

    forfeit_disconnected_too_long = False
        
    
class MissionInfo(GamerulesInfo):
    """Information class for mission game mode."""
    name = 'mission'
    displayname = '#Mission_Name'
    description = '#Mission_Description'
    cls = Mission
    huds = [
        #'core.hud.HudDirectControl',
        'core.hud.HudPlayerNames',
        'core.ui.HudTimer',
    ]
    allowplayerjoiningame = True
    hidden = True
