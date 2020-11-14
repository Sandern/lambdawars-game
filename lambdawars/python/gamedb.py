from collections import defaultdict


class DBInfo(dict):
    """ Base definition class for all types of databases. Mainly here to assign a priority for the load order. """
    #: Parse priority. Can be used to ensure one list gets parsed before the other list.
    priority = 0

# Store for game packages
dbgamepackages = {}

# Store for active loaded game definitions
# Note a game package may override the definition of a dependency
dblist = defaultdict(lambda: DBInfo())

# Location of script defined game packages
scriptgamepackages_path = 'scripts/gamedefs'


class GamePackageInfo(object):
    """ Stores info about a game package """
    loaded = False
    #:  Used for determing if we need to reload (dev only)
    loadedonce = False
    #: In case the game package is defined in a script file
    script_path = None
    
    def __init__(self,
                 name,
                 dependencies=[],
                 particles=[],
                 modules=None,
                 script_path=None):
        super().__init__()
        self.name = name
        self.dependencies = dependencies
        self.particles = particles
        self.modules = modules
        self.db = defaultdict(lambda: DBInfo())
        self.script_path = script_path


#
# Register methods
#
def RegisterGamePackage(name,
                        dependencies=[],
                        particles=None,
                        modules=None,
                        script_path=None):
    """ Register a new game package.
        Call this in the __init__.py of your new game package.

        In your __init__.py you must implement the following methods:
        LoadGamePackage()
        UnloadGamePackage()
        ReloadGamePackage()

        Your gamepackage is imported on both the client and server side.
    """
    dbgamepackages[name] = GamePackageInfo(name=name,
                                           dependencies=list(dependencies),
                                           particles=particles,
                                           modules=modules,
                                           script_path=script_path)
    return dbgamepackages[name]
