""" Provides the workshop webview component, used to publish maps to the Steam Workshop.

    Publishing a map copies its files into a staging folder that mirrors the game
    directory (maps/<name>.bsp, maps/<name>.res, ...), creates a Workshop item if the
    map was not published before, and uploads the staging folder as the item content.
    The published file id of each map is remembered in workshop/published.json, so
    publishing the same map again updates the existing item.
"""
import os
import json
import shutil

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

#: Files belonging to a map, found next to maps/<name>.bsp
MAP_FILE_SUFFIXES = ['.bsp', '.res', '.recast', '.wars', '.layout', 'mapheightfielddata.bin']
WORKSHOP_TAGS = ['Map']
MAX_PREVIEW_SIZE = 1024 * 1024
PREVIEW_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
MAX_TITLE_LENGTH = 128
MAX_DESCRIPTION_LENGTH = 8000

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


def LoadPublishedInfo():
    """ Returns the info of maps published by the local player, by map name. """
    try:
        with open(PUBLISHED_INFO_PATH, 'rt', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, ValueError):
        return {}


class WebWorkshop(WebViewComponent):
    defaultobjectname = 'workshop'

    jshandler = None
    #: State of the map being published, or None
    publishjob = None

    def OnDestroy(self):
        super().OnDestroy()

        self.StopPublishTick()

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
        """ Lists the maps in the mod maps folder, with info from previous publishes. """
        publishedinfo = self.LoadPublishedInfo()
        maps = []
        for filename in sorted(os.listdir('maps')):
            mapname, ext = os.path.splitext(filename)
            if ext != '.bsp':
                continue
            info = publishedinfo.get(mapname, {})
            maps.append({
                'name': mapname,
                'publishedfileid': info.get('publishedfileid', ''),
                'title': info.get('title', mapname),
                'description': info.get('description', ''),
                'visibility': info.get('visibility', _workshop.VISIBILITY_PRIVATE if _workshop else 2),
                'preview': info.get('preview', ''),
            })
        return maps

    def LoadPublishedInfo(self):
        return LoadPublishedInfo()

    def SavePublishedInfo(self, job):
        publishedinfo = self.LoadPublishedInfo()
        publishedinfo[job['mapname']] = {
            # Stored as string, javascript numbers can't hold 64 bit ids
            'publishedfileid': str(job['publishedfileid']),
            'title': job['title'],
            'description': job['description'],
            'visibility': job['visibility'],
            'preview': job['previewpath'],
        }
        os.makedirs(WORKSHOP_DIR, exist_ok=True)
        with open(PUBLISHED_INFO_PATH, 'wt', encoding='utf-8') as f:
            json.dump(publishedinfo, f, indent=4, sort_keys=True)

    # Publishing
    def StartPublish(self, mapname, title, description, visibility, changenote, previewpath):
        if not _workshop or not _workshop.IsAvailable():
            raise PublishError('Steam Workshop is not available')
        if not os.path.isfile(os.path.join('maps', mapname + '.bsp')):
            raise PublishError('Map %s does not exist' % mapname)
        if not title:
            raise PublishError('A title is required')
        if len(title) > MAX_TITLE_LENGTH:
            raise PublishError('The title is longer than %d characters' % MAX_TITLE_LENGTH)
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise PublishError('The description is longer than %d characters' % MAX_DESCRIPTION_LENGTH)
        if previewpath:
            previewpath = os.path.abspath(previewpath)
            if not os.path.isfile(previewpath):
                raise PublishError('Preview image %s does not exist' % previewpath)
            if os.path.splitext(previewpath)[1].lower() not in PREVIEW_EXTENSIONS:
                raise PublishError('The preview image must be a jpg, png or gif file')
            if os.path.getsize(previewpath) > MAX_PREVIEW_SIZE:
                raise PublishError('The preview image must be smaller than 1 MB')

        publishedfileid = self.LoadPublishedInfo().get(mapname, {}).get('publishedfileid', '')

        # Players only mount items with allowed content, which includes the files embedded in the map
        contentpath = self.StageMap(mapname)
        valid, reason = _workshop.ValidateItemFolder(contentpath)
        if not valid:
            raise PublishError('The map can\'t be published: %s' % reason)

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
                self.SavePublishedInfo(job)
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

    def NotifyFinished(self, success, publishedfileid, message, needslegalagreement=False):
        if self.jshandler:
            self.Invoke(self.jshandler, 'OnPublishFinished', [success, publishedfileid, message, needslegalagreement])
