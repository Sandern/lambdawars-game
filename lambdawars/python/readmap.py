from srcbase import Color
from vmath import Vector, QAngle
from gameinterface import GetMapHeader, LUMP_ENTITIES
from collections import defaultdict
import filesystem

def ParseMapEntitiesToBlocks(mapname):
    """ Read all entity blocks from a map.
        Return both by a list of blocks as by dictionary with the classnames as keys. """
    # Read all lines
    header = GetMapHeader(mapname)
    '''with open(mapname, 'rb') as f:
        f.seek(header.lumps[LUMP_ENTITIES].fileofs)
        lines = f.read(header.lumps[LUMP_ENTITIES].filelen)
        lines = lines.decode("utf-8").split('\n')'''
    # maxbytes is +1 because we want to read number of bytes
    lines = filesystem.ReadFile(mapname, 'MOD', maxbytes=header.lumps[LUMP_ENTITIES].filelen + 1,
                                startingbyte=header.lumps[LUMP_ENTITIES].fileofs)
    lines = lines.decode("utf-8").split('\n')
    
    # Parse each block
    assert(lines[0].startswith('{'))
    blocks = []
    blocksbyclass = defaultdict(list)
    for line in lines:
        if line == '\x00':
            break
        # Start of a new block
        if line.startswith('{'):
            block = defaultdict(list)
            classname = None
            continue
        # End of a block
        if line.startswith('}'):
            # Only save if the block closed
            blocks.append(block)
            if classname:
                blocksbyclass[classname].append(block)
            continue  
        # Parse field + value
        fieldvalue = line.split(None, 1)
        field = fieldvalue[0].replace('"', '')
        value = fieldvalue[1].replace('"', '')
        block[field].append(value)
        
        # Save classname
        if field == 'classname':
            classname = value

    return blocks, blocksbyclass

def StringToVector(value, default=None):   
    """ Try to convert a string to a Vector, if possible. The values must be separated by spaces """
    v = value.split()
    if len(v) != 3:
        if default is not None:
            return default
        raise ValueError('Value "%s" is not a Vector' % (v))
    return Vector(float(v[0]), float(v[1]), float(v[2]))

def StringToAngle(value, default=None):
    """ Try to convert a string to a QAngle, if possible. The values must be separated by spaces """
    v = value.split()
    if len(v) != 3:
        if default is not None:
            return default
        raise ValueError('Value "%s" is not a QAngle' % (v))
    return QAngle(float(v[0]), float(v[1]), float(v[2]))

def StringToColor(value, default=None):
    """ Try to convert a string to a Color, if possible. The values must be separated by spaces """
    v = value.split()
    if len(v) == 3:
        return Color(int(v[0]), int(v[1]), int(v[2]))
    elif len(v) == 4:
        return Color(int(v[0]), int(v[1]), int(v[2]), int(v[3]))
    if default is not None:
        return default
    raise ValueError('Value "%s" is not a Color' % (v))
