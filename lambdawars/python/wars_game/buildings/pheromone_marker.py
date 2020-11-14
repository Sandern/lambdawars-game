import random
from srcbase import *
from vmath import *

from core.units import PrecacheUnit, CreateUnit
from fields import IntegerField, FloatField

from core.buildings import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from utils import UTIL_FindPosition, FindPositionInfo, trace_t, UTIL_TraceHull
from entities import entity
import ndebugoverlay

class PheromoneMarkerBase(object):
    def __init__(self):
        self.grublist = []
        self.freepositions = []
        
    def Precache(self):
        PrecacheUnit('unit_antliongrub_resource')

    def Spawn(self):
        self.grubmins = Vector(-12, -18, -3.5)
        self.grubmaxs = Vector(13.5, 28.5, 12)
        
        if self.generationtype != 0:
            if self.generationtype not in self.generationsettings.keys():
                PrintWarning("Invalid generation type for entity %s\n" % (self.GetClassname()))
                return
            self.frequency = self.generationsettings[self.generationtype][0]
            self.amount = self.generationsettings[self.generationtype][1]
            self.maxgrubs = self.generationsettings[self.generationtype][2]
        
        self.SetThink( self.PheromoneInitThink, gpGlobals.curtime+0.1, "PheromoneInitThink" )  
        
    def UpdateOnRemove(self):
        for grubentry in self.grublist:
            if not grubentry[0]:
                continue
            grubentry[0].Remove()
        self.grublist = []
        
    def Event_Killed(self, info):
        self.FreeGrubs()
                
    def FreeGrubs(self):
        for grubentry in self.grublist:
            if grubentry[0]:
                grubentry[0].SetOwnerEntity(None)
        self.grublist = []
                
    def GenerateFreePositions(self, n):
        radius = int((self.WorldAlignMaxs().x-self.WorldAlignMins().x)*0.8)
        info = FindPositionInfo(self.GetAbsOrigin()+Vector(0,0,32.0), self.grubmins, self.grubmaxs, startradius=radius)
        for i in range(0, n):
            info = UTIL_FindPosition(info)
            if not info.success:
                return  # Screwed
            #ndebugoverlay.Box(info.position, self.grubmins, self.grubmaxs, 255, 0, 0, 255, 2)
            self.freepositions.append(info.position)
            
    def TestPosition(self, position):
        tr = trace_t()
        UTIL_TraceHull( position,
                        position + Vector( 0, 0, 10 ),
                        self.grubmins,
                        self.grubmaxs,
                        MASK_NPCSOLID,
                        None, 
                        COLLISION_GROUP_NONE,
                        tr )
        if tr.fraction == 1.0:
            return True
        return False
            
    def GetPosition(self):
        # Check free position list
        if len(self.freepositions) == 0:
            self.GenerateFreePositions( int((self.maxgrubs - len(self.grublist) )*1.25) )
        if len(self.freepositions) == 0:    # Still 0? Screwed.
            return None 
        while len(self.freepositions) > 0:
            posidx = random.randint( 0, min(25, len(self.freepositions)-1) )      
            if self.TestPosition( self.freepositions[posidx] ) == False:
                # Remove and continue
                #ndebugoverlay.Box(self.freepositions[posidx], self.grubmins, self.grubmaxs, 255, 0, 0, 255, 2)
                #print 'Removing position, not free'
                del self.freepositions[posidx]      
                continue
            return posidx
        return None
       
    def GrubDied(self, grub):
        """ Called by the grub when it dies """ 
        for i, grubentry in enumerate(self.grublist):
            if grubentry[0] == grub:
                self.freepositions.append( grubentry[1] )
                del self.grublist[i]
                break
        
    def AddGrubs(self, n):
        n = round(n)
        for i in range(0, n):
            # Grab a random free position
            posidx = self.GetPosition()
            if posidx == None:
                return i    # Screwed
            
            # Spawn a grub and remove the free position
            angle = QAngle(0, 0, 0)
            angle.y = random.uniform(0, 360)
            grub = CreateUnit( 'unit_antliongrub_resource', self.freepositions[posidx], angle, self.GetOwnerNumber() )
            grub.SetOwnerEntity(self)
            self.grublist.append( (grub.GetHandle(), self.freepositions[posidx]) )
            del self.freepositions[posidx]
        return n
        
    def AddExistingGrub(self, grub):
        grub.SetOwnerEntity(self)
        posidx = self.GetPosition()
        if posidx == None:
            self.GenerateFreePositions(10)
            posidx = self.GetPosition()
        grub.SetAbsOrigin( self.freepositions[posidx] )
        grub.SetOwnerNumber( self.GetOwnerNumber() )
        self.grublist.append( (grub.GetHandle(), self.freepositions[posidx]) )
        del self.freepositions[posidx]      # Remove from the free list
        
    def GetFreeGrub(self, worker):
        best = None
        for grubentry in self.grublist:
            grub = grubentry[0]
            if not grub.assignedtoworker:
                dist = grub.GetAbsOrigin().DistTo(worker.GetAbsOrigin())
                if not best:
                    best = grub
                    bestdist = dist
                else:
                    if dist < bestdist:
                        best = grub
                        bestdist = dist
        return best
        
    def PheromoneInitThink(self):     
        self.GenerateFreePositions( int(self.maxgrubs*1.25) )

        self.AddGrubs(self.startgrubs)
            
        self.SetThink( self.PheromoneThink, gpGlobals.curtime+self.frequency, "PheromoneThink" )
        
    def PheromoneThink(self):
        self.grublist = [grub for grub in self.grublist if bool(grub)] # Just to be sure
        if len(self.grublist) < self.maxgrubs:
            n = min(self.maxgrubs-len(self.grublist), self.amount)
            added = self.AddGrubs(n)
            if added != n:
                # Give some time to free up positions. Something is blocking likely
                self.SetNextThink(gpGlobals.curtime + 5.0, 'PheromoneThink')   
                return
            
        self.SetNextThink(gpGlobals.curtime + self.frequency, 'PheromoneThink')    

    # Settings
    generationtype = IntegerField(value=2, keyname='generationtype', 
        displayname='Generation type',
        helpstring='Speed at which new grubs a generated.',
        choices=[
            (0, "Custom"),
            (1, "Low"),
            (2, "Normal"),
            (3, "High"),
        ]
    )
    generationsettings = {
        1 : (10.0, 1, 50),
        2 : (5.0, 1, 50),
        3 : (3.0, 1, 50),
        4 : (1.0, 1, 50)
    }
    
    startgrubs = IntegerField(value=10, keyname='startgrubs')
    frequency = FloatField(value=1.0, keyname='frequency')
    amount = IntegerField(value=1, keyname='amount')
    maxgrubs = IntegerField(value=50, keyname='maxgrubs') # Max grubs this point generates. Might still mean that existing grubs are added (harvesting)  

@entity('pheromone_marker',
        studio='models/props_hive/nest_lrg_flat.mdl')
class PheromoneMarker(BaseClass, PheromoneMarkerBase):
    def __init__(self):
        BaseClass.__init__(self)
        PheromoneMarkerBase.__init__(self)
        
    def Precache(self):    
        BaseClass.Precache(self)
        PheromoneMarkerBase.Precache(self)

    def Spawn(self):
        self.SetUnitType('pheromone_marker')
    
        BaseClass.Spawn(self)
        PheromoneMarkerBase.Spawn(self)

        self.takedamage = DAMAGE_NO
        
    def UpdateOnRemove(self):
        BaseClass.UpdateOnRemove(self)
        PheromoneMarkerBase.UpdateOnRemove(self)
        
    def Event_Killed(self, info):
        BaseClass.Event_Killed(self, info)
        PheromoneMarkerBase.Event_Killed(self, info)
        
    fowflags = 0
    startgrubs = 20
    frequency = 0.1
    amount = 1
    maxgrubs = 50  
        
# Register unit
class PheromoneMarkerInfo(WarsBuildingInfo):
    name        = "pheromone_marker"
    cls_name    = "pheromone_marker"
    image_name = "vgui/units/unit_shotgun.vmt"
    modelname = 'models/props_hive/nest_lrg_flat.mdl'
    displayname = "#PheromoneMarker_Name"
    description = "#PheromoneMarker_Description"

    