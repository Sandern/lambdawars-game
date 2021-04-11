from srcbase import IN_SPEED
from core.abilities import AbilityTargetGroup
from entities import MouseTraceData, D_LI
    
class AbilityConstruct(AbilityTargetGroup):
    # Info
    name = "construct"
    image_name = 'vgui/abilities/construct.vmt'
    rechargetime = 0
    displayname = "#AbilityConstruct_Name"
    description = "#AbilityConstruct_Description"
    hidden = True
    
    defaultautocast = True
    autocastcheckonidle = True
    autocastcheckonenemy = True
    
    # Ability
    @classmethod
    def NeedsConstructOrRepair(cls, target, unit=None):
        """ Returns True if target needs either repair or construct. """
        needsconstruct, reason = cls.NeedsConstruct(target, unit=unit)
        if needsconstruct: 
            return needsconstruct, reason
        return cls.NeedsRepair(target, unit=unit)
        
    @classmethod
    def NeedsConstruct(cls, target, unit=None):
        if not target or not target.IsUnit() or not target.isbuilding or not target.IsAlive():
            return False, '#Ability_InvalidTarget'
            
        if target.constructability != cls.name:
            return False, '#Ability_InvalidTarget'
            
        if target.NeedsUnitConstructing(unit=unit):
            return True, None
            
        return False, '#AbilityConstruct_NoConstReq'
        
    @classmethod
    def NeedsRepair(cls, target, unit=None):
        if not target or not target.IsUnit() or not target.IsAlive():
            return False, '#Ability_InvalidTarget'
        if not target.isbuilding:
            if not target.repairable:
                return False, '#Ability_InvalidTarget'
        else:
            if target.constructionstate != target.BS_CONSTRUCTED:
                return False, '#AbilityConstruct_NotConstr'

        if target.constructability != cls.name:
            return False, '#Ability_InvalidTarget'
            
        if target.health >= target.maxhealth:
            return False, '#AbilityConstruct_FullHP'
            
        return True, None
    
    if isserver:
        def DoAbility(self):
            data = self.mousedata
            target = data.ent
            if not target or self.unit.IRelationType(target) != D_LI:
                self.Cancel(cancelmsg='#Ability_InvalidTarget')
                return
                
            needsconstruct, reason = self.NeedsConstruct(target)
            needsrepair, reason2 = self.NeedsRepair(target)
            if needsconstruct:
                for unit in self.units:
                    self.behaviorgeneric_action = unit.behaviorgeneric.ActionConstruct
                    self.AbilityOrderUnits(unit, target=target, ability=self)
                self.Completed()
            elif needsrepair:
                for unit in self.units:
                    self.behaviorgeneric_action = unit.behaviorgeneric.ActionRepair
                    self.AbilityOrderUnits(unit, target=target, ability=self)
                self.Completed()
            else:
                self.Cancel(cancelmsg=reason2)
                
    @classmethod
    def OverrideOrder(cls, unit, data, player):
        if unit.orders:
            return False
        target = data.ent
        if not target or unit.IRelationType(target) != D_LI:
            return False
        needs_construction_or_repair, reason = cls.NeedsConstructOrRepair(data.ent, unit=unit)
        if needs_construction_or_repair:
            if isserver:
                unit.DoAbility(cls.name, [('leftpressed', data)], queueorder=player.buttons & IN_SPEED)
            return True
        return False
            
    @classmethod
    def CheckAutoCast(info, unit):
        myorigin = unit.GetAbsOrigin()
        myowner = unit.GetOwnerNumber()
        besttarget = None
        bestdistsqr = float('inf')
        for i in range(0, unit.senses.CountSeenOther()):
            other = unit.senses.GetOther(i)
            if not other or unit.IRelationType(other) != D_LI:
                continue
            needscr, reason = info.NeedsConstructOrRepair(other, unit=unit)
            if not needscr:
                continue
                
            distsqr = myorigin.DistToSqr(other.GetAbsOrigin())
            
            # Prefer own buildings
            if besttarget and besttarget.GetOwnerNumber() != myowner and other.GetOwnerNumber() == myowner:
                besttarget = other
                bestdistsqr = distsqr
                continue
                
            # Should be closer than best
            if distsqr > bestdistsqr:
                continue
                
            besttarget = other
            bestdistsqr = distsqr
                
        if besttarget:
            leftpressed = MouseTraceData()
            leftpressed.ent = besttarget
            unit.DoAbility(info.name, [('leftpressed', leftpressed)], autocasted=True)
            return True
                
        return False
        
    @classmethod
    def TryRepairTarget(info, unit, target):
        needscr, reason = info.NeedsConstructOrRepair(target, unit=unit)
        if needscr:
            leftpressed = MouseTraceData()
            leftpressed.ent = target
            unit.DoAbility(info.name, [('leftpressed', leftpressed)], autocasted=True)
            return True
        return False
        
class AbilityRepairDog(AbilityConstruct):
    name = "repair_dog"
    displayname = "#AbilityRepairDog_Name"
    description = "#AbilityRepairDog_Description"
    defaultautocast = False
    supportsautocast = False
        
class AbilityCombineRepair(AbilityConstruct):
    name = "combine_repair"
    displayname = "#AbilityCmbRepair_Name"
    description = "#AbilityCmbRepair_Description"
    defaultautocast = False
    supportsautocast = False