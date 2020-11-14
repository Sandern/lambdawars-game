#!/usr/bin/env python3
'''
Build script for Lambda Wars

Required installed Apps:
- 630 (Alien Swarm)
- 640 (Alien Swarm SDK)
'''

import os
import shutil 
import fnmatch
import sys
import filecmp
import subprocess
import glob
import argparse
import time

modfolder = 'lambdawars'
pathbasefolder = None 

# Deploy scripts templates
appbuild_template = '''"appbuild"
{
	"appid"	"%(appid)d"
	"desc" "%(description)s" // description for this build
	"buildoutput" "output\" // build output folder for .log, .csm & .csd files, relative to location of this file
	"contentroot" "..\..\contentdev\" // root content folder, relative to location of this file
	"setlive"	"dev" // branch to set live after successful build, non if empty
	"preview" "0" // to enable preview builds
	"local"	""	// set to flie path of local content server 
	
	"depots"
	{
		"%(depotid)d" "depot_build_%(depotid)d.vdf"
	}
}'''

depotbuild_template = '''"DepotBuildConfig"
{
	// Set your assigned depot ID here
	"DepotID" "%(depotid)d"

	// Set a root for all content.
	// All relative paths specified below (LocalPath in FileMapping entries, and FileExclusion paths)
	// will be resolved relative to this root.
	// If you don't define ContentRoot, then it will be assumed to be
	// the location of this script file, which probably isn't what you want
	"ContentRoot"	"..\contentdev\"

	// include all files recursivley
  "FileMapping"
  {
  	// This can be a full path, or a path relative to ContentRoot
    "LocalPath" "*"
    
    // This is a path relative to the install folder of your game
    "DepotPath" "."
    
    // If LocalPath contains wildcards, setting this means that all
    // matching files within subdirectories of LocalPath will also
    // be included.
    "recursive" "1"
  }

	// This can be a full path, or a path relative to ContentRoot
  "FileExclusion" "*.pdb" // Exclude symbol files
  "FileExclusion" "*.pyc" // Exclude pyc files
  "FileExclusion" "*.pyo" // Exclude pyc files
  "FileExclusion" "*.mdmp" // Exclude mdmp files (crash on running "exit" from build exec script...)
  "FileExclusion" "__pycache__" // Exclude pycache folders
  
}'''

# Pak settings
shouldpakfiles = True
pakfolders = [
    'particles', 
    'materials', 
    'models',
    'scenes',
    'resource/ui',
    'sound',
    'python',
]

excludepakpaths = [
    'python/autorun_once',
    'python/ClientDLLs',
    'python/DLLs',
    'python/docs',
    'python/docsclient',
    'python/example',
    'python/tutorial',
    'python/pythonlib_dir.vpk',
    'balance_sheet.xls',
]

extrapakfiles = [
    'lobbymapinfo_default.cache',
    'scripts/hudlayout.res',
    'scripts/mod_lessons.txt',
    'scripts/mod_textures.txt',
    'scripts/game_sounds_manifest.txt',
    'scripts/game_sounds_weapons.txt',
    'scripts/game_sounds_keeper.txt',
    'scripts/game_sounds_asw_misc.txt',
    'scripts/kb_act.lst',
    'scripts/kb_act_config_rts.lst',
    'scripts/kb_def.lst',
    'scripts/kb_keys.lst',
    'resource/basemodui_english.txt',
    'resource/basemodui_scheme.res',
    'resource/gameui_english.txt',
    'resource/ModEvents.res',
    'resource/SourceScheme.res',
    'resource/spectatormenu.res',
    'resource/spectatormodes.res',
    'resource/optionssubkeyboard.res',
]

# Folders to copy
copyfolders = [
    'bin', 
    'cfg', 
    'materials',
    'maps',
    'media',
    'models',
    'particles',
    'python', 
    'resource', 
    'scripts',
    'scenes',
    'sound',
    'shaders',
    'ui',
]
        
# Extensions to ignore
ignoreext = ['.svn', # SVN
             '.pdb', '.log', '.map', '.log', # Bin
             '.tga', '.xcf', '.psd', # Materials
             '.pyc', '.info', # Python
             '.xls', '.xlsx', # Other
] 
            
# Paths to ignore
fullpathignore = [
    # For PyCharm/Visual Studio Python Tools support
    'bin/python.exe',
    'bin/pythonw.exe',

    'models/.hammer.mdlcache',
    'materials/vgui/webview',
    
    'ui/development-bundle',
    'ui/RGraph',
    
    'cfg/config.cfg',
    'cfg/config_fps.cfg',
    'cfg/config_rts.cfg',
    'cfg/pet.txt',
    'cfg/video.txt',
    'cfg/videoext.txt',
    
    # Maps
    'maps/or_test',
    'maps/flowtest',
    'maps/benchmark',
    'maps/hlw_warehouse',
    'maps/or_trapped_v2',
    'maps/sp_testmission',
    'maps/sp_enttest_map',
    'maps/sp_training',
    'maps/unittest1',
    'maps/hlw_battlemounds',
    
    # Sounds
    'sound/keeper',
    
    # Skip sqlite Python module. Triggering a false positive on some crap scanners.
    'python/DLLs/_sqlite3.pyd',
    'python/DLLs/sqlite3.dll',
    'python/ClientDLLs/_sqlite3.pyd',
    'python/ClientDLLs/sqlite3.dll',
]

# Files to rename
renamefiles = [
]

replacements = [
]

copyfiles = [
    'GameInfo.txt',
    'readme.txt',
    'changelog.txt',
    'lambdawars.fgd',
    'steam.inf',
    'swarmkeepermaps.txt',
    'detail.vbsp',
    'host.txt',
    'motd.txt',
    'maplist.txt',
    'lobbymapinfo_default.cache',
    'icon.ico',
    'icon.tga',
    'icon_big.tga',
    'whitelist.cfg',
]

buildexec_template = '''
//con_logfile console.log
//snd_rebuildaudiocache;

%(loadmapscmds)s

exit;
'''

def RenameFiles(target_folder, rename_files):
    for f in rename_files:
        path = os.path.join(target_folder, f[0])
        renamepath = os.path.join(target_folder, f[1])
        try:
            os.rename(path, renamepath)
            print('Renamed %s' % (path), flush=True)
        except WindowsError:
            print('Skipped renaming %s' % (path), flush=True)
            
def DeleteAllOfPattern(target_folder, pattern):
    for root, dirs, files in os.walk(target_folder):
        for filename in fnmatch.filter(files, pattern):
            path = os.path.join(root, filename)
            os.remove(path)
            
def AddExtraFolder(extrafilesfolder, fullpathmodfolder):
    for root, dirs, files in os.walk(extrafilesfolder):
        for name in files:
            srcpath = os.path.join(root, name)
            try:
                realroot = root.split(extrafilesfolder+'\\', 1)[1]
            except IndexError:
                #continue
                realroot = ''
            targetpath = os.path.join(fullpathmodfolder, realroot, name)
            
            targetdir = os.path.dirname(targetpath)
            if not os.path.exists(targetdir):
                os.makedirs(targetdir)
            shutil.copyfile(srcpath, targetpath)
            
class IgnorePaths(object):
    def __init__(self, paths):
        super().__init__()
        
        self.ignorepaths = paths
        
    def StartsWithIgnore(self, testpath):
        testpath = testpath.lower()
        for p in self.ignorepaths:
            if testpath.startswith(p.lower()):
                return True
        return False

    def __call__(self, path, names):
        ignore = set()
        for name in names:
            for ext in ignoreext:
                if name.lower().endswith(ext):
                    ignore.add(name)
                    break
            fullpath = os.path.normpath(os.path.join(path, name))
            if fullpath in self.ignorepaths or self.StartsWithIgnore(fullpath):
                print('ignoring %s' % (fullpath), flush=True)
                ignore.add(name)
        return ignore
    
def ListVPKFiles(path, outputset):
    pathignoreset = set(map(lambda x: os.path.normcase(os.path.normpath(os.path.abspath(x.lower()))), excludepakpaths))
    
    for root, dirs, files in os.walk(path):
        for name in files:
            fullpath = os.path.normcase(os.path.normpath(os.path.join(root, name)))
            skip = False
            for path in pathignoreset:
                if fullpath.lower().startswith(path):
                    #print('Ignoring path %s for vpk packing' % (fullpath))
                    skip = True
            if skip:
                continue
            outputset.append(os.path.join(root, name))
            
def ReadMapList(srcpath):
    maplist = []
    mappath = os.path.join(srcpath, 'maplist.txt')
    with open(mappath, 'r') as fp:
        for line in fp.readlines():
            mapname = line.strip().strip('"')
            maplist.append(mapname)
    return maplist
            
def BuildCopyFiles(srcpath, dstpath):
    # Clear old if any
    print('Removing old folder', flush=True)
    if os.path.exists(dstpath): 
        shutil.rmtree(dstpath)

    if not os.path.exists(dstpath):
        os.makedirs(dstpath)
        
    # Only include maps from maplist.txt
    maplist = ReadMapList(srcpath)
    ignoremapspaths = []
    mappath = os.path.join(srcpath, 'maps')
    for filename in os.listdir(mappath):
        mapname, ext = os.path.splitext(filename)
        if ext != '.bsp':
            continue
        if mapname not in maplist:
            ignoremapspaths.append('maps/%s' % (mapname))
    
    ignorefilelist = list(map(lambda path: os.path.normpath(os.path.join(srcpath, path)), fullpathignore+ignoremapspaths))
    
    # Only copy the folders we need
    print('Copying folders', flush=True)
    for folder in copyfolders:
        shutil.copytree(os.path.join(srcpath, folder), os.path.join(dstpath, folder), ignore=IgnorePaths(ignorefilelist))   
  
    print('Renaming files', flush=True)
    RenameFiles(dstpath, renamefiles)
    
    print('Copying single files', flush=True)
    for filename in copyfiles:
        shutil.copyfile(os.path.join(srcpath, filename), os.path.join(dstpath, filename))
        
    if os.path.exists('extrafiles'):
        print('Copying extra files', flush=True)
        for filename in os.listdir('extrafiles'):
            shutil.copyfile(os.path.join('extrafiles', filename), os.path.join(dstpath, filename))
        
    # Copy vpks from old build for incremental update
    # Not needed for Steam build.
    '''if pathbasefolder:
        print('Copying vpk files from release "%s" for incremental update' % (pathbasefolder))
        files = glob.glob(os.path.join(pathbasefolder, '*.vpk'))
        for path in files:
            print('Copying %s' %(path))
            shutil.copyfile(path, os.path.join(dstpath, os.path.basename(path)))'''
            
def BuildPostProcess(dstpath, buildnumber):
    # Post process the GameInfo.txt file
    # Replace Dev name with Public name
    gameinfopath = os.path.join(dstpath, 'GameInfo.txt')
    with open(gameinfopath, 'r', encoding='UTF-8') as fp:
        content = fp.read()
    content = content.replace("Lambda Wars Dev", "Lambda Wars")
    with open(gameinfopath, 'w', encoding='UTF-8') as fp:
        fp.write(content)
        
    if buildnumber:
        # Update steam.inf with the build number
        foundClientServerVersion = 0
        foundPathVersion = False
        steaminfpath = os.path.join(dstpath, 'steam.inf')
        with open(steaminfpath, 'r', encoding='UTF-8') as fp:
            content = fp.readlines()
        newcontent = []
        for line in content:
            key, value = line.strip().split('=')
            if key == 'ClientVersion' or key == 'ServerVersion':
                value = str(buildnumber)
                foundClientServerVersion += 1
            elif key == 'PatchVersion':
                value = '0.0.0.%s' % str(buildnumber)
                foundPathVersion = True
            newcontent.append('%s=%s' % (key, value))
        if foundClientServerVersion != 2:
            raise Exception('Could not find ClientVersion or ServerVersion key in steam.inf')
        if not foundPathVersion:
            raise Exception('Could not find PatchVersion key in steam.inf')
        with open(steaminfpath, 'w', encoding='UTF-8') as fp:
            fp.write('\n'.join(newcontent))
            
        
def RemoveEmptyFolders(path):
    if not os.path.isdir(path):
        return

    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                RemoveEmptyFolders(fullpath)

    # if folder empty, delete it
    files = os.listdir(path)
    if len(files) == 0:
        os.rmdir(path)
        
def BuildVPK(steampath, srcpath, dstpath):
    os.chdir(dstpath)
    
    # Create pak script
    pakfilesargs = {
        'steamapps' : os.path.join(steampath, 'SteamApps'),
        'outfolder' : dstpath, 
        'curfolder' : os.path.join(srcpath, 'buildscripts'), 
        'modfolder' : modfolder,
        'delcmd' : 'del pak*.vpk',
    }
    pakfilesbat = '''
    PATH=PATH;"%(steamapps)s/common/alien swarm/bin/"
    cd %(outfolder)s
    %(delcmd)s
    vpk.exe -M a pak01 "@%(curfolder)s/paklist.txt"
    ''' % pakfilesargs

    pakfilescmd = os.path.join(srcpath, 'buildscripts', 'pakfiles.bat')
    with open(pakfilescmd, 'wb') as fp:
        fp.write(bytes(pakfilesbat, 'UTF-8'))

    # Create pak list
    print('Creating paklist.txt', flush=True)
    pakset = list()
    for folder in pakfolders:
        ListVPKFiles(os.path.join(dstpath, folder), pakset)
         
    with open(os.path.join(srcpath, 'buildscripts', 'paklist.txt'), 'wt') as fp:
        for ps in pakset:
            fp.write('%s\n' % (ps.split(dstpath, 1)[1][1:]))
        for filename in extrapakfiles:
            fp.write(filename+'\n')

    # Create vpk
    print('Creating vpk pak files', flush=True)
    subprocess.call([pakfilescmd])

    # Delete old...
    print('Removed pakked files', flush=True)
    for path in pakset:
        os.remove(path)
    for folder in pakfolders:
        RemoveEmptyFolders(folder)
        #shutil.rmtree(os.path.join(dstpath, folder), ignore=IgnorePaths(excludepakpaths))
    for filename in extrapakfiles:
        os.remove(os.path.join(dstpath, filename))
        
def BuildFinalize(steampath, srcpath, dstpath):
    # Create Build exec script
    with open(os.path.join(dstpath, 'cfg', 'buildexec.cfg'), 'wt') as fp:
        fp.write(buildexec_template % {'loadmapscmds' : ''})

    # Change to destination and run build exec script
    if os.path.exists(os.path.join(dstpath, '..', 'srcds.exe')):
        print('Running Lambda Wars to generate sound cache and various...')
        os.chdir(os.path.join(dstpath, '..'))
        args = ['srcds.exe', '-game', 'lambdawars', '-textmode', '-console', '-windowed', '+exec', 'buildexec.cfg',
            #'-nosound', '-noipx', '-novid', '-nopreload', '-nojoy',
        ]
        p = subprocess.Popen(args)
        retcode = p.wait()
        #print('stdout: %s' % (p.stdout.read()))
        #print('stderr: %s' % (p.stderr.read()))
        print('retcode: %s' % (retcode))
    
    # Remove the following files
    os.chdir(dstpath)
    toremove = [
        'cfg/buildexec.cfg',
        'cfg/config.cfg',
        'cfg/config_fps.cfg',
        'cfg/server_blacklist.txt',
        'cfg/video.bak',
        'cfg/video.txt',
        'cfg/videodefaults.txt',
        'debug.log',
        'stats.txt',
        'cache',
        'mountlist.txt',
        'modelsounds.cache',
    ]
    for path in toremove:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            try:
                os.remove(path)
            except OSError as err:
                print('Could not remove %s: %s' % (path, err))
                
def WriteDeployScripts(scriptspath, appid, depotid, gamerevision, buildnumber):
    appdeploypath = os.path.join(scriptspath, 'app_build_%d.vdf' % (appid))
    depotdeploypath = os.path.join(scriptspath, 'depot_build_%d.vdf' % (depotid))
    
    description = 'Lambda Wars'
    if gamerevision:
        description += ' revision %s' % (gamerevision)
    if buildnumber:
        description += ' build %s' % (buildnumber)
    
    args = {
        'appid' : appid,
        'depotid' : depotid,
        'description' : description,
    }
    
    print('Writing "%s"' % (appdeploypath))
    with open(appdeploypath, 'w') as fp:
        fp.write(appbuild_template  % args)
    print('Writing "%s"' % (depotdeploypath))
    with open(depotdeploypath, 'w') as fp:
        fp.write(depotbuild_template  % args)
        
def MakeClientRelease(steampath, srcpath, dstpath, scriptspath=None, appid=None, depotid=None, gamerevision=None, buildnumber=None):
    srcpath = os.path.abspath(srcpath)
    dstpath = os.path.abspath(dstpath)
    if scriptspath:
        scriptspath = os.path.abspath(scriptspath)
    
    if not os.path.exists(steampath):
        raise Exception('Steam path %s does not exist!' % (steampath))
    if not os.path.exists(srcpath):
        raise Exception('Source path %s does not exist!' % (srcpath))
        
    BuildCopyFiles(srcpath, dstpath)
    BuildPostProcess(dstpath, buildnumber)
    if shouldpakfiles:
        BuildVPK(steampath, srcpath, dstpath)
    if gamerevision:
        with open(os.path.join(dstpath, 'gamerevision'), 'wt') as fp:
            fp.write(gamerevision)
    if scriptspath and appid and depotid:
        WriteDeployScripts(scriptspath, appid, depotid, gamerevision, buildnumber)
    BuildFinalize(steampath, srcpath, dstpath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lambda Wars Build script')
    parser.add_argument('--steampath', help='Path to Steam', required=True)
    parser.add_argument('--dstpath', help='Build Destination path', required=True)
    parser.add_argument('--srcpath', help='Build Source path', required=True)
    parser.add_argument('--scriptspath', help='Deploy output scripts paths')
    parser.add_argument('--appid', help='Deploy app id', type=int)
    parser.add_argument('--depotid', help='Deploy depot id', type=int)
    parser.add_argument('--gamerevision', help='The revision of this game')
    parser.add_argument('--buildnumber', help='The build number')
    args = parser.parse_args()
    
    if shouldpakfiles:
        vpkpath = os.path.join(args.steampath, 'steamapps/common/alien swarm/bin/vpk.exe')
        if not os.path.exists(vpkpath):
            print('Could not find %s. Please verify steampath is set correctly and Alien Swarm SDK (App ID 640) is installed' % (vpkpath))
            sys.exit(-1)
            
    print('Running Lambda Wars Build script', flush=True)
    
    MakeClientRelease(args.steampath, args.srcpath, args.dstpath, args.scriptspath, args.appid, args.depotid, args.gamerevision, args.buildnumber)

    