from vmath import VectorNormalize, Vector, vec3_origin
from core.abilities import AbilityTarget, AbilityBase
from keeper.tiles import TileGroundBase
from keeper.common import TestSwapMinMax
from entities import entity, CBaseEntity
import random
from core.hud import InsertResourceIndicator
from core.resources import GiveResources
from core.signals import postlevelshutdown
from core.dispatch import receiver

from collections import defaultdict
from itertools import product

if isserver:
    from entities import CreateEntityByName, DispatchSpawn, FL_EDICT_ALWAYS
else:
    from vgui import cursors
    
controllerspertype = defaultdict(lambda : defaultdict(set))

@receiver(postlevelshutdown)
def LevelPostShutdown(sender, **kwargs):
    ClearControllerLists()
    
def ClearControllerLists():
    # Ensure all lists are empty
    controllerspertype.clear()
    
# Room entities
@entity('dk_room_controller', networked=True)
class RoomController(CBaseEntity):
    roomcontrolleractive = False
    
    def __init__(self):
        super(RoomController, self).__init__()
        
        self.tiles = set()
        self.creaturesusingroom = set()
        
    def Spawn(self):
        super(RoomController, self).Spawn()
        
        h = self.GetHandle()
        ownernumber = self.GetOwnerNumber()
        controllerspertype[ownernumber][self.GetClassname()].add(h)
        
        self.roomcontrolleractive = True
        
    def UpdateOnRemove(self):
        h = self.GetHandle()
        ownernumber = self.GetOwnerNumber()

        controllerspertype[ownernumber][self.GetClassname()].discard(h)
        self.roomcontrolleractive = False

        # ALWAYS CHAIN BACK!
        super(RoomController, self).UpdateOnRemove()

    def OnChangeOwnerNumber(self, oldownernumber):
        h = self.GetHandle()
        if not self.roomcontrolleractive:
            return
           
        clsname = self.GetClassname()
           
        # Remove from old
        controllerspertype[oldownernumber][clsname].discard(h)

        # Add to new
        ownernumber = self.GetOwnerNumber()
        controllerspertype[ownernumber][clsname].add(h)
        
    def RandomTile(self):
        return random.sample(self.tiles, 1)[0] if self.tiles else None
        
    if isserver:
        def UpdateTransmitState(self):
            return self.SetTransmitState(FL_EDICT_ALWAYS)
    
        def AddTile(self, tile):
            self.tiles.add(tile.GetHandle())
            tile.roomcontroller = self.GetHandle()
            self.UpdatePosition()
            
        def RemoveTile(self, tile):
            self.tiles.discard(tile.GetHandle())
            tile.roomcontroller = None
            self.UpdatePosition()
            if not self.tiles:
                self.Remove() # No longer needed
    
        def Merge(self, roomcontroller):
            ''' Merge another room controller data and remove
                that controller. '''
            self.tiles |= roomcontroller.tiles
            for tile in roomcontroller.tiles:
                tile.roomcontroller = self.GetHandle()
            roomcontroller.Remove()
            self.UpdatePosition()
        
        def UpdatePosition(self):
            pos = Vector(vec3_origin)
            for tile in self.tiles:
                pos += tile.GetAbsOrigin()
            pos /= len(self.tiles)
            self.SetAbsOrigin(pos)
        
class TileRoom(TileGroundBase):
    roomcontroller = None
    sellable = True
    roomcontrollerclassname = 'dk_room_controller'
    
    if isserver:
        def Spawn(self):
            super(TileRoom, self).Spawn()
        
            # Notified neighbors of the change in the the base spawn method;
            # If this tile still has no room controller, create one.
            if not self.roomcontroller:
                self.roomcontroller = self.CreateRoomController()
                self.roomcontroller.AddTile(self)
                    
        def UpdateOnRemove(self):
            if self.roomcontroller:
                self.roomcontroller.RemoveTile(self)
        
            # ALWAYS CHAIN BACK!
            super(TileRoom, self).UpdateOnRemove()
        
        def CreateRoomController(self):
            roomcontroller = CreateEntityByName(self.roomcontrollerclassname)
            roomcontroller.SetOwnerNumber(self.GetOwnerNumber())
            DispatchSpawn(roomcontroller)
            return roomcontroller
    
        def OnNeighborChanged(self, othertile):
            super(TileRoom, self).OnNeighborChanged(othertile)
            
            if othertile.type != self.type:
                return
            
            if othertile.roomcontroller:
                if not self.roomcontroller:
                    othertile.roomcontroller.AddTile(self)
                elif othertile.roomcontroller != self.roomcontroller:
                    self.roomcontroller.Merge(othertile.roomcontroller)
            
    
# Spawns a room
class AbilityCreateRoom(AbilityBase):
    startsound = ''
    roomcls = None
    
    startkey = None
    endkey = None
    
    def Init(self):
        # Can't start this type of ability while having left pressed
        if self.player.IsLeftPressed():
            self.player.ClearMouse()
            
        self.player.SetSingleActiveAbility(self)
        
        self.currenttiles = set()
        
        super(AbilityCreateRoom, self).Init()

    # Mouse methods
    def GetCurrentKey(self):
        from keeper import keeperworld # FIXME
        kw = keeperworld.keeperworld
        
        data = self.player.GetMouseData()
        return kw.GetKeyFromPos(data.endpos)
    
    def OnLeftMouseButtonPressed(self):
        assert(not self.stopped)
        
        self.startkey = self.GetCurrentKey()
        
        return True
        
    def OnLeftMouseButtonReleased(self):
        assert(not self.stopped)
        
        self.endkey = self.GetCurrentKey()
        
        tiles = self.GetTiles()
        
        if isserver and tiles:
            self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), 'Spells.CreateRoom')
            minkey, maxkey = TestSwapMinMax(self.startkey, self.endkey)
            #print('Creating tiles from %s to %s' % (str(minkey), str(maxkey)))
            for x, y in product(list(range(minkey[0], maxkey[0]+1)), 
                        list(range(minkey[1], maxkey[1]+1))):
                if not self.CreateRoomAt((x, y)):
                    break
                
        self.startkey = None # Clear for creating the next room
        
        return True
        
    def OnRightMouseButtonPressed(self):
        if isserver:
            self.Cancel(debugmsg='right mouse button pressed')
        return True  
        
    def OnMouseLost(self):
        if isserver:
            self.Cancel(debugmsg='mouse lost')
            
    def IsValidTile(self, tile):
        return tile and tile.type == 'tile'
        
    def GetTiles(self):
        from keeper import keeperworld # FIXME
        kw = keeperworld.keeperworld
        
        tiles = set()
        minkey, maxkey = TestSwapMinMax(self.startkey, self.endkey)
        for x, y in product(list(range(minkey[0], maxkey[0]+1)), 
                    list(range(minkey[1], maxkey[1]+1))):
            tile = kw.tilegrid[(x, y)]
            if self.IsValidTile(tile):
                tiles.add(tile.GetHandle())
        return tiles
        
    def CreateRoomAt(self, key):
        ''' Tries to create the given room tile at the key.
            Skips if we can't create it at the key.
            Cancels if we don't have enough resources.'''
        from keeper import keeperworld # FIXME
        kw = keeperworld.keeperworld
    
        tile = kw.tilegrid[key]
        
        if tile.type != 'tile':
            return True
            
        if not self.TakeResources(refundoncancel=False):
            self.Cancel(cancelmsg='#Ability_NotEnoughResources')
            return False
    
        tile = kw.CreateTile(self.roomcls.type, tile.key, self.player.GetOwnerNumber())
        if tile:
            if self.costs:
                goldvalue = self.costs[0][0][1]
                tile.sellvalue = int(goldvalue / 2.0)
            else:
                goldvalue = 0
            InsertResourceIndicator(tile.GetAbsOrigin(), '-%s' % (str(goldvalue)))
        return True
        
    if isclient:
        def GetPreviewModel(self):
            return self.roomcls.modelname
    
        def Cleanup(self):
            super(AbilityCreateRoom, self).Cleanup()
            
            for tile in self.currenttiles:
                if tile: tile.SetPreview(None)
    
        def Frame(self):
            if not self.startkey:
                return
                
            self.endkey = self.GetCurrentKey()
            
            newcurtiles = self.GetTiles()
            
            removetiles = self.currenttiles - newcurtiles
            addtiles = newcurtiles - self.currenttiles
            
            for tile in removetiles:
                if tile: tile.SetPreview(None)
                
            for tile in addtiles:
                if tile: tile.SetPreview(self.GetPreviewModel())
            
            self.currenttiles = newcurtiles
            
        def GetCursor(self):
            return cursors.GetCursor('resource/arrows/ability_cursor.ani')
        
class AbilitySellRoom(AbilityCreateRoom):
    name = 'sellroom'
    displayname = 'Sell'
    description = 'Sells a room at half of the original price.'

    def IsValidTile(self, tile):
        return tile and tile.GetOwnerNumber() == self.player.GetOwnerNumber() and tile.sellable
    
    if isserver:
        def CreateRoomAt(self, key):
            from keeper import keeperworld # FIXME
            kw = keeperworld.keeperworld
        
            tile = kw.tilegrid[key]
            
            if not self.IsValidTile(tile):
                return True
                
            pos = tile.GetAbsOrigin()

            self.player.EmitAmbientSound(-1, self.player.GetAbsOrigin(), 'Spells.SellRoom')
            keeperworld.keeperworld.CreateTile('tile', key, self.player.GetOwnerNumber())
            
            GiveResources(self.player.GetOwnerNumber(), [('gold', tile.sellvalue)])
            InsertResourceIndicator(pos, '+%s' % (str(tile.sellvalue)))
            
            return True
            
    if isclient:
        def GetPreviewModel(self):
            return 'models/keeper/tile1.mdl'
    