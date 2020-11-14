from vmath import Vector
from .createroom import AbilityCreateRoom, TileRoom, RoomController, controllerspertype
from entities import entity
import random
if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    
def GetGoldInTreasureRooms(ownernumber):
    value = 0
    maxvalue = 0
    for room in controllerspertype[ownernumber]['dk_treasure_controller']:
        value += room.goldvalue
        maxvalue += room.maxgoldvalue
    return value, maxvalue
    
@entity('dk_treasure_controller', networked=True)
class TreasureController(RoomController):
    goldvalue = 0
    maxgoldvalue = 0
    
    def Merge(self, roomcontroller):
        self.goldvalue += roomcontroller.goldvalue
        self.maxgoldvalue += roomcontroller.maxgoldvalue
        super(TreasureController, self).Merge(roomcontroller)
        
    def IsFull(self):
        return self.goldvalue >= self.maxgoldvalue
        
    def RandomNotFullTile(self):
        tiles = [t for t in self.tiles if not t.IsFull()]
        return random.sample(tiles, 1)[0] if tiles else None
        
class RoomTreasure(TileRoom):
    type = 'treasureroom'
    modelname = 'models/keeper/treasureroom.mdl'
    maxgold = 250
    gold = None
    roomcontrollerclassname = 'dk_treasure_controller'

    def DebugPrint(self):
        if self.gold:
            return super(RoomTreasure, self).DebugPrint() + ', gold: %d, max: %d' % (self.gold.goldvalue, self.maxgold)
        return super(RoomTreasure, self).DebugPrint() + ', gold: 0, max: %d' % (self.maxgold)
    
    if isserver:
        def Spawn(self):
            super(RoomTreasure, self).Spawn()
            
            self.roomcontroller.maxgoldvalue += self.maxgold
            
        def UpdateOnRemove(self):
            self.roomcontroller.maxgoldvalue -= self.maxgold
            if self.gold:
                self.RemoveGold(self.gold)
        
            # ALWAYS CHAIN BACK!
            super(RoomTreasure, self).UpdateOnRemove()

    def IsFull(self):
        return self.GetGoldValue() >= self.maxgold

    def AddGold(self, gold):
        if not gold or self.IsFull():
            return gold
            
        splitoffgold = None
        goldvalue = self.GetGoldValue()
            
        if gold.goldvalue + goldvalue > self.maxgold:
            splitoffgold = gold.SplitOffGold(gold.goldvalue + goldvalue - self.maxgold)
                
        self.roomcontroller.goldvalue += gold.goldvalue
                
        if not self.gold:
            gold.SetAbsOrigin(self.GetAbsOrigin()+Vector(0,0,26.0))
            gold.treasuretile = self.GetHandle()
            self.gold = gold
        else:
            gold.SetOwnerNumber(self.gold.GetOwnerNumber())
            self.gold.MergeGold(gold)

        return splitoffgold

    def RemoveGold(self, gold):
        if self.gold:
            self.roomcontroller.goldvalue -= self.gold.goldvalue
            self.gold = None
        gold.treasuretile = None
        
    def OnValueChanged(self, value):
        assert(self.gold)
        self.roomcontroller.goldvalue += value
        
    def GetGoldValue(self):
        if self.gold:
            return self.gold.goldvalue
        return 0
        
    def FillWithGold(self, goldvalue):
        ''' Tries to fill up this tile with gold entities until the max 
            or desired value is reached. 
            Returns the remainder the desired gold value.
        '''
        if goldvalue <= 0:
            return 
            
        curgoldvalue = self.GetGoldValue()
        
        #print 'Adding gold: %d. cur gold: %d, key: %s' % (goldvalue, curgoldvalue, str(self.key))
        
        value = min(self.maxgold - curgoldvalue, min(self.maxgold, goldvalue))
        goldvalue -= value
            
        if self.gold:
            self.gold.UpdateGoldValue(value)
        else:
            gold = CreateEntityByName('dk_gold')
            gold.goldvalue = value
            gold.SetAbsOrigin(self.GetAbsOrigin()+Vector(0,0,26.0))
            gold.SetAbsAngles(self.GetAbsAngles())
            DispatchSpawn(gold)
            gold.Activate()
            
            # UpdateGoldState should add the gold to our tile now
            assert(self.gold == gold)

        #print('\tgold remaining: %d' % (goldvalue))
        return goldvalue
        
    #def DebugPrint(self):
    #    return super(RoomTreasure, self).DebugPrint() + ', gold: %d, maxgold: %d' % (self.goldvalue, self.maxgold)
    
class CreateLair(AbilityCreateRoom):
    name = 'createtreasureroom'
    displayname = 'Treasure'
    description = 'The Treasure room adds additional space for storing gold.'
    roomcls = RoomTreasure
    costs = [[('gold', 50)]]