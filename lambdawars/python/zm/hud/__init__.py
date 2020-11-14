from core.usermessages import usermessage

if isclient:
    from buildmenu import buildmenu
    from manipulatemenu import manipulatemenu

@usermessage('BuildMenuUpdate')
def UpdateBuildMenu(spawnidx, forceopen, spawnqueue, **kwargs):
    if forceopen:
        #if we weren't visible, this is also an opening message
        buildmenu.ShowPanel(True)

    buildmenu.SetCurrentSpawn(spawnidx)
    buildmenu.UpdateQueue(spawnqueue)
    
@usermessage('ShowManipulateMenu')
def ShowManipulateMenu(manipulate, **kwargs):
    manipulatemenu.activemanipulate = manipulate
    manipulatemenu.ShowPanel(True)