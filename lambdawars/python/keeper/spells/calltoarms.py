from vmath import QAngle
from core.abilities import AbilityTarget
from core.units import unitlist
from core.resources import TakeResources, HasEnoughResources, MessageResourceIndicator
from utils import UTIL_ListPlayersForOwnerNumber
from entities import CBaseEntity, entity
from gamerules import gamerules
from particles import *

from collections import defaultdict

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    
calltoarments = defaultdict( lambda: None )
    
@entity('sk_calltoarms')
class CallToArmsEnt(CBaseEntity):
    def Precache(self):
        super(CallToArmsEnt, self).Precache()
        
        PrecacheParticleSystem('clicked_default')
        
    def Spawn(self):
        super(CallToArmsEnt, self).Spawn()
        
        self.SetThink(self.UpdateEffects, gpGlobals.curtime)
        
    def UpdateOnRemove(self):
        super(CallToArmsEnt, self).UpdateOnRemove()
        
        calltoarments[self.GetOwnerNumber()] = None
        
    def OnChangeOwnerNumber(self, oldownernumber):
        super(CallToArmsEnt, self).OnChangeOwnerNumber(oldownernumber)
        
        if calltoarments[oldownernumber] == self.GetHandle():
            calltoarments[oldownernumber] = None
            
        assert(calltoarments[self.GetOwnerNumber()] == None)
        calltoarments[self.GetOwnerNumber()] = self.GetHandle()
        
    def UpdateEffects(self):
        origin = self.GetAbsOrigin()
        ownernumber = self.GetOwnerNumber()
        
        #if self.nexteffectsupdate < gpGlobals.curtime:
        DispatchParticleEffect('clicked_default', origin, QAngle(0,0,0))
            #self.nexteffectsupdate = gpGlobals.curtime + 1.25
            
        goldcost = 2
        if not HasEnoughResources([('gold', goldcost)], ownernumber):
            self.Remove()
            return
        
        TakeResources(ownernumber, [('gold', goldcost)])
        MessageResourceIndicator(ownernumber, origin, 'gold -%d' % (goldcost))
            
        self.SetNextThink(gpGlobals.curtime + 1.25)
        
    @classmethod
    def CreateOrUpdateCallToArms(cls, position, ownernumber):
        if calltoarments[ownernumber]:
            ent = calltoarments[ownernumber]
        else:
            ent = CreateEntityByName('sk_calltoarms')
            ent.SetOwnerNumber(ownernumber)
            DispatchSpawn(ent)
            ent.Activate()
        ent.SetAbsOrigin(position)
        
        for unit in unitlist[ownernumber]:
            if not hasattr(unit, 'DispatchEvent'):
                continue
            unit.DispatchEvent('OnCallToArms', ent)
        
        return ent
        
    nexteffectsupdate = 0.0
    
class AbilityCallToArms(AbilityTarget):
    name = "calltoarms"
    displayname = "Call to Arms"
    description = "Forces all creatures in your dungeon to defend the specified point at the cost of 2 gold per 1.25 seconds. Left click a point to activate the spell and right click to deactivate the spell."
    requireunits = False
    costs = [('gold', 10)]
    
    def DoAbilityInternal(self):
        # Copy the target position and angle
        self.targetpos = self.GetTargetPos(self.mousedata)
    
        # Cleanup
        self.cancelonmouselost = False
        if isclient:
            self.DestroyArrow()
            if self.clearvisualsonmouselost:
                self.ClearVisuals()
            else:
                if self.cleartempmodonmouselost:
                    self.ClearTempModel()
        
        # Do the actual ability
        self.PlayActivateSound()
        self.DoAbility()
        
    if isserver:
        def StartAbility(self):
            pass
        
        def DoAbility(self):
            data = self.player.GetMouseData()
            targetpos = data.endpos
            ownernumber = self.ownernumber
            
            tile = gamerules.keeperworld.GetTileFromPos(targetpos)
            if tile.GetOwnerNumber() != ownernumber:
                return
            
            if not calltoarments[ownernumber]:
                if not self.TakeResources(refundoncancel=False):
                    self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                    return
                
            CallToArmsEnt.CreateOrUpdateCallToArms(targetpos, ownernumber)
            self.Completed()
            
        def OnRightMouseButtonReleased(self):
            ownernumber = self.ownernumber
            if calltoarments[ownernumber]:
                calltoarments[ownernumber].Remove()
            return super(AbilityCallToArms, self).OnRightMouseButtonReleased()
