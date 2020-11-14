from .createroom import AbilityCreateRoom, TileRoom, RoomController
from entities import entity
import random

if isserver:
    from core.units import CreateUnit

@entity('dk_hatchery_controller', networked=True)
class HatcheryController(RoomController):
    if isserver:
        def Spawn(self):
            super(HatcheryController, self).Spawn()
            
            self.grubs = []
            self.SetThink(self.HatcheryThink, gpGlobals.curtime + random.uniform(self.minrate, self.maxrate))
            
        def HatcheryThink(self):
            self.grubs = [_f for _f in self.grubs if _f]
            
            # Allow one grub per tile for now
            if self.tiles :
                if len(self.grubs) < len(self.tiles):
                    tile = self.RandomTile()
                    grub = CreateUnit('unit_dk_grub', tile.GetAbsOrigin(), owner_number=self.GetOwnerNumber())
                    grub.hatchery = self.GetHandle()
                    self.grubs.append(grub)
            else:
                PrintWarning("Room controller without tiles!\n")
                
            self.SetNextThink(gpGlobals.curtime + random.uniform(self.minrate, self.maxrate))
            
        def GetRandomGrub(self):
            self.grubs = [_f for _f in self.grubs if _f]
            return random.sample(self.grubs, 1)[0] if self.grubs else None 
            
    minrate = 5.0
    maxrate = 15.0

class RoomHatchery(TileRoom):
    type = 'hatchery'
    modelname = 'models/keeper/hatchery.mdl'
    roomcontrollerclassname = 'dk_hatchery_controller'
    
class CreateHatchery(AbilityCreateRoom):
    name = 'createhatchery'
    displayname = 'Hatchery'
    description = 'Hatcheries generate grubs which all creatures (apart from Imps) eat to sustain themselves.'
    roomcls = RoomHatchery
    costs = [[('gold', 100)]]