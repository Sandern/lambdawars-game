'''
Controller code for toolbox panel in editor mode.
'''
from srcbase import IN_DUCK, KeyValues
from cef import CefPanel
from gameinterface import engine, ConVarRef
from entities import CBasePlayer, ReadDataDesc
from input import ButtonCode
import filesystem
import os
from fields import GetField

from gamerules import gamerules
from editorsystem import EditorSystem
from _recast import RecastMgr

class CefToolbox(CefPanel):
    name = 'toolbox'
    htmlfile = 'ui/viewport/tools/toolbox.html'
    classidentifier = 'ui/editor/Toolbox'
    cssfiles = CefPanel.cssfiles + ['tools/tools.css']
    
    currentmapname = '&lt;no map loaded&gt;'
    
    def SetupFunctions(self):
        super().SetupFunctions()
        
        self.CreateFunction('setActiveMode', False)
        self.CreateFunction('listModels', True)
        self.CreateFunction('addPlaceToolAsset', False)
        self.CreateFunction('removePlaceToolAsset', False)
        self.CreateFunction('setPlaceToolDensity', False)
        self.CreateFunction('setPlaceToolPlaceOnNavMesh', False)
        self.CreateFunction('setPlaceToolAttribute', False)
        
        self.CreateFunction('getProperties', True)
        self.CreateFunction('applyProperties', False)
        
        self.CreateFunction('getMeshSettings', True)
        self.CreateFunction('meshSetCellSize', False)
        self.CreateFunction('meshSetCellHeight', False)
        self.CreateFunction('meshSetTileSize', False)
        
    def OnLoaded(self):
        super().OnLoaded()

        self.visible = True
        
    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = super().GetConfig()
        config['currentmapname'] = self.currentmapname
        config['rootmodellist'] = self.LoadRootModelsAndFolders()
        return config
        
    def FloraKeyInput(self, down, keynum, currentbinding):
        return 1
        
    keyinputmap = {
        'flora' : 'FloraKeyInput',
    }
    def KeyInput(self, down, keynum, currentbinding):
        player = CBasePlayer.GetLocalPlayer()
        ctrldown = player.buttons & IN_DUCK
        
        if keynum == ButtonCode.KEY_DELETE:
            if down:
                # Delete selection
                engine.ServerCommand('wars_editor_delete_selection')
            return 0
        elif ctrldown and keynum == ButtonCode.KEY_C:
            if down:
                engine.ServerCommand('wars_editor_copy_selection')
            return 0
        elif ctrldown and keynum == ButtonCode.KEY_V:
            if down:
                engine.ServerCommand('wars_editor_paste_selection')
            return 0
            
        activemode = gamerules.activemode
        if activemode in self.keyinputmap:
            return getattr(self, self.keyinputmap[activemode])(down, keynum, currentbinding)
        return 1
        
    def LoadRootModelsAndFolders(self, rootpath='models/'):
        ''' Builds a list of records for tree grids. 
        
            The returned model paths uses forward slashes, which is expected by
            the vmf file format.
        '''
        records = []
        rootmodels = filesystem.ListDir(rootpath, pathid=None, wildcard='*')
        for rm in rootmodels:
            if rm == '.' or rm == '..':
                continue
            path = os.path.normpath(os.path.join(rootpath, rm)).replace('\\', '/')
            if not filesystem.IsDirectory(path) and os.path.splitext(rm)[1] != '.mdl':
                continue
            if filesystem.IsDirectory(path):
                path += '/' # Add trailing separator for directories
            records.append({
                'ModelID' : path.replace('/', '').replace('.', ''), # Bug in JQTreeGrid, due which shift select won't work with forward slashes
                'FullPath' : path,
                'Model' : rm,
            })
        return records
            
    def OnEditorSelectionChanged(self, selection):
        if self.isloaded:
            self.Invoke("editorSelectionChanged", [len(selection)])
            
    def setActiveMode(self, methodargs, callbackid):
        ''' Changes the toolmode (for example: "select", "transform", "flora"). '''
        mode = methodargs[0]
        gamerules.activemode = mode
        
    def listModels(self, methodargs, callbackid):
        modelpath =  methodargs[0]
        return self.LoadRootModelsAndFolders(modelpath)
        
    def addPlaceToolAsset(self, methodargs, callbackid):
        asset = methodargs[0]
        player = CBasePlayer.GetLocalPlayer()
        player.GetSingleActiveAbility().AddPlaceToolAsset(asset)
        engine.ServerCommand('wars_editor_add_pt_asset %s' % (asset))
        
    def removePlaceToolAsset(self, methodargs, callbackid):
        asset = methodargs[0]
        player = CBasePlayer.GetLocalPlayer()
        player.GetSingleActiveAbility().RemovePlaceToolAsset(asset)
        engine.ServerCommand('wars_editor_remove_pt_asset %s' % (asset))
        
    def setPlaceToolDensity(self, methodargs, callbackid):
        density = methodargs[0]
        player = CBasePlayer.GetLocalPlayer()
        player.GetSingleActiveAbility().SetPlaceToolDensity(float(density))
        engine.ServerCommand('wars_editor_set_pt_density %s' % (density))
        
    def setPlaceToolPlaceOnNavMesh(self, methodargs, callbackid):
        usenavmesh = methodargs[0]
        player = CBasePlayer.GetLocalPlayer()
        player.GetSingleActiveAbility().usenavmesh = bool(usenavmesh)
        engine.ServerCommand('wars_editor_set_pt_usenavmesh %d' % (int(usenavmesh)))
        
    def setPlaceToolAttribute(self, methodargs, callbackid):
        player = CBasePlayer.GetLocalPlayer()
        fieldname = methodargs[0]
        value = methodargs[1]
        ability = player.GetSingleActiveAbility()
        field = GetField(ability, fieldname)
        field.Set(ability, value)
        engine.ServerCommand('wars_editor_set_pt_attr %s %s' % (fieldname, value if type(value) != bool else int(value)))
        
    # Properties panel methods
    def getProperties(self, methodargs, callbackid):
        properties = {}
        for i in range(0, EditorSystem().GetNumSelected()):
            ent = EditorSystem().GetSelected(i)
            if not ent:
                continue
            
            datadesc = ReadDataDesc(ent)
            for key, value in datadesc.items():
                if key in properties:
                    if properties[key]['value'] != value:
                        properties[key]['value'] = '&lt;mixed&gt;'
                else:
                    properties[key] = {
                        'attribute' : key,
                        'value' : value,
                        'type' : 'string',
                    }
                
        return properties
        
    def applyProperties(self, methodargs, callbackid):
        attributevalues = methodargs[0]
        attributes = KeyValues("data")
        for entry in attributevalues:
            key = entry[0]
            value = entry[1]
            attributes.SetString(key, value)
            
        EditorSystem().QueueCommand(EditorSystem().CreateEditCommand(attributes))
        
    # Nav mesh panel methods
    def getMeshSettings(self, methodargs, callbackid):
        settings = {}
        
        recast_debug_mesh = ConVarRef('recast_debug_mesh')
        recast_draw_navmesh = ConVarRef('recast_draw_navmesh')
        recast_draw_server = ConVarRef('recast_draw_server')
        
        settings['debug_mesh'] = recast_debug_mesh.GetString() if (not methodargs or not methodargs[0]) else methodargs[0]
        settings['draw_navmesh'] = recast_draw_navmesh.GetBool()
        settings['draw_server'] = recast_draw_server.GetBool()
        
        mesh = RecastMgr().GetMesh(settings['debug_mesh'])
        #print('Getting mesh %s: %s, params: %s' % (settings['debug_mesh'], mesh, methodargs))
        if mesh:
            settings['cellsize'] = mesh.cellsize
            settings['cellheight'] = mesh.cellheight
            settings['tilesize'] = mesh.tilesize
        else:
            settings['cellsize'] = -1
            settings['cellheight'] = -1
            settings['tilesize'] = -1
        
        return settings
        
    def meshSetCellSize(self, methodargs, callbackid):
        meshname = methodargs[0]
        mesh = RecastMgr().GetMesh(meshname)
        if mesh:
            mesh.cellsize = float(methodargs[1])
            engine.ServerCommand('recast_mesh_setcellsize %s %f\n' % (meshname, mesh.cellsize))
        else:
            PrintWarning('meshSetCellSize: could not find mesh %s\n' % (meshname))
            
    def meshSetCellHeight(self, methodargs, callbackid):
        meshname = methodargs[0]
        mesh = RecastMgr().GetMesh(meshname)
        if mesh:
            mesh.cellheight = float(methodargs[1])
            engine.ServerCommand('recast_mesh_setcellheight %s %f\n' % (meshname, mesh.cellheight))
        else:
            PrintWarning('meshSetCellHeight: could not find mesh %s\n' % (meshname))
            
    def meshSetTileSize(self, methodargs, callbackid):
        meshname = methodargs[0]
        mesh = RecastMgr().GetMesh(meshname)
        if mesh:
            mesh.tilesize = float(methodargs[1])
            engine.ServerCommand('recast_mesh_settilesize %s %f\n' % (meshname, mesh.tilesize))
        else:
            PrintWarning('meshSetTileSize: could not find mesh %s\n' % (meshname))