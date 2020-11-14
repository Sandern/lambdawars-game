"""
Shows a tree with items. Items can be inserted and selected.
"""
from srcbase import KeyValues, Color
from vgui import DataType_t, surface, vgui_system, vgui_input, CursorCode
from vgui.controls import Panel, TextEntry, ScrollBar, TextImage
from input import ButtonCode_t

WINDOW_BORDER_WIDTH     = 2     # the width of the window's border
TREE_INDENT_AMOUNT      = 20

def clamp(val, min, max):
    if val > max:
        return max
    if val < min:
        return min
    return val

class TreeNodeText(TextEntry):
    """
    Displays an editable text field for the text control
    """
    def __init__(self, parent, treeView):
        super(TreeNodeText, self).__init__(parent, "TreeNodeText")
        self.treeView = treeView
        
        self.editingInPlace = False
        self.labelEditingAllowed = False
        self.SetDragEnabled( False )
        self.SetDropEnabled( False )
        self.AddActionSignalTarget( self )
        self.armForEditing = False
        self.waitingForRelease = False
        self.armingTime = 0
        self.SetAllowKeyBindingChainToParent( True )
        
        self.RegMessageMethod( "TextChanged", self.OnTextChanged )
        
    def OnTextChanged(self):
        self.GetParent().InvalidateLayout()

    def IsKeyRebound(self, code, modifiers ):
        # If in editing mode, don't try and chain keypresses
        if self.editingInPlace:
            return False

        return super(TreeNodeText, self).IsKeyRebound(code, modifiers)
        
    def PaintBackground(self):
        super(TreeNodeText, self).PaintBackground()

        if not self.labelEditingAllowed:
            return

        if not self.editingInPlace:
            return

        w, h = self.GetSize()
        surface().DrawSetColor( self.GetFgColor() )
        surface().DrawOutlinedRect( 0, 0, w, h )

    def ApplySchemeSettings(self, scheme):
        super(TreeNodeText, self).ApplySchemeSettings(scheme)
        self.SetBorder(None)
        self.SetCursor(CursorCode.dc_arrow)
        
    def OnKeyCodeTyped(self, code):
        if self.editingInPlace:
            if code == ButtonCode_t.KEY_ENTER:
                self.FinishEditingInPlace()
            elif code == ButtonCode_t.KEY_ESCAPE:
                FinishEditingInPlace( true )
            else:
                super(TreeNodeText, self).OnKeyCodeTyped(code)
            return
        elif code == ButtonCode_t.KEY_ENTER and self.labelEditingAllowed:
            self.EnterEditingInPlace()
        else:
            # let parent deal with it (don't chain back to TextEntry)
            self.CallParentFunction(KeyValues("KeyCodeTyped", "code", code))
            
    CLICK_TO_EDIT_DELAY_MSEC = 500

    def OnTick(self):
        super(TreeNodeText, self).OnTick();
        if self.armForEditing:
            msecSinceArming = vgui_system().GetTimeMillis() - self.armingTime

            if msecSinceArming > self.CLICK_TO_EDIT_DELAY_MSEC:
                self.armForEditing = False
                self.waitingForRelease = False
                RemoveTickSignal( self.GetVPanel() )
                self.EnterEditingInPlace();
        
    def OnMouseReleased(self, code):
        if self.editingInPlace:
            super(TreeNodeText, self).OnMouseReleased(code)
            return
        else:
            if self.waitingForRelease and self.IsBeingDragged() == False:
                self.armForEditing = True
                self.waitingForRelease = False
                self.armingTime = vgui_system().GetTimeMillis()
                AddTickSignal( self.GetVPanel() )  
            else:
                self.waitingForRelease = False;

        # let parent deal with it
        self.CallParentFunction(KeyValues("MouseReleased", "code", code))

    def OnCursorMoved(self, x, y ):
        # let parent deal with it
        self.CallParentFunction(KeyValues("OnCursorMoved", "x", x, "y", y))

    def OnMousePressed(self, code):
        if self.editingInPlace:
            super(TreeNodeText, self).OnMousePressed(code)
            return
        else:
            shift = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT))
            ctrl = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL))

            # make sure there is only one item selected
            # before "WaitingForRelease" which leads to label editing.
            nlist = self.treeView.selectedItems
            isOnlyOneItemSelected = ( len(nlist) == 1 )

            if ( shift == False and \
                ctrl == False and \
                self.armForEditing == False and \
                self.labelEditingAllowed and \
                isOnlyOneItemSelected and \
                self.IsTextFullySelected() and \
                self.IsBeingDragged() == False ):
                self.waitingForRelease = True

        # let parent deal with it
        self.CallParentFunction(KeyValues("MousePressed", "code", code))
        
    def OnMouseDoublePressed(self, code):
        # Once we are editing, double pressing shouldn't chain up
        if self.editingInPlace:
            super(TreeNodeText, self).OnMouseDoublePressed( code )
            return

        if self.armForEditing:
            self.armForEditing = False
            self.waitingForRelease = False
            RemoveTickSignal( self.GetVPanel() )
            
        self.CallParentFunction(KeyValues("MouseDoublePressed", "code", code))

    def EnterEditingInPlace(self):
        if self.editingInPlace:
            return

        self.editingInPlace = True
        buf = self.GetText()
        self.originalText = str(buf)
        self.SetCursor(CursorCode.dc_ibeam)
        self.SetEditable( True )
        self.SelectNone()
        self.GotoTextEnd()
        self.RequestFocus()
        self.SelectAllText(False)
        self.treeView.labelBeingEdited = True

    def FinishEditingInPlace(self, revert = False):
        if not self.editingInPlace:
            return

        self.treeView.labelBeingEdited = False
        self.SetEditable( False )
        self.SetCursor(CursorCode.dc_arrow)
        self.editingInPlace = False
        text = self.GetText()

        # Not actually changed...
        if text == self.originalText:
            return

        if revert:
            self.SetText( self.originalText )
            self.GetParent().InvalidateLayout()
        else:
            kv = KeyValues( "LabelChanged", "original", self.originalText, "changed", text )
            self.PostActionSignal( kv )

    def OnKillFocus(self):
        super(TreeNodeText, self).OnKillFocus()

        self.FinishEditingInPlace()

    def OnMouseWheeled(self, delta):
        if self.editingInPlace:
            super(TreeNodeText, self).OnMouseWheeled(delta)
            return

        self.CallParentFunction(KeyValues("MouseWheeled", "delta", delta))
        
class TreeViewSubPanel(Panel):
    """
    Scrollable area of the tree control, holds the tree itself only
    """
    def __init__(self, parent):
        Panel.__init__(self, parent)

    def ApplySchemeSettings(self, scheme):
        super(TreeViewSubPanel, self).ApplySchemeSettings(scheme)
        
        self.SetBorder(None)
        
    def OnMouseWheeled(self, delta):
        self.CallParentFunction(KeyValues("MouseWheeled", "delta", delta))
        
    def OnMousePressed(self, code):
        self.CallParentFunction(KeyValues("MousePressed", "code", code))
    
    def OnMouseDoublePressed(self, code):
        self.CallParentFunction(KeyValues("MouseDoublePressed", "code", code))

    def OnCursorMoved(self, x, y):
        self.CallParentFunction(KeyValues("OnCursorMoved", "x", x, "y", y))
        
class TreeNode(Panel):
    """
    A single entry in the tree
    """
    def __init__(self, parent, treeView):
        Panel.__init__(self, parent, "TreeNode")
        self.treeView = treeView
        
        self.expandImage = TextImage("+")
        self.expandImage.SetPos(3, 1)
        
        self.text = TreeNodeText(self, self.treeView)
        self.text.SetMultiline(False)
        self.text.SetEditable(False)
        self.text.SetPos(TREE_INDENT_AMOUNT*2, 0)
        self.text.AddActionSignalTarget( self )
        
        # Initialize variables
        self.itemIndex = -1
        self.nodeWidth = 0
        self.maxVisibleWidth = 0
        self.data = None
        self.children = []
        self.parentIndex = -1
        self.expand = False
        self.expandableWithoutChildren = False
        self.clickedItem = 0
        self.clickedSelected = False
        
    def SetFont(self, font):
        assert(font)
        if font == None:
            return

        self.text.SetFont(font)
        self.expandImage.SetFont(font)
        self.InvalidateLayout()
        for c in self.children:
            c.SetFont(font)
    
    # Item data. Can be anything
    def GetData(self):
        return self.__data
    def SetData(self, data):
        self.__data = data
        if data != None:
            # set text
            self.text.SetText(data.get("Text", ""))
            self.expandableWithoutChildren = data.get("Expand", False)
            self.InvalidateLayout()
    data = property(GetData, SetData)
    
    def PaintBackground(self):
        if self.text.editingInPlace == False:
            # setup panel drawing
            if self.treeView.IsItemSelected(self.itemIndex):
                self.text.SelectAllText(False)
            else:
                self.text.SelectNoText()

        super(TreeNode, self).PaintBackground()  
    
    # Text
    def SetText(self, text):
        self.text.SetText(text)
        self.InvalidateLayout()
        
    def GetLabelEditingAllowed(self):
        return self.text.labelEditingAllowed
    def SetLabelEditingAllowed(self, labelEditingAllowed):
        assert(self.treeView.allowLabelEditing)
        self.text.labelEditingAllowed = labelEditingAllowed
    labelEditingAllowed = property(GetLabelEditingAllowed, SetLabelEditingAllowed)

    def PerformLayout(self):
        super(TreeNode, self).PerformLayout()

        width = TREE_INDENT_AMOUNT * 2

        self.text.SetPos(width, 0)

        self.text.SetToFullWidth()
        contentWide, contentTall = self.text.GetSize()
        contentWide += 10
        self.text.SetSize( contentWide, self.treeView.rowHeight )
        width += contentWide
        self.SetSize(width, self.treeView.rowHeight)

        self.nodeWidth = width
        self.CalculateVisibleMaxWidth()
        
    def GetParentNode(self):
        if self.parentIndex < 0 or self.parentIndex >= len(self.treeView.nodeList):
            return None
        return self.treeView.nodeList[self.parentIndex]
        
    def ComputeInsertionPosition(self, child):
        if self.treeView.sortMethod == None:
            return len(self.children) - 1

        start = 0
        end = len(self.children) - 1
        while start <= end:
            mid = (start + end) >> 1
            if self.treeView.sortMethod( self.children[mid].data, child.data ):
                start = mid + 1
            elif self.treeView.sortMethod( child.data, self.children[mid].data ):
                end = mid - 1
            else:
                return mid
        return end

    def FindChild(self, child):
        if self.treeView.sortMethod == None:
            for child2 in self.children:
                if child2 == child:
                    return i
            return -1

        # Find the first entry <= to the child
        start = 0
        end = len(self.children) - 1
        while start <= end:
            mid = (start + end) >> 1

            if self.children[mid] == child:
                return mid

            if self.treeView.sortMethod( self.children[mid].data, child.data ):
                start = mid + 1
            else:
                end = mid - 1

        nMax = len(self.children)
        while end < nMax:
            # Stop when we reach a child that has a different value
            if self.treeView.sortMethod( child.data, self.children[end].data ):
                return -1

            if self.children[end] == child:
                return end

            end = end + 1
        return -1
        
    def AddChild(self, child):
        i = self.ComputeInsertionPosition( child )
        self.children.insert( i, child )
        
    def SetNodeExpanded(self, expanded):
        self.expand = expanded

        if self.expand:
            # see if we have any child nodes
            if len(self.children) < 1:
                # we need to get our children from the control
                self.treeView.GenerateChildrenOfNode(self.itemIndex)

                # if we still don't have any children, then hide the expand button
                if len(self.children) < 1:
                    self.expand = False
                    self.expandableWithoutChildren = False
                    self.treeView.InvalidateLayout()
                    return

            self.expandImage.SetText("-")
        else:
            self.expandImage.SetText("+")

            if self.expandableWithoutChildren and len(self.children) > 0:
                self.treeView.RemoveChildrenOfNode( m_ItemIndex )

            # check if we've closed down on one of our children, if so, we get the focus
            selectedItem = self.treeView.GetFirstSelectedItem()
            if selectedItem != -1 and self.treeView.nodeList[selectedItem].HasParent(self):
                self.treeView.AddSelectedItem( self.itemIndex, True )
        self.CalculateVisibleMaxWidth()
        self.treeView.InvalidateLayout()
        
    def CountVisibleNodes(self):
        count = 1  # count myself
        if self.expand:
            for c in self.children:
                count += c.CountVisibleNodes()
        return count
        
    def CalculateVisibleMaxWidth(self):
        if self.expand:
            childMaxWidth = self.GetMaxChildrenWidth()
            childMaxWidth = childMaxWidth + TREE_INDENT_AMOUNT

            width = max(childMaxWidth, self.nodeWidth)
        else:
            width = self.nodeWidth
        if width != self.maxVisibleWidth:
            self.maxVisibleWidth = width
            if self.GetParentNode():
                self.GetParentNode().OnChildWidthChange()
            else:
                self.treeView.InvalidateLayout()   
                
    def OnChildWidthChange(self):
        self.CalculateVisibleMaxWidth()
                
    def GetMaxChildrenWidth(self):
        maxWidth = 0
        for c in self.children:
            childWidth = c.maxVisibleWidth
            if childWidth > maxWidth:
                maxWidth = childWidth
        return maxWidth
        
    def GetDepth(self):
        depth = 0
        parent = self.GetParentNode()
        while parent:							
            depth = depth + 1
            parent = parent.GetParentNode()
        return depth;
        
    def HasParent(self, treeNode):
        parent = self.GetParentNode()
        while parent:
            if parent == treeNode:
                return True
            parent = parent.GetParentNode()
        return False

    def SetVisible(self,state):
        super(TreeNode, self).SetVisible(state)

        childrenVisible = (state and self.expand)
        for c in self.children:
            if not c: continue
            c.SetVisible(childrenVisible)

    def Paint(self):
        if len(self.children) > 0 or self.expandableWithoutChildren:
            self.expandImage.Paint()

        # set image
        # imageIndex = 0
        # if self.IsSelected():
            # imageIndex = data.get("SelectedImage", 0)
        # else:
            # imageIndex = data.get("Image", 0)

        # if imageIndex:
            # image = self.treeView.GetImage(imageIndex)
            # if image:
                # self.imagePanel.SetImage(pImage)
            # self.imagePanel.Paint()

        self.text.Paint()

    def ApplySchemeSettings(self,scheme):
        super(TreeNode, self).ApplySchemeSettings(scheme)

        self.SetBorder( None )
        self.SetFgColor( self.treeView.GetFgColor() )
        self.SetBgColor( self.treeView.GetBgColor() )
        self.SetFont( self.treeView.font )
        
    def SetSelectionTextColor(self, clr):
        if self.text:
            self.text.SetSelectionTextColor( clr );

    def SetSelectionBgColor(self, clr):
        if self.text:
            self.text.SetSelectionBgColor( clr );

    def SetSelectionUnfocusedBgColor(self, clr):
        if self.text:
            self.text.SetSelectionUnfocusedBgColor( clr );
        
    def SetBgColor(self, color):
        super(TreeNode, self).SetBgColor(color)
        if self.text:
            self.text.SetBgColor(color)

    def SetFgColor(self, color):
        super(TreeNode, self).SetFgColor(color)
        if self.text:
            self.text.SetFgColor(color)

    def OnSetFocus(self):
        self.text.RequestFocus()
        
    def PositionAndSetVisibleNodes(self, nStart, nCount, x, y):
        # position ourselves
        if nStart == 0:
            self.SetVisible(True)
            self.SetPos(x, y)
            y = y + self.treeView.rowHeight
            nCount = nCount - 1
        else: # still looking for first element
            nStart = nStart - 1
            self.SetVisible(False)

        x = x + TREE_INDENT_AMOUNT
        for c in self.children:
            if nCount > 0 and self.expand:
                nStart, nCount, y = c.PositionAndSetVisibleNodes(nStart, nCount, x, y)
            else:
                c.SetVisible(False)   # this will make all grand children hidden as well
                
        return nStart, nCount, y
        
    def OnMouseWheeled(self, delta):
        self.CallParentFunction(KeyValues("MouseWheeled", "delta", delta));

    def OnMouseDoublePressed(self, code):
        x, y = vgui_input().GetCursorPos();

        if code == ButtonCode_t.MOUSE_LEFT:
            x, y = self.ScreenToLocal(x, y)
            if x > TREE_INDENT_AMOUNT:
                self.SetNodeExpanded(self.expand == False)

        
    def OnMouseReleased(self, code):
        super(TreeNode, self).OnMouseReleased(code)

        if vgui_input().GetMouseCapture() == self.GetVPanel():
            vgui_input().SetMouseCapture(None)
            return
        x, y = vgui_input().GetCursorPos()
        x, y = self.ScreenToLocal(x, y)

        if x < TREE_INDENT_AMOUNT:
            return

        ctrldown = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL))
        shiftdown = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT))

        if ctrldown == False and shiftdown == False and ( code == ButtonCode_t.MOUSE_LEFT ):
            self.treeView.AddSelectedItem( self.itemIndex, True )

    def OnCursorMoved(self, x, y):
        if vgui_input().GetMouseCapture() != self.GetVPanel():
            return

        x, y = self.LocalToScreen( x, y )
        x, y = self.treeView.ScreenToLocal( x, y )
        newItem = self.treeView.FindItemUnderMouse( x, y )
        if newItem == -1:
            # Fixme:  Figure out best item
            return

        startItem = self.clickedItem
        endItem = newItem
        if startItem > endItem:
            temp = startItem
            startItem = endItem
            endItem = temp

        tnodelist = []
        tnodelist = self.treeView.rootNode.FindNodesInRange( tnodelist, startItem, endItem )

        for item in tnodelist:
            if self.clickedSelected:
                self.treeView.AddSelectedItem( item.itemIndex, False )
            else:
                self.treeView.RemoveSelectedItem( item.itemIndex )
                
    def OnMousePressed(self, code):
        super(TreeNode, self).OnMousePressed(code)

        ctrl = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL))
        shift = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT))
        x, y = vgui_input().GetCursorPos()

        expandTree = self.treeView.leftClickExpandsTree

        if code == ButtonCode_t.MOUSE_LEFT:
            x, y = self.ScreenToLocal(x, y)
            if x < TREE_INDENT_AMOUNT:
                if expandTree:
                    self.SetNodeExpanded(self.expand == False)
                # self.treeView.SetSelectedItem(m_ItemIndex)    # explorer doesn't actually select item when it expands an item
                # purposely commented out in case we want to change the behavior
            else:
                self.clickedItem = self.itemIndex
                if self.treeView.multipleItemDragging == True:
                    vgui_input().SetMouseCapture( self.GetVPanel() )
  

                if shift:
                    self.treeView.RangeSelectItems( self.itemIndex )
                else:
                    if self.treeView.IsItemSelected(self.itemIndex) == False or ctrl:
                        if self.treeView.IsItemSelected(self.itemIndex) and ctrl:
                            self.treeView.RemoveSelectedItem( self.itemIndex )
                        else:
                            self.treeView.AddSelectedItem( self.itemIndex, ctrl == False )
                    elif self.treeView.IsItemSelected(self.itemIndex) and self.treeView.multipleItemDragging == True:
                        self.treeView.AddSelectedItem( self.itemIndex, shift == False )

                self.clickedSelected = self.treeView.IsItemSelected( self.itemIndex )
        elif code == ButtonCode_t.MOUSE_RIGHT:
            # context menu selection
            # If the item was selected, leave selected items alone, otherwise make it the only selected item
            if self.treeView.IsItemSelected( self.itemIndex ) == True:
                self.treeView.AddSelectedItem( self.itemIndex, True )

            # ask parent to context menu
            self.treeView.GenerateContextMenu(self.itemIndex, x, y)

    def FindItemUnderMouse(self, nStart, nCount, x, y, mx, my):
        # position ourselves
        if nStart == 0:
            posx, posy = self.GetPos()
            if my >= posy and my < posy + self.treeView.rowHeight:
                return self, nStart, nCount, y
            y = y + self.treeView.rowHeight
            nCount = nCount - 1
        else: # still looking for first element
            nStart = nStart - 1

        x = x + TREE_INDENT_AMOUNT
        for c in self.children:
            if nCount > 0 and self.expand:
                child, nStart, nCount, y = c.FindItemUnderMouse(nStart, nCount, x, y, mx, my)
                if child != None:
                    return child, nStart, nCount, y

        return None, nStart, nCount, y
        
    def CountVisibleIndex(self):
        """ counts items above this item including itself """
        nCount = 1 # myself
        if self.GetParentNode():
            for child in self.GetParentNode().children:
                if child == self:
                    break

                nCount = nCount + child.CountVisibleNodes()
            return nCount + self.GetParentNode().CountVisibleIndex()
        else:
            return nCount

class TreeView(Panel):
    def __init__(self, parent, panelName):
        super(TreeView, self).__init__(parent, panelName)

        self.subPanel = TreeViewSubPanel(self)
        self.subPanel.SetVisible(True)
        self.subPanel.SetPos(0,0)
        
        self.horzScrollBar = ScrollBar(self, "HorizScrollBar", False)
        self.horzScrollBar.AddActionSignalTarget(self)
        self.horzScrollBar.SetVisible(False)

        self.vertScrollBar = ScrollBar(self, "VertScrollBar", True)
        self.vertScrollBar.SetVisible(False)
        self.vertScrollBar.AddActionSignalTarget(self)
        
        self.nodeList = []
        self.selectedItems = []

        # Variables
        self.sortMethod = None
        self.rowHeight = 20
        self.rootNode = None
        self.font = 0
        
        self.allowLabelEditing = False
        self.dragEnabledItems = False
        #self.deleteImageListWhenDone = False
        self.labelBeingEdited = False
        self.multipleItemDragging = False
        self.leftClickExpandsTree = True
        self.allowMultipleSelections = False
        self.mostRecentlySelectedItem = -1
        
        self.scrollbarExternal = ( False, False )
        
        # Register messages
        self.RegMessageMethod( "ScrollBarSliderMoved", self.OnSliderMoved, 1, "position", DataType_t.DATATYPE_INT )
        
    def SetFont(self, font):
        assert( font )
        if font == None:
            return

        self.font = font
        self.rowHeight = surface().GetFontTall(font) + 2

        if self.rootNode:
            self.rootNode.SetFont(font)
        self.InvalidateLayout()
        
    def AddItem(self, data, parentItemIndex):
        treeNode = TreeNode(self.subPanel, self)
        treeNode.SetDragEnabled( self.dragEnabledItems )
        self.nodeList.append(treeNode)
        treeNode.itemIndex = len(self.nodeList)-1
        treeNode.data = data
        
        if self.font != 0:
            treeNode.SetFont( self.font )
        treeNode.SetBgColor( self.GetBgColor() )
        
        if parentItemIndex == -1:
            assert(self.rootNode == None)
            self.rootNode = treeNode
            treeNode.parentIndex = -1
        else:
            treeNode.parentIndex = parentItemIndex

            # add to parent list
            self.nodeList[treeNode.parentIndex].AddChild(treeNode)
            
        treeNode.MakeReadyForUse()
            
        return treeNode.itemIndex
        
    def GetItem(self, itemIndex):
        if itemIndex < 0 or itemIndex >= len(self.nodeList):
            return None
        return self.nodeList[itemIndex]
        
    def RemoveAll(self):
        self.rootNode = None
        self.nodeList = []
        self.selectedItems = []        
        
    def IsItemIndexValid(self, itemIndex):
        return itemIndex >= 0 and itemIndex < len(self.nodeList)
        
    def ExpandItem(self, itemIndex, expand):
        if self.IsItemIndexValid(itemIndex) == False:
            return

        self.nodeList[itemIndex].SetNodeExpanded(expand)
        self.InvalidateLayout()

    def IsItemExpanded(self, itemIndex):
        if self.IsItemIndexValid(itemIndex) == False:
            return

        return self.nodeList[itemIndex].expand
        
    def OnMouseWheeled(self, delta):
        """ Scrolls the list according to the mouse wheel movement """
        if self.vertScrollBar.IsVisible() == False:
            return
        val = self.vertScrollBar.GetValue()
        val = val -(delta * 3)
        self.vertScrollBar.SetValue(val)
        
    def PerformLayout(self):    
        """ Adjusts scroll area to the right size and calls the node methods for positioning """
        wide, tall = self.GetSize()

        if self.rootNode == None:
            self.subPanel.SetSize( wide, tall )
            return
          
        sbhw, sbhh = self.GetScrollBarSize(False)
        sbvw, sbvh = self.GetScrollBarSize(True)       
        
        vbarNeeded = False
        hbarNeeded = False

        # okay we have to check if we need either scroll bars, since if we need one
        # it might make it necessary to have the other one
        nodesVisible = tall / self.rowHeight

        # count the number of visible items
        visibleItemCount = self.rootNode.CountVisibleNodes()
        maxWidth = self.rootNode.maxVisibleWidth + 10 # 10 pixel buffer

        vbarNeeded = visibleItemCount > nodesVisible
        
        if vbarNeeded == False:
            if maxWidth > wide:
                hbarNeeded = True

                # recalculate if vbar is needed now
                # double check that we really don't need it
                nodesVisible = (tall - sbhh) / self.rowHeight
                vbarNeeded = visibleItemCount > nodesVisible
        else:
            # we've got the vertical bar here, so shrink the width
            hbarNeeded = maxWidth > (wide - (sbvw+2))

            if hbarNeeded:
                nodesVisible = (tall - sbhh) / self.rowHeight
        
        subPanelWidth = wide
        subPanelHeight = tall
        
        vbarPos = 0
        if vbarNeeded:
            subPanelWidth = subPanelWidth - (sbvw + 2)
            barSize = tall
            if hbarNeeded:
                barSize = barSize - sbhh

            #!! need to make it recalculate scroll positions
            self.vertScrollBar.SetVisible(True)
            self.vertScrollBar.SetEnabled(False)
            self.vertScrollBar.SetRangeWindow( int(nodesVisible) )
            self.vertScrollBar.SetRange( 0, visibleItemCount)
            self.vertScrollBar.SetButtonPressedScrollValue( 1 )

            if self.scrollbarExternal[ 0 ] == False:
                self.vertScrollBar.SetPos(wide - (sbvw + WINDOW_BORDER_WIDTH), 0)
                self.vertScrollBar.SetSize(sbvw, barSize - 2)

            # need to figure out
            vbarPos = self.vertScrollBar.GetValue()
        else:
            self.vertScrollBar.SetVisible(False)
            self.vertScrollBar.SetValue( 0 )
        
        hbarPos = 0
        if hbarNeeded:
            subPanelHeight = subPanelHeight - (sbhh + 2)
            barSize = wide
            if vbarNeeded:
                barSize = barSize - sbvw
            self.horzScrollBar.SetVisible(True)
            self.horzScrollBar.SetEnabled(False)
            self.horzScrollBar.SetRangeWindow( int(barSize) )
            self.horzScrollBar.SetRange( 0, maxWidth)
            self.horzScrollBar.SetButtonPressedScrollValue( 10 )

            if self.scrollbarExternal[ 1 ] == False:
                self.horzScrollBar.SetPos(0, tall - (sbhh + WINDOW_BORDER_WIDTH))
                self.horzScrollBar.SetSize(barSize - 2, sbhh)
  

            hbarPos = self.horzScrollBar.GetValue()
        else:
            self.horzScrollBar.SetVisible(False)
            self.horzScrollBar.SetValue( 0 )
        
        self.subPanel.SetSize(subPanelWidth, subPanelHeight)

        y = 0
        vbarPos, visibleItemCount, y = self.rootNode.PositionAndSetVisibleNodes(vbarPos, visibleItemCount, -hbarPos, y)
        
        self.Repaint()
        
    def MakeItemVisible(self, itemIndex):
        # first make sure that all parents are expanded
        node = self.nodeList[itemIndex]
        parent = node.GetParentNode()
        while parent:
            if parent.expand == False:
                parent.SetNodeExpanded(True)
            parent = parent.GetParentNode()

        # recalculate scroll bar due to possible exapnsion
        self.PerformLayout()

        if (self.vertScrollBar.IsVisible() == False):
            return

        visibleIndex = node.CountVisibleIndex()-1
        range = self.vertScrollBar.GetRangeWindow()
        vbarPos = self.vertScrollBar.GetValue()

        # do we need to scroll up or down?
        if visibleIndex < vbarPos:
            self.vertScrollBar.SetValue(visibleIndex)
        elif visibleIndex+1 > vbarPos+range:
            self.vertScrollBar.SetValue(visibleIndex+1-range)
        self.InvalidateLayout()
        
    def GetScrollBarSize(self, vertical):
        idx = 1
        if vertical:
            idx = 0

        if self.scrollbarExternal[ idx ]:
            return 0, 0

        if vertical:
            return self.vertScrollBar.GetSize()
        else:
            return self.horzScrollBar.GetSize()
        
    def OnSizeChanged(self, wide, tall):
        super(TreeView, self).OnSizeChanged(wide, tall)
        self.InvalidateLayout()
        self.Repaint()
        
    def ApplySchemeSettings(self, scheme):
        super(TreeView, self).ApplySchemeSettings(scheme)

        self.SetBorder(scheme.GetBorder("ButtonDepressedBorder"))
        self.SetBgColor(self.GetSchemeColor("TreeView.BgColor", self.GetSchemeColor("WindowDisabledBgColor", scheme), scheme))
        self.SetFont( scheme.GetFont( "Default", self.IsProportional() ) )
        self.subPanel.SetBgColor( self.GetBgColor() )

    def SetBgColor(self, color):
        super(TreeView, self).SetBgColor(color)
        self.subPanel.SetBgColor( color )
        
    def OnSliderMoved(self, position):
        self.InvalidateLayout()
        self.Repaint()
        
    def FindItemUnderMouse(self, mx, my ):
        mx = clamp( mx, 0, self.GetWide() - 1 )
        my = clamp( my, 0, self.GetTall() - 1 )
        if mx >= TREE_INDENT_AMOUNT:
            # Find what's under this position
            # need to figure out
            vbarPos = 0
            if self.vertScrollBar.IsVisible():
                vbarPos = m_pVertScrollBar.GetValue()
            hbarPos = 0
            if self.horzScrollBar.IsVisible():
                hbarPos = m_pHorzScrollBar.GetValue()
            count = self.rootNode.CountVisibleNodes()

            y = 0
            item, vbarPos, count, y = self.rootNode.FindItemUnderMouse( vbarPos, count, -hbarPos, y, mx, my );
            if item:
                return item.itemIndex

        return -1
        
    def OnMousePressed(self, code):
        ctrl = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL))
        shift = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT))

        # Try to map mouse position to a row
        if code == ButtonCode_t.MOUSE_LEFT and self.rootNode:
            mx, my = vgui_input().GetCursorPos()
            mx, my = self.ScreenToLocal( mx, my )
            if mx >= TREE_INDENT_AMOUNT:
                # Find what's under this position
                # need to figure out
                vbarPos = 0
                if self.vertScrollBar.IsVisible():
                    vbarPos = self.vertScrollBar.GetValue()
                hbarPos = 0
                if self.horzScrollBar.IsVisible():
                    hbarPos = self.horzScrollBar.GetValue()
                count = self.rootNode.CountVisibleNodes()

                y = 0
                item, vbarPos, count, y = self.rootNode.FindItemUnderMouse( vbarPos, count, -hbarPos, y, mx, my )
                if item:
                    if self.IsItemSelected(item.itemIndex) == False:
                        self.AddSelectedItem( item.itemIndex, ctrl == False and shift == False )
                    return
                else:
                    self.ClearSelection()

        super(TreeView, self).OnMousePressed(code)
        
    def ClearSelection(self):
        self.selectedItems = []
        self.mostRecentlySelectedItem = -1
        self.PostActionSignal( KeyValues( "TreeViewItemSelectionCleared" ) )
        
    def RemoveSelectedItem(self, itemIndex):
        if self.IsItemIndexValid( itemIndex ) == False:
            return

        sel = self.nodeList[ itemIndex ]
        assert( sel )
        try:
            slot = self.selectedItems.index( sel )
            self.selectedItems.remove( sel )
            self.PostActionSignal( KeyValues( "TreeViewItemDeselected", "itemIndex", itemIndex ) )
            self.mostRecentlySelectedItem = itemIndex
        except ValueError:
            pass

    def AddSelectedItem(self, itemIndex, clearCurrentSelection, requestFocus = True, bMakeItemVisible = True):
        if clearCurrentSelection:
            self.ClearSelection()

        
        # Assume it's bogus
        if self.IsItemIndexValid( itemIndex ) == False:
            return

        sel = self.nodeList[ itemIndex ]
        assert( sel )
        if requestFocus:
            sel.RequestFocus()

        # Item 0 is most recently selected!!!
        try:
            slot = self.selectedItems.index( sel )
            self.selectedItems.remove(sel)
            self.selectedItems.insert(0, sel)
        except ValueError:
            self.selectedItems.insert(0, sel)

        if bMakeItemVisible:
            self.MakeItemVisible( itemIndex )

        self.PostActionSignal( KeyValues( "TreeViewItemSelected", "itemIndex", itemIndex ) )
        self.InvalidateLayout()

        if clearCurrentSelection:
            self.mostRecentlySelectedItem = itemIndex

    def GetFirstSelectedItem(self):
        if len(self.selectedItems) <= 0:
            return -1
        return self.selectedItems[ 0 ].itemIndex
        
    def IsItemSelected(self, itemIndex):
        # Assume it's bogus
        if self.IsItemIndexValid( itemIndex ) == False:
            return False

        sel = self.nodeList[ itemIndex ]
        try:
            return self.selectedItems.index( sel ) >= 0
        except ValueError:
            return False
            
    def SetLabelEditingAllowed(self, itemIndex, state):
        if not self.IsItemIndexValid(itemIndex):
            return
            
        self.nodeList[itemIndex].labelEditingAllowed = state
            
    # To be overridden
    def GenerateChildrenOfNode(self, itemIndex):
        pass
        
    def GenerateContextMenu(self, itemIndex, x, y ):
        pass

        
