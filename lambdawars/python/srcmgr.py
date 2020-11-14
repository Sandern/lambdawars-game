"""
Provides general information and intializes the Python side of the game.
"""
import sys
import gc
import os
import re
import pickle
import pkgutil
import traceback
import time
import imp

try:
    import sqlite3
except ImportError:
    DevMsg(1, 'srcmgr: sqlite3 missing, can not read svn entries\n')
    sqlite3 = None
    
import queue

from srcbuiltins import RegisterTickMethod
from gameinterface import engine, CommandLine
import filesystem as fs
from kvdict import LoadFileIntoDictionaries

# Global indicating the current version of Lambda Wars
# MACRO / MINOR / MICRO
VERSION = (2, 4, 0)
DEVVERSION = None

# Gameinfo
gameinfo = {}
steamappid = None
moddirectory = None

# Level related globals
levelname = ""
levelinit = False
levelpreinit = False

revisioninfopath = os.path.join(os.path.split(__file__)[0], 'srcmgr.info')
versioninfopath = os.path.join(os.path.split(__file__)[0], 'version.info')

def GetModDirectory():
    try:
        moddir = CommandLine().ParmValue("-game", CommandLine().ParmValue("-defaultgamedir", "hl2"))
        if '/' in moddir or '\\' in moddir:
            moddir = os.path.dirname(moddir)
    except UnicodeDecodeError:
        moddir = 'lambdawars'
    return moddir

def _Init():
    """ Initialize """
    global gameinfo, steamappid, moddirectory, DEVVERSION
    
    # Load gameinfo
    gameinfo = LoadFileIntoDictionaries('gameinfo.txt')
    steamappid = int(gameinfo['FileSystem']['SteamAppId'])
    
    # In the dev version, the game directory might be different
    moddirectory = GetModDirectory()
    if isclient:
        from vgui import localize
        if moddirectory != 'lambdawars':
            localize.AddFile("Resource/lambdawars_%language%.txt", "MOD", True)
        #localize.AddFile("Resource/lambdawars_ui_%language%.txt", "MOD", True)
        
    if isclient or engine.IsDedicatedServer():
        # In case of the developers/svn build, check the revision number
        # In the other case check the global version number
        # The current version is retrieved from the web.
        revision = get_svn_revision()
        if revision != 'SVN-unknown':
            DEVVERSION = revision
            soundrevision = get_svn_revision(startswith='sound')
            try:
                with open(revisioninfopath, 'rb') as fp:
                    oldrevision, oldsoundrevision = pickle.load(fp)
                if revision != oldrevision:
                    OnRevisionChanged(oldrevision, revision, oldsoundrevision, soundrevision)
            except (IOError, ValueError):
                OnRevisionChanged(None, revision, None, soundrevision)
                
            if CommandLine() and CommandLine().FindParm('-override_vpk') == 0:
                if isclient:
                    from vgui.notification import Notification
                    Notification('Specify -override_vpk', 
                        ('The developers build must be runned with the launch parameter "-override_vpk".\n')
                    )
                else:
                    PrintWarning('The developers build must be runned with the launch parameter "-override_vpk".\n')
        else:
            try:
                with open(versioninfopath, 'rb') as fp:
                    oldrversion = pickle.load(fp)
                if VERSION != oldrversion:
                    OnVersionChanged(oldrversion, VERSION)
            except IOError:
                OnVersionChanged(None, VERSION)
    else:
        # Grab revision
        revision = get_svn_revision()
        if revision != 'SVN-unknown':
            DEVVERSION = revision


# Source of this method: Django project (http://www.djangoproject.com/)
# Updated for TortoiseSVN 1.7 and higher
def get_svn_revision(path=None, startswith=None):
    """
    Returns the SVN revision in the form SVN-XXXX,
    where XXXX is the revision number.

    Returns SVN-unknown if anything goes wrong, such as an unexpected
    format of internal SVN files.

    If path is provided, it should be a directory whose SVN info you want to
    inspect. If it's not provided, this will use the root / package
    directory.
    """
    rev = None
    if path is None:
        path = '.'
    entries_path = '%s/.svn/entries' % path
    
    # 1.7 stores info in wc.db
    if sqlite3 and os.path.exists('.svn/wc.db'):
        con = sqlite3.connect('.svn/wc.db')
        cur = con.cursor()
        if startswith:
            rev = cur.execute("SELECT max(changed_revision) FROM NODES WHERE local_relpath like '%s%%'" % (startswith)).fetchall()[0][0]
        else:
            rev = cur.execute('SELECT max(revision) FROM NODES').fetchall()[0][0]
    else:
        try:
            with open(entries_path, 'r') as fp:
                entries = fp.read()
        except IOError:
            DevMsg(1, 'get_svn_revision: Failed to read %s\n' % (entries_path))
            entries = None
            
        if entries:
            # Versions >= 7 of the entries file are flat text.  The first line is
            # the version number. The next set of digits after 'dir' is the revision.
            if re.match('(\d+)', entries):
                rev_match = re.search('\d+\s+dir\s+(\d+)', entries)
                if rev_match:
                    rev = rev_match.groups()[0]
            # Older XML versions of the file specify revision as an attribute of
            # the first entries node.
            else:
                from xml.dom import minidom
                dom = minidom.parse(entries_path)
                rev = dom.getElementsByTagName('entry')[0].getAttribute('revision')

    if rev:
        return 'SVN-%s' % rev
    return 'SVN-unknown'


def RemoveJunkPycFiles(paths):
    paths = paths if type(paths) == list else [paths]
    
    starttime = time.time()
    for path in paths:
        try:
            for root, dirs, files in os.walk(path):
                for filename in files:
                    basefilename, ext = os.path.splitext(filename)
                    if ext == '.pyc' or ext == '.pyo':
                        fullpypath = os.path.normpath(os.path.join(root, filename))
                        if not os.path.exists(fullpypath):
                            print('Removing: %s' % fullpypath)
                            os.remove(fullpypath)
        except IOError:
            PrintWarning('RemoveJunkPycFiles: failed to remove junk pyc files\n')
    print('Finished removing junk pyc files in %f seconds' % (time.time() - starttime))


def OnRevisionChanged(oldrevision, revision, oldsoundrevision, soundrevision):
    """ Called when the revision changed. Deletes pyc files without py files """
    print('Revision number changed from %s to %s, performing checks...' % (oldrevision, revision))

    # Check if each .pyc file has a .py file. If that's not the case the .py file got deleted.
    # Then we can also remove the .pyc file.
    RemoveJunkPycFiles(['python'])

    # Write new revision number away
    with open(revisioninfopath, 'wb') as fp:
        pickle.dump((revision, soundrevision), fp)

def OnVersionChanged(oldversion, version):
    """ Called when the version changed. Deletes pyc files without py files """
    print('Version number changed from %s to %s, performing checks...' % (oldversion, version))
    
    # Check if each .pyc file has a .py file. If that's not the case the .py file got deleted.
    # Then we can also remove the .pyc file.
    RemoveJunkPycFiles('python')
    
    # Write new version number away
    with open(versioninfopath, 'wb') as fp:
        pickle.dump(version, fp)
    
# Dealing with threads
threadcallbacks = queue.Queue()
def DoThreadCallback(method, args):
    threadcallbacks.put((method, args))
    
def CheckThreadsCallbacks():
    while not threadcallbacks.empty():
        callback = threadcallbacks.get_nowait()
        if callback:
            try:
                callback[0](*callback[1])
            except:
                traceback.print_exc()
                
RegisterTickMethod(CheckThreadsCallbacks, 0.2)

# Level init and shutdown methods
def _LevelInitPreEntity(lvlname):
    global levelname, levelpreinit
    levelname = lvlname
    
    levelpreinit = True
    
def _LevelInitPostEntity():
    """ Called when all map entities are created.
    """
    global levelinit

    # Set level init to true
    levelinit = True
            
def _LevelShutdownPreEntity():
    """ Called before the entities are removed from the map.
        Dispatches related callbacks.
    """
    pass
    
def _LevelShutdownPostEntity():
    """ Called when all entities are removed.
        Dispatches related callbacks. """    
    global levelpreinit, levelinit, levelname

    # Put levelinit to false
    levelpreinit = False
    levelinit = False
    levelname = ""
   
    # Cleanup memory
    gc.collect()

# Temporary signal methods for c++
def _CheckReponses(responses):
    for r in responses:
        if isinstance(r[1], Exception):
            PrintWarning('Error in receiver %s (module: %s): \n%s' %
                (r[0], r[0].__module__, r[2]))
            
def _CallSignal(method, kwargs):
    _CheckReponses(method(**kwargs))

# Useful methods        
def VerifyIsClient():
    """ Throws an exception if this is not the client. To be used when importing modules. """
    if not isclient:
        raise ImportError('Cannot import this module on the server')
            
def VerifyIsServer():
    """ Throws an exception if this is not the client. To be used when importing modules. """
    if not isserver:
        raise ImportError('Cannot import this module on the client')

def ImportSubMods(mod):
    """ Import all sub modules for the specified module. """
    name = mod.__name__
    path = mod.__path__
    pathrel = []
    for v in path:
        pathrel.append(os.path.normpath(
            fs.FullPathToRelativePath(os.path.normpath(v), defaultvalue=v) if fs.IsAbsolutePath(v) else v
        ))
        
    for item in pkgutil.iter_modules(pathrel):
        submod = '%s.%s' % (name, item[1])
        try:
            __import__(submod)   
            sys.modules[submod]
        except:
            traceback.print_exc()

def ReloadSubMods(mod, exludelist=None):
    """ Reloads all sub modules for the specified module. """
    name = mod.__name__
    path = mod.__path__
    pathrel = []
    for v in path:
        pathrel.append(os.path.normpath(
            fs.FullPathToRelativePath(os.path.normpath(v)) if fs.IsAbsolutePath(v) else v
        ))
        
    for item in pkgutil.iter_modules(pathrel):
        submod = '%s.%s' % (name, item[1])
        try:
            __import__(submod)  # Might not be imported in the first place because the module is just added
            if not exludelist or submod not in exludelist:
                imp.reload(sys.modules[submod])
        except:
            traceback.print_exc()
