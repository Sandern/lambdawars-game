from vmath import *
from gamemgr import RegisterGamePackage, LoadGamePackage
from core.dispatch import receiver
from core.signals import postlevelinit, prelevelinit, navmesh_preload, recast_mapmesh_postprocess, prelevelshutdown
import readmap
from gameinterface import modelinfo, concommand, FCVAR_CHEAT
from navmesh import RecastMgr

particles = [
    # Base
    #'particles/rain_fx.pcf',
    #'particles/blood_impact.pcf',
    #'particles/water_impact.pcf',
    '!particles/error.pcf',
    'particles/base_destruction_fx.pcf',
    'particles/base_attacks.pcf',
    '!particles/ui_mouseactions.pcf',
    #'!particles/generic_hero_status.pcf',
    #'particles/generic_gameplay.pcf',
    #'particles/items_fx.pcf',
    #'particles/items2_fx.pcf',
    #'!particles/speechbubbles.pcf',
    #'particles/world_creature_fx.pcf',
    #'!particles/world_destruction_fx.pcf',
    #'particles/world_environmental_fx.pcf',
    #'!particles/status_fx.pcf',
    #'particles/radiant_fx.pcf',
    #'particles/radiant_fx2.pcf',
    #'particles/dire_fx.pcf',
    #'!particles/msg_fx.pcf',
    #'!particles/siege_fx.pcf',
    #'!particles/neutral_fx.pcf',
    
    # Heroes
    'particles/units/heroes/hero_doom_bringer.pcf',
    'particles/units/heroes/hero_skeletonking.pcf',
]
        
RegisterGamePackage(
    name=__name__,
    dependencies=['core'],
    particles=particles,
    modules = [
        'units.basedota',
        'units.*',
        'buildings.building',
        'buildings.*',
        'ents.*',
        'scriptparser',
    ],
)

def LoadGame(*args, **kwargs):
    if isclient:
        from vgui import localize
        localize.AddFile("Resource/dota_%language%.txt", None, True)

    from . import scriptparser
    scriptparser.ParseDotaUnits()
    scriptparser.ParseDotaHeroes()
    
def PostProcessMapMesh(mapmesh, bounds, **kwargs):
    treemin = -Vector(40, 40, 0)
    treemax = Vector(40, 40, 220)
    from time import time
    starttime = time()
    if bounds:
        from .ents.tree import DotaTree, treesgrid
        mins, maxs = bounds
        minkey = DotaTree.CalcKey(mins)
        maxkey = DotaTree.CalcKey(maxs)
        count = 0
        for x in range(minkey[0], maxkey[0]):
            for y in range(minkey[1], maxkey[1]):
                [mapmesh.AddEntityBBox(tree, treemin, treemax) for tree in treesgrid[(x, y)] if not tree.destroyed]
                count += len(treesgrid[(x, y)])
        print('PostProcessMapMesh: parsed %d trees (partial update in %f seconds)' % (count, time() - starttime))
    else:
        from .ents.tree import dotatrees
        [mapmesh.AddEntityBBox(tree, treemin, treemax) for tree in dotatrees if not tree.destroyed]
        print('PostProcessMapMesh: parsed %d trees (full update in %f seconds)' % (len(dotatrees), time() - starttime))

@receiver(prelevelinit)
def PreLevelInit(sender, **kwargs):
    import srcmgr
    if not srcmgr.levelname.startswith('dota'):
        return
        
    recast_mapmesh_postprocess.connect(PostProcessMapMesh)
    
    if isserver:
        LoadGamePackage('dota')
        return
        
@receiver(prelevelshutdown)
def LevelShutdown(sender, **kwargs):
    import srcmgr
    if not srcmgr.levelname.startswith('dota'):
        return
    recast_mapmesh_postprocess.disconnect(PostProcessMapMesh)
        
@receiver(postlevelinit)
def PostLevelInit(sender, **kwargs):
    import srcmgr
    if not srcmgr.levelname.startswith('dota'):            
        return

    if isserver:
        #LoadGamePackage('dota')

        return

    SpawnTrees()
    
@receiver(navmesh_preload)
def PreLoadNavMesh(sender, **kwargs):
    import srcmgr
    if not srcmgr.levelname.startswith('dota'):            
        return
        
    if isserver:
        # Build mesh on the fly. Shouldn't take much time for these settings.
        print('Building meshes...')
        
        #def PostProcessMapMesh(mapmesh, bounds, **kwargs):
        #    from .ents.tree import dotatrees
        #    print('PostProcessMapMesh: adding %d trees' % (len(dotatrees)))
        #    treemin = -Vector(40, 40, 0)
        #    treemax = Vector(40, 40, 220)
        #    [mapmesh.AddEntityBBox(tree, treemin, treemax) for tree in dotatrees]
                
        #recast_mapmesh_postprocess.connect(PostProcessMapMesh)
        
        RecastMgr().Reset()
        RecastMgr().InsertMesh('dota', agentRadius=34.0, agentHeight=72.0, agentMaxClimb=24.0, agentMaxSlope=50.0)
        RecastMgr().Build(False)
        
        #recast_mapmesh_postprocess.disconnect(PostProcessMapMesh)
            
def SpawnTrees():
    import srcmgr
    # Parse trees on client
    # Get entities
    maplocation = 'maps\\%s.bsp' % (srcmgr.levelname)
    try:
        blocks, blocksbyclass = readmap.ParseMapEntitiesToBlocks( maplocation )
    except:
        PrintWarning('Invalid map %s\n' % (maplocation))
        return
        
    dotatreesdata = blocksbyclass['ent_dota_tree']
    print('Parsing %d dota trees...' % (len(dotatreesdata)))
    from .ents.tree import DotaTree
    
    for treedata in dotatreesdata:
        tree = DotaTree()
        modelname = treedata['model'][0]
        modelindex = tree.PrecacheModel(modelname)
        #model = modelinfo.FindOrLoadModel(modelname)
        if tree.InitializeAsClientEntity(modelname, False):
            origin = readmap.StringToVector(treedata['origin'][0])
            angles = readmap.StringToAngle(treedata['angles'][0], vec3_angle)
            tree.SetAbsOrigin(origin)
            tree.SetAbsAngles(angles)
            tree.SetBodygroup(1, 1)
            tree.SetBodygroup(0, 1)
            tree.SetDistanceFade(1800.0, 2000.0)
            rendercolor = readmap.StringToVector(treedata['rendercolor'][0])
            tree.SetRenderColor(int(rendercolor.x), int(rendercolor.y), int(rendercolor.z))
            tree.Spawn()
            tree.Activate()
        else:
            PrintWarning('parse dota trees: Failed to initialize client entity with model %s. modelindex: %d\n' % (modelname, modelindex))
        
if isclient:
    @concommand('dota_spawn_trees', flags=FCVAR_CHEAT)
    def DotaSpawnTrees(args):
        SpawnTrees()
        
    @concommand('dota_spawn_test_tree', flags=FCVAR_CHEAT)
    def DotaSpawnTestTree(args):
        from entities import CBasePlayer
        player = CBasePlayer.GetLocalPlayer()
    
        from .ents.tree import DotaTree
        tree = DotaTree()
        modelname = 'models/props_tree/dire_tree004.mdl'
        modelindex = tree.PrecacheModel(modelname)
        model = modelinfo.FindOrLoadModel(modelname)
        if tree.InitializeAsClientEntity(modelname, False):
            tree.SetAbsOrigin(player.GetMouseData().groundendpos)
            tree.SetBodygroup(1, 1)
            tree.SetBodygroup(0, 1)
            tree.Spawn()
            tree.Activate()
        else:
            print('dota_spawn_test_tree failed')
            
else:
    @concommand('dota_spawn_test_tree_server', flags=FCVAR_CHEAT)
    def DotaSpawnTrees(args):
        from .ents.tree import DotaTree
        DotaTree.PrecacheModel('models/props_tree/dire_tree004.mdl')