from __future__ import unicode_literals

import logging
import os

from mopidy import backend, httpclient
import client

import pykka

class QobuzBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(QobuzBackend, self).__init__()

        self._config = config
        self._audio = audio

        self.library = client.QobuzLibraryProvider(backend=self)
        self.uri_schemes = ["qobuz"]
        self.session = None

    def on_start(self):
        self.session = client.get_requests_session(self._config["qobuz"])
