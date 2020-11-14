from core.gamerules.sandbox import Sandbox, SandBoxInfo
from core.signals import editormapchanged, editorselectionchanged
from gameinterface import engine, concommand, ConVarRef
from gamerules import gamerules
import srcmgr
if isserver:
    from utils import UTIL_IsCommandIssuedByServerAdmin, UTIL_GetPlayers, UTIL_GetCommandClient
    from entities import RespawnPlayer
    
from editorsystem import EditorSystem, CEditorSystem

sv_fogofwar = ConVarRef('sv_fogofwar')

class EditorMode(Sandbox):
    interactionmodes = {
        'select' : CEditorSystem.EDITORINTERACTION_SELECT,
        'translate' : CEditorSystem.EDITORINTERACTION_TRANSLATE,
        'rotate' : CEditorSystem.EDITORINTERACTION_ROTATE,
    }

    def InitGamerules(self):
        super().InitGamerules()

        EditorSystem().SetActive(True)
        
        # Make sure everybody is an editor player
        if isserver:
            players = UTIL_GetPlayers()
            for player in players:
                if player.GetClassname() != 'editor_player':
                    print('Respawning player as editor player')
                    RespawnPlayer(player, 'editor_player')
                    
        editormapchanged.connect(self.OnMapChanged)
        editorselectionchanged.connect(self.OnEditorSelectionChanged)
        
        if isserver:
            sv_fogofwar.SetValue(0)
        
        self.LoadCurrentMap()
        
    def ShutdownGamerules(self):
        super().ShutdownGamerules()
        
        editormapchanged.disconnect(self.OnMapChanged)
        editorselectionchanged.connect(self.OnEditorSelectionChanged)

        EditorSystem().SetActive(False)
        EditorSystem().ClearLoadedMap()
        
        # Return editor players to regular players
        if isserver:
            players = UTIL_GetPlayers()
            for player in players:
                if player.GetClassname() == 'editor_player':
                    RespawnPlayer(player, 'player')
        
    def LoadCurrentMap(self):
        EditorSystem().LoadCurrentVmf()
        
    def SaveCurrentMap(self):
        EditorSystem().SaveCurrentVmf()
        print('Saved %s' % srcmgr.levelname)
        
    def OnMapChanged(self, **kwargs):
        currentmap = srcmgr.levelname
        print('Map changed to %s' % currentmap)
            
    def OnEditorSelectionChanged(self, selection=None, **kwargs):
        if isclient:
            self.hudrefs['CefToolbox'].OnEditorSelectionChanged(selection)
            
    __activemode = 'select'
    @property
    def activemode(self):
        return self.__activemode
    @activemode.setter
    def activemode(self, value):
        self.__activemode = value
        EditorSystem().SetEditorMode(self.interactionmodes.get(value, CEditorSystem.EDITORINTERACTION_NONE))
        if isclient:
            engine.ServerCommand('wars_editor_setmode %s' % value)
            
class EditorModeInfo(SandBoxInfo):
    name = 'editormode'
    hidden = True
    displayname = '#Editor_Name'
    description = '#Editor_Description'
    cls = EditorMode
    huds = list(SandBoxInfo.huds)
    huds.extend([
        'core.editor.ui.toolbox.CefToolbox',
    ])
    allowplayerjoiningame = True
    
if isserver:
    @concommand('wars_editor')
    def CCWarsEditor(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        engine.ServerCommand('wars_setgamerules %s\n' % (EditorModeInfo.name))
        
    @concommand('wars_editor_save')
    def CCWarsEditorSave(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        gamerules.SaveCurrentMap()
        
    @concommand('wars_editor_setmode')
    def CCWarsEditorSetMode(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        gamerules.activemode = args[1]
        player = UTIL_GetCommandClient()
        player.ClearActiveAbilities()
        