from threading import Thread

import requests
import traceback
import base64
from urllib.parse import urljoin

from core.dispatch import receiver
from core.signals import preshutdown
from steam import SteamUser_GetAuthSessionTicket

import settings

match_upload_url = urljoin(settings.LAMBDAWARS_API_URL, 'matches/upload')
match_record_start_url = urljoin(settings.LAMBDAWARS_API_URL, 'matches/record_start')
match_verify_url = urljoin(settings.LAMBDAWARS_API_URL, 'matches/verify_player')

upload_threads = set()

@receiver(preshutdown)
def PreShutdown(sender, *args, **kwargs):
    """ Ensures all upload threads are finished before shutting down the game. """
    for t in list(upload_threads):
        t.join()
    upload_threads.clear()

class StatisticsMatchStartHandler(object):
    def __init__(self, match_info):
        super().__init__()

        self.match_info = match_info

    def __call__(self):
        try:
            Msg('Recording start match to server\n')

            match_info = self.match_info
            r = requests.post(match_record_start_url, json={
                'mode': match_info['mode'],
                'map': match_info['map'],
                'type': match_info['type'],
                'start_date':  match_info['start_date'],
                'players': match_info['players'],
            })

            match_server_info = r.json()
            Msg('Start match record result: %s\n' % match_server_info)

            self.match_info['uuid'] = match_server_info['match_uuid']
        except:
            PrintWarning('Failed to do match start record\n')
            traceback.print_exc()

        upload_threads.discard(self)


class StatisticsMatchUploaderHandler(object):
    def __init__(self, match_uuid, path):
        super().__init__()

        self.match_uuid = match_uuid
        self.path = path

    def __call__(self):
        try:
            Msg('Uploading match file "%s" to match server\n' % self.path)

            data = {
                'match_uuid': self.match_uuid,
            }
            filename = 'match.lwmatch'
            files = {'match_data': (filename, open(self.path, 'rb'))}

            r = requests.post(match_upload_url, data=data, files=files)

            Msg('Upload match result: %s\n' % r.text)
        except:
            PrintWarning('Failed to do upload\n')
            traceback.print_exc()

        upload_threads.discard(self)


class StatisticsVerifyPlayer(object):
    def __init__(self, match_uuid, auth_ticket):
        super().__init__()

        self.match_uuid = match_uuid
        self.auth_ticket = auth_ticket

    def __call__(self):
        try:
            auth_ticket_encoded = base64.b16encode(self.auth_ticket).decode("utf-8")

            Msg('Verifying player for match uuid %s\n' % self.match_uuid)

            data = {
                'auth_ticket': auth_ticket_encoded,
                'match_uuid': self.match_uuid,
            }

            r = requests.post(match_verify_url, data=data)

            Msg('Verify player for match uuid result: %s\n' % r.text)
        except:
            PrintWarning('Failed to do verify for player:\n')
            traceback.print_exc()

        upload_threads.discard(self)


class StatisticsUploader(object):
    def RecordMatchStart(self, match_info):
        if not match_info:
            PrintWarning('StatisticsUploader: no path specified\n')
            return

        t = Thread(target=StatisticsMatchStartHandler(match_info))
        t.start()
        upload_threads.add(t)

    def UploadMatchFile(self, match_uuid, path):
        if not match_uuid or not path:
            PrintWarning('StatisticsUploader: no match_uuid or path specified\n')
            return

        t = Thread(target=StatisticsMatchUploaderHandler(match_uuid, path))
        t.start()
        upload_threads.add(t)

    def VerifyPlayer(self, match_uuid):
        if not match_uuid:
            PrintWarning('StatisticsUploader: no match_uuid specified\n')
            return

        auth_ticket = SteamUser_GetAuthSessionTicket()

        t = Thread(target=StatisticsVerifyPlayer(match_uuid, auth_ticket))
        t.start()
        upload_threads.add(t)
