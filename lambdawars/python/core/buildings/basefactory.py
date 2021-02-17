from vmath import Vector, QAngle, VectorYawRotate, vec3_origin
from gameinterface import ConVar, FCVAR_CHEAT
from gamerules import GameRules
from core.units import CreateUnit, unitpopulationcount, GetMaxPopulation, unitlistpertype, NoSuchAbilityError
from core.abilities import PrecacheAbility
from core.notifications import (DoNotificationEntAbi, DoNotificationEnt,  GetNotifcationFilterForOwner,
                                NotificationAbilityCompleted, NotificationNotEnoughPopulation)
from .base import UnitBaseBuilding as BaseClass
from fields import EHandleField, VectorField, QAngleField, StringField, FloatField, ListField, BooleanField
from sound import CSoundEnvelopeController, CHAN_STATIC, ATTN_NORM
from gameinterface import CPASAttenuationFilter

from entities import CBaseAnimating, entity, MouseTraceData, SendProxyAlliesOnly, D_LI, D_HT
if isserver:
    from entities import gEntList
    from utils import UTIL_FindPosition, FindPositionInfo
    from core.signals import FireSignalRobust, productionstarted
else:
    from entities import C_BasePlayer
    from core.hud.buildings import HudBuildConstruction, HudBuildQueue, BaseHudSingleUnit
    from core.units.rallyline import FXRallyLine
    
if isserver:
    wars_build_instant = ConVar('wars_build_instant', '0', FCVAR_CHEAT)


class RallyPointModel(CBaseAnimating):
    def CreateRallyMark(self):
        pass

    
class QueuedAbility(object):
    def __init__(self, ability_name, ability):
        super().__init__()
        
        self.ability_name = ability_name
        self.abilities = [ability]
        self.didpopwarning = False
        
class UnitBaseFactoryShared(object):
    def __init__(self):
        super().__init__()
        
        self.buildqueue = []

    def OnBuildStateChanged(self):
        if not self.buildamount or self.buildamount[0] == 0:
            self.building = False
        else:
            self.building = True
            
    def GetBuildProgress(self):
        progress = 0
        if self.building and self.buildtime:
            if not self.onhold:
                progress = 1.0 - (self.nextcompletiontime - gpGlobals.curtime) / self.buildtime
            else:
                progress = (self.buildtime-self.onholdremainingtime) / self.buildtime
        return min(1.0, progress)

    if isserver:
        def Precache(self):
            super().Precache()
            
            self.PrecacheModel(self.rallypointmodelpath)
            
            for abi in self.unitinfo.abilities.values():
                PrecacheAbility(abi)
        
        def Spawn(self):
            super().Spawn()
            
            # Rotate
            yaw = self.GetAbsAngles().y
            VectorYawRotate(self.buildtarget, yaw, self.buildtarget)
            
            if self.rallypointname:
                rp = gEntList.FindEntityByName(None, self.rallypointname)
                if not rp:
                    PrintWarning('%s (at %s) has an invalid rally point!\n' % (self.GetClassname(), self.GetAbsOrigin()))
                else:
                    self.rallypointtarget = rp.GetAbsOrigin()
            elif self.rallypoint.IsValid():
                VectorYawRotate(self.rallypoint, yaw, self.rallypoint)
                
                # Find a position for the rallypoint. Initial position might be embedded in solid or not on the ground.
                rallypointabs = self.GetAbsOrigin() + self.rallypoint
                info = UTIL_FindPosition(FindPositionInfo(rallypointabs, -Vector(32, 32, 0), Vector(32, 32, 64), 0, 128))
                if info.success:
                    rallypointabs = info.position
                self.rallypointtarget = rallypointabs
            
            if self.spawnpointname:
                sp = gEntList.FindEntityByName(None, self.spawnpointname)
                if not sp:
                    PrintWarning('%s (at %s) has an invalid spawn point!\n' % (self.GetClassname(), self.GetAbsOrigin()))
                else:
                    self.buildtargetabs = sp.GetAbsOrigin()
            else:
                # Find abs position for build target
                # TODO: Use mins/maxs of the largest unit this building can produce?
                self.buildtargetabs = self.GetAbsOrigin() + self.buildtarget
                info = UTIL_FindPosition( FindPositionInfo(self.buildtargetabs, -Vector(32, 32, 0), Vector(32, 32, 64), 0, 128) )
                if info.success:
                    self.buildtargetabs = info.position
                    
        def ClearBuildQueue(self):
            if not self.buildqueue:
                return
                
            # Clear our build queue, ensuring Cancel is called on each ability
            # TODO: By default it refunds the resources. Decide on whether we want that.
            for entry in self.buildqueue:
                for ability in entry.abilities:
                    ability.Cancel()
            del self.buildqueue[:]
            del self.buildamount[:]
            self.building = False
            
        def UpdateOnRemove(self):
            self.ClearBuildQueue()
                
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
            
        def Event_Killed(self, info):
            self.ClearBuildQueue()
            
            super().Event_Killed(info)
        
        # Manage build queue  
        def AddAbility(self, ability):
            # Add to queue
            if len(self.buildqueue) > 0 and self.buildqueue[len(self.buildqueue)-1].ability_name == ability.info.name:
                self.buildqueue[len(self.buildqueue)-1].abilities.append(ability)
            else:
                self.buildqueue.append( QueuedAbility(ability.info.name, ability) )
            self.SetNextThink(gpGlobals.curtime)

        def CancelAbility(self, buildqueue_idx):
            # Remove ability from the queue entry and cancel it
            try:
                entry = self.buildqueue[buildqueue_idx]
                ability = entry.abilities.pop(0)
            except IndexError:
                return
            ability.Cancel()
            
            # Figure out if the entry is empty and then remove the entry if needed
            if len(entry.abilities) == 0:
                self.buildqueue.pop(buildqueue_idx)
                
                # If this is the current ability being produced, we must stop production and fire a signal
                if self.building and buildqueue_idx == 0:
                    self.building = False
            self.SetNextThink(gpGlobals.curtime)

        def CancelAll(self):
            while self.buildqueue:
                self.CancelAbility(0)

        def NotifyNotEnoughPopulation(self):
            if not self.buildqueue or self.buildqueue[0].didpopwarning:
                return

            if self.nextnotifypopulation > gpGlobals.curtime:
                return

            DoNotificationEnt(NotificationNotEnoughPopulation.name, self,
                              filter=GetNotifcationFilterForOwner(self.GetOwnerNumber()))

            # Don't spam the population warning
            self.buildqueue[0].didpopwarning = True
            self.nextnotifypopulation = gpGlobals.curtime + 10.0
            
        def GetTotalQueuedUnits(self):
            n = 0
            for bq in self.buildqueue:
                n += len(bq.abilities)
            return n
                
        # Produce unit
        def FindPositionForUnit(self, unitinfo):
            info = UTIL_FindPosition(FindPositionInfo(self.buildtargetabs, 
                        unitinfo.mins, unitinfo.maxs, 0, 400))
            if not info.success:
                return None
            return info.position
        
        def ProduceUnit(self, unit_name):
            try:
                unitinfo = self.unitinfo.GetAbilityInfo(unit_name, self.GetOwnerNumber())
            except NoSuchAbilityError:
                return True

            # Check population
            owner = self.GetOwnerNumber()
            if unitpopulationcount[owner]+unitinfo.population > GetMaxPopulation(owner):
                self.NotifyNotEnoughPopulation()
                return None    # Can't build the unit. Wait until we have more population room.

            unit_limit = getattr(getattr(GameRules(), 'info', object), 'unit_limits', {}).get(unitinfo.name, None)
            if unit_limit is not None:
                if len(unitlistpertype[owner][unitinfo.name]) >= unit_limit:
                    return None
                
            # Find a position for the unit around the build target
            spawnpos = self.FindPositionForUnit(unitinfo)
            if not spawnpos:
                DevMsg(3, 'Failed to find a position to spawn unit %s at factory %s (entindex: %d)\n' %
                       (unit_name, self.GetClassname(), self.entindex()))
                return None
                
            # Create
            unit = CreateUnit(unitinfo.name,
                              spawnpos,
                              self.GetAbsAngles()+self.buildangle,
                              self.GetOwnerNumber())
            if not unit:
                return None  # Failed, not factories fault.
                
            # Move unit to rally point
            if self.rallypointtarget and self.rallypointtarget != vec3_origin:
                data = MouseTraceData()
                if type(self.rallypointtarget) == Vector:
                    data.endpos = self.rallypointtarget
                    data.groundendpos = self.rallypointtarget
                else:
                    data.ent = self.rallypointtarget
                    data.endpos = self.rallypointtarget.GetAbsOrigin()
                    data.groundendpos = self.rallypointtarget.GetAbsOrigin()
                unit.ProcessOrder(data)
            return unit

        def BuildThink(self):
            """ Maintain factory queue """
            super().BuildThink()
            
            if not self.onhold:
                # Maintain build queue
                if self.building and self.buildqueue:
                    if self.nextcompletiontime < gpGlobals.curtime or wars_build_instant.GetBool():
                        result = self.buildqueue[0].abilities[0].ProduceAbility(self) 
                        if result:
                            # Notify produced
                            DoNotificationEntAbi(NotificationAbilityCompleted.name, self, self.buildqueue[0].abilities[0].name,
                                                 filter=GetNotifcationFilterForOwner(self.GetOwnerNumber()))
                        
                            # Update build queue     
                            self.buildqueue[0].abilities.pop(0)
                            if len(self.buildqueue[0].abilities) < 1:
                                self.buildqueue.pop(0)
                            else:
                                self.buildqueue[0].didpopwarning = False
                            
                            self.buildtime = 0.0
                            self.building = False
                else:
                    if len(self.buildqueue) > 0:
                        entry = self.buildqueue[0]
                        if entry.abilities:
                            self.nextcompletiontime = gpGlobals.curtime + entry.abilities[0].info.buildtime
                            self.buildtime = entry.abilities[0].info.buildtime
                            self.building = True
                            FireSignalRobust(productionstarted, building=self, info=entry.abilities[0].info)
                        else:
                            # Empty entry, shouldn't happen
                            self.buildqueue.pop(0)
                    
            # Build up queue types array
            for i in range(0, 5):
                if i < len(self.buildqueue):
                    self.buildtypes[i] = self.buildqueue[i].ability_name
                    self.buildamount[i] = len(self.buildqueue[i].abilities)
                else:
                    self.buildtypes[i] = None
                    self.buildamount[i] = 0

        def OnPlayerDefeated(self):
            if self.IsAlive():
                self.CancelAll()

    def Order(self, player):
        """ Called on right click when the unit is selected by the player """
        # Cannot set the rallypoint of another player
        if player.GetOwnerNumber() != self.GetOwnerNumber():
            return
            
        # Store the new rallypoint position
        data = player.GetMouseData()
        self.rallypointtarget = data.ent if data.ent and not data.ent.IsWorld() else data.endpos

        if isclient:
            self.CreateOrUpdateRallyPointEffects()

            
    if isclient:
        def OnRallypointTargetChanged(self):
            localplayer = C_BasePlayer.GetLocalPlayer()
            if not localplayer or localplayer.GetOwnerNumber() != self.GetOwnerNumber():
                return
            self.CreateOrUpdateRallyPointEffects()
    
        def CreateRallyPointEffects(self):
            if not self.rallylineenabled or not self.rallypointtarget:
                return
            
            if not self.rallypointmodel:
                self.rallypointmodel = RallyPointModel()
                self.rallypointmodel.InitializeAsClientEntity(self.rallypointmodelpath, False)
                self.rallypointmodel.CreateRallyMark()
                self.rallypointmodel.ForceClientSideAnimationOn()
                self.rallypointmodel.SetSequence(0)
        
        def DestroyRallyPointEffects(self):
            if self.rallypointmodel:
                self.rallypointmodel.Remove()
                self.rallypointmodel = None

            if self.rallyline:
                self.rallyline.Destroy()
                self.rallyline = None
                
        def CreateOrUpdateRallyPointEffects(self):
            if not self.rallylineenabled or not self.rallypointtarget:
                return
                
            self.CreateRallyPointEffects()
                
            # Update rallypoint model if we have one
            if type(self.rallypointtarget) == Vector:
                newpos = self.rallypointtarget
                if self.rallypointmodel:
                    self.rallypointmodel.SetAbsOrigin(newpos)
                    self.rallypointmodel.FollowEntity(None)
                    
                self.rallyline = FXRallyLine('vgui/rallyline', Vector(1, 1, 1), self.GetAbsOrigin(), newpos)
            else:
                targetent = self.rallypointtarget
                
                if self.rallypointmodel:
                    self.rallypointmodel.FollowEntity(targetent)
                    
                self.rallyline = FXRallyLine('vgui/rallyline', Vector(1, 1, 1), self.GetAbsOrigin(), vec3_origin, ent2=targetent)
                
        # Create/destroy rallypoint client model
        def OnSelected(self, player):
            """ When the player selects this building """    
            super().OnSelected(player)
            
            # Create effects and update them to the right positions
            self.CreateOrUpdateRallyPointEffects()
            
        def OnDeSelected(self, player):
            """ When the player deselects this building """
            super().OnDeSelected(player)
            self.DestroyRallyPointEffects()
            
        def UpdateOnRemove(self):
            """ Removes the rallypoint model if active """
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
            
            self.DestroyRallyPointEffects()
                
        # Progress bar on hover
        def ShouldShowProgressBar(self):
            localplayer = C_BasePlayer.GetLocalPlayer()
            if not localplayer or self.IRelationType(localplayer) != D_LI:
                return False
            if not localplayer.IsMouseHoveringEntity(self) and not self.ShouldAlwaysShowBars():
                return False
            return True # Either showing construction or production progress

        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            localplayer = C_BasePlayer.GetLocalPlayer()
            if localplayer and self.IRelationType(localplayer) == D_HT:
                self.unitpanelclass = BaseHudSingleUnit
            else:
                self.unitpanelclass = HudBuildQueue
        
    _onhold = BooleanField(value=False, networked=True, clientchangecallback='OnBuildStateChanged')
    @property
    def onhold(self):
        """ Indicates the build produce is on hold, even though units are queued. """
        return self._onhold
        
    @onhold.setter
    def onhold(self, v):
        if v == self._onhold:
            return
        self._onhold = v
        if v:
            self.onholdremainingtime = self.nextcompletiontime - gpGlobals.curtime
        else:
            self.nextcompletiontime = gpGlobals.curtime + self.onholdremainingtime
            
    @property
    def isproducing(self):
        """ Tests if units or abilities are currently being produced. """
        return self.building and not self._onhold
        
    # Settings
    buildtarget = VectorField(value=Vector(0,0,0), keyname='buildtarget', helpstring='Build target offset for units relative to building')
    buildangle = QAngleField(value=QAngle(0,0,0), keyname='buildangle')
    rallypoint = VectorField(invalidate=True, keyname='rallypoint')
    
    buildtargetabs = VectorField(invalidate=True, helpstring='Absolute build target for units')
    buildtypes = ListField(value=[None]*5, networked=True, sendproxy=SendProxyAlliesOnly())
    buildamount = ListField(value=[0]*5, networked=True, clientchangecallback='OnBuildStateChanged')
    nextcompletiontime = FloatField(value=0.0, networked=True, sendproxy=SendProxyAlliesOnly())
    buildtime = FloatField(value=0.0, networked=True, sendproxy=SendProxyAlliesOnly())
    rallypointtarget = EHandleField(value=None, networked=True, sendproxy=SendProxyAlliesOnly(),
                                    clientchangecallback='OnRallypointTargetChanged')
    onholdremainingtime = FloatField(value=0.0, networked=True, sendproxy=SendProxyAlliesOnly())

    # The following fields refer to target entities
    # If specified they override buildtarget/buildangle/rallypoint
    spawnpointname = StringField(value='', keyname='spawnpointname')
    rallypointname = StringField(value='', keyname='rallypointname')
    
    # Vars
    rallylineenabled = BooleanField(value=True)
    rallyline = None
    rallypointmodel = None
    rallypointmodelpath = 'models/props/spawn_flag.mdl'
    building = False
    nextnotifypopulation = 0.0

@entity('build_basefactory', networked=True)
class UnitBaseFactory(UnitBaseFactoryShared, BaseClass):
    def OnBuildStateChanged(self):
        super().OnBuildStateChanged()
        
        self.UpdateBuildingActivity()
        
        info = self.unitinfo
        # play work sound
        if info.sound_work:
            controller = CSoundEnvelopeController.GetController() #get sound controller
            if self.isproducing: # is building working?
                filter = CPASAttenuationFilter(self) # some filter thing
                self.sound_workloopentity = controller.SoundCreate(filter, self.entindex(), CHAN_STATIC, info.sound_work, ATTN_NORM) # crate sound entity
                if(self.sound_workloopentity): # if sound created play it
                    controller.Play(self.sound_workloopentity, 1.0, 100)
            elif self.sound_workloopentity: # if building is not working destroy it
                controller.SoundDestroy(self.sound_workloopentity)
                self.sound_workloopentity = None
                
        self.SetNextClientThink(gpGlobals.curtime) 
        
    def UpdateBuildingActivity(self):
        if self.building and not self.onhold:
            info = self.unitinfo
            if info.workactivity:
                self.ChangeToActivity(info.workactivity)
                curcycle = self.GetCycle()
                if self.buildtime == 0:
                    targetcycle = 1
                else:
                    targetcycle = self.nextcompletiontime/self.buildtime
                cyclerate = 0.1 * gpGlobals.frametime 
                curcycle += min(cyclerate, targetcycle - curcycle)
                self.SetCycle(curcycle)
                return
        super().UpdateBuildingActivity()

    if isserver:
        def Precache(self):
            super().Precache()
            
            info = self.unitinfo
            if info.sound_work:
                self.PrecacheScriptSound(info.sound_work)
            
        def AddAbility(self, ability):
            # Can't queue units yet when not constructed
            if self.constructionstate != self.BS_CONSTRUCTED:
                ability.Cancel()
                return 
            super().AddAbility(ability)

    def UpdateClientBuildProgress(self, building):
        if building.progressposeparm == None:
            return

        weight = self.GetBuildProgress()
            
        building.SetPoseParameter(building.progressposeparm, weight*100.0)
            
        self.SetNextClientThink(gpGlobals.curtime) 
        
    def OnNewModel(self):
        super().OnNewModel()
        
        self.progressposeparm = self.LookupPoseParameter("progress")
            
    def ClientThink(self):
        if self.constructionstate == self.BS_CONSTRUCTED and self.building:
            self.UpdateClientBuildProgress(self)
        else:
            super().ClientThink()
            
    def GetBuildProgress(self):
        if self.constructionstate == self.BS_UNDERCONSTRUCTION:
            return BaseClass.GetBuildProgress(self)
        return UnitBaseFactoryShared.GetBuildProgress(self)
            
    if isclient:
        # Called when this is the only selected unit
        # Allows the unit panel class to be changed
        def UpdateUnitPanelClass(self):
            localplayer = C_BasePlayer.GetLocalPlayer()
            if localplayer and self.IRelationType(localplayer) == D_HT:
                self.unitpanelclass = BaseHudSingleUnit
            elif self.constructionstate != self.BS_CONSTRUCTED:
                self.unitpanelclass = HudBuildConstruction
            else:
                self.unitpanelclass = HudBuildQueue

    progressposeparm = None
    sound_workloopentity = None