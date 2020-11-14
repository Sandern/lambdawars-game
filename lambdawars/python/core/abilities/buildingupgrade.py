from . base import AbilityBase
from . placeobject import AbilityPlaceObjectShared
from fields import FloatField, StringField
from utils import UTIL_EntitiesInSphere


class AbilityBuildingUpgradeShared(object):
    """ Defines common methods for AbilityBuildingUpgrade and
        AbilityTargetBuildingUpgrade regarding building upgrades.
    """
    resource_category = 'economy'

    def StartUpgradeInternal(self, building):
        """ Common functionality to start a upgrade shared by all buildings. """
        if isserver:
            building.activeupgrade = self
            building.SetConstructionState(building.BS_UPGRADING)
        self.StartUpgrade(building)
            
    def StartUpgrade(self, building):
        """ Initializes a building upgrade.
        
            The building construction code will already set the right construction values and
            changes the building activity. This method allows for further customization.
        """
        pass
            
    def CallFinishUpgrade(self, building):
        """ Internal finish upgrade. Pretty much just calls FinishUpgrade. """
        self.FinishUpgrade(building)
        self.Completed()
        
    def FinishUpgrade(self, building):
        """ Called upon finishing the upgrade.
        
            This method is responsible for applying the new upgrade values.
        """
        pass
        
    def CancelUpgrade(self, building):
        """ Restores building to previous state (if implemented). """
        pass


class AbilityBuildingUpgrade(AbilityBuildingUpgradeShared, AbilityBase):
    """ Defines a building upgrade triggered from within the building abilities itself. """
    upgradetime = FloatField(value=10)
    upgradeactivity = StringField(value='')

    def Init(self):
        self.SelectSingleUnit()
        if not self.unit:
            self.Cancel(debugmsg='Unable to to find suitable units')
            return
        
        if isserver:
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return
        
            self.StartUpgradeInternal(self.unit)


class AbilityTargetBuildingUpgrade(AbilityBuildingUpgradeShared, AbilityPlaceObjectShared):
    """ Defines a building upgrade triggered by targeting the building by another unit.
        This unit will move up to the building to start the upgrade. """
    #: Unit info name of target building to be upgradable
    targetunitinfo = StringField(value='')
    
    # Shouldn't require population
    population = 0
    # No need for rotation
    requirerotation = False
    
    lastbuildtarget = None
    
    def IsValidBuildingTarget(self, building):
        return True
        
    def GetTargetBuilding(self, pos):
        """ Tries to find a target candidate building at the specified position. """
        from core.units import GetUnitInfo
        targetunitinfo = GetUnitInfo(self.targetunitinfo)
        if not targetunitinfo:
            return None
            
        foundtarget = None
        targets = UTIL_EntitiesInSphere(1024, pos, 48.0, 0)
        for target in targets:
            if not target or not target.IsUnit():
                continue
                
            if target.GetOwnerNumber() != self.ownernumber:
                continue
                
            testunitinfo = target.unitinfo
            if not issubclass(testunitinfo, targetunitinfo):
                continue
                
            if not self.IsValidBuildingTarget(target):
                continue
                
            foundtarget = target
            break
        
        return foundtarget
        
    def IsValidPosition(self, pos):
        self.lastbuildtarget = self.GetTargetBuilding(pos)
        return self.lastbuildtarget is not None
        
    def DoPlaceObject(self):
        building = self.lastbuildtarget
        if not building:
            self.Cancel()
            return

        self.StartUpgradeInternal(building)
        return building
        
    def GetPlaceAction(self, unit):
        return unit.behaviorgeneric.ActionPlaceBuilding
        
    if isserver:
        def DoAbility(self): 
            """ In case executed by an unit it is added to this unit's building queue.
                Otherwise if executed as cheat: directly place at the target location. """
            if self.placeatmins:
                self.targetpos.z += -self.mins.z

            if self.ischeat:
                self.DoPlaceObject()
                self.Completed()
                return
                
            if not self.unit:
                self.Cancel(cancelmsg='Unit died while executing the place action')
                return
            
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources')
                return
            validposition = self.IsValidPosition(self.targetpos)
            if not validposition:
                self.Cancel(cancelmsg='#Ability_InvalidPosition', debugmsg=self.debugvalidposition)
                return
            
            self.behaviorgeneric_action = self.GetPlaceAction(self.unit)
            self.AbilityOrderUnits(self.unit, position=self.targetpos, target=self.lastbuildtarget, ability=self)
        
    if isclient:
        def GetPreviewPosition(self, groundpos):
            self.lastbuildtarget = self.GetTargetBuilding(groundpos)
            if not self.lastbuildtarget:
                return super().GetPreviewPosition(groundpos)
                
            return self.lastbuildtarget.GetAbsOrigin()
