from srcbase import *
from vmath import Vector, QAngle, VectorNormalize, VectorAngles
from entities import entity, CBaseGrenade as BaseClass, eventqueue
from core.units import CreateUnitFancy, unitlistpertype, PrecacheUnit
from gameinterface import CPASAttenuationFilter
from playermgr import OWNER_ENEMY
import math

if isserver:
    from entities import SporeExplosion, D_HT
    from utils import UTIL_Remove, UTIL_TraceLine, trace_t, UTIL_DecalTrace
    from unit_helper import GF_NOCLEAR, GF_REQTARGETALIVE, GF_USETARGETDIST, GF_ATGOAL_RELAX
    
def CreateBehaviorTamedAntlion(BaseClass):
    class BehaviorTamedAntlion(BaseClass):
        class ActionIdle(BaseClass.ActionIdle):
            def Update(self):
                if not self.CheckTamer():
                    return super().Update()
                return self.CheckTamerOrders()
                
            def OnSuspend(self):
                self.CheckTamer()
                return super().OnSuspend()
                
            def CheckTamer(self):
                outer = self.outer
                if not self.hastamer:
                    return False
                if not outer.tamer or not outer.tamer.IsAlive():
                    outer.SetOwnerNumber(OWNER_ENEMY) # Tamer died, go rampage
                    self.hastamer = False
                return self.hastamer
                
            def CheckTamerOrders(self):
                outer = self.outer
                tamer = outer.tamer
                tamertarget = getattr(tamer, 'tamertarget', None)
                tamerpostarget = getattr(tamer, 'tamerpostarget', None)
                
                # Clear any existing move order (otherwise it would interfer with the AttackMove action)
                outer.ClearAllOrders(notifyclient=True, dispatchevent=False)
                
                if tamertarget:
                    if self.outer.IRelationType(tamertarget) != D_HT:
                        outer.MoveOrder(tamertarget.GetAbsOrigin(), target=tamertarget) # Note: inserts an order
                        return self.Continue()
                    else:
                        return self.SuspendFor(self.behavior.ActionAttackMove, 'Attack move tamer target unit.', tamertarget)
                elif tamerpostarget and self.lasttamerpostarget != tamerpostarget:
                    self.lasttamerpostarget = tamerpostarget
                    return self.SuspendFor(self.behavior.ActionAttackMove, 'Attack move tamer target position.', tamerpostarget, tolerance=320.0)
                    
                # Default to following the tamer
                #outer.MoveOrder(tamer.GetAbsOrigin(), target=tamer)
                #return self.SuspendFor(self.behavior.ActionMoveTo, 'Following tamer', outer.tamer, goalflags=GF_REQTARGETALIVE|GF_USETARGETDIST|GF_NOCLEAR|GF_ATGOAL_RELAX)
                return self.Continue()
                
            def OnTamerOrdersChanged(self):
                return self.CheckTamerOrders()
                
            hastamer = True
            lasttamerpostarget = None
                
    return BehaviorTamedAntlion

@entity('bugbait')
class BugBait(BaseClass):
    if isserver:
        def Precache(self):
            super().Precache()
            
            PrecacheUnit('unit_antlion_small')
            self.PrecacheScriptSound("GrenadeBugBait.Splat")
            
            self.PrecacheModel(self.BUGBAIT_MODEL)

        def Spawn(self):
            self.Precache()
            
            self.SetModel(self.BUGBAIT_MODEL)
            
            self.SetSolid(SOLID_BBOX)
            self.SetMoveType(MOVETYPE_FLYGRAVITY)
            self.SetSolidFlags(FSOLID_NOT_STANDABLE)
            self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
            
            self.SetTouch(self.BugBaitTouch)
            
            super().Spawn()
        
    def SetVelocity(self, velocity, angVelocity):
        physobj = self.VPhysicsGetObject()
        if physobj != None:
            physobj.AddVelocity(velocity, angVelocity)
        
    def BugBaitTouch(self, other):
        if other.IsSolidFlagSet(FSOLID_VOLUME_CONTENTS | FSOLID_TRIGGER):
            # Some NPCs are triggers that can take damage (like antlion grubs). We should hit them.
            if (other.takedamage == DAMAGE_NO) or (other.takedamage == DAMAGE_EVENTS_ONLY):
                return

        if other.GetCollisionGroup() == COLLISION_GROUP_PROJECTILE:
            return
                
        self.Detonate(other)
        
    def PreAntlionSpawn(self, antlion):
        antlion.cancappcontrolpoint = False
        antlion.overrideteamcolor = Color(255, 0, 0, 255)
        antlion.tamer = self.GetThrower()
        antlion.BehaviorGenericClass = CreateBehaviorTamedAntlion(antlion.BehaviorGenericClass)
        antlion.uncontrollable = True
        
    def Detonate(self, target):
        self.SetTouch(None)
        self.takedamage = DAMAGE_NO

        owner = self.GetOwnerNumber()
        origin = self.GetAbsOrigin()
        

        tr = trace_t()
        traceDir = self.GetAbsVelocity()

        VectorNormalize(traceDir)

        UTIL_TraceLine(origin, origin + traceDir * 64, MASK_SHOT, self, COLLISION_GROUP_NONE, tr)

        if tr.fraction < 1.0:
            UTIL_DecalTrace(tr, "BeerSplash" ) # TODO: Use real decal
        
        # Make a splat sound
        filter = CPASAttenuationFilter(self)
        self.EmitSoundFilter(filter, self.entindex(), "GrenadeBugBait.Splat")
        
        tamer = self.GetThrower()
        if not tamer:
            UTIL_Remove(self)
            return
        
        maxantlions = self.bugbaitability.maxantlions if self.bugbaitability != None else 1
        abibugbait_antlions = getattr(tamer, 'abibugbait_antlions', set())
        
        if self.bugbaitability and self.bugbaitability.throwtarget: # To make targeting easier, and not depend on the touch result
            tamer.tamertarget = self.bugbaitability.throwtarget
        else:
            tamer.tamertarget = target if target.IsUnit() else None
        tamer.tamerpostarget = tr.endpos if not tamer.tamertarget else None
        
        if not self.bugbaitability or self.bugbaitability.summonantlions:
            # Some confusing written logic to clamp the number of antlions follows here/.
            # Do a time based clamp, 1 antlion per x seconds max
            reducepoints = (gpGlobals.curtime - tamer.abibugbait_lastspawntime) / 1.0
            tamer.abibugbait_spawnpenalty = max(0, tamer.abibugbait_spawnpenalty - reducepoints)
            tamer.abibugbait_lastspawntime = gpGlobals.curtime
            maxantlions = math.floor(max(0, maxantlions - tamer.abibugbait_spawnpenalty))
            
            # Clamp antlions to a global max per owner
            antlioncount = len(unitlistpertype[owner]['unit_antlion_small'])
            globalmaxantlions = 30
            maxantlions = min(maxantlions, globalmaxantlions - antlioncount)
            
            if len(abibugbait_antlions) < maxantlions:
                for i in range(0, maxantlions-len(abibugbait_antlions)):
                    # Spawn new Antlion when we don't have enough yet
                    keydata = {'burrowed' : '1', 'Uncontrollable' : '1'}
                    antlion = CreateUnitFancy('unit_antlion_small', origin, owner_number=owner, keyvalues=keydata, fnprespawn=self.PreAntlionSpawn)
                    
                    eventqueue.AddEvent(antlion, "Unburrow", variant_t(), 0.3, None, None, 0 )
                    
                    if abibugbait_antlions != None:
                        tamer.abibugbait_antlions.add(antlion)
                        tamer.abibugbait_spawnpenalty += 1
                
        # Tell Antlions of tamer that orders might have changed
        if abibugbait_antlions != None:
            for antlion in tamer.abibugbait_antlions:
                antlion.DispatchEvent('OnTamerOrdersChanged')

        UTIL_Remove(self)
        
    @classmethod
    def BugBait_Create(cls, position, angles, velocity, angVelocity, owner, timer):
        bugbait = cls.Create( "bugbait", position, angles, owner)
        
        bugbait.SetTimer(timer, timer)
        bugbait.SetVelocity(velocity, angVelocity)
        bugbait.SetThrower(owner)
        bugbait.takedamage = DAMAGE_EVENTS_ONLY

        return bugbait
        
    BUGBAIT_MODEL = 'models/weapons/w_bugbait.mdl'
    
    bugbaitability = None
    