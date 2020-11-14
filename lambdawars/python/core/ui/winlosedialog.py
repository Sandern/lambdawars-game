from srcbase import Color
from vgui import GetClientMode, scheme, AddTickSignal
from vgui.controls import Panel, Label, Button
from utils import ScreenWidth
from gameinterface import engine

class WinLoseDialog(Panel):
    def __init__(self, winners, losers, iswinner):
        super().__init__(GetClientMode().GetViewport(), "WinLoseDialog")
       
        schemeobj = scheme().LoadSchemeFromFile("resource/SourceScheme.res", "SourceScheme")
        self.SetScheme(schemeobj)
        
        self.maintext = Label(self, "MainText", '')
        if iswinner:
            self.maintext.SetText('You Won!')
        else:
            self.maintext.SetText('LOSERRRR!')
            
        winnerstr = 'winners: %s' % (', '.join(winners))
        loserstr = 'losers: %s' % (', '.join(losers))
            
        self.winners = Label(self, "Winners", winnerstr)
        self.losers = Label(self, "Losers", loserstr)
            
        self.selfref = self
        AddTickSignal(self.GetVPanel(), 15000)
        
    def OnTick(self):
        self.DeletePanel()
        self.selfref = None
            
    def ApplySchemeSettings(self, schemeobj):
        super().ApplySchemeSettings(schemeobj)
        hfontsmall = schemeobj.GetFont( "FriendsSmall" )
        hfontmedium = schemeobj.GetFont( 'HeadlineLarge' )
        
        self.SetBorder(None)#schemeobj.GetBorder("ButtonBorder"))
        self.SetBgColor(Color(0,0,0,0))#schemeobj.GetColor("TransparentGray", Color(255, 255, 255 )))
        
        self.maintext.SetFont(hfontmedium)
        self.winners.SetFont(hfontmedium)
        self.losers.SetFont(hfontmedium)
        
    def PerformLayout(self):
        super().PerformLayout()
        
        wide = scheme().GetProportionalScaledValueEx( self.GetScheme(), 200 )
        self.SetPos( int(ScreenWidth() / 2 - wide / 2),
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 50 ) )
        self.SetSize( wide,
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 50 ) )
            
        inset = scheme().GetProportionalScaledValueEx( self.GetScheme(), 20 )
        self.maintext.SetPos( inset, 
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 5 ) )
        self.maintext.SetSize( wide - inset * 2,
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 10 ) )
            
        self.winners.SetPos( inset, 
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 22 ) )
        self.winners.SetSize( wide - inset * 2,
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 5 ) )
        self.losers.SetPos( inset, 
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 30 ) )
        self.losers.SetSize( wide - inset * 2,
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 5 ) )
            