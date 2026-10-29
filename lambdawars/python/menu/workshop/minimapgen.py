""" Generating the minimap of a local map, started from the Workshop publish page.

    The map is loaded with the minimapgen gamerules (core.gamerules.minimapgen): no units, fog of war or hud.
    Once the map is shown, the minimap is captured from above (_workshop.StartMinimapCapture) into a
    temporary vtf and the game returns to the menu. The publish page shows the result, and the player
    approves it (written as the minimap of the map) or discards it (see workshop.WebWorkshop).
"""
import os
import time

from gameinterface import engine, Plat_FloatTime
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from entities import C_BasePlayer
import srcmgr

try:
    import _workshop
except ImportError:
    _workshop = None

#: Folder of the generated minimaps, below materials/ so the menu can show them with vtf://
GENERATED_FOLDER = 'overviews/minimapgen'
#: Size of the minimap, like the official ones
RESOLUTION = 1024
#: Seconds the map is shown before capturing, so textures and detail props are loaded
CAPTURE_DELAY = 2.0
#: Seconds after which the capture is given up
CAPTURE_TIMEOUT = 30.0
#: Space around the playable area on each side. From about 0.21 all of it fits in the round HUD minimap.
DEFAULT_MARGIN = 0.24

#: The map whose minimap is being generated: {mapname, file, path}, or None
request = None
#: The generated minimap: {mapname, success, error, file, pos_x, pos_y, scale}, or None
generated = None
#: The menu still has to go back to the publish page to show the generated minimap
returnpending = False

_starttime = 0.0
_capturing = False
#: The map of the request is loaded and its capture started. The gamerules of the previous map are shut down
#: when the next map loads, so only the gamerules that started the capture may end the request.
_started = False


def Request(mapname, margin=DEFAULT_MARGIN):
    """ Remembers which map is generated, before the map is loaded.

        margin is the space around the playable area on each side, in parts of its size (0 to 1).
    """
    global request, generated
    DiscardGenerated()
    name = '%s_%d' % (mapname, int(time.time()))
    request = {
        'mapname': mapname,
        'margin': max(0.0, min(1.0, margin)),
        'file': '%s/%s' % (GENERATED_FOLDER, name),
        'path': os.path.abspath(os.path.join('materials', GENERATED_FOLDER, name + '.vtf')),
    }
    os.makedirs(os.path.dirname(request['path']), exist_ok=True)


def StartCapture():
    """ Called when the minimapgen gamerules are installed on the client. """
    global _starttime, _capturing, _started
    if not request or request['mapname'].lower() != srcmgr.levelname.lower():
        PrintWarning('Minimap generation: %s was not requested from the menu\n' % srcmgr.levelname)
        return
    _starttime = 0.0
    _capturing = False
    _started = True
    if not IsTickMethodRegistered(_OnTick):
        RegisterTickMethod(_OnTick, 0.1)


def StopCapture():
    """ Called when the gamerules are removed: when the next map loads, or when the game shuts down. """
    global _capturing, _started
    if not _started:
        # The gamerules of an earlier generation, while the next one loads
        return
    if IsTickMethodRegistered(_OnTick):
        UnregisterTickMethod(_OnTick)
    if _capturing and _workshop:
        _workshop.CancelMinimapCapture()
    _capturing = False
    if request:
        _Finish(False, 'The map was left before the minimap was captured.')


def _OnTick():
    global _starttime, _capturing
    if not engine.IsInGame() or not C_BasePlayer.GetLocalPlayer():
        return

    now = Plat_FloatTime()
    if not _starttime:
        _starttime = now
        return

    if not _capturing:
        if now - _starttime < CAPTURE_DELAY:
            return
        if not _workshop or not _workshop.StartMinimapCapture(request['path'], RESOLUTION, request['margin']):
            result = _workshop.GetMinimapCaptureResult() if _workshop else None
            _Finish(False, result['error'] if result else 'Capturing the minimap is not available.')
            _Leave()
            return
        _capturing = True
        return

    result = _workshop.GetMinimapCaptureResult()
    if result is None:
        if now - _starttime > CAPTURE_TIMEOUT:
            _workshop.CancelMinimapCapture()
            _Finish(False, 'Capturing the minimap took too long.')
            _Leave()
        return

    _capturing = False
    _Finish(result['success'], result['error'], result)
    _Leave()


def _Finish(success, error, result=None):
    global request, generated, returnpending, _started
    if not request:
        return
    _started = False
    returnpending = True
    generated = {
        'mapname': request['mapname'],
        'success': success,
        'error': error,
        'file': request['file'] if success else '',
        'pos_x': result['pos_x'] if success else 0,
        'pos_y': result['pos_y'] if success else 0,
        'scale': result['scale'] if success else 0,
    }
    if not success and os.path.isfile(request['path']):
        os.remove(request['path'])
    request = None


def _Leave():
    if IsTickMethodRegistered(_OnTick):
        UnregisterTickMethod(_OnTick)
    engine.ClientCommand('disconnect\n')


def TakeReturnMap():
    """ The map of the generated minimap if the menu still has to show it, once. Called when the menu is
        shown after leaving the map. """
    global returnpending
    if not returnpending or not generated:
        return None
    returnpending = False
    return generated['mapname']


def GetGeneratedPath(info):
    return os.path.join('materials', info['file'] + '.vtf')


def DiscardGenerated():
    """ Removes the generated minimap that wasn't approved. """
    global generated
    if generated and generated['file'] and os.path.isfile(GetGeneratedPath(generated)):
        os.remove(GetGeneratedPath(generated))
    generated = None
