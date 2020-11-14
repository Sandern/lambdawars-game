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
    ''' This entity allows you to manipulate the background music. '''
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)
        
    def OnCustomTrackChanged(self):
        # In case path is empty, clears the active custom song and returns to default tracks
        musicmanager.PlayCustomTrack(self.customtrack)
        
    def OnMusicStateChanged(self):
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