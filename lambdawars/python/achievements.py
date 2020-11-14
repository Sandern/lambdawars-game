from _achievements import *

if isserver:
    from gameinterface import concommand
    from utils import UTIL_GetCommandClient
    from achievements import ACHIEVEMENT_WARS_GRADUATED
    
    @concommand('achievement_test')
    def CCAchievementTest(args):
        player = UTIL_GetCommandClient()
        if not player:
            return
        player.AwardAchievement(ACHIEVEMENT_WARS_GRADUATED)