from srcbase import Color, KeyValues
from vgui import INVALID_FONT, scheme, localize, surface, vgui_input
from vgui.controls import Panel, TextImage

class TImageInfo(object):
    image = None
    offset = 0
    xpos = 0
    width = 0

class Label(Panel):
    # Alignment
    a_northwest = 0
    a_north = 1
    a_northeast = 2
    a_west = 3
    a_center = 4
    a_east = 5
    a_southwest = 6
    a_south = 7
    a_southeast = 8
    
    # Color state
    CS_NORMAL = 0
    CS_DULL = 1
    CS_BRIGHT = 2
    
    # the +8 is padding to the content size
    # the code which uses it should really set that itself; 
    # however a lot of existing code relies on this
    Content = 8

    def __init__(self, parent, panelName, text):
        super(Label, self).__init__(parent, panelName)
        
        self.EnableSBuffer(True)
        
        self._disabledfgcolor1 = Color()
        self._disabledfgcolor2 = Color()
        
        self._imagedar = []
        
        self._textimage = TextImage(text)
        self._textimage.SetColor(Color(0, 0, 0, 0))
        
        self.SetText(text)
        self._textimageindex = self.AddImage(self._textimage, 0)
        
        self.Init()

    def Init(self):
        """ Construct the label """
        self._contentalignment = self.a_west
        self._textcolorstate = self.CS_NORMAL
        self._textinset = [0, 0]
        self._hotkey = 0
        self._associate = None
        self._associatename = None
        self.fontoverridename = None
        self.wrap = False
        self.centerwrap = False
        # SetPaintBackgroundEnabled(False)

    def SetTextColorState(self, state):
        """ Set whether the text is displayed bright or dull """
        if self._textcolorstate != state:
            self._textcolorstate = state
            self.InvalidateLayout()

    def GetContentSize(self):
        """ Return the full size of the contained content """
        if self.GetFont() == INVALID_FONT: # we haven't loaded our font yet, so load it now
            pScheme = scheme().GetIScheme(self.GetScheme())
            if pScheme:
                self.SetFont(pScheme.GetFont("Default", self.IsProportional()))

        tx0, ty0, tx1, ty1 = self.ComputeAlignment()

        # the +8 is padding to the content size
        # the code which uses it should really set that itself 
        # however a lot of existing code relies on self
        wide = (tx1 - tx0) + self._textinset[0] 

        # get the size of the text image and remove it
        iWide, iTall = self._textimage.GetSize()
        wide -=  iWide
        # get the full, untruncated (no elipsis) size of the text image.
        iWide, iTall = self._textimage.GetContentSize()
        wide += iWide

        # addin the image offsets as well
        for img in self._imagedar:
            wide += img.offset

        tall = max((ty1 - ty0) + self._textinset[1], iTall)
        return int(wide), int(tall)
    
    def CalculateHotkey(self, text):
        """ Calculate the keyboard key that is a hotkey  """
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == '&':
                # get the next character
                i += 1
                ch = text[i]

                if ch == '&':
                    # just an &
                    i += 1
                    continue
                elif ch == 0:
                    break
                elif ch.isalnum():
                    # found the hotkey
                    return ch.lower()
            i += 1
            
        return '\0'

    def HasHotkey(self, key):
        """ Check if this label has a hotkey that is the key passed in. """
        if key.isalnum():
            key = key.lower()

        if self._hotkey == key:
            return self

        return None
    
    def SetHotkey(self, ch):
        """ Set the hotkey for self label """
        self._hotkey = ch

    def OnHotkeyPressed(self):
        """ Handle a hotkey by passing on focus to associate """
        # we can't accept focus, but if we are associated to a control give it to that
        if self._associate and not self.IsBuildModeActive():
            self._associate.RequestFocus()

    def OnMousePressed(self, code):
        """ Redirect mouse pressed to giving focus to associate """
        if self._associate and not self.IsBuildModeActive():
            self._associate.RequestFocus()

    def GetText(self):
        """ Return the text in the label """
        return self._textimage.GetText()

    def SetText(self, text):
        """ Take the string and looks it up in the localization file 
            to convert it to unicode
            Setting the text will not set the size of the label.
            Set the size explicitly or use setToContent() """
        # if set to None, just make blank
        if not text:
            text = ""

        if text and text[0] == '#':
            text = localize.Find(text)

        # let the text image do the translation itself
        self._textimage.SetText(text)

        self.SetHotkey(self.CalculateHotkey(text))
        
        self.InvalidateLayout()
        self.Repaint()
        self.FlushSBuffer()

    def OnDialogVariablesChanged(self, dialogVariables):
        """ updates localized text """
        index = self._textimage.GetUnlocalizedTextSymbol()
        if index != INVALID_STRING_INDEX:
            # reconstruct the string from the variables
            buf = localize.ConstructString(index, dialogVariables)
            self.SetText(buf)

    def SetTextInset(self, xInset, yInset):
        """ Additional offset at the Start of the text (from whichever side it is aligned) """
        self._textinset[0] = xInset
        self._textinset[1] = yInset

        wide, tall = self.GetSize()
        self._textimage.SetDrawWidth(wide - self._textinset[0])

    def SetEnabled(self, state):
        """ Set the enabled state """
        super(Label, self).SetEnabled(state)

    testleftactual = set([a_northwest, a_west, a_southwest])
    testcenteractual = set([a_north, a_center, a_south])
    testyaligntextactual = set([a_northeast, a_east, a_southeast])

    testtop = set([a_northwest, a_north, a_northeast])
    testcenter = set([a_west, a_center, a_east])
    testsouth = set([a_southwest, a_south, a_southeast])

    def ComputeAlignment(self):
        """ Calculates where in the panel the content resides 
            Note:   horizontal alignment is west if the image dar has
                    more than one image in it, self is because we use image sizes
                    to determine layout in classes for example, Menu. """
        wide, tall = self.GetPaintSize()

        # text bounding box
        tx0 = 0
        ty0 = 0

        # loop through all the images and calculate the complete bounds
        maxX = maxY = 0

        actualXAlignment = self._contentalignment
        for imageInfo in self._imagedar:
            image = imageInfo.image
            if not image:
                continue # skip over None images

            # add up the bounds
            iWide, iTall = image.GetSize()
            if iWide > wide: # if the image is larger than the label just do a west alignment
                actualXAlignment = Label.a_west
            
            # get the max height
            maxY = max(maxY, iTall)
            maxX += iWide

            # add the offset to x
            maxX += imageInfo.offset

        tWide = maxX
        tTall = maxY
        
        # x align text
        if actualXAlignment in self.testleftactual:
            # left
            tx0 = 0
        elif actualXAlignment in self.testcenteractual:
            # center
            tx0 = (wide - tWide) / 2
        elif actualXAlignment in self.testyaligntextactual:
            # y align text
            tx0 = wide - tWide
            
        contentalignment = self._contentalignment
        if contentalignment in self.testtop:
            # top
            ty0 = 0
        elif contentalignment in self.testcenter:
            # center
            ty0 = (tall - tTall) / 2
        elif contentalignment in self.testsouth:
            # south
            ty0 = tall - tTall

        tx1 = tx0 + tWide
        ty1 = ty0 + tTall
        
        return tx0, ty0, tx1, ty1

    testtextinsetleft = set([a_northwest, a_west, a_southwest])
    testtextinsetright = set([a_northeast, a_east, a_southeast])
    testfixupy = set([a_west, a_center, a_east])
    def Paint(self):
        """ overridden main drawing function for the panel """
        tx0, ty0, tx1, ty1 = self.ComputeAlignment()

        # calculate who our associate is if we haven't already
        if self._associatename:
            self.SetAssociatedControl(self.FindSiblingByName(self._associatename))
            self._associatename = None
        
        labelWide, labelTall = self.GetSize()
        x = tx0
        y = int(self._textinset[1] + ty0)
        imageYPos = 0 # a place to save the y offset for when we draw the disable version of the image

        # draw the set of images
        for i, imageInfo in enumerate(self._imagedar):
            image = imageInfo.image
            if not image:
                continue # skip over None images

            # add the offset to x
            x += imageInfo.offset
            
            contentalignment = self._contentalignment

            # if this is the text image then add its inset to the left or from the right
            if i == self._textimageindex:
                if contentalignment in self.testtextinsetleft:
                    # left
                    x += self._textinset[0]
                elif contentalignment in self.testtextinsetright:
                    # right
                    x -= self._textinset[0]
                    break

            # see if the image is in a fixed position
            if imageInfo.xpos >= 0:
                x = imageInfo.xpos
                
            # draw
            imageYPos = y
            image.SetPos(x, y)

            # fix up y for center-aligned text
            if contentalignment in self.testfixupy:
                iw, it = image.GetSize()
                if it < (ty1 - ty0):
                    imageYPos = int(((ty1 - ty0) - it) / 2 + y)
                    image.SetPos(x, imageYPos)

            # don't resize the image unless its too big
            if imageInfo.width >= 0:
                w, t = image.GetSize()
                if w > imageInfo.width:
                    image.SetSize(imageInfo.width, t)

            # if it's the basic text image then draw specially
            textimage = self._textimage
            if image == textimage:
                if self.IsEnabled():
                    if self._associate and ipanel().HasParent(vgui_input().GetFocus(), self._associate.GetVPanel()):
                        textimage.SetColor(self._associateColor)
                    else:
                        textimage.SetColor(self.GetFgColor())
                    textimage.Paint()
                else:
                    # draw disabled version, with embossed look
                    # offset image
                    textimage.SetPos(x + 1, imageYPos + 1)
                    textimage.SetColor(self._disabledfgcolor1)
                    textimage.Paint()

                    surface().DrawFlushText()

                    # overlayed image
                    textimage.SetPos(x, imageYPos)
                    textimage.SetColor(self._disabledfgcolor2)
                    textimage.Paint()
            else:
                image.Paint()

            # add the image size to x
            wide, tall = image.GetSize()
            x += wide

    def DrawDashedLine(self, x0, y0, x1, y1, dashLen, gapLen):
        """ Helper function, draws a simple line with dashing parameters """
        # work out which way the line goes
        if (x1 - x0) > (y1 - y0):
            # x direction line
            while 1:
                if x0 + dashLen > x1:
                    # draw partial
                    surface().DrawFilledRect(x0, y0, x1, y1)
                else:
                    surface().DrawFilledRect(x0, y0, x0 + dashLen, y1)

                x0 += dashLen

                if x0 + gapLen > x1:
                    break

                x0 += gapLen
        else:
            # y direction
            while 1:
                if y0 + dashLen > y1:
                    # draw partial
                    surface().DrawFilledRect(x0, y0, x1, y1)
                else:
                    surface().DrawFilledRect(x0, y0, x1, y0 + dashLen)

                y0 += dashLen

                if y0 + gapLen > y1:
                    break

                y0 += gapLen

    def SetContentAlignment(self, alignment):
        self._contentalignment=alignment
        self.Repaint()
        self.FlushSBuffer()

    def SizeToContents(self):
        """ Size the width of the label to its contents - only works from in ApplySchemeSettings or PerformLayout() """
        wide, tall = self.GetContentSize()

        self.SetSize(wide, tall)

    def SetFont(self, font):
        """ Set the font the text is drawn in """
        self._textimage.SetFont(font)
        self.Repaint()
        self.FlushSBuffer()

    def OnSizeChanged(self, wide, tall):
        """ Resond to resizing of the panel """
        self.InvalidateLayout()
        super(Label, self).OnSizeChanged(wide, tall)
    
    def GetFont(self):
        """ Get the font the textImage is drawn in. """
        return self._textimage.GetFont()

    def SetFgColor(self, color):
        """ Set the foreground color of the Label """
        if not self.GetFgColor() == color:
            super(Label, self).SetFgColor(color)
            self._textimage.SetColor(color)
            self.Repaint()
            self.FlushSBuffer()

    def GetFgColor(self):
        """ Get the foreground color of the Label """
        clr = super(Label, self).GetFgColor()
        return clr

    def SetDisabledFgColor1(self, color):
        """ Set the foreground color 1 color of the Label """
        self._disabledfgcolor1 = color
        self.FlushSBuffer()

    def SetDisabledFgColor2(self, color):
        self._disabledfgcolor2 = color
        self.FlushSBuffer()

    def GetDisabledFgColor1(self):
        return self._disabledfgcolor1

    def GetDisabledFgColor2(self):
        return self._disabledfgcolor2

    def GetTextImage(self):
        return self._textimage

    def RequestInfo(self, outputData):
        if outputData.GetName() == 'GetText':
            outputData.SetWString("text", self._textimage.GetText())
            return True

        return super(Label, self).RequestInfo(outputData)

    def OnSetText(self, params):
        """ Sets the text from the message """
        pkvText = params.FindKey("text", False)
        if not pkvText:
            return

        if pkvText.GetDataType() == KeyValues.TYPE_STRING:
            self.SetText(pkvText.GetString())
        elif pkvText.GetDataType() == KeyValues.TYPE_WSTRING:
            self.SetText(pkvText.GetWString())

    def AddImage(self, image, offset):
        """ Add an image to the list
            returns the index the image was placed in """
        self._imagedar.append(TImageInfo())
        newImage = len(self._imagedar)-1
        self._imagedar[newImage].image = image
        self._imagedar[newImage].offset = int(offset)
        self._imagedar[newImage].xpos = -1
        self._imagedar[newImage].width = -1
        self.InvalidateLayout()
        return newImage
        
    def ClearImages(self):
        """ removes all images from the list
            user is responsible for the memory """
        self._imagedar = []
        self._textimageindex = -1

    def ResetToSimpleTextImage(self):
        self.ClearImages()
        self._textimageindex = self.AddImage(self._textimage, 0)

    def SetImageAtIndex(self, index, image, offset):
        """ Multiple image handling
            Images are drawn from left to right across the label, ordered by index
            By default there is a TextImage in position 0
            Set the contents of an IImage in the IImage array """
        self.EnsureImageCapacity(index)
        assert( image )
        if self._imagedar[index].image != image or self._imagedar[index].offset != offset:
            self._imagedar[index].image = image
            self._imagedar[index].offset = int(offset)
            self.InvalidateLayout()

    def GetImageAtIndex(self, index):
        """ Get an IImage in the IImage array. """
        try:
            return self._imagedar[index].image
        except IndexError:
            return None

    def GetImageCount(self):
        """ Get the number of images in the array. """
        return len(self._imagedar)
    
    def SetTextImageIndex(self, newIndex):
        """ Move where the default text image is within the image array 
            (it starts in position 0) 
            Output: the index the default text image was previously in """
        if newIndex == self._textimageindex:
            return self._textimageindex

        self.EnsureImageCapacity(newIndex)

        oldIndex = self._textimageindex
        if self._textimageindex >= 0:
            self._imagedar[self._textimageindex].image = None
        if newIndex > -1:
            self._imagedar[newIndex].image = self._textimage
        self._textimageindex = newIndex
        return oldIndex

    def EnsureImageCapacity(self, maxIndex):
        """ Ensure that the maxIndex will be a valid index """
        while len(self._imagedar) <= maxIndex:
            self.AddImage(None, 0)

    def SetImagePreOffset(self, index, preOffset):
        """ Set the offset in pixels before the image """
        if self._imagedar.IsValidIndex(index) and self._imagedar[index].offset != preOffset:
            self._imagedar[index].offset = int(preOffset)
            self.InvalidateLayout()

    def SetImageBounds(self, index, x, width):
        """ fixes the layout bounds of the image within the label """
        self._imagedar[index].xpos = int(x)
        self._imagedar[index].width = int(width)

    def SetAssociatedControl(self, control):
        """ Labels can be associated with controls, and alter behaviour based on the associates behaviour
            If the associate is disabled, so are we
            If the associate has focus, we may alter how we draw
            If we get a hotkey press or focus message, we forward the focus to the associate """
        if control != self:
            self._associate = control
        else:
            # don't let the associate ever be set to be ourself
            self._associate = None
            
    def OnRequestFocus(self, subFocus, defaultPanel):
        """ Called after a panel requests focus to fix up the whole chain """
        if self._associate and subFocus == self.GetVPanel() and not self.IsBuildModeActive():
            # we've received focus pass the focus onto the associate instead
            self._associate.RequestFocus()
        else:
            super(Label, self).OnRequestFocus(subFocus, defaultPanel)

    def ApplySchemeSettings(self, pScheme):
        """ sets custom settings from the scheme file """
        super(Label, self).ApplySchemeSettings(pScheme)

        if self.fontoverridename:
            # use the custom specified font since we have one set
            self.SetFont(pScheme.GetFont(self.fontoverridename, self.IsProportional()))
        if self.GetFont() == INVALID_FONT:
            self.SetFont( pScheme.GetFont( "Default", self.IsProportional() ) )

        if self.wrap or self.centerwrap:
            #tell it how big it is
            wide, tall = Panel.GetSize(self)
            wide -= self._textinset[0]		# take inset into account
            self._textimage.SetSize(wide, tall)

            self._textimage.RecalculateNewLinePositions()
        else:
            # if you don't set the size of the image, many, many buttons will break - we might want to look into fixing self all over the place later
            wide, tall = self._textimage.GetContentSize()
            self._textimage.SetSize(wide, tall)

        # clear out any the images, since they will have been invalidated
        for i, imginfo in enumerate(self._imagedar):
            image = imginfo.image
            if not image:
                continue # skip over None images

            if i == self._textimageindex:
                continue

            self._imagedar[i].image = None

        self.SetDisabledFgColor1(self.GetSchemeColor("Label.DisabledFgColor1", pScheme))
        self.SetDisabledFgColor2(self.GetSchemeColor("Label.DisabledFgColor2", pScheme))
        self.SetBgColor(self.GetSchemeColor("Label.BgColor", pScheme))

        if self._textcolorstate == self.CS_DULL:
            self.SetFgColor(self.GetSchemeColor("Label.TextDullColor", pScheme))
        elif self._textcolorstate == self.CS_BRIGHT:
            SetFgColor(self.GetSchemeColor("Label.TextBrightColor", pScheme))
        else: # self._textcolorstate == self.CS_NORMAL:
            self.SetFgColor(self.GetSchemeColor("Label.TextColor", pScheme))

        self._associateColor = self.GetSchemeColor("Label.SelectedTextColor", pScheme)

    def GetSettings(self, outResourceData):
        # panel settings
        super(Label, self).GetSettings(outResourceData)

        # label settings
        buf = self._textimage.GetUnlocalizedText()
        if buf.lower().startswith("#var_"):
            # strip off the variable prepender on save
            outResourceData.SetString( "labelText", buf + 5 )
        else:
            outResourceData.SetString( "labelText", buf )
        
        alignmentString = ""
        if self._contentalignment == self.a_northwest:
            alignmentString = "north-west"
        elif self._contentalignment == self.a_north:
            alignmentString = "north"
        elif self._contentalignment == self.a_northeast:
            alignmentString = "north-east"
        elif self._contentalignment == self.a_center:
            alignmentString = "center"
        elif self._contentalignment == self.a_east:
            alignmentString = "east"
        elif self._contentalignment == self.a_southwest:
            alignmentString = "south-west"
        elif self._contentalignment == self.a_south:
            alignmentString = "south"
        elif self._contentalignment == self.a_southeast:
            alignmentString = "south-east"
        else: # self._contentalignment == self.a_west:
            alignmentString = "west"

        outResourceData.SetString( "textAlignment", alignmentString )

        if self._associate:
            outResourceData.SetString("associate", self._associate.GetName())

        outResourceData.SetInt("dulltext", int(self._textcolorstate == self.CS_DULL))
        outResourceData.SetInt("brighttext", int(self._textcolorstate == self.CS_BRIGHT))

        if self.fontoverridename:
            outResourceData.SetString("font", self.fontoverridename)
        
        outResourceData.SetInt("wrap", ( int(self.wrap) ))
        outResourceData.SetInt("centerwrap", ( int(self.centerwrap) ))

        outResourceData.SetInt("textinsetx", self._textinset[0])
        outResourceData.SetInt("textinsety", self._textinset[1])

    def ApplySettings(self, inResourceData):
        super(Label, self).ApplySettings(inResourceData)

        # label settings
        labelText = inResourceData.GetString( "labelText", None )
        if labelText:
            if labelText[0] == '%' and labelText[len(labelText) - 1] == '%':
                # it's a variable, set it to be a special variable localized string
                unicodeVar = localize.ConvertANSIToUnicode(labelText)

                var = "#var_%s" % (labelText)
                localize.AddString(var[1:], unicodeVar, "")
                self.SetText(var)
            else:
                self.SetText(labelText)
                
        # text alignment
        alignmentString = inResourceData.GetString( "textAlignment", "" )
        align = -1

        if alignmentString == "north-west":
            align = self.a_northwest
        elif alignmentString == "north":
            align = self.a_north
        elif alignmentString == "north-east":
            align = self.a_northeast
        elif alignmentString == "west":
            align = self.a_west
        elif alignmentString == "center":
            align = self.a_center
        elif alignmentString == "east":
            align = self.a_east
        elif alignmentString == "south-west":
            align = self.a_southwest
        elif alignmentString == "south":
            align = self.a_south
        elif alignmentString == "south-east":
            align = self.a_southeast

        if align != -1:
            self.SetContentAlignment(align)

        # the control we are to be associated with may not have been created yet,
        # so keep a pointer to it's name and calculate it when we can
        associateName = inResourceData.GetString("associate", "")
        if associateName[0] != 0:
            self._associatename = str(associateName)
        if inResourceData.GetInt("dulltext", 0) == 1:
            self.SetTextColorState(self.CS_DULL)
        elif inResourceData.GetInt("brighttext", 0) == 1:
            self.SetTextColorState(self.CS_BRIGHT)
        else:
            self.SetTextColorState(self.CS_NORMAL)

        # font settings
        overrideFont = inResourceData.GetString("font", "")
        IpScheme = scheme().GetIScheme( self.GetScheme() )

        if overrideFont:
            self.fontoverridename = str(overrideFont)
            SetFont(pScheme.GetFont(self.fontoverridename, self.IsProportional()))
        elif self.fontoverridename:
            self.fontoverridename = None
            self.SetFont(pScheme.GetFont("Default", self.IsProportional()))

        bWrapText = inResourceData.GetInt("centerwrap", 0) > 0
        self.SetCenterWrap( bWrapText )

        bWrapText = inResourceData.GetInt("wrap", 0) > 0
        self.SetWrap( bWrapText )

        inset_x = inResourceData.GetInt("textinsetx", self._textinset[0])
        inset_y = inResourceData.GetInt("textinsety", self._textinset[1])
        self.SetTextInset( inset_x, inset_y )

        self.InvalidateLayout(True)

    def GetDescription(self):
        """ Returns a description of the label string """
        return "%s, string labelText, string associate, alignment textAlignment, int wrap, int dulltext, int brighttext, string font" % (super(Label, self).GetDescription())

    def PerformLayout(self):
        """ If a label has images in self._imagedar, the size
            must take those into account as well as the textImage part
            Textimage part will shrink ONLY if there is not enough room. """
        wide, tall = Panel.GetSize(self)
        wide -= self._textinset[0] # take inset into account

        # if we just have a textImage, this is trivial.
        if len(self._imagedar) == 1 and self._textimageindex == 0:
            if self.wrap or self.centerwrap:
                twide, ttall = self._textimage.GetContentSize()
                self._textimage.SetSize(wide, ttall)
            else:
                twide, ttall = self._textimage.GetContentSize()
                
                # tell the textImage how much space we have to draw in
                if wide < twide:
                    self._textimage.SetSize(wide, ttall)
                else:
                    self._textimage.SetSize(twide, ttall)
            return

        # assume the images in the dar cannot be resized, and if
        # the images + the textimage are too wide we shring the textimage part
        if self._textimageindex < 0:
            return
        
        # get the size of the images
        widthOfImages = 0
        for i, imageInfo in enumerate(self._imagedar):
            image = imageInfo.image
            if not image:
                continue # skip over None images

            if i == self._textimageindex:
                continue

            # add up the bounds
            iWide, iTall = image.GetSize()		
            widthOfImages += iWide
        

        # so self is how much room we have to draw the textimage part
        spaceAvail = wide - widthOfImages

        # if we have no space at all just leave everything as is.
        if spaceAvail < 0:
            return

        twide, ttall = self._textimage.GetSize()
        # tell the textImage how much space we have to draw in
        self._textimage.SetSize(spaceAvail, ttall)	
    

    def SetWrap(self, bWrap):
        self.wrap = bWrap
        self._textimage.SetWrap( self.wrap )

        self.InvalidateLayout()

    def SetCenterWrap(self, bWrap):
        self.centerwrap = bWrap
        self._textimage.SetCenterWrap( self.centerwrap )

        self.InvalidateLayout()
    