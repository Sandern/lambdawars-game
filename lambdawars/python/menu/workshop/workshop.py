""" Provides the workshop webview component.
"""
from cef import WebViewComponent, jsbind
from steam import steamapicontext, EWorkshopFileType, CreateItemResultCallResult, SubmitItemUpdateResultCallResult
import filesystem

import os

class WarsCreateItemResultCallResult(CreateItemResultCallResult):
    def OnCreateItemResult(self, data, io_failure):
        print('OnCreateItemResult')
        print('io_failure: %s' % io_failure)
        print('userneedstoacceptworkshoplegalagreement: %s' % data.userneedstoacceptworkshoplegalagreement)
        print('result: %s' % data.result)
        print('publishedfileid: %s' % data.publishedfileid)

        self.webview.SendCallback(self.callbackid, [True, data.publishedfileid])
        self.webview.create_item_callback = None

class WarsSubmitItemUpdateResultCallResult(SubmitItemUpdateResultCallResult):
    def OnSubmitItemUpdateResult(self, data, io_failure):
        print('OnSubmitItemUpdateResult')
        print('io_failure: %s' % io_failure)
        print('userneedstoacceptworkshoplegalagreement: %s' % data.userneedstoacceptworkshoplegalagreement)
        print('result: %s' % data.result)

class WebWorkshop(WebViewComponent):
    defaultobjectname = 'workshop'

    create_item_callback = None
    submit_item_result = None

    @jsbind(hascallback=True, manuallycallback=True)
    def createItem(self, methodargs, callbackid):
        if self.create_item_callback:
            self.SendCallback(callbackid, [False])
            return

        steam_ugc = steamapicontext.SteamUGC()
        steam_utils = steamapicontext.SteamUtils()

        self.create_item_callback = WarsCreateItemResultCallResult(
            steam_ugc.CreateItem(steam_utils.GetAppID(), EWorkshopFileType.k_EWorkshopFileTypeCommunity)
        )
        self.create_item_callback.webview = self
        self.create_item_callback.callbackid = callbackid

    @jsbind()
    def updateItem(self, methodargs):
        self.DoUpdateItem({
            'publishedfileid': methodargs[0],
            'content_path': methodargs[1],
            'title': methodargs[2],
            'description': methodargs[3],
            'preview_path': methodargs[4],
        })

    @jsbind(hascallback=True)
    def getDownloadInfo(self, methodargs):
        steam_ugc = steamapicontext.SteamUGC()

        success, bytes_downloaded, bytes_total = steam_ugc.GetItemDownloadInfo(methodargs[0])
        if success:
            print('bytes_downloaded: %s' % bytes_downloaded)
            print('bytes_total: %s' % bytes_total)
            return [success, bytes_downloaded, bytes_total]
        return [success]

    @jsbind(hascallback=True)
    def getInstallInfo(self, methodargs):
        steam_ugc = steamapicontext.SteamUGC()

        success, size_on_disk, folder, time_stamp = steam_ugc.GetItemInstallInfo(methodargs[0])
        if success:
            print('size_on_disk: %s' % size_on_disk)
            print('folder: %s' % folder)
            print('time_stamp: %s' % time_stamp)
            return [success, size_on_disk, folder, time_stamp]
        return [success]

    def DoUpdateItem(self, data):
        steam_ugc = steamapicontext.SteamUGC()
        steam_utils = steamapicontext.SteamUtils()

        publishedfileid = data['publishedfileid']

        update_handle = steam_ugc.StartItemUpdate(steam_utils.GetAppID(), publishedfileid)

        content_path = data.get('content_path', None)
        if content_path:
            if not os.path.isabs(content_path):
                content_path = filesystem.RelativePathToFullPath(content_path)
            content_path = os.path.normpath(content_path)
            steam_ugc.SetItemContent(update_handle, content_path)

        title = data.get('title', None)
        if title:
            steam_ugc.SetItemTitle(update_handle, title)
        description = data.get('description', None)
        if description:
            steam_ugc.SetItemDescription(update_handle, description)
        #steam_ugc.SetItemUpdateLanguage( update_handle, 'english' )
        #steam_ugc.SetItemMetadata( update_handle, 'Lambda Wars Item Metadata' )
        #steam_ugc.SetItemVisibility( update_handle, ERemoteStoragePublishedFileVisibility eVisibility )
        preview_path = data.get('preview_path', None)
        if preview_path:
            if not os.path.isabs(preview_path):
                preview_path = filesystem.RelativePathToFullPath(preview_path)
            preview_path = os.path.normpath(preview_path)
            steam_ugc.SetItemPreview(update_handle, preview_path)

        self.submit_item_result = WarsSubmitItemUpdateResultCallResult(
            steam_ugc.SubmitItemUpdate(update_handle, '')
        )

