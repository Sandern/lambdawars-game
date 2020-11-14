from srcbase import Color
from vgui import scheme
from vgui.controls import Frame, Button, RichText
from utils import ScreenWidth, ScreenHeight

class Notification(Frame):
    def __init__(self, title, notification):
        super(Notification, self).__init__(None, 'Notification')
        
        self.myref = self # Ensure we are not destroyed
        
        self.SetTitle(title, True)
        self.SetSizeable(False)
        self.SetMoveable(False)
        
        self.SetScheme(scheme().LoadSchemeFromFile("resource/SourceScheme.res", "SourceScheme"))
        
        # The notification
        self.content = RichText(self, "Content")
        self.content.SetMaximumCharCount(-1)
        self.content.SetVisible(True)
        self.content.SetEnabled(True) 
        self.content.SetVerticalScrollbar(False)
        
        self.content.SetText(notification)
        
        self.close = Button(self, 'Close', 'Close')
        self.close.SetCommand('Close')
        self.close.AddActionSignalTarget(self)
        
        self.DoModal()
        
    def ApplySchemeSettings(self, schemeobj):
        super(Notification, self).ApplySchemeSettings(schemeobj)
        
        self.content.SetBgColor( schemeobj.GetColor("ClayBG", Color(255, 255, 255 ) ) )
        
    def PerformLayout(self):
        super(Notification, self).PerformLayout()
        
        self.SetPos( ScreenWidth()/2 - scheme().GetProportionalScaledValueEx( self.GetScheme(), 100 ),
            ScreenHeight()/2 - scheme().GetProportionalScaledValueEx( self.GetScheme(), 50 ) )
        self.SetSize( scheme().GetProportionalScaledValueEx( self.GetScheme(), 200 ),
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 100 ) )

        self.content.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 190),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 70) )
        self.content.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 5),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 15) ) 
                              
        self.close.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 30),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 10) )
        self.close.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 165),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 85) ) 
                              
    def OnClose(self):
        super(Notification, self).OnClose()
        
        # Allow removal
        self.myref = None
        