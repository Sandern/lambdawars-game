""" Python version of MenuButton """
from srcbase import KeyValues
from vgui import surface, vgui_input
from vgui.controls import Button
from input import ButtonCode_t

class MenuButton(Button):
    def __init__(self, parent, panelName, text):
        super(MenuButton, self).__init__(parent, panelName, text)
        self.menu = None
        from . import menu
        self.direction = menu.Menu.DOWN
        self.dropmenuimage = None
        self.imageindex = -1
        self._openoffsetY = 0

        self.SetDropMenuButtonStyle( False )
        self.SetUseCaptureMouse( False )
        self.SetButtonActivationType( self.ACTIVATE_ONPRESSED )
        
    # functions designed to be overriden
    def OnShowMenu(self, menu):
        pass
    def OnHideMenu(self, menu):
        pass
    def OnCheckMenuItemCount(self):
        return 0

    def SetMenu(self, menu):
        """ Attaches a menu to the menu button """
        self.menu = menu

        if menu:
            menu.SetVisible(False)
            menu.AddActionSignalTarget(self)
            menu.SetParent(self)

    def DrawFocusBorder(self, tx0, ty0, tx1, ty1):
        """ Never draw a focus border """
        pass

    def SetOpenDirection(self, direction):
        """ Sets the direction from the menu button the menu should open """
        self.direction = direction

    def HideMenu(self):
        """ hides the menu """
        if self.menu == None:
            return

        # hide the menu
        self.menu.SetVisible(False)

        # unstick the button
        super(MenuButton, self).ForceDepressed(False)
        self.Repaint()

        self.OnHideMenu(self.menu)

    def OnKillFocus(self, params):
        """ Called when the menu button loses focus; hides the menu """
        #hPanel = params.GetPtr( "newPanel" )
        #if self.menu &&  self.menu.HasFocus() == False && hPanel !=  self.menu.GetVPanel():
        #    self.HideMenu()
        super(MenuButton, self).OnKillFocus()

    def OnMenuClose(self):
        """ Purpose: Called when the menu is closed """
        self.HideMenu()
        self.PostActionSignal(KeyValues("MenuClose"))

    def SetOpenOffsetY(self, yOffset):
        """ Purpose: Sets the offset from where menu would normally be placed
                    Only is used if menu is ALIGN_WITH_PARENT """
        self._openoffsetY = yOffset

    def CanBeDefaultButton(self):
        return False

    def DoClick():
        """ Handles hotkey accesses """
        if ( self.IsDropMenuButtonStyle() and 
            self.dropmenuimage ):
            # force the menu to appear where the mouse button was pressed
            mx, my = vgui_input().GetCursorPos()
            mx, my = self.ScreenToLocal( mx, my )

            contentW, contentH = self.dropmenuimage.GetContentSize()
            drawX = GetWide() - contentW - 2
            if mx <= drawX or self.OnCheckMenuItemCount() == False:
                # Treat it like a "regular" button click
                super(MenuButton, self).DoClick()
                return

        if self.menu:
            return

        # menu is already visible, hide the menu
        if self.menu.IsVisible():
            self.HideMenu()
            return

        # do nothing if menu is not enabled
        if self.menu.IsEnabled():
            return
            
        # force the menu to compute required width/height
        self.menu.PerformLayout();

        # Now position it so it can fit in the workspace
        self.menu.PositionRelativeToPanel(self, m_iDirection, self._openoffsetY )

        # make sure we're at the top of the draw order (and therefore our children as well)
        self.MoveToFront()

        # notify
        self.OnShowMenu(self.menu)

        # keep the button depressed
        super(MenuButton,self).ForceDepressed(True)

        # show the menu
        self.menu.SetVisible(True)

        # bring to focus
        self.menu.RequestFocus()

    def OnKeyCodeTyped(self, code):
        shift = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT));
        ctrl = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL));
        alt = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LALT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RALT));

        if shift == False and ctrl == False and alt == False:
            if code == ButtonCode_t.KEY_ENTER:
                    if self.IsDropMenuButtonStyle() == False:
                        self.DoClick()
        super(MenuButton,self).OnKeyCodeTyped(code)

    def OnCursorEntered(self):
        super(MenuButton,self).OnCursorEntered()
        # post a message to the parent menu.
        # forward the message on to the parent of self menu.
        msg = KeyValues ("CursorEnteredMenuButton")
        # tell the parent self menuitem is the one that was entered so it can open the menu if it wants
        msg.SetInt("VPanel", self.GetVPanel())
        self.PostMessage(self.GetParent(), msg)

    # self style is like the IE "back" button where the left side acts like a regular button, the the right side has a little
    #  combo box dropdown indicator and presents and submenu
    def SetDropMenuButtonStyle(self, state):
        changed = self.dropmenubuttonstyle != state
        self.dropmenubuttonstyle = state
        if changed == False:
            return

        if state:
            self.dropmenuimage = TextImage( "u" )
            schemeobj = scheme().GetIScheme( self.GetScheme() )
            self.dropmenuimage.SetFont(schemeobj.GetFont("Marlett", self.IsProportional()))
            # self.dropmenuimage.SetContentAlignment(Label.a_west)
            # self.dropmenuimage.SetTextInset(3, 0)
            self.imageindex = self.AddImage( self.dropmenuimage, 0 )
        else:
            self.ResetToSimpleTextImage()
            self.dropmenuimage = None
            self.imageindex = -1

    def ApplySchemeSettings(self, schemeobj ):
        super(MenuButton,self).ApplySchemeSettings( schemeobj );

        if self.dropmenuimage:
            self.SetImageAtIndex( 1, self.dropmenuimage, 0 )

    def PerformLayout(self):
        super(MenuButton,self).PerformLayout();
        if self.IsDropMenuButtonStyle() == False:
            return

        assert( self.imageindex >= 0 )
        if self.imageindex < 0 or self.dropmenuimage == None:
            return

        w, h = self.GetSize( w, h )

        self.dropmenuimage.ResizeImageToContent()
        contentW, contentH = self.dropmenuimage.GetContentSize()

        self.SetImageBounds( self.imageindex, w - contentW - 2, contentW )

    def IsDropMenuButtonStyle(self):
        return self.dropmenubuttonstyle

    def Paint(self):
        super(MenuButton,self).Paint()

        if self.IsDropMenuButtonStyle() == False:
            return
            
        contentW, contentH = self.dropmenuimage.GetContentSize()
        if self.IsEnabled():
            self.dropmenuimage.SetColor( self.GetButtonFgColor() )
        else:
            self.dropmenuimage.SetColor( self.GetDisabledFgColor1() )
        
        drawX = self.GetWide() - contentW - 2

        if self.IsEnabled():
            surface().DrawSetColor( self.GetButtonFgColor() )
        else:
            surface().DrawSetColor( self.GetDisabledFgColor1() )
        surface().DrawFilledRect( drawX, 3, drawX + 1, self.GetTall() - 3 )

    def OnCursorMoved(self, x, y ):
        super(MenuButton,self).OnCursorMoved( x, y )

        if self.IsDropMenuButtonStyle() == False:
            return
            
        contentW, contentH = self.dropmenuimage.GetContentSize()
        drawX = self.GetWide() - contentW - 2
        if x <= drawX or self.OnCheckMenuItemCount() == False:
            self.SetButtonActivationType(self.ACTIVATE_ONPRESSEDANDRELEASED)
            self.SetUseCaptureMouse(True)
        else:
            self.SetButtonActivationType(self.ACTIVATE_ONPRESSED)
            self.SetUseCaptureMouse(False)

    def GetMenu(self):
        assert(self.menu)
        return self.menu