""" Panel that holds a single image """ 
from srcbase import Color
from vgui import scheme, surface
from vgui.controls import Panel

class ImagePanel(Panel):
    def __init__(self, parent, name):
        super(ImagePanel, self).__init__(parent, name)
        
        self.image = None
        self.imagename = None
        self.colorname = None
        self.scaleimage = False
        self.tileimage = False
        self.tilehorizontally = False
        self.tilevertically = False
        self.scaleamount = 0.0
        self.fillcolor = Color(0, 0, 0, 0)
        self.drawcolor = Color(255,255,255,255)

        self.SetImage(self.image)
        
        self.EnableSBuffer(False)

    def SetImage(self, image):
        """ sets an image by file name or image ref """
        if type(image) == str:
            if self.imagename == image:
                return
            self.imagename = image
            self.InvalidateLayout(False, True) # force applyschemesettings to run
        else:
            self.image = image
            self.Repaint()
            self.FlushSBuffer()

    def PaintBackground(self):
        if self.fillcolor[3] > 0:
            # draw the specified fill color
            wide, tall = self.GetSize()
            surface().DrawSetColor(self.fillcolor)
            surface().DrawFilledRect(0, 0, wide, tall)
        if self.image:
            surface().DrawSetColor(255, 255, 255, 255)
            self.image.SetPos(0, 0)

            if self.scaleimage:
                # Image size is stored in the bitmap, so temporarily set its size
                # to our panel size and then restore after we draw it.

                imageWide, imageTall = self.image.GetSize()

                if self.scaleamount > 0.0:
                    wide = imageWide * self.scaleamount
                    tall = imageTall * self.scaleamount
                    self.image.SetSize(int(wide), int(tall))
                else:
                    wide, tall = self.GetSize()
                    self.image.SetSize(wide, tall)

                self.image.SetColor(self.drawcolor)
                self.image.Paint()

                self.image.SetSize( imageWide, imageTall )
            elif self.tileimage or self.tilehorizontally or self.tilevertically:
                wide, tall = self.GetSize()
                imageWide, imageTall = self.image.GetSize()

                y = 0
                while y < tall:
                    x = 0
                    while x < wide:
                        self.image.SetPos(x,y)
                        self.image.Paint()

                        x += imageWide

                        if not self.tilehorizontally:
                            break

                    y += imageTall

                    if not self.tilevertically:
                        break
                self.image.SetPos(0, 0)
            else:
                self.image.Paint()

    def GetSettings(self, outResourceData):
        """ Gets control settings for editing """
        super(ImagePanel, self).GetSettings(outResourceData)
        if self.imagename:
            outResourceData.SetString("image", self.imagename)
        if self.colorname:
            outResourceData.SetString("fillcolor", self.colorname)
        if self.GetBorder():
            outResourceData.SetString("border", self.GetBorder().GetName())

        outResourceData.SetInt("scaleImage", self.scaleimage)
        outResourceData.SetFloat("scaleAmount", self.scaleamount)
        outResourceData.SetInt("tileImage", self.tileimage)
        outResourceData.SetInt("tileHorizontally", self.tilehorizontally)
        outResourceData.SetInt("tileVertically", self.tilevertically)

    def ApplySettings(self, inResourceData):
        """ Applies designer settings from res file """
        self.imagename = None
        self.colorname = None

        self.scaleimage = inResourceData.GetInt("scaleImage", 0)
        self.scaleamount = inResourceData.GetFloat("scaleAmount", 0.0)
        self.tileimage = inResourceData.GetInt("tileImage", 0)
        self.tilehorizontally = inResourceData.GetInt("tileHorizontally", self.tileimage)
        self.tilevertically = inResourceData.GetInt("tileVertically", self.tileimage)
        imageName = inResourceData.GetString("image", "")
        if imageName:
            self.SetImage( imageName )

        pszFillColor = inResourceData.GetString("fillcolor", "")
        if pszFillColor:
            r = 0
            g = 0
            b = 0
            a = 255
            self.colorname = str(pszFillColor)

            # TODO: Convert to python equivalent. If we care about this method ofcourse.
            # if sscanf(pszFillColor, "%d %d %d %d", &r, &g, &b, &a) >= 3:
                # # it's a direct color
                # self.fillcolor = Color(r, g, b, a)
            # else:
                # pScheme = scheme().GetIScheme( self.GetScheme() )
                # self.fillcolor = pScheme.GetColor(pszFillColor, Color(0, 0, 0, 0))

        pszBorder = inResourceData.GetString("border", "")
        if pszBorder:
            pScheme = scheme().GetIScheme( GetScheme() )
            self.SetBorder(pScheme.GetBorder(pszBorder))

        super(ImagePanel, self).ApplySettings(inResourceData)

    def ApplySchemeSettings(self, schemeobj):
        """ load the image, this is done just before this control is displayed """
        super(ImagePanel, self).ApplySchemeSettings(schemeobj)
        if self.imagename and len(self.imagename) > 0:
            self.SetImage(scheme().GetImage(self.imagename, self.scaleimage))
