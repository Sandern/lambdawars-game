from vgui.controls import Button

class BitmapButton(Button):
    def __init__(self, parent = None, name = None, text = None):
        Button.__init__(self, parent, name, text)
        
        self.SetPaintBackgroundEnabled(False)
        
        self.images = [None]*self.BUTTON_STATE_COUNT
        self.overlayimages = [None]*self.BUTTON_STATE_COUNT
        
        self.RecalculateCurrentImage()
            
    def SetImage(self, type, image, color):
        changed = False
        if image != self.images[type]:
            self.images[type] = image
            changed = True
            
        if self.images[type] and self.images[type].GetColor() != color:
            self.images[type].SetColor( color )
            changed = True
        
        if changed:
            self.RecalculateCurrentImage()
            
    def SetAllImages(self, image, color):
        changed = False
        for i in range(0, self.BUTTON_STATE_COUNT):
            if image != self.images[i]:
                changed = True
            self.images[i] = image
        
        if image and image.GetColor() != color:
            image.SetColor( color )
            changed = True
            
        if changed: 
            self.RecalculateCurrentImage()
        
    def SetOverlayImage(self, type, image, color):
        """ Draws an image on top of the main image. Should be transparant, mainly to be used with mouse over. """    
        self.overlayimages[type] = image
        if self.overlayimages[type]:
            self.overlayimages[type].SetColor( color )     
        self.RecalculateCurrentImage()
        
    def SetEnabled(self, enabled):
        super(BitmapButton, self).SetEnabled(enabled)
        self.RecalculateCurrentImage()
            
    def SetArmed(self, state):
        super(BitmapButton, self).SetArmed(state)
        self.RecalculateCurrentImage()

    def RecalculateDepressedState(self):
        super(BitmapButton, self).RecalculateDepressedState()
        self.RecalculateCurrentImage()
        
    def RecalculateCurrentImage(self):
        """ Determines the image to use based on the state """
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
            self.currentimage = self.images[self.BUTTON_DISABLED]
            self.currentoverlayimage = self.overlayimages[self.BUTTON_DISABLED]
        self.FlushSBuffer()

    def Paint(self):    
        if self.currentimage:
            self.currentimage.DoPaint(self.GetVPanel())
        if self.currentoverlayimage:
            self.currentoverlayimage.DoPaint(self.GetVPanel())

        super(BitmapButton, self).Paint()

    def PaintBackground(self):
        pass 
        
    # Button states
    BUTTON_ENABLED              = 0
    BUTTON_ENABLED_MOUSE_OVER   = 1
    BUTTON_PRESSED              = 2
    BUTTON_DISABLED             = 3

    BUTTON_STATE_COUNT          = 4
