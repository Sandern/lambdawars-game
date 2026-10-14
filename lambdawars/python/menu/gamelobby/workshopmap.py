""" Makes sure players in a game lobby have the selected map when it comes from the Steam Workshop.

    The lobby owner publishes the Workshop item id and revision of the selected map in the lobby data.
    Other players download the item when they don't have the map (or have a different version), and
    can't get ready until the map is available.
"""
import filesystem
from gameinterface import GetMapHeader

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
    # Maps of the game itself are found first, even if a Workshop item has a map with the same name
    if filesystem.FileExists('maps/%s.bsp' % mapname, 'MOD'):
        return ''
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
