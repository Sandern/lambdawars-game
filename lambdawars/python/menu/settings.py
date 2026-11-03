""" Settings page of the menu.

    Reads and applies the same settings as the native option dialogs of the game
    (client/lambdawars/gameui/wars: vvideo.cpp, vaudio.cpp, vkeyboardmouse.cpp and
    vmultiplayer.cpp, the gamma dialog and the key bindings of scripts/kb_act.lst).
    Settings are passed to the page by id, with values the page shows directly. What
    Python can't reach (video modes, anti-aliasing modes, the voice tweak API and the
    audio language) comes from the _gamesettings module of the client.
"""
import re
import shlex

from cef import WebViewComponent, jsbind
from gameui import CGameUIConVarRef
from gameinterface import engine
from vgui import localize
import filesystem

try:
    import _gamesettings
except ImportError:
    _gamesettings = None

KEY_ACTIONS_PATH = 'scripts/kb_act.lst'
DEFAULT_CONFIG_PATH = 'cfg/config_default.cfg'

#: Windowed modes the video dialog always offers, besides the fullscreen modes (vvideo.cpp)
EXTRA_WINDOWED_MODES = [(1280, 720), (1920, 1080)]
FILTERING_MODES = [0, 1, 2, 4, 8, 16]
SPEAKER_MODES = [0, 2, 4, 5]

#: ConVar behind settings that only show when the game has it
SETTING_CONVARS = {
    'lockmouse': 'in_lock_mouse_to_window',
    'filmgrain': 'mat_grain_scale_override',
    'lighting': 'deferred_lighting_enabled',
    'gamma': 'mat_monitorgamma',
    'ordersounds': 'cl_unit_disable_order_sounds',
    'voicethreshold': 'voice_threshold',
    'console': 'con_enable',
    'landiscovery': 'net_allow_multicast',
    'customcontent': 'cl_downloadfilter',
    'colorblind': 'cl_colorblind',
    'instructor': 'gameinstructor_enable',
    'freelook': 'spec_allowroaming',
    'gore': 'z_wound_client_disabled',
}

VIDEO_SETTINGS = ['aspect', 'resolution', 'displaymode', 'lockmouse', 'filmgrain', 'antialias', 'filtering', 'vsync',
                  'multicore', 'shader', 'effect', 'model', 'pagedpool', 'lighting']
VOICE_TWEAK_SETTINGS = ['voicetransmit', 'voicereceive', 'micboost']


def ConVar(name):
    return CGameUIConVarRef(name, True)


def Localize(text):
    if text.startswith('#'):
        return localize.Find(text) or text
    return text


def ParseQuotedLine(line):
    """ Splits a line of a key list or config file into its quoted or plain words. """
    line = line.split('//', 1)[0].strip()
    if not line:
        return []
    try:
        return shlex.split(line)
    except ValueError:
        return []


class WebSettings(WebViewComponent):
    defaultobjectname = 'gamesettings'

    #: Microphone test of the sound settings
    testingmicrophone = False

    def OnDestroy(self):
        super().OnDestroy()
        self.StopMicrophoneTest()

    # Bindings
    @jsbind(hascallback=True)
    def get(self, methodargs):
        """ Returns the settings: {'values', 'available', 'resolutions', 'antialiasmodes', 'recommended',
            'languages', 'keys', 'defaultkeys', 'micvolumefound'}. """
        return [self.BuildSettings()]

    @jsbind(hascallback=True)
    def apply(self, methodargs):
        """ Applies the changed settings, a list of [id, value]. Returns {'restart': bool} when a change
            only takes effect after restarting the game. """
        return [self.ApplySettings(dict(methodargs[0]))]

    @jsbind(hascallback=True)
    def startmicrophonetest(self, methodargs):
        """ Echoes the microphone back at the given transmit volume (0-100). Returns whether it started. """
        if not _gamesettings or self.testingmicrophone:
            return [False]
        self.testingmicrophone = _gamesettings.StartMicrophoneTest(float(methodargs[0]) / 100.0)
        return [self.testingmicrophone]

    @jsbind()
    def stopmicrophonetest(self, methodargs):
        self.StopMicrophoneTest()

    @jsbind(hascallback=True)
    def microphonelevel(self, methodargs):
        """ Level of the microphone during the test (0-1), or -1 when the test stopped. """
        if not _gamesettings or not self.testingmicrophone:
            return [-1]
        level = _gamesettings.GetMicrophoneLevel()
        if level < 0:
            self.testingmicrophone = False
        return [level]

    def StopMicrophoneTest(self):
        if self.testingmicrophone and _gamesettings:
            _gamesettings.StopMicrophoneTest()
        self.testingmicrophone = False

    # Reading
    def BuildSettings(self):
        values = {}
        available = {}

        # Video
        if _gamesettings:
            mode = _gamesettings.GetVideoMode()
            values['resolution'] = '%dx%d' % (mode['width'], mode['height'])
            values['aspect'] = _gamesettings.GetScreenAspectMode(mode['width'], mode['height'])
            values['displaymode'] = 'noborder' if mode['noborder'] else ('windowed' if mode['windowed'] else 'fullscreen')
            antialiasmodes = ['%d:%d' % m for m in _gamesettings.GetAntialiasModes()]
            values['antialias'] = '%d:%d' % (ConVar('mat_antialias').GetInt(), ConVar('mat_aaquality').GetInt())
            if values['antialias'] not in antialiasmodes:
                values['antialias'] = antialiasmodes[0]
        else:
            antialiasmodes = []
        values['lockmouse'] = ConVar('in_lock_mouse_to_window').GetBool()
        values['filmgrain'] = round(ConVar('mat_grain_scale_override').GetFloat(), 1)
        filtering = ConVar('mat_forceaniso').GetInt()
        values['filtering'] = filtering if filtering in FILTERING_MODES else 1
        if ConVar('mat_vsync').GetBool():
            values['vsync'] = 'triple' if ConVar('mat_triplebuffered').GetBool() else 'double'
        else:
            values['vsync'] = 'disabled'
        values['multicore'] = ConVar('mat_queue_mode').GetInt() != 0
        values['shader'] = max(0, min(3, ConVar('gpu_level').GetInt()))
        values['effect'] = max(0, min(2, ConVar('cpu_level').GetInt()))
        values['model'] = max(0, min(2, ConVar('gpu_mem_level').GetInt()))
        values['pagedpool'] = max(0, min(2, ConVar('mem_level').GetInt()))
        values['lighting'] = ConVar('deferred_lighting_enabled').GetBool()

        # Brightness
        values['gamma'] = round(ConVar('mat_monitorgamma').GetFloat(), 1)

        # Sound
        values['volume'] = int(round(ConVar('volume').GetFloat() * 100))
        values['music'] = int(round(ConVar('snd_musicvolume').GetFloat() * 100))
        speakers = ConVar('Snd_Surround_Speakers').GetInt()
        values['speakers'] = speakers if speakers in SPEAKER_MODES else 0
        if ConVar('Snd_PitchQuality').GetBool():
            values['soundquality'] = 2
        else:
            values['soundquality'] = 0 if ConVar('dsp_slow_cpu').GetBool() else 1
        if not ConVar('closecaption').GetBool():
            values['captions'] = 'off'
        else:
            values['captions'] = 'subtitles' if ConVar('cc_subtitles').GetBool() else 'full'
        values['ordersounds'] = not ConVar('cl_unit_disable_order_sounds').GetBool()
        values['voice'] = ConVar('voice_enable').GetBool() and ConVar('voice_modenable').GetBool()
        values['voicestyle'] = 'openmic' if ConVar('voice_vox').GetBool() else 'pushtotalk'
        values['voicethreshold'] = int(round(ConVar('voice_threshold').GetFloat()))

        voice = _gamesettings.GetVoiceSettings() if _gamesettings else None
        if voice:
            values['voicetransmit'] = int(round(voice['micvolume'] * 100))
            values['voicereceive'] = int(round(voice['receivevolume'] * 100))
            values['micboost'] = voice['micboost']
        for setting in ['voice', 'voicestyle', 'voicethreshold', 'voicetransmit', 'voicereceive', 'micboost', 'testmicrophone']:
            available[setting] = bool(voice)

        languages = []
        if _gamesettings:
            language, languages = _gamesettings.GetAudioLanguages()
            values['language'] = language
        available['language'] = len(languages) > 1

        # Keyboard and mouse
        values['sensitivity'] = round(ConVar('sensitivity').GetFloat(), 1)
        values['reversemouse'] = ConVar('m_pitch').GetFloat() < 0
        values['mousefilter'] = ConVar('m_filter').GetBool()
        values['console'] = ConVar('con_enable').GetBool()

        # Multiplayer
        values['landiscovery'] = ConVar('net_allow_multicast').GetBool()
        values['customcontent'] = ConVar('cl_downloadfilter').GetString().lower()
        values['colorblind'] = ConVar('cl_colorblind').GetInt()
        values['instructor'] = ConVar('gameinstructor_enable').GetBool()
        values['freelook'] = ConVar('spec_allowroaming').GetBool()
        values['gore'] = 'low' if ConVar('z_wound_client_disabled').GetBool() else 'high'

        # Video settings need the client module
        for setting in VIDEO_SETTINGS:
            available[setting] = _gamesettings is not None
        for setting, convarname in SETTING_CONVARS.items():
            if available.get(setting, True):
                available[setting] = ConVar(convarname).IsValid()

        # Key bindings
        keys = self.LoadKeyActions()
        for section in keys:
            for action in section['actions']:
                values['key:' + action['command']] = engine.Key_LookupBinding(action['command']) or ''

        return {
            'values': values,
            'available': available,
            'resolutions': self.BuildResolutions(),
            'antialiasmodes': antialiasmodes,
            'recommended': self.BuildRecommendedVideoSettings(antialiasmodes),
            'languages': languages,
            'keys': keys,
            'defaultkeys': self.LoadDefaultKeys(),
            'micvolumefound': bool(voice and voice['micvolumefound']),
        }

    def BuildResolutions(self):
        """ The resolutions of the video dialog, as [width, height, aspect mode], for fullscreen and the
            windowed display modes (not larger than the desktop, with a few extra modes). """
        if not _gamesettings:
            return {'fullscreen': [], 'windowed': []}
        modes = [tuple(m) for m in _gamesettings.GetVideoModes()]
        desktopwidth, desktopheight = _gamesettings.GetDesktopResolution()
        windowed = sorted(set(modes + EXTRA_WINDOWED_MODES))
        windowed = [m for m in windowed if m[0] <= desktopwidth and m[1] <= desktopheight]

        def describe(modelist):
            result = []
            for width, height in modelist:
                entry = [width, height, _gamesettings.GetScreenAspectMode(width, height)]
                if entry not in result:
                    result.append(entry)
            return result
        return {'fullscreen': describe(modes), 'windowed': describe(windowed)}

    def BuildRecommendedVideoSettings(self, antialiasmodes):
        """ Video settings of "Use recommended settings", or None. The lighting stays as it is,
            like in the video dialog. """
        recommended = _gamesettings.GetRecommendedVideoSettings() if _gamesettings else None
        if not recommended:
            return None
        antialias = '%d:%d' % (recommended['mat_antialias'], recommended['mat_aaquality'])
        filtering = recommended['mat_forceaniso']
        return {
            'resolution': '%dx%d' % (recommended['width'], recommended['height']),
            'aspect': _gamesettings.GetScreenAspectMode(recommended['width'], recommended['height']),
            'displaymode': 'noborder' if recommended['noborder'] else ('windowed' if recommended['windowed'] else 'fullscreen'),
            'lockmouse': recommended['in_lock_mouse_to_window'],
            'filmgrain': round(recommended['mat_grain_scale_override'], 1),
            'antialias': antialias if antialias in antialiasmodes else antialiasmodes[0],
            'filtering': filtering if filtering in FILTERING_MODES else 1,
            'vsync': ('triple' if recommended['mat_triplebuffered'] else 'double') if recommended['mat_vsync'] else 'disabled',
            'multicore': recommended['mat_queue_mode'] != 0,
            'shader': max(0, min(3, recommended['gpu_level'])),
            'effect': max(0, min(2, recommended['cpu_level'])),
            'model': recommended['gpu_mem_level'],
            'pagedpool': recommended['mem_level'],
        }

    def LoadKeyActions(self):
        """ The actions of kb_act.lst, as sections [{'title', 'actions': [{'command', 'label'}]}]. """
        sections = []
        content = filesystem.ReadFile(KEY_ACTIONS_PATH, 'GAME', textmode=True) or ''
        for line in content.splitlines():
            words = ParseQuotedLine(line)
            if len(words) < 2:
                continue
            command, label = words[0], words[1]
            if command == 'blank':
                if label.startswith('#'):
                    sections.append({'title': Localize(label), 'actions': []})
                continue
            if not sections:
                sections.append({'title': '', 'actions': []})
            sections[-1]['actions'].append({'command': command, 'label': Localize(label)})
        return [section for section in sections if section['actions']]

    def LoadDefaultKeys(self):
        """ The first key of each command bound in config_default.cfg, used by "Use defaults". """
        defaultkeys = {}
        content = filesystem.ReadFile(DEFAULT_CONFIG_PATH, 'MOD', textmode=True) or ''
        for line in content.splitlines():
            words = ParseQuotedLine(line)
            if len(words) >= 3 and words[0].lower() == 'bind':
                defaultkeys.setdefault(words[2], words[1])
        return defaultkeys

    # Applying
    def ApplySettings(self, changes):
        restart = False
        current = self.BuildSettings()['values']
        values = dict(current)
        values.update(changes)
        changed = lambda setting: setting in changes and changes[setting] != current.get(setting)

        # Video, like Video::ApplyChanges: the ConVars, then the video mode
        if any(changed(setting) for setting in VIDEO_SETTINGS) and _gamesettings:
            samples, quality = values['antialias'].split(':')
            ConVar('mat_antialias').SetValue(int(samples))
            ConVar('mat_aaquality').SetValue(int(quality))
            ConVar('mat_forceaniso').SetValue(int(values['filtering']))
            ConVar('mat_vsync').SetValue(values['vsync'] != 'disabled')
            ConVar('mat_triplebuffered').SetValue(values['vsync'] == 'triple')
            ConVar('mat_queue_mode').SetValue(-1 if values['multicore'] else 0)
            ConVar('gpu_level').SetValue(int(values['shader']))
            ConVar('cpu_level').SetValue(int(values['effect']))
            ConVar('gpu_mem_level').SetValue(int(values['model']))
            ConVar('mem_level').SetValue(int(values['pagedpool']))
            ConVar('in_lock_mouse_to_window').SetValue(bool(values['lockmouse']))
            ConVar('mat_grain_scale_override').SetValue(float(values['filmgrain']))
            if changed('lighting'):
                ConVar('deferred_lighting_enabled').SetValue(bool(values['lighting']))
                restart = True
            width, height = [int(v) for v in values['resolution'].split('x')]
            _gamesettings.ApplyVideoSettings(width, height, values['displaymode'] != 'fullscreen',
                                             values['displaymode'] == 'noborder')

        # Brightness
        if changed('gamma'):
            ConVar('mat_monitorgamma').SetValue(float(values['gamma']))

        # Sound, like Audio::OnCommand
        if changed('volume'):
            ConVar('volume').SetValue(float(values['volume']) / 100.0)
        if changed('music'):
            ConVar('snd_musicvolume').SetValue(float(values['music']) / 100.0)
        if changed('speakers') or changed('soundquality'):
            ConVar('Snd_Surround_Speakers').SetValue(str(values['speakers']))
            quality = int(values['soundquality'])
            ConVar('dsp_slow_cpu').SetValue(quality == 0)
            ConVar('Snd_PitchQuality').SetValue(quality == 2)
            # Headphones at high quality get enhanced stereo
            ConVar('dsp_enhance_stereo').SetValue(1 if int(values['speakers']) == 0 and quality == 2 else 0)
        if changed('captions'):
            ConVar('closecaption').SetValue(values['captions'] != 'off')
            ConVar('cc_subtitles').SetValue(values['captions'] == 'subtitles')
        if changed('ordersounds'):
            ConVar('cl_unit_disable_order_sounds').SetValue(0 if values['ordersounds'] else 1)
        if changed('voice'):
            ConVar('voice_modenable').SetValue(bool(values['voice']))
            ConVar('voice_enable').SetValue(bool(values['voice']))
        if changed('voicestyle') or (changed('voice') and values['voice']):
            # Turning the open microphone off and on restarts it
            ConVar('voice_vox').SetValue(0)
            if values['voicestyle'] == 'openmic':
                ConVar('voice_vox').SetValue(1)
        if changed('voicethreshold'):
            ConVar('voice_threshold').SetValue(float(values['voicethreshold']))
        if any(changed(setting) for setting in VOICE_TWEAK_SETTINGS) and _gamesettings and 'voicetransmit' in values:
            _gamesettings.SetVoiceSettings(float(values['voicetransmit']) / 100.0, float(values['voicereceive']) / 100.0,
                                           bool(values['micboost']))

        # Keyboard and mouse, like KeyboardMouse::OnCommand
        if changed('sensitivity'):
            ConVar('sensitivity').SetValue(float(values['sensitivity']))
        if changed('reversemouse'):
            pitch = abs(ConVar('m_pitch').GetFloat())
            ConVar('m_pitch').SetValue(-pitch if values['reversemouse'] else pitch)
        if changed('mousefilter'):
            ConVar('m_filter').SetValue(bool(values['mousefilter']))
        if changed('console'):
            ConVar('con_enable').SetValue(bool(values['console']))

        # Key bindings: the old key of each changed action is unbound first, so keys can be swapped
        keychanges = [(setting[4:], values[setting]) for setting in changes if setting.startswith('key:') and changed(setting)]
        for command, key in keychanges:
            oldkey = current.get('key:' + command)
            if oldkey:
                engine.ClientCmd_Unrestricted('unbind "%s"' % oldkey)
        for command, key in keychanges:
            if key:
                engine.ClientCmd_Unrestricted('bind "%s" "%s"' % (key, command))

        # Multiplayer, like Multiplayer::OnCommand
        if changed('landiscovery'):
            ConVar('net_allow_multicast').SetValue(bool(values['landiscovery']))
        if changed('customcontent'):
            ConVar('cl_downloadfilter').SetValue(values['customcontent'])
        if changed('colorblind'):
            ConVar('cl_colorblind').SetValue(int(values['colorblind']))
        if changed('instructor'):
            ConVar('gameinstructor_enable').SetValue(bool(values['instructor']))
        if changed('freelook'):
            ConVar('spec_allowroaming').SetValue(bool(values['freelook']))
        if changed('gore'):
            ConVar('z_wound_client_disabled').SetValue(1 if values['gore'] == 'low' else 0)

        engine.ClientCmd_Unrestricted('host_writeconfig')

        # Like the audio dialog: changing the audio language restarts the game through Steam
        if changed('language') and _gamesettings:
            _gamesettings.RestartWithAudioLanguage(values['language'])

        return {'restart': restart}
