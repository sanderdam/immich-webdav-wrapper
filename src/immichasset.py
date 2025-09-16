import hashlib
import time
import os
from dateutil.parser import *
from wsgidav import util
from wsgidav.dav_provider import DAVNonCollection

class ImmichAsset(DAVNonCollection):
    def __init__(self, path, environ, asset):
        super().__init__(path, environ)
        self.asset = asset
        
    def get_content_length(self):
        try:
            return 10
            #return os.path.getsize(f"{self.asset.get('originalPath')}")
        except FileNotFoundError:
            #_logger.error("Check if mountPath is correct")
            return None

    def get_content_type(self):
        return self.asset.get("originalMimeType")

    def get_creation_date(self):
        return int(isoparse(self.asset.get("fileCreatedAt")).timestamp())

    def get_display_name(self):
        return self.name
    
    def get_display_info(self):
        return {
            "type": "File",
            "etag": self.get_etag(),
            "size": self.get_content_length(),
        }

    def get_etag(self):
        return (
            f"{hashlib.md5(self.path.encode()).hexdigest()}-"
            f"{util.to_str(self.get_last_modified())}-"
            f"{self.get_content_length()}"
        )
        
    def support_etag(self):
        return True

    def get_last_modified(self):
        return time.time()
        #return int(isoparse(self.asset.get("fileModifiedAt")).timestamp())
        
    def get_content(self):
        return open(f"{self.asset.get('originalPath')}", "rb")