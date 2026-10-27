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

from cef import WebViewComponent, jsbind
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
import kvdict

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
            and whether a map is being published. """
        if not _workshop:
            return [False, 'Workshop module not available', [], False]
        available = _workshop.IsAvailable()
        error = '' if available else _workshop.GetError()
        return [available, error, self.ListLocalMaps(), self.publishjob is not None]

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

        if self.publishjob['publishedfileid']:
            self.StartUpload()
        else:
            call = _workshop.CreateItem()
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

    def StartUpload(self):
        job = self.publishjob
        handle = _workshop.StartItemUpdate(job['publishedfileid'])
        if handle == _workshop.UPDATE_HANDLE_INVALID:
            raise PublishError('Failed to start the Workshop item update')

        if not (_workshop.SetItemTitle(handle, job['title']) and
                _workshop.SetItemDescription(handle, job['description']) and
                _workshop.SetItemVisibility(handle, job['visibility']) and
                _workshop.SetItemTags(handle, WORKSHOP_TAGS) and
                _workshop.SetItemContent(handle, job['contentpath'])):
            raise PublishError('Failed to set the Workshop item properties')
        if job['previewpath'] and not _workshop.SetItemPreview(handle, job['previewpath']):
            raise PublishError('Failed to set the preview image')

        call = _workshop.SubmitItemUpdate(handle, job['changenote'])
        if call == _workshop.API_CALL_INVALID:
            raise PublishError('Failed to submit the Workshop item')
        job['state'] = 'uploading'
        job['updatehandle'] = handle
        job['call'] = call

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
                self.CheckResult(result, 'Failed to create the Workshop item')
                job['publishedfileid'] = result['publishedfileid']
                job['needslegalagreement'] = result['needslegalagreement']
                # Remember the id right away, so a failed upload updates this item next time
                self.SavePublishedInfo(job)
                self.StartUpload()
            elif job['state'] == 'uploading':
                status, processed, total = _workshop.GetItemUpdateProgress(job['updatehandle'])
                self.NotifyProgress(status, processed, total)

                result = _workshop.GetSubmitItemUpdateResult(job['call'])
                if result is None:
                    return
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
