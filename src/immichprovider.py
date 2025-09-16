import logging
import requests
import threading
import time
from rootcollection import RootCollection
from wsgidav.dav_provider import DAVProvider
from wsgidav import util

_logger = util.get_module_logger(__name__)
_logger.setLevel(logging.INFO)

class ImmichProvider(DAVProvider):
    def __init__(self, immich_url, api_key, album_ids, refresh_rate_hours, filetype_ignore_list, flatten_structure):
        super().__init__()
        self.immich_url = immich_url
        self.api_key = api_key
        
        self.filetype_ignore_list = filetype_ignore_list                
        self.stop_event = threading.Event()

    def get_resource_inst(self, path, environ):
        _logger.info("get_resource_inst('%s')" % path)
        self._count_get_resource_inst += 1
        root = RootCollection(environ, self.immich_url, self.api_key)
        return root.resolve("", path)