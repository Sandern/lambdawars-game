from .createroom import AbilityCreateRoom, TileRoom, RoomController
from entities import entity

@entity('dk_training_controller', networked=True)
class TrainController(RoomController):
    def IsFull(self):
        ''' Trainings room is full if we have one creatures per tile. '''
        return len(self.creaturesusingroom) >= len(self.tiles)
        
class RoomTraining(TileRoom):
    type = 'training'
    modelname = 'models/keeper/training.mdl'
    roomcontrollerclassname = 'dk_training_controller'

class CreateTraining(AbilityCreateRoom):
    name = 'createtraining'
    displayname = 'Training'
    description = 'The Training Room is the place where creatures increase their experience.'
    roomcls = RoomTraining
    costs = [[('gold', 150)]]