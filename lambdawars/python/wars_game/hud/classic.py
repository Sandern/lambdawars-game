from srcbase import Color, HIDEHUD_STRATEGIC
import math

from entities import C_HL2WarsPlayer
from gameinterface import engine
from vgui import cursors, images, scheme, surface, AddTickSignal, vgui_input, HudIcons, CHudElement, GetClientMode
from vgui.controls import Panel, Label, BitmapButton

from core.resources import resources
from core.factions import GetFactionInfo
from core.hud import HudInfo
from core.units import unitpopulationcount, GetMaxPopulation

# Hud default main parts
from core.hud import BaseHudAbilities, HudUnitsContainer, BaseHudInfo, BaseHudMinimap, BaseHudGroups, BaseHudUnits

class HudUnits(BaseHudUnits):
    unitbuttontexture = 'hud_classic_unitbutton'

class HudClassic(CHudElement, Panel):
    def __init__(self):
        CHudElement.__init__(self, "HudClassic")
        Panel.__init__(self, GetClientMode().GetViewport(), "HudClassic")
        self.SetHiddenBits(HIDEHUD_STRATEGIC)
        
        self.EnableSBuffer(True)
        self.SetProportional(True)
        self.SetPaintBackgroundEnabled(True)
        self.SetKeyBoardInputEnabled(False)
        self.SetMouseInputEnabled(True)

        # Create sub panels
        self.infopanel = self.infopanelcls()
        self.minimap = self.minimapcls(GetClientMode().GetViewport())
        self.minimap.SetVisible(True)
        self.unitpanel = self.unitpanelcls(self, self.infopanel)
        self.unitpanel.defaultunitpanelclass = HudUnits
        self.unitpanel.SetVisible(True)
        self.abilitypanel = self.abilitypanelcls(self, self.infopanel)
        self.abilitypanel.SetVisible(True)
        self.grouppanel = self.grouppanelcls(self)
        self.grouppanel.SetVisible(True)
        
        # ------------ create labels
        # unit counter
        self.amountunits = Label(self,"UnitsAmount","")
        self.amountunits.MakeReadyForUse()
        self.amountunits.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
        self.amountunits.SetBgColor(Color(0,0,0,0)) #Translucent BG
        self.amountunits.SetPaintBackgroundEnabled(False)
        self.amountunits.SetPaintBorderEnabled(False)
        self.amountunits.SetContentAlignment(Label.a_west)

        # resource counter
        self.amountresources = Label(self,"ResourcesAmount","")
        self.amountresources.MakeReadyForUse()
        self.amountresources.SetScheme(scheme().LoadSchemeFromFile("resource/ClientScheme.res", "ClientScheme"))
        self.amountresources.SetBgColor(Color(0,0,0,0))	#Translucent BG
        self.amountresources.SetPaintBackgroundEnabled(False)
        self.amountresources.SetPaintBorderEnabled(False)
        self.amountresources.SetContentAlignment(Label.a_west)

        self.InitButtons()
        AddTickSignal(self.GetVPanel(), 350)
        
    def UpdateOnDelete(self):
        # Delete panels that are not our children
        # otherwise they are still around when the new hud is created
        if self.minimap:
            self.minimap.DeletePanel()
            self.minimap = None
        
    def InitButtons(self):
        # Retrieve the images for the buttons
        self.imagemenu = [ images.GetImage("VGUI/buttons/mm_button.vmt"),
                           images.GetImage("VGUI/buttons/mm_button_onOver.vmt"),
                           images.GetImage("VGUI/buttons/mm_button_onPressed.vmt") ]
        self.imageobj = [ images.GetImage("VGUI/buttons/obj_button.vmt"),
                           images.GetImage("VGUI/buttons/obj_button_onOver.vmt"),
                           images.GetImage("VGUI/buttons/obj_button_onPressed.vmt") ]
        self.imagemp3 = [ images.GetImage("VGUI/buttons/mp3player_button.vmt"),
                           images.GetImage("VGUI/buttons/mp3player_button_onOver.vmt"),
                           images.GetImage("VGUI/buttons/mp3player_button_onPressed.vmt") ]

        # Create the buttons
        self.main_menu = self.CreateButton('main_menu', self.imagemenu)
        self.obj_button = self.CreateButton('obj_button', self.imageobj)
        self.mp3_button = self.CreateButton('mp3_button', self.imagemp3)
        
    def CreateButton(self, command, images):
        color = Color(255, 255, 255, 255)
        b = BitmapButton( self, command, "") 
        b.SetImage( BitmapButton.BUTTON_ENABLED, images[0], color)
        b.SetImage( BitmapButton.BUTTON_ENABLED_MOUSE_OVER, images[1], color)
        b.SetImage( BitmapButton.BUTTON_PRESSED, images[2], color)
        b.SetVisible( True )
        b.SetPaintBackgroundEnabled( False )
        b.SetPaintBorderEnabled( False )
        b.SetParent(self)
        b.AddActionSignalTarget(self)
        b.SetCommand(command)
        return b
        
    def OnTick(self):
        super(HudClassic, self).OnTick()
        
        if not self.IsActive():
            return

        self.UpdateStats()

    def UpdateStats(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        # update amount of units
        ownernumber = player.GetOwnerNumber()
        pop = unitpopulationcount[ownernumber]
        maxpop = GetMaxPopulation(ownernumber)
        self.amountunits.SetText('%s / %s' % (pop, maxpop))
        if pop > maxpop:
            self.amountunits.SetFgColor(Color(255, 0, 0, 255))
        else:
            self.amountunits.SetFgColor(Color(255, 255, 255, 255))
            
        faction = player.GetFaction()
        info = GetFactionInfo(faction)
        if not info or not info.resources:
            self.amountresources.SetText( "-" )
            return

        # update amount of resources
        amountResources = resources[ownernumber][info.resources[0]]
        self.amountresources.SetText(str(amountResources))

    def ApplySchemeSettings(self, schemeobj):
        super(HudClassic, self).ApplySchemeSettings(schemeobj)
        
        self.SetBgColor(Color(0,0,0,0))
        
        # set fonts and colors or labels
        #font = schemeobj.GetFont("InterfaceInfoFont", self.IsProportional() )
        #self.amountunits.SetFont( font )
        #self.amountresources.SetFont( font )

        #self.amountunits.SetFgColor(self.GetSchemeColor("hudinterface.TextColor", schemeobj))
        #self.amountresources.SetFgColor(self.GetSchemeColor("hudinterface.TextColor", schemeobj))
        
    def PerformLayout(self):
        super(HudClassic, self).PerformLayout()
        
        # save the screen size and get the aspect ratio
        self.screenwidth, self.screenheight = surface().GetScreenSize()
        self.aspect = self.screenwidth / float(self.screenheight)
        
        # Get the correct background texture
        data = self.normalscreenvalues
        if self.aspect >= 1.45:
            data = self.widescreenvalues
        
        self.background = HudIcons().GetIcon(data['texture'])
        self.FlushSBuffer()
        
        tex_width = self.background.Width()
        tex_height = self.background.Height()
        
        # Set our panel size ( scale correctly with the background texture )
        size_fix = 1.0
        if self.background.Width() != 0:
            size_fix = self.screenwidth / float(self.background.Width())
        size_y = int(size_fix * self.background.Height())

        self.SetPos( 0, self.screenheight - size_y )
        self.SetSize( self.screenwidth, size_y )
        w, h = self.GetSize()

        # Position/Size minimap
        self.minimap.SetPos( int(( data['minimap_pos'] / float(tex_width) ) * w), 
            int(( data['minimap_posy'] / float(tex_height) ) * h) + self.screenheight - h )
        self.minimap.SetSize( int(( data['minimap_sizex'] / float(tex_width) )  * w), 
            int(( data['minimap_sizey'] / float(tex_height) ) * h) )
        self.minimap_absmidx = int((( data['minimap_pos'] / float(tex_width) ) * w) + 0.5*(( data['minimap_sizex'] / float(tex_width) )  * w))
        self.minimap_absmidy = int(((( data['minimap_posy'] / float(tex_height) ) * h) + self.screenheight - h ) + 0.5*(( data['minimap_sizey'] / float(tex_height) ) * h) )
        self.minimap_hsize = int(0.5*(( data['minimap_sizex'] / float(tex_width) )  * w))
            
        # Position/Size unit panel
        self.unitpanel.SetPos( int(( data['unit_posx'] / float(tex_width) ) * w), 
            int(( data['unit_posy'] / float(tex_height) ) * h) )
        self.unitpanel.SetSize( int(( data['unit_sizex'] / float(tex_width) )  * w), 
            int(( data['unit_sizey'] / float(tex_height) ) * h) )

        # Position/Size groups panel
        self.grouppanel.SetPos( int(( data['groups_posx'] / float(tex_width) ) * w), 
            int(( data['groups_posy'] / float(tex_height) ) * h) )
        self.grouppanel.SetSize( int(( data['groups_sizex'] / float(tex_width) )  * w), 
            int(( data['groups_sizey'] / float(tex_height) ) * h) )
            
        # -- set size and pos labels
        self.amountunits.SetPos( int(( data["AmountUnits_posx"] / float(tex_width) ) * w), 
            int(( data["AmountUnits_posy"] / float(tex_height) ) * h) )
        self.amountunits.SetSize( scheme().GetProportionalScaledValueEx( self.GetScheme(), 45 ), 
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 20 ) )

        self.amountresources.SetPos( int(( data["AmountResources_posx"] / float(tex_width) ) * w), 
            int(( data["AmountResources_posy"] / float(tex_height) ) * h) )
        self.amountresources.SetSize( scheme().GetProportionalScaledValueEx( self.GetScheme(), 45 ), 
            scheme().GetProportionalScaledValueEx( self.GetScheme(), 20 ) )


        # Position/Size ability panel
        self.abilitypanel.SetPos( int(( data['ability_posx'] / float(tex_width) ) * w), 
            int(( data['ability_posy'] / float(tex_height) ) * h) )
        self.abilitypanel.SetSize( int(( data['ability_sizex'] / float(tex_width) )  * w), 
            int(( data['ability_sizey'] / float(tex_height) ) * h) )
            
        # Info panel
        self.infopanel.mainhud_tall = size_y
        self.infopanel.iswidescreen = (self.aspect >= 1.45)
        self.infopanel.PerformLayout()
            
        # Buttons
        self.main_menu.SetPos( int(( data["mainmenu_posx"] / float(tex_width) ) * w), 
            int(( data["mainmenu_posy"] / float(tex_height) )  * h) )
        self.main_menu.SetSize( int(( data["mainmenu_sizex"] / float(tex_width) )  * w), 
            int(( data["mainmenu_sizey"] / float(tex_height) )  * h) )

        self.obj_button.SetPos( int(( data["objbutton_posx"] / float(tex_width) ) * w), 
            int(( data["objbutton_posy"] / float(tex_height) ) * h) )
        self.obj_button.SetSize( int(( data["objbutton_sizex"] / float(tex_width) )  * w), 
            int(( data["objbutton_sizey"] / float(tex_height) ) * h) )

        self.mp3_button.SetPos( int(( data["mp3button_posx"] / float(tex_width) ) * w), 
            int(( data["mp3button_posy"] / float(tex_height) ) * h) )
        self.mp3_button.SetSize( int(( data["mp3button_sizex"] / float(tex_width) ) * w), 
            int(( data["mp3button_sizey"] / float(tex_height) ) * h) )

    def PaintBackground(self):
        super(HudClassic, self).PaintBackground()
        
        if self.background:
            w, h = self.GetSize()
            self.background.DrawSelf(0, 0, w, h, Color(255, 255, 255, 255))
        
    def SetVisible(self, state):
        if self.minimap:
            self.minimap.SetVisible(state)
        super(HudClassic, self).SetVisible(state)
        
    def OnMousePressed(self, code):
        # The minimap is placed behind the main hud. See if we actually wanted to press the minimap
        # Note: the minimap will use MouseCapture for the other OnMouse... methods
        x, y = vgui_input().GetCursorPos()
        if math.sqrt( math.pow(x-self.minimap_absmidx, 2) + math.pow(y-self.minimap_absmidy, 2) ) < self.minimap_hsize:
            self.minimap.OnMousePressed(code)
            return 

    def OnCommand(self, command):
        if command == 'main_menu':
            engine.ClientCommand('gameui_activate"')
        elif command == 'obj_button':
            pass    # For decoration
        elif command == 'mp3_button':
            engine.ClientCommand('mp3')
        else:
            super(HudClassic, self).OnCommand(command)
            
    # Default variables
    background = None
    minimap_absmidx = 0
    minimap_absmidy = 0
    minimap_hsize = 0
    aspect = 16.0/9.0
        
    # Settings. Override in baseclasses
    defaultcursor = "resource/arrows/default_cursor.cur"
    
    minimapcls = BaseHudMinimap
    unitpanelcls = HudUnitsContainer
    abilitypanelcls = BaseHudAbilities
    infopanelcls = BaseHudInfo
    grouppanelcls = BaseHudGroups
    
    # Settings
    normalscreenvalues = {
        'texture' : 'hud_panel_old',
        
        # Minimap
        'minimap_pos'               : 24,
        'minimap_posy'              : 19,
        'minimap_sizex'             : 184,
        'minimap_sizey'             : 184,
        
        # Unit panel
        'unit_posx'                 : 365,
        'unit_posy'                 : 68,
        'unit_sizex'                : 280,
        'unit_sizey'                : 140,

        # Ability panel
        'ability_posx'              : 802,
        'ability_posy'              : 17,
        'ability_sizex'             : 204,
        'ability_sizey'             : 153,
        
        # Group panel
        'groups_posx'               : 245,
        'groups_posy'               : 28,
        'groups_sizex'              : 100,
        'groups_sizey'              : 25,
        
        # Stat labels
        "AmountUnits_posx"          : 280,
        "AmountUnits_posy"          : 183,

        "AmountResources_posx"      : 274,
        "AmountResources_posy"      : 103,
        
        # Buttons
        "mainmenu_posx"	            : 246,
        "mainmenu_posy"	            : 59,
        "mainmenu_sizex"            : 100,
        "mainmenu_sizey"            : 13,

        "objbutton_posx"            : 246,
        "objbutton_posy"            : 72,
        "objbutton_sizex"           : 100,
        "objbutton_sizey"           : 13,
        
        "mp3button_posx"            : 246,
        "mp3button_posy"            : 85,
        "mp3button_sizex"           : 100,
        "mp3button_sizey"           : 13,       
    }

    widescreenvalues = {
        'texture' : 'hud_panel_wide_old',
        
        # Minimap
        'minimap_pos'               : 63,
        'minimap_posy'              : 17,
        'minimap_sizex'             : 152,
        'minimap_sizey'             : 152,
        
        # Unit panel
        'unit_posx'                 : 348,
        'unit_posy'                 : 56,
        'unit_sizex'                : 220,
        'unit_sizey'                : 110,
        
        # Ability panel
        'ability_posx'              : 709,
        'ability_posy'              : 14,
        'ability_sizex'             : 171,
        'ability_sizey'             : 128,
        
        # Group panel
        'groups_posx'               : 240,
        'groups_posy'               : 25,
        'groups_sizex'              : 171,
        'groups_sizey'              : 20,
        
        # Stat labels
        "AmountUnits_posx"          : 272,
        "AmountUnits_posy"          : 152,

        "AmountResources_posx"      : 270,
        "AmountResources_posy"      : 87,
        
        # Buttons
        "mainmenu_posx"             : 248,
        "mainmenu_posy"             : 48,
        "mainmenu_sizex"            : 80,
        "mainmenu_sizey"            : 10,

        "objbutton_posx"            : 248,
        "objbutton_posy"            : 58,
        "objbutton_sizex"           : 80,
        "objbutton_sizey"           : 10,
        
        "mp3button_posx"            : 248,
        "mp3button_posy"            : 68,
        "mp3button_sizex"           : 80,
        "mp3button_sizey"           : 10,
    }
        
class ClassicHudInfo(HudInfo):
    name = 'classic_hud'
    cls = HudClassic
