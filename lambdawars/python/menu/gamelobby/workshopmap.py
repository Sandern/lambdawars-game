""" Makes sure players in a game lobby have the selected map when it comes from the Steam Workshop.

    The lobby owner publishes the Workshop item id and revision of the selected map in the lobby data.
    Other players download the item when they don't have the map (or have a different version), and
    can't get ready until the map is available.
"""
import filesystem
from gameinterface import GetMapHeader
from steam import steamapicontext, CSteamID

from ..workshop.workshop import LoadPublishedInfo

try:
    import _workshop
except ImportError:
    _workshop = None


def IsWorkshopAvailable():
    return _workshop is not None and _workshop.IsAvailable()


def FindMapWorkshopItem(mapname):
    """ Returns the published file id (as string) of the mounted Workshop item providing the map,
        or an empty string if the map is part of the game. """
    if not mapname or not IsWorkshopAvailable():
        return ''
    # Maps of the game itself are found first, even if a Workshop item has a map with the same name.
    # The exception are maps the local player published, which the author still has in the maps folder.
    if filesystem.FileExists('maps/%s.bsp' % mapname, 'MOD'):
        return LoadPublishedInfo().get(mapname, {}).get('publishedfileid', '')
    item = _workshop.FindMapItem(mapname)
    return str(item) if item else ''


def GetMapRevision(mapname):
    """ Returns the revision of the local copy of the map as string, or None if the map is missing. """
    if not mapname:
        return None
    try:
        return str(GetMapHeader('maps/%s.bsp' % mapname).maprevision)
    except ValueError:
        return None


class LobbyMapStatus(object):
    """ Availability of the lobby map for the local player.

        States:
            ok: map is available (and matches the host's revision)
            downloading: map is being downloaded from the Workshop
            missing: map is not available and not on the Workshop
            mismatch: local map differs from the host's and can't be updated
            failed: download from the Workshop failed
    """
    def __init__(self):
        super().__init__()

        self.state = 'ok'
        self.progress = 0
        self.error = ''
        # Workshop items requested for this lobby, so a failed or outdated item is not requested every update
        self.requesteditems = set()

    def Update(self, mapname, workshopid, revision):
        """ Updates the status for the given lobby map, requesting a download if needed.

            Returns:
                bool: True if the map became available, meaning the map list should be rebuilt.
        """
        wasavailable = self.state == 'ok'
        self.progress = 0
        self.error = ''

        localrevision = GetMapRevision(mapname)
        if not mapname or (localrevision is not None and (not revision or localrevision == revision)):
            self.state = 'ok'
        elif workshopid and IsWorkshopAvailable():
            self.UpdateWorkshopItem(int(workshopid), localrevision)
        elif localrevision is not None:
            self.state = 'mismatch'
        else:
            self.state = 'missing'

        return not wasavailable and self.state == 'ok'

    def UpdateWorkshopItem(self, item, localrevision):
        status = _workshop.GetItemStatus(item)
        if item not in self.requesteditems:
            # Downloads the item, or updates it when the local copy differs from the host's
            self.requesteditems.add(item)
            if _workshop.RequestItem(item):
                status = _workshop.GetItemStatus(item)

        if status == 'downloading':
            self.state = 'downloading'
            downloaded, total = _workshop.GetItemDownloadProgress(item)
            self.progress = int(100 * downloaded / total) if total else 0
        elif status in ('failed', 'rejected'):
            self.state = 'failed'
            self.error = _workshop.GetItemError(item)
        elif localrevision is not None:
            # Up to date with the Workshop, but the host has another version
            self.state = 'mismatch'
        else:
            self.state = 'missing'

    def ToDict(self):
        return {
            'state': self.state,
            'progress': self.progress,
            'error': self.error,
        }


#: States of LobbyMapStatus, also reported to the lobby for each player
MAP_STATES = ('ok', 'downloading', 'missing', 'mismatch', 'failed')


def FormatPlayerMapStatus(workshopid, state, progress):
    """ Formats the map status a player reports to the lobby owner: "<workshop id>:<state>:<progress>".
        The workshop id ties the status to the map, so statuses for a previously selected map are ignored. """
    return '%s:%s:%d' % (workshopid, state, progress)


def ParsePlayerMapStatus(value, workshopid):
    """ Returns (state, progress) of a reported map status, or ('', 0) if it's invalid or not
        for the current Workshop map. """
    parts = value.split(':') if value else []
    if not workshopid or len(parts) != 3 or parts[0] != workshopid or parts[1] not in MAP_STATES or not parts[2].isdigit():
        return '', 0
    return parts[1], min(100, int(parts[2]))


def IsValidPlayerMapStatus(value):
    parts = value.split(':')
    return len(parts) == 3 and parts[0].isdigit() and parts[1] in MAP_STATES and parts[2].isdigit()


class LobbyWorkshopMapInfo(object):
    """ Details of the Workshop item of the lobby map (title, preview image, author) and whether the
        local player is subscribed to it, shown in the lobby. """
    def __init__(self):
        super().__init__()

        self.item = 0
        self.details = None
        self.subscribed = False
        self.query = None

    def Update(self, workshopid):
        """ Requests the details when the Workshop map changed and polls the request.

            Returns:
                bool: True if the info changed and the lobby should be updated.
        """
        item = int(workshopid) if workshopid else 0
        changed = False
        if item != self.item:
            self.Cancel()
            self.item = item
            self.details = None
            changed = True
            if item and IsWorkshopAvailable():
                self.query = _workshop.SendDetailsQuery(item)

        if self.query:
            results = _workshop.GetQueryResults(*self.query)
            if results is not None:
                self.query = None
                if not results['iofailure'] and results['result'] == _workshop.RESULT_OK and results['items']:
                    self.details = results['items'][0]
                    changed = True

        subscribed = bool(item and IsWorkshopAvailable() and _workshop.GetItemState(item) & _workshop.ITEM_STATE_SUBSCRIBED)
        if subscribed != self.subscribed:
            self.subscribed = subscribed
            changed = True
        return changed

    def Subscribe(self):
        if self.item and IsWorkshopAvailable():
            _workshop.SubscribeItem(self.item)

    def Cancel(self):
        if self.query:
            _workshop.ReleaseQuery(self.query[0])
            self.query = None

    def ToDict(self):
        """ Returns the info for the lobby page, or None if the map is not from the Workshop. """
        if not self.item:
            return None
        details = self.details or {}
        return {
            # String, javascript numbers can't hold 64 bit ids
            'id': str(self.item),
            'title': details.get('title', ''),
            'previewurl': details.get('previewurl', ''),
            'author': GetPersonaName(details.get('owner', 0)),
            'subscribed': self.subscribed,
        }


def GetPersonaName(steamid):
    """ Returns the name of a Steam user, or an empty string while Steam retrieves it. """
    steamfriends = steamapicontext.SteamFriends()
    if not steamfriends or not steamid:
        return ''
    csteamid = CSteamID(steamid)
    name = steamfriends.GetFriendPersonaName(csteamid)
    if not name or name == '[unknown]':
        steamfriends.RequestUserInformation(csteamid, True)
        return ''
    return name
