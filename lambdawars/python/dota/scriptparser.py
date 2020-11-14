''' Parses dota script to Lambda Wars format. '''
from kvdict import LoadFileIntoDictionaries
from .units.basedota import UnitDotaInfo
from .units.hero import DotaHeroInfo
from .buildings.building import DotaBuildingInfo
from .buildings.tower import DotaTowerInfo

import traceback

entity2info_class = {
    'npc_dota_tower' : DotaTowerInfo,
    'npc_dota_building' : DotaBuildingInfo,
    'npc_dota_fort' : DotaBuildingInfo,
    'npc_dota_barracks' : DotaBuildingInfo,
    'dota_barracks' : DotaBuildingInfo,
    'npc_dota_hero' : DotaHeroInfo,
}

def ParseCommon(name, entry, basevalues):
    try:
        print('Parsing unit/hero %s' % (name))
        newdef = dict(basevalues)
        newdef.update(entry)
        
        # Translate properties to Lambda Wars
        newdef['modname'] = 'dota'
        newdef['name'] = name
        newdef['displayname'] = '#' + name
        newdef['modelname'] = newdef['Model']
        if 'ModelScale' in newdef:
            newdef['scale'] = float(newdef['ModelScale'])
        newdef['speed'] = float(newdef['MovementSpeed'])
        newdef['health'] = int(newdef['StatusHealth'])
        newdef['cls_name'] = newdef['BaseClass']
        newdef['hulltype'] = newdef['BoundsHullName']
        
        baseclass = entity2info_class.get(newdef['cls_name'], UnitDotaInfo)
        NewUnit = type("%sInfo" % name, (baseclass,), newdef)
    except:
        traceback.print_exc()
    
def ParseDotaUnits():
    path = 'scripts/npc/npc_units.txt'
    
    kv = LoadFileIntoDictionaries(path)
    if not kv:
        PrintWarning('Dota units script file "%s" missing!\n' % (path))
        return
        
    print('Registering DOTA units...')
        
    # This is loaded and overriden/added to by values in the specific heroes chunks.
    basevalues = kv.get('npc_dota_units_base', {})
    
    entclasses = set()
    hulltypes = set()
    for name, entry in kv.items():
        if name == 'Version' or name == 'npc_dota_units_base':
            continue
        entclasses.add(entry.get('BaseClass', None))
        hulltypes.add(entry.get('BoundsHullName', None))
        ParseCommon(name, entry, basevalues)
       
    print('DOTA UNIT HULL TYPES: %s' % (str(hulltypes)))
    
def ParseDotaHeroes():
    path = 'scripts/npc/npc_heroes.txt'
    
    kv = LoadFileIntoDictionaries(path)
    if not kv:
        PrintWarning('Dota heroes script file "%s" missing!\n' % (path))
        return
        
    print('Registering DOTA heroes...')
        
    # This is loaded and overriden/added to by values in the specific heroes chunks.
    basevalues = kv.get('npc_dota_hero_base', {})
    
    entclasses = set()
    hulltypes = set()
    for name, entry in kv.items():
        if name == 'Version' or name == 'npc_dota_hero_base':
            continue
        entclasses.add(entry.get('BaseClass', None))
        hulltypes.add(entry.get('BoundsHullName', None))
        ParseCommon(name, entry, basevalues)
       
    print('DOTA HEROES HULL TYPES: %s' % (str(hulltypes)))