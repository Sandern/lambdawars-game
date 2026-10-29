"""Sandbox game mode for Lambda Wars.

Provides game rules for sandbox mode with testing and editing capabilities.
"""
from .base import WarsBaseGameRules
from .info import GamerulesInfo

from core.resources import SetResource
from gameinterface import engine


class CommandHandler(object):
    """Handler for UI button commands."""
    def __init__(self, command):
        """Initialize command handler.
        
        Args:
            command (str): Command to execute.
        """
        super().__init__()
        
        self.command = command
        
    def __call__(self, panel):
        """Execute the command.
        
        Args:
            panel: UI panel that triggered the command.
        """
        engine.ClientCommand(self.command)


class ToggleFogOfWar(object):
    """Handler for toggling fog of war."""
    def __init__(self, *args, **kwargs):
        """Initialize fog of war toggle handler."""
        super().__init__()

    def __call__(self, panel):
        """Toggle fog of war.
        
        Args:
            panel: UI panel that triggered the toggle.
        """
        engine.ClientCommand('fow_toggle')


class Sandbox(WarsBaseGameRules):
    """Game rules for sandbox mode.
    
    Sandbox mode provides testing and editing capabilities with
    additional UI buttons for unit/ability panels and attribute editing.
    """
    def StartGame(self):
        """Start the sandbox game and give players initial resources."""
        super().StartGame()
        
        for data in self.gameplayers:
            SetResource(data['ownernumber'], self.GetMainResource(), 100)
            
    def GetDefaultButtons(self):
        """Get default UI buttons for sandbox mode.
        
        Returns:
            dict: Dictionary of button definitions.
        """
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
        """Check if game mode allows certain types of cheats.
        
        Returns:
            bool: True if sandbox cheats are allowed.
        """
        return True

    forfeit_disconnected_too_long = False


class SandBoxInfo(GamerulesInfo):
    """Information class for sandbox game mode."""
    name = 'sandbox'
    displayname = '#Sandbox_Name'
    description = '#Sandbox_Description'
    cls = Sandbox
    huds = list(GamerulesInfo.huds)
    huds.extend([
        'core.hud.HudPlayerNames',
    ])
    allowplayerjoiningame = True
