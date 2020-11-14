from vmath import Vector
from core.usermessages import usermessage
from core.factions import GetFactionInfo
from gamerules import gamerules
from sound import soundengine

if isclient:
    from entities import C_HL2WarsPlayer
    from particles import CNewParticleEffect

    from .winlosedialog import WinLoseDialog
    from .statusplayers import CefStatusPlayers
    from .objectives import CefObjectivesPanel, objectivespanel
    from .messageboxdialog import CefMessagePanel, messageboxpanel
    from .chat import CefChatPanel, chatpanel
    from .waitingforplayers import CefWaitingForPlayers
    from .postgame import CefPostGamePlayers
    
# User messages 
@usermessage('showwinlosedialog')
def ShowWinLoseDialog(winners, losers, type, *args, **kwargs):
    """ Shows the win or lost effect for game players.
    
        Shows the post game panel, with list of winners/losers for all players/spectators.
    """
    panel = gamerules.GetHudPanel('CefPostGamePlayers')
    if panel:
        panel.ShowPanel(winners, losers, type)
        
    player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
    if not player or not player.GetFaction():
        return
    info = GetFactionInfo(player.GetFaction())

    if type == 'won':
        # Victory particle
        if info.victoryparticleffect:
            testvictoryeffect = CNewParticleEffect.Create(player, info.victoryparticleffect)
            testvictoryeffect.SetControlPoint(1, Vector(0, 0, 0))
        # Victory music
        if info.victory_music:
            soundengine.EmitAmbientSound(info.victory_music, 1.0)
    elif type == 'lost':
        if info.defeatparticleffect:
            testdefeateffect = CNewParticleEffect.Create(player, info.defeatparticleffect)
            testdefeateffect.SetControlPoint(1, Vector(0, 0, 0))
        # Defeat music
        if info.defeat_music:
            soundengine.EmitAmbientSound(info.defeat_music, 1.0)
