from srcbase import KeyValues, Color, UtlRBTree
from vgui import vgui_input, scheme, DataType_t, CursorCode, surface, ipanel, INVALID_STRING_INDEX, localize
from vgui.controls import Panel, Button, ImagePanel, ScrollBar, Label, TextImage
from .menu import Menu
from input import ButtonCode_t

from profiler import profile

def clamp(val, min, max):
    if val > max:
        return max
    if val < min:
        return min
    return val

# Some data classes
class IndexItem(object):
    dataItem = None
    duplicateIndex = 0
    
class Column(object):
    def __init__(self):
        super(Column, self).__init__()
        
        self.sortedtree = UtlRBTree()
        
    header = None
    minwidth = 0
    maxwidth = 0
    resizeswithwindow = False
    resizer = None
    sortfunc = None
    typeistext = False
    hidden = False
    unhidable = False
    contentAlignment = 0

class ListPanelItem(object):
    """ Generic class for ListPanel items """
    kv = None
    userdata = None
    dragdata = None
    image = False
    imageindex = -1
    imageindexselected = -1
    icon = None

class ColumnButton(Button):
    """ Button at the top of columns used to re-sort """
    def __init__(self, parent, name, text):
        super(ColumnButton, self).__init__(parent, name, text)
        self.SetBlockDragChaining( True )

    def ApplySchemeSettings(self, schemeobj):

        super(ColumnButton, self).ApplySchemeSettings(schemeobj)

        self.SetContentAlignment(Label.a_west)
        self.SetFont(schemeobj.GetFont("DefaultSmall", self.IsProportional()))

    # Don't request focus.
    # self will keep items in the listpanel selected.
    def OnMousePressed(self, code):
        if not self.IsEnabled():
            return

        if code == ButtonCode_t.MOUSE_RIGHT:
            self.OpenColumnChoiceMenu()
            return
        
        if not self.IsMouseClickEnabled(code):
            return
        
        if self.IsUseCaptureMouseEnabled():
            self.SetSelected(True)
            self.Repaint()
            
            # lock mouse input to going to self button
            vgui_input().SetMouseCapture(self.GetVPanel())

    def OpenColumnChoiceMenu(self):
        self.CallParentFunction(KeyValues("OpenColumnChoiceMenu"))

class Dragger(Panel):
    """ Handles resizing of columns """
    def __init__(self, column):
        super(Dragger, self).__init__()
    
        self.dragger = column
        self.SetPaintBackgroundEnabled(False)
        self.SetPaintEnabled(False)
        self.SetPaintBorderEnabled(False)
        self.SetCursor(CursorCode.dc_sizewe)
        self.dragging = False
        self.movable = True # movable by default
        self.dragpos = 0
        self.SetBlockDragChaining( True )

    def OnMousePressed(self, code):
        if self.movable:
            vgui_input().SetMouseCapture(self.GetVPanel())
            
            x, y = vgui_input().GetCursorPos()
            self.dragpos = x
            self.dragging = True

    def OnMouseDoublePressed(self, code):
        if self.movable:
            # resize the column to the size of it's contents
            self.PostMessage(self.GetParent(), KeyValues("ResizeColumnToContents", "column", self.dragger))

    def OnMouseReleased(self, code):
        if self.movable:
            vgui_input().SetMouseCapture(0)
            self.dragging = False

    def OnCursorMoved(self, x, y):
        if self.dragging:
            x, y = vgui_input().GetCursorPos()
            msg = KeyValues("ColumnResized")
            msg.SetInt("column", self.dragger)
            msg.SetInt("delta", x - self.dragpos)
            self.dragpos = x
            if self.GetVParent():   
                self.PostMessage(self.GetVParent(), msg)

    def SetMovable(self, state):
        self.movable = state
        # disable cursor change if the dragger is not movable
        if self.IsVisible():
            if state:
                # if its not movable we stick with the default arrow
                # if parent windows Start getting fancy cursors we should probably retrive a parent
                # cursor and set it to that
                self.SetCursor(CursorCode.dc_sizewe) 
            else:
                self.SetCursor(CursorCode.dc_arrow) 

# optimized for sorting
class FastSortListPanelItem(ListPanelItem):
    # index into accessing item to sort
    def __init__(self):
        super(FastSortListPanelItem, self).__init__()
        self.sortedtreeindexes = []

    # visibility flag (for quick hide/filter)
    visible = False

    # precalculated sort orders
    primarySortIndexValue = 0
    secondarySortIndexValue = 0

s_pCurrentSortingListPanel = None
s_pCurrentSortingColumn = None
s_currentSortingColumnTypeIsText = False

s_pSortFunc = None
s_bSortAscending = True
s_pSortFuncSecondary = None
s_bSortAscendingSecondary = True

def AscendingSortFunc2(elem1):
    p1 = s_pCurrentSortingListPanel.GetItemData(elem1)
    col = s_pCurrentSortingColumn
    
    if (p1.kv.FindKey(col, True).GetDataType() == KeyValues.TYPE_INT):
        return p1.kv.GetInt(col, 0)
    
    return p1.kv.GetString(col, "")

def AscendingSortFunc(elem1, elem2):
    """ Basic sort function, for use in qsort """

    itemID1 = elem1
    itemID2 = elem2

    # convert the item index into the ListPanelItem pointers
    p1 = s_pCurrentSortingListPanel.GetItemData(itemID1)
    p2 = s_pCurrentSortingListPanel.GetItemData(itemID2)
    
    result = s_pSortFunc( s_pCurrentSortingListPanel, p1, p2 )
    if result == 0:
        # use the secondary sort function
        result = s_pSortFuncSecondary( s_pCurrentSortingListPanel, p1, p2 )
        if not s_bSortAscendingSecondary:
            result = -result

        if result == 0:
            # sort by the pointers to make sure we get consistent results
            if p1 > p2:
                result = 1
            else:
                result = -1
    else:
        # flip result if not doing an ascending sort
        if not s_bSortAscending:
            result = -result

    return result

def DefaultSortFunc(
        pPanel, 
        item1,
        item2 ):
    """ Default column sorting function, puts things in alpabetical order
        If images are the same returns 1, else 0 """
    p1 = item1
    p2 = item2
    if not p1 or not p2:  # No meaningful comparison
        return 0  

    col = s_pCurrentSortingColumn
    if s_currentSortingColumnTypeIsText: # textImage column
        if (p1.kv.FindKey(col, True).GetDataType() == KeyValues.TYPE_INT):
            # compare ints
            s1 = p1.kv.GetInt(col, 0)
            s2 = p2.kv.GetInt(col, 0)
            if s1 < s2:
                return -1
            elif s1 > s2:
                return 1
            return 0
        
        else:
            # compare as string
            s1 = p1.kv.GetString(col, "")
            s2 = p2.kv.GetString(col, "")
            return (s1 > s2) - (s1 < s2)
    
    else:    # its an imagePanel column
        s1 = p1.kv.GetPtr(col, "")
        s2 = p2.kv.GetPtr(col, "")

        if (s1 < s2):
            return -1
        elif (s1 > s2):
            return 1
        return 0

def FastSortFunc(
        pPanel, 
        item1,
        item2 ):
    """ Sorts items by comparing precalculated list values """
    p1 = item1
    p2 = item2

    assert(p1 and p2)

    # compare the precalculated indices
    if p1.primarySortIndexValue < p2.primarySortIndexValue:
        return 1
    elif p1.primarySortIndexValue > p2.primarySortIndexValue:
        return -1

    # they're equal, compare the secondary indices
    if p1.secondarySortIndexValue < p2.secondarySortIndexValue:
        return 1
    elif p1.secondarySortIndexValue > p2.secondarySortIndexValue:
        return -1

    # still equal just compare the pointers (so we get deterministic results)
    if p1 < p2:
        return 1
    return -1

s_iDuplicateIndex = 1

def RBTreeLessFunc(item1, item2):
    """ sorting function used in the column index redblack tree """
    global s_iDuplicateIndex
    result = s_pSortFunc( s_pCurrentSortingListPanel, item1.dataItem, item2.dataItem)
    if result == 0:
        # they're the same value, set their duplicate index to reflect that
        if item1.duplicateIndex:
            item2.duplicateIndex = item1.duplicateIndex
        elif item2.duplicateIndex:
            item1.duplicateIndex = item2.duplicateIndex
        else:
            s_iDuplicateIndex += 1
            item1.duplicateIndex = item2.duplicateIndex = s_iDuplicateIndex
    
    return (result > 0)
    
class ListPanel(Panel):
    def __init__(self, parent, panelname):
        super(ListPanel, self).__init__(parent, panelname)
        
        self.EnableSBuffer(True)
        
        self.columnsdata = []
        self.columnshistory = []
        self.currentcolumns = []
        
        self.dataitems = []
        self.visibleitems = []
        self.selecteditems = []
        
        self.ignoredoubleclick = False
        self.multiselectenabled = True
        self.editmodeitemid = 0
        self.editmodecolumn = 0

        self.headerheight = 20
        self.rowheight = 20
        self.canselectindividualcells = False
        self.selectcolumn = -1
        self.allowusersadddeletecolumns = False

        self.hbar = ScrollBar(self, "HorizScrollBar", False)
        self.hbar.AddActionSignalTarget(self)
        self.hbar.SetVisible(False)
        self.vbar = ScrollBar(self, "VertScrollBar", True)
        self.vbar.SetVisible(False)
        self.vbar.AddActionSignalTarget(self)

        self.label = Label(self, None, "ItemLabel")
        self.label.SetFlushedByParent(True)
        self.label.SetVisible(False)
        self.label.SetPaintBackgroundEnabled(False)
        self.label.SetContentAlignment(Label.a_west)

        self.textimage = TextImage( "" )
        self.imagepanel = ImagePanel(None, "ListImage")
        self.imagepanel.SetAutoDelete(False)

        self.sortcolumn = -1
        self.sortcolumnSecondary = -1
        self.sortascending = True
        self.sortascendingSecondary = True

        self.lastbarwidth = 0
        self.columndraggermoved = -1
        self.needssort = False
        self.lastitemselected = -1

        self.imagelist = None
        self.deleteimagelistwhendone = False
        self.emptylisttext = TextImage("")
        
        # Register message methods
        self.RegMessageMethod( "ResizeColumnToContents", self.ResizeColumnToContents, 1, "column", DataType_t.DATATYPE_INT )
        self.RegMessageMethod( "ScrollBarSliderMoved", self.OnSliderMoved )
        self.RegMessageMethod( "ColumnResized", self.OnColumnResized, 2, "column", DataType_t.DATATYPE_INT, "delta", DataType_t.DATATYPE_INT )
        self.RegMessageMethod( "SetSortColumn", self.OnSetSortColumn, 1, "column", DataType_t.DATATYPE_INT )
        self.RegMessageMethod( "OpenColumnChoiceMenu", self.OpenColumnChoiceMenu )
        self.RegMessageMethod( "ToggleColumnVisible", self.OnToggleColumnVisible, 1, "col", DataType_t.DATATYPE_INT )    
        
    def UpdateOnDelete(self):
        # free data from table
        self.RemoveAll()

        # free column headers
        for cd in self.columnsdata:
            # TODO: Add support for mark for deletion?
            if cd.header:
                cd.header.DeletePanel()
            if cd.resizer:
                cd.resizer.DeletePanel()
        
        self.columnsdata = []

        self.textimage = None
        self.imagepanel.DeletePanel()
        self.vbar.DeletePanel()

        if self.deleteimagelistwhendone:
            self.imagelist = None

        self.emptylisttext = None
        
    def SetImageList(self, imageList, deleteImageListWhenDone):
        # get rid of existing list image if there's one and we're supposed to get rid of it
        if self.imagelist and self.deleteimagelistwhendone:
            self.imagelist = None
            #self.imagelist.DeletePanel()

        self.deleteimagelistwhendone = deleteImageListWhenDone
        self.imagelist = imageList

    def SetColumnHeaderHeight(self, height):
        self.headerheight = height

    def AddColumnHeader(self, index, columnName, columnText, width, columnFlags, minWidth=20, maxWidth=10000):
        """ 
        Purpose: adds a column header. 
                 self.FindChildByName(columnHeaderName) can be used to retrieve a pointer to a header panel by name
        
        if minWidth and maxWidth are BOTH NOTRESIZABLE or RESIZABLE
        the min and max size will be calculated automatically for you with that attribute
        columns are resizable by default
        if min and max size are specified column is resizable
        
        A small note on passing numbers for minWidth and maxWidth, 
        If the initial window size is larger than the sum of the original widths of the columns,
        you can wind up with the columns "snapping" to size after the first window focus
        self is because the dxPerBar being calculated in PerformLayout()
        is making resizable bounded headers exceed thier maxWidths at the Start. 
        Solution is to either put in support for redistributing the extra dx being truncated and
        therefore added to the last column on window opening, which is what causes the snapping.
        OR to
        ensure the difference between the starting sum of widths is not too much smaller/bigger 
        than the starting window size so the starting dx doesn't cause snapping to occur.
        The easiest thing is to simply set it so your column widths add up to the starting size of the window on opening.
        
        Another note: Always give bounds for the last column you add or make it not resizable.
        
        Columns can have text headers or images for headers (e.g. password icon) """
    
        if columnFlags & self.COLUMN_FIXEDSIZE and not (columnFlags & self.COLUMN_RESIZEWITHWINDOW):
            minWidth = width
            maxWidth = width
        assert (minWidth <= width)
        assert (maxWidth >= width)

        # get our permanent index
        self.columnsdata.append(Column())
        columnDataIndex = len(self.columnsdata)-1

        # put this index on the tail, so all item's sortedtreeindexes have a consistent mapping
        self.columnshistory.append(columnDataIndex)

        # put this column in the right place visually
        self.currentcolumns.insert(index, columnDataIndex)

        # create the actual column object
        column = self.columnsdata[columnDataIndex]

        # create the column header button
        pButton = ColumnButton(self, columnName, columnText)  # the cell rendering mucks with the button visibility during the solvetraverse loop,
                                                                                        #so force applyschemesettings to make sure its run
        pButton.SetSize(width, 24)
        pButton.AddActionSignalTarget(self)
        pButton.SetContentAlignment(Label.a_west)
        pButton.SetTextInset(5, 0)

        column.header = pButton
        column.minwidth = minWidth
        column.maxwidth = maxWidth
        column.resizeswithwindow = columnFlags & self.COLUMN_RESIZEWITHWINDOW
        column.typeistext = not (columnFlags & self.COLUMN_IMAGE)
        column.hidden = False
        column.unhidable = (columnFlags & self.COLUMN_UNHIDABLE)
        column.contentalignment = Label.a_west

        dragger = Dragger(index)
        dragger.SetParent(self)
        dragger.AddActionSignalTarget(self)
        dragger.MoveToFront()
        if minWidth == maxWidth or (columnFlags & self.COLUMN_FIXEDSIZE): 
            # not resizable so disable the slider 
           dragger.SetMovable(False)
        
        column.resizer = dragger

        # add default sort function
        column.sortfunc = None
        
        # Set the SortedTree less than func to the generic RBTreeLessThanFunc
        self.columnsdata[columnDataIndex].sortedtree.SetLessFunc(RBTreeLessFunc)

        # go through all the headers and make sure their Command has the right column ID
        self.ResetColumnHeaderCommands()

        # create the data index
        self.ResortColumnRBTree(index)

        # ensure scroll bar is topmost compared to column headers
        self.vbar.MoveToFront()

        # fix up our visibility
        self.SetColumnVisible(index, not (columnFlags & self.COLUMN_HIDDEN))

        self.InvalidateLayout()

    def ResortColumnRBTree(self, col):
        """ Recreates a column's RB Sorted Tree """
        global s_pCurrentSortingListPanel, s_currentSortingColumnTypeIsText
        global s_pSortFunc, s_bSortAscending, s_pSortFuncSecondary
        try:
            dataColumnIndex = self.currentcolumns[col]
        except IndexError:
            assert(0)

        #dataColumnIndex = self.currentcolumns[col]
        columnHistoryIndex = self.columnshistory.index(dataColumnIndex)
        column = self.columnsdata[dataColumnIndex]

        rbtree = column.sortedtree

        # remove all elements - we're going to create from scratch
        rbtree.RemoveAll()

        s_pCurrentSortingListPanel = self
        s_currentSortingColumnTypeIsText = column.typeistext # type of data in the column
        sortFunc = column.sortfunc
        if not sortFunc:
            sortFunc = DefaultSortFunc
        
        s_pSortFunc = sortFunc
        s_bSortAscending = True
        s_pSortFuncSecondary = None

        # sort all current data items for self column
        for i, di in enumerate(self.dataitems):
            item = IndexItem()
            item.dataItem = self.dataitems[i]
            item.duplicateIndex = 0

            dataItem = self.dataitems[i]

            # if self item doesn't already have a SortedTreeIndex for self column,
            # if can only be because self is the brand column, so add it to the sortedtreeindexes
            if (len(dataItem.sortedtreeindexes) == len(self.columnshistory) - 1 and
                        columnHistoryIndex == len(self.columnshistory) - 1):
                dataItem.sortedtreeindexes.append(0)

            #assert( dataItem.sortedtreeindexes.IsValidIndex(columnHistoryIndex) )

            dataItem.sortedtreeindexes[columnHistoryIndex] = rbtree.Insert(item)

    def ResetColumnHeaderCommands(self):
        """ Resets the "SetSortColumn" command for each column - in case columns were added or removed """
        for i, cc in enumerate(self.currentcolumns):
            pButton = self.columnsdata[cc].header
            pButton.SetCommand(KeyValues("SetSortColumn", "column", i))

    def SetColumnHeaderText(self, col, text):
        """ Sets the header text for a particular column. """
        self.columnsdata[self.currentcolumns[col]].header.SetText(text)

    def SetColumnTextAlignment(self, col, align):
        self.columnsdata[self.currentcolumns[col]].contentalignment = align

    def SetColumnHeaderImage(self, column, imageListIndex):
        """ Sets the column header to have an image instead of text """
        assert(self.imagelist)
        self.columnsdata[self.currentcolumns[column]].header.SetTextImageIndex(-1)
        self.columnsdata[self.currentcolumns[column]].header.SetImageAtIndex(0, self.imagelist.GetImage(imageListIndex), 0)
   
    def SetColumnHeaderTooltip(self, column, tooltipText):
        """ associates a tooltip with the column header """
        self.columnsdata[self.currentcolumns[column]].header.GetTooltip().SetText(tooltipText)
        self.columnsdata[self.currentcolumns[column]].header.GetTooltip().SetTooltipFormatToSingleLine()
        self.columnsdata[self.currentcolumns[column]].header.GetTooltip().SetTooltipDelay(0)

    def GetNumColumnHeaders(self):
        return len(self.currentcolumns)

    def GetColumnHeaderText(self, index ):
        if index < len(self.currentcolumns):
            out = self.columnsdata[self.currentcolumns[index]].header.GetText()
            return True, out
        else:
            return False, None

    def SetColumnSortable(self, col, sortable):
        if sortable:
            self.columnsdata[self.currentcolumns[col]].header.SetCommand(KeyValues("SetSortColumn", "column", col))
        else:
            self.columnsdata[self.currentcolumns[col]].header.SetCommand(None)
            
    def SetColumnVisible(self, col, visible):
        """ Changes the visibility of a column """
        column = self.columnsdata[self.currentcolumns[col]]
        bHidden = not visible
        if column.hidden == bHidden:
            return

        if column.unhidable:
            return

        column.hidden = bHidden
        if bHidden:
            column.header.SetVisible(False)
            column.resizer.SetVisible(False)
        else:
            column.header.SetVisible(True)
            column.resizer.SetVisible(True)

        self.InvalidateLayout()

    def RemoveColumn(self, col):
        try:
            self.currentcolumns[col]
        except IndexError:
            return

        # find the appropriate column data 
        columnDataIndex = self.currentcolumns[col]

        # remove it from the current columns
        del self.currentcolumns[col]

        # zero out self entry in self.columnshistory
        for i, ch in enumerate(self.columnshistory):
            if ch == columnDataIndex:
                self.columnshistory[i] = -1
                break

        assert( i != len(self.columnshistory) )

        # delete and remove the column data
        self.columnsdata[columnDataIndex].sortedtree.RemoveAll()
        self.columnsdata[columnDataIndex].header.DeletePanel()
        self.columnsdata[columnDataIndex].resizer.DeletePanel()
        #self.columnsdata[columnDataIndex].header.MarkForDeletion()
        #self.columnsdata[columnDataIndex].resizer.MarkForDeletion()
        del self.columnsdata[columnDataIndex]

        self.ResetColumnHeaderCommands()
        self.InvalidateLayout()

    def FindColumn(self, columnName):
        """ Returns the index of a column by column.GetName() """
        for i, cc in enumerate(self.currentcolumns):
            if columnName == self.columnsdata[self.currentcolumns[i]].header.GetName():
                return i
        return -1

    def AddItem(self, item, userData, bScrollToItem, bSortOnAdd):
        """ adds an item to the view
                    data.GetName() is used to uniquely identify an item
                    data sub items are matched against column header name to be used in the table """
        newitem = FastSortListPanelItem()
        newitem.kv = KeyValues(item)#item.MakeCopy()
        newitem.userData = userData
        newitem.dragdata = None
        newitem.bimage = bool(newitem.kv.GetInt( "image" ) != 0)
        newitem.imageindex = newitem.kv.GetInt( "image" )
        newitem.imageindexSelected = newitem.kv.GetInt( "imageSelected" )
        #newitem.icon = newitem.kv.GetPtr( "iconImage" )    # TODO

        self.dataitems.append(newitem)
        itemID = len(self.dataitems)-1
        self.visibleitems.append(itemID)
        displayRow = len(self.visibleitems)-1
        newitem.visible = True

        # put the item in each column's sorted Tree Index
        self.IndexItem(itemID)

        if bSortOnAdd:
            self.needssort = True

        self.InvalidateLayout()
        
        if bScrollToItem:
            # scroll to last item
            self.vbar.SetValue(displayRow)
        return itemID

    def SetUserData(self, itemID, userData):
        try:
            self.dataitems[itemID].userData = userData
        except IndexError:
            pass

    def GetItemIDFromUserData(self, userData):
        """ Finds the first itemID with a matching userData """
        for itemID, item in enumerate(self.dataitems):
            if item.userData == userData:
                return itemID
        
        # not found
        return self.InvalidItemID()

    def GetItemCount(self):
        return len(self.visibleitems)

    def GetItem(self, itemNameOrID):
        """ returns pointer to data the itemID holds """
        if type(itemNameOrID) is str:
            for i, di in enumerate(self.dataitems):
                if di.kv.GetName() == itemNameOrID:
                    return i
            # failure
            return -1 
        else:
            try:
                return self.dataitems[itemNameOrID].kv
            except IndexError:
                return None

    def GetItemCurrentRow(self, itemID):
        return self.visibleitems.index(itemID)

    def SetItemDragData(self, itemID, data):
        """ Attaches drag data to a particular item """
        pItem = self.dataitems[ itemID ]
        if pItem.dragdata:
            pItem.dragdata.deleteself()    
        pItem.dragdata = KeyValues(data)#data.MakeCopy()

    def OnCreateDragData(self, msg):    
        """ Attaches drag data to a particular item """
        nCount = self.GetSelectedItemsCount()
        if nCount == 0:
            return

        for i in range(0, nCount):
            nItemID = self.GetSelectedItem( i )

            pDragData = self.dataitems[ nItemID ].dragdata
            if pDragData:
                pDragDataCopy = KeyValues(pDragData) #pDragData.MakeCopy()
                msg.AddSubKey( pDragDataCopy )

        # Add the keys of the last item directly into the root also
        nLastItemID = self.GetSelectedItem( nCount - 1 )
        pLastItemDrag = self.dataitems[ nLastItemID ].dragdata
        if pLastItemDrag:
            pLastItemDrag.CopySubkeys( msg )

    def GetItemIDFromRow(self, currentRow):
        try:
            return self.visibleitems[currentRow]
        except IndexError:
            return -1

    def IsValidItemID(self, itemID):
        return itemID < len(self.dataitems)

    def GetItemData(self, itemID):
        try:
            return self.dataitems[ itemID ] 
        except IndexError:
            return None

    def GetItemUserData(self, itemID):
        """ returns user data for itemID """
        try:
            return self.dataitems[itemID].userData
        except IndexError:
            return 0

    def ApplyItemChanges(self, itemID):
        """ updates the view with any changes to the data
            itemID - index to update """
        # reindex the item and then redraw
        self.IndexItem(itemID)
        self.InvalidateLayout()

    def IndexItem(self, itemID):
        """ Adds the item into the column indexes """
        global s_pCurrentSortingListPanel, s_pCurrentSortingColumn, s_currentSortingColumnTypeIsText
        global s_pSortFunc, s_bSortAscending, s_pSortFuncSecondary
        newitem = self.dataitems[itemID]

        # remove the item from the indexes and re-add
        maxCount = min(len(self.columnshistory), len(newitem.sortedtreeindexes))
        for i in range(0, maxCount):  
            rbtree = self.columnsdata[self.columnshistory[i]].sortedtree
            rbtree.RemoveAt(newitem.sortedtreeindexes[i])

        # make sure it's all free
        newitem.sortedtreeindexes = []

        # reserve one index per historical column - pad it out
        for i in range(0, len(self.columnshistory)):
            newitem.sortedtreeindexes.append(0)

        # set the current sorting list (since the insert will need to sort)
        s_pCurrentSortingListPanel = self

        # add the item into the RB tree for each column
        for i, ch in enumerate(self.columnshistory):
            # skip over any removed columns
            try:
                self.columnsdata[ch]
            except IndexError:
                continue

            column = self.columnsdata[ch]

            item = IndexItem()
            item.dataItem = newitem
            item.duplicateIndex = 0

            rbtree = column.sortedtree

            # setup sort state
            s_pCurrentSortingListPanel = self
            s_pCurrentSortingColumn = column.header.GetName() # name of current column for sorting
            s_currentSortingColumnTypeIsText = column.typeistext # type of data in the column
            
            sortFunc = column.sortfunc
            if not sortFunc:
                sortFunc = DefaultSortFunc
            
            s_pSortFunc = sortFunc
            s_bSortAscending = True
            s_pSortFuncSecondary = None

            # insert index		
            newitem.sortedtreeindexes[i] = rbtree.Insert(item)

    def RereadAllItems(self):
        #!! need to make this more efficient
        self.InvalidateLayout()

    # TODO: Remove? Not needed?
    def CleanupItem(self, data):
        """ Cleans up allocations associated with a particular item """
        if data:
            if data.kv:
                data.kv = None
            if data.dragdata:
                data.dragdata = None

    def RemoveItem(self, itemID):
        """ Removes an item at the specified item """
        data = self.dataitems[itemID]
        if not data:
            return

        # remove from column sorted indexes
        for i, ch in enumerate(self.columnshistory):
            try:
                self.columnsdata[ch]
            except IndexError:
                continue

            rbtree = self.columnsdata[ch].sortedtree
            rbtree.RemoveAt(data.sortedtreeindexes[i])
        

        # remove from selection
        del self.selecteditems[itemID]
        self.PostActionSignal( KeyValues("ItemDeselected") )

        # remove from visible items
        del self.visibleitems[itemID]

        # remove from data
        del self.dataitems[itemID]
        self.CleanupItem( data )
        self.InvalidateLayout()

    def RemoveAll(self):
        """ clears and deletes all the memory used by the data items """
        # remove all sort indexes
        for ch in self.columnshistory:
            self.columnsdata[ch].sortedtree.RemoveAll()
 
        for di in self.dataitems:
            self.CleanupItem( di )

        self.dataitems = []
        self.visibleitems = []
        self.ClearSelectedItems()

        self.InvalidateLayout()

    #def DeleteAllItems(self):
    #    """ obselete, use RemoveAll() """
    #    self.RemoveAll()

    def ResetScrollBar(self):
        # delete and reallocate to besure the scroll bar's
        # information is correct.
        self.vbar = ScrollBar(self, "VertScrollBar", True)
        self.vbar.SetVisible(False)
        self.vbar.AddActionSignalTarget(self)

    def GetSelectedItemsCount(self):
        """ returns the count of selected rows """
        return len(self.selecteditems)

    def GetSelectedItem(self, selectionIndex):
        """ returns the selected item by selection index
            Input  : selectionIndex - valid in range [0, GetNumSelectedRows)
            Output : int - itemID """
        try:
            return self.selecteditems[selectionIndex]
        except IndexError:
            return -1

    def GetSelectedColumn(self):
        return self.selectcolumn

    def ClearSelectedItems(self):
        """ Clears all selected rows """
        nPrevCount = len(self.selecteditems)
        self.selecteditems = []
        if nPrevCount > 0:
            self.PostActionSignal( KeyValues("ItemDeselected") )
        
        self.lastitemselected = -1
        self.selectcolumn = -1
        self.FlushSBuffer()

    def IsItemSelected(self, itemID):
        return itemID < len(self.dataitems) and itemID in self.selecteditems

    def AddSelectedItem(self, itemID):
        if itemID >= len(self.dataitems):
            return

        if itemID in self.selecteditems:
            return

        self.lastitemselected = itemID
        self.selecteditems.append( itemID )
        self.PostActionSignal( KeyValues("ItemSelected") )
        self.Repaint()
        self.FlushSBuffer()

    def SetSingleSelectedItem(self, itemID):
        self.ClearSelectedItems()
        self.AddSelectedItem(itemID)

    def SetSelectedCell(self, itemID, col):
        if not self.canselectindividualcells:
            self.SetSingleSelectedItem(itemID)
            return

        # make sure it's a valid cell
        try:
            self.dataitems[itemID]
            self.currentcolumns[col]
        except IndexError:
            return

        self.SetSingleSelectedItem(itemID)
        self.selectcolumn = col

    def GetCellText(self, itemID, col):
        """ returns the data held by a specific cell """
        itemData = self.GetItem(itemID)
        if not itemData:
            return None

        # Look up column header
        try:
            key = self.columnsdata[self.currentcolumns[col]].header.GetName()
        except IndexError:
            return None
        
        if not key:
            return None
        
        val = itemData.GetString( key, "" )
        if not val:
            return None

        wval = None

        # TODO: Add localize
        if val[0] == '#':
            si = localize.FindIndex( val[1:len(val)] )
            if si != INVALID_STRING_INDEX:
                wval = localize.GetValueByIndex(si)

        if not wval:
            wval = val#itemData.GetString( key, "" )

        return wval

    def GetCellImage(self, itemID, col):
        """ returns the data held by a specific cell """
        itemData = self.GetItem(itemID)
        if not itemData:
            return None
        
        # Look up column header
        try:
            key = self.columnsdata[self.currentcolumns[col]].header.GetName()
        except IndexError:
            return None
        
        if not key:
            return None

        if not self.imagelist:
            return None

        imageIndex = itemData.GetInt(key, 0)
        if self.imagelist.IsValidIndex(imageIndex):
            if imageIndex > 0:
                return self.imagelist.GetImage(imageIndex)
        
        return None

    def GetCellRenderer(self, itemID, col):
        """ Returns the panel to use to render a cell """
        assert(self.textimage)
        assert(self.imagepanel)
        
        column = self.columnsdata[self.currentcolumns[col]]

        pScheme = scheme().GetIScheme(self.GetScheme())

        self.label.SetContentAlignment(column.contentalignment)

        if column.typeistext:
            # Grab cell text
            tempText = self.GetCellText( itemID, col)
            item = self.GetItem( itemID )
            self.textimage.SetText(tempText)
            cw, tall = self.textimage.GetContentSize()

            # set cell size
            header = column.header
            wide = header.GetWide()
            self.textimage.SetSize( min( cw, wide - 5 ), tall)

            self.label.SetTextImageIndex( 0 )
            self.label.SetImageAtIndex(0, self.textimage, 3)
                
            selected = False
            haselement = itemID in self.selecteditems

            if haselement and (not self.canselectindividualcells or col == self.selectcolumn):
                selected = True
                focus = vgui_input().GetFocus()
                # if one of the children of the SectionedListPanel has focus, then 'we have focus' if we're selected
                if self.HasFocus() or (focus and ipanel().HasParent(focus, self.GetVParent())):
                    self.label.SetBgColor(self.GetSchemeColor("ListPanel.SelectedBgColor", pScheme))
                    # selection   
                else:
                    self.label.SetBgColor(self.GetSchemeColor("ListPanel.SelectedOutOfFocusBgColor", pScheme))   

                if item.IsEmpty("cellcolor") == False:
                    self.textimage.SetColor(item.GetColor( "cellcolor" ))
                elif item.GetInt("disabled", 0) == 0:
                    self.textimage.SetColor(self.selectionfgcolor)
                else:
                    self.textimage.SetColor(self.disabledselectionfgcolor)

                self.label.SetPaintBackgroundEnabled(True)
            else:
                if item.IsEmpty("cellcolor") == False:
                    self.textimage.SetColor(item.GetColor( "cellcolor" ))
                elif item.GetInt("disabled", 0) == 0:
                    self.textimage.SetColor(self.labelfgcolor)
                else:
                    self.textimage.SetColor(self.disabledcolor)
                self.label.SetPaintBackgroundEnabled(False)

            listItem = self.dataitems[itemID]
            if col == 0 and listItem.bimage and self.imagelist:
                pImage = None
                if listItem.icon:
                    pImage = listItem.icon
                else:
                    if selected:
                        imageIndex = listItem.imageindexSelected
                    else:
                        imageIndex = listItem.imageindex
                    if self.imagelist.IsValidIndex(imageIndex):
                        pImage = self.imagelist.GetImage(imageIndex)

                if pImage:
                    self.label.SetTextImageIndex(1)
                    self.label.SetImageAtIndex(0, pImage, 0)
                    self.label.SetImageAtIndex(1, self.textimage, 3)
            return self.label
        
        else: # if its an Image Panel
            try:
                self.selecteditems.index(itemID)
                haselement = True
            except ValueError:
                haselement = False
            if haselement and ( not self.canselectindividualcells or col == self.selectcolumn ):
                focus = vgui_input().GetFocus()
                # if one of the children of the SectionedListPanel has focus, then 'we have focus' if we're selected
                if self.HasFocus() or (focus and ipanel().HasParent(focus, self.GetVParent())):
                    self.label.SetBgColor(self.GetSchemeColor("ListPanel.SelectedBgColor", pScheme))
                    # selection
                
                else:
                    self.label.SetBgColor(self.GetSchemeColor("ListPanel.SelectedOutOfFocusBgColor", pScheme))
                # selection
                self.label.SetPaintBackgroundEnabled(True)
            else:
                self.label.SetPaintBackgroundEnabled(False)

            pIImage = self.GetCellImage(itemID, col)
            self.label.SetImageAtIndex(0, pIImage, 0)

            return self.label

    def PerformLayout(self):
        """ relayouts out the panel after any internal changes """
        if len(self.currentcolumns) == 0:
            return
        
        if self.needssort:
            self.SortList()

        rowsperpage = int(self.GetRowsPerPage())

        # count the number of visible items
        visibleItemCount = len(self.visibleitems)

        #!! need to make it recalculate scroll positions
        self.vbar.SetVisible(True)
        self.vbar.SetEnabled(False)
        self.vbar.SetRangeWindow(rowsperpage)
        self.vbar.SetRange(0, visibleItemCount)
        self.vbar.SetButtonPressedScrollValue(1)

        wide, tall = self.GetSize()
        self.vbar.SetPos(wide - (self.vbar.GetWide()+self.WINDOW_BORDER_WIDTH), 0)
        self.vbar.SetSize(self.vbar.GetWide(), tall - 2)
        self.vbar.InvalidateLayout()

        buttonMaxXPos = wide - (self.vbar.GetWide()+self.WINDOW_BORDER_WIDTH)
        
        nColumns = len(self.currentcolumns)
        # number of bars that can be resized
        numToResize=0
        if self.columndraggermoved != -1: # we're resizing in response to a column dragger
            numToResize = 1 # only one column will change size, the one we dragged
        else: # we're resizing in response to a window resize  
            for cc in self.currentcolumns:
                if (self.columnsdata[cc].resizeswithwindow # column is resizable in response to window
                        and not self.columnsdata[cc].hidden):
                
                    numToResize += 1

        # location of the last column resizer
        oldSizeX = oldSizeY = 0
        lastColumnIndex = nColumns-1
        for i in range(nColumns-1, -1, -1):
            if not self.columnsdata[self.currentcolumns[i]].hidden:
                oldSizeX, oldSizeY = self.columnsdata[self.currentcolumns[i]].header.GetPos()
                lastColumnIndex = i
                break

        bForceShrink = False
        if numToResize == 0:
            # make sure we've got enough to be within minwidth
            minWidth=0
            for cc in self.currentcolumns: 
                if not self.columnsdata[cc].hidden:
                    minWidth += self.columnsdata[cc].minwidth

            # if all the minimum widths cannot fit in the space given, then we will shrink ALL columns an equal amount
            if minWidth > buttonMaxXPos:
                dx = buttonMaxXPos - minWidth
                dxPerBar=int(float(dx)/float(nColumns))
                bForceShrink = True
            else:
                dxPerBar = 0
            self.lastbarwidth = buttonMaxXPos
        elif oldSizeX != 0: # make sure self isnt the first time we opened the window
            dx = buttonMaxXPos - self.lastbarwidth  # self is how much we grew or shrank.

            # see how many bars we have and now much each should grow/shrink
            dxPerBar=int(float(dx)/float(numToResize))
            self.lastbarwidth = buttonMaxXPos
        else: # self is the first time we've opened the window, make sure all our colums fit! resize if needed
            startingBarWidth=0
            for cc in self.currentcolumns:
                if not self.columnsdata[cc].hidden:  
                    startingBarWidth += self.columnsdata[cc].header.GetWide()
            
            dx = buttonMaxXPos - startingBarWidth  # self is how much we grew or shrank.
            # see how many bars we have and now much each should grow/shrink
            dxPerBar=int(float(dx)/float(numToResize))
            self.lastbarwidth = buttonMaxXPos

        # Make sure nothing is smaller than minwidth to start with or else we'll get into trouble below.
        for cc in self.currentcolumns:
            column = self.columnsdata[cc]
            header = column.header
            if header.GetWide() < column.minwidth:
                header.SetWide( column.minwidth )

        # self was a while(1) loop and we hit an infinite loop case, so now we max out the # of times it can loop.
        for iLoopSanityCheck in range(0, 1000):
            # try and place headers as is - before we have to force items to be minimum width
            x = -1
            for i, cc in enumerate(self.currentcolumns):
                column = self.columnsdata[cc]
                header = column.header
                if column.hidden:
                    header.SetVisible(False)
                    continue

                header.SetPos(x, 0)
                header.SetVisible(True)

                # if we couldn't fit self column - then we need to force items to be minimum width
                if x+column.minwidth >= buttonMaxXPos and not bForceShrink:
                    break

                hWide = header.GetWide()

                # calculate the column's width
                # make it so the last column always attaches to the scroll bar
                if i == lastColumnIndex:
                    hWide = buttonMaxXPos-x  
                elif i == self.columndraggermoved: # column resizing using dragger
                    hWide += dxPerBar # adjust width of column
                elif self.columndraggermoved == -1: # window is resizing
                    # either self column is allowed to resize OR we are forcing it because we're shrinking all columns
                    if column.resizeswithwindow or bForceShrink:
                        assert (column.minwidth <= column.maxwidth)
                        hWide += dxPerBar # adjust width of column

                # enforce column mins and max's - unless we're FORCING it to shrink
                if hWide < column.minwidth and not bForceShrink: 
                    hWide = column.minwidth # adjust width of column
                elif hWide > column.maxwidth: 
                    hWide = column.maxwidth
        
                header.SetSize(hWide, self.vbar.GetWide())
                x += hWide
        
                # set the resizers
                sizer = column.resizer
                if i == lastColumnIndex:
                    sizer.SetVisible(False)
                else:
                    sizer.SetVisible(True)
                
                sizer.MoveToFront()
                sizer.SetPos(x - 4, 0)
                sizer.SetSize(8, self.vbar.GetWide())
            
            # we made it all the way through
            if i == (nColumns-1):
                break
        
            # we do self AFTER trying first, to let as many columns as possible try and get to their
            # desired width before we forcing the minimum width on them

            # get the total desired width of all the columns
            totalDesiredWidth = 0
            for cc in self.currentcolumns:
                if not self.columnsdata[cc].hidden:
                    pHeader = self.columnsdata[cc].header
                    totalDesiredWidth += pHeader.GetWide()

            # shrink from the most right column to minimum width until we can fit them all
            assert(totalDesiredWidth > buttonMaxXPos)
            for i in range(nColumns-1, -1, -1):
                column = self.columnsdata[self.currentcolumns[i]]
                if not column.hidden:
                    pHeader = column.header

                    totalDesiredWidth -= pHeader.GetWide()
                    if totalDesiredWidth + column.minwidth <= buttonMaxXPos:
                        newWidth = buttonMaxXPos - totalDesiredWidth
                        pHeader.SetSize( newWidth, self.vbar.GetWide() )
                        break 

                    totalDesiredWidth += column.minwidth
                    pHeader.SetSize(column.minwidth, self.vbar.GetWide())
            
            # If we don't allow self to shrink, then as we resize, it can get stuck in an infinite loop.
            dxPerBar -= 5
            if dxPerBar < 0:
                dxPerBar = 0

            if i == -1:
                break
                
        # setup edit mode
        if self.editmodepanel:
            self.tablestartx = 0 
            self.tablestarty = self.headerheight + 1

            nTotalRows = len(self.visibleitems)
            nRowsPerPage = self.GetRowsPerPage()

            # find the first visible item to display
            nStartItem = 0
            if nRowsPerPage <= nTotalRows:
                nStartItem = self.vbar.GetValue()

            bDone = False
            drawcount = 0
            for i in range(nStartItem, nTotalRows):
                if bDone:
                    break
                x = 0
                if not self.visibleitems.IsValidIndex(i):
                    continue

                itemID = self.visibleitems[i]
                
                # iterate the columns
                for j, cc in enumerate(self.currentcolumns):
                    header = self.columnsdata[cc].header

                    if not header.IsVisible():
                        continue

                    wide = header.GetWide()

                    if ( itemID == self.editmodeitemid and
                            j == self.editmodecolumn ):
                        self.editmodepanel.SetPos( x + self.tablestartx + 2, (drawcount * self.rowheight) + self.tablestarty)
                        self.editmodepanel.SetSize( wide, self.rowheight - 1 )

                        bDone = True 

                    x += wide

                drawcount += 1

        self.Repaint()
        self.columndraggermoved = -1 # reset to invalid column

    def OnSizeChanged(self, wide, tall):
        super(ListPanel, self).OnSizeChanged(wide, tall)
        self.InvalidateLayout()
        self.Repaint()

    @profile('ListPanel.Paint')
    def Paint(self):
        """ Renders the cells """
        if self.needssort:
            self.SortList()

        # draw selection areas if any
        wide, tall = self.GetSize()

        self.tablestartx = 0 
        self.tablestarty = self.headerheight + 1

        nTotalRows = len(self.visibleitems)
        nRowsPerPage = self.GetRowsPerPage()

        # find the first visible item to display
        nStartItem = 0
        if nRowsPerPage <= nTotalRows:
            nStartItem = self.vbar.GetValue()

        vbarInset = 0
        if self.vbar.IsVisible():
            vbarInset = self.vbar.GetWide()
        maxw = wide - vbarInset - 8

    #	debug timing functions
    #	startTime = system().GetCurrentTime()

        # iterate through and draw each cell
        bDone = False
        drawcount = 0
        for i in range(nStartItem, nTotalRows):
            if bDone:
                break
            x = 0
            try:
                self.visibleitems[i]
            except IndexError:
                continue

            itemID = self.visibleitems[i]
            
            # iterate the columns
            for j, cc in enumerate(self.currentcolumns):
                header = self.columnsdata[cc].header
                render = self.GetCellRenderer(itemID, j)

                if not header.IsVisible():
                    continue

                wide = header.GetWide()

                if render:
                    # setup render panel
                    if render.GetVParent() != self.GetVPanel(): 
                        render.SetParent(self.GetVPanel())
                    
                    if not render.IsVisible():
                        render.SetVisible(True)
                    
                    xpos = x + self.tablestartx + 2

                    render.SetPos(xpos, (drawcount * self.rowheight) + self.tablestarty)

                    right = min(xpos + wide, maxw)
                    usew = right - xpos
                    render.SetSize(usew, self.rowheight - 1)

                    # mark the panel to draw immediately (since it will probably be recycled to draw other cells)
                    render.Repaint()
                    surface().SolveTraverse(render.GetVPanel())
                    x0, y0, x1, y1 = render.GetClipRect()
                    if (y1 - y0) < (self.rowheight - 3):
                        bDone = True
                        break
                    
                    surface().PaintTraverse(render.GetVPanel())
                
                # work in progress, optimized paint for text
                # else
                
                    # # just paint it ourselves
                    # char tempText[256]
                    # # Grab cell text
                    # GetCellText(i, j, tempText, sizeof(tempText))
                    # surface().DrawSetTextPos(x + self.tablestartx + 2, (drawcount * self.rowheight) + self.tablestarty)

                    # for (const char *pText = tempText *pText != 0 pText++)
                        # surface().DrawUnicodeChar(pText)

                x += wide

            drawcount += 1
        

        self.label.SetVisible(False)

        # if the list is empty, draw some help text
        if len(self.visibleitems) < 1 and self.emptylisttext:
            self.emptylisttext.SetPos(self.tablestartx + 8, self.tablestarty + 4)
            self.emptylisttext.SetSize(wide - 8, self.rowheight)
            self.emptylisttext.Paint()
        

    #	endTime = system().GetCurrentTime()
    #	ivgui().DPrintf2("ListPanel.Paint() (%.3f sec)\n", (float)(endTime - startTime))

    def HandleMultiSelection(self, itemID, row, column):
        """ Handles multiselect  """
        # deal with 'multiple' row selection

        # convert the last item selected to a row so we can multiply select by rows NOT items
        lastSelectedRow = row
        if self.lastitemselected != -1:
            row = self.visibleitems.index(self.lastitemselected)
        if row < lastSelectedRow:
            startRow = row
            endRow = lastSelectedRow
        else:
            startRow = lastSelectedRow
            endRow = row

        # clear the selection if neither control key was down - we are going to readd ALL selected items
        # in case the user changed the 'direction' of the shift add
        if not vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) and not vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL):
            self.ClearSelectedItems()

        # add any items that we haven't added
        for i in range(startRow, endRow+1):
            # get the item indexes for these rows
            selectedItemID = self.visibleitems[i]
            if selectedItemID in self.selecteditems:
                continue
            self.AddSelectedItem( selectedItemID )

    def HandleAddSelection(self, itemID, row, column):
        """ Handles multiselect """
        # dealing with row selection
        try:
            # self row is already selected, remove
            self.selecteditems.remove( itemID )
            self.PostActionSignal( KeyValues("ItemDeselected") )
            self.lastitemselected = itemID
            self.FlushSBuffer()
        except ValueError:
            self.AddSelectedItem( itemID )

    def UpdateSelection(self, code, x, y, row, column):
        # make sure we're clicking on a real item
        if row < 0 or row >= len(self.visibleitems):
            self.ClearSelectedItems()
            return

        itemID = self.visibleitems[ row ]

        # if we've right-clicked on a selection, don't change the selection
        try:
            if code == ButtonCode_t.MOUSE_RIGHT and self.selecteditems.index( itemID ):
                return
        except ValueError:
            pass

        if self.canselectindividualcells:
            if vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL):
                # we're ctrl selecting the same cell, clear it
                if ( self.lastitemselected == itemID ) and ( self.selectcolumn == column ) and ( len(self.selecteditems) == 1 ):
                    self.ClearSelectedItems()   
                else:
                    self.SetSelectedCell( itemID, column )
            else:
                self.SetSelectedCell( itemID, column )
            return

        if not self.multiselectenabled:
            self.SetSingleSelectedItem( itemID )
            return

        if vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT):
            # check for multi-select
            self.HandleMultiSelection( itemID, row, column )
        elif vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL):
            # check for row-add select
            self.HandleAddSelection( itemID, row, column )
        else:
            # no CTRL or SHIFT keys
            # reset the selection Start point
    #			if ( self.lastitemselected != itemID ) or ( len(self.selecteditems) > 1 ):
                self.SetSingleSelectedItem( itemID )
            
    def OnMousePressed(self, code):
        if code == ButtonCode_t.MOUSE_LEFT or code == ButtonCode_t.MOUSE_RIGHT:
            if len(self.visibleitems) > 0:
                # determine where we were pressed
                x, y = vgui_input().GetCursorPos()
                s, row, column = self.GetCellAtPos(x, y)

                self.UpdateSelection( code, x, y, row, column )
           
            # get the key focus
            self.RequestFocus()

        # check for context menu open
        if code == ButtonCode_t.MOUSE_RIGHT:
            if len(self.selecteditems) > 0:
                self.PostActionSignal( KeyValues("OpenContextMenu", "itemID", self.selecteditems[0] ))
            else:
                # post it, but with the invalid row
                self.PostActionSignal( KeyValues("OpenContextMenu", "itemID", -1 ))
            
    def OnMouseWheeled(self, delta):
        """ Scrolls the list according to the mouse wheel movement """
        if self.editmodepanel:
            # ignore mouse wheel in edit mode, forward right up to parent
            self.CallParentFunction(KeyValues("MouseWheeled", "delta", delta))
            return

        val = self.vbar.GetValue()
        val -= (delta * 3)
        self.vbar.SetValue(val)

    def OnMouseDoublePressed(self, code):
        """ Double-click act like the the item under the mouse was selected
            and then the enter key hit """
        if code == ButtonCode_t.MOUSE_LEFT:
            # select the item
            self.OnMousePressed(code)
            
            # post up an enter key being hit if anything was selected
            if self.GetSelectedItemsCount() > 0 and not self.ignoredoubleclick:
                self.OnKeyCodeTyped(ButtonCode_t.KEY_ENTER)
            
    def OnKeyCodeTyped(self, code):
        if self.editmodepanel:
            # ignore arrow keys in edit mode
            # forward right up to parent so that tab focus change doesn't occur
            self.CallParentFunction(KeyValues("KeyCodeTyped", "code", code))
            return

        nTotalRows = len(self.visibleitems)
        nTotalColumns = len(self.currentcolumns)
        if nTotalRows == 0:
            return

        # calculate info for adjusting scrolling
        nStartItem = self.GetStartItem()
        nRowsPerPage = int(self.GetRowsPerPage())

        nSelectedRow = 0
        try:
            nSelectedRow = self.visibleitems.index( self.lastitemselected )
        except ValueError:
            pass

        nSelectedColumn = self.selectcolumn

        if code == ButtonCode_t.KEY_HOME:
            nSelectedRow = 0
        elif code == ButtonCode_t.KEY_END:
            nSelectedRow = nTotalRows - 1
        elif code == ButtonCode_t.KEY_PAGEUP:
            if nSelectedRow <= nStartItem:
                # move up a page
                nSelectedRow -= (nRowsPerPage - 1)
            else:
                # move to the top of the current page
                nSelectedRow = nStartItem
        elif code == ButtonCode_t.KEY_PAGEDOWN:
            if nSelectedRow >= (nStartItem + nRowsPerPage-1):
                # move down a page
                nSelectedRow += (nRowsPerPage - 1)
            else:
                # move to the bottom of the current page
                nSelectedRow = nStartItem + (nRowsPerPage - 1)
        elif code == ButtonCode_t.KEY_UP:
            nSelectedRow -= 1
        elif code == ButtonCode_t.KEY_DOWN:
            nSelectedRow += 1
        elif code == ButtonCode_t.KEY_LEFT:
            if self.canselectindividualcells and (self.GetSelectedItemsCount() == 1) and (nSelectedColumn >= 0):
                nSelectedColumn -= 1
                if nSelectedColumn < 0:
                    nSelectedColumn = 0
        elif code == ButtonCode_t.KEY_RIGHT:
            if self.canselectindividualcells and (self.GetSelectedItemsCount() == 1) and (nSelectedColumn >= 0):
                nSelectedColumn += 1
                if nSelectedColumn >= nTotalColumns:
                    nSelectedColumn = nTotalColumns - 1
        else:
            # chain back
            super(ListPanel, self).OnKeyCodeTyped(code)
            return

        # make sure newly selected item is a valid range
        nSelectedRow = clamp(nSelectedRow, 0, nTotalRows - 1)

        row = self.visibleitems[ nSelectedRow ]

        # self will select the cell if in single select mode, or the row in multiselect mode
        if ( row != self.lastitemselected ) or ( nSelectedColumn != self.selectcolumn ) or ( len(self.selecteditems) > 1 ):
            self.SetSelectedCell( row, nSelectedColumn )

        # move the newly selected item to within the visible range
        if nRowsPerPage < nTotalRows:
            nStartItem = self.vbar.GetValue()
            if nSelectedRow < nStartItem:
                # move the list back to match
                self.vbar.SetValue( nSelectedRow )
            elif nSelectedRow >= nStartItem + nRowsPerPage:
                # move list forward to match
                self.vbar.SetValue( nSelectedRow - nRowsPerPage + 1)
            
        # redraw
        self.InvalidateLayout()

    def GetCellBounds(self, row, col):
        x = y = wide = tall = 0
        if col < 0 or col >= len(self.currentcolumns):
            return False, x, y, wide, tall

        if row < 0 or row >= len(self.visibleitems):
            return False, x, y, wide, tall

        # Is row on screen?
        startitem = self.GetStartItem()
        if row < startitem or row >= ( startitem + self.GetRowsPerPage() ):
            return False, x, y, wide, tall

        y = self.tablestarty
        y += ( row - startitem ) * self.rowheight
        tall = self.rowheight

        # Compute column cell
        x = self.tablestartx
        # walk columns
        c = 0
        while c < col:
            x += self.columnsdata[self.currentcolumns[c]].header.GetWide()
            c += 1
        
        wide = self.columnsdata[self.currentcolumns[c]].header.GetWide()
        return True, x, y, wide, tall

    def GetCellAtPos(self, x, y):
        """ returns True if any found, row and column are filled out """
        # convert to local
        x, y = self.ScreenToLocal(x, y)

        # move to Start of table
        x -= self.tablestartx
        y -= self.tablestarty

        startitem = self.GetStartItem()
        # make sure it's still in valid area
        if x >= 0 and y >= 0:
            # walk the rows (for when row height is independant each row)  
            # NOTE: if we do height independent rows, we will need to change GetCellBounds as well
            for row, vi in enumerate(self.visibleitems):
                if y < ( ( ( row - startitem ) + 1 ) * self.rowheight ):
                    break
            
            # walk columns
            startx = 0
            for col, cc in enumerate(self.currentcolumns):
                startx += self.columnsdata[cc].header.GetWide()

                if x < startx:
                    break

            # make sure we're not out of range
            if not ( row == len(self.visibleitems) or col == len(self.currentcolumns) ):
                return True, row, col

        # out-of-bounds
        row = col = -1
        return False, row, col

    def ApplySchemeSettings(self, schemeobj):
        # force label to apply scheme settings now so we can override it
        self.label.InvalidateLayout(True)

        super(ListPanel, self).ApplySchemeSettings(schemeobj)

        self.SetBgColor(self.GetSchemeColor("ListPanel.BgColor", schemeobj))
        self.SetBorder(schemeobj.GetBorder("ButtonDepressedBorder"))

        self.label.SetBgColor(self.GetSchemeColor("ListPanel.BgColor", schemeobj))

        self.labelfgcolor = self.GetSchemeColor("ListPanel.TextColor", schemeobj)
        self.disabledcolor = self.GetSchemeColor("ListPanel.DisabledTextColor", self.labelfgcolor, schemeobj)
        self.selectionfgcolor = self.GetSchemeColor("ListPanel.SelectedTextColor", self.labelfgcolor, schemeobj)
        self.disabledselectionfgcolor = self.GetSchemeColor("ListPanel.DisabledSelectedTextColor", self.labelfgcolor, schemeobj)

        self.emptylisttext.SetColor(self.GetSchemeColor("ListPanel.EmptyListInfoTextColor", schemeobj))
            
        self.SetFont( schemeobj.GetFont("Default", self.IsProportional() ) )
        self.emptylisttext.SetFont( schemeobj.GetFont( "Default", self.IsProportional() ) )

    def SetSortFunc(self, col, func):
        assert(col < len(self.currentcolumns))
        dataColumnIndex = self.currentcolumns[col]

        if not self.columnsdata[dataColumnIndex].typeistext and func != None:    
            self.columnsdata[dataColumnIndex].header.SetMouseClickEnabled(MOUSE_LEFT, 1)

        self.columnsdata[dataColumnIndex].sortfunc = func

        # resort self column according to sort func
        self.ResortColumnRBTree(col)

    def SetSortColumn(self, column):
        self.sortcolumn = column

    def GetSortColumn(self):
        return self.sortcolumn

    def SetSortColumnEx(self, iPrimarySortColumn, iSecondarySortColumn, bSortAscending):
        self.sortcolumn = iPrimarySortColumn
        self.sortcolumnSecondary = iSecondarySortColumn
        self.sortascending = bSortAscending

    def GetSortColumnEx(self):
        return self.sortcolumn, self.sortcolumnSecondary, self.sortascending

    def SortList(self):
        global s_pCurrentSortingListPanel, s_currentSortingColumnTypeIsText
        global s_pSortFunc, s_bSortAscending, s_pSortFuncSecondary, s_bSortAscendingSecondary
        self.needssort = False

        if len(self.visibleitems) <= 1: 
            return

        # check if the last selected item is on the screen - if so, we should try to maintain it on screen 
        startItem = self.GetStartItem()
        rowsperpage = int(self.GetRowsPerPage())
        screenPosition = -1
        if self.lastitemselected != -1 and len(self.selecteditems) > 0:
            selectedItemRow = self.visibleitems.index(self.lastitemselected)
            if selectedItemRow >= startItem and selectedItemRow <= ( startItem + rowsperpage ):
                screenPosition = selectedItemRow - startItem

        # get the required sorting functions
        s_pCurrentSortingListPanel = self

        # setup globals for use in qsort
        s_pSortFunc = FastSortFunc
        s_bSortAscending = self.sortascending
        s_pSortFuncSecondary = FastSortFunc
        s_bSortAscendingSecondary = self.sortascendingSecondary

        # walk the tree and set up the current indices
        try:
            rbtree = self.columnsdata[self.currentcolumns[self.sortcolumn]].sortedtree
            index = rbtree.FirstInorder()
            lastIndex = rbtree.LastInorder()
            prevDuplicateIndex = 0
            sortValue = 1
            while True:
                dataItem = rbtree[index].dataItem
                if dataItem.visible:
                    # only increment the sort value if we're a different token from the previous
                    if not prevDuplicateIndex or prevDuplicateIndex != rbtree[index].duplicateIndex:
                        sortValue += 1
                    dataItem.primarySortIndexValue = sortValue
                    prevDuplicateIndex = rbtree[index].duplicateIndex

                if index == lastIndex:
                    break

                index = rbtree.NextInorder(index)
        except IndexError:
            pass

        # setup secondary indices
        try:
            rbtree = self.columnsdata[self.currentcolumns[self.sortcolumnSecondary]].sortedtree
            index = rbtree.FirstInorder()
            lastIndex = rbtree.LastInorder()
            sortValue = 1
            prevDuplicateIndex = 0
            while True:
                dataItem = rbtree[index].dataItem
                if dataItem.visible:
                    # only increment the sort value if we're a different token from the previous
                    if not prevDuplicateIndex or prevDuplicateIndex != rbtree[index].duplicateIndex:
                        sortValue += 1
                    dataItem.secondarySortIndexValue = sortValue

                    prevDuplicateIndex = rbtree[index].duplicateIndex

                if index == lastIndex:
                    break

                index = rbtree.NextInorder(index)
        except IndexError:
            pass
            
        # sort the list
        self.visibleitems.sort(key=AscendingSortFunc2, reverse=s_bSortAscending)

        if screenPosition != -1:
            selectedItemRow = self.visibleitems.index(self.lastitemselected)

            # if we can put the last selected item in exactly the same spot, put it there, otherwise
            # we need to be at the top of the list
            if selectedItemRow > screenPosition: 
                self.vbar.SetValue(selectedItemRow - screenPosition)       
            else:
                self.vbar.SetValue(0)

        self.InvalidateLayout()
        self.Repaint()

    def SetFont(self, font):
        assert( font )
        if not font:
            return

        self.textimage.SetFont(font)
        self.rowheight = surface().GetFontTall(font) + 2

    def OnSliderMoved(self):
        self.InvalidateLayout()
        self.Repaint()

    def OnColumnResized(self, col, delta):
        """ deltax - deltas from current position """
        self.columndraggermoved = col

        column = self.columnsdata[self.currentcolumns[col]]

        header = column.header
        wide, tall = header.GetSize()

        wide += delta

        # enforce minimum sizes for the header
        if wide < column.minwidth:
            wide = column.minwidth
        
        # enforce maximum sizes for the header
        if wide > column.maxwidth:
            wide = column.maxwidth

        # make sure we have enough space for the columns to our right
        panelWide, panelTall = self.GetSize()
        x, y = header.GetPos()
        restColumnsMinWidth = 0
        for cc in self.currentcolumns:
            nextCol = self.columnsdata[cc]
            restColumnsMinWidth += nextCol.minwidth
        
        panelWide -= ( x + restColumnsMinWidth + self.vbar.GetWide() + self.WINDOW_BORDER_WIDTH )
        if wide > panelWide:
            wide = panelWide

        header.SetSize(wide, tall)

        # the adjacent header will be moved automatically in PerformLayout()
        header.InvalidateLayout()
        self.InvalidateLayout()
        self.Repaint()

    def OnSetSortColumn(self, column):
        """ sets which column we should sort with """
        # if it's the primary column already, flip the sort direction
        if self.sortcolumn == column:
            self.sortascending = not self.sortascending
        
        else:
            # switching sort columns, keep the old one as the secondary sort
            self.sortcolumnSecondary = self.sortcolumn
            self.sortascendingSecondary = self.sortascending
        

        self.SetSortColumn(column)

        self.SortList()

    def SetItemVisible(self, itemID, state):
        """ sets whether the item is visible or not """
        try:
            data = self.dataitems[itemID]
            if data.visible == state:
                return
                
            self.needssort = True
            
            data.visible = state
      
            if data.visible:    
                # add back to end of list
                self.visibleitems.append(itemID)
            else:
                # remove from selection if it is there.
                try:
                    self.selecteditems.remove(itemID)
                    self.PostActionSignal( KeyValues("ItemDeselected") )                
                except ValueError:
                    pass

                # remove from data
                self.visibleitems.remove(itemID)
            
                self.InvalidateLayout()
        except IndexError:
            return
        
    def IsItemVisible(self, itemID):
        """ Is the item visible? """
        try:
            data = self.dataitems[itemID]
            return data.visible
        except IndexError:
            return False

    def SetItemDisabled(self, itemID, state):
        """ sets whether the item is disabled or not (effects item color) """
        try:
            self.dataitems[itemID].kv.SetInt( "disabled", state )
        except IndexError:
            return

    def GetRowsPerPage(self):   
        """ Calculate number of rows per page """
        return float(self.GetTall() - self.headerheight) / float(self.rowheight)

    def GetStartItem(self):
        """ Calculate the item we should Start on """
        # if rowsperpage < total number of rows
        if self.GetRowsPerPage() < float(len(self.visibleitems)):
            return self.vbar.GetValue()
        return 0	# otherwise Start at top

    def SetSelectIndividualCells(self, state):
        """ whether or not to select specific cells (off by default) """
        self.canselectindividualcells = state

    def SetMultiselectEnabled(self, bState):
        """ whether or not multiple cells/rows can be selected """
        self.multiselectenabled = bState

    def IsMultiselectEnabled(self):
        return self.multiselectenabled

    def SetEmptyListText(self, text):
        """ Sets the text which is displayed when the list is empty """
        self.emptylisttext.SetText(text)
        self.Repaint()

    def OpenColumnChoiceMenu(self):
        """ opens the content menu """
        if not self.allowusersadddeletecolumns:
            return

        menu = Menu(self, "ContextMenu")

        x, y = vgui_input().GetCursorPos()
        menu.SetPos(x, y)

        # add all the column choices to the menu
        for i, cc in enumerate(self.currentcolumns):
            column = self.columnsdata[cc]

            name = column.header.GetText()
            itemID = menu.AddCheckableMenuItem(name, KeyValues("ToggleColumnVisible", "col", self.currentcolumns[i]), self)
            menu.SetMenuItemChecked(itemID, not column.hidden)

            if column.unhidable:
                menu.SetItemEnabled(itemID, False)

        menu.SetVisible(True)

    def ResizeColumnToContents(self, column):
        """ Resizes a column """
        # iterate all the items in the column, getting the size of each
        col = self.columnsdata[self.currentcolumns[column]]

        if not col.typeistext:
            return

        # start with the size of the column text
        wide = minRequiredWidth = tall = 0
        minRequiredWidth, tall = col.header.GetContentSize()

        # iterate every item
        for itemID in self.visibleitems:
            # get the text
            tempText = self.GetCellText( itemID, column )
            self.textimage.SetText(tempText)

            wide, tall = self.textimage.GetContentSize()

            if wide > minRequiredWidth:
                minRequiredWidth = wide

        # Introduce a slight buffer between columns
        minRequiredWidth += 4

        # call the resize
        wide, tall = col.header.GetSize()
        self.OnColumnResized(column, minRequiredWidth - wide)

    def OnToggleColumnVisible(self, col):
        """ Changes the visibilty of a column """
        try:
            # toggle the state of the column
            column = self.columnsdata[self.currentcolumns[col]]
            self.SetColumnVisible(col, column.hidden)
        except IndexError:
            return

    def ApplyUserConfigSettings(self, userConfig):
        """ sets user settings """
        # We save/restore self.lastbarwidth because all of the column widths are saved relative to that size.
        # If we don't save it, you can run into self case:
        #    - Window width is 500, load sizes setup relative to a 1000-width window
        #	  - Set window size to 1000
        #    - In PerformLayout, it thinks the window has grown by 500 (since self.lastbarwidth is 500 and window width is 1000)
        #      so it pushes out any COLUMN_RESIZEWITHWINDOW columns to their max extent and shrinks everything else to its min extent.
        self.lastbarwidth = userConfig.GetInt( "lastBarWidth", 0 )
        
        # read which columns are hidden
        for i, cc in enumerate(self.currentcolumns):
            name = str(i)+'_hidden'

            hidden = userConfig.GetInt(name, -1)
            if hidden == 0:
                self.SetColumnVisible(i, True)
            elif hidden == 1:
                self.SetColumnVisible(i, False)
            
            name = str(i)+'_width'
            nWidth = userConfig.GetInt( name, -1 )
            if nWidth >= 0:
                column = self.columnsdata[self.currentcolumns[i]]
                column.header.SetWide( nWidth )

    def GetUserConfigSettings(self, userConfig):
        """ returns user config settings for self control """
        userConfig.SetInt( "lastBarWidth", self.lastbarwidth )

        # save which columns are hidden
        for i, cc in enumerate(self.currentcolumns):
            column = self.columnsdata[cc]
            
            userConfig.SetInt(str(i)+'_hidden', int(column.hidden) )
            userConfig.SetInt(str(i)+'_width', column.header.GetWidth() )
    
    def HasUserConfigSettings(self):
        """ optimization, return True if self control has any user config settings """
        return True

    def SetAllowUserModificationOfColumns(self, allowed):
        """ data accessor """
        self.allowusersadddeletecolumns = allowed

    def SetIgnoreDoubleClick(self, state):
        self.ignoredoubleclick = state

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
        if self.editmodepanel.Get():
            self.editmodepanel.SetVisible(False)
            self.editmodepanel.SetParent(None)
            self.editmodepanel = None
            
    def IsInEditMode(self):
        """ returns True if we are currently in inline editing mode """
        return (self.editmodepanel.Get() != None)

    # Settings
    editmodepanel = None
    
    labelfgcolor = Color(255,255,255,255)
    disabledcolor = Color(255,255,255,255)
    selectionfgcolor = Color(255,255,255,255)
    disbledselectionfgcolor = Color(255,255,255,255)

    COLUMN_FIXEDSIZE		= 0x01  # set to have the column be a fixed size
    COLUMN_RESIZEWITHWINDOW	= 0x02  # set to have the column grow with the parent dialog growing
    COLUMN_IMAGE			= 0x04	# set if the column data is not text, but instead the index of the image to display
    COLUMN_HIDDEN			= 0x08	# column is hidden by default
    COLUMN_UNHIDABLE		= 0x10	# column is unhidable
    
    WINDOW_BORDER_WIDTH     = 2
