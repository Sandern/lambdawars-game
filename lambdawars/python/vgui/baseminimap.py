"""
Provides the methods and variables for setting up a minimap, shared by various vgui elements.
Does not draw the minimap. 
Create a minimap according to: http://developer.valvesoftware.com/wiki/Level_Overviews
"""
import srcmgr
from vgui.controls import CBaseMinimap
from kvdict import LoadFileIntoDictionaries
from gameinterface import GetLevelName
import os

class BaseMinimap(CBaseMinimap):
    def __init__(self, parent, panelname, registerlisteners=True, bsetmap=True):
        super(BaseMinimap, self).__init__(parent, panelname, registerlisteners)
        
        # The hud might be created in the middle of a game, so we likely didn't get the game_newmap event
        if bsetmap:
            self.SetMap(srcmgr.levelname)
        
    def Reset(self):
        pass
            
    def SetMap(self, mapname):    
        self.Reset()
        
        # TODO: Check for changes?
            
        resfilename = os.path.join('maps', mapname + '.res')
        values = LoadFileIntoDictionaries(resfilename)
        if not values:
            Warning("Error! hud_old_minimap.HudMinimap.SetMap: couldn't load file %s\n" % (resfilename))
            self.SetMapDefaults()
            return

        # Try to apply settings
        self.minimap_material = values.get('material', None)
        self.maporigin.x = float(values.get('pos_x', -5120.0))
        self.maporigin.y = float(values.get('pos_y', 5120.0))
        self.mapscale = float(values.get('scale', 10.0))
        self.rotatemap = bool(int(values.get('rotate', False)))
        self.fullzoom = float(values.get('zoom', 1.0))

    def SetMapDefaults(self):
        self.minimap_material = None
        self.maporigin.x = -5120.0
        self.maporigin.y = 5120.0
        self.mapscale = 10.0
        self.rotatemap = False
        self.fullzoom = 1.0