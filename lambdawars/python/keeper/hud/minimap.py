from vmath import Vector2D
from core.hud import BaseHudMinimap
from vgui import CHudElement, GetClientMode, scheme, surface, FontVertex_t
from gamerules import gamerules
from ..signals import keeperworldloaded


class Minimap(CHudElement, BaseHudMinimap):
    def __init__(self):
        CHudElement.__init__(self, "Minimap")
        BaseHudMinimap.__init__(self, GetClientMode().GetViewport())
        
        self.followangle = False
        self.baserotation = 0.0
        
        keeperworldloaded.connect(self.OnKeeperWorldLoaded)
        
    def UpdateOnDelete(self):
        keeperworldloaded.disconnect(self.OnKeeperWorldLoaded)
        surface().DestroyTextureID(self.tilestextureid)
        self.tilestextureid = -1
        
    def ApplySchemeSettings(self, scheme_obj):
        super(Minimap, self).ApplySchemeSettings(scheme_obj)
            
    def PerformLayout(self):
        super(Minimap, self).PerformLayout()
        
        xinset = scheme().GetProportionalScaledValueEx(self.GetScheme(), 5)
        self.SetPos(scheme().GetProportionalScaledValueEx(self.GetScheme(), xinset),
                    scheme().GetProportionalScaledValueEx(self.GetScheme(), xinset))
                     
        wide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 75)
        tall = scheme().GetProportionalScaledValueEx(self.GetScheme(), 75)
        self.SetSize(wide, tall)
        
    def OnKeeperWorldLoaded(self, keeperworld, **kwargs):
        print('On keeper world loaded minimap')
        self.minimap_material = None
        self.maporigin.x = -keeperworld.worldhalfx
        self.maporigin.y = keeperworld.worldhalfy
        maxsize = max(keeperworld.worldhalfx, keeperworld.worldhalfy) * 2
        self.mapscale = maxsize / 1024.0
        self.rotatemap = False
        self.fullzoom = 1.0
        
        minimapsize = float(gamerules.minimapsize)
        self.coordx = keeperworld.gridsize[0] / minimapsize
        self.coordy = keeperworld.gridsize[1] / minimapsize
        
        # load blocks texture
        self.tilestextureid = surface().CreateNewTextureID()
        #engine.ClientCommand('mat_reloadmaterial vgui/keeper/minimap')
        surface().DrawSetTextureFile(self.tilestextureid, 'vgui/keeper/minimap', True, False)
        
        self.skdrawpoints = [
            FontVertex_t(Vector2D(0,0), Vector2D(0,self.coordy)),
            FontVertex_t(Vector2D(self.GetWide(),0) , Vector2D(self.coordx,self.coordy)),
            FontVertex_t(Vector2D(self.GetWide(),self.GetTall()), Vector2D(self.coordx,0)),
            FontVertex_t(Vector2D(0,self.GetTall()), Vector2D(0,0)),
        ]
        
    def SetMap(self, *args, **kwargs):
        pass
        
    def OnThink(self):    
        super(Minimap, self).OnThink()
        
        self.viewangle = 0.0
        
    def Paint(self):
        if not self.skdrawpoints:
            return
            
        self.drawpoints = self.skdrawpoints
    
        self.DrawMapTexture(self.drawpoints)
        self.DrawTiles()
        self.DrawFOW(self.drawpoints)
        self.DrawEntityObjects()
        self.DrawPlayerView()
        #self.DrawMapBoundaries()
        self.DrawPings()
        
        super(BaseHudMinimap, self).Paint()
        
    def DrawTiles(self):
        """ Draw that thing behind the minimap """
        if self.tilestextureid < 0 and gamerules.minimaptex.IsValid():
            return
            
        surface().DrawSetColor(255,255,255, 255)
        surface().DrawSetTexture(self.tilestextureid)
        #surface().DrawTexturedRect(0, 0, self.GetWide(), self.GetTall())
        surface().DrawTexturedPolygon(self.drawpoints)
        
    backgroundtexture = None
    tilestextureid = -1
    coordx = 1.0
    coordy = 1.0
    skdrawpoints = None
        