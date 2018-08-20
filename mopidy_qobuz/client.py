from __future__ import absolute_import, unicode_literals

import requests
import urlparse
import logging
import hashlib
import functools

from mopidy import backend, models
import types
import time
import re

# URI:
# qobuz:track:$id

API_PREFIX = "http://www.qobuz.com/api.json/0.2/"
REGEX_URL = "http://www\.qobuz\.com/api\.json/0\.2/(.*)"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"

URI_ROOT = "qobuz:directory"
URI_ALBUMS = "qobuz:album"
URI_TRACKS = "qobuz:track"

logger = logging.getLogger(__name__)

def api(p):
    return urlparse.urljoin(API_PREFIX, p)

def to_album_ref(album):
    return models.Ref.album(uri="%s:%s" % (URI_ALBUMS, album["id"]),
                            name=album["title"])

def mk_track_uri(album_id, track_id):
    return "%s:%s:%s" % (URI_TRACKS, album_id, str(track_id))

def to_track_ref(album_id, track):
    return models.Ref.track(uri=mk_track_uri(album_id, track["id"]),
                            name=track["title"])

class QobuzRequestsSession(requests.Session):
    def __init__(self, app_id, app_secret, user_auth_token):
        super(QobuzRequestsSession, self).__init__()

        self._app_id = app_id
        self._app_secret = app_secret
        self._user_auth_token = user_auth_token

        self.headers.update({
            "User-Agent": USER_AGENT,
            "X-App-Id": app_id,
            "X-User-Auth-Token": user_auth_token,
        })

    def prepare_request(self, request):

        if request.method == "GET":
            path = re.search(REGEX_URL, request.url).groups()[0].replace('/','')
            params = "".join([(k + v) for k, v in request.params.items()])
            ts = long(time.time())

            sigstr = "{path}{params}{ts}{secret}".format(
                path=path, params=params, ts=ts, secret=self._app_secret)
            sigdigest = hashlib.md5(sigstr).hexdigest()

            logger.debug("Signing request %s %s", sigstr, sigdigest)
            request.params["request_ts"] = ts
            request.params["request_sig"] = sigdigest

        p = requests.Session.prepare_request(self, request)

        return p

def get_requests_session(config):

    # TODO: proxy
    login = requests.get(api("user/login"), params={
        "app_id": config["client_id"],
        "email": config["username"],
        "password": hashlib.md5(config["password"]).hexdigest(),
    }, headers={ "user-agent": USER_AGENT })
    if login.status_code != requests.codes.ok:
        pass

    # TODO: add log
    login_data = login.json()
    logger.debug("Successful logged in %s %s",
                 login_data["user"]["credential"]["description"],
                 login_data["user"]["email"])

    session = QobuzRequestsSession(config["client_id"],
        config["client_secret"], login_data["user_auth_token"])

    return session

class QobuzPlaybackProvider(backend.PlaybackProvider):
    def translate_uri(self, uri):
        return None

class QobuzLibraryProvider(backend.LibraryProvider):
    root_directory = models.Ref.directory(
        uri=URI_ROOT,
        name="Qobuz",
    )

    def __init__(self, backend):
        super(QobuzLibraryProvider, self).__init__(backend)

        self._root = [
            models.Ref.directory(uri=URI_ALBUMS, name="Albums"),
        ]

    def browse(self, uri):
        logger.debug("Browsing URI %s", uri)
        if uri == URI_ROOT:
            return self._root
        elif uri == URI_ALBUMS:
            return self._browse_albums()
        elif uri.startswith("%s:" % URI_ALBUMS):
            album_id = uri.split(':')[2]
            return self._browse_album(album_id)

        return []

    def lookup(self, uri):
        logger.error("Looking up URI %s", uri)
        if uri.startswith("%s:" % URI_TRACKS):
            track_id = uri.split(':')[3]
            return self._lookup_track(track_id)
        return []

    def _browse_albums(self):
        # TODO: paging
        album_list_req = self.backend.session.get(api("userLibrary/getAlbumsList"))
        album_list = album_list_req.json()["items"]
        return map(to_album_ref, album_list)

    def _browse_album(self, album_id):
        # github.com/Qobuz/api-documentation/blob/master/endpoints/album/get.md
        album_req = self.backend.session.get(api("album/get"), params={
            "album_id": album_id
        })
        album = album_req.json()
        return map(functools.partial(to_track_ref, album_id), album["tracks"]["items"])

    def _lookup_track(self, track_id):
        # github.com/Qobuz/api-documentation/blob/master/endpoints/track/get.md
        track_req = self.backend.session.get(api("track/get"), params={
            "track_id": track_id
        })
        track = track_req.json()
        return [
            models.Track(
                uri=mk_track_uri(track["album"]["id"], track["id"]),
                name=track["title"]
            )
        ]
