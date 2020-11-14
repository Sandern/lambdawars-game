# TODO: Port to html panel
'''
from vgui import GetClientMode, scheme, AddTickSignal, RemoveTickSignal
from vgui.tools import ToolBaseFrame
from vgui.controls import Panel, Label, TextEntry, Button
from gamerules import gamerules
from entities import C_HL2WarsPlayer, PlayerResource
from utils import UTIL_GetPlayers
from gameinterface import concommand, engine, PlayerInfo

class GiveEntry(Panel):
    def __init__(self, parent, panelname, name, ownernumber):
        self.name = name
        
        super(GiveEntry, self).__init__(parent, panelname)
        
        self.playername = Label(self, 'PlayerName', name)
        self.amount = TextEntry(self, 'Amount')
        self.givebutton = Button(self, 'GiveButton', 'send', self, "Give")
        
        self.ownernumber = ownernumber
        
    def PerformLayout(self):
        super(GiveEntry, self).PerformLayout()
        
        dy = scheme().GetProportionalScaledValueEx(self.GetScheme(), 10)
        
        playersizex = scheme().GetProportionalScaledValueEx(self.GetScheme(), 50)
        self.playername.SetSize(playersizex, dy)
        self.playername.SetPos(0,0)
        amountsizex = scheme().GetProportionalScaledValueEx(self.GetScheme(), 50)
        self.amount.SetSize(amountsizex, dy)
        self.amount.SetPos(playersizex,0)
        self.givebutton.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 50), dy)
        self.givebutton.SetPos(playersizex+amountsizex,0)
        
    def OnCommand(self, command):
        if command == 'Give':
            try:
                res = int(self.amount.GetText())
            except ValueError:
                print('invalid value %s' % (self.amount.GetText()))
                return
                
            engine.ClientCommand('player_sendres requisition %d %d' % (res, self.ownernumber))
                
            print('Giving %d to %d' % (res, self.ownernumber))
        else:
            super(GiveEntry, self).OnCommand(command)
        
class ResourcesDialog(ToolBaseFrame):
    def __init__(self):
        super(ResourcesDialog, self).__init__(GetClientMode().GetViewport(), 'ResourcesDialog')
    
        # Set scheme
        schemeobj = scheme().LoadSchemeFromFile("resource/SourceScheme.res", "SourceScheme")
        self.SetScheme(schemeobj)
        
        self.SetSizeable(False)
        
        self.SetTitle("Resources Dialog", False)
        
    def SetVisible(self, state):
        super(ResourcesDialog, self).SetVisible(state)
        
        if state:
            AddTickSignal(self.GetVPanel(),100)
        else:
            RemoveTickSignal(self.GetVPanel())
            
    def PerformLayout(self):
        super(ResourcesDialog, self).PerformLayout()
        
        y = scheme().GetProportionalScaledValueEx(self.GetScheme(), 25)
        dy = scheme().GetProportionalScaledValueEx(self.GetScheme(), 10)
        x1 = scheme().GetProportionalScaledValueEx(self.GetScheme(), 4)
        x2 = scheme().GetProportionalScaledValueEx(self.GetScheme(), 34)
        
        sizex, sizey = self.GetSize()
        
        for e in self.entries:
            e.SetSize(sizex-x1, dy)
            e.SetPos(x1, y)
            y += dy
        
        y += scheme().GetProportionalScaledValueEx(self.GetScheme(), 5)
            
        self.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 250), y)
        
    def OnTick(self):
        self.BuildPlayerList()
        
    def BuildPlayerList(self):
        localplayer = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not localplayer:
            return
            
        localownernumber = localplayer.GetOwnerNumber()
        currentplayers = []
        
        for i in range(1, gpGlobals.maxClients+1):
            #print 'i: ' + str(i) + ' team: ' + str(PlayerResource().GetTeam(i))
            #if not (PlayerResource().GetTeam(i) == TEAM_SPECTATOR):
            #    continue

            info = PlayerInfo()
            if not engine.GetPlayerInfo(i, info):
                continue
                
            on = PlayerResource().GetOwnerNumber(i)
            currentplayers.append(('player_%d' % (on), on,))
        currentplayers = tuple(currentplayers)
        
        if currentplayers != self.currentplayers:
            print 'rebuildig entries'
            
            self.entries = []
            for player in currentplayers:
                p = GiveEntry(self, player[0], player[0], player[1])
                self.entries.append(p)
            self.currentplayers = currentplayers
            self.InvalidateLayout()
        
    currentplayers = []
    entries = []
    
resourcesdialoginst = ResourcesDialog()
    
@concommand('resourcesdialog', '', 0)
def showresourcedialog(args):
    if resourcesdialoginst.IsVisible():
        resourcesdialoginst.SetVisible(False)
        resourcesdialoginst.SetEnabled(False)  
    else:
        resourcesdialoginst.SetVisible(True)
        resourcesdialoginst.SetEnabled(True)   
        resourcesdialoginst.RequestFocus()
        resourcesdialoginst.MoveToFront()
'''
