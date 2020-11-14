from srcbase import KeyValues
from vgui import INVALID_FONT, surface, scheme, vgui_input, localize
from vgui.controls import Panel, Label, TextImage, ScrollBar
from input import ButtonCode_t

BUTTON_HEIGHT_DEFAULT = 20
BUTTON_HEIGHT_SPACER = 7
SECTION_GAP = 8
COLUMN_DATA_INDENT = 6
COLUMN_DATA_GAP = 2

class column_t(object):
    def __init__(self):
        super(column_t, self).__init__()
        self.columnname = ""
        self.columntext = ""
        self.columnflags = 0
        self.width = 0
        self.fallbackfont = None
    
class section_t(object):
    def __init__(self):
        super(section_t, self).__init__()
        self.id = -1
        self.alwaysvisible = False
        self.header = None
        self.columns = []
        self.sortfunc = None

class CSectionHeader(Label):
    """ header label that separates and names each section """
    def __init__(self, parent, name, sectionID):
        super(CSectionHeader, self).__init__(parent, name, "CSectionHeader")
        
        self.listpanel = parent
        self.sectionid = sectionID
        self.SetTextImageIndex(-1)
        self.ClearImages()
        self.SetPaintBackgroundEnabled( False )

    def ApplySchemeSettings(self, schemeobj):
        super(CSectionHeader, self).ApplySchemeSettings(schemeobj)

        self.SetFgColor(self.GetSchemeColor("SectionedListPanel.HeaderTextColor", schemeobj))
        self.sectiondividercolor = self.GetSchemeColor("SectionedListPanel.DividerColor", schemeobj)
        self.SetBgColor(self.GetSchemeColor("SectionedListPanelHeader.BgColor", self.GetBgColor(), schemeobj))
        self.SetFont(schemeobj.GetFont("DefaultVerySmall", self.IsProportional()))
        self.ClearImages()

    def Paint(self):
        super(CSectionHeader, self).Paint()

        x, y, wide, tall = self.GetBounds()

        y = (tall - 2)	# draw the line under the panel

        surface().DrawSetColor(self.sectiondividercolor)
        surface().DrawFilledRect(1, y, self.GetWide() - 2, y + 1)

    def SetColor(self, col):
        self.sectiondividercolor = col
        self.SetFgColor(col)
    
    def SetDividerColor(self, col):
        self.sectiondividercolor = col

    def PerformLayout(self):
        super(CSectionHeader, self).PerformLayout()

        # set up the text in the header
        colCount = self.listpanel.GetColumnCountBySection(self.sectionid)
        if colCount != self.GetImageCount():
            # rebuild the image list
            for i in range(0, colCount):
                columnFlags = self.listpanel.GetColumnFlagsBySection(self.sectionid, i)
                image = None
                if columnFlags & SectionedListPanel.HEADER_IMAGE:
                    #!! need some kind of image reference
                    image = None
                else:
                    textImage = TextImage("")
                    textImage.SetFont(self.GetFont())
                    fallback = self.listpanel.GetColumnFallbackFontBySection( self.sectionid, i )
                    if INVALID_FONT != fallback:
                        textImage.SetUseFallbackFont( True, fallback )
                    textImage.SetColor(self.GetFgColor())
                    image = textImage
                self.SetImageAtIndex(i, image, 0)
                
        for repeat in range(0, 2):
            xpos = 0
            for i in range(0, colCount):
                columnFlags = self.listpanel.GetColumnFlagsBySection(self.sectionid, i)
                columnWidth = self.listpanel.GetColumnWidthBySection(self.sectionid, i)
                maxWidth = columnWidth
                
                image = self.GetImageAtIndex(i)
                if not image:
                    xpos += columnWidth
                    continue

                # set the image position within the label
                wide, tall = image.GetContentSize()
                contentWide = wide

                # see if we can draw over the next few column headers (if we're left-aligned)
                if not (columnFlags & SectionedListPanel.COLUMN_RIGHT):
                    for j in range(i+1, colCount):
                        # see if self column header has anything for a header
                        iwide = 0
                        itall = 0
                        if self.GetImageAtIndex(j):
                            iwide, itall = self.GetImageAtIndex(j).GetContentSize()
                        if iwide == 0:
                            # it's a blank header, ok to draw over it
                            maxWidth += self.listpanel.GetColumnWidthBySection(self.sectionid, j)

                if maxWidth >= 0:
                    wide = maxWidth

                if columnFlags & SectionedListPanel.COLUMN_RIGHT:
                    self.SetImageBounds(i, xpos + wide - contentWide, contentWide - COLUMN_DATA_GAP)
                else:
                    self.SetImageBounds(i, xpos, wide - COLUMN_DATA_GAP)
                xpos += columnWidth

                if not (columnFlags & SectionedListPanel.HEADER_IMAGE):
                    #Assert(dynamic_cast<TextImage *>(image) != None)
                    textImage = image
                    textImage.SetFont(self.GetFont()) 
                    textImage.SetText(self.listpanel.GetColumnTextBySection(self.sectionid, i))
                    textImage.ResizeImageToContentMaxWidth( maxWidth )

class CItemButton(Label):
    """ Individual items in the list """
    def __init__(self, parent, itemID):
        super(CItemButton, self).__init__(parent, None, "< item >")
        
        self.listpanel = parent
        self.id = itemID
        self.data = None
        self.Clear()
        
        self.textimages = []

    #def __del__(self):
        # free all the keyvalues
    #    self.data = None

        # clear any section data
    #    self.SetSectionID(-1)

    def Clear(self):
        self.selected = False
        self.overridecolors = False
        self.sectionid = -1
        self.SetPaintBackgroundEnabled( False )
        self.SetTextImageIndex(-1)
        self.ClearImages()

    def GetID(self):
        return self.id

    def SetID(self, itemID):
        self.id = itemID

    def GetSectionID(self):
        return self.sectionid

    def SetSectionID(self, sectionID):
        if sectionID != self.sectionid:
        
            # free any existing textimage list 
            self.ClearImages()
            # delete any images we've created
            self.textimages = []
            # mark the list as needing rebuilding
            self.InvalidateLayout()
        
        self.sectionid = sectionID

    def SetData(self, data):
        self.data = KeyValues(data)
        self.InvalidateLayout()

    def GetData(self):
        return self.data

    def PerformLayout(self):
        # get our button text
        colCount = self.listpanel.GetColumnCountBySection(self.sectionid)
        if not self.data or colCount < 1:
            self.SetText("< unset >")
        else:
            if colCount != self.GetImageCount():
                # rebuild the image list
                for i in range(0, colCount):
                    columnFlags = self.listpanel.GetColumnFlagsBySection(self.sectionid, i)
                    if not (columnFlags & SectionedListPanel.COLUMN_IMAGE):
                        image = TextImage("")
                        self.textimages.append(image)
                        image.SetFont( self.GetFont() )
                        fallback = self.listpanel.GetColumnFallbackFontBySection( self.sectionid, i )
                        if INVALID_FONT != fallback:        
                            image.SetUseFallbackFont( True, fallback ) 
                        self.SetImageAtIndex(i, image, 0)
                        
                for i in range(self.GetImageCount(), colCount):    # make sure we have enough image slots
                    self.AddImage( None, 0 )
                    
            # set the text for each column
            xpos = 0
            for i in range(0, colCount):
                keyname = self.listpanel.GetColumnNameBySection(self.sectionid, i)

                columnFlags = self.listpanel.GetColumnFlagsBySection(self.sectionid, i)
                maxWidth = self.listpanel.GetColumnWidthBySection(self.sectionid, i)
            
                image = None
                if columnFlags & SectionedListPanel.COLUMN_IMAGE: 
                    # lookup which image is being referred to
                    if self.listpanel.imagelist:
                        imageIndex = self.data.GetInt(keyname, 0)
                        if self.listpanel.imagelist.IsValidIndex(imageIndex):
                            # 0 is always the blank image
                            if imageIndex > 0:     
                                image = self.listpanel.imagelist.GetImage(imageIndex)
                                self.SetImageAtIndex(i, image, 0)
                        else:
                            # This is mildly valid (CGamesList hits it because of the way it uses the image indices)
                            assert(not("Image index out of range for ImageList in SectionedListPanel"))

                    else:
                        assert(not("Images columns used in SectionedListPanel with no ImageList set"))
                else:
                    textImage = self.GetImageAtIndex(i)
                    if textImage:
                        textImage.SetText(self.data.GetString(keyname, ""))
                        textImage.ResizeImageToContentMaxWidth( maxWidth )

                        # set the text color based on the selection state - if one of the children of the SectionedListPanel has focus, then 'we have focus' if we're selected
                        focus = vgui_input().GetFocus()
                        if not self.overridecolors: 
                            if self.IsSelected() and not self.listpanel.IsInEditMode():
                                if self.HasFocus() or (focus and ipanel().HasParent(focus, self.GetVParent())):
                                    textImage.SetColor(self.armedfgcolor2)
                                else:    
                                    textImage.SetColor(self.outoffocusselectedtextcolor)
                            
                            elif (columnFlags & SectionedListPanel.COLUMN_BRIGHT):
                                textImage.SetColor(self.armedfgcolor1)
                            else:
                                textImage.SetColor(self.fgcolor2)    
                        else: 
                            # custom colors
                            if self.IsSelected() and (self.HasFocus() or (focus and ipanel().HasParent(focus, self.GetVParent()))):
                                textImage.SetColor(self.armedfgcolor2)      
                            else:
                                textImage.SetColor(self.GetFgColor())

                    image = textImage

                # set the image position within the label
                imageWide = tall = 0
                if image:
                    imageWide, tall = image.GetContentSize()
                
                if maxWidth >= 0:
                    wide = maxWidth
                else:
                    wide = imageWide

                if i == 0 and not (columnFlags & SectionedListPanel.COLUMN_IMAGE):
                    # first column has an extra indent
                    self.SetImageBounds(i, xpos + COLUMN_DATA_INDENT, wide - (COLUMN_DATA_INDENT + COLUMN_DATA_GAP))
                else:
                    if columnFlags & SectionedListPanel.COLUMN_CENTER:
                        offSet = (wide / 2) - (imageWide / 2)
                        self.SetImageBounds(i, xpos + offSet, wide - offSet - COLUMN_DATA_GAP)
                    elif columnFlags & SectionedListPanel.COLUMN_RIGHT:
                        self.SetImageBounds(i, xpos + wide - imageWide, wide - COLUMN_DATA_GAP)
                    else:
                        self.SetImageBounds(i, xpos, wide - COLUMN_DATA_GAP)

                xpos += wide

        super(CItemButton, self).PerformLayout()

    def ApplySchemeSettings(self, schemeobj):
        super(CItemButton, self).ApplySchemeSettings(schemeobj)

        self.armedfgcolor1 = self.GetSchemeColor("SectionedListPanel.BrightTextColor", schemeobj)
        self.armedfgcolor2 = self.GetSchemeColor("SectionedListPanel.SelectedTextColor", schemeobj)
        self.outoffocusselectedtextcolor = self.GetSchemeColor("SectionedListPanel.OutOfFocusSelectedTextColor", schemeobj)
        self.armedbgcolor = self.GetSchemeColor("SectionedListPanel.SelectedBgColor", schemeobj)

        self.fgcolor2 = self.GetSchemeColor("SectionedListPanel.TextColor", schemeobj)

        self.bgcolor = self.GetSchemeColor("SectionedListPanel.BgColor", self.GetBgColor(), schemeobj)
        self.selectionbg2color = self.GetSchemeColor("SectionedListPanel.OutOfFocusSelectedBgColor", schemeobj)

        self.ClearImages()

    def PaintBackground(self):
        wide, tall = self.GetSize()

        if self.IsSelected() and not self.listpanel.IsInEditMode():
            focus = vgui_input().GetFocus()
            # if one of the children of the SectionedListPanel has focus, then 'we have focus' if we're selected
            if self.HasFocus() or (focus and ipanel().HasParent(focus, self.GetVParent())):
                surface().DrawSetColor(self.armedbgcolor)
            else:
                surface().DrawSetColor(self.selectionbg2color)
        else:
            surface().DrawSetColor(GetBgColor())
        surface().DrawFilledRect(0, 0, wide, tall)

    def Paint(self):
        super(CItemButton, self).Paint()

        if not self.showcolumns:
            return

        # Debugging code to show column widths
        wide, tall = self.GetSize()
        surface().DrawSetColor( 255,255,255,255 )
        surface().DrawOutlinedRect(0, 0, wide, tall)

        colCount = self.listpanel.GetColumnCountBySection(self.sectionid)
        if self.data and colCount >= 0:
            xpos = 0
            for i in range(0, colCount):
                keyname = self.listpanel.GetColumnNameBySection(self.sectionid, i)
                columnFlags = self.listpanel.GetColumnFlagsBySection(self.sectionid, i)
                maxWidth = self.listpanel.GetColumnWidthBySection(self.sectionid, i)

                image = None
                if columnFlags & SectionedListPanel.COLUMN_IMAGE:
                    # lookup which image is being referred to
                    if self.listpanel.imagelist:
                        imageIndex = self.data.GetInt(keyname, 0)
                        if self.listpanel.imagelist.IsValidIndex(imageIndex):
                            if imageIndex > 0:    
                                image = self.listpanel.imagelist.GetImage(imageIndex)
                else:
                    image = self.GetImageAtIndex(i)

                imageWide = tall = 0
                if image:
                    imageWide, tall = image.GetContentSize()
                    
                if maxWidth >= 0:
                    wide = maxWidth
                else:
                    wide = imageWide

                xpos += wide#max(maxWidth,wide)
                surface().DrawOutlinedRect( xpos, 0, xpos, self.GetTall() )

    def OnMousePressed(self, code):
        if code == ButtonCode_t.MOUSE_LEFT:
            self.listpanel.PostActionSignal(KeyValues("ItemLeftClick", "itemID", self.id))
        if code == ButtonCode_t.MOUSE_RIGHT:
            msg = KeyValues("ItemContextMenu", "itemID", self.id)
            #msg.SetPtr("SubPanel", self)   # TODO
            self.listpanel.PostActionSignal(msg)

        self.listpanel.SetSelectedItem(self)

    def SetSelected(self, state):
        if self.selected != state:
            if state:
                self.RequestFocus()
            
            self.selected = state
            self.SetPaintBackgroundEnabled( state )
            self.InvalidateLayout()
            self.Repaint()

    def IsSelected(self):
        return self.selected

    def OnSetFocus(self):
        self.InvalidateLayout() # force the layout to be redone so we can change text color according to focus
        super(CItemButton, self).OnSetFocus()

    def OnKillFocus(self):
        self.InvalidateLayout() # force the layout to be redone so we can change text color according to focus
        super(CItemButton, self).OnSetFocus()   # TODO: shouldn't it call OnKillFocus?

    def OnMouseDoublePressed(self, code):
        if code == ButtonCode_t.MOUSE_LEFT:
            self.listpanel.PostActionSignal(KeyValues("ItemDoubleLeftClick", "itemID", self.id))

            # post up an enter key being hit
            self.listpanel.OnKeyCodeTyped(ButtonCode_t.KEY_ENTER)
        else:
            self.OnMousePressed(code)

        self.listpanel.SetSelectedItem(self)

    def GetCellBounds(self, column):
        xpos = columnWide = 0
        colCount = self.listpanel.GetColumnCountBySection(self.sectionid)
        for i in range(0, colCount):
            maxWidth = self.listpanel.GetColumnWidthBySection(self.sectionid, i)

            image = self.GetImageAtIndex(i)
            if not image:
                continue

            # set the image position within the label
            wide, tall = image.GetContentSize()
            if maxWidth >= 0:
                wide = maxWidth

            if i == column:
                # found the cell size, bail
                columnWide = wide
                return xpos, columnWide   
            xpos += wide
        return xpos, columnWide

    def SetOverrideColors(self, state):
        self.overridecolors = state

    def SetShowColumns(self, bShow):
        self.showcolumns = bShow

class SectionedListPanel(Panel):
    def __init__(self, parent, name):
        super(SectionedListPanel, self).__init__(parent, name)
        
        self.RegMessageMethod( "ScrollBarSliderMoved", self.OnSliderMoved )
        
        self.sorteditems = []
        self.sections = []
        self.items = []
        self.freeitems = []
        
        self.scrollbar = ScrollBar(self, "SectionedScrollBar", True)
        self.scrollbar.SetVisible(False)
        self.scrollbar.AddActionSignalTarget(self)

        self.editmodeitemid = 0
        self.editmodecolumn = 0
        self.sortneeded = False
        self.verticalscrollbarenabled = True
        self.linespacing = 20

        self.imagelist = None
        self.deleteimagelistwhendone = False
        
        
        
    def ReSortList(self):
        """ Sorts the list """
        self.sorteditems = []
        sectionStart = 0
        # layout the buttons
        for section in self.sections:
            sectionStart = len(self.sorteditems)

            # find all the items in self section
            for i, item in enumerate(self.items):
                if item.GetSectionID() == section.id:
                    # insert the items sorted
                    if section.sortfunc:
                        insertionPoint = sectionStart
                        for insertionPoint in range(insertionPoint, len(self.sorteditems)):
                            if section.sortfunc(self, i, self.sorteditems[insertionPoint].GetID()):
                                break

                        if insertionPoint == len(self.sorteditems):
                            self.sorteditems.append(item)  
                        else:       
                            self.sorteditems.insert(insertionPoint, item) 
                    else:
                        # just add to the end
                        self.sorteditems.append(item)

    def PerformLayout(self):
        """ iterates through and sets up the position of all the sections and items """
        # lazy resort the list
        if self.sortneeded:
            self.ReSortList()
            self.sortneeded = False

        super(SectionedListPanel, self).PerformLayout()
        
        self.contentheight = self.LayoutPanels()

        cx, cy, cwide, ctall = self.GetBounds()
        if self.contentheight > ctall and self.verticalscrollbarenabled:
            self.scrollbar.SetVisible(True)
            self.scrollbar.MoveToFront()

            self.scrollbar.SetPos(cwide - self.scrollbar.GetWide() - 2, 0)
            self.scrollbar.SetSize(self.scrollbar.GetWide(), ctall - 2)

            self.scrollbar.SetRangeWindow(ctall)

            self.scrollbar.SetRange(0, self.contentheight)
            self.scrollbar.InvalidateLayout()
            self.scrollbar.Repaint()

            # since we're just about to make the scrollbar visible, we need to re-layout
            # the buttons since they depend on the scrollbar size
            self.contentheight = self.LayoutPanels()
        else:
            self.scrollbar.SetValue(0)
            self.scrollbar.SetVisible(False)
        
    def LayoutPanels(self):
        """ lays out the sections and rows in the panel """
        tall = self.GetSectionTall()
        x = 5
        wide = self.GetWide() - 10
        y = 5
        
        if self.scrollbar.IsVisible():
            y -= self.scrollbar.GetValue()
            wide -= self.scrollbar.GetWide()
        
        iStart = -1
        iEnd = -1

        # layout the buttons
        for sectionIndex, section in enumerate(self.sections):
            iStart = -1
            iEnd = -1
            for i, sorteditem in enumerate(self.sorteditems):
                if sorteditem.GetSectionID() == section.id:
                    if iStart == -1:
                        iStart = i
                    iEnd = i

            # don't draw self section at all if their are no item in it
            if iStart == -1 and not section.alwaysvisible:
                section.header.SetVisible(False)
                continue
            

            # draw the header
            section.header.SetBounds(x, y, wide, tall)
            section.header.SetVisible(True)
            y += tall

            if iStart == -1 and section.alwaysvisible:
                pass
            else:
                # arrange all the items in self section underneath
                for i in range(iStart, iEnd+1):
                    item = self.sorteditems[i] #items[i]
                    item.SetBounds(x, y, wide, self.linespacing)
                    
                    # setup edit mode
                    if self.editmodepanel and self.editmodeitemid == item.GetID():
                        cx, cwide = item.GetCellBounds(1)
                        self.editmodepanel.SetBounds(cx, y, cwide, tall)

                    y += self.linespacing
                    
            # add in a little boundry at the bottom
            y += SECTION_GAP

        # calculate height
        contentTall = y
        if self.scrollbar.IsVisible():
            contentTall += self.scrollbar.GetValue()
        return contentTall

    def ScrollToItem(self, iItem):
        """ Ensures that the specified item is visible in the display """
        tall = self.GetSectionTall()
        nCurrentValue = self.scrollbar.GetValue()

        # find out where the item is
        itemX, itemY = self.items[iItem].GetPos()
        # add in the current scrollbar position
        itemY += nCurrentValue

        # compare that in the list
        cx, cy, cwide, ctall = self.GetBounds()
        if self.contentheight > ctall:
            if itemY < nCurrentValue:
                # scroll up
                self.scrollbar.SetValue(itemY)
            elif itemY > nCurrentValue + ctall - tall:
                # scroll down
                self.scrollbar.SetValue(itemY - ctall + tall)
            else:
                # keep the current value
                pass
        else:
            # area isn't big enough, just remove the scrollbar
            self.scrollbar.SetValue(0)

        # reset scrollbar
        self.Repaint()

    def ApplySchemeSettings(self, schemeobj):
        """ sets background color & border """
        super(SectionedListPanel, self).ApplySchemeSettings(schemeobj)

        self.SetBgColor(self.GetSchemeColor("SectionedListPanel.BgColor", self.GetBgColor(), schemeobj))
        self.SetBorder(schemeobj.GetBorder("ButtonDepressedBorder"))

        for item in self.items: 
            item.SetShowColumns( self.showcolumns )

    def ApplySettings(self, inResourceData):
        super(SectionedListPanel, self).ApplySettings(inResourceData)
        self.linespacing = inResourceData.GetInt("linespacing", 0)
        if not self.linespacing:
            self.linespacing = 20
        if self.IsProportional():
            self.linespacing = scheme().GetProportionalScaledValueEx(self.GetScheme(), self.linespacing)

    def SetProportional(self, state):
        """ passes on proportional state to children """
        super(SectionedListPanel, self).SetProportional(state)

        # now setup the section headers and items
        for section in self.sections:
            section.header.SetProportional(state)
            
        for item in self.items:
            item.SetProportional(state)

    def SetVerticalScrollbar(self, state):
        """ sets whether or not the vertical scrollbar should ever be displayed """
        self.verticalscrollbarenabled = state

    def AddSection(self, sectionID, name, sortFunc=None):
        """ adds a new section """
        header = CSectionHeader(self, name, sectionID)
        header.MakeReadyForUse()
        self.AddSectionHelper(sectionID, header, sortFunc)

    def AddSectionHelper(self, sectionID, header, sortFunc):
        """ helper function for AddSection """
        self.sections.append(section_t())
        index = len(self.sections)-1
        self.sections[index].id = sectionID
        self.sections[index].header = header
        self.sections[index].sortfunc = sortFunc
        self.sections[index].alwaysvisible = False

    def RemoveAllSections(self):
        """ removes all the sections from the current panel """
        for section in self.sections:
            if not section:
                continue

            section.header.SetVisible(False)
            section.header.DeletePanel()#MarkForDeletion()

        self.sections = []
        self.sorteditems = []

        self.InvalidateLayout()
        self.ReSortList()

    def AddColumnToSection(self, sectionID, columnName, columnText, columnFlags, width, fallbackFont=INVALID_FONT):
        """ adds a new column to a section """
        # Localize text if possible
        pwtext = localize.Find(columnText)
        if not pwtext:
            pwtext = columnText#localize.ConvertANSIToUnicode(columnText)
            
        index = self.FindSectionIndexByID(sectionID)
        if index < 0:
            return False
        section = self.sections[index]

        # add the new column to the sections' list
        section.columns.append(column_t())
        index = len(section.columns)-1
        column = section.columns[index]

        column.columnname = str(columnName)
        column.columntext = str(columnText)
        column.columnflags = columnFlags
        column.width = width
        column.fallbackfont = fallbackFont
        return True

    def ModifyColumn(self, sectionID, columnName, columnText):
        """ modifies the text in an existing column """
        index = FindSectionIndexByID(sectionID)
        if index < 0:
            return False
        section = self.sections[index]

        # find the specified column
        for columnIndex in range(0, len(section.columns)):
            if section.columns[columnIndex].columnname == columnName:
                break
        
        try:
            section.columns[columnIndex]
        except IndexError:
            return False
        column = section.columns[columnIndex]

        # modify the text
        column.columntext = str(columnText)
        section.header.InvalidateLayout()
        return True

    def AddItem(self, sectionID, data):
        """ adds an item to the list returns itemID"""
        itemID = self.GetNewItemButton()
        self.ModifyItem(itemID, sectionID, data)

        # not sorted but in list
        self.sorteditems.append(self.items[itemID])
        self.sortneeded = True

        return itemID

    def ModifyItem(self, itemID, sectionID, data):
        """ modifies an existing item returns False if the item does not exist """
        try:
            self.items[itemID]
        except IndexError:
            return False

        self.InvalidateLayout()
        self.items[itemID].SetSectionID(sectionID)
        self.items[itemID].SetData(data)
        self.items[itemID].InvalidateLayout()
        self.sortneeded = True
        return True

    def SetItemFgColor(self, itemID, color):
        try:
            self.items[itemID]
        except IndexError:
            return

        self.items[itemID].SetFgColor( color )
        self.items[itemID].SetOverrideColors( True )
        self.items[itemID].InvalidateLayout()

    def SetItemFont(self, itemID, font):
        try:
            self.items[itemID]
        except IndexError:
            return

        self.items[itemID].SetFont( font )

    def SetSectionFgColor(self, sectionID, color):
        """ sets the color of a section text & underline """
        try:
            self.sections[sectionID]
        except IndexError:
            return

        self.sections[sectionID].header.SetColor(color)

    def SetSectionDividerColor(self, sectionID, color):
        """ added so you can change the divider color AFTER the main color """
        try:
            self.sections[sectionID]
        except IndexError:
            return

        self.sections[sectionID].header.SetDividerColor(color)

    def SetSectionAlwaysVisible(self, sectionID, visible=True):
        """ forces a section to always be visible """
        try:
            self.sections[sectionID]
        except IndexError:
            return

        self.sections[sectionID].alwaysvisible = visible

    def SetFontSection(self, sectionID, font):
        try:
            self.sections[sectionID]
        except IndexError:
            return

        self.sections[sectionID].header.SetFont(font)

    def RemoveItem(self, itemID):
        """ removes an item from the list returns False if the item does not exist or is already removed """
        try:
            self.items[itemID]
        except IndexError:
            return False

        self.sorteditems.remove(self.items[itemID])
        self.sortneeded = True

        self.items[itemID].DeletPanel()
        del self.items[itemID]

        self.InvalidateLayout()
        
        return True

    def GetColumnCountBySection(self, sectionID):
        """ returns the number of columns in a section """
        index = self.FindSectionIndexByID(sectionID)
        if index < 0:
            return 0

        return len(self.sections[index].columns)

    def GetColumnNameBySection(self, sectionID, columnIndex):
        """ returns the name of a column by section and column index returns None if there are no more columns
            valid range of columnIndex is [0, GetColumnCountBySection) """
        index = self.FindSectionIndexByID(sectionID)
        if index < 0 or columnIndex >= len(self.sections[index].columns):
            return None

        return self.sections[index].columns[columnIndex].columnname

    def GetColumnTextBySection(self, sectionID, columnIndex):
        """ returns the text for a column by section and column index """
        index = self.FindSectionIndexByID(sectionID)
        if index < 0 or columnIndex >= len(self.sections[index].columns):
            return None
        
        return self.sections[index].columns[columnIndex].columntext

    def GetColumnFlagsBySection(self, sectionID, columnIndex):
        """ returns the type of a column by section and column index """
        index = self.FindSectionIndexByID(sectionID)
        if index < 0:
            return 0

        if columnIndex >= len(self.sections[index].columns):
            return 0

        return self.sections[index].columns[columnIndex].columnflags

    def GetColumnWidthBySection(self, sectionID, columnIndex):
        index = self.FindSectionIndexByID(sectionID)
        if index < 0:
            return 0

        if columnIndex >= len(self.sections[index].columns):
            return 0

        return self.sections[index].columns[columnIndex].width

    def FindSectionIndexByID(self, sectionID):
        """ returns -1 if section not found """
        for i, section in enumerate(self.sections):
            if section.id == sectionID:
                return i
        return -1
        
    def OnSliderMoved(self):
        """ Called when the scrollbar is moved """
        self.InvalidateLayout()
        self.Repaint()

    def OnMouseWheeled(self, delta):
        """ Scrolls the list according to the mouse wheel movement """
        if self.editmodepanel:
            # ignore mouse wheel in edit mode, forward right up to parent
            self.CallParentFunction(KeyValues("MouseWheeled", "delta", delta))
            return

        # scroll the window based on the delta
        val = self.scrollbar.GetValue()
        val -= (delta * BUTTON_HEIGHT_DEFAULT * 3)
        self.scrollbar.SetValue(val)

    def OnSizeChanged(self, wide, tall):
        """ Resets the scrollbar position on size change """
        super(SectionedListPanel, self).OnSizeChanged(wide, tall)
        self.scrollbar.SetValue(0)
        self.InvalidateLayout()
        self.Repaint()

    def OnMousePressed(self, code):
        """ deselects any items """
        self.ClearSelection()

    def ClearSelection(self):
        """ deselects any items """
        self.SetSelectedItem(None)

    def MoveSelectionDown(self):
        itemID = self.GetSelectedItem()
        assert(itemID != -1)

        if not len(self.sorteditems): # if the list has been emptied
            return

        for sorteditem in self.sorteditems:
            if sorteditem.GetID() == itemID:
                break

        assert(i != len(self.sorteditems))

        # we're already on the end
        if i == len(self.sorteditems) - 1:
            return

        newItemID = self.sorteditems[i + 1].GetID()
        self.SetSelectedItem(self.items[newItemID])
        self.ScrollToItem(newItemID)

    def MoveSelectionUp(self):
        itemID = self.GetSelectedItem()
        assert(itemID != -1)

        if not len(self.sorteditems): # if the list has been emptied
            return

        for sorteditem in self.sorteditems:
            if sorteditem.GetID() == itemID:
                break

        assert(i != len(self.sorteditems))

        # we're already on the end
        if i == 0:
            return

        newItemID = self.sorteditems[i - 1].GetID()
        self.SetSelectedItem(self.items[newItemID])
        self.ScrollToItem(newItemID)

    def OnKeyCodeTyped(self, code):
        """ arrow key movement handler """
        if self.editmodepanel:
            # ignore arrow keys in edit mode
            # forward right up to parent so that tab focus change doesn't occur
            self.CallParentFunction(KeyValues("KeyCodeTyped", "code", code))
            return

        buttonTall = self.GetSectionTall()
        
        if code == ButtonCode_t.KEY_DOWN:
            self.MoveSelectionDown()
            return 
        elif code == ButtonCode_t.KEY_UP:
            self.MoveSelectionUp()
            return
        elif code == ButtonCode_t.KEY_PAGEDOWN:
            # calculate info for # of rows
            cx, cy, cwide, ctall = self.GetBounds()

            rowsperpage = ctall/buttonTall

            itemID = self.GetSelectedItem()
            lastValidItem = itemID
            secID = self.items[itemID].GetSectionID()
            i=0
            row = self.sorteditems.index(self.items[itemID])

            while i < rowsperpage:
                row += 1
                try:
                    itemID = self.sorteditems[row].GetID()
                    lastValidItem = itemID
                    i += 1

                    # if we switched sections, then count the section header as a row
                    if self.items[itemID].GetSectionID() != secID:
                        secID = self.items[itemID].GetSectionID()
                        i += 1
                except IndexError:
                    itemID = lastValidItem
                    break
            
            self.SetSelectedItem(self.items[itemID])
            self.ScrollToItem(itemID)
        elif code == ButtonCode_t.KEY_PAGEUP:
            # calculate info for # of rows
            cx, cy, cwide, ctall = self.GetBounds()
            rowsperpage = ctall/buttonTall

            itemID = self.GetSelectedItem()
            lastValidItem = itemID
            secID = self.items[itemID].GetSectionID()
            i=0
            row = self.sorteditems.index(self.items[itemID])
            while i < rowsperpage:
                row -= 1
                try:
                    itemID = self.sorteditems[row].GetID()
                    lastValidItem = itemID
                    i += 1

                    # if we switched sections, then count the section header as a row
                    if self.items[itemID].GetSectionID() != secID:
                        secID = self.items[itemID].GetSectionID()
                        i += 1
                except IndexError:
                    self.SetSelectedItem(self.items[lastValidItem])
                    self.scrollbar.SetValue(0)
                    return

            self.SetSelectedItem(self.items[itemID])
            self.ScrollToItem(itemID)
        elif code == ButtonCode_t.KEY_LEFT or code == ButtonCode_t.KEY_RIGHT:
            pass
        else:
            super(SectionedListPanel, self).OnKeyCodeTyped(code)
            
    def RemoveAll(self):
        self.DeleteAllItems()
        
    def DeleteAllItems(self):
        """ Clears the list """
        for item in self.items:
            item.SetVisible(False)
            item.Clear()

            # don't delete, move to free list
            self.freeitems.append(None)
            freeIndex = len(self.freeitems)-1
            self.freeitems[freeIndex] = item

        self.items = []
        self.sorteditems = []
        self.selecteditem = None
        self.InvalidateLayout()
        self.sortneeded = True

    def SetSelectedItem(self, item):
        """ Changes the current list selection """
        if type(item) == int:
            try:
                item = self.items[item]
            except IndexError:
                return
                
        if self.selecteditem == item:
            return

        # deselect the current item
        if self.selecteditem:
            self.selecteditem.SetSelected(False)

        # set the new item
        self.selecteditem = item
        if self.selecteditem:
            self.selecteditem.SetSelected(True)

        self.Repaint()
        if self.selecteditem:
            self.PostActionSignal(KeyValues("ItemSelected", "itemID", self.selecteditem.GetID()))
        else:
            self.PostActionSignal(KeyValues("ItemSelected", "itemID", -1))

    def GetSelectedItem(self):
        if self.selecteditem:
            return self.selecteditem.GetID()
        return -1

    def GetItemData(self, itemID):
        """ returns the data of a selected item """
        try:
            self.items[itemID]
        except IndexError:
            return None
        return self.items[itemID].GetData()

    def GetItemSection(self, itemID):
        """ returns what section an item is in """
        try:
            self.items[itemID]
        except IndexError:
            return -1
        return self.items[itemID].GetSectionID()

    def IsItemIDValid(self, itemID):
        """ returns True if the itemID is valid for use """
        return self.items.IsValidIndex(itemID)

    def GetHighestItemID(self):
        return len(self.items)-1

    def GetItemCount(self):
        """ item iterators """
        return len(self.sorteditems)

    def GetItemIDFromRow(self, row):
        """ item iterators """
        try:
            self.sorteditems[row]
        except IndexError:
            return -1
        return self.sorteditems[row].GetID()

    def GetRowFromItemID(self, itemID):
        """ returns the row that self itemID occupies. -1 if the itemID is invalid """
        for sorteditem in self.sorteditems:
            if sorteditem.GetID() == itemID:
                return i
        return -1

    def GetCellBounds(self, itemID, column):
        """ gets the local coordinates of a cell """
        x = y = wide = tall = 0
        if not self.IsItemIDValid(itemID):
            return False, x, y, wide, tall

        # get the item
        item = self.items[itemID]

        if not item.IsVisible():
            return False, x, y, wide, tall

        #!! ignores column for now
        x, y, wide, tall = item.GetBounds()
        x, wide = item.GetCellBounds(column)
        return True, x, y, wide, tall

    def InvalidateItem(self, itemID):
        """ forces an item to redraw """
        if not self.IsItemIDValid(itemID):
            return

        self.items[itemID].InvalidateLayout()
        self.items[itemID].Repaint()

    def EnterEditMode(self, itemID, column, editPanel):
        """ set up a field for editing """
        self.editmodepanel = editPanel
        self.editmodeitemid = itemID
        self.editmodecolumn = column
        editPanel.SetParent(self)
        editPanel.SetVisible(True)
        editPanel.RequestFocus()
        editPanel.MoveToFront()
        self.InvalidateLayout()

    def LeaveEditMode(self):
        """ leaves editing mode """
        if self.editmodepanel:
            self.InvalidateItem(self.editmodeitemid)
            self.editmodepanel.SetVisible(False)
            self.editmodepanel.SetParent(None)
            self.editmodepanel = None
        
    def IsInEditMode(self):
        """ returns True if we are currently in inline editing mode """
        return (self.editmodepanel != None)

    def SetImageList(self, imageList, deleteImageListWhenDone):
        """ list used to match indexes in image columns to image pointers """
        self.deleteimagelistwhendone = deleteImageListWhenDone
        self.imagelist = imageList

    def OnSetFocus(self):
        if self.selecteditem:
            self.selecteditem.RequestFocus()
        else:
            super(SectionedListPanel, self).OnSetFocus()
        
    def GetSectionTall(self):
        if len(self.sections):
            font = self.sections[0].header.GetFont()
            if font != INVALID_FONT:
                return surface().GetFontTall(font) + BUTTON_HEIGHT_SPACER
        return BUTTON_HEIGHT_DEFAULT

    def GetContentSize(self):
        """ returns the size required to fully draw the contents of the panel """
        # make sure our layout is done
        if self.IsLayoutInvalid():
            if self.sortneeded:
                self.ReSortList()
                self.sortneeded = False
            
            self.contentheight = self.LayoutPanels()

        wide = self.GetWide()
        tall = self.contentheight
        return wide, tall

    def GetNewItemButton(self):
        """ Returns the index of a new item button """
        self.items.append(None)
        itemID = len(self.items)-1
        if len(self.freeitems):
            # reusing an existing CItemButton
            self.items[itemID] = self.freeitems[0]
            self.items[itemID].SetID(itemID)
            self.items[itemID].SetVisible(True)
            del self.freeitems[0]
        else:
            # create a new CItemButton
            self.items[itemID] = CItemButton(self, itemID)
            self.items[itemID].MakeReadyForUse()
            self.items[itemID].SetShowColumns( self.showcolumns )
        
        return itemID

    def GetColumnFallbackFontBySection(self, sectionID, columnIndex):
        """ Returns fallback font to use for text image for self column """
        index = self.FindSectionIndexByID(sectionID)
        if index < 0:
            return INVALID_FONT

        if columnIndex >= len(self.sections[index].columns):
            return INVALID_FONT

        return self.sections[index].columns[columnIndex].fallbackfont

    # Defaults
    selecteditem = None
    editmodepanel = None
    contentheight = 0.0
    showcolumns = False
        
    # Column flags
    HEADER_IMAGE	= 0x01		# set if the header for the column is an image instead of text
    COLUMN_IMAGE	= 0x02		# set if the column contains an image instead of text (images are looked up by index from the ImageList) (see SetImageList below)
    COLUMN_BRIGHT	= 0x04		# set if the column text should be the bright color
    COLUMN_CENTER	= 0x08		# set to center the text/image in the column
    COLUMN_RIGHT	= 0x10		# set to right-align the text in the column