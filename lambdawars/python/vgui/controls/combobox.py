""" Python version of the vgui controls element 'ComboBox' """
from srcbase import KeyValues, Color
from vgui import DataType_t, surface, CursorCode
from vgui.controls import Button, TextEntry, Label
from .menu import Menu
from input import ButtonCode_t

class ComboBoxButton(Button):
    def __init__(self, parent, panelname, text):
        super(ComboBoxButton, self).__init__(parent, panelname, text)
        self.SetButtonActivationType( self.ACTIVATE_ONPRESSED )

    def GetButtonBgColor(self):
        if self.IsEnabled():
            return super(ComboBoxButton, self).GetButtonBgColor()
        return self.disabledbgcolor
        
    def ApplySchemeSettings(self, schemeobj):
        super(ComboBoxButton, self).ApplySchemeSettings(schemeobj)
        
        self.SetFont(schemeobj.GetFont("Marlett", self.IsProportional()))
        self.SetContentAlignment(Label.a_west)
        self.SetTextInset(3, 0)
        self.SetDefaultBorder(schemeobj.GetBorder("ScrollBarButtonBorder"))
        
        # arrow changes color but the background doesnt.
        self.SetDefaultColor(self.GetSchemeColor("ComboBoxButton.ArrowColor", schemeobj), self.GetSchemeColor("ComboBoxButton.BgColor", schemeobj))
        self.SetArmedColor(self.GetSchemeColor("ComboBoxButton.ArmedArrowColor", schemeobj), self.GetSchemeColor("ComboBoxButton.BgColor", schemeobj))
        self.SetDepressedColor(self.GetSchemeColor("ComboBoxButton.ArmedArrowColor", schemeobj), self.GetSchemeColor("ComboBoxButton.BgColor", schemeobj))
        self.disabledbgcolor = self.GetSchemeColor("ComboBoxButton.DisabledBgColor", schemeobj)

    def GetBorder(self, depressed, armed, selected, keyfocus):
        return None

    def OnCursorExited(self):
        """ Dim the arrow on the button when exiting the box
                    only if the menu is closed, so let the parent handle self. """
        # want the arrow to go grey when we exit the box if the menu is not open
        self.CallParentFunction(KeyValues("CursorExited"))
    
    # Default vars
    disabledbgcolor = Color()
        
class ComboBox(TextEntry):
    def __init__(self, parent, panelName, numLines, allowEdit):
        super(ComboBox, self).__init__(parent, panelName)
        
        self.RegMessageMethod( "ActivateItem", self.ActivateItem, 1, "itemID", DataType_t.DATATYPE_INT )
        self.RegMessageMethod( "MenuClose", self.OnMenuClose, 0 )
        self.RegMessageMethod( "MenuItemSelected", self.OnMenuItemSelected, 0 )
        self.RegMessageMethod( "SetText", self.OnSetText, 1, "text", DataType_t.DATATYPE_CONSTCHARPTR  )
        
        self.SetEditable(allowEdit)
        self.SetHorizontalScrolling(False)  # do not scroll, always Start at the beginning of the text.

        # create the drop-down menu
        self.dropdown = Menu(self, None)
        self.dropdown.AddActionSignalTarget(self)

        # button to Activate menu
        self.button = ComboBoxButton(self, None, "u")
        self.button.SetCommand("ButtonClicked")
        self.button.AddActionSignalTarget(self)

        self.SetNumberOfEditLines(numLines)

        self.highlight = False
        self.direction = Menu.DOWN
        self.openoffsetY = 0
        
    # functions designed to be overriden
    def OnShowMenu(self, menu):
        pass
    def OnHideMenu(self, menu):
        pass

    def SetNumberOfEditLines(self, numLines):   
        """ Set the number of items in the dropdown menu. """
        self.dropdown.SetNumberOfVisibleItems( numLines )
        
    def AddItem(self, itemText, userData):
        """ Add an item to the drop down
            Input  : itemText - name of dropdown menu item """
        # when the menu item is selected it will send the custom message "SetText"
        return self.dropdown.AddMenuItem( itemText, itemText, KeyValues("SetText", "text", itemText), self, userData )

    def DeleteItem(self, itemID):
        """ Removes a single item """
        if not self.dropdown.IsValidMenuID(itemID):
            return

        self.dropdown.DeleteItem( itemID )

    def UpdateItem(self, itemID, itemText, userData):
        """ Updates a current item to the drop down
            Input  : itemText - name of dropdown menu item """
        if not self.dropdown.IsValidMenuID(itemID):
            return False

        # when the menu item is selected it will send the custom message "SetText"
        self.dropdown.UpdateMenuItem(itemID, itemText, KeyValues("SetText", "text", itemText), userData)
        self.InvalidateLayout()
        return True

    def IsItemIDValid(self, itemID):
        """ Updates a current item to the drop down
            Input  : itemText - name of dropdown menu item """
        return self.dropdown.IsValidMenuID(itemID)

    def SetItemEnabled(self, itemText, state):
        self.dropdown.SetItemEnabled(itemText, state)
        
    def SetItemEnabled(self, itemID, state):
        self.dropdown.SetItemEnabled(itemID, state)

    def RemoveAll(self):
        """ Remove all items from the drop down menu """
        self.dropdown.DeleteAllItems()

    def GetItemCount(self):
        return self.dropdown.GetItemCount()

    def GetItemIDFromRow(self, row):
        # valid from [0, GetItemCount)
        return self.dropdown.GetMenuID( row )

    def ActivateItem(self, itemID):
        """ Activate the item in the menu list, as if that menu item had been selected by the user
            Input  : itemID - itemID from AddItem in list of dropdown items """
        self.dropdown.ActivateItem(itemID)

    def ActivateItemByRow(self, row):
        """ Activate the item in the menu list, as if that menu item had been selected by the user
            Input  : itemID - itemID from AddItem in list of dropdown items """
        self.dropdown.ActivateItemByRow(row)

    def SetMenu(self, menu):
        """ Allows a custom menu to be used with the combo box """
        self.dropdown = menu
        if self.dropdown:
            self.dropdown.SetParent( self )
            
    def GetMenu(self):
        return self.dropdown

    def PerformLayout(self):
        """ Layout the format of the combo box for drawing on screen """
        wide, tall = self.GetPaintSize()

        super(ComboBox, self).PerformLayout()

        buttonFont = self.button.GetFont()
        fontTall = surface().GetFontTall( buttonFont )

        buttonSize = min( tall, fontTall )

        buttonY = int( ( ( tall - 1 ) - buttonSize ) / 2 )

        self.button.SetBounds( wide - buttonSize - 4, buttonY, buttonSize, buttonSize )
        if self.IsEditable():
            self.SetCursor(CursorCode.dc_ibeam)
        else:
            self.SetCursor(CursorCode.dc_arrow)

        self.button.SetEnabled(self.IsEnabled())

        self.DoMenuLayout()
 
    def DoMenuLayout(self):
        self.dropdown.PositionRelativeToPanel( self, self.direction, self.openoffsetY )

        # reset the width of the drop down menu to be the width of the combo box
        self.dropdown.SetFixedWidth(self.GetWide())
        self.dropdown.ForceCalculateWidth()

    def SortItems(self):
        """ Sorts the items in the list """
        pass
        
    def GetActiveItem(self):
        """ return the index of the last selected item """
        return self.dropdown.GetActiveItem()

    def GetActiveItemUserData(self):
        return self.dropdown.GetItemUserData(self.GetActiveItem())

    def GetItemUserData(self, itemID):
        return self.dropdown.GetItemUserData(itemID)

    def GetItemText(self, itemID):
        """ data accessor """
        return self.dropdown.GetItemText(itemID)

    def IsDropdownVisible(self):
        return self.dropdown.IsVisible()

    def ApplySchemeSettings(self, schemeobj):
        super(ComboBox, self).ApplySchemeSettings(schemeobj)

        self.SetBorder(schemeobj.GetBorder("ComboBoxBorder"))

    def SetDropdownButtonVisible(self, state):
        """ Set the visiblity of the drop down menu button. """
        self.button.SetVisible(state)

    def OnMousePressed(self, code):
        """ overloads TextEntry MousePressed """
        if self.dropdown == None:
            return

        if not self.IsEnabled():
            return

        # make sure it's getting pressed over us (it may not be due to mouse capture)
        if not self.IsCursorOver():
            self.HideMenu()
            return

        if self.IsEditable():
            super(ComboBox, self).OnMousePressed(code)
            self.HideMenu()
        else:
            # clicking on a non-editable text box just activates the drop down menu
            self.RequestFocus()
            self.DoClick()
            
    def OnMouseDoublePressed(self, code):
        """ Double-click acts the same as a single-click """
        if self.IsEditable():
            super(ComboBox, self).OnMouseDoublePressed(code)
        else:
            self.OnMousePressed(code)
            
    def OnCommand(self, command):
        """ Called when a command is received from the menu
                Changes the label text to be that of the command """
        if command == "ButtonClicked":
            # hide / show the menu underneath
            self.DoClick()

        #super(ComboBox, self).OnCommand(command)

    def OnSetText(self, newtext):
        # see if the combobox text has changed, and if so, post a message detailing the new text
        text = newtext

        # check if the new text is a localized string, if so undo it
        # TODO: Expose the localize thingy to python
        # if text[0] == '#':
            # cbuf = g_pVGuiLocalize.ConvertUnicodeToANSI(text)

            # # try lookup in localization tables
            # unlocalizedTextSymbol = g_pVGuiLocalize.FindIndex(cbuf + 1)
            
            # if unlocalizedTextSymbol != INVALID_STRING_INDEX:
                # # we have a new text value
                # text = g_pVGuiLocalize.GetValueByIndex(unlocalizedTextSymbol)

        wbuf = self.GetText()
        
        if wbuf != text:
            # text has changed
            self.SetText(text)

            # fire off that things have changed
            kv = KeyValues("TextChanged", "text", text )
            kv.SetInt("vpanel", self.GetVPanel())
            self.PostActionSignal(kv)
            self.Repaint()

        # close the box
        self.HideMenu()

    def HideMenu(self):
        """ hides the menu """
        if not self.dropdown:
            return

        # hide the menu
        self.dropdown.SetVisible(False)
        self.Repaint()
        self.OnHideMenu(self.dropdown)

    def ShowMenu(self):
        """ shows the menu """
        if not self.dropdown:
            return

        # hide the menu
        self.dropdown.SetVisible(False)
        self.DoClick()

    def OnKillFocus(self):
        """ Called when the window loses focus hides the menu """
        self.SelectNoText()

    def OnMenuClose(self):
        """ Called when the menu is closed """
        self.HideMenu()

        if self.HasFocus():
            self.SelectAllText(False)
        elif self.highlight:
            self.highlight = False
            # we want the text to be highlighted when we request the focus
    #       SelectAllOnFirstFocus(True)
            self.RequestFocus()
        # if cursor is in self box or the arrow box
        elif self.IsCursorOver(): # make sure it's getting pressed over us (it may not be due to mouse capture)
            self.SelectAllText(False)
            self.OnCursorEntered()
            # Get focus so the box will unhighlight if we click somewhere else.
            self.RequestFocus()
        else:
            self.button.SetArmed(False)

    def DoClick(self):
        """ Handles hotkey accesses
            FIXME: make self open different directions as necessary see menubutton. """
        # menu is already visible, hide the menu
        if self.dropdown.IsVisible():
            self.HideMenu()
            return

        # do nothing if menu is not enabled
        if not self.dropdown.IsEnabled():
            return
            
        # force the menu to Think
        self.dropdown.PerformLayout()

        # make sure we're at the top of the draw order (and therefore our children as well)
        # self.RequestFocus()
        
        # We want the item that is shown in the combo box to show as selected
        itemToSelect = -1
        comboBoxContents = self.GetText()
        for i in range(0, self.dropdown.GetItemCount()):
            menuID = self.dropdown.GetMenuID(i)
            menuItemName = self.dropdown.GetMenuItem(menuID).GetText()
            if menuItemName == comboBoxContents:
                itemToSelect = i
                break

        # if we found a match, highlight it on opening the menu
        if itemToSelect >= 0:
            self.dropdown.SetCurrentlyHighlightedItem( self.dropdown.GetMenuID(itemToSelect) )

        # reset the dropdown's position
        self.DoMenuLayout()


        # make sure we're at the top of the draw order (and therefore our children as well)
        # self important to make sure the menu will be drawn in the foreground
        self.MoveToFront()

        # notify
        self.OnShowMenu(self.dropdown)

        # show the menu
        self.dropdown.SetVisible(True)

        # bring to focus
        self.dropdown.RequestFocus()

        # no text is highlighted when the menu is opened
        self.SelectNoText()

        # highlight the arrow while menu is open
        self.button.SetArmed(True)

        self.Repaint()

    def OnCursorEntered(self):
        """ Brighten the arrow on the button when entering the box """
        # want the arrow to go white when we enter the box 
        self.button.OnCursorEntered()
        TextEntry.OnCursorEntered(self)

    def OnCursorExited(self):
        """ Dim the arrow on the button when exiting the box """
        # want the arrow to go grey when we exit the box if the menu is not open
        if not self.dropdown.IsVisible():
            self.button.SetArmed(False)
            TextEntry.OnCursorExited(self)

    def OnMenuItemSelected(self):
        self.highlight = True
        # For editable cbs, fill in the text field from whatever is chosen from the dropdown...
        if self.allowedit:
            idx = self.GetActiveItem()
            if idx >= 0:
                name = self.GetItemText(idx)

                self.OnSetText( name )

        self.Repaint()

    def OnSizeChanged(self, wide, tall):
        super(ComboBox, self).OnSizeChanged( wide, tall)

        # set the drawwidth. 
        self.PerformLayout()
        bwide, btall = self.button.GetSize()
        self.SetDrawWidth( wide - bwide )

    def OnSetFocus(self):
        super(ComboBox, self).OnSetFocus()

        self.GotoTextEnd()
        self.SelectAllText(False)

    def OnKeyCodeTyped(self, code):
        """ Handles up/down arrows """
        if code == ButtonCode_t.KEY_UP:
            self.MoveAlongMenuItemList(-1)
        elif code == ButtonCode_t.KEY_DOWN:
            self.MoveAlongMenuItemList(1)
        else:
            super(ComboBox, self).OnKeyCodeTyped(code)

    # Temporary disabled
    # def OnKeyTyped(self, unichar):
        # """ handles key input """
        # if self.IsEditable(): # don't play with key presses in edit mode
            # super(ComboBox, self).OnKeyTyped( unichar )
            # return

        # itemToSelect = self.dropdown.GetActiveItem()
        # if itemToSelect < 0:
            # itemToSelect = 0

        # i = itemToSelect + 1
        # if i >= self.dropdown.GetItemCount():
            # i = 0

        # while i != itemToSelect:
            # menuID = self.dropdown.GetMenuID(i)
            # menuItemName = self.dropdown.GetMenuItem(menuID).GetText()

            # if menuItemName[0] == unichar:
                # itemToSelect = i
                # break			

            # i += 1
            # if i >= self.dropdown.GetItemCount():
                # i = 0

        # if itemToSelect >= 0 and itemToSelect < self.dropdown.GetItemCount():
            # menuID = self.dropdown.GetMenuID(itemToSelect)
            # menuItemName = self.dropdown.GetMenuItem(menuID).GetText()
            # self.OnSetText(menuItemName)
            # self.SelectAllText(False)
            # self.dropdown.ActivateItem(itemToSelect)
        # else:
            # super(ComboBox, self).OnKeyTyped( unichar )

    def MoveAlongMenuItemList(self, direction):
        # We want the item that is shown in the combo box to show as selected
        itemToSelect = -1
        
        comboBoxContents = self.GetText()
        for i in range(0, self.dropdown.GetItemCount()):
            menuID = self.dropdown.GetMenuID(i)
            menuItemName = self.dropdown.GetMenuItem(menuID).GetText()

            if menuItemName == comboBoxContents:
                itemToSelect = i
                break
  
        # if we found self item, then we scroll up or down
        if itemToSelect >= 0:
            newItem = itemToSelect + direction
            if newItem < 0:
                newItem = 0
            elif newItem >= self.dropdown.GetItemCount():
                newItem = self.dropdown.GetItemCount() - 1

            menuID = self.dropdown.GetMenuID(newItem)
            menuItemName = self.dropdown.GetMenuItem(menuID).GetText()
            self.OnSetText(menuItemName)
            self.SelectAllText(False)
            self.dropdown.ActivateItem(newItem)
            
    def SetOpenDirection(self, direction):  
        """ Sets the direction from the menu button the menu should open """
        self.direction = direction

    def SetFont(self, font):
        super(ComboBox, self).SetFont(font)

        self.dropdown.SetFont(font)

    def SetUseFallbackFont(self,  bState, hFallback):
        super(ComboBox, self).SetUseFallbackFont( bState, hFallback )
        self.dropdown.SetUseFallbackFont( bState, hFallback )
        
    # Settings
    allowedit = False

