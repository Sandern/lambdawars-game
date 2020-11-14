from .createroom import AbilityCreateRoom, TileRoom

class RoomLair(TileRoom):
    type = 'lair'
    modelname = 'models/keeper/lair.mdl'
    attachedlair = None
    
    if isserver:
        def UpdateOnRemove(self):
            if self.attachedlair:
                self.attachedlair.Remove()
                self.attachedlair = None
            super(RoomLair, self).UpdateOnRemove()
    
class CreateLair(AbilityCreateRoom):
    name = 'createlair'
    displayname = 'Lair'
    description = 'The lair is the rest place of creatures.'
    roomcls = RoomLair
    costs = [[('gold', 75)]]