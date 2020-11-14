from srcbase import KeyValues, Color
from vgui import DataType_t, ipanel, scheme, vgui_input, vgui_system, surface
from vgui.controls import Label, Button, EditablePanel, ImagePanel, IBorder
from input import ButtonCode_t

#
# Context Label
#
class ContextLabel(Label):
    def __init__(self, parent, panelName, text):
        super(ContextLabel, self).__init__(parent, paenlName, text)
        self.tabbutton = parent
        self.SetBlockDragChaining( True ) 

    def OnMousePressed(self, code):
        if self.tabbutton:
            self.tabbutton.FireActionSignal() 

    def OnMouseReleased(self, code):
        super(ContextLabel, self).OnMouseReleased( code ) 

        if self.GetParent():
            self.GetParent().OnCommand( "ShowContextMenu" ) 

    def ApplySchemeSettings(self, schemeobj):
        super(ContextLabel, self).ApplySchemeSettings( schemeobj ) 

        marlett = schemeobj.GetFont( "Marlett" ) 
        self.SetFont( marlett ) 
        self.SetTextInset( 0, 0 ) 
        self.SetContentAlignment( Label.a_northwest ) 

        if self.GetParent():
            self.SetFgColor( schemeobj.GetColor( "Button.TextColor", self.GetParent().GetFgColor() ) ) 
            self.SetBgColor( self.GetParent().GetBgColor() ) 

def IsDroppingSheet(msglist):
    """ Helper for drag drop """
    if not msglist:
        return None 

    data = msglist[0] 
    return data.GetPtr( "propertysheet" )
 
# 
# A page
# 
class Page(object):
    def __init__(self):
        super(Page, self).__init__()
        self.page = 0
        self.contextMenu = False

#
# PageTab
#
class PageTab(Button):
    """ A single tab """
    def __init__(self, parent, panelName, text, imageName, maxTabWidth, page, showContextButton, hoverActivatePageTime=-1): 
        super(PageTab, self).__init__(parent, panelName, text)
        
        self.parent = parent
        self.page = page
        self.image = 0
        self.imagename = 0
        self.showcontextlabel = showContextButton
        self.attemptingdrop = False
        self.hoveractivatepagetime = hoverActivatePageTime
        self.drophovertime = -1 
     
        self.SetCommand(KeyValues("TabPressed", "panelname", panelName)) 
        self._active = False 
        self.maxtabwidth = maxTabWidth 
        self.SetDropEnabled( True ) 
        self.SetDragEnabled( self.parent.IsDraggableTab() ) 
        if imageName:
            self.image = ImagePanel(self, text) 
            self.imagename = imageName
         
        self.SetMouseClickEnabled( ButtonCode_t.MOUSE_RIGHT, True ) 
        if self.showcontextlabel:
            self.contextlabel = ContextLabel(self, "Context", "9")

        #REGISTER_COLOR_AS_OVERRIDABLE( self._textColor, "selectedcolor" ) 
        #REGISTER_COLOR_AS_OVERRIDABLE( self._dimTextColor, "unselectedcolor" ) 
     
    contextlabel = None

    #def Paint(self):
    #    super(PageTab, self).Paint() 

    def OnCursorEntered(self):
        self.drophovertime = vgui_system().GetTimeMillis() 

    def OnCursorExited(self):
        self.drophovertime = -1 

    def OnThink(self):
        if self.attemptingdrop and self.hoveractivatepagetime >= 0 and self.drophovertime >= 0:
            hoverTime = vgui_system().GetTimeMillis() - self.drophovertime 
            if hoverTime > self.hoveractivatepagetime:
                self.FireActionSignal() 
                self.SetSelected(True) 
                self.Repaint() 

        self.attemptingdrop = False 

        super(PageTab, self).OnThink() 
     
    def IsDroppable(self, msglist):
        self.attemptingdrop = True 

        if not self.GetParent():
            return False 

        sheet = IsDroppingSheet( msglist ) 
        if sheet:
            return self.GetParent().IsDroppable( msglist ) 

        return super(PageTab, self).IsDroppable( msglist ) 

    def OnDroppablePanelPaint(self, msglist, dragPanels):
        sheet = IsDroppingSheet( msglist ) 
        if sheet:
            target = self.GetParent().GetDropTarget( msglist ) 
            if target:
            # Fixme, mouse pos could be wrong...
                target.OnDroppablePanelPaint( msglist, dragPanels ) 
                return 
                
        # Just highlight the tab if dropping onto active page via the tab
        super(PageTab, self).OnDroppablePanelPaint( msglist, dragPanels ) 
     

    def OnPanelDropped(self, msglist):
        sheet = IsDroppingSheet( msglist ) 
        if sheet:
            target = self.GetParent().GetDropTarget( msglist ) 
            if target:
            # Fixme, mouse pos could be wrong...
                target.OnPanelDropped( msglist ) 

        # Defer to active page...
        active = self.parent.GetActivePage() 
        if not active or not active.IsDroppable( msglist ):
            return 

        active.OnPanelDropped( msglist ) 

    def OnDragFailed(msglist):
        sheet = IsDroppingSheet( msglist ) 
        if not sheet:
            return 

        # Create a new property sheet
        if self.parent.IsDraggableTab():
            if len(msglist) == 1:
                data = msglist[ 0 ] 
                screenx = data.GetInt( "screenx" ) 
                screeny = data.GetInt( "screeny" ) 

                # self.parent.ScreenToLocal( screenx, screeny ) 
                if not self.parent.IsWithin( screenx, screeny ):
                    page = data.GetPtr( "propertypage" )
                    sheet = data.GetPtr( "propertysheet" )
                    title = data.GetString( "tabname", "" ) 
                    if not page or not sheet:
                        return 
                    
                    # Can only create if sheet was part of a ToolWindow derived object
                    #tw = dynamic_cast< ToolWindow * >( sheet.GetParent() ) 
                    tw = None
                    if tw: 
                        factory = tw.GetToolWindowFactory() 
                        if factory:  
                            hasContextMenu = sheet.PageHasContextMenu( page ) 
                            sheet.RemovePage( page ) 
                            factory.InstanceToolWindow( tw.GetParent(), sheet.ShouldShowContextButtons(), page, title, hasContextMenu ) 

                            if sheet.GetNumPages() == 0:        
                                tw.MarkForDeletion() 

    def OnCreateDragData(self, msg):
        assert( self.parent.IsDraggableTab() ) 

        msg.SetPtr( "propertypage", self.page ) 
        msg.SetPtr( "propertysheet", self.parent ) 
        sz = self.GetText() 
        msg.SetString( "tabname", sz  ) 
        msg.SetString( "text", sz ) 

    def ApplySchemeSettings(self, schemeobj):
        # set up the scheme settings
        super(PageTab, self).ApplySchemeSettings(schemeobj) 

        self._textColor = self.GetSchemeColor("PropertySheet.SelectedTextColor", self.GetFgColor(), schemeobj) 
        self._dimTextColor = self.GetSchemeColor("PropertySheet.TextColor", self.GetFgColor(), schemeobj) 
        self.activeborder = schemeobj.GetBorder("TabActiveBorder") 
        self.normalborder = schemeobj.GetBorder("TabBorder") 

        if self.image:
            self.ClearImages() 
            self.image.SetImage(scheme().GetImage(self.imagename, False)) 
            self.AddImage( self.image.GetImage(), 2 ) 
            w, h = self.image.GetSize() 
            if self.contextlabel:
                w += 10
                self.image.SetPos( 10, 0 ) 
            self.SetSize( w + 4, h + 2 ) 
        else:
            wide, tall = self.GetSize() 
            contentWide, contentTall = self.GetContentSize() 

            wide = max(self.maxtabwidth, contentWide + 10)   # 10 = 5 pixels margin on each side
            if self.contextlabel:
                wide += 10
            self.SetSize(wide, tall) 

        if self.contextlabel:
            self.SetTextInset( 12, 0 ) 

    def ApplySettings(self, inResourceData):
        super(PageTab, self).ApplySettings(inResourceData) 

        pBorder = inResourceData.GetString("activeborder_override", "") 
        if pBorder:
            self.activeborder = scheme().GetIScheme(self.GetScheme()).GetBorder( pBorder ) 
        pBorder = inResourceData.GetString("normalborder_override", "") 
        if pBorder:
            self.normalborder = scheme().GetIScheme(self.GetScheme()).GetBorder( pBorder ) 

    def OnCommand(self, cmd):
        if cmd == 'ShowContextMenu':
            kv = KeyValues("OpenContextMenu") 
            #kv.SetPtr( "page", self.page )         # TODO
            #kv.SetPtr( "contextlabel", self.contextlabel ) # TODO 
            self.PostActionSignal( kv ) 
            return    
        super(PageTab, self).OnCommand( cmd ) 		

    def GetBorder(self, depressed, armed, selected, keyfocus):
        if self._active:
            return self.activeborder 
        return self.normalborder 

    def GetButtonFgColor(self):
        if self._active:
            return self._textColor 
        else:
            return self._dimTextColor 

    def SetActive(self, state):
        self._active = state 
        if state:
            self.SetZPos(100)
        else:
            self.SetZPos(0)
        self.InvalidateLayout() 
        self.Repaint() 

    def SetTabWidth(self, iWidth):
        self.maxtabwidth = iWidth 
        self.InvalidateLayout() 

    def CanBeDefaultButton(self):
        return False 

    #Fire action signal when mouse is pressed down instead  of on release.
    def OnMousePressed(self, code):
        # check for context menu open
        if not self.IsEnabled():
            return 
        
        if not self.IsMouseClickEnabled(code):
            return 
        
        if self.IsUseCaptureMouseEnabled():
            self.RequestFocus() 
            self.FireActionSignal() 
            self.SetSelected(True) 
            self.Repaint() 
            
            # lock mouse input to going to self button
            vgui_input().SetMouseCapture(self.GetVPanel()) 

    def OnMouseReleased(self, code):
        # ensure mouse capture gets released
        if self.IsUseCaptureMouseEnabled():
            vgui_input().SetMouseCapture(0)   

        # make sure the button gets unselected
        self.SetSelected(False) 
        self.Repaint() 

        if code == ButtonCode_t.MOUSE_RIGHT:
            kv = KeyValues("OpenContextMenu") 
            #kv.SetPtr( "page", self.page )         # TODO
            #kv.SetPtr( "contextlabel", self.contextlabel )     # TODO
            self.PostActionSignal( kv ) 

    def PerformLayout(self):
        super(PageTab, self).PerformLayout() 

        if self.contextlabel:
            w, h = GetSize(  ) 
            self.contextlabel.SetBounds( 0, 0, 10, h ) 

    # Defaults
    _textColor = Color()
    _dimTextColor = Color()   
    activeborder = None
    normalborder = None
            
class PropertySheet(EditablePanel):
    def __init__(self, parent, panelName, draggableTabsOrCombo=False):
        super(PropertySheet, self).__init__(parent, panelName)
        
        self.pages = []
        self.pagetabs = []
        
        #CPanelAnimationVarAliasType( int, m_iTabXIndent, "tabxindent", "0", "proportional_int" )
        #CPanelAnimationVarAliasType( int, self.tabxdelta, "tabxdelta", "0", "proportional_int" )
        #CPanelAnimationVarAliasType( int, m_iTabHeight, "tabheight", "28", "proportional_int" )
        #CPanelAnimationVarAliasType( int, m_iTabHeightSmall, "tabheight_small", "14", "proportional_int" )
        self.tabxindent = 0
        self.tabxdelta = 0
        self.tabheight = 28
        self.tabheightsmall = 14
        self.contextbutton = None
        
        self.RegMessageMethod( "TabPressed", self.OnTabPressed, 1, "panelname", DataType_t.DATATYPE_CONSTCHARPTR)
        self.RegMessageMethod( "TextChanged", self.OnTextChanged, 2, "panel", DataType_t.DATATYPE_PTR, "text", DataType_t.DATATYPE_CONSTWCHARPTR)
        self.RegMessageMethod( "OpenContextMenu", self.OnOpenContextMenu, 1, "params", DataType_t.DATATYPE_KEYVALUES)
        self.RegMessageMethod( "ApplyButtonEnable", self.OnApplyButtonEnable)
        self.RegMessageMethod( "DefaultButtonSet", self.OnDefaultButtonSet, 1, "button", DataType_t.DATATYPE_PTR)   # called when default button has been set
        self.RegMessageMethod( "CurrentDefaultButtonSet", self.OnCurrentDefaultButtonSet, 1, "button", DataType_t.DATATYPE_PTR)   # called when the current default button has been set
        self.RegMessageMethod( "FindDefaultButton", self.OnFindDefaultButton)

        if type(draggableTabsOrCombo) == bool:
            self._activePage = None 
            self._activeTab = None 
            self._tabWidth = 64 
            self._activeTabIndex = 0 
            self._showTabs = True 
            self._combo = None 
            self._tabFocus = False 
            self.pagetransitioneffecttime = 0.0
            self.smalltabs = False 
            self.tabfont = 0 
            self.draggabletabs = draggableTabsOrCombo 
            self.tabKV = None 

            if self.draggabletabs:
                self.SetDropEnabled( True ) 

            self.KBNavigationEnabled = True 
        else:
            self._activePage = None 
            self._activeTab = None 
            self._tabWidth = 64 
            self._activeTabIndex = 0 
            self._combo=draggableTabsOrCombo 
            self._combo.AddActionSignalTarget(self) 
            self._showTabs = False 
            self._tabFocus = False 
            self.pagetransitioneffecttime = 0.0
            self.smalltabs = False 
            self.tabfont = 0 
            self.draggabletabs = False 
            self.tabKV = None 

    def OnSizeChanged(self, wide, tall):
        super(PropertySheet, self).OnSizeChanged(wide, tall)
        self.InvalidateLayout()
        self.Repaint()
            
    def IsDraggableTab(self):
        """ ToolWindow uses self to drag tools from container to container by dragging the tab 
            Returns True on success, False on failure. """
        return self.draggabletabs 

    def SetDraggableTabs(self, state):
        self.draggabletabs = state 

    def SetSmallTabs(self, state):
        """ Lower profile tabs """
        self.smalltabs = state 
        if self.smalltabs:
            self.tabfont = scheme().GetIScheme( self.GetScheme() ).GetFont("DefaultVerySmall") 
        else:
            self.tabfont = scheme().GetIScheme( self.GetScheme() ).GetFont("Default") 
        for tab in self.pagetabs:
            assert( tab ) 
            tab.SetFont( self.tabfont ) 

    def IsSmallTabs(self):
        """ Returns True on success, False on failure. """
        return self.smalltabs 

    def ShowContextButtons(self, state):
        self.contextbutton = state 

    def ShouldShowContextButtons(self):
        """ Returns True on success, False on failure. """
        return self.contextbutton 

    def FindPage(self, page):
        for p in self.pages:
            if p.page == page:
                return i 
        return None

    def AddPage(self, page, title, imageName=None, bHasContextMenu= False):
        """ adds a page to the sheet """
        if not page:
            return 

        # don't add the page if we already have it
        if self.FindPage( page ) != None:
            return 

        hoverActivatePageTime = 250 
        tab = PageTab(self, page.GetName()+"_tab", title, imageName, self._tabWidth, page, self.contextbutton and bHasContextMenu, hoverActivatePageTime) 
        if self.draggabletabs:
            tab.SetDragEnabled( True ) 

        tab.SetFont( self.tabfont ) 
        if self._showTabs:
            tab.AddActionSignalTarget(self) 
        elif self._combo:
            self._combo.AddItem(title, None)
        if self.tabKV:
            tab.ApplySettings( self.tabKV ) 

        self.pagetabs.append(tab) 

        info = Page() 
        info.page = page 
        info.contextMenu = self.contextbutton and bHasContextMenu 
        
        self.pages.append( info ) 

        page.SetParent(self) 
        page.AddActionSignalTarget(self) 
        self.PostMessage(page, KeyValues("ResetData")) 

        page.SetVisible(False) 
        self.InvalidateLayout() 

        if not self._activePage:
            # first page becomes the active page
            self.ChangeActiveTab( 0 ) 
            if self._activePage:
                self._activePage.RequestFocus( 0 ) 

    def SetActivePage(self, page):
        # walk the list looking for self page
        index = self.FindPage( page ) 
        if index == None:
            return 

        self.ChangeActiveTab(index) 

    def SetTabWidth(self, pixels):
        self._tabWidth = pixels 
        self.InvalidateLayout() 

    def ResetAllData(self):
        """ reloads the data in all the property page """
        # iterate all the dialogs resetting them
        for p in self.pages:
            ipanel().SendMessage(p.page.GetVPanel(), KeyValues("ResetData"), self.GetVPanel()) 

    def ApplyChanges(self):
        """ Applies any changes made by the dialog """
        # iterate all the dialogs resetting them
        for p in self.pages:
            ipanel().SendMessage(ipanel.page.GetVPanel(), KeyValues("ApplyChanges"), self.GetVPanel()) 

    def GetActivePage(self):
        """ gets a pointer to the currently active page """
        return self._activePage 

    def GetActiveTab(self):
        """ gets a pointer to the currently active tab """
        return self._activeTab 

    def GetNumPages(self):
        """ returns the number of panels in the sheet """
        return len(self.pages) 

    def GetActiveTabTitle(self):
        """ returns the name contained in the active tab """
        if self._activeTab: 
            return self._activeTab.GetText() 
        return ""

    def GetTabTitle(self, i):
        """ returns the name contained in the active tab """
        if i < 0 and i > len(self.pagetabs):
            return None 

        return self.pagetabs[i].GetText() 
        
    def GetActivePageNum(self):
        """ Returns the index of the currently active page """
        for p in self.pages:
            if p.page == self._activePage:
                return i 
        return -1 

    def RequestFocus(self, direction):
        """ Forwards focus requests to current active page """
        if direction == -1 or direction == 0:
            if self._activePage:
                self._activePage.RequestFocus(direction) 
                self._tabFocus = False 
        else:
            if self._showTabs and self._activeTab:
                self._activeTab.RequestFocus(direction) 
                self._tabFocus = True   
            elif self._activePage:
                self._activePage.RequestFocus(direction) 
                self._tabFocus = False 
                
    def RequestFocusPrev(self, panel):
        """ moves focus back """
        if self._tabFocus or not self._showTabs or not self._activeTab:
            self._tabFocus = False 
            return super(PropertySheet, self).RequestFocusPrev(panel) 
        else:
            if self.GetVParent(): 
                self.PostMessage(self.GetVParent(), KeyValues("FindDefaultButton"))
            self._activeTab.RequestFocus(-1) 
            self._tabFocus = True 
            return True 

    def RequestFocusNext(self, panel):
        """ moves focus forward """
        if not self._tabFocus or not self._activePage:
            return super(PropertySheet, self).RequestFocusNext(panel) 
        else:
            if not self._activeTab: 
                return super(PropertySheet, self).RequestFocusNext(panel) 
            else:
                self._activePage.RequestFocus(1) 
                self._tabFocus = False 
                return True 

    def ApplySchemeSettings(self, schemeobj):
        """ Gets scheme settings """
        super(PropertySheet, self).ApplySchemeSettings(schemeobj) 

        # a little backwards-compatibility with old scheme files
        pBorder = schemeobj.GetBorder("PropertySheetBorder") 
        if pBorder == schemeobj.GetBorder("Default"):
            # get the old name
            pBorder = schemeobj.GetBorder("RaisedBorder") 

        self.SetBorder(pBorder) 
        self.pagetransitioneffecttime = float(schemeobj.GetResourceString("PropertySheet.TransitionEffectTime")) 

        if self.smalltabs:
            self.tabfont = schemeobj.GetFont("DefaultVerySmall") 
        else:
            self.tabfont = schemeobj.GetFont("Default") 

        if self.tabKV:
            for pt in self.pagetabs:
                pt.ApplySettings( self.tabKV ) 

        if not self.IsProportional():
            self.tabheight = scheme().GetProportionalNormalizedValueEx( self.GetScheme(), self.tabheight ) 
            self.tabheightsmall = scheme().GetProportionalNormalizedValueEx( self.GetScheme(), self.tabheightsmall ) 

    def ApplySettings(self, inResourceData):
        super(PropertySheet, self).ApplySettings(inResourceData) 

        pTabKV = inResourceData.FindKey( "tabskv" ) 
        if pTabKV:
            self.tabKV = KeyValues("tabkv") 
            pTabKV.CopySubkeys( self.tabKV ) 

        pTabWidthKV = inResourceData.FindKey( "tabwidth" ) 
        if pTabWidthKV:
            self._tabWidth = scheme().GetProportionalScaledValueEx(self.GetScheme(), pTabWidthKV.GetInt()) 
            for pt in self.pagetabs:
                pt.SetTabWidth( self._tabWidth ) 
                
        pTransitionKV = inResourceData.FindKey( "transition_time" ) 
        if pTransitionKV:
            self.pagetransitioneffecttime = pTransitionKV.GetFloat() 

    def PaintBorder(self):
        """ Paint our border specially, with the tabs in mind """
        border = self.GetBorder() 
        if not border:
            return 

        # draw the border, but with a break at the active tab
        px = 0
        py = 0
        pwide = 0 
        ptall = 0 
        if self._activeTab:
            px, py, pwide, ptall = self._activeTab.GetBounds() 
            ptall -= 1 

        # draw the border underneath the buttons, with a break
        wide, tall = self.GetSize() 
        border.Paint(0, py + ptall, wide, tall, IBorder.SIDE_TOP, px + 1, px + pwide - 1) 

    def PerformLayout(self):
        """ Lays out the dialog """
        super(PropertySheet, self).PerformLayout() 
        
        x, y, wide, tall = self.GetBounds() 
        if self._activePage:
            if self.IsSmallTabs():
                tabHeight = self.tabheightsmall
            else:
                tabHeight = self.tabheight 
                
            if self._showTabs:
                self._activePage.SetBounds(0, tabHeight, wide, tall - tabHeight) 
            else:
                self._activePage.SetBounds(0, 0, wide, tall ) 
            self._activePage.InvalidateLayout() 

        limit = len(self.pagetabs) 

        xtab = self.tabxindent 

        # draw the visible tabs
        if self._showTabs:
            for i in range(0, limit):
                if self.IsSmallTabs():
                    tabHeight = self.tabheightsmall-1
                else:
                    tabHeight = self.tabheight-1
                width, tall = self.pagetabs[i].GetSize() 
                if self.pagetabs[i] == self._activeTab:
                    # active tab is taller
                    self._activeTab.SetBounds(xtab, 2, width, tabHeight) 
                else:
                    self.pagetabs[i].SetBounds(xtab, 4, width, tabHeight - 2) 
                 
                self.pagetabs[i].SetVisible(True) 
                xtab += (width + 1) + self.tabxdelta 
        else:
            for i in range(0, limit):
                self.pagetabs[i].SetVisible(False) 

        # ensure draw order (page drawing over all the tabs except one)
        if self._activePage:
            self._activePage.MoveToFront() 
            self._activePage.Repaint() 
        if self._activeTab:
            self._activeTab.MoveToFront() 
            self._activeTab.Repaint() 
         
    def OnTabPressed(self, panelname):
        """ Switches the active panel """
        # look for the tab in the list
        for i, pt in enumerate(self.pagetabs):
            if pt.GetName() == panelname:
                # flip to the new tab
                self.ChangeActiveTab(i) 
                return    

    def GetPage(self, i): 
        """ returns the panel associated with index i 
            Input: the index of the panel to return  """
        if i<0 and i>len(self.pages):
            return None
        return self.pages[i].page 

    def DisablePage(self, title):
        """ disables page by name """
        self.SetPageEnabled(title, False) 

    def EnablePage(self, title): 
        """ enables page by name """
        SetPageEnabled(title, True) 

    def SetPageEnabled(self, title, state):
        """ enabled or disables page by name """
        for pt in self.pagetabs:
            if self._showTabs:
                tmp = spt.GetText() 
                if tmp == title:
                    pt.SetEnabled(state) 
            else:
                self._combo.SetItemEnabled(title,state) 

    def RemoveAllPages(self):
        c = len(self.pages) 
        for i in range(c-1, -1, -1):
            self.RemovePage( self.pages[ i ].page ) 

    def RemovePage(self, panel):
        """ deletes the page associated with panel """
        location = self.FindPage( panel ) 
        if location == None:
            return 

        # Since it's being deleted, don't animate!!!
        self.previousactivepage = None 
        self._activeTab = None 

        # ASSUMPTION = that the number of pages equals number of tabs
        if self._showTabs:
            self.pagetabs[location].RemoveActionSignalTarget( self ) 
         
        # now remove the tab
        tab  = self.pagetabs[ location ] 
        self.pagetabs.Remove( location ) 
        tab.MarkForDeletion() 
        
        # Remove from page list
        self.pages.Remove( location ) 

        # Unparent
        panel.SetParent( None ) 

        if self._activePage == panel:
            self._activePage = None 
            # if self page is currently active, backup to the page before self.
            self.ChangeActiveTab( max( location - 1, 0 ) )  

        self.PerformLayout() 

    def DeletePage(self, panel): 
        """ deletes the page associated with panel """
        assert( panel ) 
        self.RemovePage( panel ) 
        panel.MarkForDeletion() 

    def ChangeActiveTab(self, index):
        """ flips to the new tab, sending out all the right notifications 
            flipping to a tab activates the tab. """
        try:
            self.pages[index]
        except ValueError:
            self._activeTab = None 
            if len(self.pages) > 0:
                self._activePage = None 
                self.ChangeActiveTab( 0 )   
            return 

        if self.pages[index].page == self._activePage:
            if self._activeTab:
                self._activeTab.RequestFocus() 
            self._tabFocus = True 
            return 
            
        for p in self.pages:
            p.page.SetVisible( False )  

        self.previousactivepage = self._activePage 
        # notify old page
        if self._activePage:
            self.PostMessage(self._activePage, KeyValues("PageHide"), self.GetVPanel()) 
            msg = KeyValues("PageTabActivated") 
            #msg.SetPtr("panel", None)  # TODO
            self.PostMessage(self._activePage, msg, self.GetVPanel()) 
         
        if self._activeTab:
            #self._activeTabIndex=index 
            self._activeTab.SetActive(False) 

            # does the old tab have the focus?
            self._tabFocus = self._activeTab.HasFocus() 
        else: 
            self._tabFocus = False 

        # flip page
        self._activePage = self.pages[index].page 
        self._activeTab = self.pagetabs[index] 
        self._activeTabIndex = index 

        self._activePage.SetVisible(True) 
        self._activePage.MoveToFront() 
        
        self._activeTab.SetVisible(True) 
        self._activeTab.MoveToFront() 
        self._activeTab.SetActive(True) 

        if self._tabFocus:
            # if a tab already has focused,give the new tab the focus
            self._activeTab.RequestFocus() 
        else:
            # otherwise, give the focus to the page
            self._activePage.RequestFocus() 

        if not self._showTabs:
            self._combo.ActivateItemByRow(index) 

        self._activePage.MakeReadyForUse() 

        # transition effect
        # TODO: Support this in python
        # if self.pagetransitioneffecttime:
            # if self.previousactivepage.Get():
                # # fade out the previous page
                # GetAnimationController().RunAnimationCommand(self.previousactivepage, "Alpha", 0.0f, 0.0f, self.pagetransitioneffecttime / 2, AnimationController::INTERPOLATOR_LINEAR) 

            # # fade in the new page
            # self._activePage.SetAlpha(0) 
            # GetAnimationController().RunAnimationCommand(self._activePage, "Alpha", 255.0f, self.pagetransitioneffecttime / 2, self.pagetransitioneffecttime / 2, AnimationController::INTERPOLATOR_LINEAR) 
        # else
            # if self.previousactivepage.Get():
                # # no transition, just hide the previous page
                # self.previousactivepage.SetVisible(False) 
            # self._activePage.SetAlpha( 255 ) 

        # notify
        self._activePage.PostMessage(self._activePage, KeyValues("PageShow"), self.GetVPanel()) 

        msg = KeyValues("PageTabActivated") 
        #msg.SetPtr("panel", self._activeTab)       # TODO
        self.PostMessage(self._activePage, msg, self.GetVPanel()) 

        # tell parent
        self.PostActionSignal(KeyValues("PageChanged")) 

        # Repaint
        self.PerformLayout()
        self.InvalidateLayout() 
        self.Repaint() 

    def HasHotkey(self, key):
        """ Gets the panel with the specified hotkey, from the current page """
        if not self._activePage:
            return None 

        for i in range(0, self._activePage.GetChildCount()):
            hot = self._activePage.GetChild(i).HasHotkey(key) 
            if hot:
                return hot 
        return None 

    def OnOpenContextMenu(self, params):
        """ catches the opencontextmenu event """
        # tell parent
        kv = KeyValues(params) 
        self.PostActionSignal( kv ) 
        page = params.GetPtr( "page" )
        if page:
            self.PostMessage( page.GetVPanel(), KeyValues(params) ) 

    def OnKeyCodeTyped(self, code):
        """ Handle key presses, through tabs. """
        shift = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LSHIFT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RSHIFT)) 
        ctrl = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL)) 
        alt = (vgui_input().IsKeyDown(ButtonCode_t.KEY_LALT) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RALT)) 
        
        if ctrl and shift and alt and code == ButtonCode_t.KEY_B:
            # enable build mode
            ep = self.GetActivePage()
            if ep and isinstance(ed, EditablePanel):
                ep.ActivateBuildMode() 
                return 
                
        if self.IsKBNavigationEnabled():
            # for now left and right arrows just open or close submenus if they are there.
            if code == ButtonCode_t.KEY_RIGHT:
                self.ChangeActiveTab(self._activeTabIndex+1) 
            elif ButtonCode_t.KEY_LEFT:
                self.ChangeActiveTab(self._activeTabIndex-1) 
            else:
                super(PropertySheet, self).OnKeyCodeTyped(code)
        else:
            super(PropertySheet, self).OnKeyCodeTyped(code) 

    def OnTextChanged(self, panel, wszText):
        """ Called by the associated combo box (if in that mode), changes the current panel """
        if panel == self._combo:
            for pt in self.pagetabs:
                tabText = pt.GetText() 
                if wszText == tabText:
                    self.ChangeActiveTab(i) 

    def OnCommand(self, command):
        # propogate the close command to our parent
        if command == "Close" and self.GetVParent():
            self.CallParentFunction(KeyValues("Command", "command", command)) 

    def OnApplyButtonEnable(self):
        # tell parent
        self.PostActionSignal(KeyValues("ApplyButtonEnable")) 	

    def OnCurrentDefaultButtonSet(self, defaultButton):
        # forward the message up
        if self.GetVParent():
            msg = KeyValues("CurrentDefaultButtonSet") 
            #msg.SetInt("button", ivgui().PanelToHandle( defaultButton ) )  # TODO
            self.PostMessage(self.GetVParent(), msg) 

    def OnDefaultButtonSet(self, defaultButton):
        # forward the message up
        if self.GetVParent():
            msg = KeyValues("DefaultButtonSet") 
            #msg.SetInt("button", ivgui().PanelToHandle( defaultButton ) )  # TODO
            self.PostMessage(self.GetVParent(), msg) 

    def OnFindDefaultButton(self):
        if self.GetVParent():
            self.PostMessage(self.GetVParent(), KeyValues("FindDefaultButton")) 

    def PageHasContextMenu(self, page):
        pageNum = self.FindPage( page ) 
        if pageNum == None:
            return False 
        return self.pages[ pageNum ].contextMenu 

    def OnPanelDropped(self, msglist):
        if len(msglist) != 1:
            return 

        sheet = IsDroppingSheet( msglist ) 
        if not sheet:
            # Defer to active page
            if self._activePage and self._activePage.IsDropEnabled():
                return self._activePage.OnPanelDropped( msglist ) 
            return  

        data = msglist[ 0 ] 

        page = data.GetPtr( "propertypage" )
        title = data.GetString( "tabname", "" ) 
        if not page or not sheet:
            return 

        # Can only create if sheet was part of a ToolWindow derived object
        #tw = dynamic_cast< ToolWindow * >( sheet.GetParent() ) 
        tw = None
        if tw:
            factory = tw.GetToolWindowFactory() 
            if factory:
                showContext = sheet.PageHasContextMenu( page ) 
                sheet.RemovePage( page ) 
                if sheet.GetNumPages() == 0:
                    tw.MarkForDeletion() 

                self.AddPage( page, title, None, showContext ) 

    def IsDroppable(self, msglist):
        if not self.draggabletabs:
            return False 

        if len(msglist) != 1:
            return False 

        mx, my = vgui_input().GetCursorPos() 
        mx, my = self.ScreenToLocal(mx, my) 

        if self.IsSmallTabs():
            tabHeight = self.tabheightsmall
        else:
            tabHeight = self.tabheight
        if my > tabHeight:
            return False 

        sheet = IsDroppingSheet( msglist ) 
        if not sheet:
            return False 
        
        if sheet == self:
            return False 
        return True 

    # Mouse is now over a droppable panel
    def OnDroppablePanelPaint(self, msglist, dragPanels):
        # Convert self panel's bounds to screen space
        w, h = self.GetSize() 

        if self.IsSmallTabs():
            tabHeight = self.tabheightsmall
        else:
            tabHeight = self.tabheight
        h = tabHeight + 4 

        x = y = 0 
        x, y = self.LocalToScreen(x, y) 

        surface().DrawSetColor( self.GetDropFrameColor() ) 
        # Draw 2 pixel frame
        surface().DrawOutlinedRect( x, y, x + w, y + h ) 
        surface().DrawOutlinedRect( x+1, y+1, x + w-1, y + h-1 ) 

        if not self.IsDroppable( msglist ):
            return 

        if not self._showTabs:
            return 

        # Draw a fake new tab...
        x = 0 
        y = 2 
        w = 1 
        h = tabHeight 

        last = len(self.pagetabs) 
        if last != 0:
            self.pagetabs[ last - 1 ].GetBounds( x, y, w, h ) 

        # Compute left edge of "fake" tab
        x += ( w + 1 ) 

        # Compute size of new panel
        data = msglist[ 0 ] 
        text = data.GetString( "tabname", "" ) 
        assert( text ) 

        fakeTab = PageTab( self, "FakeTab", text, None, self._tabWidth, None, False ) 
        fakeTab.SetBounds( x, 4, w, tabHeight - 4 ) 
        fakeTab.SetFont( self.tabfont ) 
        fakeTab.MakeReadyForUse()
        fakeTab.Repaint() 
        surface().SolveTraverse( fakeTab.GetVPanel(), True ) 
        surface().PaintTraverse( fakeTab.GetVPanel() ) 
        fakeTab.DeletePanel()
     
    def SetKBNavigationEnabled(self, state):
        self.KBNavigationEnabled = state 
     
    def IsKBNavigationEnabled(self):
        """ Returns True on success, False on failure. """
        return self.KBNavigationEnabled 
     
