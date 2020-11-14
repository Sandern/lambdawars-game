from srcbase import IN_DUCK
from srcbuiltins import Color
from vmath import Vector
from core.abilities import AbilityBase
from core.decorators import clientonly
from gameinterface import engine
from fields import FloatField, BooleanField, ColorField

if isclient:
    from particles import CNewParticleEffect

class PlaceTool(AbilityBase):
    def Init(self):
        super().Init()
        
        self.assets = set()
        
        ''' Initializes the tool ability. '''
        if self.allowmultipleability:
            self.player.AddActiveAbility(self)
        else:
            self.player.SetSingleActiveAbility(self)
            
        #if isclient:
        #    self.placetoolparticle = CNewParticleEffect.Create(None, self.placetoolparticlename)
        #    self.UpdatePlaceToolParticle(self.GetPlaceOrigin())
        self.CreatePlaceToolParticle()
            
    def Cleanup(self):
        super().Cleanup()
    
        self.DestroyPlaceToolParticle()
        
    def OnLeftMouseButtonPressed(self):
        self.placingactive = True
        return True
        
    def OnLeftMouseButtonReleased(self):
        self.placingactive = False
        return True
            
    def OnRightMouseButtonPressed(self):
        if isclient:
            self.sizingplacetool = True
            self.lasty = self.player.GetMouseData().y
        return True
            
    def OnRightMouseButtonReleased(self):
        self.sizingplacetool = False
        return True
        
    def OnMouseLost(self):        
        ''' Lost mouse input because something cleared it. '''
        if isserver:
            self.Cancel(debugmsg='mouse lost')
        
    def GetPlaceOrigin(self):
        data = self.player.GetMouseData()
        placeorigin = data.groundendpos
        return placeorigin
        
    def Frame(self):
        if self.sizingplacetool and self.canresizeradius:
            newy = self.player.GetMouseData().y
            diff = self.lasty - newy
            if diff != 0:
                self.placetoolradius += 2.0 * diff
                self.placetoolradius = max(32.0, min(self.placetoolradius, 2048.0))
                engine.ServerCommand('wars_editor_setplacetoolradius %f' % (self.placetoolradius))
                self.lasty = newy
                #self.DestroyPlaceToolParticle()
                #self.CreatePlaceToolParticle()
                self.refreshparticletime = 0
    
        # Bugged particle crap...
        if self.refreshparticletime < gpGlobals.curtime:
            self.refreshparticletime = gpGlobals.curtime + 2.5
            self.DestroyPlaceToolParticle()
            self.CreatePlaceToolParticle()
    
        placeorigin = self.GetPlaceOrigin()
        self.UpdatePlaceToolParticle(placeorigin)
        
    @clientonly
    def CreatePlaceToolParticle(self):
        if self.placetoolparticle:
            return
            
        self.placetoolparticle = CNewParticleEffect.Create(None, self.placetoolparticlename)
        self.UpdatePlaceToolParticle(self.GetPlaceOrigin())
        
    @clientonly
    def DestroyPlaceToolParticle(self):
        if not self.placetoolparticle:
            return
            
        self.placetoolparticle.StopEmission(False, True, False, True)
        self.placetoolparticle = None
        
    @property
    def placecolor(self):
        return Vector(0, 1, 0)
    
    @clientonly
    def UpdatePlaceToolParticle(self, placeorigin):
        if not self.placetoolparticle:
            return
            
        self.placetoolparticle.SetControlPoint(0, placeorigin+Vector(0,0,1024))
        self.placetoolparticle.SetControlPoint(1, self.placecolor)
        self.placetoolparticle.SetControlPoint(2, Vector(self.placetoolradius, self.placetoolradius, 0))
        self.placetoolparticle.RecalculateBoundingBox()
        
    def Tick(self):
        if self.placingactive:
            self.DoPlace()
        
    def DoPlace(self):
        pass
        
    def IsValidAsset(self, asset):
        return True
        
    def AddPlaceToolAsset(self, asset):
        if not self.IsValidAsset(asset):
            return
        self.assets.add(asset)
        
    def RemovePlaceToolAsset(self, asset):
        self.assets.discard(asset)
        
    def SetPlaceToolDensity(self, density):
        self.density = density
        
    # Allowing multiple tools active at once
    allowmultipleability = False
    # Place tool particle name
    placetoolparticlename = 'unit_circle_ground'
    #: Place tool particle instance
    placetoolparticle = None
    #: Active radius of the place tool.
    placetoolradius = FloatField(value=256.0)
    #: Whether or not the tool can be resized from the default radius
    canresizeradius = BooleanField(value=True)
    #: Active density
    density = FloatField(value=1.0)
    #: Whether or not to use the ground normal for placing props
    usegroundnormal = BooleanField(value=True)
    #: Whether or not to use the navigation mesh for finding positions
    usenavmesh = BooleanField(value=True)
    #: Ignore any placed clip
    ignoreclips = BooleanField(value=False)
    #: Color modifier
    color = ColorField(value=Color(255, 255, 255, 255))
    
    refreshparticletime = 0.0
    
    placingactive = False
    
    sizingplacetool = False
    lasty = 0