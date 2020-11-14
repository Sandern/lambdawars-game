from srcbase import *
from gameinterface import ConVarRef
from gamerules import TEAM_UNASSIGNED, TEAM_SPECTATOR
import random

if isserver:
    from gameinterface import (ConVar, FCVAR_NOTIFY, FCVAR_ARCHIVE, FCVAR_REPLICATED, FCVAR_CHEAT, FireGameEvent, GameEvent, 
            MapEntity_ParseAllEntities, IMapEntityFilter, GetMapEntityRef, GetMapEntityRefIteratorHead, GetMapEntityRefIteratorNext, engine)
    from utils import UTIL_ClientPrintAll, HUD_PRINTTALK, HUD_PRINTCENTER, HUD_PRINTCONSOLE, UTIL_Remove, UTIL_PlayerByIndex, INDEXENT, UTIL_EntityByIndex, ClientPrint
    from entities import gEntList, g_EventQueue, CreateEntityByName, CBaseEntity as BaseResourceClass, entity, FL_EDICT_ALWAYS
    from core.usermessages import CSingleUserRecipientFilter
else:
    from entities import C_BaseEntity as BaseResourceClass, entity
    
from core.gamerules import GamerulesInfo, WarsBaseGameRules
from core.units import CreateUnit
from core.resources import resources
from core.usermessages import usermessage
from fields import GenericField

from ..shared import *

fraglimit = ConVarRef('mp_fraglimit')
mp_timelimit = ConVarRef('mp_timelimit')

if isserver:
    # ZM convars
    roundlimit = ConVar( "zm_roundlimit","0", FCVAR_NOTIFY, "Sets the number of rounds before the server changes map\n" )

    #zm_bansheemax = ConVar("zm_bansheemax", "0.0", FCVAR_ARCHIVE|FCVAR_NOTIFY, 
    #    "Sets maximum number of banshees per player the ZM is allowed to have active at once. Set to 0 to remove the cap. Disabled by default since new population system was introduced that in practice includes a banshee limit.")
    zm_banshee_limit = ConVar("zm_banshee_limit", "-1", FCVAR_ARCHIVE|FCVAR_NOTIFY, 
        "Sets maximum number of banshees per survivor that the ZM is allowed to have active at once. Set to 0 or lower to remove the cap. Disabled by default since new population system was introduced that in practice includes a banshee limit.")

    zm_weaponreset = ConVar( "zm_weaponreset", "0",  FCVAR_NOTIFY, 
        "If set to 1, makes weapons be reset to their spawn after being dropped by (dead) players. Default and recommended off (= 0)." )
        
    zm_debugevents = ConVar("zm_debugevents", "0",  FCVAR_CHEAT, "Set to 1 to force zm game events to fire without a listener")
        
    # hl2mp
    mp_restartgame = ConVar( "mp_restartgame", "0", 0, "If non-zero, game will restart in the specified number of seconds" )

#TGB: HL2DM'S LIST, NOT OURS
s_PreserveEnts = [
    "ai_network",
    "ai_hint",
    "hl2mp_gamerules",
    "team_manager",
    "player_manager",
    "env_soundscape",
    "env_soundscape_proxy",
    "env_soundscape_triggerable",
    "env_sun",
    "env_wind",
    "env_fog_controller",
    "func_brush",
    "func_wall",
    "func_buyzone",
    "func_illusionary",
    "infodecal",
    "info_projecteddecal",
    "info_node",
    "info_target",
    "info_node_hint",
    "info_player_deathmatch",
    "info_player_combine",
    "info_player_rebel",
    "info_map_parameters",
    "keyframe_rope",
    "move_rope",
    "info_ladder",
    "player",
    "point_viewcontrol",
    "scene_manager",
    "shadow_control",
    "sky_camera",
    "soundent",
    "trigger_soundscape",
    "viewmodel",
    "predicted_viewmodel",
    "worldspawn",
    "point_devshot_camera",
]

#qck: Define up here, rather than in a local function. Might need it someplace else, and I find it cleaner.
#TGB: extended with entities taken from HL2MP preservation list, seeing as I see no reason ZM would be different wrt those ents
entitiesToKeep = [
        #START OLDLIST
        #"worldspawn",
        #"predicted_viewmodel",
        #"player",
        #"hl2mp_gamerules",
        #"ai_network",
        #"soundent",
        #"info_player_start",
        #"info_player_combine",
        #"info_player_rebel",
        #"info_player_deathmatch",
        #"player_manager",
        #"event_queue_saveload_proxy", #qck: Do we need this? I removed it without any problems, but added it back just in case.
        #"team_manager",
        #"scene_manager",
        #END OLDLIST

    "ai_network",
    "ai_hint",
    "hl2mp_gamerules",
    "team_manager",
    "player_manager",
    "env_soundscape",
    "env_soundscape_proxy",
    "env_soundscape_triggerable",
    "env_sun",
    "env_wind",
    "env_fog_controller",
    #	"func_brush", #TGB: causes trouble in dotd
    "func_wall",
    "func_buyzone",
    "func_illusionary",
    "infodecal",
    "info_projecteddecal",
    "info_node",
    "info_target",
    "info_node_hint",
    "info_player_deathmatch",
    "info_player_combine",
    "info_player_rebel",
    "info_player_zombiemaster",
    "info_map_parameters",
    #	"keyframe_rope", #TGB: causes trouble in miner
    #	"move_rope",
    "info_ladder",
    "player",
    "point_viewcontrol",
    "scene_manager",
    "shadow_control",
    "sky_camera",
    "soundent",
    "trigger_soundscape",
    "viewmodel",
    "predicted_viewmodel",
    "worldspawn",
    "point_devshot_camera",
    
    'zm_sharedresources',
]

@usermessage()
def UpdateVisibleEnts(**kwargs):
    if zmresources:
        zmresources.UpdateVisible()

zmresources = None

def ZMResources():
    if not zmresources:
        class Temp:
            zmplayer = None
        return Temp()
    return zmresources

@entity('zm_sharedresources', networked=True)
class SharedResources(BaseResourceClass):
    zmplayer = GenericField(value=None, networked=True)
    
    if isclient:
        oldzmplayer = None
    
    def Spawn(self):
        global zmresources
        super(SharedResources, self).Spawn()
        zmresources = self
        
    def UpdateOnRemove(self):
        global zmresources
        super(SharedResources, self).UpdateOnRemove()
        if zmresources == self:
            zmresources = None
    
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)
        
    def OnDataChanged(self, type):
        super(SharedResources, self).OnDataChanged(type)
        
        self.UpdateVisible()

    def UpdateVisible(self):
        if self.zmplayer != self.oldzmplayer:
            self.oldzmplayer = self.zmplayer
            
            for zme in zombiemastervisible:
                if zme:
                    zme.UpdateVisibility()
        
if isserver:
    class CHL2MPMapEntityFilter(IMapEntityFilter):
        def ShouldCreateEntity(self, pClassname):
            # Don't recreate the preserved entities.
            if pClassname not in s_PreserveEnts:
                return True
            else:
                # Increment our iterator since it's not going to call CreateNextEntity for this ent.
                self.iterator = GetMapEntityRefIteratorNext(self.iterator)
                return False

        def CreateNextEntity(self, pClassname):
            if self.iterator == -1:
                # This shouldn't be possible. When we loaded the map, it should have used 
                # CCSMapLoadEntityFilter, which should have built the g_MapEntityRefs list
                # with the same list of entities we're referring to here.
                assert(False)
                return None
            else:
                ref = GetMapEntityRef(self.iterator)
                self.iterator = GetMapEntityRefIteratorNext(self.iterator) # Seek to the next entity.

                if ref.m_iEdict == -1 or INDEXENT(ref.m_iEdict):
                    # Doh! The entity was delete and its slot was reused.
                    # Just use any old edict slot. This case sucks because we lose the baseline.
                    return CreateEntityByName(pClassname)
                else:
                    # Cool, the slot where this entity was is free again (most likely, the entity was 
                    # freed above). Now create an entity with this specific index.
                    return CreateEntityByName(pClassname, ref.m_iEdict)

        iterator = 0 # Iterator into g_MapEntityRefs.
        
    class CZMMapEntityFilter(IMapEntityFilter):
        def ShouldCreateEntity(self, pClassname):
            # Don't recreate the preserved entities.
            if pClassname not in entitiesToKeep:
                return True
            else:
                # Increment our iterator since it's not going to call CreateNextEntity for this ent.
                self.iterator = GetMapEntityRefIteratorNext(self.iterator)

        def CreateNextEntity(self, pClassname):
            if self.iterator == -1:
                # This shouldn't be possible. When we loaded the map, it should have used 
                # CCSMapLoadEntityFilter, which should have built the g_MapEntityRefs list
                # with the same list of entities we're referring to here.
                assert(False)
                return None
            else:
                ref = GetMapEntityRef(self.iterator)
                self.iterator = GetMapEntityRefIteratorNext(self.iterator) # Seek to the next entity.

                if ref.m_iEdict == -1 or INDEXENT(ref.m_iEdict):
                    # Doh! The entity was delete and its slot was reused.
                    # Just use any old edict slot. This case sucks because we lose the baseline.
                    return CreateEntityByName( pClassname )
                else:
                    # Cool, the slot where this entity was is free again (most likely, the entity was 
                    # freed above). Now create an entity with this specific index.
                    return CreateEntityByName( pClassname, ref.m_iEdict )

        iterator = -1 # Iterator into g_MapEntityRefs.
            
class ZM(WarsBaseGameRules):
    def __init__(self): 
        super(ZM, self).__init__()
        
        self.teamplayenabled = True
        self.intermissionendtime = 0.0
        #self.roundrestart = gpGlobals.curtime + 1.0 #tgb: always begin with a RR so everything is proper #UNDONE interferes with other RR mechanics
        self.roundrestart = 0.0
        self.roundstarttime = 0.0
        self.gamestarttime = 0
        self.roundscompleted = 0

        self.respawnableitemsandweapons = []
        self.tmnextperiodicthink = 0
        self.restartgametime = 0
        self.completereset = False
        self.heardallplayersready = False
        self.awaitingreadyrestart = False

        self.isrestarting = False
        
        self.zmplayer = None
        
    # Helper for summon command
    def SummonZombie(self, unitname, player, spawnidx, amount=1):
        if not player:
            return

        #TGB: now uses idx given by command
        pZombieSpawn = UTIL_EntityByIndex(spawnidx)
        if not pZombieSpawn:
            return

        #determine what to spawn
        #type = pZombieSpawn.GetTypeCode(text)

        #TGB: we now only need to check on spawnflags here, 
        # STODO
        '''
        if type < 0 or type >= ZOMBIE_TOTALTYPES:
            PrintWarning("Bad zombie type\n")
            return
        '''

        # try to add the zombie to the queue for this spawn
        result = False
        for i in range(0, amount):
            result = pZombieSpawn.QueueUnit(unitname)

        if result == False:
            if amount == 1:
                ClientPrint(player, HUD_PRINTTALK, "Zombie could not be added to the spawn queue.")
            else:
                ClientPrint(player, HUD_PRINTTALK, "Not all zombies could be added to the queue.")
        
    # Commands
    def ClientCommand(self, player, args):
        command = args[0]
        
        if command == 'buildmenu_closed':
            # let a zspawn know its build menu has been closed, so it stops sending updates
            zombiespawn = UTIL_EntityByIndex(int(args[1]))
            zombiespawn.ShowBuildMenu(False)
            return True
        elif command == 'summon':
            if args.ArgC() != 3:
                PrintWarning("Bad summon command.\n")
                return True
            self.SummonZombie(args[1].lower(), player, int(args[2]))
            return True
        elif command == 'create_trap':
            if player != self.zmplayer:
                return True

            pEntity = None
            pZombieManipulate = None
            pTrapActual = None

            vecTrapCoordinates = Vector()
            vecTrapCoordinates.x = float(args[1])
            vecTrapCoordinates.y = float(args[2])
            vecTrapCoordinates.z = float(args[3])

            entityIndex = pPlayer.lastselected

            pEntity = UTIL_EntityByIndex(entityIndex)

            #qck: If the last thing we selected was a zombie spawn (it has to be) do some things.
            #LAWYER:  Actually, in this case, it has to be a Manipulate
            if pEntity:
                pZombieManipulate = pEntity # TODO: add check
                if pZombieManipulate:
                    #TGB: make sure we have not hit our trap limit for this manipulate
                    if pZombieManipulate.GetTrapcount() >= ZM_MAX_TRAPS_PER_MANIP:
                        #we've already hit the limit
                        ClientPrint( pPlayer, HUD_PRINTTALK, "Limit of traps for this manipulate reached, can't create new trap!\n")
                        return

                    trapCost = 0
                    if pZombieManipulate.trapcost <= 0:
                        trapCost = pZombieManipulate.cost * 1.5
                    else:
                        trapCost = pZombieManipulate.trapcost

                    if pPlayer.m_iZombiePool >= trapCost:
                        pPlayer.m_iZombiePool -= trapCost

                        #LAWYER: Here, we must add the stuff to create a trap.
                        #REMINDER:  Cost concerns!
                        #Create a trap object
                        pTrapBase = CreateEntityByName( "info_manipulate_trigger" )

                        if pTrapBase:
                            pTrapBase.SetAbsOrigin( vecTrapCoordinates )

                            pTrapBase.Spawn()
                            pTrapBase.Activate()
                            #TGB: not sure why we do a second cast instead of going straight to Trigger above
                            pTrapActual = pTrapBase
                            if pTrapActual:
                                #LAWYER:  Assign it to the parent Manipulate
                                pTrapActual.parentmanipulate = pZombieManipulate

                        #TGB: add to count
                        pZombieManipulate.AddedTrap()
                        #confirm
                        ClientPrint( pPlayer, HUD_PRINTTALK, "Created trap!\n")
                    else:
                        ClientPrint( pPlayer, HUD_PRINTTALK, "Not enough resources!\n")
                        return True
            return True
        elif command == 'manipulate':
        #	Warning("Manipulating\n")

            if player.GetOwnerNumber() != ON_ZOMBIEMASTER:
        #		Msg("You aren't a Zombiemaster, and can't do that.\n")
                return True
            pEntity = None
            pZombieManipulate = None

            if player:
        #			Warning("We have a player\n")
                entityIndex = player.lastselected #LAWYER:  Collect the entity's index

                pEntity = UTIL_EntityByIndex( entityIndex )
                if pEntity:
        #				Warning("We have an entity\n")
                    pZombieManipulate = pEntity
                    if pZombieManipulate:
        #				Warning("We have a manipulate\n")
                       #LAWYER: It's a manipulatable!  DO SOMETHING!
                                #We should stick a gump in here, but for now, we'll skip it
        #						Msg("Activated!\n")
                        if resources[player.GetOwnerNumber()][RESOURCE_ZOMBIEPOOL] >= pZombieManipulate.cost:
                            #Warning("We should be activating it\n")
                                player.m_iZombiePool -= pZombieManipulate.cost
                                pZombieManipulate.Trigger(player)
                        else:
                            #	Warning("Not enough resources!\n")
                            ClientPrint( player, HUD_PRINTTALK, "Not enough resources!\n")
            return True
            
        return super(ZM, self).ClientCommand(player, args)

    # Events
    def PlayerKilled(self, victim, info):
        if self.IsIntermission():
            return
        super(ZM, self).PlayerKilled(victim, info)

    def ZombieKilled(self, pVictim, info): 
        if not pVictim:
            return

        # Find the killer & the scorer
        pInflictor = info.GetInflictor()
        pKiller = info.GetAttacker()
        pScorer = GetDeathScorer( pKiller, pInflictor )

        killerID = pScorer.GetUserID() if (pScorer) else -1

        #TGB: copied from DeathNotice for players, throwing a zombie death event lets server plugins
        #	do nicer stat tracking, as requested by server-admin-dude asceth
        event = GameEvent('zombie_death', zm_debugevents.GetBool())
        if event:
            weapon = "world"
            #TGB: molotov/barrel hack
            if info.GetDamageType() & DMG_BURN:
                weapon = "fire"
            elif info.GetDamageType() & DMG_BLAST:
                weapon = "explosion"
            elif pScorer and pScorer.activeweapon:
                weapon = pScorer.activeweapon.GetClassname()
            #else "world"

            event.SetString("type", pVictim.GetClassname())
            event.SetInt("attacker", killerID )
            event.SetInt("damage", ceil(info.GetDamage()))
            event.SetString("weapon", weapon)
            event.SetInt("z_id", pVictim.entindex())
        
            FireGameEvent(event)
            
            #DevMsg("Throwing zombie_death event: type %s, attacker %i, dmg %i, weapon %s\n", pVictim.GetClassname(), killerID, ceil(info.GetDamage()), weapon)

    def ZombieSpawned(self, pZombie):
        if not pZombie: return
        
        event = GameEvent('zombie_spawn', zm_debugevents.GetBool())
        if event:
            event.SetString("type", pZombie.GetClassname())
            event.SetInt("z_id", pZombie.entindex())
            FireGameEvent( event )

            #DevMsg("Throwing zombie_create event: type %s\n", pZombie.GetClassname())

    #TGB: another event, all these together pretty much allow achievements through server plugins
    def ZombieHurt(self, pVictim, info):
        if not pVictim:
            return

        # Find the killer & the scorer
        pInflictor = info.GetInflictor()
        pKiller = info.GetAttacker()
        pScorer = self.GetDeathScorer(pKiller, pInflictor)

        killerID = pScorer.GetUserID() if pScorer else -1
        
        event = GameEvent('zombie_hurt', zm_debugevents.GetBool())
        if event:
            weapon = "world"
            #TGB: molotov/barrel hack
            if info.GetDamageType() & DMG_BURN:
                weapon = "fire"
            elif info.GetDamageType() & DMG_BLAST:
                weapon = "explosion"
            elif pScorer and pScorer.activeweapon:
                weapon = pScorer.activeweapon.GetClassname()
            #else "world"

            #DevMsg("Inflictor: %s\n", (pInflictor) ? pInflictor.GetClassname() : "None")

            event.SetString("type", pVictim.GetClassname())
            event.SetInt("attacker", killerID )
            event.SetInt("damage", ceil(info.GetDamage()))
            event.SetString("weapon", weapon)
            event.SetInt("z_id", pVictim.entindex())

            # This event is not transmitted to clients, as that'd be a waste of bandwidth
            FireGameEvent( event, True )

            #DevMsg("Throwing zombie_death event: type %s, attacker %i, dmg %i, weapon %s\n", pVictim.GetClassname(), killerID, ceil(info.GetDamage()), weapon)

    #TGB: game event for getting points
    def PlayerGotPoints(self, pPlayer, points, pEntity):
        pBasePlayer = pPlayer
        if pBasePlayer and pBasePlayer.IsPlayer() and pEntity:
        
            event = GameEvent('player_got_points', zm_debugevents.GetBool())
            if event:
                event.SetInt("player", pBasePlayer.GetUserID())
                event.SetInt("points", points)
                event.SetInt("score_ent", pEntity.entindex())

                FireGameEvent( event, True )

    #TGB: game event for win condition
    def TeamVictorious(self, humans_won, cause):
        event = GameEvent('round_victory', zm_debugevents.GetBool())
        if event:
            #const char *name = STRING( pManipulate.GetEntityName() ) #I remember linux hating getentityname
            event.SetBool("humans_won", humans_won)
            event.SetString("cause", cause)

            FireGameEvent( event, True )

    #TGB: game event for triggered manip
    def ManipulateTriggered(self, pManipulate):
        if not pManipulate: return
        
        event = GameEvent('triggered_manipulate', zm_debugevents.GetBool())
        if event:
            #const char *name = STRING( pManipulate.GetEntityName() ) #I remember linux hating getentityname
            event.SetInt("entindex", pManipulate.entindex())

            FireGameEvent( event, True )
            
    def IsTeamplay(self):
        return True
    
    # Thinking
    def Think(self):
        super(ZM, self).Think()
        
        #LAWYER:  Check if we want a round restart!
        if self.roundrestart != 0.0 and gpGlobals.curtime >= self.roundrestart:
                #LAWYER:  Restart the round!
                self.roundrestart = 0.0 #Reset the clock!
                PrintWarning("Restarting round...\n")
                self.EndRound()

        if self.gameover:   # someone else quit the game already
            # check to see if we should change levels now
            if self.intermissionendtime < gpGlobals.curtime:
                self.ChangeLevel() # intermission is over

            return

    #	flTimeLimit = mp_timelimit.GetFloat() * 60
        flFragLimit = fraglimit.GetFloat()
        flRoundLimit = roundlimit.GetFloat() #LAWYER:  Maximum number of rounds

        if self.GetMapRemainingTime() < 0:
            self.GoToIntermission()
            return

        #LAWYER:  We need to check for round limit!
        if flRoundLimit:
            if self.roundscompleted > (flRoundLimit + 1): #LAWYER:  Fudged, to give a more accurate round count
                #Number of rounds exceeded - next map!
                self.GoToIntermission()

        if flFragLimit:
            if self.IsTeamplay() == True:
                # STODO
                '''
                pCombine = g_Teams[TEAM_HUMANS]
                pRebels = g_Teams[TEAM_ZOMBIEMASTER]

                if pCombine.GetScore() >= flFragLimit or pRebels.GetScore() >= flFragLimit:
                    self.GoToIntermission()
                    return
                '''
            else:
                # check if any player is over the frag limit
                for i in range(1, gpGlobals.maxClients+1):
                    pPlayer = UTIL_PlayerByIndex( i )

                    if pPlayer and pPlayer.FragCount() >= flFragLimit:
                        self.GoToIntermission()
                        return

        if gpGlobals.curtime > self.tmnextperiodicthink:
            self.CheckRestartGame()
            self.tmnextperiodicthink = gpGlobals.curtime + 1.0

        if self.restartgametime > 0.0 and self.restartgametime <= gpGlobals.curtime:
            self.RestartGame()

        if zm_weaponreset.GetBool():
            self.ManageObjectRelocation()
        
    def SpawnSurvivor(self, player, origin, angles):
        """ Spawn a survivor unit and attach the player """
        angles[0] = 0.0 # Set pitch to zero
        survivor = CreateUnit('zm_unit_survivor', origin, angles, 2)
        player.SetControlledUnit(survivor)
        
    #TGBNOTE: this could be what makes weapons "respawn", or at least one of the causes
    def ManageObjectRelocation(self):
        pass

    def GetGameDescription(self):
    #	if ( IsTeamplay() )
    #		return "Team Deathmatch" 

        return "Zombie Python Master"


    def GetMapRemainingTime(self):
        # if timelimit is disabled, return 0
        if mp_timelimit.GetInt() <= 0:
            return 0

        # timelimit is in minutes
        timeleft = (self.gamestarttime + mp_timelimit.GetInt() * 60.0 ) - gpGlobals.curtime

        return timeleft

    #=========================================================
    # Deathnotice. 
    #=========================================================
    def DeathNotice(self, victim, info):
        # Work out what killed the player, and send a message to all clients about it
        killer_weapon_name = "world"		# by default, the player is killed by the world
        killer_ID = 0
        bZombieKill = False

        # Find the killer & the scorer
        pInflictor = info.GetInflictor()
        pKiller = info.GetAttacker()
        pScorer = self.GetDeathScorer( pKiller, pInflictor )

        if not pKiller or not pVictim: return #just in case

        # Custom kill type?
        if info.GetCustomKill():
            killer_weapon_name = self.GetCustomKillString( info )
            if pScorer:
                killer_ID = pScorer.GetUserID()
        else:
            # Is the killer a client?
            if pScorer:
                killer_ID = pScorer.GetUserID()
                
                if pInflictor:
                    if pInflictor == pScorer:
                        # If the inflictor is the killer,  then it must be their current weapon doing the damage
                        if pScorer.activeweapon:
                            killer_weapon_name = pScorer.activeweapon.GetClassname()
                    else:
                        killer_weapon_name = pInflictor.GetClassname()  # it's just that easy
            else:
                killer_weapon_name = pInflictor.GetClassname()

            # strip the NPC_* or weapon_* from the inflictor's classname
            if killer_weapon_name.startswith('weapon_'):
                killer_weapon_name = killer_weapon_name[6:-1]
            elif killer_weapon_name.startswith("npc_"):
                killer_weapon_name = killer_weapon_name[3:-1]
            # STODO
            '''
            elif ( V_strncmp( killer_weapon_name, "func_", 5 ) == 0 )
            
                killer_weapon_name += 5
            
            elif ( V_strstr( killer_weapon_name, "physics" ) )
            
                killer_weapon_name = "physics"
            

            if ( V_strcmp( killer_weapon_name, "prop_combine_ball" ) == 0 )
            
                killer_weapon_name = "combine_ball"
            
            elif ( V_strcmp( killer_weapon_name, "grenade_ar2" ) == 0 )
            
                killer_weapon_name = "smg1_grenade"
            
            elif ( V_strcmp( killer_weapon_name, "satchel" ) == 0 or V_strcmp( killer_weapon_name, "tripmine" ) == 0)
            
                killer_weapon_name = "slam"
            '''


            #TGB: if a human was killed by a zombie
            if pVictim.GetTeamNumber() == 2 and pKiller.Classify() == CLASS_ZOMBIE:
                killer_weapon_name = "Zombie"
                #DevMsg("Killed by a zombie. pKiller class = %s \n", pKiller.GetClassname())

                if pKiller.GetClassname() == "npc_zombie":
                    killer_weapon_name = "Shambler"
                elif pKiller.GetClassname() == "npc_fastzombie":
                    killer_weapon_name = "Banshee"
                elif pKiller.GetClassname() == "npc_poisonzombie":
                    killer_weapon_name = "Hulk"
                elif pKiller.GetClassname() == "npc_burnzombie":
                    killer_weapon_name = "Immolator"
                elif pKiller.GetClassname() == "npc_dragzombie":
                    killer_weapon_name = "Drifter"
                else:
                    killer_weapon_name = 'Unknown'

                bZombieKill = True
                #find the ZM id
                for i in range(1, gpGlobals.maxClients+1):
                    plr = UTIL_PlayerByIndex( i )

                    if plr:
                        if plr.GetTeamNumber() == 3:
                            killer_ID = plr.GetUserID()
                            break
                            
        event = GameEvent('player_death')
        if event:
            event.SetInt("userid", pVictim.GetUserID() )
            event.SetInt("attacker", killer_ID )
            event.SetString("weapon", killer_weapon_name )
            #event.SetInt( "priority", 7 )
            event.SetBool("zombie", bZombieKill)
            if bZombieKill:
                event.SetInt("z_id", pKiller.entindex() )
            else:
                event.SetInt("z_id", 0 )

            FireGameEvent( event )

    def HavePlayers(self):
        # STODO
        return True
        
    def CheckRestartGame(self):
        # Restart the game if specified by the server
        iRestartDelay = mp_restartgame.GetInt()

        if iRestartDelay > 0:
            if iRestartDelay > 60:
                iRestartDelay = 60

            # let the players know
            seconds = "SECOND" if iRestartDelay == 1 else "SECONDS"
            UTIL_ClientPrintAll( HUD_PRINTCENTER, "Game will restart in %d %s" % (iRestartDelay, seconds) )
            UTIL_ClientPrintAll( HUD_PRINTCONSOLE, "Game will restart in %d %s" % (iRestartDelay, seconds) )

            self.restartgametime = gpGlobals.curtime + iRestartDelay
            self.completereset = True
            mp_restartgame.SetValue( 0 )

    #TGBMERGENOTE: This is Valve's implementation of roundrestart. It speaks of combine and rebels and therefore errors, but we may be able to copy stuff from it to enhance our implementation.

    def RestartGame(self):
        DevMsg("RUNNING VALVE'S RESTARTGAME OH NOE\n")
    
    def CleanUpMap(self):
        # Recreate all the map entities from the map data (preserving their indices),
        # then remove everything else except the players.

        # Get rid of all entities except players.
        pCur = gEntList.FirstEnt()
        while pCur:
            pWeapon = pCur
            # Weapons with owners don't want to be removed..
            if pWeapon:
                if not pWeapon.GetPlayerOwner():
                    UTIL_Remove( pCur )

            # remove entities that has to be restored on roundrestart (breakables etc)
            elif pCur.GetClassname() not in s_PreserveEnts:
                UTIL_Remove( pCur )

            pCur = gEntList.NextEnt( pCur )

        # Really remove the entities so we can have access to their slots below.
        gEntList.CleanupDeleteList()

        # Cancel all queued events, in case a func_bomb_target fired some delayed outputs that
        # could kill respawning CTs
        g_EventQueue.Clear()

        filter = CHL2MPMapEntityFilter()
        filter.iterator = GetMapEntityRefIteratorHead()

        # DO NOT CALL SPAWN ON info_node ENTITIES!
        MapEntity_ParseAllEntities(engine.GetMapEntitiesString(), filter, True)
        
    if isserver:
        def InitGamerules(self):
            super(ZM, self).InitGamerules()
            
            self.sr = CreateEntityByName('zm_sharedresources')
            self.sr.Spawn()
            
            for i in range(1, gpGlobals.maxClients+1):
                pPlayerMP = UTIL_PlayerByIndex(i)
                if pPlayerMP:
                    self.SetupPlayer(pPlayerMP)
            
            self.FinishingRound()
            
        def ShutdownGamerules(self):
            super(ZM, self).ShutdownGamerules()
            
            self.sr.Remove()
            self.sr = None
            
    def SetupPlayer(self, player):
        player.m_iZMVoteRR = 0
        player.m_iZMPriority = 0
        player.m_zmParticipation = 0
        player.m_bObserve = False
        player.m_iZombiePool = 0
        player.m_iZombiePopCount = 0
        player.m_iZombieSelected = 0
        
        
    def PlayerSpawn(self, player):
        super(ZM, self).PlayerSpawn(player)
        
        #self.PlayerSpawning()
        
    def FinishingRound(self):
        #LAWYER:  ZOOOOMJ! There's been a call to restart the round!  Start the clock!
        if self.roundrestart <= gpGlobals.curtime: # LAWYER:  Only change the clock if it's not ticking
            self.roundrestart = gpGlobals.curtime + 4.0

            #TGB: moved into this if block to avoid spammo
            UTIL_ClientPrintAll(HUD_PRINTTALK, "The round is restarting...\n")
    
    def EndRound(self):
        """
            1. fire round_restart event
            2. clear lagcompensation history
            3. destroy zm_group_manager			(seems redundant, as it'd be killed by WorldReset, but can't hurt)
            4. count players and remove their weapons
            5. IF NO PLAYERS, RR ENDS HERE

            6. reset players to the survivor team, also find the player with highest ZMing priority
            7. build some lists to use in ZM picking (more detail in the relevant code)
            8. pick ZM and move him to the right team
            9. RESET WORLD
           10. spawn players
           11. process info_loadout


            there are some potential issues with this. For example, why is the world only reset with no
            players present? It seems healthy to reset the world regularly, though it would be a bit odd
            if our current memleak comes from there, seeing as servers with active players often get RRs
            with proper worldresets, and still have memleaks. Might be better to leave that alone until
            other options have been exhausted.

            The bits that occur before the check need looking at. Also, the check should perhaps be
            moved up, as that would be more logical: the RR event would only be fired for an actual RR, 
            etc. Checking for players is trivial by getting at the CTeam classes.
        """
        print("Round ending...\n")

        if self.HavePlayers() == False:
            print("No players present, aborting round restart.\n")
            return

        UTIL_ClientPrintAll(HUD_PRINTTALK, "Round has ended. Starting new round...\n")

        #LAWYER:  -----Perform clean-up operations-----

        #TGB: currently only exists to tell server plugins about the restart
        event = GameEvent('round_restart')
        if event:
            FireGameEvent(event)

        #TGB: clear lagcomp history
        # STODO: Add?
        #lagcompensation.ClearHistory()

        #qck: Clean up groups

        pManEnt = gEntList.FindEntityByClassname(None, "zm_group_manager")
        if pManEnt:
            pManager = pManEnt
            if pManager:
                UTIL_Remove(pManager)

                DevMsg("Reset server group manager\n")

        #iNumPlayers = 0 #init player counting var

        #print("Counting players AND Stripping weapons...\n")
        print("Stripping weapons...\n")

        #TGB: Count players AND strip weapons
        #LAWYER:  -----Count the players-----
        #LAWYER:  -----Weapon Strip-----
        for i in range(1, gpGlobals.maxClients+1):
            #TGB:should be possible, but is unnecessary right now
            #CHL2MP_Player *pPlayer = dynamic_cast< CHL2MP_Player * >(UTIL_PlayerByIndex( i ))

            pPlayer = UTIL_PlayerByIndex(i)

            if pPlayer:
                # TODO: refactor into a Reset() function for players? [19-11-2008]

                pPlayer.m_iZombieGroup = None
                #TGB: count player
                #iNumPlayers++

                #TGB: 0000106 make sure players don't get to keep ammo
                pPlayer.RemoveAllAmmo()

                #LAWYER: the actual stripping component
                for i in range(0, pPlayer.WeaponCount()):
                    pWeapon = pPlayer.GetWeapon( i )
                    if not pWeapon:
                        continue

                    DevMsg(1, "Removing weapon #%i: %s\n" % (i, pWeapon.GetClassname()))

                    pPlayer.Weapon_Drop( pWeapon, (0,0,0), (0,0,0) )
                    UTIL_Remove( pWeapon )
                
                DevMsg(1, "After stripping weapons %i remain\n" % (pPlayer.WeaponCount()))

        #TGB: 0-player check moved to occur before anything else, makes more sense that way

        #TGB: 0-player check
    # 	if (iNumPlayers == 0)
    # 	
    # 		print("Cannot RoundRestart, there are no (connected) players!\n") #LAWYER:  Don't restart without players!
    # 		return
    # 	
        
        ''' TGB: 
            Right, I want to add some randomization here, but looking at it I don't like the multiple spawns.
            UPDATE: modified ChangeTeam not to spawn a player yet, so we can shuffle them around all we want.
        '''

        pZMPlayer = None

        print("Resetting players to survivor team...\n")
        iHighest = -1 #we already want to know the highest priority level
        for i in range(1, gpGlobals.maxClients+1):
            pPlayerMP = UTIL_PlayerByIndex(i)
            
            if pPlayerMP: #Flash everyone onto the Human team
                #LAWYER:  Reset RR will
                pPlayerMP.m_iZMVoteRR = 0
                pPlayerMP.SetOwnerNumber(ON_SURVIVOR)
                pPlayerMP.ChangeTeam(TEAM_UNASSIGNED)
                #pPlayerMP.ChangeTeamDelayed(TEAM_HUMANS) #set player as human
                #Try to kill crazy lists	
                #pPlayerMP.ShowViewPortPanel( PANEL_START, False ) # STODO

                #TGB: determine highest ZM priority of all players
                if pPlayerMP.m_iZMPriority > iHighest and pPlayerMP.m_zmParticipation == 0:
                    iHighest = pPlayerMP.m_iZMPriority


        '''TGB:
            The below works like this:
                1. Dump all ZMs that have the highest priority in a list
                2. Dump all other non-observers in a list
                3. If the list from 1 has players in it, randomly pick one as ZM
                4. Else, randomly pick one from list 2 as ZM
        '''

        print("Building list of potential ZM players...\n")

        #TGB: build a list of all players with the top priority
        pZMs = []
        #TGB: and a list of all players that prefer survivor and/or do not have top priority
        pEmergencyZMs = []

        for i in range(1, gpGlobals.maxClients+1): #Now check, assuming there are available players
            pPlayerMP = UTIL_PlayerByIndex(i)
            if pPlayerMP:
                #TGB: this was below the continues before. However, when we want an emergency ZM, we
                #	want anyone at all. Doesn't make sense to exclude observers etc.
                #Emergency ZM? = any priority + any willingness
                pEmergencyZMs.insert(0, pPlayerMP) #add this player to the list of emergency ZMs

                #Observer?
                if pPlayerMP.m_zmParticipation == 2:
                    pPlayerMP.ChangeTeam(TEAM_SPECTATOR)
                    #pPlayerMP.ChangeTeamDelayed(TEAM_SPECTATOR) #LAWYER:  This player doesn't want to play in this round
                    continue #NEXT!

                #First-choice ZM? = high priority + wants to zm
                if pPlayerMP.m_iZMPriority == iHighest and pPlayerMP.m_zmParticipation == 0:
                    pZMs.insert(0, pPlayerMP) #add this player to the list of first-choice ZMs
                    continue #NEXT

        #TGB: we now have two lists: 
        #one with people we would typically choose as ZM, ie. w/ highest priority and zm-willingness
        #one with people that we will only choose if no other options are available

        #TGB: ----- SELECT ZM -----
        if len(pZMs) > 0: #TGB: got any good candidates?
            print("Picking willing ZM...\n")
            #yuppers, select a random one
            randnum = random.randint(0, len(pZMs) - 1)
            pZMPlayer = pZMs[randnum] #select a random one

            if not pZMPlayer:
                DevWarning("Invalid player in ZMs list!\n")
        
        else: #oh sh, gotta use the emergency list
            #LAWYER:  1-player check
            #TGB: did not seem useful: all players are in the pEmergencyZMs list, the single player
            #	will therefore always get picked.
            '''if iNumPlayers == 1: #nom nom nom
            
                CBaseEntity *pOnePlayer = None
                pOnePlayer = gEntList.FindEntityByClassname( pOnePlayer, "player" )
                pZMPlayer = dynamic_cast< CHL2MP_Player * >(pOnePlayer)
            
            else
            
                Msg("Picking unwilling ZM as no willing ones are available...\n")
                const int randnum = random.RandomInt(0, pEmergencyZMs.Count() - 1)
                pZMPlayer = pEmergencyZMs[randnum]
            '''

            print("Picking unwilling ZM as no willing ones are available...")
            randnum = random.randint(0, len(pEmergencyZMs) - 1)
            pZMPlayer = pEmergencyZMs[randnum]

            if not pZMPlayer:
                DevWarning("Invalid player in emergency ZMs list!")
        
        
        #LAWYER:  -----Emergency player picker, in case of all players being unwilling-----
        #TGB: super last chance check, should never occur
        while pZMPlayer == None:
            print("Attempting emergency ZM player pick(s)...")
            pForcedZM = None
            pForcedZM = gEntList.FindEntityByClassname(pForcedZM, "player")
            pZMPlayer = pForcedZM

        #TGB: ----- ZOMBIEMASTERIFY THE CHOSEN ZM ----- 
        #pZMPlayer = None # STEMP
        if pZMPlayer:
            print("Moving chosen ZM to Zombie Master position...")
            #TGB: reset ZMpriority
            pZMPlayer.m_iZMPriority = 0
            pZMPlayer.SetOwnerNumber(ON_ZOMBIEMASTER)
            pZMPlayer.ChangeTeam(TEAM_UNASSIGNED)
            #pZMPlayer.ChangeTeamDelayed(3)
            
            self.zmplayer = pZMPlayer
            print('SETTING NEW zm player: %s' % (pZMPlayer))
            self.sr.zmplayer = pZMPlayer

        #LAWYER:  -----Reset the world-----
        print("Resetting entities...")
        self.WorldReset()
        
        #LAWYER: -----Spawn the players-----
        print("Spawning players...")
        for i in range(1, gpGlobals.maxClients+1):
            pPlayer = UTIL_PlayerByIndex( i )
            pPlayerMP = None
            pPlayerMP = pPlayer

            if pPlayerMP:
                #TGB: handled in spawn() now
                #pPlayer.m_iWeaponFlags = 0 #LAWYER:  Reset weaponflags.
                
                #TGB: cleaned up a bit

                #observers get off easy
                if pPlayerMP.m_bObserve:
                    continue

                #show participation picker
                # STODO
                #if pPlayerMP.m_zmParticipation == 3:
                #    pPlayerMP.ShowViewPortPanel( PANEL_START, True ) #LAWYER:  Show them the start panel again, if they've not picked
            
                #TGB: everyone being spawned here gets a ZMrating increase, if not the ZM
                if pPlayerMP.GetTeamNumber() != 3:
                    pPlayerMP.m_iZMPriority += 10
                
                #LAWYER:  Display map objectives on spawn
                data = KeyValues("data")
                if data:
                    data.SetString( "title", "Objectives" )		# info panel title
                    data.SetString( "type", "1" )			# show userdata from stringtable entry
                    data.SetString( "msg",	"mapinfo" )		# use this stringtable entry

                    #pPlayerMP.ShowViewPortPanel( PANEL_INFO, True, data ) # STODO

                    data = None

                #TGB: finally spawn this chap
                pPlayerMP.Spawn()
                
                #S: create survivor
                if pPlayerMP.GetOwnerNumber() == 2:
                    self.SpawnSurvivor(pPlayerMP, pPlayerMP.GetAbsOrigin(), pPlayerMP.GetAbsAngles())

        #LAWYER:  Increase the roundcounter!
        self.roundstarttime = gpGlobals.curtime #we just started a new round
        self.roundscompleted += 1

        #LAWYER:  Apply any weapons!
        pFound = None
        m_pLoadOut = None
        pFound = gEntList.FindEntityByClassname( pFound, "info_loadout" )
        Msg("Finding a Loadout entity...")
        if pFound:
            m_pLoadOut = pFound
            if m_pLoadOut:
                print("Found a Loadout! Distributing...")
                m_pLoadOut.Distribute()
        else:
            print("No loadout.")
            
        # Force update visible
        #filter = CSingleUserRecipientFilter(pZMPlayer)
        #filter.MakeReliable()
        UpdateVisibleEnts() # Push visible update for all players

        print("RoundRestart complete!")
        
    def WorldReset(self):
        #qck: COMMENT OUT FOR LINUX TEST
        #qck: I found that only worldspawn should be kept out of the whole "reset" phase. Everything else should
        #pass through it, but certain entities can't be passed through UTIL_Remove(). So we setup an array to keep 
        #things out of UTIL_Remove(), and a small, normal filter to keep worldspawn out of ParseAllEntities()

        #qck: Get rid of the entities we don't need to keep for the next round.
        pEnt = gEntList.FirstEnt()
        while pEnt:
            if pEnt.GetClassname() not in entitiesToKeep:
                UTIL_Remove( pEnt )

            pEnt = gEntList.NextEnt( pEnt )
        
        gEntList.CleanupDeleteList()
        g_EventQueue.Clear() #qck: This clears out the global queue, which stores all entity output. Reset to avoid logic running over into the next round.

        '''
        # STODO, already covered by the unitlistpertype (core.units)
        #TGB: lets clear out our nasty global lists as well
        gEntList.m_ZombieList.Purge()
        gEntList.m_BansheeList.Purge()
        gEntList.m_ZombieSelected.Purge()
        #these aren't as round dependent
        #TGB: I put these back in, because we want to be safe and it won't hurt
        gEntList.m_ZombieSpawns.Purge()
        gEntList.m_ZombieManipulates.Purge()
        '''
        
        '''qck: Parse all entities using the pristine map entity lump. Spawn, Reset their keyfields, etc.
               Using CMapEntityFilter with a slight modification to be sure it skips worldspawn */
        /*TGB: I've found this is not the case. Entities we preserve have to be filtered, or they will duplicate.
         With every preserved ent duplicating on roundrestart, entity limit overflows are unavoidable. '''
                
        #TGB: copying the filter in from HL2MP function, adapted for ZM
        filter = CZMMapEntityFilter()
        filter.iterator = GetMapEntityRefIteratorHead()

        # DO NOT CALL SPAWN ON info_node ENTITIES!

        #CMapEntityFilter filter
        print("Parsing entities...") 
        MapEntity_ParseAllEntities( engine.GetMapEntitiesString(), filter, True )
    

class ZMInfo(GamerulesInfo):
    name = 'zm'
    displayname = '#ZM_Name'
    description = '#ZM_Description'
    cls = ZM
    mappattern = '^zm_.*$'
