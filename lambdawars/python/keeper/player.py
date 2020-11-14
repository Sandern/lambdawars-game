from vmath import QAngle, Vector, AngleVectors
from entities import entity, CHL2WarsPlayer
from gamerules import gamerules
from gameinterface import engine
from .common import keydist, GetDungeonHeart
from . import taskqueue
from fields import IntegerField

if isclient:
    from core.signals import FireSignalRobust, refreshhud

@entity('dk_player', networked=True)
class DKPlayer(CHL2WarsPlayer):
    def __init__(self):
        super().__init__()
        
        self.selectedblocks = set()
        self.selectingblocks = [] # List of blocks being selected, but not definitive yet
        self.grabbedunits = []
        
    def GetDefaultFaction(self):
        return 'keeper'
        
    def Spawn(self):
        super().Spawn()
        
        self.TeleportToHeart()
        
    if isserver:
        def OnChangeOwnerNumber(self, oldownernumber):
            super().OnChangeOwnerNumber(oldownernumber)
            
            taskqueue.taskqueues[self.GetOwnerNumber()].UpdateMaxGold()
        
    def TeleportToHeart(self):
        heart = GetDungeonHeart(self.GetOwnerNumber())
        if not heart:
            print('TeleportToHeart: Cannot teleport player; no dungeon heart')
            return
        angles = QAngle(-115, 135, 0)
        forward = Vector()
        AngleVectors(angles, forward, None, None)
        self.SetLocalOrigin(heart.GetAbsOrigin()+Vector(0,0,200.0))
        self.SetLocalAngles(QAngle(-115, 90, 0))
        self.SnapEyeAngles(QAngle(65, 90, 0))
        #print('Teleported player to dungeon heart')
        
    # Selecting blocks
    def GetSelectingBlocks(self):
        ''' Returns the list of blocks the player is currently adding to the selection. '''
        blocks = []
        
        tilegrid = gamerules.keeperworld.tilegrid
        
        keymin = [0,0]
        keymax = [0,0]
        if self.selectionstart[0] <= self.selectionend[0]:
            keymin[0] = self.selectionstart[0]
            keymax[0] = self.selectionend[0] 
        else:
            keymin[0] = self.selectionend[0] 
            keymax[0] = self.selectionstart[0] 
        if self.selectionstart[1] <= self.selectionend[1]:
            keymin[1] = self.selectionstart[1]
            keymax[1] = self.selectionend[1] 
        else:
            keymin[1] = self.selectionend[1] 
            keymax[1] = self.selectionstart[1] 
            
        for i in range(keymin[0], keymax[0]+1):
            for j in range(keymin[1], keymax[1]+1):
                b = tilegrid[(i,j)]
                if not b.isblock:
                    continue
                blocks.append(b.GetHandle())
        return blocks
        
    def ShouldSelect(self, blocks):
        ''' Determines if the player is selecting or unselecting blocks. '''
        select = False
        for b in blocks:
            if b not in self.selectedblocks:
                select = True
                break
        return select
    
    def StartSelection(self, key):
        ''' Starts a new selection of blocks. '''
        self.selectionstart = key
        self.UpdateSelection(key)
        
    def UpdateSelection(self, key):
        ''' Updates the list of blocks that is currently pending for adding to the selection.'''
        self.selectingblocks = [_f for _f in self.selectingblocks if _f]
        
        if not self.selectionstart:
            return
        
        #if keydist(self.selectionstart, key) > 10:
        #    return # Don't update, otherwise message overflow when sending too many
        
        # Unmark old blocks
        for b in self.selectingblocks:
            if self.GetOwnerNumber() not in b.selectedbyplayers:
                b.UnmarkSelected()
    
        self.selectionend = key
        self.selectingblocks = self.GetSelectingBlocks()
        if isclient:
            select = self.ShouldSelect(self.selectingblocks)
            for b in self.selectingblocks:
                if select: 
                    b.MarkSelected()
                else:
                    b.UnmarkSelected()
        
    def EndSelection(self):
        ''' Finalize the currently new selection of blocks
            and marks them for digging (or unmarks them for digging). '''
        if not self.selectionstart:
            return
        self.selectingblocks = [_f for _f in self.selectingblocks if _f]
        blocks = self.selectingblocks
        select = self.ShouldSelect(blocks)
        
        oldselectedblocks = set(self.selectedblocks)
        
        if select:
            for b in blocks:
                if b not in self.selectedblocks:
                    b.Select(self)
                    self.selectedblocks.add(b)
        else:
            for b in blocks:
                if b in self.selectedblocks:
                    b.Deselect(self)
                    self.selectedblocks.remove(b)

        # tell server
        if isclient:
            engine.ServerCommand('dk_blockrange_auto %d %d %d %d' % (
                    self.selectionstart[0], self.selectionstart[1],
                    self.selectionend[0], self.selectionend[1]))
            
        # Clear selection
        self.selectionstart = None
        self.selectingblocks = []
            
        #removed = oldselectedblocks.difference(self.selectedblocks)
        #for b in removed:
        #    engine.ServerCommand('dk_block_deselect %d %d' % (b.key[0], b.key[1]))
        #for b in self.selectedblocks.difference(oldselectedblocks):
        #    engine.ServerCommand('dk_block_select %d %d' % (b.key[0], b.key[1]))

    def OnRightMouseButtonReleased(self, data):
        tile = gamerules.keeperworld.GetTileFromPos(data.endpos)
        if self.grabbedunits and tile.GetOwnerNumber() == self.GetOwnerNumber() and not self.GetMouseCapture():
            releaseall = self.WasRightDoublePressed()
            grabbedunits = list(self.grabbedunits)
            for unit in grabbedunits:
                try:
                    fngrab = unit.PlayerGrab
                except AttributeError:
                    continue
                fngrab(self, True)
                if not releaseall: break
        else:
            super().OnRightMouseButtonReleased(data)
            
    def OnMaxGoldChanged(self):
        FireSignalRobust(refreshhud)

    selectionstart = None
    selectionend = None
    
    maxgold = IntegerField(value=0, networked=True, clientchangecallback='OnMaxGoldChanged')
        