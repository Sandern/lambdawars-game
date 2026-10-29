from entities import CPointEntity, entity
from fields import input, PlayerField, IntegerField, BooleanField, StringField, OutputField, fieldtypes, input

if isclient:
    from vgui.musicplayer import musicmanager
else:
    from entities import FL_EDICT_ALWAYS

@entity('wars_music_controller', networked=True,
        base=['Targetname', 'Parentname', 'Angles', 'Wars'],
        iconsprite='editor/wars_music_controller.vmt')
class EntMusicController(CPointEntity):
    """Entity that controls background music playback for the match.

    Can stop music entirely, resume default playlists, or play a specific
    custom track defined by map logic.
    """
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)
        
    def OnCustomTrackChanged(self):
        """Client callback that switches to the configured custom track (or clears it)."""
        # In case path is empty, clears the active custom song and returns to default tracks
        musicmanager.PlayCustomTrack(self.customtrack)
        
    def OnMusicStateChanged(self):
        """Client callback that toggles the global music active flag."""
        musicmanager.active = self.musicenabled
        
    @input(inputname='StopMusic', helpstring='Stops any music from being played')
    def InputStopMusic(self, inputdata):
        self.musicenabled = False
        self.musicstopped.FireOutput(self, self)
        
    @input(inputname='PlayDefault', helpstring='Starts playing default tracks again')
    def InputPlayDefault(self, inputdata):
        self.musicenabled = True
        self.customtrack = '' # Clear any custom track
        
    @input(inputname='PlayCustom', helpstring='Starts playing a custom track', fieldtype=fieldtypes.FIELD_STRING)
    def InputPlayCustom(self, inputdata):
        self.musicenabled = True
        self.customtrack = inputdata.value.String()
        
    customtrack = StringField(value='', keyname='customtrack', displayname='Custom Track', 
                              helpstring='Path to custom track', networked=True, clientchangecallback='OnCustomTrackChanged')
    musicenabled = BooleanField(value=True, keyname='musicenabled', displayname='Music Enabled', 
                                helpstring='Whether music is enabled or disabled', networked=True, clientchangecallback='OnMusicStateChanged')
    musicstopped = OutputField(keyname='MusicStopped')