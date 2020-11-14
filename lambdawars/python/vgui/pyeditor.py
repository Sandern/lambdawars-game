"""
The vgui side of the editor
"""
from .pyeditorbase import *
from vgui import scheme
from vgui.controls import Frame, RichText, TreeView, Button
from gameinterface import ConCommand
from srcbase import Color

try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatter import Formatter
    from pygments.styles import get_style_by_name
    
    pygments_available = True
except ImportError:
    pygments_available = False

def rgb(c):
    split = (c[0:2], c[2:4], c[4:6])
    return [int(x, 16) for x in split]

if pygments_available:
    class PyRichTextFormatter(Formatter):
        def __init__(self, **options ):
            Formatter.__init__(self, **options)
            
            self.styles = {}
            for token, style in self.style:
                self.styles[token] = style['color']

        def format(self, tokensource, outfile):
            # lastval is a string we use for caching
            # because it's possible that an lexer yields a number
            # of consecutive tokens with the same token type.
            # to minimize the size of the generated html markup we
            # try to join the values of same-type tokens here
            lastval = ''
            lasttype = None    
        
            # Get color, insert color change, insert char
            for ttype, value in tokensource:
                while ttype not in self.styles:
                    ttype = ttype.parent
                    
                if ttype == lasttype:
                    # the current token type is the same of the last
                    # iteration. cache it
                    lastval += value
                else:
                    # not the same token as last iteration, but we
                    # have some data in the buffer. wrap it with the
                    # defined style and write it to the output file
                    if lastval:
                        style = self.styles[lasttype]
                        if style:
                            clr = rgb( style )
                            self.out_content.InsertColorChange( Color( clr[0], clr[1], clr[2], 255 ) )
                        else:
                            self.out_content.InsertColorChange( self.out_content.GetFgColor() )
                        
                        # FIXME: Actually can't display utf-8, but most files seem to have some unicode
                        self.out_content.InsertString( str(lastval) )
                        
                    # set lastval/lasttype to current values
                    lastval = value
                    lasttype = ttype

class PyEditor(Frame, PyEditorBase):
    def __init__(self):
        Frame.__init__(self, None, "PyEditor")
        PyEditorBase.__init__(self) 

        self.SetTitle('PyEditor (view only)', True)
        self.SetSizeable(False)
        
        self.SetScheme(scheme().LoadSchemeFromFile("resource/SourceScheme.res", "SourceScheme"))
        
        # Create a text entry
        self.content = RichText(self, "Content")
        self.content.SetMaximumCharCount(-1)
        self.content.SetVisible(True)
        self.content.SetEnabled(True) 
        self.content.SetVerticalScrollbar(True)
        
        # Add a tree
        self.fileTreeVGUI = TreeView(self, "FileTree")
        self.fileTreeVGUI.SetVisible(True)
        self.fileTreeVGUI.SetEnabled(True) 
        
        # Add a button
        self.button = Button(self, 'Blaat', 'Blaat', self, "CommandThis")
        self.button.SetVisible(True)
        self.button.SetEnabled(True) 
        
        # Register messages
        self.RegMessageMethod('TreeViewItemSelected', self.OnItemSelected)
        self.RegMessageMethod('TreeViewItemDeSelected', self.OnItemDeSelected)
                              
    def PerformLayout(self):
        super(PyEditor, self).PerformLayout()
        
        self.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 15),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 15))
        wide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 600)
        tall = scheme().GetProportionalScaledValueEx(self.GetScheme(), 450)
        self.SetSize(wide, tall)
        
        # Size up content box
        self.content.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 460),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 405) )
        self.content.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 130),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 20) ) 
        
        # Add items to filetree
        self.RefreshFileTree()
        
        # Setup filetree
        self.fileTreeVGUI.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 110),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 405) )
        self.fileTreeVGUI.SetPos(scheme().GetProportionalScaledValueEx(self.GetScheme(), 15),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 20) ) 
        self.fileTreeVGUI.MakeReadyForUse()
        
        # Button
        self.button.SetSize(scheme().GetProportionalScaledValueEx(self.GetScheme(), 30),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 15))
        self.button.SetPos(scheme().GetProportionalScaledValueEx(self.GetScheme(), 555),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 430)) 
                              
    def AddFileItems(self, index, entry):
        # Add myself to my parent as an entry
        newIndex = self.fileTreeVGUI.AddItem( {'Text':entry.name, 'Data':entry}, index)
        if entry.isDir:
            for v in entry.treeList:
                self.AddFileItems(newIndex, v)
        
    def RefreshFileTree(self):
        super(PyEditor, self).RefreshFileTree()
        
        # Remove old items
        self.fileTreeVGUI.RemoveAll()
        
        # Add the root node
        rootIndex = self.fileTreeVGUI.AddItem({'Text':self.fileTreeRoot.name, 'Data':self.fileTreeRoot}, -1)
        
        # Add items
        for v in self.fileTreeRoot.treeList:
            self.AddFileItems(rootIndex, v)
        
    def OnItemSelected(self):
        # Don't care about directories
        if os.path.isdir(self.fileTreeVGUI.nodeList[self.fileTreeVGUI.GetFirstSelectedItem()].data['Data'].fullPath) == True:
            return
            
        # Verify we are not opening the same file again
        if len(self.openFiles) > 0:
            if self.openFiles[0].entry.fullPath is self.fileTreeVGUI.nodeList[self.fileTreeVGUI.GetFirstSelectedItem()].data['Data'].fullPath:
                return
        
        # Close old file if any
        if len(self.openFiles) > 0:
            self.CloseFile(self.openFiles[0])
        self.content.SetText("")
        
        # Just open the selected file ( only one item selected is allowed )
        self.OpenFile(self.fileTreeVGUI.nodeList[self.fileTreeVGUI.GetFirstSelectedItem()].data['Data'])
        
        # Set contents to file 
        self.ParseContent(self.openFiles[0].contents)
        
    def OnItemDeSelected(self):
        pass
    
    def ParseContent(self, content):
        if pygments_available:
            get_style_by_name('fruity')
            formatter = PyRichTextFormatter(style='fruity')
            formatter.out_content = self.content
            highlight(content, PythonLexer(), formatter)
        else:
            self.content.InsertString(content)
        
editor = PyEditor()   
        
def show_editor( args ):
    #global editor
    if editor.IsVisible():
        editor.SetVisible(False)
        editor.SetEnabled(False)  
    else:
        editor.SetVisible(True)
        editor.SetEnabled(True)   
        editor.RequestFocus()
        editor.MoveToFront()
show_editor_command = ConCommand( "pyeditor", show_editor, "Show up the ingame python editor", 0 )

