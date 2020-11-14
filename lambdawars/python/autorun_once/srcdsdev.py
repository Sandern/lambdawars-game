''' 
Registers a periodic check to see if the server should restarted.
The server restarter is responsible for updating the developer build.
'''
import srcmgr
from srcbuiltins import RegisterTickMethod
from gameinterface import engine
from utils import UTIL_GetPlayers

import contextlib
try:
    import urllib, urllib.request, urllib.error, urllib.parse
    import xml.etree.ElementTree as ET
    import socket
except ImportError:
    urllib = None
    ET = None
    socket = None
    
def TestShouldTestRevisionTick():
    # Don't do this when there are players connected
    if len(UTIL_GetPlayers()) > 0:
        return
        
    CheckRemoteRevision()
    
def CheckRemoteRevision():
    ''' Intended for dedicated servers running the developers build.
        Checks if our current revision matches the remote revision.
        Exists the game, so the server gets restarted and updated.
    '''
    #print('srcds: Checking for latest revision...')
    
    url = 'http://svn.lambdawars.com/svninfo.php'
    try:
        with contextlib.closing(urllib.request.urlopen(url, timeout=2.5)) as fp:
            content = fp.read()
    except urllib.error.URLError as e:
        PrintWarning('CheckRemoteRevision: failed to get latest svn info. Reason: %s\n' % (e.reason))
        return # Try again next tick
    except socket.timeout:
        PrintWarning('CheckRemoteRevision: failed to get latest svn info (timed out)\n')
        return # Try again next tick
    except socket.error as msg:
        PrintWarning('CheckRemoteRevision: failed to get latest svn info. Reason: %s\n' % (msg))
        return # Try again next tick
        
    root = ET.fromstring(content)
    commit = root.find('./entry/commit')
    if commit is None:
        PrintWarning('CheckRemoteRevision: could not find commit entry in: \n%s\n' % (content))
        return
        
    revision = commit.get('revision')
    latestversion = 'SVN-%s' % (revision)
    if srcmgr.DEVVERSION != latestversion:
        print('CURRENT REVISION %s does not match latest revision %s. Restarting server...' % (srcmgr.DEVVERSION, latestversion))
        engine.ServerCommand('exit\n')
        
if isserver and engine.IsDedicatedServer() and srcmgr.DEVVERSION != None:
    if urllib and ET and socket:
        # Note: tick method is only called when a map is loaded
        print('Automatically restarting server latest revision changes is ON...')
        RegisterTickMethod(TestShouldTestRevisionTick, 300.0, True, True) 
    else:
        PrintWarning('Cannot automatically check for latest revision because could not import urllib or xml.etree.ElementTree or socket.\n')