""" Util for reading or writing keyvalue/json game packages. """
from gamedb import RegisterGamePackage, dbgamepackages, scriptgamepackages_path, dblist
from srcbuiltins import DictToKeyValues, WriteKeyValuesToFile
from gameinterface import concommand
from fields import GetAllFields, GetField
import filesystem

import os.path
import json
import traceback


def BuildScriptGamePackages():
    for filename in filesystem.ListDir(scriptgamepackages_path, 'MOD'):
        full_path = os.path.join(scriptgamepackages_path, filename)
        root, ext = os.path.splitext(full_path)
        if ext not in ['.json']:
            continue

        pkg_name = os.path.basename(root)

        try:
            # Create the package
            if pkg_name not in dbgamepackages:
                RegisterGamePackage(pkg_name, script_path=full_path)
            gp = dbgamepackages[pkg_name]

            # Read definitions
            if ext != '.json':
                PrintWarning('Unsupported script package with extension %s\n' % ext)
                return

            #ReadJSONGamePackage(gp)
        except:
            traceback.print_exc()


def WriteKeyValueGamePackage(name, outname):
    """ Writes an existing game package to script file.
    
        Args:
            name (str): Game package to be copied.
            outname (str): Name of copied game package.
    """
    if not name:
        raise Exception('WriteKeyValueGamePackage: name not specified')
    if not outname:
        raise Exception('WriteKeyValueGamePackage: outname not specified')
        
    outpath = os.path.join(scriptgamepackages_path, '%s.txt' % outname)
        
    if name == outname and filesystem.FileExists(outpath):
        raise Exception('WriteKeyValueGamePackage: name cannot be the same as out')
        
    gp = dbgamepackages[name]
    
    defs = {}
    out_gp = {
        'defs': defs,
        'name': outname,
        'dependencies': [name],
    }

    from core.units import UnitInfo
    
    for k, v in gp.db.items():
        defs[k] = {}
        for name, info in v.items():
            # Special case! unit definitions are also in abilities definitions, so don't need to write them twice.
            if k == 'abilities' and issubclass(info, UnitInfo):
                continue
            entry = {
                '__bases__': [info.__dict__.get('name', info.__class__.__name__)],
            }

            fields = GetAllFields(info, includebases=False)
            for f in fields:
                entry[f.name] = f.ToString(f.default)
            defs[k][info.name] = entry
        
    #print('outgp: %s' % (str(outgp)))
    kv = DictToKeyValues(out_gp, name=outname)
    WriteKeyValuesToFile(kv, outpath)


def default_handler(o):
    PrintWarning('Could not handle object: %s\n' % o)
    return '<error>'
    # Let the base class default method raise the TypeError
    #return json.JSONEncoder.default(self, o)


def WriteJSONGamePackage(name, outname):
    if not name:
        raise Exception('WriteJSONGamePackage: name not specified')
    if not outname:
        raise Exception('WriteJSONGamePackage: outname not specified')

    out_path = os.path.join(scriptgamepackages_path, '%s.json' % outname)

    if name == outname and filesystem.FileExists(out_path):
        raise Exception('WriteJSONGamePackage: name cannot be the same as out')

    gp = dbgamepackages[name]

    defs = {}
    out_gp = {
        'defs': defs,
        'name': outname,
        'dependencies': [name],
    }

    for k, v in gp.db.items():
        defs[k] = {}
        for name, info in v.items():
            entry = {}

            __bases__ = [info.__dict__.get('name', info.__class__.__name__)]
            if len(__bases__) == 1:
                entry['__base__'] = __bases__[0]
            else:
                entry['__bases__'] = __bases__

            fields = GetAllFields(info, includebases=False)
            for f in fields:
                try:
                    entry[f.name] = f.ToJSON(f.default)
                except Exception as e:
                    PrintWarning('%s.%s: Failed to set field %s with error:\n%s\n' % (k, name, f.name, e))
                    traceback.print_exc()

            defs[k][info.name] = entry

    filesystem.WriteFile(out_path, 'MOD',
                         json.dumps(out_gp, sort_keys=True, indent=4, separators=(',', ': '), default=default_handler))

def ReadJSONGamePackage(gp):
    path = gp.script_path

    if not filesystem.FileExists(path):
        raise Exception('ReadJSONGamePackage: path "%s" does not exists' % path)

    # In case we are reloading the script
    gp.db.clear()

    data = json.loads(filesystem.ReadFile(path, 'MOD', textmode=True))

    dependencies = [name for name in data.get('dependencies', []) if name in dbgamepackages]
    defs = data.get('defs', {})

    if not dependencies:
        PrintWarning('Script game package has no dependencies, required for basing off new definitions\n')
        return

    gp.dependencies = dependencies

    for db_name, db_entries in defs.items():
        for name, info_definition in db_entries.items():
            # Can either define a list of bases or one base
            __bases__ = info_definition.get('__bases__', [])
            if not __bases__:
                __bases__ = [info_definition.get('__base__', None)]

            __bases__ = tuple(filter(bool, [dblist[db_name].get(v) for v in __bases__]))

            if not __bases__:
                PrintWarning('%s: no base class for definition %s\n' % (db_name, name))
                continue

            # Create a temporary class to retrieve the fields of the bases
            tmp_cls = type('temp', __bases__, {'modname': None})

            decoded_values = {}
            for key, value in info_definition.items():
                if key in ['name', '__bases__', '__base__']:
                    continue
                try:
                    f = GetField(tmp_cls, key)
                except (KeyError, AttributeError):
                    PrintWarning('%s.%s: Field %s no longer exists\n' % (db_name, name, key))
                    continue

                try:
                    decoded_values[f.name] = f.FromJSON(value)
                except Exception as e:
                    PrintWarning('%s.%s: Failed to set field %s with error:\n%s\n' % (db_name, name, key, e))
                    traceback.print_exc()

            decoded_values['name'] = name
            decoded_values['modname'] = gp.name

            # Auto registers into game package
            cls = type(name, __bases__, decoded_values)


@concommand('gp_copy')
def GPCopy(args):
    WriteJSONGamePackage(args[1], args[2])
