from srcbase import SOLID_NONE
from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseBuilding as BaseClass
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK
from core.units import CreateUnit, PrecacheUnit, unitlistpertype
from gamerules import gamerules
from particles import *
import random
from .common import GetDungeonHeart
from utils import UTIL_GetPlayers

if isserver:
    from gameinterface import GameEvent, FireGameEvent
    from .common import sk_creature_limit
    
@entity('dk_portal', networked=True)
class Portal(BaseClass):
    def __init__(self):
        super().__init__()
        
        self.portaltiles = []
        self.spawnedcreatures = 0
        self.nextcreaturetime = 0
        
        self.SetCanBeSeen(False)
        
    if isserver:
        def Precache(self):
            super().Precache()
            
            self.PrecacheScriptSound('Portal.Claimed')
            
            for c in self.creatures:
                PrecacheUnit(c)
                
        def Spawn(self):
            super().Spawn()
            
            self.SetSolid(SOLID_NONE)
            self.spawnedtime = gpGlobals.curtime
            
            self.nextcreaturetime = gpGlobals.curtime + 15.0
            
            DispatchParticleEffect('landingbay_lift_fog_volume', self.GetAbsOrigin() + Vector(0, 0, 64.0), QAngle(0, 0, 0), self)
            
    def CountCreatures(self):
        return sum([len(unitlistpertype[self.GetOwnerNumber()][c]) for c in self.creatures])
        
    def BuildThink(self):
        self.SetNextThink(gpGlobals.curtime + 0.5)
        
        if gamerules.dkgameover:
            return
        
        if self.GetOwnerNumber() <= 1:
            if self.fireunclaimedevent and gpGlobals.curtime - self.spawnedtime > 30.0:
                for player in UTIL_GetPlayers():
                    event = GameEvent('sk_portal_unclaimed')
                    event.SetInt("userid", player.GetUserID())
                    event.SetInt("entindex", self.entindex())
                    FireGameEvent(event)
                
                self.fireunclaimedevent = False
            return
            
        creaturecount = self.CountCreatures()
        
        if creaturecount >= sk_creature_limit.GetInt():
            return
            
        if self.nextcreaturetime < gpGlobals.curtime:
            unit = CreateUnit(random.sample(self.creatures,1)[0], self.GetAbsOrigin() + Vector(0,0,32), owner_number=self.GetOwnerNumber())
            unit.portal = self.GetHandle()
            unit.heart = GetDungeonHeart(self.GetOwnerNumber())
            self.nextcreaturetime = gpGlobals.curtime + random.uniform(self.createintervalmin, self.createintervalmax)
            self.spawnedcreatures += 1
            
            self.createintervalmin = min(50.0, 10.0 + creaturecount * 5.0)
            self.createintervalmax = max(70.0, 20.0 + creaturecount * 5.0)
        
    def Claim(self, ownernumber):
        self.SetOwnerNumber(ownernumber)
        for tile in self.portaltiles:
            tile.SetOwnerNumber(ownernumber)
            tile.TellNeighborsChanged()
        self.EmitAmbientSound(-1, self.GetAbsOrigin(), 'Portal.Claimed')
        
        for player in UTIL_GetPlayers():
            if player.GetOwnerNumber() == ownernumber:
                event = GameEvent('sk_portal_claimed')
                event.SetInt("userid", player.GetUserID())
                event.SetInt("entindex", self.entindex())
                FireGameEvent(event)
        
        self.nextcreaturetime = gpGlobals.curtime + random.uniform(self.createintervalmin, self.createintervalmax)
  
    creatures = [
        'unit_parasite',
        'unit_drone',
        'unit_buzzer',
    ]
    
    spawnedtime = 0.0
    fireunclaimedevent = True
    createintervalmin = 10.0
    createintervalmax = 20.0
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    
# Register unit
class PortalInfo(WarsBuildingInfo):
    name = "dk_portal" 
    cls_name = "dk_portal"
    modelname = 'models/keeper/portal.mdl'
    health = 200
    population = 0
    
    