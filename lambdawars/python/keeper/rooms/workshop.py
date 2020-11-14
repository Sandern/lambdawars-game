from .createroom import AbilityCreateRoom, TileRoom

class RoomWorkshop(TileRoom):
    type = 'workshop'
    modelname = 'models/keeper/lair.mdl'

class CreateWorkshop(AbilityCreateRoom):
    name = 'createworkshop'
    displayname = 'Workshop'
    description = 'The workshop is the room at which traps are constructed.'
    roomcls = RoomWorkshop
    costs = [[('gold', 125)]]