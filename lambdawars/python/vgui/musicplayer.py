"""
Controls the music
"""
import random

from srcbuiltins import RegisterTickMethod, UnregisterTickMethod
from sound import soundengine
from gameinterface import concommand
from entities import CBasePlayer
from core.signals import postlevelinit, prelevelshutdown

class MusicManager(object):
    def __init__(self):
        super().__init__()
        
        self.playlist = self.default_playlist
        
        postlevelinit.connect(self.LevelInitPostEntity)
        prelevelshutdown.connect(self.LevelShutdownPreEntity)
        
        self.activemusic = []
        
    def LoadPlayList(self, musicplaylist=None):
        if not musicplaylist:
            musicplaylist = self.default_playlist
            
        if musicplaylist != self.playlist:
            self.playlist = musicplaylist
            self.StartMusic()
    
    def LevelInitPostEntity(self, **kwargs):
        self.active = True
        self.last_music_update_time = 0
        self.dynamiclevel = 0
        self.dangerstarttime = 0
        
        RegisterTickMethod(self.OnTick, 0.1)
        self.StartMusic()

    def LevelShutdownPreEntity(self, **kwargs):
        self.active = False
        UnregisterTickMethod(self.OnTick)
        
    def OnTick(self):
        self.UpdateMusic()

    @property
    def default_playlist(self):
        return self.__default_playlist
        
    __active = True
    @property
    def active(self):
        return self.__active
    @active.setter
    def active(self, active):
        if not active:
            self.StopMusic()
        self.__active = active
        
    def StopMusic(self):
        """ Stops all active music immediately. """
        for song in self.activemusic:
            guidsong = song['guid']
            if soundengine.IsSoundStillPlaying(guidsong):
                soundengine.StopSoundByGuid(guidsong)
        self.activemusic = []
        
    def FadeOutActiveMusic(self):
        for song in self.activemusic:
            song['mode'] = 'fadeout'
        
    def StartMusic(self):
        """ Starts new music. Stops all active music immediately.
            The type of music started depends on the mode (i.e. dynamic or static list)
        """
        self.StopMusic()
        
        if self.dynamicmusic:
            self.AddSong(self.dynamic_music_defs[0][0], repeat=True)
        else:
            self.NextSong()
            
    def NextSong(self):
        """ Plays the next song in the static play list.
            Stops any active track.
        """
        self.StopMusic()
        if not self.active:
            return
        self.AddSong(random.sample(self.playlist, 1)[0])
        
    def AddSong(self, path, mode=None, repeat=False, volume=None):
        """ Generic method for adding a new music track
            to the active songs.

            Args:
                path (str): Path to music file
                mode (str): music mode
                repeat (bool): Keep repeating
                volume (float): Volume
        """
        if volume is None:
            volume = self.volume if mode != 'fadein' else 0.0
            
        soundengine.EmitAmbientSound(path, self.volume)
        
        self.activemusic.append({
            'path': path,
            'guid': soundengine.GetGuidForLastSoundEmitted(),
            'volume': volume,
            'repeat': repeat,
            'mode': mode,
        })
        
    def PlayCustomTrack(self, path):
        self.StopMusic() # Stop current track if any
        
        if path:
            self.AddSong(path)
        else:
            self.StartMusic() # Clears custom track and restart the music mode
            
    def IsMusicPlaying(self):
        musicactive = False
        for song in self.activemusic:
            if soundengine.IsSoundStillPlaying(song['guid']):
                musicactive = True
        return musicactive
        
    def UpdateMusic(self):
        deltatime = gpGlobals.curtime - self.last_music_update_time
        self.last_music_update_time = gpGlobals.curtime
        
        if not self.active:
            return
           
        if self.dynamicmusic:
            from core.units import UnitBaseShared
            player = CBasePlayer.GetLocalPlayer()
            
            lasttakedamage = UnitBaseShared.lasttakedamageperowner[player.GetOwnerNumber()]
            isindanger = lasttakedamage != None and (gpGlobals.curtime - lasttakedamage) < 3.0
            
            if not isindanger:
                targetdangerlevel = 0
                self.dangerstarttime = gpGlobals.curtime
            else:
                dangerduration = gpGlobals.curtime - self.dangerstarttime
                if dangerduration < 10.0:
                    targetdangerlevel = 1
                else:
                    targetdangerlevel = 2
                    
            if targetdangerlevel != self.dynamiclevel:
                #print('Danger level changed from %d to %d' % (self.dynamiclevel, targetdangerlevel))
                self.FadeOutActiveMusic()
                self.AddSong(self.dynamic_music_defs[0][targetdangerlevel], mode='fadein', repeat=True)
                self.dynamiclevel = targetdangerlevel
        
            # Update active songs
            for song in list(self.activemusic):
                if not soundengine.IsSoundStillPlaying(song['guid']):
                    self.activemusic.remove(song)
                    if song['repeat']:
                        self.AddSong(song['path'], repeat=True, volume=song['volume'], mode=song['mode'])
                        #print('Repeating %s' % (song['path']))
                    continue
            
                # Update fade in/out
                # Faded out songs are automatically removed
                if song['mode'] == 'fadeout':
                    song['volume'] = max(0, song['volume'] - ((deltatime*self.volume)/self.fadeduration))
                    soundengine.SetVolumeByGuid(song['guid'], song['volume'])
                    if song['volume'] == 0:
                        soundengine.StopSoundByGuid(song['guid'])
                        self.activemusic.remove(song)
                        #print('%s song faded out' % (song['path']))
                        continue
                elif song['mode'] == 'fadein' and song['volume'] < self.volume:
                    song['volume'] = min(self.volume, song['volume'] + ((deltatime*self.volume)/self.fadeduration))
                    soundengine.SetVolumeByGuid(song['guid'], song['volume'])
                        
        else:
            if not self.IsMusicPlaying():
                self.NextSong()

    volume = 0.20
    last_music_update_time = 0
    
    # Playlist static
    __default_playlist = [
        'music/A New Revolution.mp3',
        'music/Glowstick.mp3',
        'music/Endangered Specimen.mp3',
        'music/Atmospheric Disturbances.mp3',
        'music/Now is the Hour.mp3',
        'music/Uprising.mp3',
        'music/Fight and Flight.mp3',
        'music/Transmission.mp3',
        'music/Toxic Street.mp3',
        'music/Blank City.mp3',
        'music/Synthesis Of Life.mp3',
    ]
    
    # Dynamic mode
    dynamicmusic = False
    dynamiclevel = 0
    dangerstarttime = 0
    fadeduration = 4.0
    
    dynamic_music_defs = [
        ['Music/Dynamic A/Dynamic A level 1.mp3', 'Music/Dynamic A/Dynamic A level 2.mp3', 'Music/Dynamic A/Dynamic A level 3.mp3'],
    ]
    
musicmanager = MusicManager()

# Commands
@concommand('music_toggle', helpstring='Toggle music')
def cc_music_toggle(args):
    musicmanager.active = not musicmanager.active

@concommand('music_nextsong', helpstring='Next music song')
def cc_music_nextsong(args):
    musicmanager.NextSong()
    
@concommand('music_info', helpstring='Music player debug')
def music_info(args):
    if musicmanager.dynamicmusic:
        print('Dynamic music active. Level: %d' % (musicmanager.dynamiclevel))
        dangerduration = gpGlobals.curtime - musicmanager.dangerstarttime
        print('\tCurrent danger duration: %f' % (dangerduration))
    else:
        print('Static music list active')
    for song in musicmanager.activemusic:
        print('Song "%s". Volume: %f' % (song['path'], song['volume']))


