from vgui.controls import Panel
from vgui import surface, WarsVGUIScreen
from utils import MainViewUp, MainViewRight, MainViewForward
from vmath import QAngle, VectorAngles
from te import ClientSideEffect, BITS_CLIENTEFFECT_POSTSCREEN

class UnitBar(Panel):
    def __init__(self, barcolor, fillcolor, outlinecolor):
        super(UnitBar, self).__init__()
    
        self.barcolor = barcolor
        self.fillcolor = fillcolor
        self.outlinecolor = outlinecolor
        
    def Paint(self):
        s = surface()
        barfilled = int(self.weight * self.GetTall())
    
        # draw bar part
        s.DrawSetColor( self.barcolor )
        s.DrawFilledRect(
            0, 
            0, 
            self.GetWide(), 
            barfilled
        )

        # Draw filler part
        s.DrawSetColor( self.fillcolor )
        s.DrawFilledRect(
            0, 
            barfilled, 
            self.GetWide(), 
            self.GetTall()
        )

        # draw the outline of the healthbar
        s.DrawSetColor( self.outlinecolor )
        s.DrawOutlinedRect(
            0, 
            0, 
            self.GetWide(), 
            self.GetTall() 
        )
        
    weight = 1.0
    
class UnitBarRenderer(ClientSideEffect):
    def __init__(self, screen):
        super(UnitBarRenderer, self).__init__('UnitBarRenderer', BITS_CLIENTEFFECT_POSTSCREEN)
        self.screen = screen
    def Draw(self, frametime):
        if not self.IsActive():
            return
        self.screen.Draw()
        
class BaseScreen(WarsVGUIScreen):
    def __init__(self):
        super(BaseScreen, self).__init__()

        self.renderer = UnitBarRenderer(self)
        
    def Shutdown(self):
        self.renderer.Destroy()
        self.renderer.screen = None
        self.renderer = None
        self.SetPanel(None)
        
class UnitBarScreen(BaseScreen):
    def __init__(self, unit, barcolor, fillcolor, outlinecolor, worldsizey=3.0, worldbloatx=0.0, offsety=0.0, offsetz=0.0, panel=None):
        ''' Initializes a bar drawn in screen for a unit.
        
            Args:
                unit(entity): The unit
                barcolor(Color): Color of bar
                fillcolor(Color): The color of the remaining part of the bar
                outlinecolor(Color): The outline color of the bar
                
            Kwargs:
                worldsizey(float): Y size of bar in Hammer units
                worldbloatx(float): Additional x width of bar in Hammer units
                offsety(float): Screen offset y, for showing multiple bars
                offsetz(float): Additional z origin offset of bar to unit
                panel(Panel): Panel?
        '''
        super(UnitBarScreen, self).__init__()

        if not panel: 
            panel = UnitBar(barcolor, fillcolor, outlinecolor)
        self.SetPanel(panel)
        self.unit = unit.GetHandle()
        self.offsety = offsety
        self.worldsizey = worldsizey
        self.worldbloatx = worldbloatx
        self.offsetz = offsetz + unit.barsoffsetz
        
        mins = self.unit.WorldAlignMins()
        maxs = self.unit.WorldAlignMaxs()
    
        wide = maxs.x - mins.x + 8.0 + self.worldbloatx
        self.SetWorldSize(self.worldsizey, wide)

        #scaleup = 640/wide
        #self.GetPanel().SetBounds(0, 0, int(3*scaleup), int((maxs.x - mins.x + 8.0)*scaleup))
        self.GetPanel().SetBounds(0, 0, 640, 1024)

    def Draw(self):
        maxs = self.unit.WorldAlignMaxs()
        
        origin = self.unit.GetAbsOrigin() + MainViewRight()*(self.GetHeight()/2)
        origin.z += maxs.z + self.offsetz
        origin += MainViewUp()*(8.0 + self.offsety)
        self.SetOrigin(origin)
        
        angles = QAngle()
        dir = MainViewUp()
        VectorAngles(dir, angles)
        self.SetAngles(angles)
    
        super(UnitBarScreen, self).Draw()
        
                