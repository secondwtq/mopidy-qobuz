from __future__ import unicode_literals

from mopidy import config, ext
from os import path

__version__ = "0.0.1"

class Extension(ext.Extension):

    dist_name = "Mopidy-Qobuz"
    ext_name = "qobuz"
    version = __version__

    def get_default_config(self):
        return config.read(path.join(path.dirname(__file__), "ext.conf"))

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()

        schema["username"] = config.String()
        schema["password"] = config.Secret()

        schema["client_id"] = config.String()
        schema["client_secret"] = config.Secret()

        return schema

    def validate_config(self, config):
        if not config.getboolean("qobuz", "enabled"):
            return

    def setup(self, registry):
        from mopidy_qobuz.backend import QobuzBackend
        registry.add("backend", QobuzBackend)
