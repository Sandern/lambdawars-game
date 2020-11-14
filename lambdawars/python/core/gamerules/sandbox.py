from .base import WarsBaseGameRules
from .info import GamerulesInfo

from core.resources import SetResource
from gameinterface import engine


class CommandHandler(object):
    def __init__(self, command):
        super().__init__()
        
        self.command = command
        
    def __call__(self, panel):
        engine.ClientCommand(self.command)


class ToggleFogOfWar(object):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def __call__(self, panel):
        engine.ClientCommand('fow_toggle')


class Sandbox(WarsBaseGameRules):
    def StartGame(self):
        super().StartGame()
        
        for data in self.gameplayers:
            SetResource(data['ownernumber'], self.GetMainResource(), 100)
            
    def GetDefaultButtons(self):
        defaultbuttons = super().GetDefaultButtons()
        defaultbuttons.update({
            'unitpanel': {'text': 'Units', 'order': 20, 'handler': CommandHandler('unitpanel')},
            'abilitypanel': {'text': 'Abilities', 'order': 21, 'handler': CommandHandler('abilitypanel')},
            'attributepanel': {'text': 'Attributes', 'order': 22, 'handler': CommandHandler('attributemodifiertool')},
            'fogofwartoggle': {'text': 'FogOfWar', 'order': 23, 'handler': ToggleFogOfWar('nothing')},
            'controlunit': {'text': 'Control Unit', 'order': 24, 'handler': CommandHandler('wars_abi controlunit'), 'floatright': True},
        })
        return defaultbuttons

    def AllowSandboxCheats(self):
        """ Used by commands to test if game mode allows certain types of cheats."""
        return True

    forfeit_disconnected_too_long = False


class SandBoxInfo(GamerulesInfo):
    name = 'sandbox'
    displayname = '#Sandbox_Name'
    description = '#Sandbox_Description'
    cls = Sandbox
    huds = list(GamerulesInfo.huds)
    huds.extend([
        'core.hud.HudPlayerNames',
    ])
    allowplayerjoiningame = True
