from srcbase import SOLID_BBOX
from vmath import *
from core.buildings import UnitBaseAutoTurret, WarsTurretInfo
from core.ents.homingprojectile import HomingProjectile
import random
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK
if isserver:
    from wars_game.ents.grenade_spit import GrenadeSpit
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_PredictedPosition
from gameinterface import *
    
sv_gravity = ConVarRef('sv_gravity')

@entity('npc_dota_tower', networked=True)
@entity('dota_tower_good')
class TowerGood(UnitBaseAutoTurret):
    pitchturnspeed = 2000.0
    yawturnspeed = 2000.0
    firerate = 3.0
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    
    buildingsolidmode = SOLID_BBOX
    
    def KeyValue(self, key, value):
        if key == 'unittype':
            return False
        if key == 'MapUnitName':
            self.SetUnitType(value)
            return True
        return super().KeyValue(key, value)
    
    def OnUnitTypeChanged(self, oldunittype):
        super().OnUnitTypeChanged(oldunittype)
        
        HealthBarOffset = getattr(self.unitinfo, 'HealthBarOffset', None)
        if HealthBarOffset:
            colprop = self.CollisionProp()
            self.barsoffsetz = HealthBarOffset - colprop.OBBMaxs().z
    
    def GetNavBlockBB(self):
        mins = Vector(self.unitinfo.mins)
        maxs = Vector(self.unitinfo.maxs)
        mins.z -= 64.0
        return mins, maxs
    
    def Precache(self):
        super().Precache()
        
        self.PrecacheSound('Tower.Fire.Attack')
        
    def Spawn(self):
        super().Spawn()
        
        # In Dota 2, the team number is the owner
        self.SetOwnerNumber(self.GetTeamNumber())
    
    def Fire(self, bulletcount, attacker=None, ingorespread=False):
        if not self.enemy:
            return
        vFirePos = Vector()
        att = self.LookupAttachment('attach_attack1')
        self.GetAttachment(att, vFirePos)

        HomingProjectile.SpawnProjectile(self, vFirePos, self.enemy, 100.0, 300.0, particleeffect='ranged_tower_good')#, pexplosioneffect='ranged_tower_good_explosion')
        #HomingProjectile.SpawnProjectile(self, vFirePos, self.enemy, 100.0, 50.0, particleeffect='generic_projectile')
        self.EmitSound('Tower.Fire.Attack')
        
class DotaTowerInfo(WarsTurretInfo):
    displayname = 'Towah'

'''
# Register unit
class TowerGoodInfo(WarsTurretInfo):
    name        = "build_tower_good"
    cls_name    = "npc_dota_tower"
    image_name  = "vgui/abilities/ability_rebelhq.vmt"
    health      = 2000
    modelname   = 'models/props_structures/tower_good.mdl'
    sensedistance = 700.0
    
class TowerGoodInfo(WarsTurretInfo):
    name        = "build_tower_bad" 
    cls_name    = "npc_dota_tower"
    image_name  = "vgui/abilities/ability_rebelhq.vmt"
    health      = 2000
    modelname   = 'models/props_structures/tower_bad.mdl'
    sensedistance = 700.0
    '''
    