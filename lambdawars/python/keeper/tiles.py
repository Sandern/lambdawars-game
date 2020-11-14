from srcbase import FL_STATICPROP, MOVETYPE_NONE, SOLID_BBOX, SOLID_VPHYSICS, EF_NODRAW, DONT_BLEED, Color
from vmath import Vector, QAngle, anglemod
from entities import IMouse, EFL_SERVER_ONLY, DENSITY_NONE
import ndebugoverlay 
from _navmesh import NavMeshGetPathDistance
from fow import FogOfWarMgr
from gameinterface import ConVar, FCVAR_CHEAT
from gamerules import gamerules
from collections import defaultdict
from core.dispatch import receiver
from core.signals import postlevelshutdown, FireSignalRobust
from core.units import CreateUnit
from .signals import updatealltasks
import playermgr

if isclient:
    from entities import C_BaseAnimating as BaseClass
    from srcbase import RenderMode_t
else:
    from entities import CBaseAnimating as BaseClass
    
from .taskqueue import taskqueues
    
if isserver:
    dk_tile_debug = ConVar('dk_tile_debug', '0', FCVAR_CHEAT)
    
tiles = defaultdict(set)
tilespertype = defaultdict(lambda : defaultdict(set))
nonblocktiles = defaultdict(set)
lightkeys = set()

#tilesneighbors = defaultdict(lambda : defaultdict(set)) # [ownernumber][type]

@receiver(postlevelshutdown)
def LevelPostShutdown(sender, **kwargs):
    ClearTileLists()
    
def ClearTileLists():
    # Ensure all lists are empty
    tiles.clear()
    tilespertype.clear()
    nonblocktiles.clear()
    lightkeys.clear()
    
def SpawnTile(cls, owner, key, origin, ownernumber=1):
    #modelinfo.FindOrLoadModel(cls.modelname)
    if isclient:
        tile = cls()
        tile.owner = owner
        tile.key = key
        #tile.SetDistanceFade(2300.0, 2300.0)
        tile.SetDistanceFade(1500.0, 1500.0)
        #tile.SetDistanceFade(250.0, 250.0)
        tile.SetOwnerNumber(ownernumber)
        if tile.InitializeAsClientEntity(tile.modelname, False):
            tile.SetAbsOrigin(origin)
            tile.Spawn()
        else:
            print('SpawnTile: Failed to initialize client entity')
            tile = None
    else:
        tile = cls()
        tile.owner = owner
        tile.key = key
        tile.AddEFlags(EFL_SERVER_ONLY)
        tile.SetAbsOrigin(origin)
        tile.SetOwnerNumber(ownernumber)
        tile.PostConstructor(tile.type)
        tile.Spawn()
    return tile
    
# Stub for accessing tiles outside the world
class Nothing(object):
    type = 'none'
    owner = None
    key = (0,0)
    isblock = False
    isdiggable = False
    
    @staticmethod
    def Activate(): pass
    @staticmethod
    def Remove(): pass
    @staticmethod
    def OnNeighborChanged(othertile): pass
    @staticmethod
    def Select(): pass
    @staticmethod
    def Deselect(): pass
    
    def __bool__(self):
        return False
        
def GenerateModelCases(models):
    shiftbits = lambda bits: bits[1:] + bits[:1]
    
    generatetestbits = list(models.keys())
    for testbits in generatetestbits:
        yaw = anglemod(models[testbits][1].y)
        newtestbits = testbits
        for i in range(0, 3):
            yaw = anglemod(yaw - 90.0)
            newtestbits = shiftbits(newtestbits)
            
            if newtestbits not in models:
                models[newtestbits] = (models[testbits][0], QAngle(0, yaw, 0))
    
class TileBase(BaseClass, IMouse):
    """ Base tile, used for various different type of tiles. """
    mins = -Vector(40, 40, 0)
    maxs = Vector(40, 40, 112)
    #: Type of this tile
    type = 'nothing'
    #: The keeper world
    owner = None
    #: Our position in the grid
    key = (0,0)
    #: Is it a block?
    isblock = False
    #: Is it a diggable block?
    isdiggable = False
    #: In case the tile is claimable, this is used when an imp is claiming it.
    impassigned = None
    #: If true, it is added to the non block tiles list. Creatures may use this to wander to random tiles.
    walkabletile = False
    #: If true, the player can sell these tiles if the player owns them
    sellable = False
    #: Color of this tile on the minimap.
    minimapcolor = Color(0, 0, 0, 0)
    #: Model dictionary for different cases.
    #: The different cases are encoded as a bit string.
    #: Correspond to the following keys: [(x-1, y), (x, y-1), (x+1, y), (x, y+1)].
    #: The code will rotate to try to match a case.
    models = {
        #'0000' : ('', QAngle(0.0, 0.0, 0.0)),
        #'1000' : ('', QAngle(0.0, 0.0, 0.0)),
        #'1100' : ('', QAngle(0.0, 0.0, 0.0)),
        #'1110' : ('', QAngle(0.0, 0.0, 0.0)),
        #'1010' : ('', QAngle(0.0, 0.0, 0.0)),
    }
    
    previewmodelname = None
    connectedareas = None
    tileactive = False
    
    def __init__(self):
        BaseClass.__init__(self)
        IMouse.__init__(self)
        
        self.SetForceAllowVPhysics()
        
        self.neighbors = {}

        if isserver:
            self.SetDensityMapType(DENSITY_NONE)
            
    def GetIMouse(self):
        return self
        
    if isserver:
        def OnCursorEntered(self, player):
            if dk_tile_debug.GetBool():
                 self.debugoverlays = 1 # Activates calling DrawDebugGeometryOverlays
                #self.EntityText(0, self.DebugPrint(), 2.0)
                
        def OnCursorExited(self, player):
            if dk_tile_debug.GetBool():
                 self.debugoverlays = 0
                #self.EntityText(0, self.DebugPrint(), 2.0)
                
        def DrawDebugGeometryOverlays(self):
            #ndebugoverlay.Text(self.GetAbsOrigin(), self.DebugPrint(), False, gpGlobals.frametime)
            self.EntityText(0, self.DebugPrint(), 0)
            
    #def OnHoverPaint(self):
    #    if dk_tile_debug.GetBool():
    #        ndebugoverlay.Text(self.GetAbsOrigin(), self.DebugPrint(), False, gpGlobals.frametime)
              
    def DebugPrint(self):
        return '%s: %s, owner: %d' % (self.type, str(self.key), self.GetOwnerNumber()) + \
               ', height: %.0f' % (FogOfWarMgr().GetHeightAtPoint(self.GetAbsOrigin()))
        
    def GenerateTestBitString(self):
        testbits = ''
        for key in self.neighborkeys:
            if key not in self.neighbors:
                testbits += '0'
                continue
            tile = self.neighbors[key]
            if not tile:
                testbits += '0'
                continue
            if tile.type == self.type:
                testbits += '1'
            else:
                testbits += '0'
        return testbits
        
    @classmethod
    def PrecacheBlockModels(cls):
        cls.modelindex = cls.PrecacheModel(cls.modelname)
        cls.modelindices = {}
        for key, info in cls.models.items():
            cls.modelindices[key] = (cls.PrecacheModel(info[0]), info[1])
        
    def UpdateModel(self):
        """ The task of UpdateModel is to select the correct model depending
            on the surrounding tile types. """
        if self.previewmodelname:
            self.SetModel(self.previewmodelname)
            return
        # Observe neighbors
        testbits = self.GenerateTestBitString()
        
        modelindex = None
        if testbits in self.modelindices:
            modelindex, angles = self.modelindices[testbits]
            self.SetAbsAngles(angles)
 
        if modelindex == None:
            modelindex = self.modelindex
            #if self.isblock:
            #    PrintWarning('UpdateModel: failed to find model for case %s (type: %s)\n' % (testbits, str(self)))
        
        self.SetModelIndex(modelindex)
    
        self.CreateVPhysics()

    def Spawn(self):
        super().Spawn()
        
        #self.SetBloodColor(DONT_BLEED)
        
        # NOTE: Don't change the order of neighborkeys! Selecting the model depends on it.
        x, y = self.key
        self.neighborkeys = [(x-1, y), (x, y-1), (x+1, y), (x, y+1)] 
        
        h = self.GetHandle()
        ownernumber = self.GetOwnerNumber()
        tiles[ownernumber].add(h)
        tilespertype[ownernumber][self.type].add(h)
        if self.walkabletile:
            nonblocktiles[ownernumber].add(h)
        self.connectedareas = set([h])
        self.tileactive = True
        
        # Already done in UpdateModel:
        self.SetSolid(SOLID_BBOX)
        self.SetMoveType(MOVETYPE_NONE)
        self.SetCollisionBounds(self.mins, self.maxs)
        self.CollisionProp().MarkPartitionHandleDirty()
        
        if isserver:
            self.AddFlag(FL_STATICPROP)
            
        if isclient:
            POSITION_CHANGED = 0x1
            ANGLES_CHANGED = 0x2
            VELOCITY_CHANGED = 0x4
            self.InvalidatePhysicsRecursive(POSITION_CHANGED | ANGLES_CHANGED | VELOCITY_CHANGED)
            self.UpdatePartitionListEntry()
            #self.UpdateVisibility()
            #self.CreateShadow() # TODO: Seems bugged
             
            # Reset interpolation history, so it doesn't contains shit
            # -> shouldn't do anything for client side created entities...
            #    Apparently it does do something, since it fucks up the angles of all tiles.
            #self.ResetLatched() 
            
            #pos = self.GetAbsOrigin()
            #fullsize = 32768.0 / 8.0 #32768.0
            #hsize = fullsize / 2.0
            #gamerules.minimaptex.SetPixel(int(((pos.x+hsize)/fullsize)*512), int(((pos.y+hsize)/fullsize)*512), self.minimapcolor)
            gamerules.minimaptex.SetPixel(self.key[0]+int(round(self.owner.gridsize[0]/2)), 
                        self.key[1]+int(round(self.owner.gridsize[1]/2)), self.minimapcolor)
             
        self.CollisionProp().UpdatePartition()
        
        #self.CreateVPhysics()
        
        origin = self.GetAbsOrigin()
        mins = origin + self.mins
        maxs = origin + self.maxs
        if self.isblock:
            FogOfWarMgr().ModifyHeightAtExtent(mins, maxs, maxs.z + 256.0)
        else:
            FogOfWarMgr().ModifyHeightAtExtent(mins, maxs, 0.0)
            
    def Activate(self):
        """ Called after the tile is spawned.
        
            When creating the world, this is called after all tiles are spawned.
        """
        self.BuildNeighbors()
        # NOTE: Don't need to tell neighbors about change when the world is being created, 
        #       since they are all about to be activated too
        if not self.owner.loadingmap: 
            gamerules.ScheduleUpdateNavMesh(self.key)
            self.TellNeighborsChanged()
            
    def CreateVPhysics( self ):
        if self.VPhysicsGetObject(): return True # Do not recreate the physics object
        
        self.SetSolid(SOLID_VPHYSICS)
        self.VPhysicsInitStatic()
        self.SetSolid(SOLID_BBOX) # Slam back
        #self.SetCollisionBounds(self.mins, self.maxs)
        #self.CollisionProp().MarkPartitionHandleDirty()
        return True
        
    def UpdateOnRemove(self):
        if self.owner.worldisremoving:
            super().UpdateOnRemove()
            return
        
        for neighbor in self.neighbors.values():
            if not neighbor:
                continue
            neighbor.OnNeighborRemoved(self)
            
        h = self.GetHandle()
        ownernumber = self.GetOwnerNumber()
            
        if taskqueues != None:
            for o, tq in taskqueues.items():
                tq.OnTileRemoved(h)
        
        tiles[ownernumber].discard(h)
        tilespertype[ownernumber][self.type].discard(h)
        nonblocktiles[ownernumber].discard(h)
        self.tileactive = False
        
        self.connectedareas.discard(h)

        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
        self.owner = None
        
    def OnChangeOwnerNumber(self, oldownernumber):
    #    print('OnChangeOwnerNumber: do something')
    
        if isclient:
            c = playermgr.dbplayers[self.GetOwnerNumber()].color
            self.SetTeamColor(Vector(c.r()/255.0, c.g()/255.0, c.b()/255.0)) 
    
        h = self.GetHandle()
        if not self.tileactive:
            return
           
        # Remove from old
        tilespertype[oldownernumber][self.type].discard(h)
        tiles[oldownernumber].discard(h)
        nonblocktiles[oldownernumber].discard(h)

        # Add to new
        ownernumber = self.GetOwnerNumber()
        tiles[ownernumber].add(h)
        tilespertype[ownernumber][self.type].add(h)
        if self.walkabletile:
            nonblocktiles[ownernumber].add(h)
        
        from .keeperworld import ClientChangeTileOwner # FIXME
        ClientChangeTileOwner(self.key, self.GetOwnerNumber())

    def BuildNeighbors(self):
        """ Called on tile spawn, to build a list of neighbors + information about them. """
        tilegrid = self.owner.tilegrid
        for key in self.neighborkeys:
            tile = tilegrid[key]
            if not tile:    
                continue
            self.OnNeighborChanged(tile)
        
    def TellNeighborsChanged(self):
        """ Called on tile spawn, to notify the neighbors and update their neighbor list. """
        tilegrid = self.owner.tilegrid
        for key in self.neighborkeys:
            tile = tilegrid[key]
            if not tile:    
                continue
            tile.OnNeighborChanged(self)
                        
    def OnNeighborChanged(self, othertile):
        """ Updates neighbor information. """
        self.neighbors[othertile.key] = othertile
        
        #if isclient:
        self.UpdateModel()
        #else:
        #    self.SetThink(self.UpdateModel, gpGlobals.curtime, 'UpdateModel') # Delay model updating by a frame
            
        # Update connected areas
        if not self.isblock and not othertile.isblock:
            if self.connectedareas != othertile.connectedareas: #self not in othertile.connectedareas:
                if len(self.connectedareas) > len(othertile.connectedareas):
                    self.MergeAreaSet(othertile.connectedareas)
                else:
                    othertile.MergeAreaSet(self.connectedareas)

    def OnNeighborRemoved(self, othertile):
        try:
            if self.neighbors[othertile.key] == othertile:
                del self.neighbors[othertile.key]
        except KeyError:
            PrintWarning('OnNeighborRemoved: tile at %s not in our neighbors list!\n' % (str(othertile.key)))

    def DrawDebugOverlay(self):
        ndebugoverlay.Box(self.GetAbsOrigin(), self.mins, self.maxs, 255, 0, 0, 255, 0.1)
        
    def IsReachable(self, unit):
        unittile = self.owner.tilegrid[unit.key]
        for tile in self.neighbors.values():
            if not tile or tile.isblock: 
                continue
            if unittile.connectedareas != tile.connectedareas:
                continue
            #if NavMeshGetPathDistance(unit.GetAbsOrigin(), tile.GetAbsOrigin()) < 0:
            #    continue
            return True
            
        return False
        
    def MergeAreaSet(self, areas):
        self.connectedareas |= areas
        for tile in areas:
            tile.connectedareas = self.connectedareas

        if taskqueues != None:
            for owner in taskqueues.keys():
                FireSignalRobust(updatealltasks, owner=owner)
            
    def IsOwnedByPlayer(self, player):
        return True
        
    def IsClaimable(self, ownernumber):
        return False
        
    def Claim(self, ownernumber):
        pass
        
    def HasOneOrMoreNonBlockNeighbors(self):
        """ A block is reachable if it has at least one normal tile next to it.
            In that case we can add it as a task if it is selected.
            Still doesn't guarantee the imp can reach it, so upon finding imps 
            an additional check will need to be done.
        """
        for key in self.neighborkeys:
            tile = self.owner.tilegrid[key]
            if tile.isblock:    
                continue
            return True
        return False
        
    def SetPreview(self, preview=None):
        self.previewmodelname = preview
        self.UpdateModel()
        
        if not preview:
            self.SetRenderMode(RenderMode_t.kRenderNormal)
            self.SetRenderColor(255, 255, 255)
            self.SetRenderAlpha(255)
        else:
            self.SetRenderMode(RenderMode_t.kRenderTransTexture)
            self.SetRenderColor(0, 255, 0)
            self.SetRenderAlpha(255)
        
class TileGroundBase(TileBase):
    """ Something you can walk on. """
    
    modelname = 'models/keeper/ground1.mdl'
    mins = -Vector(40, 40, 0)
    maxs = Vector(40, 40, 24)
    createnavarea = True
    walkabletile = True

    def Spawn(self):
        super().Spawn()
        
        if isserver:
            if self.createnavarea:
                origin = self.GetAbsOrigin()
                origin.z += self.maxs.z + 4.0
        
    def IsOwnedByPlayer(self, player):
        return player.GetOwnerNumber() == self.GetOwnerNumber()

    def IsClaimable(self, ownernumber):
        return self.GetOwnerNumber() != ownernumber
        
    def OnNeighborChanged(self, othertile):
        """ Updates neighbor information. """
        super().OnNeighborChanged(othertile)

        h = self.GetHandle()

        o = othertile.GetOwnerNumber()
        if taskqueues is not None and o >= 2:
            tq = taskqueues[o]
            if self.IsClaimable(o):
                tq.InsertClaimTileTask(h)
        
class TileGround(TileGroundBase):
    type = 'ground'

    def IsClaimable(self, ownernumber):
        return True
        
    def Claim(self, ownernumber):
        self.owner.CreateTile('tile', self.key, ownernumber)
        
class TilePlayer(TileGroundBase):
    type = 'tile'
    modelname = 'models/keeper/tile1.mdl'
    
    def Claim(self, ownernumber):
        self.SetOwnerNumber(ownernumber)
        
class PortalTile(TileGroundBase):
    type = 'portal'
    modelname = 'models/keeper/tile1.mdl'
    portal = None
    
    def Spawn(self):
        super().Spawn()
        
        x, y = self.key
        self.portalkeys = [(x-1, y), (x, y-1), (x+1, y), (x, y+1),
                      (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)]
    if isserver:
        def Activate(self):
            super().Activate()
            
            if self.IsPortalCenter():
                self.portal = CreateUnit('dk_portal', self.GetAbsOrigin() + Vector(0, 0, 24.0), owner_number=self.GetOwnerNumber())
                
                self.portal.portaltiles.append(self.GetHandle())
                tilegrid = self.owner.tilegrid
                for key in self.portalkeys:
                    tile = tilegrid[key]
                    self.portal.portaltiles.append(tile.GetHandle())
                    tile.portal = self.portal

    def IsPortalCenter(self):
        tilegrid = self.owner.tilegrid
        for key in self.portalkeys:
            tile = tilegrid[key]
            if not tile or tile.type != 'portal':    
                return False
        return True

    def Claim(self, ownernumber):
        if self.portal:
            self.portal.Claim(ownernumber)

class HeartTile(TileGroundBase):
    type = 'heart'
    modelname = 'models/keeper/tile1.mdl'
    heart = None
    createnavarea = False
    walkabletile = False
    
    def Spawn(self):
        super().Spawn()
        
        x, y = self.key
        self.heartkeys = [(x-1, y), (x, y-1), (x+1, y), (x, y+1),
                      (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)]
                      
    def IsClaimable(self, ownernumber):
        return False
        
    if isserver:
        def Activate(self):
            super().Activate()
            
            if self.IsHeartCenter():
                self.heart = CreateUnit('dk_heart', self.GetAbsOrigin(), owner_number=self.GetOwnerNumber())
                
                self.heart.hearttiles.append(self.GetHandle())
                tilegrid = self.owner.tilegrid
                for key in self.heartkeys:
                    tile = tilegrid[key]
                    self.heart.hearttiles.append(tile.GetHandle())
                    tile.heart = self.heart
                    
    def IsHeartCenter(self):
        tilegrid = self.owner.tilegrid
        for key in self.heartkeys:
            tile = tilegrid[key]
            if not tile or tile.type != 'heart':    
                return False
        return True
        
class WaterTile(TileGroundBase):
    type = 'water'
    modelname = 'models/keeper/water.mdl'
    mins = -Vector(40, 40, 16)
    maxs = Vector(40, 40, 8)
    
    def IsClaimable(self, ownernumber):
        return False
