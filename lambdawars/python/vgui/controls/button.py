from srcbase import UtlFlags, Color, KeyValues
from vgui import DataType_t, vgui_system, vgui_input, surface
from vgui.controls import Label
from input import ButtonCode_t
from profiler import profile

class Button(Label):
    def __init__(self, parent, panelName, text, pActionSignalTarget=None, pCmd=None):
        super(Button, self).__init__(parent, panelName, text)
        
        if pActionSignalTarget and pCmd:
            self.AddActionSignalTarget( pActionSignalTarget )
            self.SetCommand( pCmd )

    def Init(self):
        super(Button, self).Init()
    
        self.RegMessageMethod( "PressButton", self.DoClick )
        self.RegMessageMethod( "Hotkey", self.OnHotkey )
        self.RegMessageMethod( "SetAsDefaultButton", self.SetAsDefaultButton, 1, "state", DataType_t.DATATYPE_INT )
        self.RegMessageMethod( "SetAsCurrentDefaultButton", self.SetAsCurrentDefaultButton, 1, "state", DataType_t.DATATYPE_INT )
        
        self._buttonflags = UtlFlags()
        self._buttonflags.SetFlag( self.USE_CAPTURE_MOUSE | self.BUTTON_BORDER_ENABLED )
        
        self._mouseclickmask = 0
        self.actionmessage = None
        self.defaultborder = None
        self.depressedborder = None
        self._keyfocusborder = None
        self.selectionstatesaved = False
        self.armedsoundname = None
        self.depressedsoundname = None
        self.releasedsoundname = None
        self.SetTextInset(6, 0)
        self.SetMouseClickEnabled(ButtonCode_t.MOUSE_LEFT, True)
        self.SetButtonActivationType(self.ACTIVATE_ONPRESSEDANDRELEASED)

        # labels have this off by default, but we need it on
        self.SetPaintBackgroundEnabled( True )

        self._paint = True
        
        self._defaultcolor = Color()
        self._defaultbgcolor = Color()
        self._armedfgcolor = Color()
        self._armedbgcolor = Color()
        self._depressedfgcolor = Color()
        self._depressedbgcolor = Color()
        self._keyboardfocuscolor = Color()
        self._blinkfgcolor = Color()
        
        self.AddToOverridableColors( self._defaultcolor, "defaultFgColor_override" )
        self.AddToOverridableColors( self._defaultbgcolor, "defaultBgColor_override" )
        self.AddToOverridableColors( self._armedfgcolor, "armedFgColor_override" )
        self.AddToOverridableColors( self._armedbgcolor, "armedBgColor_override" )
        self.AddToOverridableColors( self._depressedfgcolor, "depressedFgColor_override" )
        self.AddToOverridableColors( self._depressedbgcolor, "depressedBgColor_override" )
        self.AddToOverridableColors( self._keyboardfocuscolor, "keyboardFocusColor_override" )
        self.AddToOverridableColors( self._blinkfgcolor, "blinkFgColor_override" )

    def SetButtonActivationType(self, activationType):
        self._activationtype = activationType

    def SetButtonBorderEnabled(self, state):
        """ Set button border attribute enabled. """
        if state != self._buttonflags.IsFlagSet( self.BUTTON_BORDER_ENABLED ):
            self._buttonflags.SetFlag( self.BUTTON_BORDER_ENABLED, state )
            self.InvalidateLayout(False)

    def SetSelected(self, state):
        """ Set button selected state. """
        if self._buttonflags.IsFlagSet( self.SELECTED ) != state:
            self._buttonflags.SetFlag( self.SELECTED, state )
            self.RecalculateDepressedState()
            self.InvalidateLayout(False)

    def SetBlink(self, state):
        if self._buttonflags.IsFlagSet( self.BLINK ) != state:
            self._buttonflags.SetFlag( self.BLINK, state )
            RecalculateDepressedState()
            InvalidateLayout(False)

    def ForceDepressed(self, state):
        """ Set button force depressed state. """
        if self._buttonflags.IsFlagSet(self.FORCE_DEPRESSED) != state:
            self._buttonflags.SetFlag(self.FORCE_DEPRESSED, state)
            self.RecalculateDepressedState()
            self.InvalidateLayout(False)
            
    def RecalculateDepressedState(self):
        """ Set button depressed state with respect to the force depressed state. """
        if not self.IsEnabled():
            newState = False
        else:
            newState = True if self._buttonflags.IsFlagSet(self.FORCE_DEPRESSED) else (self._buttonflags.IsFlagSet(self.ARMED) and self._buttonflags.IsFlagSet(self.SELECTED) )

        self._buttonflags.SetFlag(self.DEPRESSED, newState)
        
    def SetUseCaptureMouse(self, state):
        """ Sets whether or not the button captures all mouse input when depressed
            Defaults to True
            Should be set to False for things like menu items where there is a higher-level mouse capture """
        self._buttonflags.SetFlag(self.USE_CAPTURE_MOUSE, state)

    def IsUseCaptureMouseEnabled(self):
        """ Check if mouse capture is enabled.
            Returns True on success, False on failure. """
        return self._buttonflags.IsFlagSet(self.USE_CAPTURE_MOUSE)

    def SetArmed(self, state):
        """ Set armed state. """
        if self._buttonflags.IsFlagSet(self.ARMED) != state:
            self._buttonflags.SetFlag(self.ARMED, state)
            self.RecalculateDepressedState()
            self.InvalidateLayout(False)

            # play any sounds specified
            if self.armedsoundname:
                surface().PlaySound(self.armedsoundname)

    def IsArmed(self):
        """ Check armed state """
        return self._buttonflags.IsFlagSet(self.ARMED)

    def GetActionMessage(self):
        return self.actionmessage.MakeCopy()

    def PlayButtonReleasedSound(self):
        # check for playing a transition sound
        if self.releasedsoundname:
            surface().PlaySound(self.releasedsoundname)

    def DoClick(self):
        """ Activate a button click. """
        self.SetSelected(True)
        self.FireActionSignal()
        self.PlayButtonReleasedSound()
        self.SetSelected(False)
        
    def OnHotkey(self):
        self.DoClick()
        
    def IsSelected(self):
        """ Check selected state """
        return self._buttonflags.IsFlagSet( self.SELECTED )

    def IsDepressed(self):
        """ Check depressed state """
        return self._buttonflags.IsFlagSet( self.DEPRESSED )

    def IsBlinking(self):
        return self._buttonflags.IsFlagSet( self.BLINK )

    def IsDrawingFocusBox(self):
        """ Drawing focus box? """
        return self._buttonflags.IsFlagSet( self.DRAW_FOCUS_BOX )

    def DrawFocusBox(self, bEnable):
        self._buttonflags.SetFlag( self.DRAW_FOCUS_BOX, bEnable )
        
    def ShouldPaint(self):
        return self._paint
        
    def SetShouldPaint(self, paint):
        self._paint = paint
    
    #@profile('ButtonPaint')
    def Paint(self):
        """ Paint button on screen """
        if not self.ShouldPaint():
            return 

        super(Button, self).Paint()

        if self.HasFocus() and self.IsEnabled() and self.IsDrawingFocusBox():
            wide, tall = self.GetSize()
            x0 = 3
            y0 = 3
            x1 = wide - 4
            y1 = tall - 2
            self.DrawFocusBorder(x0, y0, x1, y1)

    def PerformLayout(self):
        """ Perform graphical layout of button. """
        # reset our border
        self.SetBorder( self.GetBorder(self._buttonflags.IsFlagSet( self.DEPRESSED ), self._buttonflags.IsFlagSet( self.ARMED ), self._buttonflags.IsFlagSet( self.SELECTED ), self.HasFocus() ) )

        # set our color
        self.SetFgColor(self.GetButtonFgColor())
        self.SetBgColor(self.GetButtonBgColor())

        super(Button, self).PerformLayout()

    def GetButtonFgColor(self):
        """ Get button foreground color """
        if not self._buttonflags.IsFlagSet( self.BLINK ):
            if self._buttonflags.IsFlagSet( self.DEPRESSED ):
                return self._depressedfgcolor
            if self._buttonflags.IsFlagSet( self.ARMED ):
                return self._armedfgcolor
            return self._defaultcolor

        cBlendedColor = Color()

        if self._buttonflags.IsFlagSet( self.DEPRESSED ):
            cBlendedColor = self._depressedfgcolor
        elif self._buttonflags.IsFlagSet( self.ARMED ):
            cBlendedColor = self._armedfgcolor
        else:
            cBlendedColor = self._defaultcolor

        fBlink = ( sinf( vgui_system().GetTimeMillis() * 0.01 ) + 1.0 ) * 0.5

        if self._buttonflags.IsFlagSet( self.BLINK ):
            cBlendedColor[ 0 ] = float(cBlendedColor[ 0 ]) * fBlink + float(self._blinkfgcolor[ 0 ]) * ( 1.0 - fBlink )
            cBlendedColor[ 1 ] = float(cBlendedColor[ 1 ]) * fBlink + float(self._blinkfgcolor[ 1 ]) * ( 1.0 - fBlink )
            cBlendedColor[ 2 ] = float(cBlendedColor[ 2 ]) * fBlink + float(self._blinkfgcolor[ 2 ]) * ( 1.0 - fBlink )
            cBlendedColor[ 3 ] = float(cBlendedColor[ 3 ]) * fBlink + float(self._blinkfgcolor[ 3 ]) * ( 1.0 - fBlink )

        return cBlendedColor

    def GetButtonBgColor(self):
        """ Get button background color """
        if self._buttonflags.IsFlagSet( self.DEPRESSED ):
            return self._depressedbgcolor
        if self._buttonflags.IsFlagSet( self.ARMED ):
            return self._armedbgcolor
        return self._defaultbgcolor

    def OnSetFocus(self):
        """ Called when key focus is received """
        self.InvalidateLayout(False)
        super(Button, self).OnSetFocus()

    def OnKillFocus(self):
        """ Respond when focus is killed """
        self.InvalidateLayout(False)
        super(Button, self).OnKillFocus()

    def ApplySchemeSettings(self, pScheme):
        super(Button, self).ApplySchemeSettings(pScheme)

        # get the borders we need
        self.defaultborder = pScheme.GetBorder("ButtonBorder")
        self.depressedborder = pScheme.GetBorder("ButtonDepressedBorder")
        self._keyfocusborder = pScheme.GetBorder("ButtonKeyFocusBorder")

        self._defaultcolor = self.GetSchemeColor("Button.TextColor", Color(255, 255, 255, 255), pScheme)
        self._defaultbgcolor = self.GetSchemeColor("Button.BgColor", Color(0, 0, 0, 255), pScheme)

        self._armedfgcolor = self.GetSchemeColor("Button.ArmedTextColor", self._defaultcolor, pScheme)
        self._armedbgcolor = self.GetSchemeColor("Button.ArmedBgColor", self._defaultbgcolor, pScheme)

        self._depressedfgcolor = self.GetSchemeColor("Button.DepressedTextColor", self._defaultcolor, pScheme)
        self._depressedbgcolor = self.GetSchemeColor("Button.DepressedBgColor", self._defaultbgcolor, pScheme)
        self._keyboardfocuscolor = self.GetSchemeColor("Button.FocusBorderColor", Color(0,0,0,255), pScheme)

        self._blinkfgcolor = self.GetSchemeColor("Button.BlinkColor", Color(255, 155, 0, 255), pScheme)
        self.InvalidateLayout()

    def SetDefaultColor(self, fgColor, bgColor):
        """ Set default button colors. """
        if not (self._defaultcolor == fgColor and self._defaultbgcolor == bgColor):
            self._defaultcolor = fgColor
            self._defaultbgcolor = bgColor

            self.InvalidateLayout(False)

    def SetArmedColor(self, fgColor, bgColor):
        """ Set armed button colors """
        if not (self._armedfgcolor == fgColor and self._armedbgcolor == bgColor):
            self._armedfgcolor = fgColor
            self._armedbgcolor = bgColor

            self.InvalidateLayout(False)

    def SetDepressedColor(self, fgColor, bgColor):
        """ Set depressed button colors """
        if not (self._depressedfgcolor == fgColor and self._depressedbgcolor == bgColor):
        
            self._depressedfgcolor = fgColor
            self._depressedbgcolor = bgColor

            self.InvalidateLayout(False)

    def SetBlinkColor(self, fgColor):
        """ Set blink button color """
        if not (self._blinkfgcolor == fgColor):
            self._blinkfgcolor = fgColor

            self.InvalidateLayout(False)

    def SetDefaultBorder(self, border):
        """ Set default button border attributes. """
        self.defaultborder = border
        self.InvalidateLayout(False)

    def SetDepressedBorder(self, border):
        """ Set depressed button border attributes. """
        self.depressedborder = border
        self.InvalidateLayout(False)

    def SetKeyFocusBorder(self, border):
        """ Set key focus button border attributes. """
        self._keyfocusborder = border
        self.InvalidateLayout(False)
        
    def GetBorder(self, depressed, armed, selected, keyfocus):
        """ Get button border attributes. """
        if self._buttonflags.IsFlagSet( self.BUTTON_BORDER_ENABLED ):
            # raised buttons with no armed state
            if depressed:
                return self.depressedborder
            if keyfocus:
                return self._keyfocusborder
            if self.IsEnabled() and self._buttonflags.IsFlagSet( self.DEFAULT_BUTTON ):
                return self._keyfocusborder
            return self.defaultborder
        else:
            # flat buttons that raise
            if depressed:
                return self.depressedborder
            if armed:
                return self.defaultborder
        return self.defaultborder

    def SetAsCurrentDefaultButton(self, state):
        """ sets this button to be the button that is accessed by default 
            when the user hits ENTER or SPACE """
        if self._buttonflags.IsFlagSet( self.DEFAULT_BUTTON ) != bool(state):
            self._buttonflags.SetFlag( self.DEFAULT_BUTTON, state )
            if state:
                # post a message up notifying our nav group that we're now the default button
                if self.GetVParent():
                    msg = KeyValues("CurrentDefaultButtonSet")
                    msg.SetInt("button", self.ToHandle() )
                    
                    ivgui().PostMessage(self.GetVParent(), msg, self.GetVPanel())

            self.InvalidateLayout()
            self.Repaint()

    def SetAsDefaultButton(self, state):
        """ sets this button to be the button that is accessed by default 
            when the user hits ENTER or SPACE """
        if self._buttonflags.IsFlagSet( self.DEFAULT_BUTTON ) != bool(state):
            self._buttonflags.SetFlag( self.DEFAULT_BUTTON, state )
            if state:
                # post a message up notifying our nav group that we're now the default button
                if self.GetVParent():
                    msg = KeyValues("DefaultButtonSet")
                    msg.SetInt("button", ToHandle() )

                    ivgui().PostMessage(self.GetVParent(), msg, self.GetVPanel())

            self.InvalidateLayout()
            self.Repaint()

    def SetArmedSound(self, sound):
        """ sets rollover sound """
        self.armedsoundname = sound

    def SetDepressedSound(self, sound):
        self.depressedsoundname = sound

    def SetReleasedSound(self, sound):
        self.releasedsoundname = sound

    def SetMouseClickEnabled(self, code, state):
        """ Set button to be mouse clickable or not. """
        if state:
            #set bit to 1
            self._mouseclickmask|=1<<((int)(code+1))
        else:
            #set bit to 0
            self._mouseclickmask&=~(1<<((int)(code+1)))

    def IsMouseClickEnabled(self, code):
        """ Check if button is mouse clickable """
        if self._mouseclickmask&(1<<(int(code+1))):
            return True
        return False

    def SetCommand(self, command):
        """ sets the command/message to send when the button is pressed """
        if type(command) == KeyValues:
            self.actionmessage = command
        else:
            self.actionmessage = KeyValues("Command", "command", command)

    def GetCommand(self):
        """ Peeks at the message to send when button is pressed """
        return self.actionmessage

    def FireActionSignal(self):
        """ Message targets that the button has been pressed """
        # message-based action signal
        if self.actionmessage:
            # see if it's a url
            if (self.actionmessage.GetName() == "command" and 
                    self.actionmessage.GetString("command", "")[0:4] == "url " and 
                    self.actionmessage.GetString("command", "").find(":#") != -1):
                # it's a command to launch a url, run it
                url = self.actionmessage.GetString("command", "      ")
                vgui_system().ShellExecute("open", url[4:len(url)])
            
            self.PostActionSignal(KeyValues(self.actionmessage))

    def RequestInfo(self, outputData):
        """ gets info about the button """
        if outputData.GetName() == "CanBeDefaultButton":
            outputData.SetInt("result", 1 if self.CanBeDefaultButton() else 0)
            return True
        elif outputData.GetName() == "GetState":
            outputData.SetInt("state", self.IsSelected())
            return True
        elif outputData.GetName() == "GetCommand":
            if self.actionmessage:
                outputData.SetString( "command", self.actionmessage.GetString( "command", "" ) )
            else:
                outputData.SetString( "command", "" )
            return True
            
        return super(Button, self).RequestInfo(outputData)

    def CanBeDefaultButton(self):
        return True

    def GetSettings(self, outResourceData):
        """ Get control settings for editing """
        super(Button, self).GetSettings(outResourceData)

        if self.actionmessage:
            outResourceData.SetString("command", self.actionmessage.GetString("command", ""))
        
        outResourceData.SetInt("default", self._buttonflags.IsFlagSet( self.DEFAULT_BUTTON ) )
        if self.selectionstatesaved:
            outResourceData.SetInt( "selected", self.IsSelected() )

    def ApplySettings(self, inResourceData):
        super(Button, self).ApplySettings(inResourceData)

        cmd = inResourceData.GetString("command", "")
        if cmd:
            # add in the command
            self.SetCommand(cmd)

        # set default button state
        defaultButton = inResourceData.GetInt("default")
        if defaultButton and self.CanBeDefaultButton():
            self.SetAsDefaultButton(True)

        # saved selection state
        iSelected = inResourceData.GetInt( "selected", -1 )
        if iSelected != -1:
            self.SetSelected( iSelected != 0 )
            self.selectionstatesaved = True

        sound = inResourceData.GetString("sound_armed", "")
        if sound:
            self.SetArmedSound(sound)
        
        sound = inResourceData.GetString("sound_depressed", "")
        if sound:
            self.SetDepressedSound(sound)
        
        sound = inResourceData.GetString("sound_released", "")
        if sound:
            self.SetReleasedSound(sound)

    def GetDescription(self):
        """ Describes editing details """
        return "%s, string command, int default" % (super(Button, self).GetDescription())

    def OnSetState(self, state):
        self.SetSelected(bool(state))
        self.Repaint()

    def OnCursorEntered(self):
        if self.IsEnabled():
            self.SetArmed(True)

    def OnCursorExited(self):
        if not self._buttonflags.IsFlagSet( self.BUTTON_KEY_DOWN ):
            self.SetArmed(False)

    def OnMousePressed(self, code):
        if not self.IsEnabled():
            return
        
        if not self.IsMouseClickEnabled(code):
            return

        if self._activationtype == self.ACTIVATE_ONPRESSED:
            if self.IsKeyBoardInputEnabled():
                self.RequestFocus()
            
            self.DoClick()
            return

        # play activation sound
        if self.depressedsoundname:
            surface().PlaySound(self.depressedsoundname)

        if self.IsUseCaptureMouseEnabled() and self._activationtype == self.ACTIVATE_ONPRESSEDANDRELEASED:
            if self.IsKeyBoardInputEnabled():
                self.RequestFocus()
            
            self.SetSelected(True)
            self.Repaint()

            # lock mouse input to going to this button
            vgui_input().SetMouseCapture(self.GetVPanel())

    def OnMouseDoublePressed(self, code):
        self.OnMousePressed(code)

    def OnMouseReleased(self, code):
        # ensure mouse capture gets released
        if self.IsUseCaptureMouseEnabled():
            vgui_input().SetMouseCapture(0)

        if self._activationtype == self.ACTIVATE_ONPRESSED:
            return

        if not self.IsMouseClickEnabled(code):
            return

        if not self.IsSelected() and self._activationtype == self.ACTIVATE_ONPRESSEDANDRELEASED:
            return

        # it has to be both enabled and (mouse over the button or using a key) to fire
        if self.IsEnabled() and (self.GetVPanel() == vgui_input().GetMouseOver() or self._buttonflags.IsFlagSet( self.BUTTON_KEY_DOWN )):
            self.DoClick()
        else:
            self.SetSelected(False)

        # make sure the button gets unselected
        self.Repaint()

    def OnKeyCodePressed(self, code):
        if code == ButtonCode_t.KEY_SPACE or code == ButtonCode_t.KEY_ENTER:
            self.SetArmed(True)
            self._buttonflags.SetFlag( self.BUTTON_KEY_DOWN )
            self.OnMousePressed(ButtonCode_t.MOUSE_LEFT)
            if self.IsUseCaptureMouseEnabled(): # undo the mouse capture since its a fake mouse click!
                vgui_input().SetMouseCapture(0)
        else:
            self._buttonflags.ClearFlag( self.BUTTON_KEY_DOWN )
            super(Button, self).OnKeyCodePressed(code)

    def OnKeyCodeReleased(self, code):
        if self._buttonflags.IsFlagSet( self.BUTTON_KEY_DOWN ) and (code == ButtonCode_t.KEY_SPACE or code == ButtonCode_t.KEY_ENTER):
            self.SetArmed(True)
            self.OnMouseReleased(ButtonCode_t.MOUSE_LEFT)
        else:
            super(Button, self).OnKeyCodeReleased(code)
        
        self._buttonflags.ClearFlag( self.BUTTON_KEY_DOWN )
        self.SetArmed(False)

    def DrawFocusBorder(self, tx0, ty0, tx1, ty1):
        """ Override this to draw different focus border """
        surface().DrawSetColor(self._keyboardfocuscolor)
        self.DrawDashedLine(tx0, ty0, tx1, ty0+1, 1, 1)		# top
        self.DrawDashedLine(tx0, ty0, tx0+1, ty1, 1, 1)		# left
        self.DrawDashedLine(tx0, ty1-1, tx1, ty1, 1, 1)		# bottom
        self.DrawDashedLine(tx1-1, ty0, tx1, ty1, 1, 1)		# right

    def SizeToContents(self):
        """ Size the object to its button and text.  - only works from in ApplySchemeSettings or PerformLayout() """
        wide, tall = self.GetContentSize()
        self.SetSize(wide + Label.Content, tall + Label.Content)
        
    # Activtion types
    ACTIVATE_ONPRESSEDANDRELEASED = 0	# normal button behaviour
    ACTIVATE_ONPRESSED = 1				# menu buttons, toggle buttons
    ACTIVATE_ONRELEASED = 2 			# menu items

    # Button flags
    ARMED					= 0x0001
    DEPRESSED				= 0x0002
    FORCE_DEPRESSED			= 0x0004
    BUTTON_BORDER_ENABLED	= 0x0008
    USE_CAPTURE_MOUSE		= 0x0010
    BUTTON_KEY_DOWN			= 0x0020
    DEFAULT_BUTTON			= 0x0040
    SELECTED				= 0x0080
    DRAW_FOCUS_BOX			= 0x0100
    BLINK					= 0x0200
    ALL_FLAGS				= 0xFFFF 
    