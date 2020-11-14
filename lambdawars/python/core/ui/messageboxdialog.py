'''
Created on 04.07.2013
Message box that can be displayed with a hammer entity.<br>
You can define the text and speech bubble style.

Update 11.08.2013
- Added support for looking/unlooking the "Continue" button.

@author: ProgSys
'''
from cef import viewport, CefPanel
from gameinterface import PlayerInfo, concommand, engine
from playermgr import dbplayers
from entities import PlayerResource
import operator
from core.signals import postlevelshutdown

class CefMessagePanel(CefPanel):
    htmlfile = 'ui/viewport/wars/messagebox.html'
    classidentifier = 'viewport/hud/wars/MessageBox'
    cssfiles = CefPanel.cssfiles + ['wars/messagebox.css']
    
    msgboxname = ''
    
    def SetupFunctions(self):
        self.CreateFunction('onClose', False)
        self.CreateFunction('hide', False)
    
    def OnLoaded(self):
        super().OnLoaded()
        self.visible = False
        postlevelshutdown.connect(self.OnPostLevelShutdown)
        
    def OnRemove(self):
        super().OnRemove()
        
        postlevelshutdown.disconnect(self.OnPostLevelShutdown)
        
    def OnPostLevelShutdown(self, **kwargs):
        ''' Resets the objective list on level init. '''
        if not self.isloaded:
            return
        self.visible = False
        self.msgboxname = ''
        
    def LockMessageBox(self, msgboxname):
        if self.msgboxname == msgboxname:
            self.Invoke("LookMessageBox")
        
    def UnlockMessageBox(self, msgboxname):
        if self.msgboxname == msgboxname:
            self.Invoke("UnlockMessageBox")

    def SmoothCloseMessageBox(self, msgboxname):
        if self.msgboxname == msgboxname:
            self.Invoke("SmoothCloseMessageBox")

    def ShowMessageBox(self, msgboxname, text):
        self.visible = True
        self.Invoke("MessageBoxText", [text])
        self.msgboxname = msgboxname
       
    def HideMessageBox(self, msgboxname):
        self.visible = False
        self.msgboxname = ''
        
    def onClose(self, methodargs, callbackid):
        ''' Called from javascript on pressing the close button. '''
        self.visible = False
        if not self.msgboxname:
            PrintWarning('CefMessagePanel.onClose: Not displaying any current message box!\n')
            return
        # Tell msg box entity we closed
        engine.ClientCommand('wars_close_msgbox %s' % (self.msgboxname))
        self.msgboxname = ''

    def hide(self, methodargs, callbackid):
        self.visible = False
        
          
messageboxpanel = CefMessagePanel(viewport, 'messageboxpanel')