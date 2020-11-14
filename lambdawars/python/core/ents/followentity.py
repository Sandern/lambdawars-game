from srcbase import *
from vmath import *
from fields import EHandleField, FloatField, BooleanField, FlagsField, input, fieldtypes
from entities import CBaseEntity, entity, entitylist
from core.decorators import serveronly_assert
from utils import UTIL_GetPlayers, UTIL_ListPlayersForOwnerNumber

if isclient:
    from entities import C_HL2WarsPlayer
else:
    from entities import FL_EDICT_ALWAYS

@entity('wars_player_follow_entity', networked=True, iconsprite='editor/wars_player_follow_entity.vmt')
class PlayerFolowEntity(CBaseEntity):
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)

    def OnFollowEntityChanged(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer() 
        if not player:
            return
            
        if not self.allplayers and player.GetOwnerNumber() != self.GetOwnerNumber():
            return
            
        if type(self.followentity) == list:
            player.CamFollowGroup(self.followentity, self.forced)
        else:
            player.CamFollowEntity(self.followentity, self.forced)

    @input(inputname='CamFollowEntity', helpstring='', fieldtype=fieldtypes.FIELD_STRING)
    def InputCamFollowEntity(self, inputdata):
        if not self.enabled or (self.triggeronce and self.istriggeredonce):
            return
            
        self.followentity = None
            
        targetname = inputdata.value.String()
        target = entitylist.FindEntityByName(None, targetname)
        if not target:
            PrintWarning('#%d.InputCamFollowEntity: Could not find target entity %s\n' % (self.entindex(), targetname))
            return
            
        while target:
            if self.followentity:
                if type(self.followentity) != list:
                    self.followentity = [self.followentity]
                self.followentity.append(target)
            else:
                self.followentity = target
            target = entitylist.FindEntityByName(target, targetname)
            
        if self.GetSpawnFlags() & self.SF_FREEZE_PLAYER:
            for player in self.GetTargetPlayers():
                player.AddFlag(FL_FROZEN)
            
        self.istriggeredonce = True
        
    @input(inputname='CamReleaseFollowEntity', helpstring='')
    def InputCamReleaseFollowEntity(self, inputdata):
        if not self.enabled:
            return
        if self.GetSpawnFlags() & self.SF_FREEZE_PLAYER:
            for player in self.GetTargetPlayers():
                player.RemoveFlag(FL_FROZEN)
        self.followentity = None
        
    @serveronly_assert
    def GetTargetPlayers(self):
        if self.allplayers:
            return UTIL_GetPlayers()
        return UTIL_ListPlayersForOwnerNumber(self.GetOwnerNumber())
        
    followentity = EHandleField(value=None, networked=True, clientchangecallback='OnFollowEntityChanged')
    forced = BooleanField(value=True, networked=True, keyname='forced', displayname='Forced', helpstring='Force the entity to be followed by the player. The player will not be able to stop following unless stopped with the forced parameter.')
    enabled = BooleanField(value=True, keyname='enabled', displayname='Enabled', helpstring='Is this entity enabled?')
    triggeronce = BooleanField(value=False, keyname='triggeronce', displayname='Trigger Once', helpstring='Allow triggering this follow entity once')
    allplayers = BooleanField(value=False, networked=True, keyname='allplayers', displayname='All Players', helpstring='Force all players to follow the entity.')
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_FREEZE_PLAYER', ( 1 << 0 ), True, 'Freeze Player')],
        cppimplemented=True)
    
    istriggeredonce = False