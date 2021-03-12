from srcbase import IN_SPEED
from vmath import vec3_origin, vec3_angle
from core.abilities import AbilityTargetGroup
from core.units import GetUnitInfo
from fields import IntegerField, FloatField

if isserver:
    from core.units import BehaviorGeneric
    from entities import entitylist
    from unit_helper import GF_OWNERISTARGET
    
if isserver:
    class ActionSalvaging(BehaviorGeneric.ActionChanneling):
        def Init(self, scrapmarker, *args, **kwargs):
            super().Init(*args, **kwargs)
            
            self.scrapmarker = scrapmarker
            
        def OnStart(self):
            self.scrapmarker.salvagingworkers.add(self.outer)
            return super().OnStart()
            
        def OnEnd(self):
            if self.scrapmarker:
                self.scrapmarker.salvagingworkers.discard(self.outer)
            super().OnEnd()
            
        def Update(self):
            if not self.scrapmarker:
                return self.Done('Scrap marker is gone!')
            return super().Update()
        
    class ActionSalvage(BehaviorGeneric.ActionAbility):
        """ Main action for salvaging ability of Rebel engineer.
        
            Action flow:
            1. Find nearest scrap marker (or use provided targeted one by player)
            2. Move to found scrap marker
            3. Start salvaging action
            4. Return to nearest scrap collection point
            5. Repeat 1
        """
        def FindNearestBuilding(self, classnames, checkownernumber=True, fnfilter=lambda x: True):
            """ Finds nearest building entity of which the classname matches one in the provided list.
                
                Args:
                    classnames(list): List of classnames
                    
                Kwargs:
                    checkownernumber (bool): whether or not to check the owner of the building matching the unit executing this action.
                    fnfilter (method): optional filter which receives the current entity checking as argument
            """
            classnames = [classnames] if type(classnames) == str else classnames
            best = None
        
            for classname in classnames:
                cur = entitylist.FindEntityByClassname(None, classname)
                while cur:
                    isvalid = getattr(cur, 'isconstructed', False)
                
                    if isvalid and (not checkownernumber or cur.GetOwnerNumber() == self.outer.GetOwnerNumber()) and fnfilter(cur):
                        dist = cur.GetAbsOrigin().DistTo(self.outer.GetAbsOrigin())
                        if not best:
                            best = cur
                            bestdist = dist
                        else:
                            if dist < bestdist:
                                best = cur
                                bestdist = dist
                    cur = entitylist.FindEntityByClassname(cur, classname)
            return best
            
        def FindNearestHQ(self): 
            return self.FindNearestBuilding(['build_reb_hq', 'build_reb_junkyard', 'build_comb_hq', 'build_comb_factory'])
        def FindNearestScrapMarker(self, maxrange=None, mustbefree=False):
            origin = self.outer.GetAbsOrigin()
            fnfilter = lambda cur: (not mustbefree or len(cur.salvagingworkers) < cur.unitinfo.maxworkers) and (not maxrange or (origin - cur.GetAbsOrigin()).Length2D() < maxrange)
            return self.FindNearestBuilding(['scrap_marker', 'scrap_marker_small'], checkownernumber=False, fnfilter=fnfilter)
            
        def Update(self):
            ability = self.order.ability
            target = self.order.target
            outer = self.outer
            
            if not outer.carryingscrap:
                path = outer.navigator.path
                
                # Not carrying any scrap, so moving to a scrap marker
                targetscrapmarker = target
                if not ability.CanSalvageTarget(targetscrapmarker):
                    targetscrapmarker = self.FindNearestScrapMarker()
                    
                # Check if we are at a scrap marker, but it's taken. In this case find a non free within radius
                # It's also possible the scrap marker depleted while we arrived at it (or waiting for a spot).
                if (path.success and path.pathcontext == targetscrapmarker and
                        (not targetscrapmarker or
                                 len(targetscrapmarker.salvagingworkers) >= targetscrapmarker.unitinfo.maxworkers)):
                    othertarget = self.FindNearestScrapMarker(maxrange=512.0, mustbefree=True)
                    if othertarget:
                        self.order.target = othertarget  # Remember new choice
                        targetscrapmarker = othertarget
                            
                # Target must exist
                if not targetscrapmarker:
                    return self.ChangeTo(self.behavior.ActionIdle, "No salvage target")
                    
                # Get in range
                self.contextmovetoscrap = targetscrapmarker
                if path.pathcontext != self.contextmovetoscrap or not path.success:
                    return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to scrap marker", targetscrapmarker, 
                            tolerance=self.TOLERANCE, goalflags=GF_OWNERISTARGET, pathcontext=self.contextmovetoscrap)
                
                # There's a maximum number of workers which can salvage at the same time
                if len(targetscrapmarker.salvagingworkers) >= targetscrapmarker.unitinfo.maxworkers:
                    # Maybe there is another free scrap point nearby? Change to that one instead.
                    return self.Continue()
                
                # Salvage time
                trans = self.SuspendFor(ActionSalvaging, 'Salvaging', targetscrapmarker, ability.salvagetime, ability=ability)
                self.scrapingaction = self.nextaction
                return trans
            else:
                # Carrying scrap, so moving back to collection point
                collectionpoint = target
                if not ability.CanReturnSalvageToBase(outer, collectionpoint):
                    collectionpoint = self.FindNearestHQ()
                    
                if not collectionpoint:
                    return self.ChangeTo(self.behavior.ActionIdle, "No collection point to return to...")
                    
                self.movingtohq = collectionpoint
                self.contextmovetocollectpoint = collectionpoint
                return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to collection point with a scrap on my back", collectionpoint, 
                        tolerance=self.TOLERANCE, pathcontext=self.contextmovetocollectpoint)
            
        def OnResume(self):
            outer = self.outer
            
            if self.scrapingaction:
                p = self.order.target
                if p and self.scrapingaction.channelsuccess:
                    # Salvage time
                    scrap = p.GetScrap(value=self.order.ability.salvagenumber)
                    if scrap:
                        scrap.SetOwnerEntity(outer)
                        scrap.AttachTo(outer)
                        scrap.SetLocalOrigin(vec3_origin)
                        scrap.SetLocalAngles(vec3_angle)
                        outer.carryingscrap = scrap.GetHandle()
            
                self.scrapingaction = None
            elif outer.carryingscrap:
                if self.movingtohq and outer.navigator.path.success:
                    # Add resources and destroy scrap
                    outer.carryingscrap.AttachTo(None)
                    outer.carryingscrap.AddResourcesAndRemove(outer.GetOwnerNumber())
                    outer.carryingscrap = None
                    
            # Reset just in case
            self.movingtohq = None
                    
        TOLERANCE = 32.0
        
        contextmovetoscrap = 'contextmovetoscrap'
        contextmovetocollectpoint = 'contextmovetocollectpoint'
        
        movingtohq = None # The current collection point we are moving to
        scrapingaction = None
        
class AbilitySalvage(AbilityTargetGroup):
    # Info
    name = "salvage"
    image_name = 'vgui/abilities/collectgrubs.vmt'
    rechargetime = 0
    displayname = "#RebSalvage_Name"
    description = "#RebSalvage_Description"
    image_name = 'vgui/rebels/abilities/salvage'
    hidden = True
    
    salvagetime = FloatField(value=6.9)
    salvagenumber = IntegerField(value=4)
    
    targetmarker = None
    
    @classmethod
    def CanSalvageTarget(cls, target):
        if not target or not target.IsUnit():
            return False
            
        info = GetUnitInfo('scrap_marker')
        if not info or not issubclass(target.unitinfo, info):
            return False
            
        return True
        
    @classmethod
    def CanReturnSalvageToBase(cls, unit, target):
        if not target or not target.IsUnit():
            return False
            
        if target.GetClassname() != 'build_reb_hq' or not unit.carryingscrap:
            return False
        
        return True
    
    @classmethod
    def OverrideOrder(cls, unit, data, player):
        target = data.ent
        
        if cls.CanSalvageTarget(target) or cls.CanReturnSalvageToBase(unit, target):
            if isserver:
                unit.DoAbility('salvage', [('leftpressed', data)], queueorder=player.buttons & IN_SPEED)
            return True
        
        return False
        
    def DoAbility(self):
        data = self.mousedata
        target = data.ent
        if not target or target.IsWorld():
            self.Cancel()
            return
        
        for unit in self.units:
            if not self.CanSalvageTarget(target) and not self.CanReturnSalvageToBase(unit, target):
                continue
                
            self.targetmarker = target
            self.AbilityOrderUnits(unit, target=target, ability=self)
        self.Completed()
            
    if isserver:
        behaviorgeneric_action = ActionSalvage
