# Some default inits
import achievements

if isclient:
    import hotkeymgr

    try:
        import vgui.pyeditor
    except:
        print('Failed to import PyEditor') # Temp for Py3
    import vgui.pyinterpreter
    import vgui.tools
    import vgui.gamepackagelist
    import vgui.musicplayer
    #import vgui.mainmenu