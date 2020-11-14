from srcbase import *
from vmath import *
from core.buildings import UnitBaseBuilding as BaseClass, WarsBuildingInfo
from entities import entity, FOWFLAG_BUILDINGS_NEUTRAL_MASK, D_LI
from core.units import UnitBase, UnitInfo
from core.resources import GiveResources, MessageResourceIndicator
from wars_game.resources import ResScrapInfo
from core.signals import unitkilled, prelevelinit, startgame
from core.dispatch import receiver
from fields import IntegerField, PlayerField
from playermgr import dbplayers, relationships, OWNER_LAST
import random
from gamerules import GameRules

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_Remove, UTIL_ScaleForGravity, UTIL_SetSize, trace_t, UTIL_TraceLine, UTIL_PrecacheOther
else:
    from entities import C_HL2WarsPlayer
    
@entity('scrap_marker', networked=True)
class ScrapMarker(BaseClass):
    """ Scrap marker. Contains scrap. """
    def __init__(self):
        super().__init__()
        
        self.salvagingworkers = set()

        if isserver:
            startgame.connect(self.OnStartGame)

    if isserver:
        def OnStartGame(self, gamerules, **kwargs):
            # spawn_constraint not set or gameplayers empty (started in another way then the lobby)
            if self.spawn_constraint < OWNER_LAST or not gamerules.gameplayers:
                return

            for data in gamerules.gameplayers:
                owner = data.get('ownernumber', None)
                if not owner or owner != self.spawn_constraint:
                    continue

                # Found the owner. Bug out.
                return

            # Did not find the owner in the game players.
            # Spawn constraint player should spawn for this scrap marker to appear
            # Remove the scrap pile
            self.SetThink(self.Remove, gpGlobals.curtime)

        def Spawn(self):
            if self.unitinfo == self.unitinfofallback:
                self.SetUnitType('scrap_marker')
        
            super().Spawn()
            
            self.SetCanBeSeen(False)
            
            self.scrap = self.totalscrap

            self.takedamage = DAMAGE_NO

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            startgame.disconnect(self.OnStartGame)
            
        def GetScrap(self, value=1):
            """ Returns a new scrap entity containing a max of the specified value.

                Kwargs:
                    value (int): Desired scrap to get
            """
            if not self.scrap:
                return None
            value = min(self.scrap, value) if self.scrap != -1 else value
            scrap = CreateEntityByName('scrap')
            scrap.value = value
            DispatchSpawn(scrap)
            if self.scrap != -1:
                self.scrap -= value
                if not self.scrap:
                    self.SetThink(self.SUB_Remove, gpGlobals.curtime)
            return scrap
        
    # Show a custom panel when this is the only selected building    
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            from wars_game.hud import HudBuildScrap
            self.unitpanelclass = HudBuildScrap
            
        # Hide health bar
        def ShowBars(self):
            pass
                
                
    fowflags = FOWFLAG_BUILDINGS_NEUTRAL_MASK
    scrap = IntegerField(networked=True)
    totalscrap = IntegerField(value=4500, networked=True)
    spawn_constraint = PlayerField(value=0, keyname='SpawnConstraint',  helpstring='Scrap marker is removed from map if given player does not play. Neutral means it always stays')
    
    big_scrap_models = [
        "models/pg_props/pg_buildings/pg_scrap_pile.mdl",
        "models/pg_props/pg_buildings/pg_scrap_pile02.mdl",
    ]

    medium_scrap_models = [
        "models/props_c17/FurnitureBathtub001a.mdl",
        "models/props_c17/FurnitureCouch001a.mdl",
        "models/props_c17/substation_circuitbreaker01a.mdl",
        "models/props_c17/substation_transformer01d.mdl",
        "models/props_c17/TrapPropeller_Engine.mdl",
        "models/props_canal/boat002b.mdl",
        "models/props_combine/Cell_01_pod_cheap.mdl",
        "models/props_combine/headcrabcannister01b.mdl",
        "models/props_combine/plazafallingmonitor.mdl",
        "models/props_wasteland/laundry_dryer001.mdl",
        "models/props_wasteland/laundry_dryer002.mdl",
        "models/props_wasteland/prison_bedframe001a.mdl",
        "models/props_c17/oildrum001.mdl",
    ]

    small_scrap_models = [
        "models/items/item_item_crate.mdl",
        "models/props_c17/canister01a.mdl",
        "models/props_c17/canister02a.mdl",
        "models/props_c17/canister_propane01a.mdl",
        "models/props_c17/metalPot001a.mdl",
        "models/props_c17/pulleywheels_large01.mdl",
        "models/props_interiors/SinkKitchen01a.mdl",
        "models/props_junk/gascan001a.mdl",
        "models/props_junk/MetalBucket01a.mdl",
        "models/props_junk/PlasticCrate01a.mdl",
        "models/props_junk/PropaneCanister001a.mdl",
        "models/props_junk/MetalBucket02a.mdl",
        "models/props_junk/TrafficCone001a.mdl",
        "models/props_junk/bicycle01a.mdl",
        "models/props_lab/monitor01a.mdl",
        "models/props_lab/monitor02.mdl",
        "models/props_wasteland/controlroom_monitor001a.mdl",
    ]
    
@entity('scrap_marker_small')
class ScrapMarkerSmall(ScrapMarker):
    """ Scrap marker Small. Also contains scrap. """
    totalscrap = 900

class ScrapMarkerInfo(WarsBuildingInfo):
    name = "scrap_marker"
    cls_name = "scrap_marker"
    image_name = "vgui/units/unit_shotgun.vmt"
    modellist = ScrapMarker.big_scrap_models
    displayname = "#ScrapMarker_Name"
    description = "#ScrapMarker_Description"
    minimaphalfwide = 4
    minimaphalftall = 4
    minimaplayer = -1 # Draw earlier than units to avoid overlapping
    minimapicon_name = 'hud_minimap_scrap'
    maxworkers = IntegerField(value=5, helpstring='Maximum number of workers which can be salvaging at the same time from this scrap marker')
    
class ScrapMarkerSmallInfo(ScrapMarkerInfo):
    name = "scrap_marker_small"
    cls_name = "scrap_marker_small"
    image_name = "vgui/units/unit_shotgun.vmt"
    modellist = ['models/pg_props/pg_buildings/pg_scrap_pile_small.mdl']
    displayname = "#ScrapMarker_Name"
    description = "#ScrapMarker_Description"
    maxworkers = 2


class ScrapEntityInfo(UnitInfo):
    name = "scrap"
    cls_name = "scrap"
    minimaphalfwide = 0
    minimaphalftall = 0
    sai_hint = set([])
    population = 0


@entity('scrap', networked=True)
class Scrap(UnitBase):
    __scrap_pickup_sounds = {
        'combine': 'combine_scrap_pickup',
        'rebels': 'rebels_scrap_pickup',
    }

    def GetIMouse(self):
        """ Returns if this entity has a mouse interface.
            By default units have this, but return None to prevent this.
        """
        return None
        
    def IsSelectableByPlayer(self, player, target_selection):
        return False
        
    def CanBePickedUp(self, owner):
        return dbplayers[owner].faction in ['rebels', 'combine'] and relationships[(self.GetOwnerNumber(), owner)] == D_LI
        
    def ShouldDraw(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        return player is not None and self.CanBePickedUp(player.GetOwnerNumber())
        
    # Don't show health bar or any bars for scrap
    def ShowBars(self):
        pass

    if isserver:
        def Precache(self):
            self.PrecacheModel(self.modelname)
            self.PrecacheModel(self.itemmodelname)
            
            super().Precache()
            
            for gibmodel in self.gibmodels:
                self.PrecacheModel(gibmodel)

            for sound_script in set(self.__scrap_pickup_sounds.values()):
                self.PrecacheScriptSound(sound_script)
            
        def Spawn(self):
            self.SetUnitType('scrap')
            self.Precache()
            self.SetModel(self.modelname)
            super().Spawn()
            self.SetCanBeSeen(False)
            
        def InitForPickup(self):
            self.SetModel(self.itemmodelname)
            
            #self.SetSolid(SOLID_VPHYSICS)
            self.SetSolidFlags(FSOLID_NOT_SOLID|FSOLID_TRIGGER)
            #self.SetMoveType(MOVETYPE_VPHYSICS)
            self.CollisionProp().UseTriggerBounds(True,1)
            
            #self.VPhysicsInitNormal(SOLID_VPHYSICS, FSOLID_NOT_STANDABLE, False)
            
            mins = -Vector(24, 24, 0)
            maxs = Vector(24, 24, 48)
            
            UTIL_SetSize(self, mins, maxs)
            
            origin = self.GetAbsOrigin()
            tr = trace_t()
            UTIL_TraceLine(origin, origin - Vector(0, 0, 4096.0), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr)
            self.SetAbsOrigin(tr.endpos)
            
            #self.SetThink(self.ActivateForPickup, gpGlobals.curtime + 2.5)
            self.ActivateForPickup()
            
        def ActivateForPickup(self):
            self.SetTouch(self.ScrapTouch)
            self.enableunitblink = True
            # Remove after 30 seconds if still not picked up 
            self.SetThink(self.SUB_Remove, gpGlobals.curtime + 30.0)
            
        def ScrapTouch(self, other):
            if not other.IsUnit():
                return # Filter things like projectiles
            owner = other.GetOwnerNumber()
            if not self.CanBePickedUp(owner):
                return 
                
            GiveResources(owner, [(ResScrapInfo, self.value)], firecollected=True)
            MessageResourceIndicator(owner, self.GetAbsOrigin(), '+%d' % self.value, ResScrapInfo.name)

            self.EmitSound(self.__scrap_pickup_sounds.get(dbplayers[owner].faction, 'rebels_scrap_pickup'))
        
            self.Remove()
            
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

        def AttachTo(self, unit):
            if unit:
                self.FollowEntity(unit, True)
                self.SetOwnerNumber(unit.GetOwnerNumber())
                self.carriedbyunit = unit.GetHandle()
            else:
                self.StopFollowingEntity()
                self.SetOwnerNumber(0)
                self.carriedbyunit = None

        def AddResourcesAndRemove(self, ownernumber):
            MessageResourceIndicator(self.GetOwnerEntity().GetOwnerNumber(), self.GetAbsOrigin(), '+%d' % (self.value), ResScrapInfo.name)
            GiveResources(ownernumber, [(ResScrapInfo, self.value)], firecollected=True)
            self.Remove()
            
        @classmethod
        def CreatePickupableScrap(cls, position, ownernumber, value=1):
            scrap = CreateEntityByName('scrap')
            scrap.SetAbsOrigin(position)
            scrap.SetOwnerNumber(ownernumber)
            scrap.value = value
            DispatchSpawn(scrap)
            scrap.InitForPickup()
        
    modelname = 'models/pg_props/pg_obj/pg_backpack_scrap.mdl'
    itemmodelname = 'models/pg_props/pg_obj/pg_item_scrap.mdl'
    
    gibmodels = [
        'models/pg_props/pg_obj/gibs/pg_backpack_scrap_gib1.mdl',
        'models/pg_props/pg_obj/gibs/pg_backpack_scrap_gib2.mdl',
        'models/pg_props/pg_obj/gibs/pg_backpack_scrap_gib3.mdl',
        'models/pg_props/pg_obj/gibs/pg_backpack_scrap_gib4.mdl',
        'models/pg_props/pg_obj/gibs/pg_backpack_scrap_gib5.mdl',
    ]
    carriedbyunit = None
    
    customeyeoffset = Vector(0,0,0)
    
    value = 5

if isserver:
    @receiver(prelevelinit)
    def OnLevelPreInit(**kwargs):
        UTIL_PrecacheOther('scrap')
    
    # Disabled: units no longer drop scrap
    @receiver(unitkilled)
    def OnUnitKilled(unit, dmginfo, **kwargs):
        supportsscrap = getattr(GameRules(), 'supportsscrap', True)
        if not supportsscrap:
            return
            
        unitinfo = unit.unitinfo
        if unitinfo.scrapdropchance <= 0 or random.random() < unitinfo.scrapdropchance:
            return
    
        attacker = dmginfo.GetAttacker()
        if not attacker or relationships[(attacker.GetOwnerNumber(), unit.GetOwnerNumber())] == D_LI:
            return
        
        ownernumber = attacker.GetOwnerNumber()
        
        Scrap.CreatePickupableScrap(unit.GetAbsOrigin(), ownernumber, value=5)
        