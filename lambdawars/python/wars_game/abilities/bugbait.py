from core.abilities import AbilityThrowObject, AbilityInstant
from fields import IntegerField
from entities import MouseTraceData
if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_PrecacheOther
    
class AbilityBugBaitShared(object):
    summonantlions = False
    maxantlions = IntegerField(value=3, helpstring='Max number of spawned Antlions per tamer.')
    
    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()
            
            UTIL_PrecacheOther('bugbait')
        
    @classmethod
    def SetupOnUnit(info, unit):
        super().SetupOnUnit(unit)
        
        if getattr(unit, 'abibugbait_antlions', None) == None:
            unit.abibugbait_antlions = set()
            unit.abibugbait_lastspawntime = 0
            unit.abibugbait_spawnpenalty = 0
        
    @classmethod
    def OnUnitThink(info, unit):
        unit.abibugbait_antlions = set(filter(bool, unit.abibugbait_antlions))

class AbilityBugBait(AbilityBugBaitShared, AbilityThrowObject):
    # Info
    name = "bugbait"
    rechargetime = 6.0
    throwrange = 1024
    #energy = 35.0
    #costs = [('requisition', 10)]
    displayname = "#RebBugBait_Name"
    description = "#RebBugBait_Description"
    image_name = 'vgui/rebels/abilities/rebel_bugbait.vmt'
    
    objectclsname = 'bugbait'
    
    #defaultautocast = True
    #autocastcheckonidle = True
    
    # TODO: make ability work on group
    def SelectUnits(self): 
        return self.SelectGroupUnits() 
    
    def SetupObject(self, throwobject):
        super().SetupObject(throwobject)
        
        throwobject.bugbaitability = self
        
    allowmultipleability = True

class AbilityBugBaitRecall(AbilityBugBaitShared, AbilityInstant):
    # Info
    name = "bugbaitrecall"
    rechargetime = 15.0
    displayname = "#RebBugBaitRecall_Name"
    description = "#RebBugBaitRecall_Description"
    image_name = 'vgui/rebels/abilities/reb_squeez_bugbait.vmt'
    energy = 75
    summonantlions = True
    
    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        requirements.discard('energy') 
        return requirements
    if isserver:
        def DoAbility(self):
            self.SelectGroupUnits()
            if not self.units:
                self.Cancel(debugmsg='No units found for ability')
                return
                
            #units = self.TakeEnergy(self.units)
            #if not units:
            #    self.Cancel(debugmsg='No units with enough energy found')
            #    return
                
            self.throwtarget = None
            for unit in list(self.units):
                if len(unit.abibugbait_antlions) == 0:
                    energy = self.energy
                elif len(unit.abibugbait_antlions) != self.maxantlions:
                    energy = self.energy * (1 - len(unit.abibugbait_antlions)/self.maxantlions)
                elif len(unit.abibugbait_antlions) == self.maxantlions:
                    energy = 1
                if not self.TakeEnergy(unit, energy):
                    continue
                bugbait = CreateEntityByName('bugbait')
                bugbait.SetAbsOrigin(unit.GetAbsOrigin())
                bugbait.SetOwnerNumber(self.ownernumber)
                bugbait.SetThrower(unit)
                bugbait.bugbaitability = self
                DispatchSpawn(bugbait)
                bugbait.Detonate(target=unit)
                
            self.SetRecharge(list(self.units))
            self.Completed()
            
    allowmultipleability = True

    sai_hint = AbilityInstant.sai_hint | set(['sai_deploy'])
    
    