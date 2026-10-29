""" Provides the workshop browser webview component, used to find and subscribe to maps on the Steam Workshop.

    Results are queried one page at a time (at most _workshop.RESULTS_PER_PAGE items). Only one query runs
    at a time: starting a new query cancels the previous one.
"""
import re
import math

from cef import WebViewComponent, jsbind
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from steam import steamapicontext, CSteamID

try:
    import _workshop
except ImportError:
    _workshop = None

#: Only items with this tag are listed, the tag set when publishing a map
WORKSHOP_MAP_TAG = 'Map'
#: Time period used for sorting by popularity
TREND_DAYS = 30

#: BBCode tags used in Workshop descriptions, like [b], [url=...] and [/list]
BBCODE_PATTERN = re.compile(r'\[/?[a-zA-Z0-9*]+(?:=[^\]]*)?\]')


def GetSortOptions():
    """ Maps sort names used by the menu to (query type for all items, sort order for user lists). """
    return {
        'trend': (_workshop.QUERY_RANKED_BY_TREND, _workshop.USER_SORT_SUBSCRIPTION_DESC),
        'toprated': (_workshop.QUERY_RANKED_BY_VOTE, _workshop.USER_SORT_VOTE_SCORE_DESC),
        'subscriptions': (_workshop.QUERY_RANKED_BY_UNIQUE_SUBSCRIPTIONS, _workshop.USER_SORT_SUBSCRIPTION_DESC),
        'newest': (_workshop.QUERY_RANKED_BY_PUBLICATION_DATE, _workshop.USER_SORT_CREATION_DESC),
        'updated': (_workshop.QUERY_RANKED_BY_LAST_UPDATED_DATE, _workshop.USER_SORT_LAST_UPDATED_DESC),
        'title': (_workshop.QUERY_RANKED_BY_TEXT_SEARCH, _workshop.USER_SORT_TITLE_ASC),
        'relevance': (_workshop.QUERY_RANKED_BY_TEXT_SEARCH, _workshop.USER_SORT_SUBSCRIPTION_DESC),
    }


def StripBBCode(text):
    return BBCODE_PATTERN.sub('', text).strip()


class WebWorkshopBrowser(WebViewComponent):
    defaultobjectname = 'workshopbrowser'

    #: Query being sent, or None
    activequery = None

    def OnDestroy(self):
        super().OnDestroy()

        self.CancelQuery()

    @jsbind(hascallback=True, manuallycallback=True)
    def query(self, methodargs, callbackid):
        """ Queries a page of Workshop maps.

            Args: page (starting at 1), sort name, search text, list ('all', 'subscribed' or 'mine')
            Callback args: success, error message, items, total number of matching items, number of pages
        """
        page, sort, searchtext, listname = methodargs[:4]
        page = max(1, int(page))

        self.CancelQuery()

        if not _workshop or not _workshop.IsAvailable():
            self.SendCallback(callbackid, [False, 'The Steam Workshop is not available', [], 0, 0])
            return

        sortoptions = GetSortOptions()
        querytype, usersortorder = sortoptions.get(sort, sortoptions['trend'])
        if listname == 'all':
            searchtext = searchtext.strip()
            # Ranking by text search needs search text
            if querytype == _workshop.QUERY_RANKED_BY_TEXT_SEARCH and not searchtext:
                querytype = _workshop.QUERY_RANKED_BY_TREND
            trenddays = TREND_DAYS if querytype == _workshop.QUERY_RANKED_BY_TREND else 0
            sentquery = _workshop.SendQuery(querytype, page, searchtext, WORKSHOP_MAP_TAG, trenddays)
        else:
            # Steam does not support search text for lists of a user
            userlist = _workshop.USER_LIST_SUBSCRIBED if listname == 'subscribed' else _workshop.USER_LIST_PUBLISHED
            accountid = steamapicontext.SteamUser().GetSteamID().GetAccountID()
            sentquery = _workshop.SendUserQuery(accountid, userlist, usersortorder, page, WORKSHOP_MAP_TAG)

        if not sentquery:
            self.SendCallback(callbackid, [False, 'Failed to send the query to Steam', [], 0, 0])
            return

        handle, call = sentquery
        self.activequery = {'handle': handle, 'call': call, 'callbackid': callbackid}
        if not IsTickMethodRegistered(self.OnQueryTick):
            RegisterTickMethod(self.OnQueryTick, 0.1, True, True)

    @jsbind(hascallback=True)
    def getstates(self, methodargs):
        """ Returns the subscription state of items and the names of item authors.

            Args: list of item ids, list of author steam ids
            Callback args: dict of item id to state, dict of author steam id to name
        """
        itemids, ownerids = methodargs[:2]
        if not _workshop or not _workshop.IsAvailable():
            return [{}, {}]
        states = {itemid: self.GetItemState(int(itemid)) for itemid in itemids}
        names = {ownerid: self.GetPersonaName(int(ownerid)) for ownerid in ownerids}
        return [states, names]

    @jsbind()
    def subscribe(self, methodargs):
        if _workshop and _workshop.IsAvailable():
            _workshop.SubscribeItem(int(methodargs[0]))

    @jsbind()
    def unsubscribe(self, methodargs):
        if _workshop and _workshop.IsAvailable():
            _workshop.UnsubscribeItem(int(methodargs[0]))

    # Queries
    def OnQueryTick(self):
        query = self.activequery
        if not query:
            self.StopQueryTick()
            return

        results = _workshop.GetQueryResults(query['handle'], query['call'])
        if results is None:
            return

        self.activequery = None
        self.StopQueryTick()

        if results['iofailure'] or results['result'] != _workshop.RESULT_OK:
            error = 'Lost connection with Steam' if results['iofailure'] else 'Steam error code %d' % results['result']
            self.SendCallback(query['callbackid'], [False, error, [], 0, 0])
            return

        items = [self.BuildItem(data) for data in results['items']]
        total = results['total']
        numpages = int(math.ceil(total / float(_workshop.RESULTS_PER_PAGE)))
        self.SendCallback(query['callbackid'], [True, '', items, total, numpages])

    def CancelQuery(self):
        """ Stops waiting for the active query. Its callback is never called. """
        if self.activequery:
            _workshop.ReleaseQuery(self.activequery['handle'])
            self.activequery = None
        self.StopQueryTick()

    def StopQueryTick(self):
        if IsTickMethodRegistered(self.OnQueryTick):
            UnregisterTickMethod(self.OnQueryTick)

    # Items
    def BuildItem(self, data):
        """ Converts query result data to a dictionary for the menu.
            Ids are strings, because javascript numbers can't hold 64 bit ids. """
        itemid = data['publishedfileid']
        item = {
            'id': str(itemid),
            'title': data['title'],
            'description': StripBBCode(data['description']),
            'tags': [tag for tag in data['tags'].split(',') if tag and tag != WORKSHOP_MAP_TAG],
            'previewurl': data['previewurl'],
            'owner': str(data['owner']),
            'author': self.GetPersonaName(data['owner']),
            # Published by the local player, who can update it
            'mine': data['owner'] == steamapicontext.SteamUser().GetSteamID().ConvertToUint64(),
            'timecreated': data['timecreated'],
            'timeupdated': data['timeupdated'],
            'votesup': data['votesup'],
            'votesdown': data['votesdown'],
            'score': data['score'],
            'filesize': data['filesize'],
            'subscriptions': data['subscriptions'],
            'banned': data['banned'],
        }
        item.update(self.GetItemState(itemid))
        return item

    def GetItemState(self, itemid):
        """ Returns the state of an item for the local player.

            States: none, subscribed (waiting for download), downloading, installed, rejected (content not allowed)
        """
        flags = _workshop.GetItemState(itemid)
        state = {'state': 'none', 'progress': 0, 'error': ''}
        if _workshop.GetItemStatus(itemid) == 'rejected':
            state['state'] = 'rejected'
            state['error'] = _workshop.GetItemError(itemid)
        elif not flags & _workshop.ITEM_STATE_SUBSCRIBED:
            pass
        elif flags & (_workshop.ITEM_STATE_DOWNLOADING | _workshop.ITEM_STATE_DOWNLOAD_PENDING):
            state['state'] = 'downloading'
            downloaded, total = _workshop.GetItemDownloadProgress(itemid)
            state['progress'] = int(100 * downloaded / total) if total else 0
        elif flags & _workshop.ITEM_STATE_INSTALLED:
            state['state'] = 'installed'
        else:
            state['state'] = 'subscribed'
        return state

    def GetPersonaName(self, steamid):
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
