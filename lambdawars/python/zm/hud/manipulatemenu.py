from srcbase import KeyValues
from vgui import scheme, AddTickSignal, RemoveTickSignal
from vgui.controls import Frame, Button, Label
from entities import C_BasePlayer
from gameinterface import engine, ConVar, FCVAR_ARCHIVE

from core.resources import resources

from convars import *
from ..shared import *

class ManipulateMenu(Frame):
    activemanipulate = None

    def __init__(self):
        super(ManipulateMenu, self).__init__(None, 'manipulate')

        self.jumpkey = -1 # this is looked up in Activate()
        #m_iScoreBoardKey = -1 # this is looked up in Activate()

        # initialize dialog
        self.SetTitle("Manipulate", True)

        # load the new scheme early!!
        schemeobj = scheme().LoadSchemeFromFile("resource/ZombieMaster.res", "ZombieMaster")
        self.SetScheme(schemeobj)
        self.SetSizeable(False)

        self.SetProportional(False) #TGB: no more proportional

        # info window about this map
    #	m_pMapInfo = new RichText( this, "MapInfo" )
        self.SetMoveable(True)
        
        self.activate = Button(self, "Activate", 'manipulate')
        self.activate.SetCommand('manipulate')
        self.activate.AddActionSignalTarget(self.GetVPanel())
        self.trap = Button(self, 'Trap', 'toggle_trap')
        self.trap.AddActionSignalTarget(self.GetVPanel())
        self.trap.SetCommand('toggle_trap')
        self.description = Label(self, 'Description', 'desc')
        
        self.LoadControlSettings("Resource/UI/ManipulateMenu.res")
        self.InvalidateLayout()

        self.mapname = None
        
        AddTickSignal(self.GetVPanel(), 200)

    #-----------------------------------------------------------------------------
    # Purpose: sets the text color of the map description field
    #-----------------------------------------------------------------------------
    def ApplySchemeSettings(self, schemeobj):
        super(ManipulateMenu, self).ApplySchemeSettings(schemeobj)

    #-----------------------------------------------------------------------------
    # Purpose: shows the manipulate menu
    #-----------------------------------------------------------------------------
    def ShowPanel(self, bShow):
        if super(ManipulateMenu, self).IsVisible() == bShow:
            return

        #LAWYER:  Extra stuff to get the value of the Manipulate
        pPlayer = C_BasePlayer.GetLocalPlayer()  #LAWYER:  Get the local player
        if pPlayer:
            self.SetLabelText( "Activate", '\nActivate for %d' % (self.activemanipulate.cost) )
            if self.activemanipulate.cost > resources[pPlayer.GetOwnerNumber()][RESOURCE_ZOMBIEPOOL]:
                self.SetControlEnabled( "Activate", False)
            else:
                self.SetControlEnabled( "Activate", True)
        
        if bShow:
            # STODO
            #TGB: spawnmenu cannot be open open as it will conflict
            #m_pViewPort.ShowPanel( PANEL_BUILD, False )
            #also hide viewport
            #m_pViewPort.ShowPanel( PANEL_VIEWPORT, False )

            self.Activate()

            self.SetMouseInputEnabled( True )

            self.SetKeyBoardInputEnabled( zm_menus_use_keyboard.GetBool() )	

            # get key bindings if shown

            # STODO
            #if self.jumpkey < 0: # you need to lookup the jump key AFTER the engine has loaded
            #    self.jumpkey = gameuifuncs.GetEngineKeyCodeForBind( "jump" )
            

            '''if ( m_iScoreBoardKey < 0 ) 
            
                m_iScoreBoardKey = gameuifuncs.GetEngineKeyCodeForBind( "showscores" )
            '''
        else:
            self.SetVisible( False )
            self.SetMouseInputEnabled( False )
        

    #	m_pViewPort.ShowBackGround( bShow )

    def Update(self):
        pass

    #-----------------------------------------------------------------------------
    # Purpose: Sets the text of a control by name
    #-----------------------------------------------------------------------------
    def SetLabelText(self, textEntryName, text):
        entry = self.FindChildByName(textEntryName)
        if entry:
            entry.SetText(text)

    #LAWYER: (MANIPULATE MENU) Define the pressing of buttons
    def OnCommand(self, command):
        if command != "vguicancel": #not a cancel msg
            if command == "toggle_trap":
                #TGB: instead of going through server, send a rallymode cmd to vgui_viewport
                # STODO
                msg = KeyValues("ButtonCommand")
                msg.SetString("command", "MODE_TRAP")
                #pview = gViewPortInterface.FindPanelByName(PANEL_VIEWPORT)
                #if pview:
                #    PostMessage(pview.GetVPanel(), msg)
            else:
                #probably the "manipulate" manip-activation command
                engine.ClientCommand(command)
        
        self.DoClose()
      
        super(ManipulateMenu, self).OnCommand(command)

    #-----------------------------------------------------------------------------
    # Purpose: #LAWYER:  Update the thingy!
    #-----------------------------------------------------------------------------
    def OnTick(self):
        if super(ManipulateMenu, self).IsVisible() == False:
            return

        #LAWYER:  Extra stuff to get the value of the Manipulate
        pPlayer = C_BasePlayer.GetLocalPlayer()  #LAWYER:  Get the local player
        if not pPlayer:
            return
            
        #print 'man: %d %d' % (self.activemanipulate.cost, self.activemanipulate.trapcost)

        self.SetLabelText( "Activate", 'Activate for %d' % (self.activemanipulate.cost))
        if self.activemanipulate.cost > resources[pPlayer.GetOwnerNumber()][RESOURCE_ZOMBIEPOOL]:
            self.SetControlEnabled( "Activate", False)
        else:
            self.SetControlEnabled( "Activate", True)
        
        #LAWYER:  Stuff for Trap system
        i = 0
        if self.activemanipulate.trapcost <= 0:
            i = (self.activemanipulate.cost * 1.5)
        else:
            i = (self.activemanipulate.trapcost)
        
        self.SetLabelText( "Trap", 'Create Trap for %d' % (i))
        if i > resources[pPlayer.GetOwnerNumber()][RESOURCE_ZOMBIEPOOL]:
            self.SetControlEnabled( "Trap", False)
        else:
            self.SetControlEnabled( "Trap", True)
        
        if self.activemanipulate.description:
            #DevMsg("%s\n", pPlayer.m_szLastDescription)
            #qck: Set label text equal to description, etc.
            self.SetLabelText("Description", self.activemanipulate.description)

    def OnKeyCodePressed(self, code):
        lastPressedEngineKey = engine.GetLastPressedEngineKey()

        if self.jumpkey >= 0 and self.jumpkey == lastPressedEngineKey:
            self.DoClose()
        else:
            super(ManipulateMenu, self).OnKeyCodePressed( code )

    #--------------------------------------------------------------
    # Helper that closes this menu 
    #--------------------------------------------------------------
    def DoClose(self):
        self.Close()
        #gViewPortInterface.ShowBackGround( False )

        #TGB: only if we're zm
        #pPlayer = C_BasePlayer.GetLocalPlayer()
        #if pPlayer and pPlayer == GameRules.zmplayer:
            #bring viewport back up
        #    m_pViewPort.ShowPanel( PANEL_VIEWPORT, True )
    
manipulatemenu = ManipulateMenu()