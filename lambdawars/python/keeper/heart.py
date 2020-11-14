from srcbase import SOLID_NONE
from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity
from core.units import CreateUnit

from . import keeperworld

@entity('dk_heart', networked=True)
class Heart(BaseClass):
    def __init__(self):
        super().__init__()
        
        self.hearttiles = []
        
    def Precache(self):
        super().Precache()
        
        self.PrecacheScriptSound('Heart.Beat')
        
    if isserver:
        def Spawn(self):
            super().Spawn()
            
            self.SetThink(self.HeartBeat, gpGlobals.curtime + 1.0, 'HeartBeat')
            
        def HeartBeat(self):
            self.EmitSound('Heart.Beat')
            self.SetNextThink(gpGlobals.curtime + self.heartbeatrate, 'HeartBeat')
            
            if self.health < self.maxhealth:
                # Also regen health per heartbeat
                self.health = self.health + 1
            
    def OnTakeDamage_Alive(self, info):
        self.lastenemyattack = gpGlobals.curtime
        return super().OnTakeDamage_Alive(info)
        
    heartbeatrate = 2.0
    lastenemyattack = 0.0
    blocknavareas = False
    
# Register unit
class HeartInfo(WarsBuildingInfo):
    name = "dk_heart" 
    cls_name = "dk_heart"
    modelname = 'models/keeper/Heart.mdl'
    health = 1500
    population = 0
    sound_death = 'Heart.Die'
    generateresources = {'type' : 'gold', 'amount' : 1, 'interval' : 5.0} # Get one gold free per second