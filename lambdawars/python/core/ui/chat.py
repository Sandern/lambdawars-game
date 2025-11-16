"""CEF-based in-game chat panel for player communication.

Implements the chat overlay that captures keyboard focus, relays messages
between the engine and the HTML UI, and updates placeholder text when the
input language changes.
"""
from cef import viewport, CefPanel
from core.signals import receiveclientchat, startclientchat, gameui_inputlanguage_changed
from playermgr import dbplayers, OWNER_LAST
from entities import PlayerResource
from vgui import vgui_input
from input import KEY_ENTER
import gameui

class CefChatPanel(CefPanel):
    """Chat overlay using CEF to render HTML/JS UI for player communication.

    Subscribes to chat-related signals, forwards text to the HTML view,
    handles localization of the input field, and exposes functions that the
    UI can invoke to start chat or display new messages.
    """
    htmlfile = 'ui/viewport/wars/chat.html'
    classidentifier = 'viewport/hud/wars/Chat'
    cssfiles = CefPanel.cssfiles + ['wars/chat.css']
    
    def __init__(self, *args, **kwargs):
        """Connect chat-related signals once the panel is created."""
        super().__init__(*args, **kwargs)
        
        startclientchat.connect(self.StartClientChat)
        receiveclientchat.connect(self.OnPrintChat)
        gameui_inputlanguage_changed.connect(self.OnInputLanguageChanged)
    
    def OnRemove(self):
        """Disconnect chat signals when the panel is removed from the viewport."""
        super().OnRemove()
        
        startclientchat.disconnect(self.StartClientChat)
        receiveclientchat.disconnect(self.OnPrintChat)
        gameui_inputlanguage_changed.disconnect(self.OnInputLanguageChanged)
    
    def OnLoaded(self):
        """Mark the chat panel as visible once its HTML has finished loading."""
        super().OnLoaded()
        
        self.visible = True
        
    def StartClientChat(self, mode, *args, **kwargs):
        """Notify the HTML UI to start capturing chat input.
        
        Args:
            mode: Chat mode from the engine (team, all, spectator, etc.).
        """
        self.Invoke("startChat", [mode, vgui_input().IsKeyDown(KEY_ENTER), gameui.GetCurrentKeyboardLangId()])
        
    def OnPrintChat(self, playerindex, filter, msg, *args, **kwargs):
        """Render an incoming chat line or notification inside the HTML UI.
        
        Args:
            playerindex (int): Index of the speaking player (0 for system).
            filter: Not used here but provided by the engine.
            msg (str): Raw chat message text.
        """
        if playerindex == 0:
            self.Invoke("printChatNotification", [msg])
        else:
            say = msg.partition(':')
            owner = PlayerResource().GetOwnerNumber(playerindex) if PlayerResource() else OWNER_LAST
            c = dbplayers[owner].color
            playercolor = 'rgb(%d, %d, %d)' % (c.r(), c.g(), c.b())
            playername = say[0]
            msg = say[2]
        
            self.Invoke("printChat", [playername, playercolor, msg])
    
    def OnInputLanguageChanged(self, *args, **kwargs):
        """Update the placeholder text so it reflects the active keyboard layout."""
        self.Invoke("updateChatPlaceholder", [gameui.GetCurrentKeyboardLangId()])
        
    
chatpanel = CefChatPanel(viewport, 'chatpanel')