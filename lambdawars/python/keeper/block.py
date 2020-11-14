from srcbase import Color, SOLID_VPHYSICS, SOLID_BBOX, MOVETYPE_NONE, LIFE_ALIVE, DAMAGE_YES, MASK_SOLID, COLLISION_GROUP_NONE, DONT_BLEED
from vmath import Vector, QAngle, VectorScale, VectorNormalize, AngleMatrix, TransformAABB, VectorRotate, matrix3x4_t, VectorVectors, VectorAngles
import ndebugoverlay 
import srcmgr
import random

from .tiles import TileBase, lightkeys, GenerateModelCases
from .taskqueue import taskqueues

from keeper.light import CreateDungeonLight
from .common import nearestkeybydist

from utils import trace_t, UTIL_TraceLine
from entities import IMouse, EFL_SERVER_ONLY, DENSITY_GAUSSIAN
if isclient:
    from srcbase import RenderMode_t
    from entities import C_BaseCombatCharacter as BaseClass, CBasePlayer
    from .blockhovereffect import BlockSelectionRenderer, BlockScreen
    from materials import glowobjectmanager
else:
    from entities import CBaseCombatCharacter as BaseClass, CreateEntityByName, DispatchSpawn

class BlockBase(TileBase):
    mins = -Vector(40, 40, 0)
    maxs = Vector(40, 40, 112)

    isblock = True
    isdiggable = True
    
    minimapcolor = Color(75, 54, 29, 220)
    
    def __init__(self):
        super().__init__()
        
        self.selectedbyplayers = set()
        self.SetAllowNavIgnore(True)
        
        if isserver:
            self.SetDensityMapType(DENSITY_GAUSSIAN)
        
            self.lifestate = LIFE_ALIVE
            self.takedamage = DAMAGE_YES
            
            self.SetBlocksLOS(True)
            self.SetAIWalkable(True)
            
            #self.SetBloodColor(DONT_BLEED)

    def GetCursor(self):
        return 14
        
    def Spawn(self):
        super().Spawn()
        
        if isserver:
            self.health = 40
            self.maxhealth = 40
            
        # Tiles are 24.0 height, so raise ourself
        origin = self.GetAbsOrigin()
        origin.z += 24.0
        self.SetAbsOrigin(origin)
        
    def GenerateTestBitString(self):
        testbits = ''
        for key in self.neighborkeys:
            if key not in self.neighbors:
                testbits += '0'
                continue
            tile = self.neighbors[key]
            if not tile:
                testbits += '0'
                continue
            if tile.isblock:
                testbits += '1'
            else:
                testbits += '0'
        return testbits
    
    def DebugPrint(self):
        return super().DebugPrint() + ', hp: %d' % (self.health)
        
    def UpdateOnRemove(self):
        # Hide selection
        self.UnmarkSelected()
        if isclient:
            self.HideBars()
        
        # TODO: Make sure we are not in the selected set
        #if self in self.owner.selectedblocks:
        #    self.owner.selectedblocks.remove(self)
            
        # Make sure we are cleaned up
        self.Cleanup()
            
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
    def PassesDamageFilter(self, dmginfo):
        attacker = dmginfo.GetAttacker()
        try:
            return attacker.candigblocks
        except AttributeError:
            return False
        
    def OnTakeDamage(self, dmginfo):
        #print 'processing damage'
        attacker = dmginfo.GetAttacker()
        if attacker.IsUnit() and not attacker.GetCommander():
            try:
                if not attacker.candigblocks or attacker.targetblock != self:
                    return 0
            except AttributeError:
                pass
                
        # If we are here, the attacker is a digger
        # Retrieve the real damage
        dmginfo.SetDamage(attacker.digdamage)
                
        return super().OnTakeDamage(dmginfo)
        
    def Event_Killed(self, info):
        self.Cleanup()
        #return super().Event_Killed(info)
        
    def Cleanup(self):
        if self.owner and self.owner.worldisremoving:
            return
        if self.iscleanedup:
            return
        self.iscleanedup = True # Prevents CreateTile from executing the part after this again, since it destroys the existing block
        
        if isserver:
            self.owner.CreateTile('ground', self.key, 0) # Killing a block results in a ground tile

    if isclient:
        blockselectionscreen = None
        blockselectionvisible = False
        def ShowBars(self):
            if self.blockselectionvisible:
                return
            self.blockselectionvisible = BlockScreen(self)
                
            self.barsvisible = True
            
        def HideBars(self):
            if not self.blockselectionvisible:
                return
            self.blockselectionvisible.Shutdown()
            self.blockselectionvisible = None
                
            self.blockselectionvisible = False
            
    def OnCursorEntered(self, player):
        super().OnCursorEntered(player)
        
        if isclient:
            self.ShowBars()
        #print('%s players mouse entered %s' % (isclient, self))
        #print('\t%s %s %s' % (self.GetSolid(), self.GetSolidFlags(), self.CollisionProp().BoundingRadius()))
        if player.selectionstart:
            player.UpdateSelection(self.key)

    def OnCursorExited(self, player):
        super().OnCursorExited(player)
        
        #print('%s players mouse exited %s' % (isclient, self))
        if isclient:
            self.HideBars()
    
    def OnClickLeftPressed(self, player):
        # Retrieve block from trace endpos
        # The trace entity is not enough, since that covers all blocks.
        player.SetMouseCapture(self)
        #print('Setting mouse capture to: %s' % (str(self.key)))
        player.StartSelection(self.key)
        
        player.EmitAmbientSound(-1, player.GetAbsOrigin(), 'Misc.DigMark')
            
    def OnClickLeftReleased(self, player):
        #print('%s Left released: %s' % (isserver, str(self.key)))
        ent = player.GetMouseData().ent
        if type(ent) == Block:
            player.UpdateSelection(ent.key)
        player.EndSelection()
        
    def MarkSelected(self):
        if isclient:
            #self.SetRenderMode(RenderMode_t.kRenderTransTexture)
            #self.SetRenderColor(160, 160, 255)
            #self.SetRenderAlpha(255)
            self.EnableGlow(True)
    
    def UnmarkSelected(self):
        if isclient:
            #self.SetRenderMode(RenderMode_t.kRenderNormal)
            #self.SetRenderColor(255, 255, 255)
            #self.SetRenderAlpha(255)
            self.EnableGlow(False)
            
    if isclient:
        glowidx = None
        def EnableGlow(self, enable=True):
            if self.glowidx != None:
                glowobjectmanager.UnregisterGlowObject(self.glowidx)
                self.glowidx = None
                
            if enable:
                self.glowidx = glowobjectmanager.RegisterGlowObject(self, Vector(0, 1, 0.0), 0.3, True, True, -1)  
                glowobjectmanager.SetFullBloomRender(self.glowidx, True, 1)
                
    def Select(self, player):
        self.SelectByOwner(player.GetOwnerNumber())

    def Deselect(self, player):
        self.DeselectByOwner(player.GetOwnerNumber())
        
    def SelectByOwner(self, owner):
        if owner in self.selectedbyplayers:
            return
        self.selectedbyplayers.add(owner)
        self.MarkSelected()
        self.UpdateDigTaskIfSelected()
        
    def DeselectByOwner(self, owner):
        if owner not in self.selectedbyplayers:
            return
        self.selectedbyplayers.remove(owner)
        self.UnmarkSelected()
        self.UpdateDigTaskIfSelected()
        
    def OnNeighborChanged(self, othertile):
        super().OnNeighborChanged(othertile)
        if self.owner.loadingmap:
            return
            
        self.UpdateDigTaskIfSelected()
            
    def UpdateDigTaskIfSelected(self):
        if not isserver:
            return
            
        if not self.HasOneOrMoreNonBlockNeighbors():
            for tqownernumber, tq in taskqueues.items():
                if tqownernumber >= 1:
                    tq.RemoveDigWallTask(self.GetHandle())
            return
            
        # For the players that have selected this block, add a dig task
        for ownernumber in self.selectedbyplayers:
            taskqueues[ownernumber].InsertDigWallTask(self.GetHandle())
            
        # Make sure the other task queues don't have the task
        for tqownernumber, tq in taskqueues.items():
            if tqownernumber not in self.selectedbyplayers and tqownernumber >= 1:
                tq.RemoveDigWallTask(self.GetHandle())
                
    iscleanedup = False
    baseskin = 0
    glowhandle = None
    
class BlockRock(BlockBase):
    type = 'rock'
    isdiggable = False
    modelname = 'models/keeper/rock.mdl'
    
    minimapcolor = Color(75, 59, 39, 220)
    
    def OnClickLeftPressed(self, player): pass   
    def OnClickLeftReleased(self, player): pass
    
    def OnTakeDamage(self, dmginfo):
        return 0 # Can't take damage
        
    def SelectByOwner(self, owner): pass
    def DeselectByOwner(self, owner): pass
    def MarkSelected(self): pass
    def UnmarkSelected(self): pass
    def UpdateDigTaskIfSelected(self): pass
    
class Block(BlockBase):
    type = 'block'
    #modelname = 'models/keeper/block1.mdl'
    modelname = 'models/keeper/infested_pillar.mdl'
    
    # Dictionary with models for different case and their base yaw offsets
    # They will be rotated to match the correct tile case
    # OLD:
    models = {
        '0000' : ('models/keeper/infested_pillar.mdl', QAngle(0.0, 0.0, 0.0)), # In the middle of non block tiles
        '1000' : ('models/keeper/infested_endwall.mdl', QAngle(0.0, 0.0, 0.0)),
        '1100' : ('models/keeper/infested_corner.mdl', QAngle(0.0, 180.0, 0.0)), # Corner
        '1110' : ('models/keeper/infested_1sided.mdl', QAngle(0.0, 180.0, 0.0)),
        '1010' : ('models/keeper/infested_2sided.mdl', QAngle(0.0, 180.0, 0.0)),
        '1111' : ('models/keeper/infested_cap.mdl', QAngle(0.0, 0.0, 0.0)), # Enclosed by block tiles
    }
    GenerateModelCases(models)
    # NEW?
    '''non_fortified_models = {
        '0000' : ('models/pg_props/pg_keeper/pg_dirt_wall_column.mdl', QAngle(0.0, -90.0, 0.0)), # In the middle of non block tiles
        '1000' : ('models/pg_props/pg_keeper/pg_dirt_wall_front_back_left.mdl', QAngle(0.0, 90.0, 0.0)),
        '1100' : ('models/pg_props/pg_keeper/pg_dirt_wall_front_left.mdl', QAngle(0.0, 90.0, 0.0)), # Corner
        '1110' : ('models/pg_props/pg_keeper/pg_dirt_wall_front.mdl', QAngle(0.0, 90.0, 0.0)),
        '1010' : ('models/pg_props/pg_keeper/pg_dirt_wall_front_back.mdl', QAngle(0.0, 90.0, 0.0)),
        '1111' : ('models/pg_props/pg_keeper/pg_dirt_wall_cap.mdl', QAngle(0.0, -90.0, 0.0)), # Enclosed by block tiles
    }
    GenerateModelCases(non_fortified_models)
    fortified_models = {
        '0000' : ('models/pg_props/pg_keeper/pg_stone_wall_column.mdl', QAngle(0.0, -90.0, 0.0)), # In the middle of non block tiles
        '1000' : ('models/pg_props/pg_keeper/pg_stone_wall_front_back_left.mdl', QAngle(0.0, 90.0, 0.0)),
        '1100' : ('models/pg_props/pg_keeper/pg_stone_wall_front_left.mdl', QAngle(0.0, 90.0, 0.0)), # Corner
        '1110' : ('models/pg_props/pg_keeper/pg_stone_wall_front.mdl', QAngle(0.0, 90.0, 0.0)),
        '1010' : ('models/pg_props/pg_keeper/pg_stone_wall_front_back.mdl', QAngle(0.0, 90.0, 0.0)),
        '1111' : ('models/pg_props/pg_keeper/pg_stone_wall_cap.mdl', QAngle(0.0, -90.0, 0.0)), # Enclosed by block tiles
    }
    GenerateModelCases(fortified_models) # Updates the dictionary with all cases
    models = non_fortified_models
    
    @classmethod
    def PrecacheBlockModels(cls):
        cls.modelindex = cls.PrecacheModel(cls.modelname)
        
        cls.modelindices_non_fortified = {}
        cls.modelindices_fortified = {}
        
        for key, info in cls.non_fortified_models.items():
            cls.modelindices_non_fortified[key] = (cls.PrecacheModel(info[0]), info[1])
        for key, info in cls.fortified_models.items():
            cls.modelindices_fortified[key] = (cls.PrecacheModel(info[0]), info[1])
            
        cls.modelindices = cls.modelindices_non_fortified'''
    
    def DebugPrint(self):
        return super().DebugPrint() + ', fortified: %s, testbits: %s' % (self.fortified, self.GenerateTestBitString())
        
    def UpdateOnRemove(self):
        self.ClearLight()
        
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
    def OnNeighborChanged(self, othertile):
        super().OnNeighborChanged(othertile)
    
        if othertile.isblock:
            return
            
        #print('%s other tile not a block -> %s %d' % (str(self.key), str(othertile.key), othertile.GetOwnerNumber()))
        if taskqueues != None and not self.fortified:
            ownernumber = othertile.GetOwnerNumber()
            if ownernumber >= 2:
                taskqueues[ownernumber].InsertFortifyTask(self.GetHandle())

    def CanBeFortified(self, ownernumber):
        if self.fortified:
            return False
        for tile in self.neighbors.values():
            if tile.isblock:
                continue
            if tile.GetOwnerNumber() == ownernumber:
                return True
        return False
        
    def Fortify(self):
        self.baseskin = 2
        
        self.SetBodygroup(self.BG_FORTIFIED, 1)
        #self.modelindices = self.modelindices_fortified
        #self.UpdateModel()
        
        # Only change skin if not selected
        if isclient:
            player = CBasePlayer.GetLocalPlayer()
            if player and player.GetOwnerNumber() not in self.selectedbyplayers:
                self.skin = self.baseskin

        self.fortified = True
        self.maxhealth = 100
        self.health = 100
        
        if isserver:
            from . import keeperworld # FIXME
            keeperworld.ClientFortifyBlock(self.key)
            
            # Randomly create lights for fortified walls.
            # Also avoid too many lights in one area (only 1 per 10x10 tiles or so)
            lightkey = self.key #(int(self.key[0]/15), int(self.key[1]/15))
            if self.key not in lightkeys:
                if lightkeys:
                    nearestlight = nearestkeybydist(self.key, lightkeys)
                    distsqr = (self.key[0]-nearestlight[0])**2+(self.key[1]-nearestlight[1])**2
                else:
                    distsqr = 42*42
                    
                if distsqr > (6*6) and random.random() < 0.2:
                    tile = None
                    for tile in self.neighbors.values():
                        if tile.isblock:
                            continue
                        if tile.GetOwnerNumber() >= 2:
                            break
                            
                    if tile:
                        dir = Vector(tile.key[0] - self.key[0], tile.key[1] - self.key[1], 0.0)
                        VectorNormalize(dir)
                        angles = QAngle()
                        VectorAngles(dir, angles)
                        
                        pos = self.GetAbsOrigin() + dir * (self.maxs.x + 14.0)
                        pos.z += 136.0
                        self.lights = CreateDungeonLight(pos, yaw=angles.y)
                        
                        lightkeys.add(lightkey)
                        self.lightkey = lightkey
                    
    def ClearLight(self):
        if self.lights:
            for l in self.lights: 
                if l: l.Remove()
            lightkeys.discard(self.lightkey)

    def UpdateDigTaskIfSelected(self):
        super().UpdateDigTaskIfSelected()

        if taskqueues != None:
            for tqownernumber, tq in taskqueues.items():
                if not self.CanBeFortified(tqownernumber) or tqownernumber in self.selectedbyplayers or tqownernumber < 2:
                    continue
                
                taskqueues[tqownernumber].InsertFortifyTask(self.GetHandle())
        
    fortified = False
    lights = None
    lightkey = None
    
    BG_NORMAL = 0
    BG_FORTIFIED = 1

class BlockGold(BlockBase):
    type = 'gold'
    #modelname = 'models/keeper/gold.mdl'
    modelname = 'models/keeper/infested_pillar.mdl'
    
    minimapcolor = Color(215, 215, 70, 220)
    
    # Dictionary with models for different case and their base yaw offsets
    # They will be rotated to match the correct tile case
    models = {
        '0000' : ('models/keeper/infested_pillar.mdl', QAngle(0.0, 0.0, 0.0)), # In the middle of non block tiles
        '1000' : ('models/keeper/infested_endwall.mdl', QAngle(0.0, 0.0, 0.0)),
        '1100' : ('models/keeper/infested_corner.mdl', QAngle(0.0, 180.0, 0.0)), # Corner
        '1110' : ('models/keeper/infested_1sided.mdl', QAngle(0.0, 180.0, 0.0)),
        '1010' : ('models/keeper/infested_2sided.mdl', QAngle(0.0, 180.0, 0.0)),
        '1111' : ('models/keeper/infested_cap.mdl', QAngle(0.0, 0.0, 0.0)), # Enclosed by block tiles
    }
    GenerateModelCases(models) # Updates the dictionary with all cases
    
    def UpdateModel(self):
        super().UpdateModel()
        
        #self.SetBodygroup(self.BG_FORTIFIED, 1)
        self.SetBodygroup(self.BG_CRYSTALS, 1)
            
    if isserver:
        def Spawn(self):
            super().Spawn()

            self.health = 100
            self.maxhealth = 100
            
            self.droppgoldonhp = 80
            
        def OnTakeDamage(self, dmginfo):
            dmg = super().OnTakeDamage(dmginfo)
            if not self.owner: return dmg
            attacker = dmginfo.GetAttacker()
            origin = attacker.GetAbsOrigin()
            while self.health < self.droppgoldonhp:
                self.DropGold(attacker.GetAbsOrigin())
            
                self.droppgoldonhp -= 10
                
            return dmg
        
        def Event_Killed(self, info):
            rv = super().Event_Killed(info)
            
            origin = self.GetAbsOrigin() + Vector(0, 0, 8.0)
            for i in range(0, 3):
                self.DropGold(origin)
            
            return rv
            
        def DropGold(self, origin):
            # Drop gold
            gold = CreateEntityByName('dk_gold')
            gold.SetAbsOrigin(origin)
            gold.SetAbsAngles(QAngle(0, random.uniform(0,360), 0))
            DispatchSpawn(gold)
            gold.Activate()
            
    BG_NORMAL = 0
    BG_FORTIFIED = 1
    BG_CRYSTALS = 2