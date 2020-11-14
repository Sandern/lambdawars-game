"""
Python interpreter window on the client
"""
from srcbase import Color
from vgui import scheme
from vgui.controls import Frame, RichText, TextEntry
from gameinterface import ConCommand, engine
from input import ButtonCode_t

class PyInterpreterEntry(TextEntry):
    def __init__(self, parent, panelname):
        super(PyInterpreterEntry, self).__init__(parent, panelname)
        self.SetCatchEnterKey( True )
        
    def OnKeyCodeTyped(self, code):
        if code == ButtonCode_t.KEY_ENTER or code == ButtonCode_t.KEY_PAD_ENTER:
            self.GetParent().history.InsertColorChange( Color( 255, 255, 255, 255 ) )
            self.GetParent().history.InsertString( '>>> ' + self.GetText() + '\n' )
            engine.ClientCommand( 'cl_py_run ' + self.GetText() )
            self.SetText( "" )
        else:
            super(PyInterpreterEntry, self).OnKeyCodeTyped( code )

class PyInterpreter(Frame):
    def __init__(self):
        super(PyInterpreter, self).__init__(None, "PyInterpreter")
        
        self.SetTitle( 'PyInterpreter (Client only)', True )
        self.SetSizeable(False)
        
        self.SetScheme( scheme().LoadSchemeFromFile("resource/SourceScheme.res", "SourceScheme") )
        
        # History
        self.history = RichText(self, "History")
        self.history.SetMaximumCharCount(-1)
        self.history.SetVisible(True)
        self.history.SetEnabled(True) 
        self.history.SetVerticalScrollbar( True )
        
        # Input
        self.input = PyInterpreterEntry(self, "Input")
        self.input.SetMaximumCharCount(-1)
        self.input.SetVisible(True)
        self.input.SetEnabled(True)

    def PerformLayout(self):
        super(PyInterpreter, self).PerformLayout()
       
        self.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 15),
                     scheme().GetProportionalScaledValueEx(self.GetScheme(), 15))
        wide = scheme().GetProportionalScaledValueEx(self.GetScheme(), 600)
        tall = scheme().GetProportionalScaledValueEx(self.GetScheme(), 450)
        self.SetSize(wide, tall)        
     
        # Size up content box
        self.history.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 580),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 400) )
        self.history.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 10),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 20) )

        self.input.SetSize( scheme().GetProportionalScaledValueEx(self.GetScheme(), 580),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 20) )
        self.input.SetPos( scheme().GetProportionalScaledValueEx(self.GetScheme(), 10),
                              scheme().GetProportionalScaledValueEx(self.GetScheme(), 420) )    

interpreter = PyInterpreter()   
        
def show_interpreter( args ):
    if interpreter.IsVisible():
        interpreter.SetVisible(False)
        interpreter.SetEnabled(False)  
    else:
        interpreter.SetVisible(True)
        interpreter.SetEnabled(True)   
        interpreter.input.RequestFocus()
        interpreter.MoveToFront()
show_interpreter_command = ConCommand( "pyinterpreter", show_interpreter, "Show up the ingame python interpreter", 0 )                              