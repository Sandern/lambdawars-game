'''
Pick up item. Can be picked up by defined units and filtered via triggers.
'''

from srcbase import *
from vmath import *
from core.units import UnitBase
from fields import FloatField, BooleanField, ModelField, FilterField, input, fieldtypes, OutputField
from entities import entity, entlist

if isserver:
    from utils import UTIL_Remove, UTIL_ScaleForGravity, UTIL_SetSize, trace_t, UTIL_TraceLine

@entity('wars_generic_item', networked=True, studio='null')
class GenericItem(UnitBase):
    def GetIMouse(self):
        ''' Returns if this entity has a mouse interface.
            By default units have this, but return None to prevent this.
        '''
        return None
        
    def IsSelectableByPlayer(self, player, target_selection):
        return False

    #outputs
    onpickup = OutputField(keyname='OnPickUp', fieldtype=fieldtypes.FIELD_INTEGER)
    ondrop = OutputField(keyname='OnDrop', fieldtype=fieldtypes.FIELD_INTEGER)
    
    if isserver:
        def Precache(self):
            self.PrecacheModel(self.worldmodel)
            self.PrecacheModel(self.carrymodel)
            
            super().Precache()
            
            for gibmodel in self.gibmodels:
                self.PrecacheModel(gibmodel)
            
        def Spawn(self):
            self.resetposition = self.GetAbsOrigin()
            self.worldmodel = self.GetModelName()
            self.Precache()
            super().Spawn()
            self.SetupForPickup()
            self.SetCanBeSeen(False)
            self.FindFilterEntity()
            
        def UpdateOnRemove(self):
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
            
            # Detach and drop
            self.Detach(nodropoutput=True)
        
        def FindFilterEntity(self):
            self.pickupfilter = None
            if not self.pickupfiltername:
                return
            self.pickupfilter = entlist.FindEntityByName(None, self.pickupfiltername)
            if not self.pickupfilter:
                PrintWarning('#%d: Item "%s" could not find filter entity %s\n' % (self.entindex(), self.GetEntityName(), self.pickupfiltername))
            
        def PlaceOnGround(self):
            origin = self.GetAbsOrigin()
            tr = trace_t()
            UTIL_TraceLine(origin, origin - Vector(0, 0, 4096.0), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr)
            self.SetAbsOrigin(tr.endpos)
            
        def SetupForPickup(self):
            self.SetModel(self.worldmodel)
            
            #self.SetSolid(SOLID_VPHYSICS)
            self.SetSolid(SOLID_BBOX)
            self.SetSolidFlags(FSOLID_NOT_SOLID|FSOLID_TRIGGER)
            #self.SetMoveType(MOVETYPE_VPHYSICS)
            self.CollisionProp().UseTriggerBounds(True,1)
            
            #self.VPhysicsInitNormal(SOLID_VPHYSICS, FSOLID_NOT_STANDABLE, False)
            
            mins = -Vector(24, 24, 0)
            maxs = Vector(24, 24, 48)
            
            UTIL_SetSize(self, mins, maxs)
            
            self.PlaceOnGround()
            self.PhysicsTouchTriggers()
            
            self.SetThink(self.ActivateForPickup, gpGlobals.curtime + self.afterdroppickupdelay)
            
        def SetupForCarrying(self):
            self.SetTouch(None)
            self.SetModel(self.carrymodel)
            
        def ResetPositionThink(self):
            # Got picked up in the meanwhile
            if self.carriedbyunit:
                return
                
            # Already close enough to start position
            distance = self.GetAbsOrigin().DistTo(self.resetposition)
            if distance < 16.0:
                return
                
            self.ResetPosition()
                
        def ResetPosition(self):
            ''' Sets origin of item to reset position. '''
            self.Detach() # Just in case
            self.SetAbsOrigin(self.resetposition)
                
        def ActivateForPickup(self):
            if not self.enabledforpickup:
                return
                
            self.SetTouch(self.ItemTouch)
            self.enableunitblink = True
            
            if self.resettime > 0.01:
                self.SetThink(self.ResetPositionThink, gpGlobals.curtime + self.resettime)
            
        def OnUnitDetach(self, unit, dmginfo=None):
            ''' Notifies the item the unit detaches itself from the item.
                The item is responsible for doing the detaching work.
            '''
            self.Detach()

        def ItemTouch(self, other):
            ownernumber = other.GetOwnerNumber()

            if self.IsMarkedForDeletion():
                return
                
            if not other.IsUnit():
                return
                
            if self.pickupfilter and not self.pickupfilter.PassesFilter(self, other):
                return
                
            self.AttachTo(other)
            self.onpickup.Set(ownernumber, self, self)
            
        def ShouldGib(self, info):
            return True
        
        def Event_Gibbed(self, info):
            gibbed = self.CorpseGib(info)

            if gibbed:
                # don't remove players!
                UTIL_Remove(self)
                self.SetThink(None) # We're going away, so don't think anymore.
            else:
                self.CorpseFade()

            return gibbed
            
        def CorpseGib(self, info):
            if not self.gibmodels:
                return False
            vecForce = Vector(0, 0, 0)
            fadetime = 3.0
            for i in range(0, 3):
                #gib = CreateRagGib( random.sample(self.gibmodels, 1)[0], self.GetAbsOrigin(), self.GetAbsAngles(), vecForce, fadetime, False)
                
                pChunk = CreateEntityByName("gib")
                pChunk.Spawn( random.sample(self.gibmodels, 1)[0], random.uniform( 0.5, 1.0 ) )
                pChunk.SetBloodColor( DONT_BLEED )

                pChunk.SetAbsOrigin( self.GetAbsOrigin() )
                pChunk.SetAbsAngles( self.GetAbsAngles() )
                
                pChunk.SetSolidFlags( FSOLID_NOT_SOLID )
                #pChunk.SetSolid( SOLID_BBOX )
                pChunk.SetGravity( UTIL_ScaleForGravity( 400 ) )

                pChunk.SetOwnerEntity( self )
                
                pChunk.SetCollisionGroup( COLLISION_GROUP_DEBRIS )
                
            return True
            
        def Detach(self, nodropoutput=False):
            ''' Detaches the item from the unit it is currently carried by. 
                This removes the item from the unit's item list.
            '''
            unit = self.carriedbyunit
            if not unit:
                return
                
            h = self.GetHandle()
            try:
                unit.items.remove(h)
            except ValueError:
                PrintWarning('Item carried by unit, but not in item list of unit!\n')
                
            self.StopFollowingEntity()
            self.SetOwnerNumber(0)
            self.carriedbyunit = None
            self.SetupForPickup()
            
            if not nodropoutput:
                self.ondrop.Set(unit.GetOwnerNumber(), self, self)
                
        def AttachTo(self, unit):
            ''' Attaches the item to an unit. 
                This adds the item to the unit's item list.
            '''
            self.Detach()
            if not unit:
                return
                
            h = self.GetHandle()
            self.SetupForCarrying()
            self.FollowEntity(unit, self.bonemerge)
            self.SetOwnerNumber(unit.GetOwnerNumber())
            if h not in unit.items:
                unit.items.append(h)
            self.carriedbyunit = unit.GetHandle()
            
        @input(inputname='EnableForPickup', helpstring='Enable for pickup')
        def InputEnableForPickup(self, inputdata):
            if self.enabledforpickup:
                return
            
            self.enabledforpickup = True
            
            if not self.carriedbyunit:
                self.ActivateForPickup()
                
        @input(inputname='EnableForPickup', helpstring='Enable for pickup')
        def InputDisableForPickup(self, inputdata):
            if not self.enabledforpickup:
                return
            
            self.enabledforpickup = False
            
        @input(inputname='Kill', helpstring='Kill item entity')
        def InputKill(self, data):
            UTIL_Remove(self)

        @input(inputname='SetPickupFilter', helpstring='Sets/changes the pickup filter entity', fieldtype=fieldtypes.FIELD_STRING)
        def InputSetPickupFilter(self, data):
            self.pickupfiltername = data.value.String()
            self.FindFilterEntity()
            
        @input(inputname='ResetPosition', helpstring='Resets position of item now.')
        def InputResetPosition(self, data):
            self.ResetPosition()
            
        @input(inputname='SetResetPosition', helpstring='Updates the reset position. Pass the name of the target reset position or leave empty for using the current item position.', fieldtype=fieldtypes.FIELD_STRING)
        def InputSetResetPosition(self, data):
            ''' Updates the reset position of the entity.
                This can either be a target entity or the current item position. '''
            targetname = data.value.String()
            if not targetname:
                self.resetposition = self.GetAbsOrigin()
            else:
                targetent = entlist.FindEntityByName(None, targetname)
                if not targetent:
                    PrintWarning('#%d: Item "%s" could not find target reset entity %s\n' % (self.entindex(), self.GetEntityName(), targetname))
                    return
                self.resetposition = targetent.GetAbsOrigin()
                
        @input(inputname='SetResetTime', helpstring='Sets the reset time. Below 1 is considered no reset to start position.', fieldtype=fieldtypes.FIELD_INTEGER)
        def InputSetResetTime(self, data):
            self.resettime = data.value.Int()
                
    # Fields
    worldmodel = ModelField(value='')
    carrymodel = ModelField(value='models/pg_props/pg_obj/pg_backpack_scrap.mdl', keyname='carrymodel', displayname='Carry Model', helpstring='Model used by unit when carrying the item.')
    enabledforpickup = BooleanField(value=True, keyname='enableforpickup', displayname='Enabled', helpstring='Whether this item can be picked up by an unit.')
    afterdroppickupdelay = FloatField(value=0.0, keyname='afterdroppickupdelay', displayname='Pickup Delay', helpstring='Time it takes before the item is pickupable after dropping')
    bonemerge = BooleanField(value=True, keyname='bonemerge', displayname='Bone Merge', helpstring='Perform bone merge on unit carrying this item.')
    pickupfiltername = FilterField(value='', keyname='pickupfilter', displayname='Pickup Filter', helpstring='Filter entity name for restricting pickup by units (e.g. enemies)')
    resettime = FloatField(value=0.0, keyname='resettime', displayname='Reset Time', helpstring='Time after which the item is reset to the start position when not carried')

    gibmodels = [
    ]
    
    # Variables
    carriedbyunit = None
    pickupfilter = None
    