from core.units import UnitInfo
from core.buildings import WarsBuildingInfo
from core.units.info import dbunits
from core.abilities.info import dbabilities
from core.abilities import GetTechNode, SubMenu, AbilityMenuBase
from core.factions import dbfactions
from gameinterface import concommand
import filesystem as fs

import subprocess
import os

try:
    # just get sdk dir relative to path.
    SDKDIR = '../../%s/sourcesdk/bin/source2007/bin' % (os.environ['STEAMUSER'])
except KeyError:
    DevMsg(1, 'core.utils.GenerateImage: Couldn\'t retrieve STEAMUSER\n')
    SDKDIR = ''

# Code uses Image Magick to generate some simple transparent text images
# Get it from http://www.imagemagick.org/script/index.php
# Then either modify your PATH environ or add IMAGEMAGICK to your environment variables.
try:
    IMAGEMAGICKEXE = exectuable = os.environ['IMAGEMAGICK']
except KeyError:
    DevMsg(1, 'core.utils.GenerateImage: Set IMAGEMAGICK in your environ variables to the executable of Image Magick\n')
    IMAGEMAGICKEXE = 'convert.exe'
        
def GetOutput(stderr, stdout):
    stdout_output = list()
    while True:
        data = stdout.read()
        if not data:
            break
        stdout_output.append(data)
    stdout.close()
        
    stdout_output = ''.join(stdout_output)
    
    if not stderr.closed:
        stderr_output = list()
        while True:
            data = stderr.read()
            if not data:
                break
            stderr_output.append(data)
        stderr.close()
            
        if stderr_output:
            stderr_output = ''.join(stderr_output)
            
    return stderr_output, stdout_output
    
def Classify(info):
    if issubclass(info, WarsBuildingInfo):
        return 'buildings'
    if issubclass(info, UnitInfo):
        return 'units'
    return 'abilities'
        
def GenerateImage(info, targetfolder, targetoutputfolder, nosubcat=False):
    if not nosubcat:
        subcat = Classify(info)
    else:
        subcat = ''

    # Setup paths
    targetfolder = os.path.join(targetfolder, subcat)
    targetoutputfolder = os.path.join(targetoutputfolder, subcat)
    targetpath = os.path.join(targetfolder, info.name) # Intermediate path (i.e. materialsrc folder)
    targetoutputpath = os.path.join(targetoutputfolder, info.name) # Output path (i.e. materials folder)
    if not os.path.exists(targetfolder):
        os.makedirs(targetfolder)
    if not os.path.exists(targetoutputfolder):
        os.makedirs(targetoutputfolder)
            
    if os.path.exists('%s.vtf' % (targetoutputpath)):
        print('%s already exists, skipping...' % (targetoutputpath))
        return

    # Create abbriviation
    words = info.displayname.split()
    n = min(len(words), 2)
    abbr = ''
    for w in words[0:n]:
        abbr += w[0]
    abbr.upper()

    #cmdline = [IMAGEMAGICKEXE, '-size', '128x128', 'canvas:none', '-pointsize', '56', '-draw', '"text 20,80 \'%s\'"' % (abbr), fs.RelativePathToFullPath('%s.png' % (info.name))]
    cmdline = '%s -fill #FFFFFF -size 128x128 canvas:none -pointsize 56 -draw "text 20,80 \'%s\'" %s.tga' % (IMAGEMAGICKEXE, abbr, targetpath)

    p = subprocess.Popen(
        cmdline, 
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stderr_output, stdout_output = GetOutput(p.stderr, p.stdout)
    status = p.wait()
    
    if stderr_output:
        print(stderr_output)
        return
        
    # Second part: create vtf
    # Create config file for vtex
    config = '''nonice 1
nolod 1
nomip 1
    '''
    fp = open('%s.txt' % (targetpath), 'wb')
    fp.write(config)
    fp.close()
    
    # Run vtex
    cmdline = '%s -nopause %s' % (os.path.join(SDKDIR, 'vtex.exe'), targetpath)
    p = subprocess.Popen(
        cmdline, 
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stderr_output, stdout_output = GetOutput(p.stderr, p.stdout)
    status = p.wait()
    
    if stdout_output:
        print(stdout_output)
        
    if stderr_output:
        print(stderr_output)
        return
        
    # Create vmt
    vmtpath = os.path.normpath(targetoutputpath)
    vmtpath = vmtpath.replace('materials\\', '')
    vmt = '''"UnlitGeneric"
{
	"$basetexture" "%s"
	"$translucent" "1"
	"$ignorez"     "1"
	"$no_fullbright" "1"
}
    ''' % (vmtpath)
    fp = open('%s.vmt' % (targetoutputpath), 'wb')
    fp.write(vmt)
    fp.close()
    
def RecursiveCreateImages(info, done, targetfolder, targetoutputfolder):
    if info in done:
        return
        
    GenerateImage(info, targetfolder, targetoutputfolder)
    done.add(info)
    
    try: abilities = info.abilities
    except AttributeError: abilities = None
    try: successorability = info.successorability
    except AttributeError: successorability = None
        
    if abilities:
        for name in abilities.values():
            RecursiveCreateImages(dbabilities[name], done, targetfolder, targetoutputfolder)
                
    if successorability:
        RecursiveCreateImages(dbabilities[successorability], done, targetfolder, targetoutputfolder)
        
@concommand('generate_stubicons')
def CCGenerateStubIcons(args):
    if args.ArgC() < 2:
        print('Usage: generate_stubicons faction')
        return
    
    specificfaction = args[1]
    
    for faction in dbfactions.values():
        if specificfaction and specificfaction != faction.name:
            continue
        print('Creating %s' % (faction.startbuilding))
        
        targetfolder = fs.RelativePathToFullPath('materialsrc/vgui/%s/' % (faction.name))
        targetoutputfolder = os.path.normpath('materials/vgui/%s/' % (faction.name))
        if not os.path.exists(targetfolder):
            os.makedirs(targetfolder)
        if not os.path.exists(targetoutputfolder):
            os.makedirs(targetoutputfolder)
            
        done = set()
        RecursiveCreateImages(dbabilities[faction.startbuilding], done, targetfolder, targetoutputfolder)
        
@concommand('generate_singlestubicon')
def CCGenerateSingleStubIcon(args):
    if args.ArgC() < 3:
        print('Usage: generate_stubicons ability materialpath')
        return
        
    info = dbabilities[args[1]]
    targetfolder = fs.RelativePathToFullPath('materialsrc/%s' % (args[2]))
    targetoutputfolder = os.path.normpath('materials/%s' % (args[2]))
    GenerateImage(info, targetfolder, targetoutputfolder, nosubcat=True)
