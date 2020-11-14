from srcbase import *
from vmath import vec3_origin, vec3_angle
from entities import CBaseAnimating, entity
from . import keeperworld
from .tiles import tilespertype

from core.resources import ResourceInfo, UpdateResource, resources, ResetResource

from .taskqueue import taskqueues
from .pickupableobject import PickupableObject

if isserver:
    from entities import gEntList, CreateEntityByName, DispatchSpawn

goldlist = []

def ResetGold():
    ResetResource('gold')
    del goldlist[:]

class ResGrubsInfo(ResourceInfo):
    name = 'gold'
    
    @classmethod
    def TakeResources(cls, ownernumber, amount):  
        goldvalue = amount
        gold = gEntList.FindEntityByClassname(None, "dk_gold")
        while gold and goldvalue > 0:
            if not gold.IsMarkedForDeletion() and gold.GetOwnerNumber() == ownernumber:
                goldvalue = gold.TakeGoldValue(goldvalue)
            gold = gEntList.FindEntityByClassname(gold, "dk_gold")

    @classmethod
    def GiveResources(cls, ownernumber, amount): 
        # Find a treasure tile and add gold to it
        goldvalue = amount
        treasuretiles = tilespertype[ownernumber]['treasureroom']
        for t in treasuretiles:
            goldvalue = t.FillWithGold(goldvalue)
            if goldvalue <= 0:
                break
                
        if goldvalue > 0:
            PrintWarning('GoldGiveResources: Failed to add gold to treasure tiles of owner %d (already filled or no tiles (%d)). Remainder: %d\n' % (ownernumber, len(treasuretiles), goldvalue))
            
@entity('dk_gold')
class Gold(PickupableObject, CBaseAnimating):
    #modelname = 'models/keeper/crystal_single.mdl' #'models/props_mining/ingot001.mdl'
    
    modelsingle = 'models/keeper/crystal_single.mdl'
    modelsmall = 'models/keeper/crystal_small.mdl'
    modelbig = 'models/keeper/crystal_large.mdl'
    
    carriedbyimp = None
    goldvalue = 100
    treasuretile = None
    goldactive = False
    
    def __init__(self):
        CBaseAnimating.__init__(self)
        PickupableObject.__init__(self)
        
    #def GetIMouse(self):
    #    return self
        
    def Precache(self):
        super().Precache()
        
        self.PrecacheModel(self.modelsingle)
        self.PrecacheModel(self.modelsmall)
        self.PrecacheModel(self.modelbig)

    def Spawn(self):
        self.Precache()
        
        super().Spawn()
        
        self.UpdateModel()
        
        self.SetSolid(SOLID_BBOX)
        #self.SetSolid(SOLID_VPHYSICS)
        #physicsObject = self.VPhysicsInitNormal(SOLID_VPHYSICS, self.GetSolidFlags(), False)
        #self.SetMoveType(MOVETYPE_VPHYSICS)
        self.SetMoveType(MOVETYPE_NONE)
        #self.AddSolidFlags(FSOLID_NOT_SOLID)
        self.SetCollisionGroup(WARS_COLLISION_GROUP_IGNORE_ALL_UNITS)
        
        # Causes crashes:
        #self.SetSolid(SOLID_BBOX)
        #self.SetSolidFlags(FSOLID_NOT_SOLID|FSOLID_TRIGGER)
        #self.SetMoveType(MOVETYPE_NONE)
        #self.SetCollisionGroup(COLLISION_GROUP_NONE)
        #self.CollisionProp().UseTriggerBounds(True,1)
        
        goldlist.append(self.GetHandle())
        
        self.goldactive = True
        self.UpdateGoldState()
  
    def UpdateOnRemove(self):
        h = self.GetHandle()
        try: goldlist.remove(h)
        except ValueError: pass
        
        self.goldactive = False
        self.UpdateGoldState()

        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
    def OnChangeOwnerNumber(self, oldownernumber):
        super().OnChangeOwnerNumber(oldownernumber)
        
        if not self.goldactive:
            return
    
        if oldownernumber > 1:
            UpdateResource(oldownernumber, 'gold', -self.goldvalue)
            
        newowner = self.GetOwnerNumber()
        if newowner > 1:
            UpdateResource(newowner, 'gold', self.goldvalue)
            
    def SnapToTile(self):
        assert(not self.GetMoveParent())
        pos = self.GetAbsOrigin()
        kw = keeperworld.keeperworld
        tile = kw.tilegrid[kw.GetKeyFromPos(pos)]
        pos.z = tile.GetAbsOrigin().z + 28.0
        self.SetAbsOrigin(pos)
    
    def IsInTreasureRoom(self):
        return bool(self.treasuretile)
        
    def UpdateGoldState(self):
        splitoffgold = None
        h = self.GetHandle()
        assert(h)
        if not self.goldactive:
            self.SetOwnerNumber(0)
            if self.treasuretile:
                self.treasuretile.RemoveGold(h)
            # make sure there is no gold task anymore
            for ownernumber, tq in taskqueues.items():
                tq.RemoveTasksWithGold(h)
            return 0
            
        if self.carriedbyimp or self.grabbedbyplayer:
            # Remove gold from owner (since we are carrying it)
            self.SetOwnerNumber(0)
            if self.treasuretile:
                self.treasuretile.RemoveGold(h)
            splitoffgold = 0
            # make sure there is no gold task
            for ownernumber, tq in taskqueues.items():
                tq.RemoveTasksWithGold(h)
            return splitoffgold
            
        if not self.treasuretile:
            kw = keeperworld.keeperworld
            tile = kw.tilegrid[kw.GetKeyFromPos(self.GetAbsOrigin())]
            if tile.type == 'treasureroom':
                splitoffgold = tile.AddGold(h) # This will set the treasure room handle
                if self.IsMarkedForDeletion():
                    return splitoffgold # Got removed/merged while adding ourself to the treasure tile
                    
        if self.treasuretile:
            ownernumber = self.treasuretile.GetOwnerNumber()
            self.SetOwnerNumber(ownernumber)
            taskqueues[ownernumber].RemoveTasksWithGold(h)
        else:
            self.SetOwnerNumber(0)
            
            if self.TryMergeNearbyGold():
                return 0
            
            ownernumber = 2
            taskqueues[ownernumber].InsertPickupGoldTask(h)
            
        self.SnapToTile()
            
        return splitoffgold
        
    def TryMergeNearbyGold(self):
        ownernumber = self.GetOwnerNumber()
        assert(ownernumber == 0)
        
        origin = self.GetAbsOrigin()
        radius = 48.0
        gold = gEntList.FindEntityByClassnameWithin(None, "dk_gold", origin, radius)
        while gold:
            if gold != self and not gold.IsMarkedForDeletion() and not gold.carriedbyimp and not gold.grabbedbyplayer and gold.GetOwnerNumber() == ownernumber:
                gold.MergeGold(self)
                #print 'Merging gold %s with %s. New value: %s' % (str(self.GetHandle()), str(gold), gold.goldvalue)
                return True
            gold = gEntList.FindEntityByClassnameWithin(gold, "dk_gold", origin, radius)
        return False
        
    def UpdateModel(self):
        if self.goldvalue <= 100:
            self.SetModel(self.modelsingle)
        elif self.goldvalue > 100 < 150:
            self.SetModel(self.modelsmall)
        elif self.goldvalue >= 150:
            self.SetModel(self.modelbig)
        
    def UpdateGoldValue(self, value):
        ''' Updates the gold value by value.
            value can be negative or positive.
            Updates the resources of the owner.
            Removes this gold entity if it hits zero.
        '''
        self.goldvalue += value
        if self.GetOwnerNumber() < 2:
            self.Remove() if self.goldvalue <= 0 else self.UpdateModel()
            return

        UpdateResource(self.GetOwnerNumber(), 'gold', value)
        
        if self.treasuretile:
            self.treasuretile.OnValueChanged(value)

        self.Remove() if self.goldvalue <= 0 else self.UpdateModel()
            
    def TakeGoldValue(self, value):
        ''' Decreases the gold value by value.
            Takes as much as it can. 
            Returns the remainder. 
            value must be positive. '''
        assert(value > 0)
        if value > self.goldvalue:
            value -= self.goldvalue
            self.UpdateGoldValue(-self.goldvalue)
            return value
        self.UpdateGoldValue(-value)
        return 0
        
    def MergeGold(self, gold):
        ''' Merge an existing gold entity.
            Just adds the value of that gold entity to ours and removes the other one. '''
        assert(self.GetOwnerNumber() == gold.GetOwnerNumber())
        self.goldvalue = self.goldvalue + gold.goldvalue
        # Set to 0, so it's not removed from the resources
        # Otherwise it would first remove the gold and then add it here again.
        gold.goldvalue = 0 
        gold.Remove()
        self.UpdateModel()
        
    def SplitOffGold(self, value):
        ''' Remove the given gold value from this gold entity, resulting in a new gold entity. '''
        assert(self.goldvalue > value)
        assert(value > 0)
        assert(not self.GetMoveParent())
        gold = CreateEntityByName('dk_gold')
        gold.goldvalue = value
        gold.SetAbsOrigin(self.GetAbsOrigin())
        gold.SetAbsAngles(self.GetAbsAngles())
        DispatchSpawn(gold)
        gold.Activate()

        self.UpdateGoldValue(-value)
        
        return gold
        
    def AttachToImp(self, imp=None):
        splitoffgold = None
        if imp:
            self.SetOwnerEntity(imp)
            self.SetParent(imp, imp.LookupAttachment("nozzle"))
            assert(self.GetMoveParent())
            self.SetLocalOrigin(vec3_origin)
            self.SetLocalAngles(vec3_angle)
            self.carriedbyimp = imp.GetHandle()
            
            splitoffgold = self.UpdateGoldState()
        else:
            self.SetOwnerEntity(None)
            self.SetParent(None)
            self.carriedbyimp = None
            
            angles = self.GetAbsAngles()
            angles.x = angles.z = 0.0
            self.SetAbsAngles(angles)
            
            splitoffgold = self.UpdateGoldState()
            
        return splitoffgold
        
    def OnGrabReleased(self, player):
        #print 'released gold'
        self.UpdateGoldState()
        
    def OnGrabbed(self, player):
        #print 'grabbed gold'
        # Can only pick up to 100, so must split off some otherwise
        if self.goldvalue > 100:
            self.SplitOffGold(self.goldvalue - 100)
        self.UpdateGoldState()
        
        
            