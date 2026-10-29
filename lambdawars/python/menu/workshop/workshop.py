""" Provides the workshop webview component, used to publish maps to the Steam Workshop.

    Publishing a map copies its files into a staging folder that mirrors the game
    directory (maps/<name>.bsp, maps/<name>.res, ...), creates a Workshop item if the
    map was not published before, and uploads the staging folder as the item content.
    The published file id of each map is remembered in workshop/published.json, so
    publishing the same map again updates the existing item.

    Before updating an item, a review compares the new upload with what is on the
    Workshop: the details are fetched from Steam, and the current version of the item
    is downloaded (without subscribing) to compare the files. If that fails, the files
    are compared with the file list saved at the last upload.
"""
import os
import json
import shutil
import hashlib
import time
import base64
import re

from srcbase import KeyValues
from cef import WebViewComponent, jsbind
import matchmaking
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
import kvdict
import readmap

from . import minimapgen

try:
    import _workshop
except ImportError:
    _workshop = None

WORKSHOP_DIR = 'workshop'
PUBLISHED_INFO_PATH = os.path.join(WORKSHOP_DIR, 'published.json')
STAGING_DIR = os.path.join(WORKSHOP_DIR, 'staging')
#: Official maps of the game, which can't be published. One quoted map name per line.
#: Releases only include the maps in this list.
OFFICIAL_MAPLIST_PATH = 'maplist.txt'

#: Files belonging to a map, found next to maps/<name>.bsp
MAP_FILE_SUFFIXES = ['.bsp', '.res', '.recast', '.wars', '.layout', 'mapheightfielddata.bin']
WORKSHOP_TAGS = ['Map']
MAX_PREVIEW_SIZE = 1024 * 1024
#: Preview image types, with the mime type used to show them in the menu
PREVIEW_TYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
PREVIEW_EXTENSIONS = sorted(PREVIEW_TYPES.keys())
MAX_TITLE_LENGTH = 128
MAX_DESCRIPTION_LENGTH = 8000
#: Time Steam gets to start and finish downloading the current version of an item when reviewing an update
REVIEW_DOWNLOAD_START_TIMEOUT = 20.0
REVIEW_DOWNLOAD_TIMEOUT = 120.0
#: Pages of 50 items when listing the player's Workshop items
MAX_MY_ITEMS_PAGES = 10

LEGAL_AGREEMENT_URL = 'https://steamcommunity.com/sharedfiles/workshoplegalagreement'
ITEM_URL = 'https://steamcommunity.com/sharedfiles/filedetails/?id=%s'

#: Readable messages for common EResult values returned by Steam
RESULT_MESSAGES = {
    2: 'Generic Steam failure',
    8: 'Invalid parameter (check the title, description and preview image)',
    9: 'File not found',
    15: 'Access denied (is the Workshop enabled for this game?)',
    16: 'Steam timed out',
    17: 'You are banned from the Workshop',
    20: 'Insufficient privileges',
    25: 'Workshop limit exceeded',
    33: 'Insufficient privileges',
    37: 'Lost connection with Steam',
}


#: Steam's EItemUpdateStatus, logged while uploading
UPDATE_STATUS_NAMES = {
    0: 'invalid (Steam has no upload for this handle)',
    1: 'preparing config',
    2: 'preparing content',
    3: 'uploading content',
    4: 'uploading preview image',
    5: 'committing changes',
}
#: Seconds between the log lines while the status of an upload doesn't change
PUBLISH_LOG_INTERVAL = 10.0


def LogPublish(message):
    """ Console output of each publishing step, to find out why an upload fails on a PC. """
    print('Workshop publish: %s' % message)


def FormatCallResult(result):
    return 'result %d (%s), item %s, io failure %s, needs legal agreement %s' % (
        result['result'], 'OK' if result['result'] == _workshop.RESULT_OK else RESULT_MESSAGES.get(result['result'], 'unknown'),
        result['publishedfileid'], result['iofailure'], result['needslegalagreement'])


class PublishError(Exception):
    pass


def LoadOfficialMaps():
    """ Returns the lowercase names of the official maps of the game. """
    try:
        with open(OFFICIAL_MAPLIST_PATH, 'rt', encoding='utf-8', errors='replace') as f:
            return {line.strip().strip('"').lower() for line in f if line.strip()}
    except IOError:
        PrintWarning('Workshop: could not read the official map list %s\n' % OFFICIAL_MAPLIST_PATH)
        return set()


def LoadPublishedInfo():
    """ Returns the info of maps published by the local player, by map name. """
    try:
        with open(PUBLISHED_INFO_PATH, 'rt', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, ValueError):
        return {}


def HashFile(path):
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            sha1.update(chunk)
    return sha1.hexdigest()


def BuildFileList(folder):
    """ Returns the files in a folder as {relative path: {'size': size, 'sha1': hash}}.
        Paths use forward slashes. """
    files = {}
    for root, dirs, filenames in os.walk(folder):
        for filename in filenames:
            path = os.path.join(root, filename)
            relpath = os.path.relpath(path, folder).replace('\\', '/')
            files[relpath] = {'size': os.path.getsize(path), 'sha1': HashFile(path)}
    return files


def CompareFileLists(oldfiles, newfiles):
    """ Returns a list of {'path', 'size', 'status'} for all files, status being added, changed,
        removed or same. Changed files are listed first. Paths are compared case insensitive. """
    oldbykey = {path.lower(): (path, info) for path, info in oldfiles.items()}
    newbykey = {path.lower(): (path, info) for path, info in newfiles.items()}
    result = []
    for key in set(oldbykey) | set(newbykey):
        if key not in oldbykey:
            path, info = newbykey[key]
            status = 'added'
        elif key not in newbykey:
            path, info = oldbykey[key]
            status = 'removed'
        else:
            path, info = newbykey[key]
            status = 'same' if oldbykey[key][1].get('sha1') == info['sha1'] else 'changed'
        result.append({'path': path, 'size': info.get('size', 0), 'status': status})
    statusorder = {'changed': 0, 'added': 1, 'removed': 2, 'same': 3}
    result.sort(key=lambda entry: (statusorder[entry['status']], entry['path']))
    return result


def NormalizeText(text):
    """ Steam may return text with other line endings than it was uploaded with. """
    return (text or '').replace('\r\n', '\n').strip()


def GetMapMinimap(mapname):
    """ The minimap of a local map, as the lobby shows it: the overview material named in the res file of
        the map, uploaded with the map files. Also the start positions, normalized to the overview (0 to 1)
        like the lobby settings do.

        State: ok, none (no res file or no overview material in it) or missing (the material isn't found)
    """
    respath = os.path.join('maps', mapname + '.res')
    info = {'state': 'none', 'res': 'maps/%s.res' % mapname, 'image': '', 'src': '', 'positions': []}
    if not os.path.isfile(respath):
        return info
    kvres = kvdict.LoadFileIntoDictionaries(respath) or {}
    material = kvres.get('material', '')
    if not material:
        return info
    info['image'] = 'materials/%s.vtf' % material
    if not os.path.isfile(os.path.join('materials', material + '.vtf')):
        info['state'] = 'missing'
        return info
    info['state'] = 'ok'
    # The file may be replaced by a generated minimap, so the menu shouldn't use a cached image
    info['src'] = 'vtf://%s.vtf?v=%d' % (material, int(os.path.getmtime(os.path.join('materials', material + '.vtf'))))
    try:
        info['positions'] = GetStartPositions(mapname, float(kvres.get('pos_x', -512.0)),
                                              float(kvres.get('pos_y', -512.0)), float(kvres.get('scale', 1.0)))
    except ValueError as e:
        PrintWarning('Workshop: invalid minimap values in %s: %s\n' % (respath, e))
    return info


def GetStartPositions(mapname, pos_x, pos_y, scale):
    """ The start positions of a map on its minimap (0 to 1), ordered by position number. """
    try:
        size = scale * 1024.0
        blocks, blocksbyclass = readmap.ParseMapEntitiesToBlocks(os.path.join('maps', mapname + '.bsp'))
        positions = {}
        for startent in blocksbyclass['info_start_wars']:
            if not startent['ownernumber'] or not startent['origin']:
                continue
            position = int(startent['ownernumber'][0])
            if position not in positions:
                origin = list(map(float, startent['origin'][0].split()))
                positions[position] = [(origin[0] - pos_x) / size, (pos_y - origin[1]) / size]
        return [positions[position] for position in sorted(positions)]
    except (OSError, ValueError, IndexError, ZeroDivisionError) as e:
        PrintWarning('Workshop: could not read the start positions of %s: %s\n' % (mapname, e))
        return []


def IsLocalMap(mapname):
    """ A map name (not a path) of a map in the maps folder. """
    return os.path.basename(mapname) == mapname and os.path.isfile(os.path.join('maps', mapname + '.bsp'))


#: Material of a generated minimap, like the official ones
MINIMAP_VMT = '''"UnlitGeneric"\r
{\r
	"$translucent" "1"\r
	"$basetexture" "%s"\r
	"$vertexcolor" "1"\r
	"$vertexalpha" "1"\r
	"$no_fullbright" "1"\r
	"$ignorez" "1"\r
}\r
'''

#: Minimap values written to the res file of a map, with the format of the official res files
MINIMAP_RES_KEYS = [('material', '%s'), ('pos_x', '%.0f'), ('pos_y', '%.0f'), ('scale', '%.3f'), ('rotate', '%d'), ('zoom', '%.1f')]


def WriteMinimapRes(mapname, values):
    """ Sets the minimap values in maps/<map>.res, keeping the other keys and comments of the file.
        Creates the res file if the map has none. """
    respath = os.path.join('maps', mapname + '.res')
    lines = []
    newline = '\r\n'
    if os.path.isfile(respath):
        with open(respath, 'rb') as f:
            data = f.read().decode('utf-8', errors='replace')
        newline = '\r\n' if '\r\n' in data else '\n'
        lines = data.replace('\r\n', '\n').split('\n')
    if not any(line.strip().startswith('{') for line in lines):
        lines = ['"%s"' % mapname, '{', '}', '']

    for key, fmt in MINIMAP_RES_KEYS:
        if key not in values:
            continue
        value = fmt % values[key]
        pattern = re.compile(r'^(\s*"%s"\s+)"[^"]*"' % key, re.IGNORECASE)
        for i, line in enumerate(lines):
            if pattern.match(line):
                lines[i] = pattern.sub(lambda m: '%s"%s"' % (m.group(1), value), line, count=1)
                break
        else:
            # Before the closing brace of the file
            close = max(i for i, line in enumerate(lines) if line.strip().startswith('}'))
            lines.insert(close, '\t"%s"\t\t"%s"' % (key, value))

    with open(respath, 'wb') as f:
        f.write(newline.join(lines).encode('utf-8'))


class WebWorkshop(WebViewComponent):
    defaultobjectname = 'workshop'

    jshandler = None
    #: State of the map being published, or None
    publishjob = None
    #: State of the update being reviewed, or None
    reviewjob = None
    #: State of loading the player's Workshop items, or None
    myitemsjob = None
    #: State of the Workshop item being linked to a local map, or None
    linkjob = None
    #: Callback of the open preview image file dialog, or None
    previewdialogcallback = None

    def OnDestroy(self):
        super().OnDestroy()

        self.StopPublishTick()
        self.CancelReview()
        self.CancelMyItems()
        self.CancelLink()
        self.StopPreviewDialogTick()

    @jsbind()
    def sethandler(self, methodargs):
        self.jshandler = methodargs[0]

    @jsbind(hascallback=True)
    def getinfo(self, methodargs):
        """ Returns whether the Workshop is available, the error if not, the local maps
            and the map being published (see GetPublishState). """
        if not _workshop:
            return [False, 'Workshop module not available', [], None]
        available = _workshop.IsAvailable()
        error = '' if available else _workshop.GetError()
        return [available, error, self.ListLocalMaps(), self.GetPublishState()]

    @jsbind(hascallback=True)
    def getpublishstate(self, methodargs):
        """ Returns the map being published (see GetPublishState), without listing the local maps. """
        return [self.GetPublishState()]

    def GetPublishState(self):
        """ The map being published and its last progress, so a page opened during the upload can show it.
            None if no map is being published. """
        job = self.publishjob
        if not job:
            return None
        status, processed, total = job.get('progress', (None, 0, 0))
        return {
            'mapname': job['mapname'],
            'title': job['title'],
            'publishedfileid': str(job['publishedfileid']) if job['publishedfileid'] else '',
            'status': status,
            'processed': processed,
            'total': total,
        }

    @jsbind()
    def publish(self, methodargs):
        """ Starts publishing a map.

            Args: map name, title, description, visibility, change note, preview image path
        """
        if self.publishjob:
            self.NotifyFinished(False, '', 'Already publishing a map')
            return

        mapname, title, description, visibility, changenote, previewpath = methodargs[:6]
        try:
            self.StartPublish(mapname, title.strip(), description.strip(), int(visibility),
                              changenote.strip(), previewpath.strip())
        except PublishError as e:
            LogPublish('failed before uploading: %s' % e)
            self.publishjob = None
            self.NotifyFinished(False, '', str(e))

    @jsbind(hascallback=True, manuallycallback=True)
    def reviewupdate(self, methodargs, callbackid):
        """ Compares an update of a published map with what is on the Workshop.

            Args: map name, title, description, visibility, preview image path
            Callback args: success, error message, review (see BuildReview)
        """
        mapname, title, description, visibility, previewpath = methodargs[:5]
        self.CancelReview()
        try:
            self.StartReview(mapname, title.strip(), description.strip(), int(visibility), previewpath.strip(), callbackid)
        except PublishError as e:
            self.reviewjob = None
            self.SendCallback(callbackid, [False, str(e), None])

    @jsbind(hascallback=True, manuallycallback=True)
    def getmyitems(self, methodargs, callbackid):
        """ Lists the maps the player published on the Workshop, also those published from another PC.

            Callback args: success, error message, list of {'id', 'title', 'timeupdated'}
        """
        self.CancelMyItems()
        if not _workshop or not _workshop.IsAvailable():
            self.SendCallback(callbackid, [False, 'Steam Workshop is not available', []])
            return
        self.myitemsjob = {'callbackid': callbackid, 'page': 0, 'items': [], 'query': None}
        self.RequestMyItemsPage()

    @jsbind(hascallback=True, manuallycallback=True)
    def linkitem(self, methodargs, callbackid):
        """ Remembers the local map of one of the player's Workshop items as published, for items
            published from another PC, so they can be updated from this PC.

            Args: published file id
            Callback args: success, error message, map name
        """
        self.CancelLink()
        try:
            self.StartLink(int(methodargs[0]), callbackid)
        except PublishError as e:
            self.linkjob = None
            self.SendCallback(callbackid, [False, str(e), ''])

    @jsbind(hascallback=True, manuallycallback=True)
    def choosepreview(self, methodargs, callbackid):
        """ Opens a file dialog to choose the preview image, starting in the folder of the current one.

            Args: current preview image path
            Callback args: chosen path (empty if cancelled), error message
        """
        if not _workshop:
            self.SendCallback(callbackid, ['', 'Workshop module not available'])
            return
        currentfolder = os.path.dirname(os.path.abspath(methodargs[0])) if methodargs[0] else ''
        if not os.path.isdir(currentfolder):
            currentfolder = ''
        patterns = ';'.join('*' + ext for ext in PREVIEW_EXTENSIONS)
        if self.previewdialogcallback is not None or \
                not _workshop.OpenFileDialog('Choose a preview image', 'Images (%s)' % patterns, patterns, currentfolder):
            self.SendCallback(callbackid, ['', 'A file dialog is already open'])
            return
        self.previewdialogcallback = callbackid
        RegisterTickMethod(self.OnPreviewDialogTick, 0.1, True, True)

    @jsbind(hascallback=True)
    def getpreviewimage(self, methodargs):
        """ Loads a preview image to show it in the menu, which can't load local files.

            Args: preview image path
            Callback args: image as data URI (empty if not valid), error message
        """
        previewpath = os.path.abspath(methodargs[0])
        try:
            self.ValidatePreviewImage(previewpath)
            with open(previewpath, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')
        except (PublishError, OSError) as e:
            return ['', str(e)]
        mimetype = PREVIEW_TYPES[os.path.splitext(previewpath)[1].lower()]
        return ['data:%s;base64,%s' % (mimetype, data), '']

    @jsbind(hascallback=True)
    def getminimap(self, methodargs):
        """ Returns the minimap of a local map (see GetMapMinimap).

            Args: map name
        """
        mapname = methodargs[0]
        if not IsLocalMap(mapname):
            return [None]
        return [GetMapMinimap(mapname)]

    @jsbind(hascallback=True)
    def generateminimap(self, methodargs):
        """ Loads a local map to generate its minimap (see minimapgen). The game returns to the menu after
            capturing it, then the menu asks for approval.

            Args: map name, margin around the playable area on each side in percent of its size
            Callback args: error message, empty if the map is loading
        """
        mapname = methodargs[0]
        if not IsLocalMap(mapname):
            return ['This map is not in your maps folder.']
        if self.publishjob:
            return ['Wait until the upload is done.']

        try:
            margin = float(methodargs[1]) / 100.0
        except (IndexError, TypeError, ValueError):
            margin = minimapgen.DEFAULT_MARGIN
        minimapgen.Request(mapname, margin)
        sessiondata = KeyValues('Session')
        sessiondata.SetString('system/network', 'offline')
        sessiondata.SetString('game/mode', 'minimapgen')
        sessiondata.SetString('game/mission', mapname)
        matchmaking.CreateSession(sessiondata)
        matchmaking.matchsession.Command(KeyValues('Start'))
        return ['']

    @jsbind(hascallback=True)
    def getgeneratedminimap(self, methodargs):
        """ Returns the generated minimap waiting for approval {mapname, success, error, src, positions},
            or None. """
        info = minimapgen.generated
        if not info:
            return [None]
        result = {'mapname': info['mapname'], 'success': info['success'], 'error': info['error'],
                  'src': '', 'positions': []}
        if info['success']:
            result['src'] = 'vtf://%s.vtf' % info['file']
            result['positions'] = GetStartPositions(info['mapname'], info['pos_x'], info['pos_y'], info['scale'])
        return [result]

    @jsbind(hascallback=True)
    def approveminimap(self, methodargs):
        """ Uses the generated minimap as the minimap of its map: materials/overviews/<map>.vtf, with the
            minimap values in the res file of the map. Always the map's own material, so a minimap of
            another map named in the res file isn't overwritten.

            Args: map name
            Callback args: error message (empty if saved), the new minimap (see GetMapMinimap)
        """
        mapname = methodargs[0]
        info = minimapgen.generated
        if not info or not info['success'] or info['mapname'] != mapname:
            return ['There is no generated minimap for this map.', None]

        material = 'overviews/%s' % mapname
        try:
            vtfpath = os.path.join('materials', material + '.vtf')
            os.makedirs(os.path.dirname(vtfpath), exist_ok=True)
            shutil.copyfile(minimapgen.GetGeneratedPath(info), vtfpath)
            vmtpath = os.path.join('materials', material + '.vmt')
            if not os.path.isfile(vmtpath):
                with open(vmtpath, 'wb') as f:
                    f.write((MINIMAP_VMT % material).encode('utf-8'))
            WriteMinimapRes(mapname, {'material': material, 'pos_x': info['pos_x'], 'pos_y': info['pos_y'],
                                      'scale': info['scale'], 'rotate': 0})
        except OSError as e:
            return ["The minimap couldn't be saved: %s" % e, None]

        minimapgen.DiscardGenerated()
        return ['', GetMapMinimap(mapname)]

    @jsbind()
    def discardminimap(self, methodargs):
        """ Removes the generated minimap without using it. """
        minimapgen.DiscardGenerated()

    @jsbind()
    def openlegalagreement(self, methodargs):
        self.OpenURL(LEGAL_AGREEMENT_URL)

    @jsbind()
    def openitem(self, methodargs):
        self.OpenURL(ITEM_URL % methodargs[0])

    def OpenURL(self, url):
        from steam import steamapicontext
        steamfriends = steamapicontext.SteamFriends()
        if steamfriends:
            steamfriends.ActivateGameOverlayToWebPage(url)

    # Local maps and published info
    def ListLocalMaps(self):
        """ Lists the maps in the mod maps folder, except the official maps, with info from previous publishes. """
        publishedinfo = self.LoadPublishedInfo()
        officialmaps = LoadOfficialMaps()
        maps = []
        for filename in sorted(os.listdir('maps')):
            mapname, ext = os.path.splitext(filename)
            if ext != '.bsp' or mapname.lower() in officialmaps:
                continue
            info = publishedinfo.get(mapname, {})
            maps.append({
                'name': mapname,
                'publishedfileid': info.get('publishedfileid', ''),
                'title': info.get('title', mapname),
                'description': info.get('description', ''),
                'visibility': info.get('visibility', _workshop.VISIBILITY_PRIVATE if _workshop else 2),
                'preview': info.get('preview', ''),
                'lastupload': info.get('lastupload', 0),
            })
        return maps

    def LoadPublishedInfo(self):
        return LoadPublishedInfo()

    def SavePublishedInfo(self, job, uploaded=False):
        """ Saves the info of a published map. After a successful upload, also saves the
            uploaded files, used to review the next update. """
        publishedinfo = self.LoadPublishedInfo()
        info = publishedinfo.get(job['mapname'], {})
        info.update({
            # Stored as string, javascript numbers can't hold 64 bit ids
            'publishedfileid': str(job['publishedfileid']),
            'title': job['title'],
            'description': job['description'],
            'visibility': job['visibility'],
            'preview': job['previewpath'],
        })
        if uploaded:
            info['files'] = job['files']
            info['lastupload'] = int(time.time())
            if job['previewsha1']:
                info['previewsha1'] = job['previewsha1']
        publishedinfo[job['mapname']] = info
        self.WritePublishedInfo(publishedinfo)

    def WritePublishedInfo(self, publishedinfo):
        os.makedirs(WORKSHOP_DIR, exist_ok=True)
        with open(PUBLISHED_INFO_PATH, 'wt', encoding='utf-8') as f:
            json.dump(publishedinfo, f, indent=4, sort_keys=True)

    # Publishing
    def ValidatePublishRequest(self, mapname, title, description, previewpath):
        """ Checks the input of a publish or review. Returns the absolute preview image path. """
        if not _workshop or not _workshop.IsAvailable():
            raise PublishError('Steam Workshop is not available')
        if not os.path.isfile(os.path.join('maps', mapname + '.bsp')):
            raise PublishError('Map %s does not exist' % mapname)
        if mapname.lower() in LoadOfficialMaps():
            raise PublishError('%s is an official map and can\'t be published' % mapname)
        if not title:
            raise PublishError('A title is required')
        if len(title) > MAX_TITLE_LENGTH:
            raise PublishError('The title is longer than %d characters' % MAX_TITLE_LENGTH)
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise PublishError('The description is longer than %d characters' % MAX_DESCRIPTION_LENGTH)
        if previewpath:
            previewpath = os.path.abspath(previewpath)
            self.ValidatePreviewImage(previewpath)
        return previewpath

    def ValidatePreviewImage(self, previewpath):
        if not os.path.isfile(previewpath):
            raise PublishError('Preview image %s does not exist' % previewpath)
        if os.path.splitext(previewpath)[1].lower() not in PREVIEW_EXTENSIONS:
            raise PublishError('The preview image must be a jpg or png file')
        if os.path.getsize(previewpath) > MAX_PREVIEW_SIZE:
            raise PublishError('The preview image can be at most 1 MB')

    def StageAndValidateMap(self, mapname):
        """ Stages the map files and checks the content is allowed. Returns the staging folder. """
        contentpath = self.StageMap(mapname)
        # Players only mount items with allowed content, which includes the files embedded in the map
        valid, reason = _workshop.ValidateItemFolder(contentpath)
        if not valid:
            raise PublishError('The map can\'t be published: %s' % reason)
        return contentpath

    def StartPublish(self, mapname, title, description, visibility, changenote, previewpath):
        previewpath = self.ValidatePublishRequest(mapname, title, description, previewpath)

        publishedfileid = self.LoadPublishedInfo().get(mapname, {}).get('publishedfileid', '')

        contentpath = self.StageAndValidateMap(mapname)

        self.publishjob = {
            'mapname': mapname,
            'title': title,
            'description': description,
            'visibility': visibility,
            'changenote': changenote,
            'previewpath': previewpath,
            'publishedfileid': int(publishedfileid) if publishedfileid else 0,
            'needslegalagreement': False,
            'contentpath': contentpath,
            # Saved after the upload, to review the next update
            'files': BuildFileList(contentpath),
            'previewsha1': HashFile(previewpath) if previewpath else None,
        }
        self.LogPublishRequest()

        if self.publishjob['publishedfileid']:
            self.StartUpload()
        else:
            call = _workshop.CreateItem()
            LogPublish('creating a new item, call %s' % call)
            if call == _workshop.API_CALL_INVALID:
                raise PublishError('Failed to create the Workshop item')
            self.publishjob['state'] = 'creating'
            self.publishjob['call'] = call
            self.NotifyProgress('creating', 0, 0)

        if not IsTickMethodRegistered(self.OnPublishTick):
            RegisterTickMethod(self.OnPublishTick, 0.2, True, True)

    # Reviewing updates
    def StartReview(self, mapname, title, description, visibility, previewpath, callbackid):
        previewpath = self.ValidatePublishRequest(mapname, title, description, previewpath)
        info = self.LoadPublishedInfo().get(mapname, {})
        publishedfileid = info.get('publishedfileid', '')
        if not publishedfileid:
            raise PublishError('Map %s has not been published yet' % mapname)

        contentpath = self.StageAndValidateMap(mapname)
        self.reviewjob = {
            'mapname': mapname,
            'publishedfileid': publishedfileid,
            'info': info,
            'title': title,
            'description': description,
            'visibility': visibility,
            'previewpath': previewpath,
            'files': BuildFileList(contentpath),
            'callbackid': callbackid,
            'fetch': self.StartItemFetch(int(publishedfileid)),
        }
        if not IsTickMethodRegistered(self.OnReviewTick):
            RegisterTickMethod(self.OnReviewTick, 0.1, True, True)

    def OnReviewTick(self):
        job = self.reviewjob
        if not job:
            self.StopReviewTick()
            return
        if self.PollItemFetch(job['fetch']):
            self.FinishReview()

    # Fetching the current state of a Workshop item
    def StartItemFetch(self, item):
        """ Requests the current details of an item and downloads its current version, without
            subscribing. Steam only downloads what changed, and nothing if its cached copy is up
            to date. Poll with PollItemFetch. """
        return {
            'item': item,
            'query': _workshop.SendDetailsQuery(item),
            'details': None,
            'download': 'pending' if _workshop.DownloadItem(item, True) else 'failed',
            'downloadstart': time.time(),
        }

    def PollItemFetch(self, fetch):
        """ Returns True once the details request and the download finished (or failed).
            Results are in fetch['details'] (None if failed) and fetch['download'] ('done' or 'failed'). """
        if fetch['query']:
            results = _workshop.GetQueryResults(*fetch['query'])
            if results is not None:
                fetch['query'] = None
                if not results['iofailure'] and results['result'] == _workshop.RESULT_OK and results['items']:
                    fetch['details'] = results['items'][0]

        if fetch['download'] == 'pending':
            item = fetch['item']
            flags = _workshop.GetItemState(item)
            elapsed = time.time() - fetch['downloadstart']
            if flags & (_workshop.ITEM_STATE_DOWNLOADING | _workshop.ITEM_STATE_DOWNLOAD_PENDING):
                downloaded, total = _workshop.GetItemDownloadProgress(item)
                self.NotifyReviewProgress(downloaded, total)
                if elapsed > REVIEW_DOWNLOAD_TIMEOUT:
                    fetch['download'] = 'failed'
            elif flags & _workshop.ITEM_STATE_INSTALLED and not flags & _workshop.ITEM_STATE_NEEDS_UPDATE:
                fetch['download'] = 'done'
            elif elapsed > REVIEW_DOWNLOAD_START_TIMEOUT:
                # Steam didn't start the download
                fetch['download'] = 'failed'

        return not fetch['query'] and fetch['download'] != 'pending'

    def CancelItemFetch(self, fetch):
        if fetch and fetch['query']:
            _workshop.ReleaseQuery(fetch['query'][0])
            fetch['query'] = None

    def FinishReview(self):
        job = self.reviewjob
        self.reviewjob = None
        self.StopReviewTick()
        self.SendCallback(job['callbackid'], [True, '', self.BuildReview(job)])

    def BuildReview(self, job):
        """ Compares the update with the item on the Workshop.

            The details (title, description, visibility) are compared with the details on the
            Workshop, or with the last upload if Steam didn't return them. The files are compared
            with the downloaded current version of the item, or with the files of the last upload
            if it could not be downloaded.
        """
        info = job['info']
        item = int(job['publishedfileid'])
        details = job['fetch']['details']

        if details:
            current = details
            detailssource = 'workshop'
        else:
            current = info
            detailssource = 'lastupload'

        fields = []
        for key in ['title', 'description']:
            fields.append({
                'key': key,
                'current': current.get(key, ''),
                'new': job[key],
                'changed': NormalizeText(current.get(key, '')) != NormalizeText(job[key]),
            })
        currentvisibility = int(current.get('visibility', job['visibility']))
        fields.append({
            'key': 'visibility',
            'current': currentvisibility,
            'new': job['visibility'],
            'changed': currentvisibility != job['visibility'],
        })

        # The preview image only changes if a file is given
        if not job['previewpath']:
            preview = {'status': 'keep', 'file': ''}
        else:
            changed = HashFile(job['previewpath']) != info.get('previewsha1')
            preview = {'status': 'changed' if changed else 'same', 'file': os.path.basename(job['previewpath'])}

        installfolder = _workshop.GetItemInstallFolder(item) if job['fetch']['download'] == 'done' else None
        if installfolder and os.path.isdir(installfolder):
            currentfiles = BuildFileList(installfolder)
            filessource = 'workshop'
        elif 'files' in info:
            currentfiles = info['files']
            filessource = 'lastupload'
        else:
            currentfiles = {}
            filessource = 'none'
        files = CompareFileLists(currentfiles, job['files'])

        numchangedfiles = len([f for f in files if f['status'] != 'same'])
        return {
            'mapname': job['mapname'],
            'publishedfileid': job['publishedfileid'],
            'fields': fields,
            'preview': preview,
            'files': files,
            'numchangedfiles': numchangedfiles,
            'numsamefiles': len(files) - numchangedfiles,
            'filessource': filessource,
            'detailssource': detailssource,
            'lastupload': info.get('lastupload', 0),
            'haschanges': numchangedfiles > 0 or preview['status'] == 'changed' or any(f['changed'] for f in fields),
        }

    def CancelReview(self):
        if self.reviewjob:
            self.CancelItemFetch(self.reviewjob['fetch'])
        self.reviewjob = None
        self.StopReviewTick()

    def StopReviewTick(self):
        if IsTickMethodRegistered(self.OnReviewTick):
            UnregisterTickMethod(self.OnReviewTick)

    # The player's Workshop items
    def RequestMyItemsPage(self):
        """ Requests the next page of the player's published maps. Steam only returns the items of
            the account, so maps of other players are never listed. """
        from steam import steamapicontext
        job = self.myitemsjob
        job['page'] += 1
        accountid = steamapicontext.SteamUser().GetSteamID().GetAccountID()
        job['query'] = _workshop.SendUserQuery(accountid, _workshop.USER_LIST_PUBLISHED,
                                               _workshop.USER_SORT_LAST_UPDATED_DESC, job['page'], WORKSHOP_TAGS[0])
        if not job['query']:
            self.FinishMyItems(False, 'Failed to request your Workshop items from Steam')
            return
        if not IsTickMethodRegistered(self.OnMyItemsTick):
            RegisterTickMethod(self.OnMyItemsTick, 0.1, True, True)

    def OnMyItemsTick(self):
        job = self.myitemsjob
        if not job:
            self.StopMyItemsTick()
            return

        results = _workshop.GetQueryResults(*job['query'])
        if results is None:
            return
        job['query'] = None

        if results['iofailure'] or results['result'] != _workshop.RESULT_OK:
            self.FinishMyItems(False, 'Failed to get your Workshop items from Steam')
            return

        for data in results['items']:
            job['items'].append({
                # String, javascript numbers can't hold 64 bit ids
                'id': str(data['publishedfileid']),
                'title': data['title'],
                'timeupdated': data['timeupdated'],
            })

        if results['items'] and len(job['items']) < results['total'] and job['page'] < MAX_MY_ITEMS_PAGES:
            self.RequestMyItemsPage()
        else:
            self.FinishMyItems(True, '')

    def FinishMyItems(self, success, error):
        job = self.myitemsjob
        self.myitemsjob = None
        self.StopMyItemsTick()
        self.SendCallback(job['callbackid'], [success, error, job['items']])

    def CancelMyItems(self):
        if self.myitemsjob and self.myitemsjob['query']:
            _workshop.ReleaseQuery(self.myitemsjob['query'][0])
        self.myitemsjob = None
        self.StopMyItemsTick()

    def StopMyItemsTick(self):
        if IsTickMethodRegistered(self.OnMyItemsTick):
            UnregisterTickMethod(self.OnMyItemsTick)

    # Linking Workshop items published from another PC
    def StartLink(self, item, callbackid):
        if not _workshop or not _workshop.IsAvailable():
            raise PublishError('Steam Workshop is not available')
        self.linkjob = {
            'callbackid': callbackid,
            'fetch': self.StartItemFetch(item),
        }
        if not IsTickMethodRegistered(self.OnLinkTick):
            RegisterTickMethod(self.OnLinkTick, 0.1, True, True)

    def OnLinkTick(self):
        job = self.linkjob
        if not job:
            self.StopLinkTick()
            return
        if not self.PollItemFetch(job['fetch']):
            return

        self.linkjob = None
        self.StopLinkTick()
        try:
            mapname = self.LinkItem(job['fetch'])
        except PublishError as e:
            self.SendCallback(job['callbackid'], [False, str(e), ''])
            return
        self.SendCallback(job['callbackid'], [True, '', mapname])

    def LinkItem(self, fetch):
        """ Finds the map in the downloaded item, and remembers the local map as published as this item.
            Only items of the player can be linked.

            Returns the map name.
        """
        item = fetch['item']
        details = fetch['details']
        if not details:
            raise PublishError('Could not get the details of the Workshop item from Steam')
        from steam import steamapicontext
        if details['owner'] != steamapicontext.SteamUser().GetSteamID().ConvertToUint64():
            raise PublishError('This Workshop item was published by someone else')
        if fetch['download'] != 'done':
            raise PublishError('Could not download the Workshop item to find its map')

        mapsfolder = os.path.join(_workshop.GetItemInstallFolder(item) or '', 'maps')
        mapnames = [os.path.splitext(f)[0] for f in os.listdir(mapsfolder) if f.lower().endswith('.bsp')] if os.path.isdir(mapsfolder) else []
        if len(mapnames) != 1:
            raise PublishError('The Workshop item does not contain exactly one map')
        mapname = mapnames[0]

        if not os.path.isfile(os.path.join('maps', mapname + '.bsp')):
            raise PublishError('The map of this Workshop item, %s, is not in your maps folder' % mapname)
        if mapname.lower() in LoadOfficialMaps():
            raise PublishError('%s is an official map and can\'t be published' % mapname)

        publishedinfo = self.LoadPublishedInfo()
        info = publishedinfo.get(mapname, {})
        if info.get('publishedfileid', str(item)) != str(item):
            raise PublishError('Map %s is already published as Workshop item %s' % (mapname, info['publishedfileid']))
        info.update({
            'publishedfileid': str(item),
            'title': details['title'],
            'description': details['description'],
            'visibility': details['visibility'],
            'preview': info.get('preview', ''),
        })
        publishedinfo[mapname] = info
        self.WritePublishedInfo(publishedinfo)
        return mapname

    def CancelLink(self):
        if self.linkjob:
            self.CancelItemFetch(self.linkjob['fetch'])
        self.linkjob = None
        self.StopLinkTick()

    def StopLinkTick(self):
        if IsTickMethodRegistered(self.OnLinkTick):
            UnregisterTickMethod(self.OnLinkTick)

    # Preview image file dialog
    def OnPreviewDialogTick(self):
        path = _workshop.GetFileDialogResult()
        if path is None:
            return
        callbackid = self.previewdialogcallback
        self.StopPreviewDialogTick()
        error = ''
        if path:
            try:
                self.ValidatePreviewImage(path)
            except PublishError as e:
                error = str(e)
        self.SendCallback(callbackid, [path, error])

    def StopPreviewDialogTick(self):
        self.previewdialogcallback = None
        if IsTickMethodRegistered(self.OnPreviewDialogTick):
            UnregisterTickMethod(self.OnPreviewDialogTick)

    def StageMap(self, mapname):
        """ Copies the files of a map into a staging folder mirroring the game directory.

            Returns the absolute path of the staging folder.
        """
        stagingpath = os.path.abspath(os.path.join(STAGING_DIR, mapname))
        try:
            if os.path.isdir(stagingpath):
                shutil.rmtree(stagingpath)
            os.makedirs(os.path.join(stagingpath, 'maps'))

            for suffix in MAP_FILE_SUFFIXES:
                srcpath = os.path.join('maps', mapname + suffix)
                if os.path.isfile(srcpath):
                    shutil.copy2(srcpath, os.path.join(stagingpath, srcpath))

            # Overview image used by the lobby, referenced from the res file
            respath = os.path.join('maps', mapname + '.res')
            if os.path.isfile(respath):
                overview = kvdict.LoadFileIntoDictionaries(respath).get('material', '')
                for ext in ['.vmt', '.vtf']:
                    srcpath = os.path.join('materials', overview + ext)
                    if overview and os.path.isfile(srcpath):
                        os.makedirs(os.path.dirname(os.path.join(stagingpath, srcpath)), exist_ok=True)
                        shutil.copy2(srcpath, os.path.join(stagingpath, srcpath))
        except (IOError, OSError) as e:
            raise PublishError('Failed to copy map files: %s' % e)
        return stagingpath

    def LogPublishRequest(self):
        """ What is uploaded: the item, the files of the content folder and the preview image. """
        job = self.publishjob
        LogPublish('map %s, %s' % (job['mapname'], 'updating item %s' % job['publishedfileid']
                                   if job['publishedfileid'] else 'publishing as a new item'))
        try:
            from steam import steamapicontext
            LogPublish('app id %s, Steam user %s' % (steamapicontext.SteamUtils().GetAppID(),
                                                     steamapicontext.SteamUser().GetSteamID().ConvertToUint64()))
        except Exception as e:
            LogPublish('could not read the app id and Steam user: %s' % e)
        LogPublish('content folder %s' % job['contentpath'])
        total = 0
        for root, dirs, files in os.walk(job['contentpath']):
            for name in files:
                path = os.path.join(root, name)
                size = os.path.getsize(path)
                total += size
                LogPublish('  %s (%d bytes)' % (os.path.relpath(path, job['contentpath']), size))
        LogPublish('%d bytes in the content folder' % total)
        if job['previewpath']:
            LogPublish('preview image %s (%d bytes)' % (job['previewpath'], os.path.getsize(job['previewpath'])))
        else:
            LogPublish('no preview image')

    def StartUpload(self):
        job = self.publishjob
        handle = _workshop.StartItemUpdate(job['publishedfileid'])
        LogPublish('update handle %s for item %s' % (handle, job['publishedfileid']))
        if handle == _workshop.UPDATE_HANDLE_INVALID:
            raise PublishError('Failed to start the Workshop item update')

        # One at a time, so the log shows which one Steam refused
        settings = [
            ('title', lambda: _workshop.SetItemTitle(handle, job['title'])),
            ('description', lambda: _workshop.SetItemDescription(handle, job['description'])),
            ('visibility', lambda: _workshop.SetItemVisibility(handle, job['visibility'])),
            ('tags', lambda: _workshop.SetItemTags(handle, WORKSHOP_TAGS)),
            ('content folder', lambda: _workshop.SetItemContent(handle, job['contentpath'])),
        ]
        if job['previewpath']:
            settings.append(('preview image', lambda: _workshop.SetItemPreview(handle, job['previewpath'])))
        for name, setting in settings:
            if not setting():
                LogPublish('Steam refused the %s' % name)
                raise PublishError('Failed to set the %s of the Workshop item' % name)

        call = _workshop.SubmitItemUpdate(handle, job['changenote'])
        LogPublish('submitted the update, call %s' % call)
        if call == _workshop.API_CALL_INVALID:
            raise PublishError('Failed to submit the Workshop item')
        job['state'] = 'uploading'
        job['updatehandle'] = handle
        job['call'] = call
        job['submittime'] = time.time()
        job['loggedstatus'] = None
        job['loggedtime'] = 0.0

    def OnPublishTick(self):
        job = self.publishjob
        if not job:
            self.StopPublishTick()
            return

        try:
            if job['state'] == 'creating':
                result = _workshop.GetCreateItemResult(job['call'])
                if result is None:
                    return
                LogPublish('created the item: %s' % FormatCallResult(result))
                self.CheckResult(result, 'Failed to create the Workshop item')
                job['publishedfileid'] = result['publishedfileid']
                job['needslegalagreement'] = result['needslegalagreement']
                # Remember the id right away, so a failed upload updates this item next time
                self.SavePublishedInfo(job)
                self.StartUpload()
            elif job['state'] == 'uploading':
                status, processed, total = _workshop.GetItemUpdateProgress(job['updatehandle'])
                job['progress'] = (status, processed, total)
                self.NotifyProgress(status, processed, total)

                now = time.time()
                if status != job['loggedstatus'] or now - job['loggedtime'] >= PUBLISH_LOG_INTERVAL:
                    job['loggedstatus'] = status
                    job['loggedtime'] = now
                    LogPublish('upload status %s: %d of %d bytes, %.0f seconds after submitting' % (
                        UPDATE_STATUS_NAMES.get(status, status), processed, total, now - job['submittime']))

                result = _workshop.GetSubmitItemUpdateResult(job['call'])
                if result is None:
                    return
                LogPublish('uploaded: %s' % FormatCallResult(result))
                self.CheckResult(result, 'Failed to upload the map')
                job['needslegalagreement'] = job['needslegalagreement'] or result['needslegalagreement']
                self.SavePublishedInfo(job, uploaded=True)
                self.FinishPublish(True, '')
        except PublishError as e:
            self.FinishPublish(False, str(e))

    def CheckResult(self, result, message):
        if result['iofailure']:
            raise PublishError('%s: lost connection with Steam' % message)
        if result['result'] != _workshop.RESULT_OK:
            reason = RESULT_MESSAGES.get(result['result'], 'Steam error code %d' % result['result'])
            raise PublishError('%s: %s' % (message, reason))

    def FinishPublish(self, success, message):
        LogPublish('done' if success else 'failed: %s' % message)
        job = self.publishjob
        self.publishjob = None
        self.StopPublishTick()
        publishedfileid = str(job['publishedfileid']) if job['publishedfileid'] else ''
        self.NotifyFinished(success, publishedfileid, message, job['needslegalagreement'])

    def StopPublishTick(self):
        if IsTickMethodRegistered(self.OnPublishTick):
            UnregisterTickMethod(self.OnPublishTick)

    # Notifications to javascript
    def NotifyProgress(self, status, processed, total):
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnPublishProgress', [status, processed, total])

    def NotifyReviewProgress(self, downloaded, total):
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnReviewProgress', [downloaded, total])

    def NotifyFinished(self, success, publishedfileid, message, needslegalagreement=False):
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnPublishFinished', [success, publishedfileid, message, needslegalagreement])
