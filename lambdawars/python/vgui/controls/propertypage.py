from vgui.controls import EditablePanel
from input import ButtonCode_t

class PropertyPage(EditablePanel):
    def __init__(self, parent, panelname):
        super(PropertyPage, self).__init__(parent, panelname)
        
        # Called when page is loaded.  Data should be reloaded from document into controls.
        self.RegMessageMethod( "ResetData", self.OnResetData)

        # Called when the OK / Apply button is pressed.  Changed data should be written into document.
        self.RegMessageMethod( "ApplyChanges", self.OnApplyChanges)

        # called when the page is shown/hidden
        self.RegMessageMethod( "PageShow", self.OnPageShow)
        self.RegMessageMethod( "PageHide", self.OnPageHide)

        # called to be notified of the tab button used to Activate this page
        # if overridden this must be chained back to
        self.RegMessageMethod( "PageTabActivated", self.OnPageTabActivated, 1, "panel", DataType_t.DATATYPE_PTR)      
        
    def OnResetData(self):
        """ Called when page is loaded.  Data should be reloaded from document into controls. """
        pass
        
    def OnApplyChanges(self):
        """ Called when the OK / Apply button is pressed.  Changed data should be written into document. """
        pass

    def OnPageShow(self):
        """ Designed to be overriden """
        pass

    def OnPageHide(self):
        """ Designed to be overriden """
        pass
        
    def OnPageTabActivated(self, pageTab):
        self._pageTab = pageTab 

    def OnKeyCodeTyped(self, code):
        # left and right only get propogated to parents if our tab has focus
        if code == ButtonCode_t.KEY_RIGHT: 
            if self._pageTab != None and self._pageTab.HasFocus():
                super(PropertyPage, self).OnKeyCodeTyped(code) 
        elif ButtonCode_t.KEY_LEFT:
            if self._pageTab != None and self._pageTab.HasFocus():
                super(PropertyPage, self).OnKeyCodeTyped(code) 
        else:
            super(PropertyPage, self).OnKeyCodeTyped(code) 

    def SetVisible(self, state):
        # TODO
        #if self.IsVisible() and not state:
            # if we're going away and we have a current button, get rid of it
        #    if self.GetFocusNavGroup().GetCurrentDefaultButton():
        #        self.GetFocusNavGroup().SetCurrentDefaultButton(None) 

        super(PropertyPage, self).SetVisible(state) 
