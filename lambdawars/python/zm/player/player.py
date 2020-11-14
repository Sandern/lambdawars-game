from srcbase import *
from entities import entity
if isserver:
    from entities import CHL2WarsPlayer as BaseClass
else:
    from entities import C_HL2WarsPlayer as BaseClass
    
@entity('zm_player_survivor', networked=True)
class PlayerSurvivor(BaseClass):
    def __init__(self):
        super(PlayerSurvivor, self).__init__()
        
        print('Player created')
        
    def GiveDefaultItems(self):
        pass
        
    def PickDefaultSpawnTeam(self):
        pass
        
    def StopObserverMode(self):
        pass
        
    def Spawn(self):
        self.nextmodelchangeTime = 0.0
        self.nextteamchangeTime = 0.0

        self.PickDefaultSpawnTeam()

        super(BaseClass, self).Spawn() # Skip BaseClass
        
        self.SetMoveType(MOVETYPE_WALK)

        #pl.deadflag = false
        self.RemoveSolidFlags(FSOLID_NOT_SOLID)

        self.RemoveEffects(EF_NODRAW)
        self.StopObserverMode()
        
        self.GiveDefaultItems()

        self.RemoveEffects(EF_NOINTERP)