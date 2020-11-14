__all__ = ['controls']

from _vgui import *
from _vguicontrols import EAvatarSize, k_EAvatarSize32x32, k_EAvatarSize64x64, k_EAvatarSize184x184
from utils import ScreenWidth, ScreenHeight

def XRES(x): return int( x  * ( ScreenWidth() / 640.0 ) )
def YRES(y): return int( y  * ( ScreenHeight() / 480.0 ) )

# Aliases
DataType = DataType_t

# Ugly work-around
__real_vgui_input = vgui_input

def vgui_input():
    i = __real_vgui_input()
    i.GetCursorPos = PyInput_GetCursorPos
    i.GetCursorPosition = PyInput_GetCursorPosition
    return i