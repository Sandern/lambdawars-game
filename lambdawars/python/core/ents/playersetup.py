from entities import CPointEntity, entity
from fields import input, PlayerField, StringField, FlagsField, fieldtypes
from playermgr import dbplayers, SendPlayerInfo
from readmap import StringToColor
from gameinterface import CReliableBroadcastRecipientFilter
from core.factions import GetFactionInfo

factionchoices = [
    ('rebels', 'Rebels'),
    ('combine', 'Combine'),
]

@entity('wars_player_setup',
        base=['Targetname', 'Parentname', 'Angles'],
        iconsprite='editor/wars_player_setup.vmt')
class EntPlayerRelation(CPointEntity):

    # Spawnflags
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('PLAYER_SETUP_APPLY_AT_START', ( 1 << 0 ), False, 'Apply at start')], # Apply at start.
        cppimplemented=True)

    def Precache(self):
        super().Precache()
        
        info = GetFactionInfo(self.faction)
        if info:
            info.Precache()
            
    def Spawn(self):
        self.Precache()
        
        super().Spawn()
		
        if self.GetSpawnFlags() & self.PLAYER_SETUP_APPLY_AT_START:
            dbplayers[self.player].faction = self.faction
            dbplayers[self.player].color = StringToColor(self.color)
            SendPlayerInfo(CReliableBroadcastRecipientFilter(), self.player)

    @input(inputname='ApplyFaction', helpstring='Apply the faction setting.')
    def InputApplyFaction(self, inputdata):
        dbplayers[self.player].faction = self.faction
        SendPlayerInfo(CReliableBroadcastRecipientFilter(), self.player)
        
    @input(inputname='ApplyColor', helpstring='Apply the team color setting.')
    def InputApplyColor(self, inputdata):
        dbplayers[self.player].color = StringToColor(self.color)
        SendPlayerInfo(CReliableBroadcastRecipientFilter(), self.player)
    
    @input(inputname='ApplyAll', helpstring='Apply both faction and color setting.')
    def InputApplyColor(self, inputdata):
        dbplayers[self.player].faction = self.faction
        dbplayers[self.player].color = StringToColor(self.color)
        SendPlayerInfo(CReliableBroadcastRecipientFilter(), self.player)
		
    player = PlayerField(keyname='player', displayname='Player', helpstring='Target of the setup')
    faction = StringField(value='rebels', keyname='Faction', displayname='Faction', choices=factionchoices, helpstring='Faction to be applied.')
    color = StringField(value='200 120 20 255', keyname='Color', displayname='Color', helpstring='Color to be applied, space separated rgba')
    