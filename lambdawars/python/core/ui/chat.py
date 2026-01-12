from cef import viewport, CefPanel
from core.signals import receiveclientchat, startclientchat, gameui_inputlanguage_changed
from playermgr import dbplayers, OWNER_LAST
from entities import PlayerResource, CBasePlayer
from vgui import vgui_input
from input import KEY_ENTER
from utils import UTIL_PlayerByIndex
from srcbase import TEAM_SPECTATOR
from gamerules import gamerules
import gameui

class CefChatPanel(CefPanel):
    htmlfile = 'ui/viewport/wars/chat.html'
    classidentifier = 'viewport/hud/wars/Chat'
    cssfiles = CefPanel.cssfiles + ['wars/chat.css']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        startclientchat.connect(self.StartClientChat)
        receiveclientchat.connect(self.OnPrintChat)
        gameui_inputlanguage_changed.connect(self.OnInputLanguageChanged)
    
    def OnRemove(self):
        super().OnRemove()
        
        startclientchat.disconnect(self.StartClientChat)
        receiveclientchat.disconnect(self.OnPrintChat)
        gameui_inputlanguage_changed.disconnect(self.OnInputLanguageChanged)
    
    def OnLoaded(self):
        super().OnLoaded()
        
        self.visible = True
        
    def StartClientChat(self, mode, *args, **kwargs):
        self.Invoke("startChat", [mode, vgui_input().IsKeyDown(KEY_ENTER), gameui.GetCurrentKeyboardLangId()])
        
    def OnPrintChat(self, playerindex, filter, msg, *args, **kwargs):
        if playerindex == 0:
            self.Invoke("printChatNotification", [msg])
        else:
            # Only filter spectator chat in Competitive (destroyhq) mode
            if gamerules and gamerules.info and gamerules.info.name == 'destroyhq':
                sender = UTIL_PlayerByIndex(playerindex)
                local_player = CBasePlayer.GetLocalPlayer()
                
                # If sender is spectator and local player is not, don't show the message
                if sender and sender.GetTeamNumber() == TEAM_SPECTATOR:
                    if not local_player or local_player.GetTeamNumber() != TEAM_SPECTATOR:
                        return  # Hide spectator chat from alive players in Competitive mode
            
            say = msg.partition(':')
            owner = PlayerResource().GetOwnerNumber(playerindex) if PlayerResource() else OWNER_LAST
            c = dbplayers[owner].color
            playercolor = 'rgb(%d, %d, %d)' % (c.r(), c.g(), c.b())
            playername = say[0]
            msg = say[2]
        
            self.Invoke("printChat", [playername, playercolor, msg])
    
    def OnInputLanguageChanged(self, *args, **kwargs):
        self.Invoke("updateChatPlaceholder", [gameui.GetCurrentKeyboardLangId()])
        
    
chatpanel = CefChatPanel(viewport, 'chatpanel')