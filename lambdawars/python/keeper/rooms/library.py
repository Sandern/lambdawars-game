from .createroom import AbilityCreateRoom, TileRoom

class RoomLibrary(TileRoom):
    type = 'library'
    modelname = 'models/keeper/lair.mdl'

class CreateLibrary(AbilityCreateRoom):
    name = 'createlibrary'
    displayname = 'Library'
    description = 'Research room.'
    roomcls = RoomLibrary
    costs = [[('gold', 200)]]