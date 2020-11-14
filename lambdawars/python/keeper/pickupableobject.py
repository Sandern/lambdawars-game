from srcbase import FSOLID_NOT_SOLID, MOVETYPE_STEP, FSOLID_TRIGGER
from vmath import Vector
from entities import IMouse
from . import keeperworld
if isserver:
    from gameinterface import GameEvent, FireGameEvent
    
class PickupableObject(IMouse):
    #def __init__(self):
    #    super().__init__()
        
    def GetIMouse(self):
        return self
        
    def UpdateKey(self):
        # Update position on grid
        kw = keeperworld.keeperworld
        if kw:
            self.key = kw.GetKeyFromPos(self.GetAbsOrigin())
            
    def GetTile(self):
        kw = keeperworld.keeperworld
        if kw:
            return kw.tilegrid[self.key]
        return None
                
    def OnClickLeftReleased(self, player):
        super().OnClickLeftReleased(player)
        self.PlayerGrab(player)
        
    def PlayerGrab(self, player, release=False):
        self.UpdateKey()
        
        if not release:
            #print 'Trying to pickup ent %s, can: %s' % (str(self), str(self.CanPickup(player)))
            if self.GetHandle() not in player.grabbedunits and self.CanPickup(player):
                player.grabbedunits.append(self.GetHandle())
                self.grabbedbyplayer = player
                
                self.oldsolidflags = self.GetSolidFlags()
                self.AddSolidFlags(FSOLID_NOT_SOLID)
                self.RemoveSolidFlags(FSOLID_TRIGGER)
                
                self.SetThink(self.UpdateFollowMouse, gpGlobals.curtime)
                self.oldmovetype = self.GetMoveType()
                self.SetMoveType(MOVETYPE_STEP)
                
                #if self.unitinfo.hangsound:
                #    self.EmitAmbientSound(-1, self.GetAbsOrigin(), self.unitinfo.hangsound)

                event = GameEvent('sk_playergrabbed')
                event.SetInt("entindex", self.entindex())
                FireGameEvent(event)
                
                self.OnGrabbed(player)
                #print 'grabbed %s' % (str(self))
        else:
            kw = keeperworld.keeperworld
            canrelease = True
            if kw:
                tile = kw.tilegrid[self.key]
                if tile.isblock or tile.GetOwnerNumber() != player.GetOwnerNumber():
                    canrelease = False

            if canrelease and self.GetHandle() in player.grabbedunits:
                self.grabbedbyplayer = None
                
                self.SetThink(None)
                self.SetMoveType(self.oldmovetype)

                try:
                    player.grabbedunits.remove(self.GetHandle())
                except ValueError:
                    pass
                self.RemoveSolidFlags(FSOLID_NOT_SOLID)
                self.AddSolidFlags(self.oldsolidflags)
                
                #if self.unitinfo.dropsound:
                #    self.EmitAmbientSound(-1, self.GetAbsOrigin(), self.unitinfo.dropsound)
                    
                event = GameEvent('sk_playerreleased')
                event.SetInt("entindex", self.entindex())
                FireGameEvent(event)
                
                self.OnGrabReleased(player)
                
                #print 'released %s' % (str(self))
    
    def UpdateFollowMouse(self):
        self.UpdateKey()
        
        if self.grabbedbyplayer:
            data = self.grabbedbyplayer.GetMouseData()
            pos = data.groundendpos + Vector(0, 0, 96.0)
            self.SetAbsOrigin(pos)
        
        self.simulationtime = gpGlobals.curtime
    
        self.SetNextThink(gpGlobals.curtime + 0.1)
                
    def OnGrabReleased(self, player):
        pass
    def OnGrabbed(self, player):
        pass
        
    def CanPickup(self, player):
        tile = self.GetTile()
        return tile and tile.GetOwnerNumber() == player.GetOwnerNumber()
                
    grabbedbyplayer = None
    oldmovetype = None
    oldsolidflags = 0
    