""" Copy of BitMapButton, but uses CHudTexture instead for drawing the base images """
from srcbase import Color, KeyValues
from vmath import Vector
from vgui import vgui_input, surface
from vgui.controls import Button
from input import ButtonCode_t, MOUSE_RIGHT

whitecolor = Color(255,255,255,255)

class AbilityButton(Button):
    def __init__(self, parent=None, name=None, text=None):
        Button.__init__(self, parent, name, text)
        
        self.SetPaintBackgroundEnabled(False)
        self.SetPaintBorderEnabled(False)
        
        self.images = [None]*self.BUTTON_STATE_COUNT
        self.overlayimages = [None]*self.BUTTON_STATE_COUNT
        self.autocastoverlayimage = None
        
        self.RecalculateCurrentImage()
        
    def ApplySchemeSettings(self, scheme):
        super().ApplySchemeSettings(scheme)
        
        self.SetBorder(None)
        
    def SetImage(self, type, image, color=None):
        changed = False
        if image != self.images[type]:
            self.images[type] = image
            changed = True
        
        if changed:
            self.RecalculateCurrentImage()
            
    def SetAllImages(self, image, color=None):
        changed = False
        for i in range(0, self.BUTTON_STATE_COUNT):
            if image != self.images[i]:
                changed = True
            self.images[i] = image
            
        if changed: 
            self.RecalculateCurrentImage()
        
    def SetOverlayImage(self, type, image, color=None):
        """ Draws an image on top of the main image. Should be transparant, mainly to be used with mouse over. """    
        self.overlayimages[type] = image   
        self.RecalculateCurrentImage()
        
    def SetAutocastOverlayImage(self, image):
        self.autocastoverlayimage = image
        self.RecalculateCurrentImage()
        
    def SetEnabled(self, enabled):
        super().SetEnabled(enabled)
        self.RecalculateCurrentImage()
            
    def SetArmed(self, state):
        super().SetArmed(state)
        self.RecalculateCurrentImage()

    def RecalculateDepressedState(self):
        super().RecalculateDepressedState()
        self.RecalculateCurrentImage()
        
    def RecalculateCurrentImage(self):
        """ Determines the image to use based on the state """
        self.buttonteamcolor = None
        self.currentimage = self.images[self.BUTTON_ENABLED]
        self.currentoverlayimage = self.overlayimages[self.BUTTON_ENABLED]
        if self.IsArmed():
            if self.IsDepressed():
                self.currentimage = self.images[self.BUTTON_PRESSED]
                self.currentoverlayimage = self.overlayimages[self.BUTTON_PRESSED]
            else:
                self.currentimage = self.images[self.BUTTON_ENABLED_MOUSE_OVER]
                self.currentoverlayimage = self.overlayimages[self.BUTTON_ENABLED_MOUSE_OVER]
        elif self.IsEnabled() == False:
            self.buttonteamcolor = Vector(1, 0, 0)
            self.currentimage = self.images[self.BUTTON_DISABLED]
            self.currentoverlayimage = self.overlayimages[self.BUTTON_DISABLED]
        self.FlushSBuffer()
        
    def Paint(self):    
        x, y = self.GetPos()
        w, h = self.GetSize()
        
        if self.currentimage:
            self.currentimage.DrawSelf(0, 0, w, h, whitecolor)
        if self.buttonteamcolor:
            surface().SetProxyUITeamColor(self.buttonteamcolor)
        else:
            surface().ClearProxyUITeamColor()
        if self._iconimage:
            self._iconimage.DoPaint(int(w*self.iconcoords[0]), int(h*self.iconcoords[1]),
                                    int(w*self.iconcoords[2]), int(w*self.iconcoords[2]))
        if self.currentoverlayimage:
            self.currentoverlayimage.DrawSelf(0, 0, w, h, whitecolor)
            
        if self.autocastoverlayimage:
            self.autocastoverlayimage.DrawSelf(0, 0, w, h, whitecolor)

        super().Paint()

    def PaintBackground(self):
        pass 
        
    _iconimage = None
    @property
    def iconimage(self):
        return self._iconimage
    @iconimage.setter
    def iconimage(self, iconimage):
        if iconimage == self._iconimage:
            return
        self._iconimage = iconimage
        self.FlushSBuffer()
        
    iconcoords = (0.1, 0.1, 0.8) # X, Y, Size Wide -> also applied to height.
    
    # Right click command support
    def SetCommandRightClick(self, command):
        if type(command) == str:
            command = KeyValues("Command", "command", command)
        
        self._actionmessageright = command
        
    def FireActionSignalRightClick(self):
        """ Message targets that the button has been pressed """
        # message-based action signal
        if self._actionmessageright:
            self.PostActionSignal(KeyValues(self._actionmessageright))

    def DoClickRight(self):
        """ Purpose: Activate a button click. """
        self.SetSelected(True)
        self.FireActionSignalRightClick()
        self.PlayButtonReleasedSound()
        self.SetSelected(False)
        
    def ByPassNotEnabled(self, code):
        return self.alwaysallowrightclick and code == ButtonCode_t.MOUSE_RIGHT
        
    def OnMousePressed(self, code):
        if not self.IsEnabled() and not self.ByPassNotEnabled(code):
            return
        
        if not self.IsMouseClickEnabled(code):
            return

        if self._activationtype == self.ACTIVATE_ONPRESSED:
            if self.IsKeyBoardInputEnabled():
                self.RequestFocus()
            if code == MOUSE_RIGHT:
                self.DoClickRight()
            else:
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
        if (self.IsEnabled() or self.ByPassNotEnabled(code)) and (self.GetVPanel() == vgui_input().GetMouseOver() or self._buttonflags.IsFlagSet( self.BUTTON_KEY_DOWN )):
            if code == MOUSE_RIGHT:
                self.DoClickRight()
            else:
                self.DoClick()
        else:
            self.SetSelected(False)

        # make sure the button gets unselected
        self.Repaint()
        
    _actionmessageright = None

    # Button states
    BUTTON_ENABLED = 0
    BUTTON_ENABLED_MOUSE_OVER = 1
    BUTTON_PRESSED = 2
    BUTTON_DISABLED = 3

    BUTTON_STATE_COUNT = 4
    
    alwaysallowrightclick = True
    buttonteamcolor = None

