"""
Provides the internals of a simple ingame python editor.
No vgui stuff here.
"""

import os
import fnmatch

class PyOpenFile:
    """ An object representing an open file """
    def __init__(self, entry):
        self.entry = entry
        
        # Read text
        with open(entry.fullPath, 'rt') as fh:
            self.contents = fh.read()
        
class PyFileNode:
    """ An object representing a file node"""
    def __init__(self, name, fullpath, isDir):
        self.name = name
        self.fullPath = fullpath
        self.isDir = isDir
        
        if self.isDir:
            self.treeList = []

            
class PyEditorBase:
    def __init__(self):
        self.openFiles = []     # A list of the open files
        self.fileTreeRoot = None
        
    def OpenFile(self, entry):
        if os.path.isdir(entry.fullPath) == False:
            self.openFiles.append( PyOpenFile( entry ) )
        
    def CloseFile(self, entry):
        for v in self.openFiles:
            if v is entry:
                self.openFiles.remove( v )
                break
        
    def BuildFileTree(self, treeList, entry, entry_path ):
        if os.path.isdir(entry_path) == False and fnmatch.fnmatch(entry, '*.py') == False:
            return
        
        treeList.append( PyFileNode(entry, entry_path, os.path.isdir(entry_path) ) )
        if treeList[len(treeList)-1].isDir:
            # List contents and call buildFileTree
            for file in os.listdir(treeList[len(treeList)-1].fullPath):
                path = os.path.join(treeList[len(treeList)-1].fullPath, file)
                self.BuildFileTree( treeList[len(treeList)-1].treeList, file, path )
        
    def RefreshFileTree(self):
        # Clear old
        self.fileTree = []
        
        # Start from the python folder
        self.fileTreeRoot = PyFileNode('python', 'python', os.path.isdir('python') )
        for file in os.listdir(self.fileTreeRoot.fullPath):
            path = os.path.join(self.fileTreeRoot.fullPath, file)
            self.BuildFileTree( self.fileTreeRoot.treeList, file, path )        

