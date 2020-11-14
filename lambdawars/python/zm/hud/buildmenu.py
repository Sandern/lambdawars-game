from vgui import scheme, AddTickSignal, RemoveTickSignal
from vgui.controls import Frame
from entities import C_BasePlayer
from gameinterface import engine

from convars import *

from ..shared import *

class BuildMenu(Frame):
    lastflags = 0
    currentspawn = -1

    def __init__(self):
        super(BuildMenu, self).__init__(None, 'build')
    
        self.jumpkey = -1 # this is looked up in Activate()
    #	m_iScoreBoardKey = -1 # this is looked up in Activate()

        # initialize dialog
        self.SetTitle("Spawn Menu", True)

        # load the new scheme early!!
        s = scheme().LoadSchemeFromFile("resource/ZombieMaster.res", "ZombieMaster")
        self.SetScheme(s)
        self.SetSizeable(False)

        self.largefont = scheme().GetIScheme(s).GetFont("Trebuchet18", True)
        self.mediumfont = scheme().GetIScheme(s).GetFont("Trebuchet16", True)

        self.SetProportional(False)

        self.LoadControlSettings("Resource/UI/BuildMenu.res")

        AddTickSignal(self.GetVPanel(), 150)

        #TGB: moved here because the .res seemed to override it
        self.SetMoveable(True)
        self.InvalidateLayout()

        #we fetch a bunch of pointers to various elements here so we can alter them quickly and easily
        self.info_image = self.FindChildByName("ZombieImage")

        self.info_rescost = self.FindChildByName("CostRes")
        self.info_popcost = self.FindChildByName("CostPop")
        self.info_description = self.FindChildByName("LabelDescription")

        self.removelast = self.FindChildByName("RemoveLast")
        self.clearqueue = self.FindChildByName("ClearQueue")

        # STODO
        '''
        #prepare a list of our spawn buttons etc so we can easily iterate over them
        for (int i=0 i < TYPE_TOTAL i++)
        
            char buffer[25]
            Q_snprintf(buffer, sizeof(buffer), "z_spawn1_%02d", i)
            spawnbuttons[i] = FindChildByName(buffer)

            Q_snprintf(buffer, sizeof(buffer), "z_spawn5_%02d", i)
            spawnfives[i] = FindChildByName(buffer)

            zombieimages[i] = vgui::scheme().GetImage(TypeToImage[i], True)
            zombiequeue[i] = vgui::scheme().GetImage(TypeToQueueImage[i], False)

        
        kv = new KeyValues("zombiedesc.res")
        if  kv.LoadFromFile( (IBaseFileSystem*)filesystem, "resource/zombiedesc.res", "MOD"):
        
            #braaaaaaah, char juggling is pain

            const char *temp = kv.GetString("shambler", "Shambler")
            int length = 128
            char *saved = new char[length]
            Q_strncpy(saved, temp, strlen(temp) + 1)
            zombiedescriptions[TYPE_SHAMBLER] = saved

            temp = kv.GetString("banshee", "Banshee")
            saved = new char[length]
            Q_strncpy(saved, temp, strlen(temp) + 1)
            zombiedescriptions[TYPE_BANSHEE] = saved

            temp = kv.GetString("hulk", "Hulk")
            saved = new char[length]
            Q_strncpy(saved, temp, strlen(temp) + 1)
            zombiedescriptions[TYPE_HULK] = saved

            temp = kv.GetString("drifter", "Drifter")
            saved = new char[length]
            Q_strncpy(saved, temp, strlen(temp) + 1)
            zombiedescriptions[TYPE_DRIFTER] = saved

            temp = kv.GetString("immolator", "Immolator")
            saved = new char[length]
            Q_strncpy(saved, temp, strlen(temp) + 1)
            zombiedescriptions[TYPE_IMMOLATOR] = saved
        
        #will delete its child keys as well
        kv.deleteThis()

        for (int i=0 i < BM_QUEUE_SIZE i++)
        
            char buffer[10]
            Q_snprintf(buffer, sizeof(buffer), "queue%02d", i)
            queueimages[i] = dynamic_cast<vgui::ImagePanel*>(FindChildByName(buffer))
            
        '''
        
    
    #-----------------------------------------------------------------------------
    # Purpose: shows the build menu
    #-----------------------------------------------------------------------------
    def ShowPanel(self, bShow):
    #	CBasePlayer *pPlayer = C_BasePlayer::GetLocalPlayer()
        if super(BuildMenu, self).IsVisible() == bShow:
            return

        if bShow:
            # STODO
            '''
            #TGB: manipmenu cannot be open open as it will conflict
            m_pViewPort.ShowPanel( PANEL_MANIPULATE, False )
            #viewport has to go too, or the build menu can sometimes become unresponsive to commands
            m_pViewPort.ShowPanel( PANEL_VIEWPORT, False )
            '''
            
            #TGB: update costs if necessary
            '''we print these live from the cvar now
            if (NeedCostsUpdate())
            
                LoadControlSettings("Resource/UI/BuildMenu.res")
                PrintAllCosts()

                #it would be nice to save away the original unprinted strings for easy cost updating without reloading the .res
                #however, a change of zombiecosts should not happen often at all, at most once for each time you join a server
                
                DevMsg("Reloaded buildmenu\n")
            '''

            #LAWYER:  ZombieFlags stuff
            self.CalculateButtonState()

            self.Activate()

            self.SetMouseInputEnabled( True ) 

            self.SetKeyBoardInputEnabled( zm_menus_use_keyboard.GetBool() )
        
            ## get key bindings if shown
            # STODO
            '''
            if self.jumpkey < 0: # you need to lookup the jump key AFTER the engine has loaded
                self.jumpkey = gameuifuncs.GetEngineKeyCodeForBind( "jump" ) 
            '''
            
            #if ( m_iScoreBoardKey < 0 ) 
            #
            #	m_iScoreBoardKey = gameuifuncs.GetEngineKeyCodeForBind( "showscores" )
            #
        else:
            self.SetVisible(False)
            self.SetMouseInputEnabled(False)

            #bring viewport back up
            pPlayer = C_BasePlayer.GetLocalPlayer()
            if pPlayer and pPlayer.GetOwnerNumber() == ON_ZOMBIEMASTER:
                # STODO
                #prevent edge cases with roundrestarts while panel is open
                #m_pViewPort.ShowPanel( PANEL_VIEWPORT, True )
                pass

        #m_pViewPort.ShowBackGround( bShow )
    

    #LAWYER: (BUILD MENU) Define the pressing of buttons
    def OnCommand(self, command):
        if command != "vguicancel":
            #TGB: some special commands need the current spawn idx
            if (command.startswith('summon') or #both summon commands
                command.startswith('buildmenu_')): #remove last and clear queue commands
                engine.ClientCommand(command % (self.currentspawn))
                return
            
            elif command == "toggle_rally":
                pass
                #engine.ClientCommand(command)

                # STODO
                #TGB: instead of going through server, send a rallymode cmd to vgui_viewport
                '''
                msg = new KeyValues("ButtonCommand")
                msg.SetString("command", "MODE_RALLY")
                IViewPortPanel *pview = gViewPortInterface.FindPanelByName(PANEL_VIEWPORT)
                if pview:
                    PostMessage(pview.GetVPanel(), msg)
                '''

                #no return here means the buildmenu will close, as it should in this case
            
            else:
                engine.ClientCommand(command)
                return

        self.DoClose()

        super(BuildMenu, self).OnCommand(command)

    #-----------------------------------------------------------------------------
    # Purpose: Forces an update
    #-----------------------------------------------------------------------------
    def OnThink(self):
        #pPlayer = C_BasePlayer.GetLocalPlayer()
        if super(BuildMenu, self).IsVisible() == False:
            return

        self.CalculateButtonState()

        # STODO
        '''
        for (int i = 0 i < TYPE_TOTAL i++)
        
            if ((spawnbuttons[i] and spawnbuttons[i].IsCursorOver()) or
                (spawnfives[i] and spawnfives[i].IsCursorOver()))
            
                ShowZombieInfo(i)
        '''

        #TGB: force close if not ZM
        pPlayer = C_BasePlayer.GetLocalPlayer()
        if pPlayer and pPlayer.GetOwnerNumber() != ON_ZOMBIEMASTER:
            #prevent edge cases with roundrestarts while panel is open
            self.DoClose()

    #TGB: renamed from CalculateFlags to reflect increased functionality
    def CalculateButtonState(self):
        pPlayer = C_BasePlayer.GetLocalPlayer()  #LAWYER:  Get the local player
        if pPlayer:
            pass
            # STODO
            '''
            #TODO: usermessage-ify
            if self.lastflags == pPlayer.m_iLastZombieFlags:
                return

            button_states[TYPE_TOTAL] #five buttons

            self.lastflags = pPlayer.m_iLastZombieFlags

            #TGB: if the flags are 0/unset, all zombies should be available
            #so changed from != 0 to == 0
            if  (pPlayer.m_iLastZombieFlags == 0)
            
                for (int type=0 type < TYPE_TOTAL type++)
                    button_states[type] = True
            
            else
            
                #Someone's defined ZombieFlags here, so start disabling things
                for (int type=0 type < TYPE_TOTAL type++)
                    button_states[type] = False

                int iCalculation = pPlayer.m_iLastZombieFlags

                #Burnzombies
                if (iCalculation - BURNZOMBIE_FLAG >= 0)
                
                    iCalculation -= BURNZOMBIE_FLAG
                    button_states[TYPE_IMMOLATOR] = True
                
                #Dragzombies
                if (iCalculation - DRAGZOMBIE_FLAG >= 0)
                
                    iCalculation -= DRAGZOMBIE_FLAG
                    button_states[TYPE_DRIFTER] = True
                
                #Hulks
                if (iCalculation - HULK_FLAG >= 0)
                
                    iCalculation -= HULK_FLAG
                    button_states[TYPE_HULK] = True
                
                #Fasties
                if (iCalculation - FASTIE_FLAG >= 0)
                
                    iCalculation -= FASTIE_FLAG
                    button_states[TYPE_BANSHEE] = True
                
                #Shamblies
                if (iCalculation - SHAMBLIE_FLAG >= 0)
                
                    iCalculation -= SHAMBLIE_FLAG
                    button_states[TYPE_SHAMBLER] = True
            '''    
            

            #TGB: we now have the current state of the buttons as the flags set them
            #	now we can just disable the ones that we don't have the res or pop for

            #TGB: while writing this I decided that it should be possible to queue up zombies you can't yet pay for
            '''
            int pool = pPlayer.m_iZombiePool
            int pop = pPlayer.m_iZombiePopCount
            int popmax = zm_zombiemax.GetInt()
            for (int type=0 type < TYPE_TOTAL type++)
            
                ZombieCost cost = GetCostForType(type)

                if ((pool - cost.resources < 0) or
                    (pop + cost.population > popmax))
                
                    button_states[type] = False
                    continue
                
            
            '''
            
            # STODO
            '''
            #TGB: apply state to buttons
            for (int type=0 type < TYPE_TOTAL type++)
            
                if (spawnbuttons[type])
                    spawnbuttons[type].SetEnabled(button_states[type])

                if (spawnfives[type])
                    spawnfives[type].SetEnabled(button_states[type])
            '''

    # Grabs the pop and res costs for a given type
    def GetCostForType(self, type):
        return 0 # STODO
        '''
        switch(type)
        
        case TYPE_SHAMBLER:
            return ZombieCost(zm_cost_shambler.GetInt(), zm_popcost_shambler.GetInt())
        case TYPE_BANSHEE:
            return ZombieCost(zm_cost_banshee.GetInt(), zm_popcost_banshee.GetInt())
        case TYPE_HULK:
            return ZombieCost(zm_cost_hulk.GetInt(), zm_popcost_hulk.GetInt())
        case TYPE_DRIFTER:
            return ZombieCost(zm_cost_drifter.GetInt(), zm_popcost_drifter.GetInt())
        case TYPE_IMMOLATOR:
            return ZombieCost(zm_cost_immolator.GetInt(), zm_popcost_immolator.GetInt())
        default:
            return ZombieCost(0, 0)
        '''

    #--------------------------------------------------------------
    # TGB: show the zombie img and info in the middle area 
    #--------------------------------------------------------------
    def ShowZombieInfo(self, type):
        if not self.info_image or not self.info_rescost or not self.info_popcost or not self.info_description:
            return

        self.info_image.SetImage(zombieimages[type])

        cost = self.GetCostForType(type)

        self.info_rescost.SetText(str(cost.resources))

        self.info_popcost.SetText(str(cost.population))

        self.info_description.SetText(zombiedescriptions[type])
    
    #--------------------------------------------------------------
    # Update the queue images to reflect the types in the given array 
    #--------------------------------------------------------------
    def UpdateQueue(self, q, size=TYPE_TOTAL):
        zombies_present = False
        # STODO
        '''
        for (int i=0 i < size i++)
        
            const int type = q[i]

            if (!queueimages[i])
                return

            # Is there a zombie queued at this spot?
            if (type > TYPE_INVALID and type < TYPE_TOTAL)
            
                vgui::IImage *given_img = zombiequeue[type]

                if (given_img != queueimages[i].GetImage())
                
                    #queueimages[i].SetShouldScaleImage(True)
                    queueimages[i].SetImage(given_img)
                
                queueimages[i].SetVisible(True)

                zombies_present = True
            
            else
            
                # no valid type, so don't draw an image
                queueimages[i].SetVisible(False)


        if (self.removelast)
            self.removelast.SetEnabled(zombies_present)
        if (self.clearqueue)
            self.clearqueue.SetEnabled(zombies_present)
        '''

    #--------------------------------------------------------------
    # TGB: tell the server we're not showing a spawn's menu anymore 
    #--------------------------------------------------------------
    def OnClose(self):
        engine.ExecuteClientCmd('buildmenu_closed %d' % (self.currentspawn))

        self.currentspawn = -1

        super(BuildMenu, self).OnClose()

    #--------------------------------------------------------------
    # TGB: we have this so that when keyboard grabbing is disabled for this menu we still have a close-menu-shortcut
    #--------------------------------------------------------------
    def OnKeyCodePressed(self, code):
        lastPressedEngineKey = engine.GetLastPressedEngineKey()

        if self.jumpkey >= 0 and self.jumpkey == lastPressedEngineKey:
            self.DoClose()
        else:
            super(BuildMenu, self).OnKeyCodePressed( code )

    #--------------------------------------------------------------
    # 
    #--------------------------------------------------------------
    def SetCurrentSpawn(self, idx):
        if self.currentspawn != idx:
            self.currentspawn = idx

    #--------------------------------------------------------------
    # Helper that closes the menu 
    #--------------------------------------------------------------
    def DoClose(self):
        self.Close()
        self.SetVisible( False )
        self.SetMouseInputEnabled( False )

        # STODO
        '''
        #bring viewport back up
        pPlayer = C_BasePlayer.GetLocalPlayer()
        if pPlayer and pPlayer.GetOwnerNumber() == ON_ZOMBIEMASTER:
            #prevent edge cases with roundrestarts while panel is open
            m_pViewPort.ShowPanel( PANEL_VIEWPORT, True )

        gViewPortInterface.ShowBackGround( False )
        '''
    
buildmenu = BuildMenu()
