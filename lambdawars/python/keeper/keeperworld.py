from srcbase import (FSOLID_CUSTOMRAYTEST, FSOLID_CUSTOMBOXTEST)
from vmath import Vector

import math
import sys
import random
from collections import defaultdict
import traceback

from fields import GenericField
from entities import entity, DENSITY_NONE
from gameinterface import engine, concommand, FCVAR_CHEAT
from profiler import profile
from gamerules import gamerules
from utils import UTIL_GetPlayers
from playermgr import OWNER_ENEMY
from core.usermessages import usermessage
from core.signals import prelevelshutdown, FireSignalRobust, recast_mapmesh_postprocess
from core.units import PrecacheUnit
from particles import *
from .signals import keeperworldloaded
from navmesh import RecastMgr
from fow import FogOfWarMgr

from .levelloader import BaseLevelLoader, DK1LevelLoader

if isserver:
    from entities import CBaseEntity as BaseClass, FL_EDICT_ALWAYS, EFL_FORCE_CHECK_TRANSMIT, CTakeDamageInfo, gEntList
    from core.usermessages import CSingleUserRecipientFilter
    from core.units import CreateUnit, unitlistpertype
    from core.dispatch import receiver
    from core.signals import clientactive
    from utils import UTIL_PrecacheOther, UTIL_GetCommandClient
else:
    from entities import C_BaseEntity as BaseClass

    from .blockhovereffect import BlockSelectionRenderer
    
from .block import Block, BlockGold, BlockRock
from .tiles import SpawnTile, Nothing, TileGround, TilePlayer, PortalTile, HeartTile, WaterTile
from .rooms import RoomTreasure, RoomLair, RoomHatchery, RoomTraining, RoomLibrary, RoomWorkshop
from .common import *
import ndebugoverlay

keeperworld = None
lastlevel = ''
nextlevel = ''

@usermessage()
def ClientLoadMap(level, **kwargs):
    keeperworld.LoadMap(level)

@usermessage()
def ClientChangeTile(type, key, ownernumber, **kwargs):
    keeperworld.CreateTile(type, key, ownernumber)
    
@usermessage()
def ClientChangeTileOwner(key, ownernumber, **kwargs):
    keeperworld.tilegrid[key].SetOwnerNumber(ownernumber)
    
@usermessage()
def ClientFortifyBlock(key, **kwargs):
    tile = keeperworld.tilegrid[key]
    if not tile:
        return
    tile.Fortify()
    
if isserver:
    @receiver(clientactive)
    def NewClientActive(client, **kwargs):
        if not keeperworld:
            return
        filter = CSingleUserRecipientFilter(client)
        filter.MakeReliable()

        for key in keeperworld.changedkeys:
            tile = keeperworld.tilegrid[key]
            ClientChangeTile(tile.type, key, tile.GetOwnerNumber())
            
        if keeperworld.maploaded and not GetDungeonHeart(client.GetOwnerNumber()):
            print('New player with ownernumber %d' % (client.GetOwnerNumber()))
            keeperworld.AddPlayerDynamic(client.GetOwnerNumber())
            
    @receiver(prelevelshutdown)
    def PreLevelShutdown(**kwargs):
        # Kill keeperworld
        if keeperworld:
            keeperworld.Remove()
   
# Dictionary containing all tile types
tilemap = {
    TileGround.type : TileGround,
    TilePlayer.type : TilePlayer,
    WaterTile.type : WaterTile,
    PortalTile.type : PortalTile,
    HeartTile.type : HeartTile,
    
    RoomTreasure.type : RoomTreasure,
    RoomLair.type : RoomLair,
    RoomHatchery.type : RoomHatchery,
    RoomTraining.type : RoomTraining,
    RoomLibrary.type : RoomLibrary,
    RoomWorkshop.type : RoomWorkshop,
    
    Block.type : Block,
    BlockGold.type : BlockGold,
    BlockRock.type : BlockRock,
}

@entity('keeperworld', networked=True)
class KeeperWorld(BaseClass):
    def __init__(self):
        global keeperworld
        
        super().__init__()
        
        self.tilegrid = defaultdict(lambda : Nothing())

        keeperworld = self
        gamerules.keeperworld = self

        if isserver:
            self.SetDensityMapType(DENSITY_NONE)
    
    def Precache(self):
        super().Precache()
        
        if isserver:
            PrecacheUnit('dk_portal')
            PrecacheUnit('dk_heart')
            UTIL_PrecacheOther('dk_gold')
            
            PrecacheUnit('unit_dk_marine')
        
        # Precache block models, save off the model indices
        for k, v in tilemap.items():
            v.PrecacheBlockModels()
            #v.modelindex = self.PrecacheModel(v.modelname)
            #v.modelindices = {}
            #for key, info in v.models.items():
            #    v.modelindices[key] = (self.PrecacheModel(info[0]), info[1])
        
        if isserver:
            # Precache sound scripts
            self.PrecacheScriptSound('Misc.DigMark')
            
            self.PrecacheScriptSound('Spells.Generic')
            self.PrecacheScriptSound('Spells.PossessCreature')
            self.PrecacheScriptSound('Spells.CreateImp')
            
            self.PrecacheScriptSound('Rooms.BuildTreasureRoom')
            
            # Particles
            PrecacheParticleSystem('grub_death_juice')
            PrecacheParticleSystem('landingbay_lift_fog_volume')
            
    if isserver:
        def Spawn(self):
            global nextlevel
            
            self.Precache()
            
            self.AddEFlags(EFL_FORCE_CHECK_TRANSMIT)
            self.AddSolidFlags(FSOLID_CUSTOMRAYTEST|FSOLID_CUSTOMBOXTEST)
        
            super().Spawn()
            
            recast_mapmesh_postprocess.connect(self.PostProcessMapMesh)
            
            self.LoadMap((nextlevel, random.randint(0, sys.maxsize)))
            nextlevel = ''
            
        def UpdateTransmitState(self):
            return self.SetTransmitState(FL_EDICT_ALWAYS)
    else:
        def Spawn(self):
            self.Precache()
            
            super().Spawn()
               
    # Cleaning up
    def UpdateOnRemove(self):
        global keeperworld
        
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
        if isserver:
            recast_mapmesh_postprocess.disconnect(self.PostProcessMapMesh)
        
        if keeperworld == self:
            keeperworld = None
        if gamerules.keeperworld == self:
            gamerules.keeperworld = None
            
        self.ClearTileGrid()
        
        if isclient:
            self.blockselectioneffect.Destroy()
            self.blockselectioneffect = None
            
    def ClearTileGrid(self):
        self.worldisremoving = True
        
        # Remove all blocks
        errorsoccurred = False
        for b in self.tilegrid.values():
            if not b:
                continue
            try:
                b.Remove()
            except:
                errorsoccurred = True
        if errorsoccurred:
            PrintWarning('Errors occurred while destroying the tile grid\n')
        self.tilegrid.clear()
        
        self.worldisremoving = False
        
    # Loading the level
    if isclient:
        def OnLevelChanged(self):
            self.LoadMap(self.levelsettings)
        
    def LoadMap(self, levelsettings=None):
        global lastlevel
        
        #DestroyAllNavAreas()

        if not levelsettings:
            assert(isserver)
            levelname = None
            randomlevelseed = random.randint(0, sys.maxsize)
            levelsettings = (levelname, randomlevelseed)

        levelname, randomlevelseed = levelsettings
        
        lastlevel = levelname
        
        print('LoadMap: Loading map %s, seed: %d (client: %s)' % (levelname, randomlevelseed, isclient))
        
        # Set variables that will trigger client level loading
        if isserver:
            if levelsettings[0] == levelname:
                levelsettings = None
            
            # This will make the client load
            self.levelsettings = (levelname, randomlevelseed) 
        
        # Create a map which contains the type of each cell
        if levelname:
            if levelname[0] == '#':
                self.worldmap, self.gridsize = DK1LevelLoader().ReadWorldMap(folder='maps/keeperlevels', levelname=levelname[1:], randomseed=randomlevelseed)
            else:
                self.worldmap, self.gridsize = BaseLevelLoader().ReadWorldMap(levelname=levelname, randomseed=randomlevelseed)
        else:
            print('LoadMap: No level specified. Loading the default map.')
            self.worldmap, self.gridsize = BaseLevelLoader().ReadWorldMap(randomseed=randomlevelseed)
            
        self.xsize = self.cubesize[1].x - self.cubesize[0].x
        self.ysize = self.cubesize[1].y - self.cubesize[0].y
        
        gridxhalf = int(round(self.gridsize[0]/2))
        gridyhalf = int(round(self.gridsize[1]/2))
        
        self.worldhalfx = self.xsize * gridxhalf
        self.worldhalfy = self.ysize * gridyhalf
        
        bloat = self.xsize
        self.mins.x = -self.worldhalfx - bloat
        self.maxs.x = self.worldhalfx + bloat
        self.mins.y = -self.worldhalfy - bloat
        self.maxs.y = self.worldhalfy + bloat
        self.mins.z = 0
        self.maxs.z = self.cubesize[1].z

        if isclient:
            self.blockselectioneffect = BlockSelectionRenderer()
 
        if isserver:
            engine.ServerCommand('profiling_run 2')
            engine.ServerExecute()
        else:
            engine.ExecuteClientCmd('cl_profiling_run 2')

        self.LoadDelayed()
        
    @profile('KeeperLoadWorld')
    def LoadDelayed(self):  
        self.loadingmap = True

        # Create blocks where needed
        print('KEEPER SPAWNING TILES')
        gridxhalf = int(round(self.gridsize[0]/2))
        gridyhalf = int(round(self.gridsize[1]/2))
        for x in range(0, self.gridsize[0]):
            for y in range(0, self.gridsize[1]):
                key = (x-gridxhalf, y-gridyhalf)
                entry = self.worldmap[key]

                tile = self.CreateTile(entry['type'], key, entry['ownernumber'], loadingmap=True, activate=False)
                if 'sellable' in entry:
                    tile.sellable = entry['sellable']
                    
        # For each block, Activate and notify about the neighbors
        [tile.Activate() for tile in list(self.tilegrid.values())]
        
        if isserver:
            # Create initial navigation mesh
            RecastMgr().Build()
                
        self.loadingmap = False
        
        self.changedkeys = set() # Changed keys since map load

        if isserver:
            # Map is now loaded, but we should slam all players to their heart
            players = UTIL_GetPlayers()
            for player in players:
                if not player or not player.IsConnected():
                    continue
                    
                try:
                    player.TeleportToHeart()
                except:
                    PrintWarning('Failed to place player at dungeon heart: \n')
                    traceback.print_exc()
        else:
            FogOfWarMgr().ResetExplored()
                    
        FireSignalRobust(keeperworldloaded, keeperworld=self.GetHandle())
        
        self.maploaded = True
        
    def PostProcessMapMesh(self, mapmesh, bounds, **kwargs):
        if not bounds:
            tiles = list(filter(bool, self.tilegrid.values()))
            print('PostProcessMapMesh tiles: %d' % (len(tiles)))
            [mapmesh.AddEntity(tile) for tile in tiles]
        else:
            mins, maxs = bounds
            minkey = self.GetKeyFromPos(mins)
            maxkey = self.GetKeyFromPos(maxs)
            tilegrid = self.tilegrid
            for x in range(minkey[0]-1, maxkey[0]+1):
                for y in range(minkey[1]-1, maxkey[1]+1):
                    tile = tilegrid[(x,y)]
                    if not tile:
                        continue
                    mapmesh.AddEntity(tile)
            #tiles = list(filter(bool, self.tilegrid.values()))
            #[mapmesh.AddEntity(tile) for tile in tiles]
        
        self.AddEntObstaclesToNavMesh(mapmesh)
        
    def UpdateNavMeshPartial(self, mins, maxs):
        #minkey = self.GetKeyFromPos(mins)
        #maxkey = self.GetKeyFromPos(maxs)
    
        '''def PostProcessMapMesh(mapmesh, **kwargs):
            # TODO: Optimize, just need blocks covering the tiles
            #import time
            #starttime = time.time()
            
            #tilegrid = self.tilegrid
            #for x in range(minkey[0]-1, maxkey[1]+1):
            #    for y in range(minkey[1]-1, maxkey[1]+1):
            #        mapmesh.AddEntity(tilegrid[(x,y)])
            tiles = list(filter(bool, self.tilegrid.values()))
            #print('PostProcessMapMesh tiles: %d' % (len(tiles)))
            [mapmesh.AddEntity(tile) for tile in tiles]
            #print('Post processed tiles in %f time' % (time.time() - starttime))
            self.AddEntObstaclesToNavMesh(mapmesh)'''
            
        #recast_mapmesh_postprocess.connect(PostProcessMapMesh)
        #print('RecastMgr PARTIAL BUILD')
        RecastMgr().RebuildPartial(mins, maxs)
        #recast_mapmesh_postprocess.disconnect(PostProcessMapMesh)
                
    def AddEntObstaclesToNavMesh(self, mapmesh):
        for owner, unitspertype in unitlistpertype.items():
            for heart in unitspertype['dk_heart']:
                mapmesh.AddEntity(heart)
                    
    def CreateFromMap(self, blockmap):
        tiles = []
        for key, entry in blockmap.items():
            tile = self.CreateTile(entry['type'], key, entry['ownernumber'], activate=False)
            if 'sellable' in entry:
                tile.sellable = entry['sellable']
            tiles.append(tile)
            
        [tile.Activate() for tile in tiles]

    # Creating/destroying tiles
    def CreateTile(self, type, key, ownernumber=OWNER_ENEMY, loadingmap=False, activate=True):
        ''' Creates a new tile at the given position in the grid.
            Destroys the old tile (if any).
        '''
        # Destroy old tile if any
        if self.tilegrid[key].type != 'none':
            origin = self.tilegrid[key].GetAbsOrigin()
            self.DestroyTile(key)
            
        # Compute origin
        gridxhalf = int(round(self.gridsize[0]/2))
        gridyhalf = int(round(self.gridsize[1]/2))
        origin = Vector(
            -self.worldhalfx + self.xsize * (key[0]+gridxhalf),
            -self.worldhalfy + self.ysize * (key[1]+gridyhalf),
            0.0
        )
        
        # Create new tile
        self.tilegrid[key] = SpawnTile(tilemap[type], self, key, origin, ownernumber)
        if not self.tilegrid[key]:
            PrintWarning('CreateTile: Something went wrong!')
            return None
            
        if activate:
            self.tilegrid[key].Activate()
            
        if self.changedkeys:
            self.changedkeys.add(key)
        
        # Notify clients
        if isserver and not loadingmap:
            ClientChangeTile(type, key, ownernumber)
        
        return self.tilegrid[key]
            
    def DestroyTile(self, key):
        ''' Destroys the tile at the given position in the grid. '''
        tile = self.tilegrid[key]
        self.tilegrid[key] = Nothing()
        tile.Remove()
        
    def IsNearOtherHeart(self, pos, maxradius):
        heart = gEntList.FindEntityByClassnameWithin(None, "dk_heart", pos, maxradius)
        return bool(heart)
        
    def AddPlayerDynamic(self, ownernumber):
        # TODO: Make something better
        x, y = self.gridsize
        hx = int(x/2.0)
        hy = int(y/2.0)
        inset = 12
        
        for i in range(0, 100):
            heartkey = (random.randint(-hx+inset, hx-inset-1), random.randint(-hy+inset, hy-inset-1))
            pos = self.GetPosFromKey(heartkey)
            if not self.IsNearOtherHeart(pos, 1500.0):
                print('Found spot for heart')
                
                heartmap = {}
                BaseLevelLoader.CreateHeartAt(heartmap, heartkey, ownernumber)
                
                if random.random() < 0.5:
                    key = (heartkey[0]+5+random.randint(0,5), heartkey[1]+random.randint(-5,5))
                else:
                    key = (heartkey[0]+random.randint(-5,5), heartkey[1]+5+random.randint(0,5))
                BaseLevelLoader.CreatePortalAt(heartmap, key, 0)
        
                self.CreateFromMap(heartmap)
                
                engine.ServerCommand('say Added player with ownernumber %d dynamically\n;' % (ownernumber))
                    
                return
        
        engine.ServerCommand('say could not add player with ownernumber %d dynamically\n;' % (ownernumber))
        
    def DropUnitsAt(self, key, units, ownernumber=OWNER_ENEMY):
        tile = self.tilegrid[key]
        if tile.isblock:
            tile = self.CreateTile('ground', key)
            
        if type(units) != list: units = [units]
                        
        spawnpos = tile.GetAbsOrigin()
        spawnpos.z += 16.0
        unitsinst = []
        for unit in units:
            inst = CreateUnit(unit, spawnpos, owner_number=ownernumber)
            inst.UnitThink()
            unitsinst.append(inst)
            
        self.CreateRouteToHeart(key)
        
        return unitsinst
            
    def CreateRouteToHeart(self, key, maxdist=10000):
        heart = GetDungeonHeart(2)
        if not heart:
            PrintWarning('CreateRouteToHeart: no dungeon heart\n')
            return
            
        heartkey = self.GetKeyFromPos(heart.GetAbsOrigin())
        
        visited = set()
        
        curkey = key
        tilegrid = self.tilegrid
        foundheart = False
        for i in range(0, maxdist):
            tile = tilegrid[key]
            if tile.isblock:
                tile.SelectByOwner(OWNER_ENEMY)

            visited.add(key)
                
            if tile.key == heartkey:
                foundheart = True
                break
                
            newkey = None
            
            # Prefer to go to non block tiles (except if already visited of course)
            for ntile in tile.neighbors.values():
                if not ntile.isblock and ntile.key not in visited:
                    newkey = ntile.key
                    break
                
            # Default to closest next tile
            if not newkey:
                xdir = heartkey[0] - key[0]
                xstep = 1 if xdir > 0 else -1
                
                ydir = heartkey[1] - key[1]
                ystep = 1 if ydir > 0 else -1
                
                xdirkey = (key[0] + xstep, key[1])
                xdirtile = self.tilegrid[xdirkey]
                
                ydirkey = (key[0], key[1] + ystep)
                ydirtile = self.tilegrid[ydirkey]
                
                # Prefer non gold direction
                if xdirtile.type == 'gold' and ydirtile.type != 'gold':
                    newkey = ydirkey
                elif ydirtile.type == 'gold' and xdirtile.type != 'gold':
                    newkey = xdirkey
                elif abs(xdir) > abs(ydir):
                    newkey = xdirkey
                else:
                    newkey = ydirkey
            
            key = newkey
            
        if not foundheart:
            PrintWarning('CreateRouteToHeart: failed to build dig route to heart\n')
            
    # Misc methods
    def GetNearestTile(self, type, pos, maxdist=5):
        x, y = self.GetKeyFromPos(pos)
        bestblock = None
        bestdist = None
        w = int(math.round(maxdist/2.0))-1
        for i in range(x-w, x+w+1):
            for j in range(y-w, y+w+1):
                b = self.tilegrid[(i,j)]
                if not b or b.type != type:
                    continue
                dist = pos.DistTo(b.GetAbsOrigin())
                if not bestblock or bestdist > dist:
                    bestblock = b.GetHandle()
                    bestdist = dist
        return bestblock

    def GetKeyFromPos(self, pos):
        ''' Returns the key in the tilegrid for the given position (Vector). '''
        return int(round(pos.x/self.xsize)), int(round(pos.y/self.ysize))
        
    def GetPosFromKey(self, key):
        ''' Returns the position in the world for the given key (tuple of size 2). '''
        return Vector(key[0]*self.xsize, key[1]*self.ysize, 0.0)
        
    def GetTileFromPos(self, pos):
        ''' Returns the tile at pos (Vector). '''
        return self.tilegrid[self.GetKeyFromPos(pos)]
        
    def GetBlockFromMouse(self, mousedata):
        return self.tilegrid[self.GetKeyFromPos(mousedata.endpos)]
                    
    mins = -Vector(80, 80, 0)
    maxs = Vector(80, 80, 128)
    
    # Instance data
    xsize = 128.0
    ysize = 128.0
    worldhalfx = 128
    worldhalfy = 128
    groundheight = 24.0

    maploaded = False
    loadingmap = False
    worldisremoving = False
    
    changedkeys = None
    
    levelsettings = GenericField(value=None, networked=True, clientchangecallback='OnLevelChanged')
    
    # Settings
    cubesize = (-Vector(40, 40, 0), Vector(40, 40, 112))
    
    # Max is about 170 by 170 blocks (up to 30k blocks)
    gridsize = (30, 30)
    
if isserver:
    @concommand('sk_print_connected_areas', 'print connected areas', FCVAR_CHEAT)
    def CCPrintConnectedAreas(args):
        # Collect areas
        areaslists = []
        for tile in keeperworld.tilegrid.values():
            if tile and not tile.isblock and tile.connectedareas not in areaslists:
                areaslists.append(tile.connectedareas)
            
        # Print
        for i, areas in enumerate(areaslists):
            print('%d Area list: ' % (i))
            for a in areas:
                print('\tKey %s' % (str(a.key)))
        print('%d connected area lists found' % (len(areaslists)))
    
    @concommand('sk_kill_block', '', FCVAR_CHEAT)
    def CCKillBlock(args):
        player = UTIL_GetCommandClient()
        tile = keeperworld.GetBlockFromMouse(player.GetMouseData())
        if tile and tile.isblock:
            #tile.TakeDamage( CTakeDamageInfo( player, player, 0, 1000, 0 ) )
            tile.Event_Killed( CTakeDamageInfo( player, player, 0, 1000, 0 ) )
            
    @concommand('sk_test_add_player_dynamic', '', FCVAR_CHEAT)
    def CCTestAddPlayerDynamic(args):
        player = UTIL_GetCommandClient()
        keeperworld.AddPlayerDynamic(int(args[1]))
