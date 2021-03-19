from srcbase import *
from vmath import Vector, QAngle, VectorYawRotate, VectorAngles, VectorNormalize, vec3_origin
from entities import entity, FClassnameIs
from .base import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from utils import UTIL_FindPosition, FindPositionInfo
from fields import StringField, VectorField, OutputField, BooleanField, IntegerField, ListField, FloatField, fieldtypes
from core.attributes import CoverAttributeInfo
from core.signals import FireSignalRobust, garrisonchanged
from core.units.info import ParseAttributes
from playermgr import ListAlliesOfOwnerNumber
import random
import operator
import math

if isserver:
    from entities import entitylist, CTakeDamageInfo
    from utils import UTIL_DropToFloor
    from gameinterface import CRecipientFilter
    from core.units import UnitCombatSense, unit_nodamage


class UnitBaseGarrisonableShared(object):
    if isserver:
        def Spawn(self):
            super().Spawn()

            # Do not interfere with range checks of garrisoned units
            #self.SetBlocksLOS(False)

            if self.sense_distance is not None:
                self.senses = UnitCombatSense(self)
                self.senses.sensedistance = self.sense_distance
                self.senses.testlos = True
                if self.sense_cone is not None:
                    self.senses.SetUseLimitedViewCone(True)
                    self.senses.SetViewCone(self.sense_cone)
            
            # Set enter offset if any
            if self.entertarget:
                rp = entitylist.FindEntityByName(None, self.entertarget)
                if not rp:
                    PrintWarning('%s (at %s) has an invalid enter point!\n' % (self.GetClassname(), self.GetAbsOrigin()))
                else:
                    self.enteroffset = rp.GetAbsOrigin() - self.GetAbsOrigin()
                    
            if self.enteroffset != vec3_origin:
                self.SetEnterOffset(self.enteroffset)
            
            # Rotate exit offset
            yaw = self.GetAbsAngles().y
            VectorYawRotate(self.exitoffset, yaw, self.exitoffset)
            
            # Set exit offset
            if self.exittarget:
                rp = entitylist.FindEntityByName(None, self.exittarget)
                if not rp:
                    PrintWarning('%s (at %s) has an invalid exit point!\n' % (self.GetClassname(), self.GetAbsOrigin()))
                else:
                    self.exitoffset = rp.GetAbsOrigin()
            else:
                # Find a position for the rallypoint. Initial position might be embedded in solid or not on the ground.
                self.exitoffset = self.GetAbsOrigin() + self.exitoffset
                info = UTIL_FindPosition(FindPositionInfo(self.exitoffset, -Vector(32, 32, 0), Vector(32, 32, 64), 0, 128))
                if info.success:
                    self.exitoffset = info.position

        def UpdateOnRemove(self):
            self.UnGarrisonAll()
            self.senses = None
            
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
                
        def Event_Killed(self, info):
            super().Event_Killed(info)
            
            self.UnGarrisonAll()

        def HealThink(self):
            medicCount = len([unit for unit in self.units if 'heal' in unit.unitinfo.abilities.values()])
            if medicCount > 0:
                dt = gpGlobals.curtime - self.GetLastThink()
                heal = int(round(dt * 2 * medicCount))

                for unit in self.units:
                    # Must not be mechanic
                    if 'mechanic' in unit.attributes:
                        continue

                    if unit.health < unit.maxhealth:
                        unit.health += min(heal, (unit.maxhealth - unit.health))

        def BuildThink(self):
            self.HealThink()
            super().BuildThink()

            if self.senses:
                self.senses.PerformSensing()
                self.UpdateEnemy(self.senses)
            for unit in list(self.units):
                if not self.CanGarrisonUnitByOwner(unit):
                    self.UnGarrisonAll()

        def GetEnemyForGarrisonedUnit(self, unit):
            if self.senses:
                return self.enemy
            return unit.enemy

    def OnUnitTypeChanged(self, oldunittype):
        """ Called when the unit type changes. Updates population. """
        super().OnUnitTypeChanged(oldunittype)

        self.garrisoned_attributes = self.InitializeAttributes(self.unitinfo.garrisoned_attributes)

    def OnTakeDamage(self, dmg_info):
        if unit_nodamage.GetBool():
            return 0

        # Modify damage, make units absorb some damage too
        if dmg_info.GetDamage() > 1.0 and self.units:
            attacker = dmg_info.GetAttacker()
            if not attacker or not attacker.IsUnit() or attacker.unitinfo.tier != 1:
                garrisoned_scaled_damage = CTakeDamageInfo(attacker, attacker, dmg_info.GetDamage(), dmg_info.GetDamageType())
                garrisoned_scaled_damage.attributes = dmg_info.attributes
                garrisoned_scaled_damage = self.ScaleDamageToAttributes(garrisoned_scaled_damage, self.garrisoned_attributes)
                damage = garrisoned_scaled_damage.GetDamage()

                # Split damage by two
                # if attribute == 'fire':
                splitdamage = damage * self.units_dmg_modifier
                # else splitdamage = 0
                # Send damage to units
                n = len(self.units)
                if n == 1:
                    info2 = CTakeDamageInfo(attacker, attacker, 0, 0)
                    info2.SetDamage(splitdamage)
                    unit = min(self.units)
                    unit.OnTakeDamage(info2)
                else:
                    units = random.sample(list(self.units), int(n/2))
                    splitdamage2 = splitdamage / float(n/2)
                    for unit in units:
                        info2 = CTakeDamageInfo(attacker, attacker, 0, 0)
                        info2.SetDamage(splitdamage2)
                        unit.OnTakeDamage(info2)
        
        # Clamp damage to healthungarrisonable
        #if self.destroyable and self.healthungarrisonable != 0:
        #    pass

        # Damage building
        ret = super().OnTakeDamage(dmg_info)

        # Ungarrison if below a certain threshold
        if self.units and self.health < self.healthungarrisonable:
            self.UnGarrisonAll()
    
        return ret
    
    def GetCurrentPopulation(self):
        return sum(map(operator.attrgetter('population'), self.units))
    
    def CanGarrisonUnit(self, unit):
        if not self.isconstructed:
            return False
            
        if self.health < self.healthungarrisonable:
            return False
            
        if self.maxpopulation > 0:
            curpop = self.GetCurrentPopulation()
            if curpop + unit.population > self.maxpopulation:
                return False
                
        owner = self.GetOwnerNumber()        
        unitowner = unit.GetOwnerNumber()
        owners = ListAlliesOfOwnerNumber(owner)
        unitowners = ListAlliesOfOwnerNumber(unitowner)
        
            
        for owner in owners:
            if unitowners != owners:
                return False
            else:
                return True
        return True
    def CanGarrisonUnitByOwner(self, unit):
        owner = self.GetOwnerNumber()        
        unitowner = unit.GetOwnerNumber()
        owners = ListAlliesOfOwnerNumber(owner)
        unitowners = ListAlliesOfOwnerNumber(unitowner)
        
            
        for owner in owners:
            if unitowners != owners:
                return False
            else:
                return True
        return True

    def GarrisonUnit(self, unit):
        if unit in self.units:
            return
            
        unit.garrison_oldlosmask = unit.attacklosmask
        unit.garrison_oldsensedistance = unit.senses.sensedistance
        unit.locomotionfacingonly = True
        unit.AddSolidFlags(FSOLID_NOT_SOLID)
        #unit.AddEffects(EF_NODRAW)
        #if unit.activeweapon:
            #unit.activeweapon.AddEffects(EF_NODRAW)
            #unit.activeweapon.SetCollisionGroup(WARS_COLLISION_GROUP_IGNORE_ALL_UNITS)
            #unit.activeweapon.SetCollisionGroup(COLLISION_GROUP_DEBRIS)
            
        #unit.SetCanBeSeen(False)
        #position all units correctly
      
        unit.navigator.StopMoving()
        unit.garrisoned = True
        unit.garrisoned_building = self.GetHandle()
        unit.senses.sensedistance = unit.senses.sensedistance + 128.0 # Make sure units are not outranged by similar units (TODO: maybe find a better solution later)
        unit.OnGarrisonedChanged()
        self.units.append(unit.GetHandle())
        unit.AddAttribute(CoverAttributeInfo)

        for idx, listunit in enumerate(self.units):
            angle = (3.14/float(self.maxpopulation))*idx+ (self.GetAbsAngles().y*3.14/180) -(1.4/float(self.maxpopulation))*len(self.units)
            listunit.SetAbsOrigin(self.GetAbsOrigin()+Vector(60*math.cos(angle),60*math.sin(angle),   0))
        #unit.SetAbsOrigin(self.GetAbsOrigin())

        # Deselect the unit from everywhere
        players = list(unit.selected_by_players)
        for p in players:
            p.RemoveUnit(unit)

        filter = CRecipientFilter()
        filter.MakeReliable()
        [filter.AddRecipient(p) for p in players]
        unit.SendEvent(filter, unit.UNIT_DESELECT)
        
        # Become owned by unit
        if len(self.units) == 1:
            if not self.playerowned: self.SetOwnerNumber(unit.GetOwnerNumber())
            self.ongarrisoned.Set(self.GetOwnerNumber(), self, self)
            
    def UnGarrisonUnit(self, unit):
        if unit not in self.units:
            return

        unit.locomotionfacingonly = False
        unit.RemoveSolidFlags(FSOLID_NOT_SOLID)
        unit.RemoveEffects(EF_NODRAW)
        if unit.activeweapon:
            unit.activeweapon.RemoveEffects(EF_NODRAW)
        unit.SetCanBeSeen(True)
        unit.garrisoned = False
        unit.garrisoned_building = None
        unit.senses.sensedistance = unit.garrison_oldsensedistance
        self.units.remove(unit.GetHandle())
        unit.RemoveAttribute(CoverAttributeInfo)
        unit.OnGarrisonedChanged()
        
        info = unit.unitinfo
        
        # Place the unit somewhere..
        # Find a position for the unit around the exit (todo: define exit)
        dir = self.exitoffset - self.GetAbsOrigin()
        VectorNormalize(dir)
        angle = QAngle()
        VectorAngles(dir, angle)
        
        radius = (self.exitoffset - self.GetAbsOrigin()).Length2D()
        info = UTIL_FindPosition(FindPositionInfo(self.GetAbsOrigin(), 
                    info.mins, info.maxs, radius, max(1024, radius*2), startyaw=angle.y))
        position = info.position if info.success else self.GetAbsOrigin()
            
        unit.SetAbsOrigin(position + Vector(0,0,24)) # Must float above the ground a bit, otherwise we fall through the ground
        UTIL_DropToFloor(unit, MASK_NPCSOLID)
        
        unit.ClearOrder(dispatchevent=True)
        
        # Become free again
        #if not self.units:
        #    if not self.playerowned: self.SetOwnerNumber(0)
        #    self.onungarrisoned.Set('', self, self)
            
    def UnGarrisonAll(self):
        self.units[:] = [u for u in self.units if bool(u)] # Remove none entries
        for unit in list(self.units):
            self.UnGarrisonUnit(unit)
            
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            from core.hud import BaseHudGarrisonUnits
            self.unitpanelclass = BaseHudGarrisonUnits
            
        def OnGarrisonedUnitsChanged(self):
            FireSignalRobust(garrisonchanged, building=self)
    
    garrisonable = True
    garrisoned_attributes = {}
    exitoffset = VectorField(value=Vector(0,0,0), keyname='exitoffset', helpstring='Offset at which units exit the building')
    exittarget = StringField(value='', keyname='exittarget', helpstring='Target entity at which units exit')
    enteroffset = VectorField(value=Vector(0,0,0), keyname='enteroffset', helpstring='Offset at which units enter the building')
    entertarget = StringField(value='', keyname='entertarget', helpstring='Target entity at which units enter')
    destroyable = BooleanField(value=True, keyname='destroyable', helpstring='Can this building be completely destroyed?')
    healthungarrisonable = IntegerField(value=0, keyname='healthungarrisonable', helpstring='Health at which this building is ungarrisonable')
    maxpopulation = IntegerField(value=0, keyname='maxpopulation', helpstring='Maximum number of population in units this building can take.')
    playerowned = BooleanField(value=False, keyname='playerowned', helpstring='Do not change the owner of the building to neutral when empty.')
    units_dmg_modifier = FloatField(value=0.0, helpstring='Modifies the damage taken by garrisoned units')  # change
    # from 0.4 to 0.0 so units inside the bunker receive no damage.
    
    ongarrisoned = OutputField(keyname='OnGarrisoned', fieldtype=fieldtypes.FIELD_INTEGER)
    onungarrisoned = OutputField(keyname='OnUnGarrisoned')
    
    units = ListField(networked=True, clientchangecallback='OnGarrisonedUnitsChanged')

    senses = None

    #: Used by wars_game.abilties.garrison actions to decide on enemies when not None
    sense_distance = None
    sense_cone = None


@entity('build_garrisonable', networked=True,
        studio='null')
class UnitBaseGarrisonableBuilding(UnitBaseGarrisonableShared, BaseClass):
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            from core.hud import BaseHudGarrisonUnits, HudBuildConstruction
            if self.constructionstate != self.BS_CONSTRUCTED:
                self.unitpanelclass = HudBuildConstruction
            else:
                self.unitpanelclass = BaseHudGarrisonUnits
                


class GarrisonableBuildingInfo(WarsBuildingInfo):
    cls_name = 'build_garrisonable'
    attributes = ['building']

    #: Attributes applied to garrisoned units when receiving damage
    garrisoned_attributes = []
    
    abilities = {
        0: 'ungarrisonall',
        8: 'cancel',
    }

    @classmethod
    def OnLoaded(info):
        super().OnLoaded()

        # Convert attributes names to refs to the info class of that attribute
        info.garrisoned_attributes = ParseAttributes(info, info.garrisoned_attributes)