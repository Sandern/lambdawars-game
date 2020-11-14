'''
Sander's TODO list:
    - Change player modifications to player controlled unit modifications
'''

from srcbase import *
from vmath import *
from entities import entity, IMouse
from gamerules import GameRules

from core.units import CreateUnitFancy, unitpopulationcount

from zm.shared import *
from zm.gamerules.zm import ZMResources

if isserver:
    from entities import CBaseAnimating as BaseAnimating, CPointEntity, CBaseTrigger, gEntList, CreateEntityByName, DispatchSpawn, CBaseTrigger
    from utils import UTIL_PrecacheOther, UTIL_ClientPrintAll, HUD_PRINTTALK, UTIL_Remove, ClientPrint, UTIL_SetSize
    from gameinterface import CSingleUserRecipientFilter
else:
    from entities import C_BaseAnimating as BaseAnimating, C_BasePlayer
    
from fields import IntegerField, StringField, BooleanField, input, OutputField

from zm.hud import UpdateBuildMenu

if isserver:
    @entity('func_win')
    class CZombieMaster_HumanWin(CPointEntity):
        def Spawn(self):
            self.SetSolid( SOLID_NONE )
            self.AddEffects( EF_NODRAW )

            self.SetMoveType( MOVETYPE_NONE )

        #-----------------------------------------------------------------------------
        # Purpose: Input handler for making the round end.
        #-----------------------------------------------------------------------------
        @input(inputname='Win')
        def InputHumanWin(self, inputdata):
        #LAWYER:  We need to stick loads of bits and pieces here to make the players know they won
        #Perhaps add a sound in here?
            for i in range(1, gpGlobals.maxClients+1):
                plr = UTIL_PlayerByIndex( i )

                if plr and plr.GetOwnerNumber() == ON_SURVIVOR:
                        plr.IncrementFragCount(HUMAN_WIN_SCORE) #LAWYER:  50 points for surviving a round
                        #LAWYER:  Add resources and score

            UTIL_ClientPrintAll(HUD_PRINTTALK, "The living have prevailed!\n")

            GameRules().TeamVictorious(True, "objective")

            GameRules().FinishingRound()

        #-----------------------------------------------------------------------------
        # Purpose: Input handler for making the round end, but with the ZM winning
        #-----------------------------------------------------------------------------
        @input(inputname='Lose')
        def InputHumanLose(self, inputdata):
            for i in range(1, gpGlobals.maxClients+1):
                plr = UTIL_PlayerByIndex( i )

                if plr:
                    if plr.GetOwnerNumber() == ON_ZOMBIEMASTER:
                        plr.IncrementFragCount(HUMAN_LOSE_SCORE) #LAWYER:  50 points for surviving a round
                        break

            UTIL_ClientPrintAll( HUD_PRINTTALK, "The living have failed their objectives!\n" )	

            GameRules().TeamVictorious( False, "objective" )

            GameRules().FinishingRound()

@entity('info_zombiespawn', networked=True)
class ZombieSpawn(BaseAnimating, IMouse):
    if isserver:
        active = BooleanField(keyname='Active')
        zombieflags = IntegerField(value=0, keyname='zombieflags')
        rallyname = StringField(keyname='rallyname')
        nodename = StringField(keyname='nodename')
        
        queue_size = 10

        def __init__(self):
            BaseAnimating.__init__(self)
            IMouse.__init__(self)  
        
            self.spawnqueue = []
            self.nodepoints = []
            
        def GetIMouse(self):
            return self
            
        def Precache(self):
            self.PrecacheModel( ENTITY_MODEL_Z )

        def Spawn(self):
            self.Precache()

            self.SetModel(ENTITY_MODEL_Z)
            self.SetSolid(SOLID_BBOX)
            UTIL_SetSize(self, -Vector(20,20,20), Vector(20,20,20))
            self.SetMoveType(MOVETYPE_FLY)

            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_TRIGGER|FSOLID_NOT_SOLID)

            if not self.active:
                self.AddEffects(EF_NODRAW)
            else:
                self.RemoveEffects(EF_NODRAW)

             #rallyPoint = dynamic_cast<CZombieRallyPoint *>(CreateEntityByName("info_rallypoint" ))
             #rallyPoint.SetOwnerEntity(this)
             #rallyPoint.Spawn()
             #rallyPoint.SetSpawnParent( entindex() )

            #TGB: see if we have a map-set rallypoint
            pRallyEnt = gEntList.FindEntityByName(None, self.rallyname, self)
            self.rallypoint = pRallyEnt
            if self.rallypoint:
                DevMsg(1, "ZSpawn: Map-set rally!\n")
                rallyPoint.SetOwnerEntity(self)
                rallyPoint.SetSpawnParent(selfentindex())
                rallyPoint.ActivateRallyPoint()
            else:
                DevMsg(1, "ZSpawn: No map-set rally!\n")
                #create a dummy
                rallyPoint = CreateEntityByName("info_rallypoint" )
                rallyPoint.SetOwnerEntity(self)
                rallyPoint.Spawn()
                rallyPoint.SetSpawnParent(self.entindex())

            #LAWYER:  Spawn nodes!  Shamelessly ripped off of TGB
            
        #	DevMsg("ZSP: I'm a spawn and nodename is %s\n", nodeName)

            self.nodepoints = []

            #TGB: previously, we built a list of spawn nodes here, but at this phase of post-mapload 
            #  not all of them would have spawned yet sometimes, it seems, so now we do this the first time
            #  we actually need a spawn location

            self.didspawnsetup = False #clunky

            self.SetThink(self.SpawnThink)

            self.spawning = False

        def OnClickLeftPressed(self, player):
            self.ShowBuildMenu(True)
            
        @input(inputname='Toggle')
        def InputToggle(self, inputData):
            # Toggle our active state
            if self.active:
                self.active = False
                self.AddEffects(EF_NODRAW)
            else:
                self.active = True
                self.RemoveEffects(EF_NODRAW)
                
        @input(inputname='Hide')
        def InputHide(self, inputData):
            self.active = False
            self.AddSolidFlags(FSOLID_NOT_SOLID)
            self.AddEffects(EF_NODRAW)
            
        @input(inputname='Unhide')
        def InputUnhide(self, inputData):
            self.active = True
            self.RemoveEffects(EF_NODRAW)
        
        def Trigger(self, iEntIndex):
            #Msg("Pressed...\n") #LAWYER:  We need to feed into self some actual, useful information.
            #m_OnPressed.FireOutput(pActivator, self)
            pass

        #--------------------------------------------------------------
        # TGB: spawns a zombie from self zombiespawn, WILL DEDUCT RESOURCES
        #--------------------------------------------------------------
        def CreateUnit(self, type):
            if self.active == False: #LAWYER:  No spawning from inactive spots
                return False

            '''
            pZM = GameRules().zmplayer
            if not pZM:
                return False #makes no sense for zombiespawns to spawn things without a zm anyway

            cost = ZombieSpawn.GetCostForType(type)

            if resources[pZM.GetOwnerNumber()][RESOURCE_ZOMBIEPOOL] - cost.resources < 0:
                ClientPrint(pZM, HUD_PRINTTALK, "Failed to spawn zombie: not enough resources!\n")
                return False

            if (unitpopulationcount[pZM.GetOwnerNumber()] + cost.population) > zm_zombiemax.GetInt():
                ClientPrint(pZM, HUD_PRINTCENTER, "Failed to spawn zombie: population limit reached!\n")
                return False

            if type == TYPE_BANSHEE and ZombieSpawn.OverBansheeLimit():
                ClientPrint(pZM, HUD_PRINTCENTER, "Failed to spawn zombie: maximum number of banshees reached!\n")
                return False
            '''

            vSpawnPoint = self.GetAbsOrigin() #self.FindValidSpawnPoint()

            #point will be 0,0,0 if no spot was found, which means we should delay spawning
            if vSpawnPoint.IsZero():
                return False

            pZombie = self.SpawnZombie(type, vSpawnPoint, self.GetAbsAngles())

            #DevMsg("Attempted to create exp_ent\n")
            if pZombie:
                #finish up with specific stuff
                pZombie.SetOwnerEntity( self )
                pZombie.SetZombieSpawnID(entindex())

                #TGB: success, deduct sauce
                TakeResources(ON_ZOMBIEMASTER, (RESOURCE_ZOMBIEPOOL, cost.resources))

                return True

            return False

        #--------------------------------------------------------------
        # TGB: general static method for a proper zombie spawn
        #--------------------------------------------------------------
        @staticmethod
        def SpawnZombie(unitname, origin, angles):
            info = GetUnitInfo(unitname)
            #check whether the zombie fits within the limit
            #have to do self check here as well for non-traditional spawning like hidden spawns, as they use self function
            pZM = GameRules().zmplayer
            if not pZM or (unitpopulationcount[pZM.GetOwnerNumber()] + info.population) > zm_zombiemax.GetInt():
                ClientPrint(pZM, HUD_PRINTCENTER, "Failed to spawn zombie: population limit reached!\n")
                return None
            return CreateUnitFancy(unitname, origin, ON_ZOMBIEMASTER)
        

        def FindValidSpawnPoint(self):
            #TGB: before we begin, see if we set our nodes up yet
            if self.didspawnsetup == False:
                self.nodepoints = []

                pNodeEnt = gEntList.FindEntityByName( None, nodeName, self )
                if pNodeEnt:
                    node = pNodeEnt
                    while node != None:
                        self.nodepoints.append(node)

                        node = node.nodePoint

                self.didspawnsetup = True
                DevMsg("ZSpawn: %i spawnnodes found\n", len(self.nodepoints))

            vForward = Vector()
            vRight = Vector()
            vUp = Vector()
            AngleVectors(self.GetAbsAngles(), vForward, vRight, vUp)

            #LAWYER:  Check the spawn spot
            tr = trace_t()
            vSpawnPoint = Vector(0,0,0)
            
            #CZombieSpawnNode*	iterated
            #LAWYER:  Added lovin' for the nodes
            #TGB: reworked for random node selection

            untried_nodes = [] #we haven't tried these yet
            #copy over the nodes, so we can juggle them around safely
            untried_nodes = list(self.nodepoints)
            
            #TGB: try more often if mapper went through the trouble of adding shitloads of nodes.
            max_attempts = max(25, len(untried_nodes))

            # TODO: TGB: possible future avenue: spawning on nodegraph nodes as fallback, like L4D does [19-11-2008]
            for i in range(0, max_attempts):
                #index of the node we tried (if any) in untried_nodes (so we know which one to scrap if it's taken)
                node_idx = -1

                #do we still have proper nodes to try?
                if len(untried_nodes) > 0:
                    #TGB: self was a case where I didn't get lawyer-banana-logic, so just made it go away and rewrote it

                    #actually we don't have to do shit here, really, now that we cached our nodes
                    idx = random.randint(0, len(untried_nodes) - 1) #random is inclusive wrt max

                    if untried_nodes[idx]:
                        DevMsg("ZSpawn: picked node %i of %i\n", idx, len(self.nodepoints))
                        vSpawnPoint = untried_nodes[idx].GetAbsOrigin()

                        node_idx = idx

                #LAWYER:  End of nodes
                #also fallback if untried_nodes[idx] == None
                if node_idx == -1:
                    #self will randomly generate spawn points in the local area.
                    xDeviation = random.randint( -128, 128 )
                    yDeviation = random.randint( -128, 128 )

                    vSpawnPoint = self.GetAbsOrigin() + (vForward * 64) #Forward of the node a little
                    vSpawnPoint.x = vSpawnPoint.x + xDeviation
                    vSpawnPoint.y = vSpawnPoint.y + yDeviation

                UTIL_TraceHull( vSpawnPoint,
                                vSpawnPoint + Vector( 0, 0, 1 ),
                                hull.Mins('HULL_HUMAN'),
                                hull.Maxs('HULL_HUMAN'),
                                MASK_NPCSOLID,
                                None,
                                COLLISION_GROUP_NONE,
                                tr )

                if tr.fraction != 1.0:
                    #LAWYER:  The spawn is blocked!
                    
                    if node_idx != -1:
                        del untried_nodes[node_idx]

                    #TGB: zero spawnpoint, so that if self was our last attempt we won't return a bogus one
                    #	instead we return something that our caller can use to detect our failure.
                    vSpawnPoint.Init()
                    #continue
                else:
                    break

            return vSpawnPoint

        #--------------------------------------------------------------
        # TGB: returns True if the ZM can NOT spawn more banshees 
        #--------------------------------------------------------------
        @staticmethod
        def OverBansheeLimit():
            #if the bansheemax is inactive, we don't have to check further
            bmax = zm_banshee_limit.GetFloat()
            if bmax <= 0.0:
                return False

            #self is a clean way of getting the number of players
            survivors = GetGlobalTeam( 2 ) #ugly magic number
            if not survivors:
                return False

            playercount = survivors.GetNumPlayers()

            limit = ceil(bmax * playercount)
            current = gEntList.m_BansheeList.Count()

            #if new count is higher than the limit, disallow
            if limit < (current + 1):
                return True
            else:
                return False

        # Spawn the next zombie from the head of the queue
        def SpawnThink(self):
            if len(self.spawnqueue) <= 0:
                self.spawning = False
                return #stop thinking and spawning

            # if there are still units in the queue, we'll always want another think
            self.SetNextThink(gpGlobals.curtime + zm_spawndelay.GetFloat())

            unitname = self.spawnqueue[0] #head of the queue
            
            # check if we can spawn self unit now, or if we should delay
            # STODO
            #if current_type == TYPE_BANSHEE and ZombieSpawn.OverBansheeLimit():
            #    return #over the limit right now, maybe next think one will have died

            # same thing for any zombie type and the popcount
            info = GetUnitInfo(unitname)
            pZM = GameRules().zmplayer

            if not pZM: return

            if ((unitpopulationcount[pZM.GetOwnerNumber()] + info.population) > zm_zombiemax.GetInt() or
                resources[pZM.GetOwnerNumber()][RESOURCE_ZOMBIEPOOL] - cost.resources < 0):
            
                #TGB: in self case, jitter the think time a bit to avoid potential simultaneous spawning when room frees up
                self.SetNextThink(gpGlobals.curtime + zm_spawndelay.GetFloat() + random.uniform(0.1, 0.2))
                return

            # if we get here, we have room for self zombie
            self.CreateUnit(unitname)

            # remove it from the top of the queue
            self.spawnqueue.pop(0)

            self.UpdateBuildMenu(False)

        #--------------------------------------------------------------
        # TGB: add a zombie to the queue 
        #--------------------------------------------------------------
        def QueueUnit(self, unitname):
            if len(self.spawnqueue) >= self.queue_size:
                return False #queue full

            if self.CanSpawn(unitname) == False:
                return False

            self.spawnqueue.append(unitname) #insert adds to the tail of the queue

            if not self.spawning:
                self.StartSpawning()

            self.UpdateBuildMenu(False)
            return True

        #--------------------------------------------------------------
        # TGB: start spawning zombies from the queue, which will end automatically when it's empty 
        #--------------------------------------------------------------
        def StartSpawning(self):
            self.SetNextThink(gpGlobals.curtime + zm_spawndelay.GetFloat())
            self.spawning = True

        #Are we allowed to spawn a zombietype at a spawn?
        def CanSpawn(self, unitname):
            return True # STODO
            '''
            if self.zombieflags == 0:
                return True
            else:
                #TGB: set up list of what we can spawn
                allowed = [False]*TYPE_TOTAL

                iCalculation = self.zombieflags

                #Burnzombies
                if iCalculation - 16 >= 0:
                    iCalculation -= 16
                    allowed[TYPE_IMMOLATOR] = True
                
                #Dragzombies
                if iCalculation - 8 >= 0:
                    iCalculation -= 8
                    allowed[TYPE_DRIFTER] = True
                
                #Hulks
                if iCalculation - 4 >= 0:
                    iCalculation -= 4
                    allowed[TYPE_HULK] = True
                
                #Fasties
                if iCalculation - 2 >= 0:
                    iCalculation -= 2
                    allowed[TYPE_BANSHEE] = True
                
                #Shamblies
                if iCalculation - 1 >= 0:
                    iCalculation -= 1
                    allowed[TYPE_SHAMBLER] = True

                return allowed[type]
            '''
                
            return False

        # Grabs the pop and res costs for a given type
        costfortype = {
            TYPE_SHAMBLER : (lambda: zm_cost_shambler.GetInt(), zm_popcost_shambler.GetInt()),
            TYPE_BANSHEE : (lambda: zm_cost_banshee.GetInt(), zm_popcost_banshee.GetInt()),
            TYPE_HULK : (lambda: zm_cost_hulk.GetInt(), zm_popcost_hulk.GetInt()),
            TYPE_DRIFTER : (lambda: zm_cost_drifter.GetInt(), zm_popcost_drifter.GetInt()),
            TYPE_IMMOLATOR : (lambda: zm_cost_immolator.GetInt(), zm_popcost_immolator.GetInt()),
        }
        
        @staticmethod
        def GetCostForType(type):
            try:
                return ZombieSpawn.costfortype[type]
            except KeyError:
                return ZombieCost(0, 0)

        #--------------------------------------------------------------
        # TGB: helper for finding the type of an ent 
        #--------------------------------------------------------------
        @staticmethod
        def GetTypeCode(entname):
            '''
            if ( V_strcmp(entname, "npc_zombie") == 0  )
                return TYPE_SHAMBLER
            else if ( V_strcmp(entname, "npc_fastzombie") == 0 )
                return TYPE_BANSHEE
            else if ( V_strcmp(entname, "npc_poisonzombie") == 0 )
                return TYPE_HULK
            else if ( V_strcmp(entname, "npc_dragzombie") == 0 )
                return TYPE_DRIFTER
            else if ( V_strcmp(entname, "npc_burnzombie") == 0 )
                return TYPE_IMMOLATOR
            '''

            return TYPE_INVALID

        #--------------------------------------------------------------
        # TGB: open the buildmenu for self spawn 
        #--------------------------------------------------------------
        def ShowBuildMenu(self, state):
            self.showingmenu = state

            if state:
                self.UpdateBuildMenu(True) #True = always open menu if it was not open

        #--------------------------------------------------------------
        # TGB: send usermessage to spawn with queue info 
        #--------------------------------------------------------------
        def UpdateBuildMenu(self, force_open):
            #despite self check, we still need to send whether we want the message to server as menu-opening
            #because in a laggy situation the client may have closed the menu without us knowing
            if self.showingmenu == False:
                return

            zmplayer = GameRules().zmplayer
            if zmplayer:
                filter = CSingleUserRecipientFilter(zmplayer) # set recipient
                filter.MakeReliable()  # reliable transmission
                
                queueupdate = []
                for i in range(0, self.queue_size):
                    if i < len(self.spawnqueue):
                        queueupdate.append(self.spawnqueue[i])
                    else:
                        queueupdate.append(None)
                    
                UpdateBuildMenu(self.entindex(), force_open, queueupdate, filter=filter)

        #--------------------------------------------------------------
        # TGB: rip the last zombie out of the queue 
        #--------------------------------------------------------------
        def RemoveLast(self):
            pZM = GameRules().zmplayer
            if not pZM: return

            size = len(self.spawnqueue)
            if size > 0:
                del self.spawnqueue[size - 1]

                ClientPrint(pZM, HUD_PRINTTALK, "Removed zombie from spawn queue.\n")	

                self.UpdateBuildMenu(False) #non-opening update
            else:
                ClientPrint(pZM, HUD_PRINTTALK, "No zombie to remove from queue!\n")	

        #--------------------------------------------------------------
        # TGB: clear out the entire queu 
        #--------------------------------------------------------------
        def ClearQueue(self):
            self.spawnqueue.Purge()

            self.UpdateBuildMenu(False) #non-opening
    else:
        def ShouldDraw(self):
            player = C_BasePlayer.GetLocalPlayer()
            if not player or ZMResources().zmplayer != player:
                return False
            return super(ZombieSpawn, self).ShouldDraw()
            
        def Spawn(self):
            super(ZombieSpawn, self).Spawn()
            
            zombiemastervisible.append(self.GetHandle())
            
        def UpdateOnRemove(self):
            super(ZombieSpawn, self).UpdateOnRemove()
            
            try: zombiemastervisible.remove(self.GetHandle())
            except ValueError: pass # Already removed
        
@entity('info_spawnnode')
class ZombieSpawnNode(BaseAnimating):
    if isserver:
        nodePoint = None
        nodeName = StringField(keyname='nodename')
       
        def Precache(self):
            self.PrecacheModel('models/spawnnode.mdl')
            
        def Spawn(self):
            self.Precache()

            #for testing
            self.SetModel('models/spawnnode.mdl')
            self.SetSolid(SOLID_BBOX)
            UTIL_SetSize( self, -Vector(2,2,2), Vector(2,2,2) )
            self.SetMoveType(MOVETYPE_FLY)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_TRIGGER|FSOLID_NOT_SOLID)
            
            #LAWYER:  Spawn nodes!  Shamelessly ripped off of TGB
            
            ''' TGB: future generations: watch out with GetEntityName, linux didn't like it here
        #ifndef _LINUX
            DevMsg("ZSN: my name is %s and nodename is %s\n", GetEntityName(), nodeName)
        #endif
            '''
            pNodeEnt = gEntList.FindEntityByName(None, self.nodeName, self)
            if pNodeEnt:
                self.nodePoint = pNodeEnt
            '''if pNodeEnt and self.nodePoint:
                DevMsg("ZSpawn: Spawn node!\n")
            else:
                DevMsg("ZSpawn: No spawn node!\n")
            '''
    else:
        def ShouldDraw(self):
            player = C_BasePlayer.GetLocalPlayer()
            if not player or ZMResources().zmplayer != player:
                return False
            return super(ZombieSpawnNode, self).ShouldDraw()
            
        def Spawn(self):
            super(ZombieSpawnNode, self).Spawn()
            
            zombiemastervisible.append(self.GetHandle())
            
        def UpdateOnRemove(self):
            super(ZombieSpawnNode, self).UpdateOnRemove()
            
            try: zombiemastervisible.remove(self.GetHandle())
            except ValueError: pass # Already removed
            
@entity('info_rallypoint')
class ZombieRallyPoint(BaseAnimating):
    if isserver:
        active = False
        owner = 0
        
        def Precache(self):
            self.PrecacheModel('models/rallypoint.mdl')

        def Spawn(self):
            self.Precache()

            #for testing
            self.SetModel('models/rallypoint.mdl')
            self.SetSolid(SOLID_BBOX)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_TRIGGER|FSOLID_NOT_SOLID)
            UTIL_SetSize( self, -Vector(2,2,2), Vector(2,2,2) )
            self.SetMoveType(MOVETYPE_FLY)

            #TGB: init location. If we don't, map-set points won't have coords
            #user-set ones override these, so doesn't affect those
            self.veccoordinates = self.GetAbsOrigin()

        def GetCoordinates(self):
            return self.veccoordinates

        def SetCoordinates(self, vecNewRallyCoordinates):
            self.veccoordinates = Vector(vecNewRallyCoordinates)

            self.SetAbsOrigin(vecNewRallyCoordinates)

        def GetSpawnParent(self):
            return self.owner

        def SetSpawnParent(self, entindex):
            self.owner = entindex

        def ActivateRallyPoint(self):
            self.active = True

        def DeactivateRallyPoint(self):
            self.active = False
    else:
        def ShouldDraw(self):
            player = C_BasePlayer.GetLocalPlayer()
            if not player or ZMResources().zmplayer != player:
                return False
            return super(ZombieRallyPoint, self).ShouldDraw()
            
        def Spawn(self):
            super(ZombieRallyPoint, self).Spawn()
            
            zombiemastervisible.append(self.GetHandle())
            
        def UpdateOnRemove(self):
            super(ZombieRallyPoint, self).UpdateOnRemove()
            
            try: zombiemastervisible.remove(self.GetHandle())
            except ValueError: pass # Already removed
            
@entity('info_ambush_point', networked=True)
class ZombieAmbushPoint(BaseAnimating):
    def __init__(self):
        super(ZombieAmbushPoint, self).__init__()
        
        self.zombielisteners = []

    if isserver:
        def Precache(self):
            self.PrecacheModel("models/trap.mdl")

        def Spawn(self):
            self.startambush = False

            self.Precache()
            DevMsg("Spawned an ambush node\n")

            self.SetModel(TRAP_MODEL)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_TRIGGER|FSOLID_NOT_SOLID)
            self.SetSolid(SOLID_BBOX)
            UTIL_SetSize( self, -Vector(20,20,20), Vector(20,20,20) )

            #scale = zm_ambush_triggerrange.GetFloat() / 34.5f
            #self.SetModelWidthScale(scale)

            self.SetMoveType(MOVETYPE_FLY)

            self.SetThink(self.ScanThink)
            self.SetNextThink(gpGlobals.curtime + 0.5)

        def Ambush(self):
            #qck: Start the ambush, and die.
            self.startambush = True #TGB: self is used to kill off the entity in the next think
            
            plr = GameRules().zmplayer

            if plr:
                ClientPrint(plr, HUD_PRINTTALK, "Ambush in progress!\n")

            for pEntity in self.zombielisteners:
                if pEntity and pEntity.IsAlive():
                    pEntity.swarmambushpoint = True

            #return self.startambush
            return True

        #qck: Borrowed from manipulate trap system. 
        def ScanThink(self):
            #qck: Die if we've been used up.
            if self.startambush:
                #DevMsg("Ambushpoint: removing myself\n")
                #TGB: zombies will have been triggered and have unregistered themselves already
                UTIL_Remove(self)
                return
            
            #qck: Just poll our listeners and see if they're alive still. If so, fine. If not, remove them.
            self.zombielisteners = filter( lambda ent: ent and ent.IsAlive(), self.zombielisteners )

            #qck: If all of our zombies are dead, vanish
            if len(self.zombielisteners) == 0:
                UTIL_Remove(self)
                return

            #DevMsg("ZombieListeners: %i\n", self.zombielisteners.Count())
            pIterated = gEntList.FindEntityInSphere(None, self.GetAbsOrigin(), zm_ambush_triggerrange.GetInt())
            while pIterated:
                pPlayer = pIterated
                if pPlayer:
                    if pPlayer.GetOwnerNumber() == ON_SURVIVOR:
                        #TGB: a return here was preventing a new think from being scheduled, meaning we never got removed post-ambush
                        self.Ambush()

                        #TGB: give zombies some time to start moving to our position
                        self.SetNextThink(gpGlobals.curtime + 1.0)
                        
                pIterated = gEntList.FindEntityInSphere(pIterated, self.GetAbsOrigin(), zm_ambush_triggerrange.GetInt())
                
            self.SetNextThink( gpGlobals.curtime + 0.3 )

        def PlayerMoveAmbush(self, newPosition):
            self.SetAbsOrigin( newPosition )

        def PlayerDismantleAmbush(self):
            #qck: Let the zombies know we aren't in an ambush anymore without triggering the ambush. 
            for pAI in self.zombielisteners:
                if pAI and pAI.IsAlive():
                    pAI.isinambush = False
                    pAI.ambushpoint = None

            UTIL_Remove(self) 

        def AssignAmbushPoint(self, pAI):
            #qck: Add AI to the ambush point member list, and return a pointer to ourself.
            self.zombielisteners.append(pAI)
            return self

        def RemoveFromAmbush(self, pAI):
            self.zombielisteners.remove(pAI)

            if not self.zombielisteners:
                UTIL_Remove(self)
    else:
        def ShouldDraw(self):
            player = C_BasePlayer.GetLocalPlayer()
            if not player or ZMResources().zmplayer != player:
                return False
            return super(ZombieAmbushPoint, self).ShouldDraw()
            
        def Spawn(self):
            super(ZombieAmbushPoint, self).Spawn()
            
            zombiemastervisible.append(self.GetHandle())
            
        def UpdateOnRemove(self):
            super(ZombieAmbushPoint, self).UpdateOnRemove()
            
            try: zombiemastervisible.remove(self.GetHandle())
            except ValueError: pass # Already removed
            
if isserver:
    @entity('func_giveresources')
    class ZombieMasterGiveResources(CPointEntity):
        def Spawn(self):
            self.SetSolid(SOLID_NONE)
            self.AddEffects(EF_NODRAW)

            self.SetMoveType(MOVETYPE_NONE)

        #-----------------------------------------------------------------------------
        # Purpose: Give (or take, in the case of negative numbers) some resources to the ZM
        #-----------------------------------------------------------------------------
        @input(inputname='GiveResources')
        def InputGiveResources(self, inputdata):
            for i in range(1, gpGlobals.maxClients+1):
                plr = UTIL_PlayerByIndex(i)
                if plr:
                    if plr.IsZM():
                        #TGB: refactorified
                        newpool = plr.m_iZombiePool + inputdata.value.Int()
                        plr.m_iZombiePool = 0 if ( newpool < 0 ) else newpool #no negative resources
                        
    @entity('trigger_blockspotcreate')
    class TriggerBlockSpotCreate(CBaseTrigger):
        def Spawn(self):
            super(TriggerBlockSpotCreate, self).Spawn()

            self.InitTrigger()

            #SetThink( &CTriggerBlockSpotCreate::CountThink )
        #	SetNextThink( gpGlobals.curtime )
        
        '''
        #-----------------------------------------------------------------------------
        # Purpose: Counts the number of ents
        #-----------------------------------------------------------------------------
        def CountThink( void )
        
            SetNextThink( gpGlobals.curtime + 1.0f )

        #	if (self.active == False)
        #			return
            Vector vecMins = CollisionProp().OBBMins()
            Vector vecMaxs = CollisionProp().OBBMaxs()
            Warning("Mins - %f,%f,%f\n", vecMins.x, vecMins.y, vecMins.z)
            Warning("Maxs - %f,%f,%f\n", vecMaxs.x, vecMaxs.y, vecMaxs.z)

        '''
        
        def InputToggle(self, inputData):
            # Toggle our active state
            if self.active:
                self.active = False
            else:
                self.active = True
                
        def InputDisable(self, inputData):
            self.active = False

        def InputEnable(self, inputData):
            self.active = True
