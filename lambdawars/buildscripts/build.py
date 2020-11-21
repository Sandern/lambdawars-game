#!/usr/bin/env python3
'''
Build script for Lambda Wars
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

pak_configuration = [
    {
        'root': 'platform',
        'folders': [
            'admin',
            'demo',
            'friends',
            'materials/debug',
            'materials/engine',
            'materials/vgui',
            'resource',
            'scripts',
            'servers',
        ],
        'files': [],
        'exclude': [
            'admin/admin_', # *.txt
            'admin/server_', # *.txt
            'admin/game_ready.wav',
            'admin/helpfile.vdf',
            'admin/helpfile_adminmod.vdf',
            'admin/helpfile_cstrike.vdf',
            'admin/hlds_logo.tga',
            'admin/game_ready.wav',
            'admin/mainserverconfig.vdf',
            'demo/animationdemo.vas',
            'friends/friend_join.wav',
            'friends/friend_online.wav',
            'friends/message.wav',
            'friends/servers.vdf',
            'friends/icon_', # *.tga
            'friends/trackerui_', # *.txt
            'resource/dmecontrols_english.txt',
            'resource/toolactbusy_english.txt',
            'resource/toolpet_english.txt',
            'resource/toolshared_english.txt',
            'resource/platform_', # *.txt
            'resource/icon_', # *.tga
            'resource/valve_logo.tga',
            'resource/vgui_', # *.txt
            'resource/warning.wav',
            'scripts/plugin_animations.txt',
            'scripts/preload_xbox.xsc',
            'servers/game_ready.wav',
            'servers/icon_', # *.tga
            'servers/regions.vdf',
            'servers/serverbrowser_', # *.txt
        ],
    },
    {
        'root': 'swarm_base',
        'folders': [
            'materials',
            'models',
            'particles',
            'resource',
        ],
        'files': [],
        'exclude': [
            'resource/chat_english.txt',
            'resource/closecaption_english.dat',
            'resource/closecaption_english.txt',
            'resource/halflife2.vfont',
            'resource/hl2crosshairs.vfont',
            'resource/hl2ep2.vfont',
            'resource/valve_english.txt',
        ],
    },
    {
        'root': 'swarm',
        'folders': [
            'materials',
            'models',
            'particles',
            'resource',
            'sound',
        ],
        'files': [],
        'exclude': [],
    },
    {
        'root': 'lambdawars',
        'folders': [
            'particles', 
            'materials', 
            'models',
            'scenes',
            'resource/ui',
            'sound',
            'python',
        ],
        'files': [
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
        ],
        'exclude': [
            'python/autorun_once',
            'python/ClientDLLs',
            'python/DLLs',
            'python/docs',
            'python/docsclient',
            'python/example',
            'python/tutorial',
            'python/pythonlib_dir.vpk',
        ],
    }
]

# Folders to copy
copyfolders = [
    'bin',
    'platform',

    'swarm_base',
    'swarm',

    'lambdawars/bin', 
    'lambdawars/cfg', 
    'lambdawars/materials',
    'lambdawars/maps',
    'lambdawars/media',
    'lambdawars/models',
    'lambdawars/particles',
    'lambdawars/python', 
    'lambdawars/resource', 
    'lambdawars/scripts',
    'lambdawars/scenes',
    'lambdawars/sound',
    'lambdawars/shaders',
    'lambdawars/ui',
]
        
# Extensions to ignore
ignoreext = ['.git', # Git
             '.pdb', '.log', '.map', '.log', # Bin
             '.tga', '.xcf', '.psd', # Materials
             '.pyc', '.info', # Python
             '.xls', '.xlsx', # Other
] 
            
# Paths to ignore
fullpathignore = [
    # SDK
    'bin/vpk.exe',

    # For PyCharm/Visual Studio Python Tools support
    'lambdawars/bin/python.exe',
    'lambdawars/bin/pythonw.exe',

    'lambdawars/models/.hammer.mdlcache',
    'lambdawars/materials/vgui/webview',
    
    'lambdawars/ui/development-bundle',
    'lambdawars/ui/RGraph',
    
    'lambdawars/cfg/config.cfg',
    'lambdawars/cfg/config_fps.cfg',
    'lambdawars/cfg/config_rts.cfg',
    'lambdawars/cfg/pet.txt',
    'lambdawars/cfg/video.txt',
    'lambdawars/cfg/videoext.txt',
    
    # Maps
    'lambdawars/maps/or_test',
    'lambdawars/maps/flowtest',
    'lambdawars/maps/benchmark',
    'lambdawars/maps/hlw_warehouse',
    'lambdawars/maps/or_trapped_v2',
    'lambdawars/maps/sp_testmission',
    'lambdawars/maps/sp_enttest_map',
    'lambdawars/maps/sp_training',
    'lambdawars/maps/unittest1',
    'lambdawars/maps/hlw_battlemounds',
    
    # Sounds
    'lambdawars/sound/keeper',
    
    # Skip sqlite Python module. Triggering a false positive on some crap scanners.
    'lambdawars/python/DLLs/_sqlite3.pyd',
    'lambdawars/python/DLLs/sqlite3.dll',
    'lambdawars/python/ClientDLLs/_sqlite3.pyd',
    'lambdawars/python/ClientDLLs/sqlite3.dll',
]

# Files to rename
renamefiles = [
]

replacements = [
]

copyfiles = [
    'lambdawars.exe',

    'lambdawars/GameInfo.txt',
    'lambdawars/readme.txt',
    'lambdawars/changelog.txt',
    'lambdawars/lambdawars.fgd',
    'lambdawars/steam.inf',
    'lambdawars/swarmkeepermaps.txt',
    'lambdawars/detail.vbsp',
    'lambdawars/host.txt',
    'lambdawars/motd.txt',
    'lambdawars/maplist.txt',
    'lambdawars/lobbymapinfo_default.cache',
    'lambdawars/icon.ico',
    'lambdawars/icon.tga',
    'lambdawars/icon_big.tga',
    'lambdawars/whitelist.cfg',
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
    
def ListVPKFiles(path, outputset, exclude):
    pathignoreset = set(map(lambda x: os.path.normcase(os.path.normpath(os.path.abspath(x.lower()))), exclude))
    
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
    mappath = os.path.join(srcpath, 'lambdawars/maplist.txt')
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
    mappath = os.path.join(srcpath, 'lambdawars/maps')
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
            
def BuildPostProcess(dstpath, buildnumber):
    # Post process the GameInfo.txt file
    # Replace Dev name with Public name
    gameinfopath = os.path.join(dstpath, 'lambdawars/GameInfo.txt')
    with open(gameinfopath, 'r', encoding='UTF-8') as fp:
        content = fp.read()
    content = content.replace("Lambda Wars Dev", "Lambda Wars")
    with open(gameinfopath, 'w', encoding='UTF-8') as fp:
        fp.write(content)
        
    if buildnumber:
        # Update steam.inf with the build number
        foundClientServerVersion = 0
        foundPathVersion = False
        steaminfpath = os.path.join(dstpath, 'lambdawars/steam.inf')
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

def BuildVPKs(srcpath, dstpath):
    for config in pak_configuration:
        BuildVPK(config, srcpath, dstpath)
        
def BuildVPK(config, srcpath, dstpath):
    out_folder = os.path.join(dstpath, config['root'])
    pak_list_name = 'paklist_%s.txt' % (config['root'])

    os.chdir(out_folder)
    
    # Create pak script
    pakfilesargs = {
        'srcpath': srcpath,
        'outfolder': out_folder,
        'curfolder': os.path.join(srcpath, 'lambdawars/buildscripts'), 
        'delcmd': 'del pak*.vpk',
        'pak_list_name': 'pak_list_name',
    }
    pakfilesbat = '''
    PATH=PATH;"%(srcpath)s/bin/"
    cd %(outfolder)s
    %(delcmd)s
    vpk.exe -M a pak01 "@%(curfolder)s/%(pak_list_name)s"
    ''' % pakfilesargs

    pakfilescmd = os.path.join(srcpath, 'lambdawars/buildscripts', 'pakfiles_%s.bat' % (config['root']))
    with open(pakfilescmd, 'wb') as fp:
        fp.write(bytes(pakfilesbat, 'UTF-8'))

    # Create pak list
    print('Creating %s' % pak_list_name, flush=True)
    pakset = list()
    for folder in config['folders']:
        ListVPKFiles(os.path.join(out_folder, folder), pakset, config['exclude'])
         
    with open(os.path.join(srcpath, 'lambdawars/buildscripts', pak_list_name), 'wt') as fp:
        for ps in pakset:
            fp.write('%s\n' % (ps.split(out_folder, 1)[1][1:]))
        for filename in config['files']:
            fp.write(filename+'\n')

    # Create vpk
    print('Creating vpk pak files', flush=True)
    subprocess.call([pakfilescmd])

    # Delete old...
    print('Removed pakked files', flush=True)
    for path in pakset:
        os.remove(path)
    for folder in config['folders']:
        RemoveEmptyFolders(folder)
    for filename in config['files']:
        os.remove(os.path.join(out_folder, filename))
        
def BuildFinalize(srcpath, dstpath):
    # Create Build exec script
    with open(os.path.join(dstpath, 'lambdawars/cfg/buildexec.cfg'), 'wt') as fp:
        fp.write(buildexec_template % {'loadmapscmds' : ''})
    
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
        
def MakeClientRelease(srcpath, dstpath, scriptspath=None, appid=None, depotid=None, gamerevision=None, buildnumber=None):
    srcpath = os.path.abspath(srcpath)
    dstpath = os.path.abspath(dstpath)
    if scriptspath:
        scriptspath = os.path.abspath(scriptspath)
    
    if not os.path.exists(srcpath):
        raise Exception('Source path %s does not exist!' % (srcpath))
        
    BuildCopyFiles(srcpath, dstpath)
    BuildPostProcess(dstpath, buildnumber)
    if shouldpakfiles:
        BuildVPKs(srcpath, dstpath)
    if gamerevision:
        with open(os.path.join(dstpath, 'lambdawars/gamerevision'), 'wt') as fp:
            fp.write(gamerevision)
    if scriptspath and appid and depotid:
        WriteDeployScripts(scriptspath, appid, depotid, gamerevision, buildnumber)
    BuildFinalize(srcpath, dstpath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lambda Wars Build script')
    parser.add_argument('--dstpath', help='Build Destination path', required=True)
    parser.add_argument('--srcpath', help='Build Source path', required=True)
    parser.add_argument('--scriptspath', help='Deploy output scripts paths')
    parser.add_argument('--appid', help='Deploy app id', type=int)
    parser.add_argument('--depotid', help='Deploy depot id', type=int)
    parser.add_argument('--gamerevision', help='The revision of this game')
    parser.add_argument('--buildnumber', help='The build number')
    args = parser.parse_args()
    
    if shouldpakfiles:
        vpkpath = os.path.join(args.srcpath, 'bin/vpk.exe')
        if not os.path.exists(vpkpath):
            print('Could not find %s. Please check src files.' % (vpkpath))
            sys.exit(-1)
            
    print('Running Lambda Wars Build script', flush=True)
    
    MakeClientRelease(args.srcpath, args.dstpath, args.scriptspath, args.appid, args.depotid, args.gamerevision, args.buildnumber)

    