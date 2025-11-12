"""Controller for the CEF top menu bar displayed in the game viewport.

Initialises the top bar HTML, registers button callbacks, and relays button
presses back into Python handlers provided by gamerules or other systems.
"""

from cef import viewport, CefPanel
from gamerules import gamerules

class CefTopBar(CefPanel):
    """Manages the top bar CEF UI, handling button registration and events.

    Creates the CEF binding for the top bar, keeps a Python-side registry of
    button handlers, and invokes registered callbacks when HTML buttons fire
    events.
    """
    name = 'topbar'
    htmlfile = 'ui/viewport/wars/topbar.html'
    classidentifier = 'viewport/hud/wars/TopBar'
    cssfiles = CefPanel.cssfiles + ['wars/topbar.css']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.handlers = {}
        
    def SetupFunctions(self):
        super().SetupFunctions()
        
    def OnLoaded(self):
        super().OnLoaded()
        
        self.handlers.clear()

        self.CreateFunction('onButtonPressed', False)
        
        if hasattr(gamerules, 'SetupTopBar'):
            gamerules.SetupTopBar()
        
        self.visible = True
        
    def InsertButton(self, name, text='', imagepath='', order=0, handler=None, floatright=False):
        self.Invoke("insertButton", [name, text, imagepath, order, floatright])
        self.handlers[name] = handler

    def onButtonPressed(self, methodargs, callbackid):
        buttonname = methodargs[0]
        handler = self.handlers.get(buttonname, None)
        if handler:
            handler(self)