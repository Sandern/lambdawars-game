"""
This module manages game packages.

A game package contains definitions for units, abilities, factions, etc.
"""
import sys
import os
import traceback
import inspect
import time
import imp
import logging

import srcmgr
from srcmgr import ImportSubMods, ReloadSubMods
from fields import SetupClassFields, GetAllFields
from gamedb import (dbgamepackages, GamePackageInfo, dblist, RegisterGamePackage)

from core.dispatch import receiver
from core.signals import prelevelinit, gamepackageloaded, gamepackageunloaded
from core.usermessages import usermessage, usermessage_shared
from core.util.gamepackage import BuildScriptGamePackages, ReadJSONGamePackage
from gamerules import GameRules
from particles import ReadParticleConfigFile, DecommitTempMemory
from entities import GetAllClassnames, GetClassByClassname, CBasePlayer
import filesystem
import matchmaking

import consolespace

# Server specific
if isserver:
    from entities import entlist, RespawnPlayer
    from utils import UTIL_IsCommandIssuedByServerAdmin, UTIL_Remove, UTIL_GetPlayers
    from gameinterface import CSingleUserRecipientFilter, concommand, FCVAR_CHEAT, AutoCompletion, engine


if isclient:
    @receiver(prelevelinit)
    def ClientPreLevelInit(sender, **kwargs):
        # Use level init to purge all loaded packages on the client
        # The server will send the list of packages to load
        packages = set(dbgamepackages.keys())
        done = set()
        for name in packages:
            if dbgamepackages[name].loaded:
                done |= UnLoadGamePackage(name)


def GetSortedDBList(db):
    """ Given a DB of a gamepackage, sort it on priority. """
    sorteddblist = list(db.items())
    sorteddblist.sort(key=lambda i: i[1].priority, reverse=True)
    return sorteddblist


# BaseInfoMetaclass registers the class        
class BaseInfoMetaclass(type):
    def __new__(cls, name, bases, dct):
        # Create the new cls
        newcls = type.__new__(cls, name, bases, dct)
        
        # Parse all fields instances defined on the object
        SetupClassFields(newcls)
        
        # Auto generate name if specified
        if 'name' not in dct and newcls.autogenname:
            newcls.name = '%s__%s' % (newcls.__module__, newcls.__name__)
        
        # If no mod name is give, but we do have a name, then use the newcls module as modname
        if 'modname' not in dct and newcls.name:
            newcls.modname = newcls.__module__
        
        # Might be a 'fallback' info object that is not registered
        if newcls.modname != None:
            modname = newcls.modname.split('.')[0]
            
            # temp: Make sure the db list has the right priority
            if newcls.id not in dbgamepackages[modname].db:
                dbgamepackages[modname].db[newcls.id].priority = dblist[newcls.id].priority
            
            # Add to our gamepackage for loading/unloading
            # Overwrite old one
            dbgamepackages[modname].db[newcls.id][newcls.name] = newcls
            
            # Add to the active list if our gamepackage is loaded   
            if dbgamepackages[modname].loaded:
                dblist[newcls.id][newcls.name] = newcls
                newcls.OnLoaded()  
        return newcls


class BaseInfo(object, metaclass=BaseInfoMetaclass):
    """ Base object for registering units, abilities, gamerules, etc
        into a game package. 
    """
    
    id = None
    modname = None
    name = None
    autogenname = False
    
    # Default method implementations
    @classmethod 
    def OnLoaded(info):
        pass
    @classmethod 
    def OnUnLoaded(info):
        pass


def BuildGamePackageList():
    """ Build list of available game packages.
    
        Scans for both Python defined packages as for 
        reading out the script defined packages.

        A python package is considered a game package
        if it contains a package.json file.
    """
    # Find Python defined game packages
    for d in filesystem.ListDir('python/'):
        init_path = os.path.join('python', d, '__init__.py')
        package_path = os.path.join('python', d, 'package.json')
        if not filesystem.FileExists(init_path) or not filesystem.FileExists(package_path):
            continue
        try:
            __import__(d)
        except:
            print('%s is not a gamepackage: ' % (d))
            traceback.print_exc()
            continue

    # Add scripts to the party
    BuildScriptGamePackages()


def GPImportModules(gpname, modulelist):
    """ Imports Python modules defined by a game packages.
    
        Each game package definition may define a list with the paths
        of modules. $ and # can be used to annotate them as server or client
        only and wildcards to load all in a folder.
        
        Args:
            gpname (str): Name of the game package.
            modulelist (list): the list of modules to import.
    """
    # '#' denotes server only and '$' client only
    skipstartsymbol = '$' if isserver else '#'
    stripsymbol = '$#'
    for m in modulelist:
        if m.startswith(skipstartsymbol):
            continue
        m = m.lstrip(stripsymbol)
        modulename = '%s.%s' % (gpname, m)

        # Ending with '*' means import the whole package
        if modulename.endswith('*'):
            modulename = modulename.split('.*')[0]
            try:
                __import__(modulename)
                mod = sys.modules[modulename]
            except:
                PrintWarning('Error encountered while trying to import sub modules of %s\n' % (modulename))
                traceback.print_exc()
                continue
            ImportSubMods(mod)
        else:
            try:
                __import__(modulename)
            except:
                PrintWarning('Error encountered while trying to import sub modules of %s\n' % (modulename))
                traceback.print_exc()
                
def GPReloadModules(gpname, modulelist):
    # '#' denotes server only and '$' client only
    skipstartsymbol = '$' if isserver else '#'
    stripsymbol = '$#'
    done = set()
    for m in modulelist:
        if m.startswith(skipstartsymbol):
            continue
        m = m.lstrip(stripsymbol)
        modulename = '%s.%s' % (gpname, m)

        # Ending with '*' means import the whole package + the module itself
        if modulename.endswith('*'):
            modulename = modulename.split('.*')[0]
            __import__(modulename)
            mod = sys.modules[modulename]
            ReloadSubMods(mod, done)
        
        try:
            imp.reload(sys.modules[modulename])
        except:
            PrintWarning('Error encountered while trying to reload sub modules of %s\n' % (modulename))
            traceback.print_exc()
        
        done.add(modulename)


#
# Loading/unloading game packages
#    
def LoadGamePackage(package_name, informclient=True):
    """ Load a game package (a set of units, abilities, gamerules, etc). """
    # Check if the package is already loaded
    try:
        gp = dbgamepackages[package_name]
        if gp.loaded:
            return
    except KeyError:
        logging.exception('Could not load %s game package. Maybe not registered?', package_name)
        return
        
    startmeasuretime = time.time()
        
    try:
        if not gp.script_path:
            # TODO: not needed? should already be imported at this point
            __import__(package_name)
        try:
            gp = dbgamepackages[package_name]
        except KeyError:
            PrintWarning('Failed to load gamepackage %s\n' % package_name)
            return

        if not gp.script_path:
            # Bind to console space for easy usage with spy/cpy commands
            setattr(consolespace, package_name, sys.modules[package_name])

        # Read particle files (once only, annoyingly slow on reloading a package. TODO: Make it an option)
        particles = gp.particles
        if particles and not gp.loadedonce:
            print('Loading particles of gamepackage %s' % package_name)
            for p in particles:
                ReadParticleConfigFile(p)
            DecommitTempMemory()
            
        loadtimeone = time.time() - startmeasuretime
            
        # Load dependencies
        for d in gp.dependencies:
            LoadGamePackage(d, False)
            
        startmeasuretime = time.time()
            
        # Do imports
        if gp.modules:
            GPImportModules(package_name, gp.modules)

        # In case of script: read the json file
        if gp.script_path:
            ReadJSONGamePackage(gp)
        
        # Import everything that must be registered from within the module
        if not gp.script_path and hasattr(sys.modules[package_name], 'LoadGame'):
            sys.modules[package_name].LoadGame(gp=gp)
        
        # Add abilities/factions/units from the db's
        sorteddblist = GetSortedDBList(gp.db)
        for k, v in sorteddblist:
            for k2, info in v.items():
                try:
                    dblist[k][info.name] = info
                    info.OnLoaded()
                except:
                    PrintWarning('OnLoaded call failed on info object %s:\n' % (info.name))
                    traceback.print_exc()
                    del dblist[k][info.name]
        
        # Now say we are loaded
        gp.loaded = True
        gp.loadedonce = True
    except ImportError:
        PrintWarning('Failed to load game package %s\n' % (package_name))
        traceback.print_exc()
        return
        
    # Change callbacks
    responses = gamepackageloaded.send_robust(None, packagename=package_name)
    for r in responses:
        if isinstance(r[1], Exception):
            PrintWarning('Error in receiver %s (module: %s): %s\n' % (r[0], r[0].__module__, r[1]))
        
    # Inform clients
    if isserver and informclient and srcmgr.levelinit is True:
        ClientLoadPackage(package_name)
            
    DevMsg(1, '%s: Loaded gamepackage %s in %f seconds\n' % ('Client' if isclient else 'Server', package_name, loadtimeone + (time.time() - startmeasuretime)))


def UnLoadGamePackage(package_name, informclient=True):
    """ Unloads a game package. This means all the units, 
        abilities, gamerules, etc will not show up anymore.
        It does not delete the references or anything. """
    additional_unloads = set()
    # Check if the package is already not loaded
    try:
        if dbgamepackages[package_name].loaded == False:
            PrintWarning('Game package %s is not loaded\n' % package_name)
            return additional_unloads
    except KeyError:
        PrintWarning('Game package %s is not loaded\n' % package_name)
        return additional_unloads  # Doesn't exist, so not loaded
        
    # Unload dependencies
    for gp in dbgamepackages.keys():
        if gp == package_name:
            continue
        if dbgamepackages[gp].loaded and package_name in dbgamepackages[gp].dependencies:
            additional_unloads.add(gp)
            additional_unloads |= UnLoadGamePackage(gp, False)  
        
    # Unload the package itself
    try:
        gp = dbgamepackages[package_name]
        
        for k, v in gp.db.items():
            # Remove abilities/factions/units from the dbs
            for k2, info in v.items():
                try:
                    info.OnUnLoaded()
                except:
                    PrintWarning('OnUnLoaded call failed on info object %s:\n' % (info.name))
                    traceback.print_exc()
                del dblist[k][info.name]

        # Call unload method
        if not gp.script_path and hasattr(sys.modules[package_name], 'UnloadGame'):
            sys.modules[package_name].UnloadGame(gp=gp)
        gp.loaded = False
    except:
        PrintWarning('Failed to unload game package %s\n' % (package_name))
        traceback.print_exc()  
        
    # Dispatch callbacks
    responses = gamepackageunloaded.send_robust(None, packagename=package_name)
    for r in responses:
        if isinstance(r[1], Exception):
            PrintWarning('Error in receiver %s (module: %s): %s\n' % (r[0], r[0].__module__, r[1]))
            
    # Inform clients
    if isserver and informclient and srcmgr.levelinit == True:
        ClientUnloadPackage(package_name)
    return additional_unloads


def GetDependencies(package_name): 
    dependencies = set()
    for gp in dbgamepackages.keys():
        if gp == package_name:
            continue
        if package_name in dbgamepackages[gp].dependencies:
            dependencies.add(gp)
            dependencies |= GetDependencies(gp)  
    return dependencies


def ReLoadGamePackageInternal(package_name):
    gp = dbgamepackages[package_name]
    
    # Unload myself (also unloads the dependencies)
    loaded = gp.loaded
    loadedonce = gp.loadedonce

    loadeddep = UnLoadGamePackage(package_name, False)
    deps = GetDependencies(package_name)
    
    # Reload myself
    try:
        if not gp.script_path:
            imp.reload(sys.modules[package_name])
        
            # Bind to console space for easy usage with spy/cpy commands
            setattr(consolespace, package_name, sys.modules[package_name])
        
        gp = dbgamepackages[package_name] # Gamepackage becomes registered again, get new instance
        gp.loadedonce = loadedonce
        if not gp.script_path and hasattr(sys.modules[package_name], 'LoadGame'): # Call load game to ensure registering the modules
            sys.modules[package_name].LoadGame(gp=gp)
        if not gp.script_path and hasattr(sys.modules[package_name], 'UnloadGame'): # Call unload in case in expects that after a load
            sys.modules[package_name].UnloadGame(gp=gp)
            
        # Do reloads
        if gp.modules:
            GPImportModules(package_name, gp.modules)
            GPReloadModules(package_name, gp.modules)
                
        if not gp.script_path and hasattr(sys.modules[package_name], 'ReloadGame'):
            sys.modules[package_name].ReloadGame(gp=gp)
    except:
        PrintWarning("Failed to reload game package %s\n" % (package_name))
        raise   
        
    # Reload dependencies
    for gpdep in deps:
        if not dbgamepackages[gpdep].loadedonce:
            continue
        ReLoadGamePackageInternal(gpdep)
        
    # Load this package
    if loaded:
        LoadGamePackage(package_name)
        # Load the deps that were loaded
        for gpdep in loadeddep:
            LoadGamePackage(gpdep)


def ReLoadGamePackage(package_name):
    """ For developing. NOTE: it only reloads the package partly and is maintained manually """
    deps = GetDependencies(package_name)
    
    active_gamerules = None
    oldtechnodes = []
    
    # The following could fail if one of the shutdown functions contains an error.
    # Reload regardless if this fails!
    try:
        # Get ref to all old tech nodes
        for name, info in dblist['abilities'].items():
            oldtechnodes.append(info.techinfo)
            
        # In case the package we are reloading is not loaded yet, load it and keep it loaded (for convenience).
        if not dbgamepackages[package_name].loaded:
            LoadGamePackage(package_name, False)
        
        # Make sure the gamepackage + dependencies were at least one time loaded
        for gp in deps:
            if not dbgamepackages[gp].loadedonce:
                continue
            if not dbgamepackages[gp].loaded:
                LoadGamePackage(gp, False)
                UnLoadGamePackage(gp, False)
                
        # If the current gamerules is in one of the packages of the dependencies, then clear gamerules
        from core.gamerules import ClearGamerules, SetGamerules
        if GameRules():
            try:
                modname = dblist['gamerules'][GameRules().info.name].modname.split('.')[0]
                if modname in deps or modname == package_name:
                    active_gamerules = GameRules().info.name
                    ClearGamerules()
            except KeyError:    # Might happen after a failed reload. Remember active gamerules after a failed reload? Otherwise we have no gamerules.
                pass
                
        # Make sure the hud is destroyed
        if isclient:
            from core.factions import DestroyHud
            DestroyHud()
    except:
        traceback.print_exc()
            
    # Do the reloading
    ReLoadGamePackageInternal(package_name)
    
    # Inform clients ( before reactivating the gamerules, because the gamerules sends a message to the client )
    if isserver and srcmgr.levelinit is True:
        ClientReloadPackage(package_name)
        
    # Reactivate the gamerules if it was loaded
    if isserver and active_gamerules != None:
        print('Resetting active gamerules...')
        SetGamerules(active_gamerules)
        
    # Figure out if the player class entity got reloaded. In that case we should respawn the player.
    if isserver:
        classes = GetClassesForGamepackage(package_name)
        for d in deps: classes |= GetClassesForGamepackage(d)
        
        for player in UTIL_GetPlayers():
            if player.GetClassname() in classes:
                RespawnPlayer(player, player.GetClassname())
    
    if isserver:
        # Restore all tech
        from core.abilities import GetTechNode
        for otninfo in oldtechnodes:
            for o, otn in otninfo.items():
                tn = GetTechNode(otn.name, o)
                if not tn:
                   continue
                tn.available = otn.available
                tn.techenabled = otn.techenabled
                tn.showonunavailable = otn.showonunavailable
                tn.successorability = otn.successorability
    
    if isclient:
        # Restore hud
        from core.factions import CreateHud
        CreateHud(CBasePlayer.GetLocalPlayer().GetFaction())


#
# Methods for making the client load the game packages
#
@usermessage()
def ClientLoadPackage(packagename, **kwargs):
    LoadGamePackage(packagename)


@usermessage()
def ClientUnloadPackage(packagename, **kwargs):
    UnLoadGamePackage(packagename)


@usermessage()
def ClientReloadPackage(packagename, **kwargs):
    ReLoadGamePackage(packagename)


@usermessage_shared()
def ReloadParticlesPackage(package_name, **kwargs):
    particles = dbgamepackages[package_name].particles
    if particles:
        [ReadParticleConfigFile(p) for p in particles]
        DecommitTempMemory()
    else:
        PrintWarning("No particles for game package %s\n" % (package_name))


if isserver:
    def _ClientActive(player):
        """ Inform client about all packages that need to be imported """  
        filter = CSingleUserRecipientFilter(player)
        filter.MakeReliable()
        for package in dbgamepackages.values():
            if package.loaded:
                ClientLoadPackage(package.name, filter=filter)
                
    def _ApplyGameSettings(kv):
        """ Called by matchmaking code to apply game settings.

            Args:
                kv (dict): contains the game settings.

            Returns (bool): True to indicate game settings have been applied. Returning False will fallback to the
                            default behavior.
        """
        settings = kv
        
        # First try each game package's ApplyGameSettings method
        for name, package in dbgamepackages.items():
            if name not in sys.modules:
                continue
            
            try:
                ApplyGameSettings = getattr(sys.modules[name], 'ApplyGameSettings', None)
                if ApplyGameSettings is not None and ApplyGameSettings(settings):
                    # At this point, gamerules have been set. Make sure the game server state is ingame.
                    if matchmaking.GetWarsGameServerState() == matchmaking.k_EGameServer_StartingGame:
                        matchmaking.SetWarsGameServerState(matchmaking.k_EGameServer_InGame)
                    return True
            except:
                traceback.print_exc()
                
        # Check loaded gamerules
        game = kv.get('game', None)
        if game:
            mode = game.get('mode', None)
            mapname = game.get('mission', None)
            if mode and mapname:
                for rulesinfo in dblist['gamerules'].values():
                    if rulesinfo.name == mode:
                        # Setup the mode for the next loaded map
                        from core.gamerules import SetNextLevelGamerules
                        SetNextLevelGamerules(mode, gamedata=kv)
                        
                        # Load the map
                        mapcommand = kv.get('map', {}).get('mapcommand', 'map')
                        engine.ServerCommand('%s %s sdk reserved\n' % (mapcommand, mapname))
                        
                        return True
                
        return False

#        
# The commands to load and unload a game package
#
if isserver:
    @concommand('load_gamepackage', 'Load a game package', completionfunc=AutoCompletion(lambda: dbgamepackages.keys()))
    def cc_load_gamepackage(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        LoadGamePackage(args[1])

    @concommand('unload_gamepackage', 'Unload a game package', completionfunc=AutoCompletion(lambda: dbgamepackages.keys()))
    def cc_unload_gamepackage(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        UnLoadGamePackage(args[1])
    
    @concommand('reload_gamepackage', 'Reload a game package', completionfunc=AutoCompletion(lambda: dbgamepackages.keys()))
    def cc_reload_gamepackage(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        ReLoadGamePackage(args[1])
        
    @concommand('reload_gamepackage_particles', 'Reload particle systems of package', completionfunc=AutoCompletion(lambda: dbgamepackages.keys()))
    def cc_reload_gamepackage_particles(args):
        if not UTIL_IsCommandIssuedByServerAdmin():
            return
        ReloadParticlesPackage(args[1])
        
    
    # Useful game package related commands
    def GetClassesForGamepackage(packagename):
        entities = GetAllClassnames()
        classes = set()
        
        for clsname in entities:
            cls = GetClassByClassname(clsname)
            if not cls:
                continue
                
            modname = cls.__module__.split('.')[0]
            
            if modname != packagename:
                continue
            
            classes.add(clsname)
        
        return classes

    @concommand('wars_pkg_remove_ents_all', 'Removes all units on the map belonging to the specified game package', FCVAR_CHEAT,
                completionfunc=AutoCompletion(lambda: dbgamepackages.keys()))
    def cc_wars_pkg_remove_ents_all(args):
        """ Removes all entities belonging to the specified game package.
        """
        if len(args) < 2:
            print("Removes all entities of the specified type\n\tArguments:   {entity_name} / {class_name}")
        else:
            # Build list of classnames
            for i in range(1, len(args)): 
                try:
                    pkg = dbgamepackages[args[i]]
                except KeyError:
                    print('Invalid package name %s' % (args[i]))
                    continue

                classes = set()
                for info in pkg.db['units'].values():
                    classes.add(info.cls_name)

                # Now iterate all entities and remove
                # Otherwise remove based on name or classname
                count = 0
                total = 0
                ent = entlist.FirstEnt()
                while ent != None:
                    total += 1
                    if ent.GetClassname() in classes:
                        UTIL_Remove(ent)
                        count += 1
                    ent = entlist.NextEnt(ent)
                    
                if count:
                    print("Removed %d out of %d entities from classes of game package %s\n" % (count, total, args[1]))
                else:
                    print("No entities for game package %s found (total ents %d).\n" % (args[1], total))
                    
    @concommand('wars_print_registered', 'Prints registered things', FCVAR_CHEAT,
                completionfunc=AutoCompletion(lambda: dblist.keys()))
    def cc_wars_print_registered(args):
        try:
            component = args[1]
        except IndexError:
            print('Invalid component')
            return
            
        if component not in dblist:
            print('Invalid component %s' % (component))
            return
        register = dblist[component]
        
        for k, v in register.items():
            sourcelines, startlinenumber = inspect.getsourcelines(v)
            print('Name: %s' % k)
            print('\t%s' % (inspect.getsourcefile(v)))
            print('\t%s: %s' % (startlinenumber, sourcelines[0].rstrip()))
            print('')
            
    @concommand('wars_gameserver_steamid')
    def cc_wars_gameserver_steamid(args):
        from steam import steamgameserverapicontext
        print(steamgameserverapicontext.SteamGameServer().GetSteamID())

# Build game package list on import
BuildGamePackageList()
