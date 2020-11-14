import os
import math
from collections import defaultdict
import random

class BaseLevelLoader(object):
    def CreateDefaultWorldMap(self):
        return defaultdict(lambda : {
            'type' : 'block', 
            'ownernumber' : 1,
        })

    # Helpers
    @classmethod
    def CreateTileAt(self, worldmap, key, type, ownernumber):
        worldmap[key] = {'type' : type, 'ownernumber' : ownernumber}
        
    @classmethod
    def CreatePortalAt(self, worldmap, key, ownernumber=1):
        for i in range(-1, 2):
            for j in range(-1, 2):
                worldmap[(key[0]+i, key[1]+j)] = {'type' : 'portal', 'ownernumber' : ownernumber}
    
    @classmethod
    def CreateHeartAt(self, worldmap, key, ownernumber):
        for i in range(-2, 3):
            worldmap[(key[0]+i, key[1]-2)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            worldmap[(key[0]+i, key[1]+2)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            worldmap[(key[0]-2, key[1]+i)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            worldmap[(key[0]+2, key[1]+i)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            
        for i in range(-1, 2):
            for j in range(-1, 2):
                worldmap[(key[0]+i, key[1]+j)] = {'type' : 'heart', 'ownernumber' : ownernumber}
                
    # Random generator helpers
    def GenerateRandomArea(self, worldmap, hx, hy, type, minx, maxx, miny, maxy, owner=0):
        keystart = (random.randint(-hx+1, hx-1), random.randint(-hy+1, hy-1))
        keyend = (keystart[0]+random.randint(minx, maxx), keystart[1]+random.randint(miny, maxy))
        keystart, keyend = self.FixMinMax(keystart, keyend)
        
        print('Generating random area of %s at %s and %s' % (str(type), str(keystart), str(keyend)))
        
        wide = keyend[0] - keystart[0]
        tall = keyend[1] - keystart[1]
        sqrt = wide * tall
        
        w = random.random()
        if w < 0.25:
            # Simple filled rectangle 
            for x in range(keystart[0], keyend[0]):
                for y in range(keystart[1], keyend[1]):
                    self.CreateTileAt(worldmap, (x, y), type, owner)
        else:
            # Something random
            for i in range(0, int(sqrt/2.0)):
                self.CreateTileAt(worldmap, 
                    (random.randint(keystart[0], keyend[0]), random.randint(keystart[1], keyend[1])), type, owner)

                    
    def LoadTestMap1(self):
        # Create a map which contains the type of each cell
        worldmap = self.CreateDefaultWorldMap()
        #for i in range(-2, 3):
        #    for j in range(-2, 3):
        #        self.CreateTileAt(worldmap, (i, j), 'tile', 2)
                
        self.CreateHeartAt(worldmap, (0,0), 2)
                
        #for i in range(-2, 3):
        #    self.CreateTileAt(worldmap, (i, -3), 'treasureroom', 2)
                
        self.CreateTileAt(worldmap, (-3,0), 'ground', 0)
        self.CreateTileAt(worldmap, (-3,-1), 'ground', 0)
        self.CreateTileAt(worldmap, (-3,-2), 'ground', 0)
        
        self.CreateTileAt(worldmap, (-8,0), 'gold', 1)
        self.CreateTileAt(worldmap, (-8,-1), 'gold', 1)
        self.CreateTileAt(worldmap, (-8,-2), 'gold', 1)

        for i in range(12, 18):
            for j in range(-4, 0):
                self.CreateTileAt(worldmap, (j,i), 'gold', 1)
                
        for i in range(-18, -15):
            for j in range(-11, -3):
                self.CreateTileAt(worldmap, (j,i), 'gold', 1)
                
        for i in range(6, 10):
            for j in range(0, 3):
                self.CreateTileAt(worldmap, (j,i), 'gold', 1)
                
        self.CreatePortalAt(worldmap, (12, 0)) # NOTE: Surrounded by border tiles
        
        return worldmap, (40, 40)
        
    def LoadTestMap2(self):
        # Create a map which contains the type of each cell
        worldmap = self.CreateDefaultWorldMap()
        for i in range(-3, 4):
            for j in range(-3, 4):
                self.CreateTileAt(worldmap, (i, j), 'tile', 2)
                
        self.CreateHeartAt(worldmap, (0,0), 2)
                
        for i in range(-8, -3):
            for j in range(-3, 4):
                self.CreateTileAt(worldmap, (i, j), 'lair', 2)
        for i in range(-3, 4):
            for j in range(-8, -3):
                self.CreateTileAt(worldmap, (i, j), 'hatchery', 2)
        for i in range(-3, 4):
            for j in range(4, 9):
                self.CreateTileAt(worldmap, (i, j), 'training', 2)

        for i in range(4, 11):
            self.CreateTileAt(worldmap, (i,0), 'tile', 2)
                
        self.CreateTileAt(worldmap, (-9,0), 'gold', 1)
        self.CreateTileAt(worldmap, (-9,-1), 'gold', 1)
        self.CreateTileAt(worldmap, (-9,-2), 'gold', 1)
        
        self.CreateTileAt(worldmap, (-9,-14), 'gold', 1)
        self.CreateTileAt(worldmap, (-8,-14), 'gold', 1)
        self.CreateTileAt(worldmap, (-7,-14), 'gold', 1)
        self.CreateTileAt(worldmap, (-6,-14), 'gold', 1)
        
        for i in range(12, 18):
            for j in range(-4, 0):
                self.CreateTileAt(worldmap, (j,i), 'gold', 1)
                
        for i in range(-18, -15):
            for j in range(-11, -3):
                self.CreateTileAt(worldmap, (j,i), 'gold', 1)
                
        self.CreatePortalAt(worldmap, (12, 0), ownernumber=2) # NOTE: Surrounded by border tiles
        
        return worldmap, (40, 40)
        
    def FixMinMax(self, key1, key2):
        newkey1 = [0,0]
        newkey2 = [0,0]
        
        for i in range(0, 2):
            if key1[i] < key2[i]:
                newkey1[i] = key1[i]
                newkey2[i] = key2[i]
            else:
                newkey2[i] = key1[i]
                newkey1[i] = key2[i]

        return tuple(newkey1), tuple(newkey2)
        
    def GenerateRandomMap(self, gridsize):
        # Pretty much a quick job at creating a random level
        # Should make something better at a later point...
        
        worldmap = self.CreateDefaultWorldMap()
        
        x, y = gridsize
        hx = int(x/2.0)
        hy = int(y/2.0)
        
        size = x * y
        scale = size / 7225.0 # Use 85 * 85 as reference scale
        scale = max(0.3, scale)
        
        # Create random empty unclaimed land
        m = random.randint(int(5.0*scale), max(1, int(14.0*scale)))
        if m:
            for i in range(0, m):
                self.GenerateRandomArea(worldmap, hx, hy, 'ground', 2, 5, 2, 5, 0)
                    
        # Create random empty unclaimed gold
        m = random.randint(int(8*scale), max(1, int(18.0*scale)))
        if m:
            for i in range(0, m):
                self.GenerateRandomArea(worldmap, hx, hy, 'gold', 1, 10, 1, 10, 1)
                
        # Maybe a bit of water?
        if int(3*scale):
            m = random.randint(0, int(3*scale))
            if m:
                for i in range(0, m):
                    self.GenerateRandomArea(worldmap, hx, hy, 'water', 2, 8, 2, 8, 0)
                            
        # Surround borders with rocks
        for i in range(-hx, hx):
            self.CreateTileAt(worldmap, (i, -hy), 'rock', 1)
            self.CreateTileAt(worldmap, (i, hy-1), 'rock', 1)
            
        for i in range(-hy, hy):
            self.CreateTileAt(worldmap, (-hx, i), 'rock', 1)
            self.CreateTileAt(worldmap, (hx-1, i), 'rock', 1)
            
        # Create a dungeon heart somewhere (do it last, so it's not overwritten)
        inset = 12
        heartkey = (random.randint(-hx+inset, hx-inset-1), random.randint(-hy+inset, hy-inset-1))
        self.CreateHeartAt(worldmap, heartkey, 2)
        
        # Add a portal near the heart
        if random.random() < 0.5:
            key = (heartkey[0]+5+random.randint(0,5), heartkey[1]+random.randint(-5,5))
        else:
            key = (heartkey[0]+random.randint(-5,5), heartkey[1]+5+random.randint(0,5))
        self.CreatePortalAt(worldmap, key, 0)
                    
        return worldmap, gridsize
        
    def ReadWorldMap(self, folder=None, levelname=None, randomseed=None): 
        if levelname and levelname.startswith('random'):
            assert(randomseed != None)
            random.seed(randomseed)
            try:
                x, y = levelname.split('_')[1:3]
                gridsize = (int(x), int(y))
            except (IndexError, ValueError):
                PrintWarning('RandomWorld: Failed to parse gridsize from levelname. Format is: "Random_X_Y". Defaulting to 40x40.\n')
                gridsize = (40, 40)
            return self.GenerateRandomMap(gridsize)
        return self.levelloaders[levelname](self)

    levelloaders = defaultdict(lambda: (lambda self: self.LoadTestMap1()))
    levelloaders['testmap1'] = lambda self: self.LoadTestMap1()
    levelloaders['testmap2'] = lambda self: self.LoadTestMap2()
    
class DK1LevelLoader(BaseLevelLoader):
    ''' Dungeon Keeper 1 level loader.
    
        File Format: http://keeper.lubie.org/dk1_docs/dk_mapfiles_ref.htm
    
    '''
    
    # Tile types:
        # 0	Rock	22	Torture room
        # 1	Gold	24	Training room
        # 2	Earth	26	Dungeon Heart pedestal
        # 3	Earth with torch plate	28	Workshop
        # 4	Wall	30	Scavenger room
        # 5	Wall	32	Temple
        # 6	Wall	34	Graveyard
        # 7	Wall	36	Hatchery
        # 8	Wall	38	Lair
        # 9	Wall	40	Barracks
        # 10	Unclaimed path	42/43	Wooden door
        # 11	Claimed land	44/45	Braced door
        # 12	Lava	46/47	Iron door
        # 13	Water	48/49	Magic door
        # 14	Portal	51	Bridge
        # 16	Treasure room	52	Gem
        # 18	Library	53	Guardpost
        # 20	Prison 
    typemap = {
        0 : 'rock', # Rock
        1 : 'gold', # Gold
        2 : 'block', # Earth
        3 : 'block', # Earth
        4 : 'block', # Wall
        5 : 'block', # Wall
        6 : 'block', # Wall
        7 : 'block', # Wall
        8 : 'block', # Wall
        9 : 'block', # Wall
        10 : 'ground', # Unclaimed path
        11 : 'tile', # Claimed land
        12 : 'ground', # Lava
        13 : 'water', # Water
        14 : 'portal', # Portal
        16 : 'treasureroom', # Treasure room
        24 : 'training', # Training room
        26 : 'heart', # Dungeon Heart pedestal
        36 : 'hatchery', # Hatchery
        38 : 'lair', # Lair
    }

    # Owner types
    ownermap = {
        0x00 : 2, # PLAYER0
        0x01 : 3, # PLAYER1
        0x02 : 4, # PLAYER2
        0x03 : 5, # PLAYER3
        0x04 : 1, # PLAYER_GOOD
        0x05 : 0, # PLAYER_UNSET
    }
    
    def AddTreasureTiles(self, worldmap, key, ownernumber):
        for i in range(-2, 3):
            worldmap[(key[0]+i, key[1]-2)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            worldmap[(key[0]+i, key[1]+2)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            worldmap[(key[0]-2, key[1]+i)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            worldmap[(key[0]+2, key[1]+i)] = {'type' : 'treasureroom', 'ownernumber' : ownernumber, 'sellable' : False}
            
    def FindHeartMiddles(self, worldmap):
        middles = []
        for key, value in worldmap.items():
            if value['type'] == 'heart':
                x, y = key
                neighborkeys = [(x-1, y), (x, y-1), (x+1, y), (x, y+1)] 
                middle = True
                for nkey in neighborkeys:
                    if nkey not in worldmap or worldmap[nkey]['type'] != 'heart':
                        middle = False
                        break
                if middle:
                    middles.append((key, value['ownernumber']))
        return middles
    
    def ReadWorldMap(self, folder=None, levelname=None, randomseed=None): 
        ''' Example usuage:
        
            > worldmap = reader.ReadWorldMap('KEEPER/levels', 'map00001')
        '''
        worldmap = self.CreateDefaultWorldMap()
        
        # Load tile types
        slbpath = '%s.slb' % (os.path.join(folder, levelname))
        try:
            fp = open(slbpath, 'rb')
        except IOError:
            PrintWarning('Failed to load %s\n' % (slbpath))
            return None
        ba = bytearray(fp.read())
        fp.close()
        rowsize = int(math.sqrt(len(ba)/2))
        hrowsize = int(rowsize/2)
        
        i = 0
        while i < len(ba):
            type = ba[i]
            
            pos = int(i / 2)
            key = (int(pos % rowsize) - hrowsize, int(pos / rowsize) - hrowsize)
            
            try: worldmap[key]['type'] = self.typemap[type]
            except KeyError: pass

            assert(ba[i+1] == 0)
            i += 2
            
        # Load owners of the different tiles
        ownpath = '%s.own' % (os.path.join(folder, levelname))
        fp = open(ownpath, 'rb')
        ba = bytearray(fp.read())
        fp.close()
        rowsize = int(math.sqrt(len(ba)))
        
        for x in range(0, rowsize/3):
            for y in range(0, rowsize/3):
                own = ba[(y*3)*rowsize+(x*3)]
                key = (int(x)-hrowsize,int(y)-hrowsize)
                
                worldmap[key]['ownernumber'] = self.ownermap[own]
        
        # Add treasure tiles around heart
        middles = self.FindHeartMiddles(worldmap)
        for m in middles:
            self.AddTreasureTiles(worldmap, m[0], m[1])
        
        return worldmap, (86, 86)
        