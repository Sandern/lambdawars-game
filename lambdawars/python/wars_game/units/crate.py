from srcbase import *
from vmath import Vector
from entities import entity, Activity
from core.units import UnitInfo, UnitBase as BaseClass, CreateUnitFancy, PrecacheUnit
from core.resources import GiveResources, MessageResourceIndicator
from wars_game.resources import ResRequisitionInfo
import random
import bisect
from gamerules import gamerules
from fields import BooleanField
from gameinterface import modelinfo

import ndebugoverlay

if isserver:
    from entities import CreateEntityByName, g_EventQueue, variant_t, DispatchSpawn
    from utils import UTIL_SetSize, UTIL_SetModel, UTIL_RemoveImmediate
    
# Small helper function for selecting units to some probability distribution
# http://rosettacode.org/wiki/Probabilistic_choice#Python
def probchoice(items, probs):
    '''\
    Splits the interval 0.0-1.0 in proportion to probs
    then finds where each random.random() choice lies
    '''

    prob_accumulator = 0
    accumulator = []
    for p in probs:
        prob_accumulator += p
        accumulator.append(prob_accumulator)
 
    while True:
        r = random.random()
        yield items[bisect.bisect(accumulator, r)]

@entity('crate', networked=True)
class UnitCrate(BaseClass):
    if isserver:
        def __init__(self):
            super().__init__()
            
            self.UseClientSideAnimation()
            
        def Precache(self):
            super().Precache()

            bomb = CreateEntityByName( "prop_physics" )
            bomb.KeyValue('model', 'models/props_c17/oildrum001_explosive.mdl')
            bomb.Precache()
            UTIL_RemoveImmediate(bomb)
            
            [PrecacheUnit(unit) for unit in self.units_weak]
            [PrecacheUnit(unit) for unit in self.units_med]
            [PrecacheUnit(unit) for unit in self.units_strong]
            [PrecacheUnit(unit) for unit in self.units_superstrong]
            
            self.PrecacheModel(self.unitinfo.explodemodelname)
            
            self.PrecacheScriptSound('Wood_Crate.Break')
            
        def Spawn(self):
            super().Spawn()
            
            self.SetOwnerNumber(0)
            
            self.takedamage = DAMAGE_NO
            self.SetCanBeSeen(False)

            self.SetSolidFlags(FSOLID_NOT_SOLID|FSOLID_TRIGGER)
            self.SetMoveType(MOVETYPE_NONE)
            self.SetCollisionGroup(COLLISION_GROUP_NONE)

            self.CollisionProp().UseTriggerBounds(True,1)
            UTIL_SetSize(self, self.unitinfo.mins, self.unitinfo.maxs)

            self.SetThink(self.ActivateCrateTouch, gpGlobals.curtime + 10.0)
    else:
        def OnNewModel(self):
            super().OnNewModel()
        
            self.ForceUseFastPath(False)

            #testorigin = self.WorldSpaceCenter() + self.customlightingoffset
            #ndebugoverlay.Box(testorigin, -Vector(16, 16, 16), Vector(16, 16, 16), 255, 0, 0, 255, 5.0)
            #print self.customlightingoffset
            
            if not self.playedconstructanim:
                self.playedconstructanim = True
                
                act = Activity(self.LookupActivity('ACT_CONSTRUCTION'))
                self.SetCycle(0.0)
                self.ResetSequence(self.SelectWeightedSequence(act))
            
            # For explode model: Play animation + set lighting offset
            model = modelinfo.GetModel(self.GetModelIndex())
            if hasattr(self.unitinfo, 'explodemodelname') and modelinfo.GetModelName(model) == self.unitinfo.explodemodelname:
            
                # Ugly code to fix the origin that does not work correctly
                mins, maxs = modelinfo.GetModelBounds(model)
                adjworldcenter = maxs.z - mins.z
                offsetorigin = self.GetAbsOrigin()
                offsetorigin.z += adjworldcenter
                self.customlightingoffset = offsetorigin + Vector(0, -128, 512.0)
            
                self.Blink(0)
                act = Activity(self.LookupActivity('ACT_EXPLODE'))
                self.SetCycle(0.0)
                self.ResetSequence(self.SelectWeightedSequence(act))
            else:
                offsetorigin = self.GetAbsOrigin() - self.WorldSpaceCenter()
                self.customlightingoffset = offsetorigin + Vector(0, 0, 64.0)
                
        '''def OnDataChanged(self, updatetype):
            super().OnDataChanged(updatetype)
            
            offsetorigin = self.GetAbsOrigin() - self.WorldSpaceCenter()
            self.customlightingoffset = offsetorigin + Vector(0, 0, 64.0)
            
            testorigin = self.WorldSpaceCenter() + self.customlightingoffset
            ndebugoverlay.Box(testorigin, -Vector(16, 16, 16), Vector(16, 16, 16), 255, 0, 0, 255, 5.0)
            print self.customlightingoffset'''
                
        def OnDeployed(self):
            act = Activity(self.LookupActivity('ACT_IDLE'))
            self.SetCycle(0.0)
            self.ResetSequence(self.SelectWeightedSequence(act))
            self.Blink(-1) # Blink infinitely
            
        #def OnDataUpdateCreated(self):
        #    super().OnDataUpdateCreated()
            
            
    def CreateRandomUnit(self, unitlist, owner):
        unittype = random.choice(unitlist)
        CreateUnitFancy(unittype, self.GetAbsOrigin(), owner_number=owner)
        
    def DoExplosion(self):
        bomb = CreateEntityByName( "env_explosion" ) 
        bomb.SetAbsOrigin(self.GetAbsOrigin())
        bomb.KeyValue( "iMagnitude", "120" )
        bomb.KeyValue( "DamageForce", "700" )
        bomb.KeyValue( "fireballsprite", "sprites/zerogxplode.spr" )
        bomb.KeyValue( "rendermode", "5" )
        DispatchSpawn( bomb )       
        bomb.Activate()    
        
        value = variant_t()
        g_EventQueue.AddEvent( bomb, "Explode", value, 0.0, None, None )
        g_EventQueue.AddEvent( bomb, "kill", value, 2.0, None, None )
        
    def SpawnExplosiveBarrel(self):
        bomb = CreateEntityByName( "prop_physics" )
        bomb.KeyValue('model', 'models/props_c17/oildrum001_explosive.mdl')
        bomb.SetAbsOrigin(self.GetAbsOrigin())
        bomb.AcceptInput('Wake', None, None, variant_t(), 0)
        DispatchSpawn( bomb )      
        bomb.Activate()
        
        bomb.Ignite(30.0, False)
        
    def ActivateCrateTouch(self):
        self.deployed = True
        self.SetTouch(self.CrateTouch)
        self.SetBodygroup(0, 1) # Remove parachute
        if self.lifetime:
            self.SetThink(self.BreakAndRemove, gpGlobals.curtime + self.lifetime)
        
    def CrateTouch(self, other):
        if not other or not other.IsUnit() or other.GetOwnerNumber() < 2:
            return
           
        # Disable touch
        self.SetTouch(None)
            
        options = self.unitinfo.options
        type = next(probchoice(options[0], options[1]))
        ownernumber = other.GetOwnerNumber()
          
        if type == 'explosion':
            self.DoExplosion()
        elif type == 'explosivebarrel':
            self.SpawnExplosiveBarrel()
        elif type == 'requisition':
            resourceamount = random.randint(30, 70)
            try:
                resourcetype = gamerules.GetMainResource()
            except:
                resourcetype = ResRequisitionInfo.name
            GiveResources(ownernumber, [(resourcetype, resourceamount)], firecollected=True)
            MessageResourceIndicator(ownernumber, self.GetAbsOrigin(), '+%d' % (resourceamount), resourcetype)
        elif type == 'unit_weak':
            self.CreateRandomUnit(self.units_weak, ownernumber)
        elif type == 'unit_med':
            self.CreateRandomUnit(self.units_med, ownernumber)
        elif type == 'unit_strong':
            self.CreateRandomUnit(self.units_strong, ownernumber)
        elif type == 'unit_superstrong':
            self.CreateRandomUnit(self.units_superstrong, ownernumber)
            
        self.BreakAndRemove()
            
    def BreakAndRemove(self):
        self.SetTouch(None)
        
        UTIL_SetModel(self, self.unitinfo.explodemodelname)
        UTIL_SetSize(self, self.unitinfo.mins, self.unitinfo.maxs)
        
        self.EmitSound('Wood_Crate.Break')
        
        self.SetThink(self.SUB_Remove, gpGlobals.curtime + 10.0)

    units_weak = ['unit_rebel_partisan', 'unit_antlion', 'unit_zombie']
    units_med = ['unit_combine', 'unit_rebel', 'unit_combine_sg', 'unit_rebel_sg', 'unit_combine_ar2', 'unit_rebel_ar2', 'unit_zombine']
    units_strong = ['unit_hunter', 'unit_vortigaunt', 'unit_poisonzombie', 'unit_combine_elite']
    units_superstrong = ['unit_strider']
    
    # Override to supress warning, don't care about eyeoffset
    customeyeoffset = Vector(0,0,0)
        
    playedconstructanim = False
    lifetime = None
    
    deployed = BooleanField(value=False, networked=True, clientchangecallback='OnDeployed')
        
class CrateInfo(UnitInfo):
    name = 'crate'
    cls_name = 'crate'
    displayname = "#Crate_Name"
    description = "#Crate_Description"
    modelname = 'models/pg_props/pg_obj/pg_wars_item_box01.mdl'
    explodemodelname = 'models/pg_props/pg_obj/pg_wars_item_box01_des.mdl'
    viewdistance = 256.0
    health = 1
    mins = -Vector(32, 32, 0)
    maxs = Vector(32, 32, 64)
    oncreatedroptofloor = False
    options = (['explosion', 'explosivebarrel', 'requisition', 'unit_weak', 'unit_med', 'unit_strong', 'unit_superstrong'], 
               [0.05, 0.1, 0.25, 0.3, 0.199, 0.1, 0.001])
    minimaphalfwide = 4
    minimaphalftall = 4
    minimaplayer = -1 # Draw earlier than units to avoid overlapping
    minimapicon_name = 'hud_minimap_crate'
    