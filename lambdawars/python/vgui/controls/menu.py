""" 
Python version of Menu 

A menu is a list of items that can be selected with one click, navigated
			with arrow keys and/or hot keys, and have a lit behavior when mouse over.
			It is NOT the button which opens the menu, but only the menu itself.

 Behaviour spec:
 Menu navigation can be done in 2 modes, via keyboard keys and via mouse.
 Clicking on menu button opens menu.
 Only one item in a menu is highlighted at a time.
 Only one submenu in a menu is open at a time.
 Disabled menuitems get highlighted via mouse and keys but will not activate.

 Mouse:
   Moving mouse into a menuitem highlights it.
   If the menuitem has a cascading menu, the menu opens when the mouse enters
    the menuitem. The cascading menuitem stays highlighted while its menu is open.
   No submenu items are highlighted by default.
   Moving the mouse into another menuitem closes any previously open submenus in the list.
   Clicking once in the menu item activates the menu item and closes all menus.
   Moving the mouse off a menuitem unhighlights it.
   The scroll bar arrows can be used to move up/down the menu one item at a time.
   The clicking and dragging on the scroll bar nob also scrolls the menu items.
   If a highlighed menuitem scrolls off, and the user then begins navigating via keys,
    the menu will snap the scroll bar so the highlighted item is visible.
   If user has been navigating via keys, moving the mouse over a menu item 
    highlights it.
 Mousewheel:
   You must have the mouse inside the menu/scroll bar to use the wheel.
   The mouse wheel moves the highlighted menuitem up or down the list.
   If the list has no scroll bar the wheel will cycle from the bottom of the list
    to the top of the list and vice versa.
   If the list has a scrollbar the mouse wheel will stop at the top or bottom
    of the list. 
   If the mouse is over the scroll bar no items are highlighted.
 Keyboard:
   When a menu is opened, no items are highlighted.
   If a menuitem has a cascading menu it does not open when the item is highlighted.
   The down arrow selects the next item in the list. 
    (first item if none are highlighted and there is a scrollbar).
   The up arrow selects the previous item in the list 
    (first item if none are highlighted and there is a scrollbar, last item if none are
    highlighted and there is no scrollbar).
   Selecting a new menuitem closes any previously open submenus in the list.
   The enter key activates the selected item and closes all menus.
   If the selected item has a cascading menu, activating it opens its submenu.
   These may also be activated by pressing the right arrow.
   Pressing the left arrow closes the submenu.
   When the submenu is opened the cascading menuitem stays highlighted.
   No items in the submenu are highlighted when it is opened.
   
   Note: Cascading menuitems in menus with a scrollbar is not supported.
         Its a clunky UI and if we want this we should design a better solution,
         perhaps along the lines of how explorer's bookmarks does it.
         It currently functions, but there are some arm/disarm bugs.
"""

from srcbase import KeyValues, Color
from vgui import scheme, ipanel, surface, vgui_input, DataType_t, INVALID_FONT
from vgui.controls import Panel, Label, ScrollBar
from input import ButtonCode_t

from .menuitem import MenuItem

class MenuManager(object):
    def __init__(self):
        super(MenuManager, self).__init__()
        self.menus = []
        
    def AddMenu(self, m):
        if m == None:
            return

        for item in self.menus:
            if item == m:
                return

        self.menus.append( m )

    def RemoveMenu(self, m):
        if m == None:
            return
            
        try:
            self.menus.remove(m)
        except ValueError:
            pass

    def OnInternalMousePressed(self, other, code):
        c = len(self.menus)
        if c == 0:
            return

        x, y = vgui_input().GetCursorPos()

        mouseInsideMenuRelatedPanel = False

        for i in range(c-1, -1, -1):
            m = self.menus[i]
            if m == None:
                del self.menus[i]
                continue

            # See if the mouse is within a menu
            if self.IsWithinMenuOrRelative( m, x, y ):
                mouseInsideMenuRelatedPanel = True
                
        if mouseInsideMenuRelatedPanel:
            return

        self.AbortMenus()

    def AbortMenus(self):
        # Close all of the menus
        c = len(self.menus)
        for i in range(c-1, -1, -1):
            m = self.menus[i]
            if m == None:
                continue

            del self.menus[i]

            # Force it to close
            m.SetVisible( False )

        self.menus = []
        
    def IsWithinMenuOrRelative(self, panel, x, y):
        topMost = panel.IsWithinTraverse( x, y, True )
        if topMost:
            # It's over the menu
            if topMost == panel.GetVPanel():
                return True
                
            # It's over something which is parented to the menu (i.e., a menu item)
            if ipanel().HasParent( topMost, panel.GetVPanel() ):
                return True

        if panel.GetParent():
            parent = panel.GetParent()

            topMost = parent.IsWithinTraverse( x, y, True )

            if topMost:
                if topMost == parent.GetVPanel():
                    return True

        return False

class MenuSeparator(Panel):
    """ divider line in a menu """
    def __init__(self, parent, panelName):
        super(MenuSeparator, self).__init__( parent, panelName )
        self.SetPaintEnabled( True )
        self.SetPaintBackgroundEnabled( True )
        self.SetPaintBorderEnabled( False )

    def Paint(self):
  
        w, h = self.GetSize()

        surface().DrawSetColor( self.GetFgColor() )
        surface().DrawFilledRect( 4, 1, w-1, 2 )

    def ApplySchemeSettings(self, schemeobj):
        super(MenuSeparator, self).ApplySchemeSettings( schemeobj )

        self.SetFgColor( schemeobj.GetColor( "Menu.SeparatorColor", Color( 142, 142, 142, 255 ) ) )
        self.SetBgColor( schemeobj.GetColor( "Menu.BgColor", Color( 0, 0, 0, 255 ) ) )
        
class Menu(Panel):
    def __init__(self, parent, panelName):
        super(Menu, self).__init__(parent, panelName)
        
        self.RegMessageMethod( "MenuItemSelected", self.OnMenuItemSelected, 1, "panel", DataType_t.DATATYPE_INT )
        self.RegMessageMethod( "ScrollBarSliderMoved", self.OnSliderMoved, 0 )
        
        self.menuitems = []

        self.visiblesorteditems = []
        self.sorteditems = []		# used for visual 
        self.separators = []        # menu item ids after  which separators should be shown
        self.separatorpanels = [] 
        
        self.aligment = Label.a_west
        self.fixedwidth = 0
        self.minimumwidth = 0
        self.numvisiblelines = -1 # No limit
        self.currentlyselecteditemid = -1
        self.scroller = ScrollBar(self, "MenuScrollBar", True)
        self.scroller.SetVisible(False)
        self.scroller.AddActionSignalTarget(self)
        self._sizedforscrollbar = False
        self.SetZPos(1)
        self.SetVisible(False)
        self.MakePopup(False)
        self.SetParent(parent)
        self._recalculatewidth = True
        self.inputmode = self.MOUSE
        self.checkimagewidth = 0
        self.activateditem = 0

        self.usefallbackfont = False
        self.fallbackitemfont = INVALID_FONT

        if self.IsProportional():
            self.menuitemheight =  scheme().GetProportionalScaledValueEx( self.GetScheme(), self.DEFAULT_MENU_ITEM_HEIGHT )
        else:
            self.menuitemheight =  self.DEFAULT_MENU_ITEM_HEIGHT
        self.itemfont = INVALID_FONT

    def DeleteAllItems(self):
        """ Remove all menu items from the menu. """
        for mi in self.menuitems:
            mi.DeletePanel()
        self.menuitems = []

        self.sorteditems = []
        self.visiblesorteditems = []
        self.separators = []
        self.separatorpanels = []
        self.InvalidateLayout()
        
    def AddMenuItemIntern(self, item):
        item.SetParent( self )
        self.menuitems.append( item )
        itemID = len(self.menuitems)-1
        self.sorteditems.append(itemID)
        self.InvalidateLayout(False)
        self._recalculatewidth = True
        item.SetContentAlignment( self.aligment )
        if INVALID_FONT != self.itemfont:
            item.SetFont( self.itemfont )
        if self.usefallbackfont and INVALID_FONT != self.fallbackitemfont:
            l = item
            ti = l.GetTextImage()
            if ti:
                ti.SetUseFallbackFont( self.usefallbackfont, self.fallbackitemfont )
        return itemID       

    def AddMenuItem(self, itemname, itemtext, command, target, userdata=None, cascademenu = None, checkable=False):
        """ All in one replacement for the 1000 AddMenuItem functions of the C++ version """
        if itemname == None:
            itemname = itemtext
        if command == None:
            command = itemtext
        item = MenuItem(self, itemname, itemtext, cascademenu, checkable )
        item.SetCommand(command)
        item.AddActionSignalTarget(target)
        item.SetUserData(userdata)

        return self.AddMenuItemIntern(item)

    def DeleteItem(self, itemID):
        """ Remove a single item """
        # FIXME: self doesn't work with separator panels yet
        assert( len(self.separatorpanels) == 0 )

        del self.menuitems[itemID]

        self.sorteditems.remove( itemID )
        self.visiblesorteditems.remove( itemID )

        self.InvalidateLayout(False)
        self._recalculatewidth = True  

    def AddCheckableMenuItem(self, itemName, itemText, command, target, userData=None ):
        """ Add a checkable menu item to the menu. """
        return self.AddMenuItem(itemName, itemText, command, target, userData, None, True)

    def AddCascadingMenuItem( itemName, itemText, command, target, cascadeMenu , userData = None ):
        """ Add a Cascading menu item to the menu. """
        return self.AddMenuItem(itemName, itemText, command, target, userData, cascadeMenu)

    def UpdateMenuItem(self, itemID, itemText, message, userData=None):
        """ Sets the values of a menu item at the specified index
            Input  : index - the index of self item entry
            message - pointer to the message to send when the item is selected """
        try:
            menuItem = self.menuitems[itemID]
            # make sure its enabled since disabled items get highlighted.
            if menuItem:
                menuItem.SetText(itemText)
                menuItem.SetCommand(message)
                if userData:
                    menuItem.SetUserData(userData)
        except IndexError:
            assert(0)
        self._recalculatewidth = True

    def SetContentAlignment(self, alignment):
        """ Sets the content alignment of all items in the menu """
        if self.aligment != alignment:
            self.aligment = alignment

            # Change the alignment of existing menu items
            for item in self.menuitems:
                item.SetContentAlignment( alignment )

    def SetFixedWidth(self, width):
        """ Locks down a specific width """
        # the padding makes it so the menu has the label padding on each side of the menu.
        # makes the menu items look centered.
        self.fixedwidth = width
        self.InvalidateLayout(False)

    def SetMenuItemHeight(self, itemHeight):
        """ sets the height of each menu item """
        self.menuitemheight = itemHeight

    def GetMenuItemHeight(self):
        return self.menuitemheight

    def CountVisibleItems(self):
        count = 0
        for item in self.sorteditems:
            if self.menuitems[ item ].IsVisible():
                count += 1
        return count

    def ComputeWorkspaceSize(self):
        # make sure we factor in insets
        ileft, iright, itop, ibottom = self.GetInset()

        workX, workY, workWide, workTall = surface().GetWorkspaceBounds()
        workTall -= 20
        workTall -= itop
        workTall -= ibottom
        return workWide, workTall

    def PositionRelativeToPanel(self, relative, direction, nAdditionalYOffset =0, showMenu = False ):
        """ Assumes relative coords in screenspace """
        assert( relative )
        rx, ry, rw, rh = relative.GetBounds()
        rx, ry = relative.LocalToScreen(rx, ry)

        if direction == self.CURSOR:
            # force the menu to appear where the mouse button was pressed
            rx, ry = vgui_input().GetCursorPos()
            rw = rh = 0
        elif ( direction == self.ALIGN_WITH_PARENT and relative.GetVParent() ):
           rx = 0
           ry = 0
           rx, ry = relative.ParentLocalToScreen(rx, ry)
           rx -= 1 # take border into account
           ry += rh + nAdditionalYOffset
           rw = rh = 0
        else:
            rx = 0
            ry = 0
            rx, ry = relative.LocalToScreen(rx, ry)

        workWide, workTall = self.ComputeWorkspaceSize()

        # Final pos
        x = 0
        y = 0

        mWide, mTall = self.GetSize()

        if direction == Menu.UP: # Menu prefers to open upward
            x = rx
            topOfReference = ry
            y = topOfReference - mTall
            if y < 0:
                bottomOfReference = ry + rh + 1
                remainingPixels = workTall - bottomOfReference

                # Can't fit on bottom, either, move to side
                if mTall >= remainingPixels:
                    y = workTall - mTall
                    x = rx + rw
                    # Try and place it to the left of the button
                    if x + mWide > workWide:
                        x = rx - mWide
                else:
                    # Room at bottom
                    y = bottomOfReference
            # Everyone else aligns downward...
        else: # == Menu.LEFT or Menu.RIGHT or Menu.DOWN:
            x = rx
            bottomOfReference = ry + rh + 1
            y = bottomOfReference
            if bottomOfReference + mTall >= workTall:
                # See if there's run straight above
                if mTall >= ry: # No room, try and push menu to right or left
                    y = workTall - mTall
                    x = rx + rw
                    # Try and place it to the left of the button
                    if x + mWide > workWide:
                        x = rx - mWide
                else:
                    # Room at top
                    y = ry - mTall
                        
        # Check left rightness
        if x + mWide > workWide:
            x = workWide - mWide
            assert( x >= 0 ) # yikes!!!
        elif x < 0:
            x = 0

        self.SetPos(x, y)
        if showMenu:
            self.SetVisible( True )

    def ComputeFullMenuHeightWithInsets(self):
        # make sure we factor in insets
        ileft, iright, itop, ibottom = self.GetInset()

        separatorHeight = 3

        # add up the size of all the child panels
        # move the child panels to the correct place in the menu
        totalTall = itop + ibottom
        for itemId in self.sorteditems: # use sortedItems instead of MenuItems due to SetPos()
            child = self.menuitems[ itemId ]
            assert( child )
            if child == None:
                continue
            # These should all be visible at self point
            if not child.IsVisible():
                continue

            totalTall += self.menuitemheight

            # Add a separator if needed...
            try:
                sepIndex = self.separators.index( itemId )
                totalTall += separatorHeight
            except ValueError:
                pass
        return totalTall
        
    def PerformLayout(self):
        """ Reformat according to the new layout """
        parent = self.GetParentMenuItem() 
        cascading =  parent != None

        # make sure we factor in insets
        ileft, iright, itop, ibottom = self.GetInset()

        workWide, workTall = self.ComputeWorkspaceSize()

        fullHeightWouldRequire = self.ComputeFullMenuHeightWithInsets()

        bNeedScrollbar = fullHeightWouldRequire >= workTall 

        maxVisibleItems = self.CountVisibleItems()

        if ( self.numvisiblelines > 0 and 
             maxVisibleItems > self.numvisiblelines ):
            bNeedScrollbar = True
            maxVisibleItems = self.numvisiblelines

        # if we have a scroll bar
        if bNeedScrollbar:
            # add it to the display
            self.AddScrollBar()

            # self fills in self.visiblesorteditems as needed
            self.MakeItemsVisibleInScrollRange( self.numvisiblelines, min( fullHeightWouldRequire, workTall ) )
        else:
            self.RemoveScrollBar()
            # Make everything visible
            self.visiblesorteditems = []
            for itemID in self.sorteditems:
                child = self.menuitems[ itemID ]
                if child == None or child.IsVisible() == False:
                    continue

                self.visiblesorteditems.append( itemID )

            # Hide the separators, the needed ones will be readded below
            for seppanel in self.separatorpanels:
                if seppanel:
                    seppanel.SetVisible( False )
        
        # get the appropriate menu border
        self.LayoutMenuBorder()

        TrueW = self.GetWide()
        if bNeedScrollbar:
            TrueW -= self.scroller.GetWide()
        separatorHeight = self.MENU_SEPARATOR_HEIGHT

        # add up the size of all the child panels
        # move the child panels to the correct place in the menu
        menuTall = 0
        totalTall = itop + ibottom
        for itemId in self.visiblesorteditems:  # use sortedItems instead of MenuItems due to SetPos()
            child = self.menuitems[ itemId ]
            assert( child )
            if child == None:
                continue
            # These should all be visible at self point
            if not child.IsVisible():
                continue

            if totalTall >= workTall:
                break

            if INVALID_FONT != self.itemfont:
                child.SetFont( self.itemfont )

            # take into account inset
            child.SetPos (0, menuTall)
            child.SetTall( self.menuitemheight ) # Width is set in a second pass
            menuTall += self.menuitemheight
            totalTall += self.menuitemheight

            # self will make all the menuitems line up in a column with space for the checks to the left.
            if ( not child.IsCheckable() ) and ( self.checkimagewidth > 0 ):
                # Non checkable items have to move over
                child.SetTextInset( self.checkimagewidth, 0 )
            elif child.IsCheckable():
                child.SetTextInset(0, 0) #TODO: for some reason I can't comment self out.

            # Add a separator if needed...
            try:
                sepIndex = self.separators.index( itemId )
                sep = self.separatorpanels[ sepIndex ]
                assert( sep )
                sep.SetVisible( True )
                sep.SetBounds( 0, menuTall, TrueW, separatorHeight )
                menuTall += separatorHeight
                totalTall += separatorHeight  
            except ValueError:
                pass
        
        if not self.fixedwidth:
            self._recalculatewidth = True
            self.CalculateWidth()
        elif self.fixedwidth:
            self._menuWide = self.fixedwidth
            # fixed width menus include the scroll bar in their width.
            if self._sizedforscrollbar:
                self._menuWide -= self.scroller.GetWide()
        
        self.SizeMenuItems()
        
        extraWidth = 0
        if self._sizedforscrollbar:
            extraWidth = self.scroller.GetWide()

        mwide = self._menuWide + extraWidth
        if mwide > workWide:
            mwide = workWide
        mtall = menuTall + itop + ibottom
        if mtall > workTall:
            # Shouldn't happen
            mtall = workTall

        # set the new size of the menu
        self.SetSize( mwide, mtall )
        
        # move the menu to the correct position if it is a cascading menu.
        if cascading:
            # move the menu to the correct position if it is a cascading menu.
            self.PositionCascadingMenu()
            
        # set up scroll bar as appropriate
        if self.scroller.IsVisible():
            self.LayoutScrollBar()
        
        for item in self.menuitems:
            item.InvalidateLayout() # cause each menu item to redo its apply settings now we have sized ourselves

        self.Repaint()

    def ForceCalculateWidth(self):
        """ Force the menu to work out how wide it should be """
        self._recalculatewidth = True
        self.CalculateWidth()
        self.PerformLayout()

    def CalculateWidth(self):
        """ Figure out how wide the menu should be if the menu is not fixed width """
        if not self._recalculatewidth:
            return

        self._menuWide = 0
        if not self.fixedwidth:
            # find the biggest menu item
            for item in self.menuitems:
                wide, tall = item.GetContentSize()
                if wide > self._menuWide - Label.Content:
                    self._menuWide =  wide + Label.Content	
        
        # enfoce a minimumWidth 
        if self._menuWide < self.minimumwidth:
            self._menuWide = self.minimumwidth

        self._recalculatewidth = False

    def LayoutScrollBar(self):
        """ Set up the scroll bar attributes,size and location. """
        #!! need to make it recalculate scroll positions
        self.scroller.SetEnabled(False)
        self.scroller.SetRangeWindow( len(self.visiblesorteditems))
        self.scroller.SetRange( 0, self.CountVisibleItems() )	
        self.scroller.SetButtonPressedScrollValue( 1 )

        wide, tall = self.GetSize ()

        # make sure we factor in insets
        ileft, iright, itop, ibottom = self.GetInset()

        # with a scroll bar we take off the inset
        wide -= iright

        self.scroller.SetPos(wide - self.scroller.GetWide(), 1)
        
        # scrollbar is inside the menu's borders.
        self.scroller.SetSize(self.scroller.GetWide(), tall - ibottom - itop)

    def PositionCascadingMenu(self):
        """ Figure out where to open menu if it is a cascading menu """
        assert(self.GetVParent())
        # move the menu to the correct place below the menuItem
        parentWide, parentTall = ipanel().GetSize(self.GetVParent())
        parentX, parentY = ipanel().GetPos(self.GetVParent())
        
        parentX += parentWide
        parentY = 0

        parentX, parentY = self.ParentLocalToScreen(parentX, parentY)

        self.SetPos(parentX, parentY)
        
        # for cascading menus, 
        # make sure we're on the screen
        x, y, wide, tall = self.GetBounds()
        workX, workY, workWide, workTall = surface().GetWorkspaceBounds()
        
        if x + wide > workX + workWide:
            # we're off the right, move the menu to the left side
            # orignalX - width of the parentmenuitem - width of self menu.
            # add 2 pixels to offset one pixel onto the parent menu.
            x -= (parentWide + wide)
            x -= 2
        else:
            # alignment move it in the amount of the insets.
            x += 1

        if y + tall > workY + workTall:
            lastWorkY = workY + workTall
            pixelsOffBottom = ( y + tall ) - lastWorkY

            y -= pixelsOffBottom
            y -= 2
        else:
            y -= 1
            
        self.SetPos(x, y)
        
        self.MoveToFront()

    def SizeMenuItems(self):
        """ Size the menu items so they are the width of the menu.
            Also size the menu items with cascading menus so the arrow fits in there. """
        ileft, iright, itop, ibottom = self.GetInset()
        
        # assign the sizes of all the menu item panels
        for child in self.menuitems:
            if child:
                # labels do thier own sizing. self will size the label to the width of the menu,
                # self will put the cascading menu arrow on the right side automatically.	
                child.SetWide(self._menuWide - ileft - iright)			

    def MakeItemsVisibleInScrollRange(self, maxVisibleItems, nNumPixelsAvailable ):
        """ Makes menu items visible in relation to where the scroll bar is """
        # Detach all items from tree
        for item in self.menuitems:
            item.SetBounds( 0, 0, 0, 0 )
        for seppanel in self.separatorpanels:
            seppanel.SetVisible( False )

        self.visiblesorteditems = []

        tall = 0

        startItem = self.scroller.GetValue()
        assert( startItem >= 0 )
        while True:
            if startItem >= len(self.sorteditems):
                break

            itemId = self.sorteditems[ startItem ]

            if not self.menuitems[ itemId ].IsVisible():
                startItem += 1
                continue

            itemHeight = self.menuitemheight
            try:
                sepIndex = self.separators.index( itemId )
                itemHeight += MENU_SEPARATOR_HEIGHT
            except ValueError:
                pass

            if tall + itemHeight > nNumPixelsAvailable:
                break

            # Too many items
            if maxVisibleItems > 0:
                if len(self.visiblesorteditems) >= maxVisibleItems:
                    break

            tall += itemHeight
            # Re-attach self one
            self.visiblesorteditems.append( itemId )
            startItem += 1

    def LayoutMenuBorder(self):
        """ Get the approproate menu border """
        schemeobj = scheme().GetIScheme( self.GetScheme() )

        menuBorder = schemeobj.GetBorder("MenuBorder")	   
        
        if menuBorder:
            self.SetBorder(menuBorder)
            
    def Paint(self):
        """ Draw a black border on the right side of the menu items """
        if self.scroller.IsVisible():		
            # draw black bar
            wide, tall = self.GetSize()
            surface().DrawSetColor(self._borderdark)
            if self.IsProportional():
                surface().DrawFilledRect(wide - self.scroller.GetWide(), -1, wide - self.scroller.GetWide() + 1, tall)	
            else:
                surface().DrawFilledRect(wide - self.scroller.GetWide(), -1, wide - self.scroller.GetWide() + 1, tall)	
                
    def SetNumberOfVisibleItems(self, numItems):
        """ sets the max number of items visible (scrollbar appears with more) """
        self.numvisiblelines = numItems
        self.InvalidateLayout(False)

    def GetMenuItem(self, itemID):
        try:
            return self.menuitems[itemID]
        except IndexError:
            return None

    def IsValidMenuID(self, itemID):
        try:
            self.menuitems[itemID]
            return True
        except IndexError:
            return False

    def CloseOtherMenus(self, item):
        """ When a menuItem is selected, close cascading menus
            if the menuItem selected has a cascading menu attached, we
            want to keep that one open so skip it.
            Passing None will close all cascading menus. """
        for m in self.menuitems:
            if not m or m == item:
                continue

            m.CloseCascadeMenu()
            
    def OnCommand(self, command ):
        """ Respond to string commands. """
        # forward on the message
        self.PostActionSignal(KeyValues("Command", "command", command))
        
        Panel.OnCommand(command)

    def OnKeyCodeTyped(self, code):
        """ Handle key presses, Activate shortcuts """
        # Don't allow key inputs when disabled!
        if not self.IsEnabled():
            return

        alt = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LALT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RALT))
        if alt:
            super(Menu, self).OnKeyCodeTyped( code )
            self.PostActionSignal(KeyValues("MenuClose"))

        if code == ButtonCode_t.KEY_ESCAPE or code == ButtonCode_t.KEY_XBUTTON_B:
            # hide the menu on ESC
            self.SetVisible(False)
            
        elif code == ButtonCode_t.KEY_UP or code == ButtonCode_t.KEY_XBUTTON_UP or code == ButtonCode_t.KEY_XSTICK1_UP:
            # arrow keys scroll through items on the list.
            # they should also scroll the scroll bar if needed
            self.MoveAlongMenuItemList(self.MENU_UP, 0)
            try:
                self.menuitems[self.currentlyselecteditemid].ArmItem()
            except IndexError:
                pass
                
        elif code == ButtonCode_t.KEY_DOWN or code == ButtonCode_t.KEY_XBUTTON_DOWN or code == ButtonCode_t.KEY_XSTICK1_DOWN:
            self.MoveAlongMenuItemList(self.MENU_DOWN, 0)
            try:
                self.menuitems[self.currentlyselecteditemid].ArmItem()	
            except IndexError:
                pass
                
        elif code == ButtonCode_t.KEY_RIGHT or code == ButtonCode_t.KEY_XBUTTON_RIGHT or code == ButtonCode_t.KEY_XSTICK1_RIGHT:
            # for now left and right arrows just open or close submenus if they are there.
            # make sure a menuItem is currently selected
            try:
                if self.menuitems[self.currentlyselecteditemid].HasMenu():
                    self.ActivateItem(self.currentlyselecteditemid)
                else:
                    super(Menu, self).OnKeyCodeTyped( code )
            except IndexError:
                super(Menu, self).OnKeyCodeTyped( code )
                
        elif code == ButtonCode_t.KEY_LEFT or code == ButtonCode_t.KEY_XBUTTON_LEFT or code == ButtonCode_t.KEY_XSTICK1_LEFT:
                # if our parent is a menu item then we are a submenu so close us.
                if self.GetParentMenuItem():
                    self.SetVisible(False)
                else:
                    super(Menu, self).OnKeyCodeTyped( code )
                    
        elif code == ButtonCode_t.KEY_ENTER or code == ButtonCode_t.KEY_XBUTTON_A:
            # make sure a menuItem is currently selected
            try:
                self.ActivateItem(self.currentlyselecteditemid)
            except IndexError:
                super(Menu, self).OnKeyCodeTyped( code ) # chain up
                
        # don't chain back

    def OnKeyTyped(self, unichar):
        """ Handle key presses, Activate shortcuts """
        #
        # NOTE - if hotkeys are ever enabled you need to work out a way to differentiate between
        # combo box menus (which can't have hot keys) and system style menus (which do have hot keys).
        #
        #
        itemToSelect = self.currentlyselecteditemid
        if itemToSelect < 0:
            itemToSelect = 0

        i = itemToSelect + 1
        if i >= len(self.menuitems):
            i = 0

        while i != itemToSelect:
            menuItemName = self.menuitems[i].GetText()

            if menuItemName[0] == unichar:
                itemToSelect = i
                break			

            i += 1
            if i >= len(self.menuitems):
                i = 0

        if itemToSelect >= 0:
            self.SetCurrentlyHighlightedItem( itemToSelect )
            self.InvalidateLayout()
            
        # don't chain back

    def OnMouseWheeled(self, delta):
        """ Purpose: Handle the mouse wheel event, scroll the selection """
        if not self.scroller.IsVisible():
            return
        
        val = self.scroller.GetValue()
        val -= delta
        
        self.scroller.SetValue(val)	

        # moving the slider redraws the scrollbar,
        # and so we should redraw the menu since the
        # menu draws the black border to the right of the scrollbar.
        self.InvalidateLayout()

        # don't chain back
        
    def OnKillFocus(self):
        """ Lose focus, hide menu """
        # check to see if it's a child taking it
        if vgui_input().GetFocus() == False or ipanel().HasParent(vgui_input().GetFocus(), self.GetVPanel()) == False:
            # if we don't accept keyboard input, then we have to ignore the killfocus if it's not actually being stolen
            if self.IsKeyBoardInputEnabled() == False and vgui_input().GetFocus() == False:
                return

            # get the parent of self menu. 
            item = self.GetParentMenuItem()
            # if the parent is a menu item, self menu is a cascading menu
            # if the panel that is getting focus is the parent menu, don't close self menu.
            if (item) and (vgui_input().GetFocus() == item.GetVParent()):
                # if we are in mouse mode and we clicked on the menuitem that
                # triggers the cascading menu, leave it open.
                if self.inputmode == self.MOUSE:
                    # return the focus to the cascading menu.
                    self.MoveToFront()
                    return

            # forward the message to the parent.
            self.PostActionSignal(KeyValues("MenuClose"))

            # hide self menu
            self.SetVisible(False)

    # Singleton helper class
    g_MenuMgr = MenuManager()

    @staticmethod
    def OnInternalMousePressed( other, code ):
        """ Static method called on mouse released to see if Menu objects should be aborted """
        self.g_MenuMgr.OnInternalMousePressed( other, code )

    def SetVisible(self, state):
        """ Set visibility of menu and its children as appropriate. """
        if state == self.IsVisible():
            return

        if state == False:
            self.PostActionSignal(KeyValues("MenuClose"))
            self.CloseOtherMenus(None)

            self.SetCurrentlySelectedItem(-1)

            self.g_MenuMgr.RemoveMenu( self )
        elif state == True:
            self.MoveToFront()
            self.RequestFocus()

            self.g_MenuMgr.AddMenu( self )
        
        # must be after movetofront()
        super(Menu, self).SetVisible(state)
        self._sizedforscrollbar = False

    def ApplySchemeSettings(self, schemeobj):
        super(Menu, self).ApplySchemeSettings(schemeobj)
        
        self.SetFgColor(self.GetSchemeColor("Menu.TextColor", schemeobj))
        self.SetBgColor(self.GetSchemeColor("Menu.BgColor", schemeobj))

        self._borderdark = schemeobj.GetColor("BorderDark", Color(255, 255, 255, 0))

        for item in self.menuitems:
            if item.IsCheckable():
                wide, tall = item.GetCheckImageSize()

                self.checkimagewidth = max ( self.checkimagewidth, wide )
        self._recalculatewidth = True
        self.CalculateWidth()

        self.InvalidateLayout()

    def SetBgColor(self, newColor):
        super(Menu, self).SetBgColor( newColor )
        for item in self.menuitems:
            if item.HasMenu():
                item.GetMenu().SetBgColor( newColor )
                
    def SetFgColor(self, newColor ):
        super(Menu, self).SetFgColor( newColor )
        for item in self.menuitems:
            if item.HasMenu():
                item.GetMenu().SetFgColor( newColor )

    def SetBorder(self, border):
        Panel.SetBorder(self, border)

    def GetParentMenuItem(self):
        """ returns a pointer to a MenuItem that is self menus parent, if it has one """
        parent = self.GetParent()
        if type(parent) == MenuItem:
            return parent
        return None

    def OnMenuItemSelected(self, vpanel):
        """ Hide the menu when an item has been selected """
        self.SetVisible(False)
        self.scroller.SetVisible(False)
        
        panel = ipanel().GetPanel(vpanel, self.GetModuleName())
        
        # chain self message up through the hierarchy so
        # all the parent menus will close
        
        # get the parent of self menu. 
        item = self.GetParentMenuItem()
        # if the parent is a menu item, self menu is a cascading menu
        if item:
            # get the parent of the menuitem. it should be a menu.
            parentMenu = item.GetParentMenu()
            if parentMenu:
                # send the message to self parent menu
                kv = KeyValues("MenuItemSelected")
                kv.SetInt("panel", vpanel)
                self.PostMessage(parentMenu,  kv)
                
        activeItemSet = False
        
        for i, item in enumerate(self.menuitems):
            if item == panel:
                activeItemSet = True
                self.activateditem = i
                break

        # also pass it to the parent so they can respond if they like
        if self.GetVParent():
            kv = KeyValues("MenuItemSelected")
            kv.SetInt("panel", vpanel)

            self.PostMessage(self.GetParent(), kv)

    def GetActiveItem(self):
        return self.activateditem

    def GetItemUserData(self, itemID):
        try:
            menuItem = self.menuitems[itemID]
            # make sure its enabled since disabled items get highlighted.
            if menuItem and menuItem.IsEnabled():
                return menuItem.GetUserData()
        except IndexError:
            return None

    def GetItemText(self, itemID):
        """ data accessor """
        try:
            menuItem = self.menuitems[itemID]
            if menuItem:
                return menuItem.GetText()
        except IndexError:
            return ""

    def ActivateItem(self, itemID):
        """ Activate the n'th item in the menu list, as if that menu item had been selected by the user """
        try:
            menuItem = self.menuitems[itemID]
            # make sure its enabled since disabled items get highlighted.
            if menuItem and menuItem.IsEnabled():
                menuItem.FireActionSignal()
                self.activateditem = itemID
        except IndexError:
            pass

    def ActivateItemByRow(self, row):
        try:
            self.ActivateItem(self.sorteditems[row])
        except IndexError:
            pass

    def GetItemCount(self):
        """ Return the number of items currently in the menu list """
        return len(self.menuitems)

    def GetMenuID(self, index):
        try:
            return self.sorteditems[index]
        except IndexError:
            return -1

    def GetCurrentlyVisibleItemsCount(self):
        """ Return the number of items currently visible in the menu list """
        if len(self.menuitems) < self.numvisiblelines:
            cMenuItems = 0
            for item in self.menuitems:
                if item.IsVisible():
                    ++cMenuItems

            return cMenuItems
        return self.numvisiblelines

    def SetItemEnabled(self, itemIDorStr, state):
        """ Enables/disables choices in the list
            itemText - string name of item in the list 
            state - True enables, False disables """
        if type(itemIDorStr) == str:
            for item in self.menuitems:
                if itemIDorStr == item.GetName():
                    item.SetEnabled(state)
        else:
            try:
                self.menuitems[itemIDorStr].SetEnabled(state)
            except IndexError:
                return

    def SetItemVisible(self, itemIDorStr, state):
        """ shows/hides choices in the list """
        if type(itemIDorStr) == str:
            for item in self.menuitems:
                if itemIDorStr == item.GetName():
                    item.SetVisible(state)
                    self.InvalidateLayout()
        else:
            try:
                self.menuitems[itemIDorStr].SetVisible(state)
            except IndexError:
                return        
  
    def AddScrollBar(self):
        """" Make the scroll bar visible and narrow the menu
            also make items visible or invisible in the list as appropriate """
        self.scroller.SetVisible(True)
        self._sizedforscrollbar = True
        
    def RemoveScrollBar(self):
        """ Make the scroll bar invisible and widen the menu """
        self.scroller.SetVisible(False)
        self._sizedforscrollbar = False

    def OnSliderMoved(self):
        """ Invalidate layout if the slider is moved so items scroll """
        self.CloseOtherMenus(None) # close any cascading menus

        # Invalidate so we redraw the menu!
        self.InvalidateLayout()
        self.Repaint()
        
    def OnCursorMoved(self, x, y):
        """ Toggle into mouse mode. """
        self.inputmode = self.MOUSE
        
        # chain up
        self.CallParentFunction(KeyValues("OnCursorMoved", "x", x, "y", y))
        self.RequestFocus()
        self.InvalidateLayout()

    def OnKeyCodePressed(self, code):
        """ Toggle into keyboard mode. """
        self.inputmode = self.KEYBOARD
        # send the message to self parent in case self is a cascading menu
        if self.GetVParent():
            self.PostMessage(self.GetParent(), KeyValues("KeyModeSet"))
        
    def ClearCurrentlyHighlightedItem(self):
        try:
            self.menuitems[self.currentlyselecteditemid].DisarmItem()
        except IndexError:
            self.currentlyselecteditemid = -1

    def SetCurrentlySelectedItem(self, item):
        """ Sets the item currently highlighted in the menu by index or reference """
        if type(item) == int:
            itemID = item
            # dont deselect if its the same item
            if itemID == self.currentlyselecteditemid:
                return

            try:
                self.menuitems[self.currentlyselecteditemid].DisarmItem()
            except IndexError:
                pass

            self.PostActionSignal(KeyValues("MenuItemHighlight", "itemID", itemID))
            self.currentlyselecteditemid = itemID    
        else:
            itemNum = -1
            # find it in our list of menuitems
            for i, child in enumerate(self.menuitems):
                if child == item:
                    itemNum = i
                    break
            assert( itemNum >= 0 )

            self.SetCurrentlySelectedItem(itemNum)            

    def SetCurrentlyHighlightedItem(self, itemID):
        """ self will set the item to be currenly selected and highlight it
            will not open cascading menu. self was added for comboboxes
            to have the combobox item highlighted in the menu when they open the
            dropdown. """
        self.SetCurrentlySelectedItem(itemID)
        row = self.sorteditems.index(itemID)
        assert(row != -1)

        # if there is a scroll bar, and we scroll off lets move it.
        if self.scroller.IsVisible():
            # now if we are off the scroll bar, it means we moved the scroll bar
            # by hand or set the item off the list 
            # so just snap the scroll bar straight to the item.
            if ( ( row >  self.scroller.GetValue() + self.numvisiblelines - 1 ) or
                 ( row < self.scroller.GetValue() ) ):			
                if not self.scroller.IsVisible():
                    return
                
                self.scroller.SetValue(row)	

        try:
            if self.menuitems[self.currentlyselecteditemid].IsArmed() == False:
                self.menuitems[self.currentlyselecteditemid].ArmItem()
        except IndexError:
            pass

    def GetCurrentlyHighlightedItem(self):
        return self.currentlyselecteditemid

    def OnCursorEnteredMenuItem(self, VPanel):
        """ Respond to cursor entering a menuItem. """
        menuItem = VPanel
        # if we are in mouse mode
        if self.inputmode == self.MOUSE:
            item = ipanel().GetPanel(menuItem, self.GetModuleName())
            # arm the menu
            item.ArmItem()
            # open the cascading menu if there is one.
            item.OpenCascadeMenu()
            self.SetCurrentlySelectedItem(item)

    def OnCursorExitedMenuItem(self, VPanel):
        """ Respond to cursor exiting a menuItem """
        menuItem = VPanel
        # only care if we are in mouse mode
        if self.inputmode == self.MOUSE:
            item = ipanel().GetPanel(menuItem, self.GetModuleName())
            # unhighlight the item.
            # note menuItems with cascading menus will stay lit.
            item.DisarmItem()

    def MoveAlongMenuItemList(self, direction, loopCount):
        """ Move up or down one in the list of items in the menu 
            Direction is MENU_UP or MENU_DOWN """
        itemID = self.currentlyselecteditemid
        row = self.sorteditems.index(itemID)
        row += direction
        
        if row > len(self.sorteditems) - 1:
            if self.scroller.IsVisible():
                # stop at bottom of scrolled list
                row = len(self.sorteditems) - 1
            else:
                # if no scroll bar we circle around
                row = 0
        elif row < 0:
            if self.scroller.IsVisible():
                # stop at top of scrolled list
                row = self.scroller.GetValue()
            else:
                # if no scroll bar circle around
                row = len(self.sorteditems)-1

        # if there is a scroll bar, and we scroll off lets move it.
        if self.scroller.IsVisible():
            if row > self.scroller.GetValue() + self.numvisiblelines - 1:		
                val = self.scroller.GetValue()
                val -= -direction
                
                self.scroller.SetValue(val)	
                
                # moving the slider redraws the scrollbar,
                # and so we should redraw the menu since the
                # menu draws the black border to the right of the scrollbar.
                self.InvalidateLayout()
            elif row < self.scroller.GetValue():	
                val = self.scroller.GetValue()	
                val -= -direction
                
                self.scroller.SetValue(val)	
                
                # moving the slider redraws the scrollbar,
                # and so we should redraw the menu since the
                # menu draws the black border to the right of the scrollbar.
                self.InvalidateLayout()	

            # now if we are still off the scroll bar, it means we moved the scroll bar
            # by hand and created a situation in which we moved an item down, but the
            # scroll bar is already too far down and should scroll up or vice versa
            # so just snap the scroll bar straight to the item.
            if ( ( row > self.scroller.GetValue() + self.numvisiblelines - 1) or
                 ( row < self.scroller.GetValue() ) ):		
                self.scroller.SetValue(row)	

        # switch it back to an itemID from row
        try:
            self.SetCurrentlySelectedItem( self.sorteditems[row] )
        except IndexError:
            pass

        # don't allow us to loop around more than once
        if loopCount < len(self.menuitems):
            # see if the text is empty, if so skip
            text = self.menuitems[self.currentlyselecteditemid].GetText()
            if text[0] == 0 or not self.menuitems[self.currentlyselecteditemid].IsVisible():
                # menu item is empty, keep moving along
                self.MoveAlongMenuItemList(direction, loopCount + 1)

    def GetMenuMode(self):
        """ Return which type of events the menu is currently interested in
            MenuItems need to know because behaviour is different depending on mode. """
        return self.inputmode

    def OnKeyModeSet(self):
        """ Set the menu to key mode if a child menu goes into keymode
            self mode change has to be chained up through the menu heirarchy
            so cascading menus will work when you do a bunch of stuff in keymode
            in high level menus and then switch to keymode in lower level menus. """
        self.inputmode = self.KEYBOARD

    def SetMenuItemChecked(self, itemID, state):
        """ Set the checked state of a menuItem """
        self.menuitems[itemID].SetChecked(state)

    def IsChecked(self, itemID):
        """ Check if item is checked. """
        return self.menuitems[itemID].IsChecked()

    def SetMinimumWidth(self, width):
        """ Set the minmum width the menu has to be. self
            is useful if you have a menu that is sized to the largest item in it
            but you don't want the menu to be thinner than the menu button """
        self.minimumwidth = width

    def GetMinimumWidth(self):
        """ Get the minmum width the menu """
        return self.minimumwidth

    def AddSeparator(self):
        lastID = len(self.menuitems) - 1
        self.separators.append( lastID )
        self.separatorpanels.append( MenuSeparator( self, "MenuSeparator" ) )

    def AddSeparatorAfterItem(self, itemID):
        try:
            self.menuitems[itemID]
        except:
            assert(0)
        self.separators.append( itemID )
        self.separatorpanels.append( MenuSeparator( self, "MenuSeparator" ) )

    def MoveMenuItem(self, itemID, moveBeforeselfItemID):
        for item in self.sorteditems:
            if item == itemID:
                self.sorteditems.remove( item )
                break

        # Didn't find it
        if i >= c:
            return

        # Now find insert pos
        for item in self.self.sorteditems:
            if item == moveBeforeselfItemID:
                self.sorteditems.insert( i, itemID )
                break
                
    def SetFont(self, font):
        self.itemfont = font
        if font:
            self.menuitemheight = surface().GetFontTall( font ) + 2
        self.InvalidateLayout()

    def SetCurrentKeyBinding(self, itemID, hotkey):
        try:
            menuItem = self.menuitems[itemID]
            menuItem.SetCurrentKeyBinding( hotkey )
        except IndexError:
            pass

    @staticmethod
    def PlaceContextMenu(parent, menu):
        """ Static method to display a context menu """
        assert( parent )
        assert( menu )
        if menu == None or parent == None:
            return

        menu.SetVisible(False)
        menu.SetParent( parent )
        menu.AddActionSignalTarget( parent )

        # get cursor position, self is local to self text edit window
        cursorX, cursorY = vgui_input().GetCursorPos()

        menu.SetVisible(True)
        
        # relayout the menu immediately so that we know it's size
        menu.InvalidateLayout(True)
        menuWide, menuTall = menu.GetSize()
        
        # work out where the cursor is and therefore the best place to put the menu
        wide, tall = surface().GetScreenSize()
        
        if (wide - menuWide > cursorX):
            # menu hanging right
            if (tall - menuTall > cursorY):
                # menu hanging down
                menu.SetPos(cursorX, cursorY)
            else:
                # menu hanging up
                menu.SetPos(cursorX, cursorY - menuTall)
        else:
            # menu hanging left
            if (tall - menuTall > cursorY):
                # menu hanging down
                menu.SetPos(cursorX - menuWide, cursorY)
            else:
                # menu hanging up
                menu.SetPos(cursorX - menuWide, cursorY - menuTall)
        
        menu.RequestFocus()

    def SetUseFallbackFont(self, bState, hFallback ):
        self.fallbackitemfont = hFallback
        self.usefallbackfont = bState
        
    # Settings
    DEFAULT_MENU_ITEM_HEIGHT = 22       # height of items in the menu
    MENU_UP = -1                        # used for moving up/down list of menu items in the menu
    MENU_DOWN = 1   

    MOUSE = 0
    KEYBOARD = 1

    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3
    CURSOR = 4	# make the menu appear under the mouse cursor
    ALIGN_WITH_PARENT = 5 # make the menu appear under the parent    
    
    MENU_SEPARATOR_HEIGHT = 3
        