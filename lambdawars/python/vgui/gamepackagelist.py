from srcbase import Color, KeyValues
from vgui import scheme
from vgui.controls import Frame, Button, RichText, ListPanel
from utils import ScreenWidth, ScreenHeight
from gameinterface import ConCommand, engine, ConVarRef
from entities import C_BasePlayer
import gamemgr

from core.dispatch import receiver
from core.signals import gamepackageloaded, gamepackageunloaded

@receiver(gamepackageloaded)
@receiver(gamepackageunloaded)
def OnGamePackageChanged(sender, packagename, **kwargs):
    gamepackagemanager.OnGamePackageChanged(packagename)

class GamePackageManager(Frame):
    """ Shows the list of available game packages. 
        Allows you to load and unload packages."""
    def __init__(self):
        super(GamePackageManager, self).__init__(None, 'GamePackageManager')
        
        schemeobj = scheme().LoadSchemeFromFile("resource/SourceScheme.res", "SourceScheme")
        self.SetScheme(schemeobj)
        self.SetVisible(False)
        
        self.SetTitle('Game Package Manager', False)
        #self.SetProportional(True)
        
        self.packagelist = ListPanel(self, 'PackageList')
        self.packagelist.SetScheme(schemeobj)
        self.packagelist.SetMultiselectEnabled(False)
        self.packagelist.SetSortColumn(0)
        
        self.packagelist.AddColumnHeader(0, "name", "Packages", 100, 0)
        self.packagelist.AddColumnHeader(1, "desc", "Description", 300, 0)
        self.packagelist.AddColumnHeader(2, "loaded", "Loaded", 100, 0)
        
        self.loadpackage = Button(self, 'LoadPackage', 'Load', self, 'LoadPackage')
        self.unloadpackage = Button(self, 'UnloadPackage', 'Unload', self, 'UnloadPackage')
        
        self.LoadControlSettings("Resource/UI/GamePackageManagerPanel.res")
        
        self.RefreshPackageList()
        
    def ApplySchemeSettings(self, schemeobj):
        super(GamePackageManager, self).ApplySchemeSettings(schemeobj)

    def PerformLayout(self):
        super(GamePackageManager, self).PerformLayout()
        
    def OnCommand(self, command):
        if command == 'LoadPackage':
            itemid = self.packagelist.GetSelectedItem(0)
            if itemid == -1: 
                return
            package = self.packagelist.GetItem(itemid).GetString('name')
            engine.ServerCommand('load_gamepackage %s' % (package))
            return
        elif command == 'UnloadPackage':
            itemid = self.packagelist.GetSelectedItem(0)
            if itemid == -1: 
                return
            package = self.packagelist.GetItem(itemid).GetString('name')
            engine.ServerCommand('unload_gamepackage %s' % (package))
            return
        super(GamePackageManager, self).OnCommand(command)
        
    def RefreshPackageList(self):
        # Remember selection
        itemid = self.packagelist.GetSelectedItem(0)
        pkgname = self.packagelist.GetItem(itemid).GetName() if itemid != -1 else None
        
        self.packagelist.RemoveAll()
        for name, package in gamemgr.dbgamepackages.items():
            data = KeyValues(package.name, 'name', package.name)
            data.SetString('loaded', 'Yes' if package.loaded else 'No')
            self.packagelist.AddItem( data, 0, False, True )
            
        # Restore selection
        if pkgname:
            for i in range(0, len(self.packagelist.dataitems)):
                if self.packagelist.GetItem(i).GetName() == pkgname:
                    self.packagelist.SetSingleSelectedItem(i)
                    break
        
        # Update button states
        # Only hosts can load/unload packages
        #localplayer = C_BasePlayer.GetLocalPlayer()
        # FIXME: Need a way to check if the client is connected to a dedicated or listened server
        #if localplayer.entindex() != 1:
        #    self.loadpackage.SetEnabled(False)
        #    self.unloadpackage.SetEnabled(False)
        #else:
        #    self.loadpackage.SetEnabled(True)
        #    self.unloadpackage.SetEnabled(True)
            
    def OnGamePackageChanged(self, packagename):
        self.RefreshPackageList()
        
gamepackagemanager = GamePackageManager()   
        
def show_gamepackagemanager(args):
    if gamepackagemanager.IsVisible():
        gamepackagemanager.SetVisible(False)
        gamepackagemanager.SetEnabled(False)  
    else:
        gamepackagemanager.SetVisible(True)
        gamepackagemanager.SetEnabled(True)   
        gamepackagemanager.RequestFocus()
        gamepackagemanager.MoveToFront()
        
        gamepackagemanager.SetPos( ScreenWidth()/2 - gamepackagemanager.GetWide()/2, 
                                   ScreenHeight()/2 - gamepackagemanager.GetTall()/2)
show_gamepackagemanager_command = ConCommand( "gamepackagemanager", show_gamepackagemanager, "Show a panel to manage game packages", 0 )