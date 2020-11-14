""" Python version of MenuItem """
from srcbase import KeyValues
from vgui import surface
from vgui.controls import TextImage, Button, Label

class MenuItemCheckImage(TextImage):
    """ Check box image """ 
    def __init__(self, item):
        super(MenuItemCheckImage, self).__init__(self, "g")
        self._menuitem = item

        self.SetSize(20, 13)

    def Paint(self):
        self.DrawSetTextFont(self.GetFont())
        
        # draw background
        self.DrawSetTextColor(self._menuitem.GetBgColor())
        self.DrawPrintChar(0, 0, 'g')

        # draw check
        if self._menuitem.IsChecked():
            if self._menuitem.IsEnabled():
                self.DrawSetTextColor(self._menuitem.GetButtonFgColor())
                self.DrawPrintChar(0, 2, 'a')
            elif self._menuitem.IsEnabled() == False:
                # draw disabled version, with embossed look
                # offset image
                self.DrawSetTextColor(self._menuitem.GetDisabledFgColor1())
                self.DrawPrintChar(1, 3, 'a')
                
                # overlayed image
                self.DrawSetTextColor(self._menuitem.GetDisabledFgColor2())
                self.DrawPrintChar(0, 2, 'a')
        
# MenuItem class   
class MenuItem(Button):     
    def __init__(self, parent, panelName, text, cascadeMenu=None, checkable=False):
        """
         Input:	parent - the parent of self menu item, usually a menu
                    text - the name of the menu item as it appears in the menu
                    cascadeMenu - if self item triggers the opening of a cascading menu
                    provide a pointer to it.
                    MenuItems cannot be both checkable and trigger a cascade menu.
        """
        self.cascademenu = cascadeMenu
        self.checkable = checkable
        
        self.userdata = None
        self.currentkeybinding = None        
        
        super(MenuItem, self).__init__(parent, panelName, text)

        # only one arg should be passed in.
        assert ((cascadeMenu != None and checkable) == False)
        
        #self.Init()

    def Init(self):
        """ Basic initializer """
        super(MenuItem, self).Init()
        
        self.cascadearrow	= None
        self.check = None

        if self.cascademenu:
            self.cascademenu.SetParent(self)
            self.cascadearrow = TextImage (" 4")	# self makes a right pointing arrow.

            self.cascademenu.AddActionSignalTarget(self)
        elif self.checkable:
            # move the text image over so we have room for the check
            self.SetTextImageIndex(1)
            self.check = MenuItemCheckImage(self)
            self.SetImageAtIndex(0, self.check, self.CHECK_INSET)
            self.SetChecked(False)

        self.SetButtonBorderEnabled( False )
        self.SetUseCaptureMouse( False )
        self.SetContentAlignment( Label.a_west )
        
        self.SetButtonActivationType(self.ACTIVATE_ONRELEASED)

        # note menus handle all the sizing of menuItem panels
  
    def GetParentMenu(self):
        return self.GetParent()

    def PerformLayout(self):
        """ Layout the Textimage and the Arrow part of the menuItem """
        Button.PerformLayout(self)
        # make the arrow image match the button layout.
        # self will make it brighten and dim like the menu buttons.
        if self.cascadearrow:
            self.cascadearrow.SetColor(self.GetButtonFgColor())

    def CloseCascadeMenu(self):
        """ Close the cascading menu if we have one. """
        if self.cascademenu:
            if self.cascademenu.IsVisible():
                self.cascademenu.SetVisible(False)
            # disarm even if menu wasn't visible!
            self.SetArmed(False)

    def OnCursorMoved(self, x, y):
        """ Purpose: Handle cursor moving in a menuItem. """
        # if menu is in keymode and we moved the mouse
        # highlight self item
        from . import menu
        if self.GetParentMenu().GetMenuMode() == menu.Menu.KEYBOARD:
            self.OnCursorEntered()

        # chain up to parent
        self.CallParentFunction(KeyValues("OnCursorMoved", "x", x, "y", y))

    def OnCursorEntered(self):
        """ Handle mouse cursor entering a menuItem. """
        # post a message to the parent menu.
        # forward the message on to the parent of self menu.
        msg = KeyValues ("CursorEnteredMenuItem")
        # tell the parent self menuitem is the one that was entered so it can highlight it
        msg.SetInt("VPanel", self.GetVPanel())

        self.PostMessage(self.GetParent(), msg)

    def OnCursorExited(self):
        """ Handle mouse cursor exiting a menuItem. """
        # post a message to the parent menu.
        # forward the message on to the parent of self menu.
        msg = KeyValues ("CursorExitedMenuItem")
        # tell the parent self menuitem is the one that was entered so it can unhighlight it
        msg.SetInt("VPanel", self.GetVPanel())

        self.PostMessage(self.GetParent(), msg)

    def OnKeyCodeReleased(self, code):
        """ Handle mouse cursor exiting a menuItem """
        from . import menu
        if self.GetParentMenu().GetMenuMode() == menu.Menu.KEYBOARD and self.cascademenu:
            return
        # only disarm if we are not opening a cascading menu using keys.
        Button.OnKeyCodeReleased(self, code)

    def ArmItem(self):
        """ Highlight a menu item
            Menu item buttons highlight if disabled, but won't activate. """
        # close all other menus 
        self.GetParentMenu().CloseOtherMenus(self)
        # arm the menuItem.
        Button.SetArmed(self, True)	

        # When you have a submenu with no scroll bar the menu
        # border will not be drawn correctly. self fixes it.
        parent = self.GetParentMenu()
        if parent:
            parent.ForceCalculateWidth()
            
        self.Repaint()

    def DisarmItem(self):
        """ Unhighlight a menu item """
        # normal behaviour is that the button becomes unarmed
        # do not unarm if there is a cascading menu. CloseCascadeMenu handles self.
        # and the menu handles it since we close at different times depending
        # on whether menu is handling mouse or key events.
        if self.cascademenu == None:
            Button.OnCursorExited(self)

        # When you have a submenu with no scroll bar the menu
        # border will not be drawn correctly. self fixes it.
        parent = self.GetParentMenu()
        if parent:
            parent.ForceCalculateWidth()
        self.Repaint()

    def IsItemArmed(self):
        return Button.IsArmed(self)

    def OnKillFocus(self):
        """ Pass kill focus events up to parent, self will tell all panels
            in the hierarchy to hide themselves, and enables cascading menus to
            all disappear on selecting an item at the end of the tree. """
        self.GetParentMenu().OnKillFocus()

    def FireActionSignal(self):
        """ fire the menu item as if it has been selected and 
            Tell the owner that it is closing """
        # cascading menus items don't trigger the parent menu to disappear
        # (they trigger the cascading menu to open/close when cursor is moved over/off them)
        if self.cascademenu == None:
            kv = KeyValues("MenuItemSelected")
            kv.SetInt("panel", self.GetVPanel() )
            self.PostMessage(self.GetParent(), kv)

            #	self.PostMessage(self.GetParent(), KeyValues("MenuItemSelected"))		
            Button.FireActionSignal(self)
            # toggle the check next to the item if it is checkable
            if self.checkable:
                self.SetChecked( not self.checked )
        else:
            # if we are in keyboard mode, open the child menu.
            from . import menu
            if self.GetParentMenu().GetMenuMode() == menu.Menu.KEYBOARD:
                self.OpenCascadeMenu()		

    def OpenCascadeMenu(self):	
        """ Opens the cascading menu """
        if self.cascademenu:
            # perform layout on menu, self way it will open in the right spot 
            # if the window's been moved
            self.cascademenu.PerformLayout()
            self.cascademenu.SetVisible(True)
            self.ArmItem()

    def HasMenu(self):
        """ Return True if self item triggers a cascading menu """
        return (self.cascademenu != None)

    def ApplySchemeSettings(self, schemeobj):
        """ Apply the resource scheme to the menu. """
        # chain back first
        Button.ApplySchemeSettings(self, schemeobj)

        # get color settings
        self.SetDefaultColor(self.GetSchemeColor("Menu.TextColor", self.GetFgColor(), schemeobj), self.GetSchemeColor("Menu.BgColor", self.GetBgColor(), schemeobj))
        self.SetArmedColor(self.GetSchemeColor("Menu.ArmedTextColor", self.GetFgColor(), schemeobj), self.GetSchemeColor("Menu.ArmedBgColor", self.GetBgColor(), schemeobj))
        self.SetDepressedColor(self.GetSchemeColor("Menu.ArmedTextColor", self.GetFgColor(), schemeobj), self.GetSchemeColor("Menu.ArmedBgColor", self.GetBgColor(), schemeobj))

        self.SetTextInset(int(schemeobj.GetResourceString("Menu.TextInset")), 0)
        
        # reload images since applyschemesettings in label wipes them out.
        if self.cascadearrow:
            self.cascadearrow.SetFont(schemeobj.GetFont("Marlett", self.IsProportional() ))
            self.cascadearrow.ResizeImageToContent()
            self.AddImage(self.cascadearrow, 0)
        elif self.checkable:
            self.check.SetFont( schemeobj.GetFont("Marlett", self.IsProportional()))
            self.SetImageAtIndex(0, self.check, self.CHECK_INSET)
            self.check.ResizeImageToContent()

        if self.currentkeybinding:
            self.currentkeybinding.SetFont(schemeobj.GetFont("Default", self.IsProportional() ))
            self.currentkeybinding.ResizeImageToContent()

        # Have the menu redo the layout
        # Get the parent to resize
        parent = self.GetParentMenu()
        if parent:
            parent.ForceCalculateWidth()

    def GetTextImageSize(self):
        """ Return the size of the text portion of the label.
            for normal menu items self is the same as the label size, but for
            cascading menus it gives you the size of the text portion only, without
            the arrow. """
        wide, tall = self.GetTextImage().GetSize()
        return wide, tall

    def SetTextImageSize(self, wide, tall):
        """ Set the size of the text portion of the label.
                    For normal menu items self is the same as the label size, but for
                    cascading menus it sizes textImage portion only, without
                    the arrow. """
        self.GetTextImage().SetSize(wide, tall)

    def GetArrowImageSize(self):
        """ Return the size of the arrow portion of the label.
                    If the menuItem is not a cascading menu, 0 is returned. """
        wide = 0
        tall = 0
        if self.cascadearrow:
            self.cascadearrow.GetSize(wide, tall)
        return wide, tall

    def GetCheckImageSize(self):
        """ Return the size of the check portion of the label. """
        wide = 0
        tall = 0
        if self.check:
            # resize the image to the contents size
            self.check.ResizeImageToContent()
            self.check.GetSize(wide, tall)

            # include the inset for the check, since nobody but us know about the inset
            wide += self.CHECK_INSET
        return wide, tall

    def GetMenu(self):
        """ Return a the menu that self menuItem contains
                  self is useful when the parent menu's commands must be
                  sent through all menus that are open as well (like hotkeys) """
        return self.cascademenu

    def GetBorder(self, depressed, armed, selected, keyfocus):
        """ Purpose: Get the border style for the button. Menu items have no border so
                    return None """
        return None

    def OnKeyModeSet(self):
        """ Set the menu to key mode if a child menu goes into keymode """
        # send the message to self parent in case self is a cascading menu
        self.PostMessage( self.GetParent(), KeyValues("KeyModeSet") )

    def IsCheckable(self):
        """ Purpose: Return if self menuitem is checkable or not
            self is used by menus to perform the layout properly. """
        return self.checkable
    
    def IsChecked(self):
        """ Return if self menuitem is checked or not """
        return self.checked

    def SetChecked(self, state):
        """ Set the checked state of a checkable menuitem
                    Does nothing if item is not checkable """
        if self.checkable:
            self.checked = state

    def CanBeDefaultButton(self):
        return False

    def GetUserData(self):
        if self.HasMenu():
            return self.cascademenu.GetItemUserData( self.cascademenu.GetActiveItem() )
        else:
            return self.userdata

    def SetUserData(self, kv):
        """ sets the user data """
        if self.userdata:
            self.userdata = None
        
        if kv != None:
            self.userdata = kv

    def SetCurrentKeyBinding(self, keyName):
        """ Passing in None removes self object
            Input  : keyName """
        if keyName == None:
            self.currentkeybinding = None
            return

        if self.currentkeybinding == None:
            self.currentkeybinding = TextImage( keyName )
        else:
            curtext = self.currentkeybinding.GetText()
            if curtext == keyName:
                return

            self.currentkeybinding.SetText( keyName )

        self.InvalidateLayout( False, True )
        
    KEYBINDING_INSET = 5

    def Paint(self):
        super(MenuItem, self).Paint()
        if self.currentkeybinding == None:
            return

        w, h = self.GetSize()
        iw, ih = self.currentkeybinding.GetSize()

        x = w - iw - self.KEYBINDING_INSET
        y = ( h - ih ) / 2

        if IsEnabled():
            self.currentkeybinding.SetPos( x, y )
            self.currentkeybinding.SetColor( self.GetButtonFgColor() )
            self.currentkeybinding.Paint()
        else:
            self.currentkeybinding.SetPos( x + 1 , y + 1 )
            self.currentkeybinding.SetColor( self.GetDisabledFgColor1() )
            self.currentkeybinding.Paint()

            surface().DrawFlushText()

            self.currentkeybinding.SetPos( x, y )
            self.currentkeybinding.SetColor( self.GetDisabledFgColor2() )
            self.currentkeybinding.Paint()

    def GetContentSize(self):
        cw, ch = super(MenuItem, self).GetContentSize()
        if self.currentkeybinding == None:
            return cw, ch

        iw, ih = self.currentkeybinding.GetSize()

        cw += iw + self.KEYBINDING_INSET
        ch = max( ch, ih )
        return cw, ch
        
    CHECK_INSET = 6