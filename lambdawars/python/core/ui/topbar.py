'''
Controller code for top menu bar in the game view port.
'''

from cef import viewport, CefPanel
from gamerules import gamerules

class CefTopBar(CefPanel):
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