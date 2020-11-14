""" Small module to store cursors. Might be merged with another module later """
from vgui import surface

cursordb = {}

def GetCursor( path ):
    cursor = cursordb.get( path, None )
    if cursor:
        return cursor
        
    cursordb[path] = surface().CreateCursorFromFile( path )
    return cursordb[path]