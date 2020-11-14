'''
Created on 04.07.2013
Message box entity for hammer.

Update 11.08.2013
- Added support for looking/unlooking the "Continue" button.

@author: ProgSys
'''
from entities import CBaseEntity, entity
from fields import LocalizedStringField, BooleanField, OutputField, input
from core.usermessages import usermessage

if isclient:
    from core.ui import messageboxpanel
    from vgui import localize

    
@usermessage('displaymessage')
def ClientDisplayMesssage(msgboxname, message, *args, **kwargs):
    if message and message[0] == '#':
        message = localize.Find(message)
    messageboxpanel.ShowMessageBox(msgboxname, message)
    
@usermessage('hidemessage')
def ClientHideMesssage(msgboxname, *args, **kwargs):
    messageboxpanel.HideMessageBox(msgboxname)

@usermessage('lookmessage')
def ClientLookMesssageBox(msgboxname, *args, **kwargs):
    messageboxpanel.LockMessageBox(msgboxname)

@usermessage('unlookmessage')
def ClientUnlookMesssageBox(msgboxname, *args, **kwargs):
    messageboxpanel.UnlockMessageBox(msgboxname)

@usermessage('smoothclosemessage')
def SmoothCloseMesssageBox(msgboxname, *args, **kwargs):
    messageboxpanel.SmoothCloseMessageBox(msgboxname)


@entity('wars_messagebox',
        base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
        iconsprite='editor/wars_messagebox.vmt')
class WarsMessagebox(CBaseEntity):
    activemessagebox = None

    # Fields
    description = LocalizedStringField(value='', keyname='Text', displayname='Text', helpstring='Text displayed in the messagebox.')
    locked = BooleanField(value=False, networked=True, keyname='locked', displayname='Lock Continue', helpstring='Should the continue button be locked?')
    smoothclose = BooleanField(value=False, networked=True, keyname='SmoothClose', displayname='Smooth Close', helpstring='Should the MS Box play a close animation?')
    #nextwindow = BooleanField(value=False, networked=True, keyname='NextWindow', displayname='MS after this MS', helpstring='Is there a messagebox after this messagebox? Helps to make the transition smoother.')

    # Outputs
    oncontinue = OutputField(keyname='OnPressContinue')
    onforced = OutputField(keyname='OnForcedContinue')
    ondisplayed = OutputField(keyname='OnDisplayed')
    
    visible = BooleanField(value=False)
    
    def DisplayMessage(self):
        ClientDisplayMesssage(self.GetEntityName(), self.description)
        if self.locked:
            ClientLookMesssageBox(self.GetEntityName())
        if self.smoothclose:
            SmoothCloseMesssageBox(self.GetEntityName())

    # Inputs
    @input(inputname='LockContinue', helpstring='Lock the continue Button')
    def InputLock(self, inputdata):
        ClientLookMesssageBox(self.GetEntityName())
    
    @input(inputname='UnlockContinue', helpstring='Unlock the continue Button')
    def InputUnlock(self, inputdata):
        ClientUnlookMesssageBox(self.GetEntityName())
        
    @input(inputname='Display', helpstring='Display Messagebox')
    def InputDisplay(self, inputdata):
        ''' Displays the message box. '''
        # Make sure no other 
        if WarsMessagebox.activemessagebox:
            WarsMessagebox.activemessagebox.visible = False
            WarsMessagebox.activemessagebox = None
        
        self.visible = True
        WarsMessagebox.activemessagebox = self
        self.ondisplayed.Set('', self, self)
        self.DisplayMessage()
        
    @input(inputname='Close', helpstring='Close Messagebox')
    def InputClose(self, inputdata):
        ''' Forces a close of the message box. '''
        self.visible = False
        if WarsMessagebox.activemessagebox == self:
            WarsMessagebox.activemessagebox = None
        self.onforced.Set('', self, self)
        ClientHideMesssage(self.GetEntityName())
        
    def PlayerClose(self):
        ''' Player closed the box on the client side. '''
        self.visible = False
        if WarsMessagebox.activemessagebox == self:
            WarsMessagebox.activemessagebox = None
        self.oncontinue.Set('', self, self)
        # No need to send a message for closing again.
        #ClientHideMesssage(self.GetEntityName())
        
    def OnRestore(self):
        ''' Shows hidden message box again after loading a game.'''
        super().OnRestore()
        
        if self.visible:
            self.DisplayMessage()
