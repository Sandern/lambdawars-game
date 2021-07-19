from core.units import UnitBaseAirLocomotion
from .antlion import UnitAntlion as BaseClass, AntlionWorkerInfo
from entities import entity, Activity
if isserver:
    from core.units import UnitCombatAirNavigator

@entity('unit_mutalisk', networked=True)
class UnitMutalisk(BaseClass):
    aiclimb = False
    LocomotionClass = UnitBaseAirLocomotion
    if isserver:
        NavigatorClass = UnitCombatAirNavigator

    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 1024.0
        self.testroutestartheight = 2048.0
        
    def Spawn(self):
        super().Spawn()
        
        self.locomotion.desiredheight = 240.0
        self.locomotion.flynoiserate = 64.0
        self.locomotion.flynoisez = 32.0
        
    def ShouldGib(self, info):
        return True
            
    # Activity translation table
    acttables = {
        Activity.ACT_IDLE : Activity.ACT_GLIDE,
        Activity.ACT_WALK : Activity.ACT_GLIDE,
        Activity.ACT_RUN : Activity.ACT_GLIDE,
        Activity.ACT_MP_JUMP_START : 'ACT_ANTLION_JUMP_START',
        Activity.ACT_MP_JUMP_LAND : 'ACT_ANTLION_LAND',
        Activity.ACT_MP_JUMP_FLOAT : Activity.ACT_GLIDE,
    }
    
    selectionparticlename = 'unit_circle_ground'

class MutaliskInfo(AntlionWorkerInfo):
    name = 'unit_mutalisk'
    cls_name = 'unit_mutalisk'
    keyvalues = {'spawnflags' : str(UnitMutalisk.SF_ANTLION_WORKER)}
    abilities = {                        
        8 : 'attackmove',
        9 : 'holdposition',
    }
    image_name = 'vgui/units/unit_antlion_worker.vmt'
    image_dis_name = 'vgui/units/unit_antlion_worker_dis.vmt'
    portrait = 'resource/portraits/antlionWorkerPortrait.bik'
    costs = [('grubs', 1)]
    buildtime = 3.5
    health = 120
    displayname = 'Mutalisk'
    description = 'Awesome mutalisk' 
    modelname = 'models/antlion_worker.mdl'
    