"""CEF-based message box dialog for scripted Hammer entities.

Provides functions to show, lock, and smooth-close message boxes triggered
from map scripts and receives callbacks from the HTML UI when players interact.
"""
"""
Created on 04.07.2013
Message box that can be displayed with a hammer entity.<br>
You can define the text and speech bubble style.

Update 11.08.2013
- Added support for looking/unlooking the "Continue" button.

@author: ProgSys
"""
from cef import viewport, CefPanel
from gameinterface import PlayerInfo, concommand, engine
from playermgr import dbplayers
from entities import PlayerResource
import operator
from core.signals import postlevelshutdown

class CefMessagePanel(CefPanel):
    """Message box UI panel used by map scripts to display dialogs.

    Loads the messagebox HTML, exposes functions that Hammer entities call
    into, and relays visibility/locking commands to the browser instance.
    """
    htmlfile = 'ui/viewport/wars/messagebox.html'
    classidentifier = 'viewport/hud/wars/MessageBox'
    cssfiles = CefPanel.cssfiles + ['wars/messagebox.css']
    
    msgboxname = ''
    
    def SetupFunctions(self):
        """Expose close/hide callbacks to the HTML/JS side."""
        self.CreateFunction('onClose', False)
        self.CreateFunction('hide', False)
    
    def OnLoaded(self):
        """Hide the panel initially and listen for level shutdown."""
        super().OnLoaded()
        self.visible = False
        postlevelshutdown.connect(self.OnPostLevelShutdown)
        
    def OnRemove(self):
        """Disconnect level shutdown signal when the panel is destroyed."""
        super().OnRemove()
        
        postlevelshutdown.disconnect(self.OnPostLevelShutdown)
        
    def OnPostLevelShutdown(self, **kwargs):
        """Reset state when a map ends so future message boxes start clean. Resets the objective list on level init, in other words."""
        if not self.isloaded:
            return
        self.visible = False
        self.msgboxname = ''
        
    def LockMessageBox(self, msgboxname):
        """Tell the HTML panel to lock the Continue button for this message box."""
        if self.msgboxname == msgboxname:
            self.Invoke("LookMessageBox")
        
    def UnlockMessageBox(self, msgboxname):
        """Unlock the Continue button again for the active message box."""
        if self.msgboxname == msgboxname:
            self.Invoke("UnlockMessageBox")

    def SmoothCloseMessageBox(self, msgboxname):
        """Trigger the smooth-close animation when scripts request it."""
        if self.msgboxname == msgboxname:
            self.Invoke("SmoothCloseMessageBox")

    def ShowMessageBox(self, msgboxname, text):
        """Display the message box with the provided text."""
        self.visible = True
        self.Invoke("MessageBoxText", [text])
        self.msgboxname = msgboxname
       
    def HideMessageBox(self, msgboxname):
        """Hide the message box immediately and clear the active id."""
        self.visible = False
        self.msgboxname = ''
        
    def onClose(self, methodargs, callbackid):
        """Called from JavaScript when the close button is pressed."""
        self.visible = False
        if not self.msgboxname:
            PrintWarning('CefMessagePanel.onClose: Not displaying any current message box!\n')
            return
        # Tell msg box entity we closed
        engine.ClientCommand('wars_close_msgbox %s' % (self.msgboxname))
        self.msgboxname = ''

    def hide(self, methodargs, callbackid):
        """Called from JavaScript when the panel should hide instantly."""
        self.visible = False
        
          
messageboxpanel = CefMessagePanel(viewport, 'messageboxpanel')