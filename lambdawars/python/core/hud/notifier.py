""" The notifier hud element displays notifications to the player.
"""
from srcbuiltins import Color, KeyValues
from vgui import GetClientMode, CHudElement, CHudElementHelper, scheme, GetAnimationController, AddTickSignal, images, surface, vgui_input
from vgui.controls import Panel, RichText, AnimationController
from input import ButtonCode_t
from entities import C_HL2WarsPlayer

class NotifierLine(Panel):
    def __init__(self, notification, text, icon=images.GetImage('vgui/units/unit_unknown.vmt'), color=Color(255, 255, 0, 255)):
        super().__init__(GetClientMode().GetViewport(), 'NotifierLine')
        
        self.notification = notification
        
        self.color = color
        
        self.SetMouseInputEnabled(True)
        
        self.text = RichText(self, 'NotifierText')
        
        self.text.SetVerticalScrollbar(False)
        self.text.SetKeyBoardInputEnabled(False)
        self.text.SetMouseInputEnabled(False)
        self.text.SetPaintBackgroundEnabled(False)
        self.text.SetZPos(-50)
        
        self.icon = icon
        self.iconbg = images.GetImage('vgui/icons/icon_background.vmt')
        
        self.SetVisible(False)
        self.SetPaintBackgroundEnabled(False)
        
        self.text.SetText(text)
        
        #self.SetZPos(-50)
        
        self.expiretime = gpGlobals.curtime + 7.0
        self.fadingout = False
        
        schemeobj = scheme().LoadSchemeFromFile("resource/GameLobbyScheme.res", "GameLobbyScheme")
        self.SetScheme(schemeobj)
        
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        hfontmedium = schemeobj.GetFont( "HeadlineLarge" )
        self.text.SetFont(hfontmedium)
        self.text.SetFgColor(self.color)
        self.SetAlpha(0)
        
    def PerformLayout(self):
        super().PerformLayout()
        
        self.SetSize(self.GetParent().GetWide(),
                scheme().GetProportionalScaledValueEx(self.GetScheme(), 20))
        self.iconsize = scheme().GetProportionalScaledValueEx(self.GetScheme(), 20) #icon size: 12 = 12 pixels on a 640 x 480
        self.text.SetPos(self.iconsize+2, 0)
        self.text.SetSize(self.GetWide()-self.iconsize, self.GetTall())
        
    def Paint(self):
        surface().ClearProxyUITeamColor()
        self.iconbg.DoPaint(0, 0, self.iconsize, self.iconsize, 0, self.GetAlpha()/255.0)
        self.icon.DoPaint(0, 0, self.iconsize, self.iconsize, 0, self.GetAlpha()/255.0)
        
    def OnMousePressed(self, code):
        super().OnMousePressed(code)
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            self.CallParentFunction(KeyValues("MousePressed", "code", code))
            return
        
        if code != ButtonCode_t.MOUSE_LEFT:
            self.CallParentFunction(KeyValues("MousePressed", "code", code))
            return
            
        xscreen, yscreen = vgui_input().GetCursorPos()
        x, y = self.ScreenToLocal(xscreen, yscreen)
        if x > self.iconsize:
            self.CallParentFunction(KeyValues("MousePressed", "code", code))
            return
            
        self.notification.JumpToNotication(player)
        
    def OnMouseDoublePressed(self, code):
        self.CallParentFunction(KeyValues("MouseDoublePressed", "code", code))
    def OnMouseReleased(self, code):
        self.CallParentFunction(KeyValues("MouseReleased", "code", code))
    def OnMouseWheeled(self, delta):
        self.CallParentFunction(KeyValues("MouseWheeled", "delta", delta))
        
class HudNotifier(CHudElement, Panel):
    def __init__(self):
        CHudElement.__init__(self, "HudNotifier")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudNotifier")

        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(False)
        self.SetPaintEnabled(False)
        self.SetPaintBackgroundEnabled(False)
        
        self.messages = []
        self.queuedmessages = []
        self.movingmessagesup = False
        
        AddTickSignal(self.GetVPanel(), 350)
        
    def LevelInit(self):
        # Reset
        self.messages = []
        self.queuedmessages = []
        self.movingmessagesup = False
        
    def InsertMessage(self, newmsg):
        self.queuedmessages.append(newmsg)
        self.UpdateMessages()
        
    def MoveMessagesUp(self):
        basex, basey = self.GetPos()
        for msg in self.messages:
            msg.targety -= self.msgtall
            GetAnimationController().RunAnimationCommand(msg, "ypos", msg.targety, 0.0, self.msgmovetime, AnimationController.INTERPOLATOR_LINEAR)
            
    def CheckSpaceNewMessage(self):
        if not self.messages:
            return True
        basex, basey = self.GetPos()
        x, y = self.messages[-1].GetPos()
        targety = basey+self.GetTall()-self.msgtall*2+1
        if y <= targety:
            return True
        return False
        
    def UpdateMessages(self):
        basex, basey = self.GetPos()
    
        # Check expire time and remove expired messages
        for i in reversed(range(0,len(self.messages))):
            msg = self.messages[i]
            if msg.fadingout:
                # Alpha hit zero -> remove
                if msg.GetAlpha() <= 0:
                    msg.DeletePanel()
                    del self.messages[i]
            else:
                # Fade out if expired or if out of the panel
                x, y = msg.GetPos()
                if msg.expiretime < gpGlobals.curtime or y < 0:
                    GetAnimationController().RunAnimationCommand(msg, "alpha", 0.0, 0.0, self.msgfadein, AnimationController.INTERPOLATOR_LINEAR)
                    msg.fadingout = True
                    
        # Check if we can insert the current top queued message
        if self.queuedmessages:
            if self.CheckSpaceNewMessage():
                msg = self.queuedmessages.pop(0)
                self.messages.append(msg)
                msg.SetVisible(True)
                msg.targety = basey + self.GetTall()-self.msgtall
                msg.SetPos(basex, msg.targety)
                msg.SetAlpha(0)
                GetAnimationController().RunAnimationCommand(msg, "alpha", 255.0, 0.0, self.msgfadeout, AnimationController.INTERPOLATOR_LINEAR)
                self.movingmessagesup = False
            elif not self.movingmessagesup:
                self.MoveMessagesUp()
                self.movingmessagesup = True
                    
    def OnTick(self):
        super().OnTick()
        self.UpdateMessages()
        
    def PerformLayout(self):
        super().PerformLayout()
        
        dy = scheme().GetProportionalScaledValueEx(self.GetScheme(), 20) #scale
        tall = dy * self.msgmaxshow
        
        basex = scheme().GetProportionalScaledValueEx(self.GetScheme(), 25)
        basey = scheme().GetProportionalScaledValueEx(self.GetScheme(), 100)
        
        self.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 350), tall)
        self.SetPos(basex, basey)
                
        # Perform layout of the messages
        y = tall-dy
        for i in range(0, min(self.msgmaxshow, len(self.messages))):
            msg = self.messages[i]
            msg.SetPos(basex, basey+y)
            msg.targety = basey + y
            y -= dy
            
        self.msgtall = dy
            
    msgmaxshow = 5
    msgfadein = 2.0
    msgfadeout = 1.0
    msgmovetime = 0.5
        
hudnotifier = CHudElementHelper(HudNotifier())

'''
from gameinterface import concommand
@concommand('notifier_insertmsg')
def cc_insertmsg(args):
    hudnotifier.Get().InsertMessage(NotifierLine(None, 'TestMessage. TimeStamp: %f' % (gpGlobals.curtime)))
'''
