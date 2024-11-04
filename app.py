import hashlib
import logging
import os
import requests
import threading
import time
from cheroot import wsgi
from datetime import datetime
from dotenv import load_dotenv
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.dav_provider import DAVProvider, DAVCollection, DAVNonCollection
from wsgidav.util import join_uri
from wsgidav import util

_logger = util.get_module_logger(__name__)
_logger.setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

class ImmichProvider(DAVProvider):
    def __init__(self, immich_url, api_key, album_ids, refresh_rate_hours, filetype_ignore_list):
        super().__init__()
        self.immich_url = immich_url
        self.api_key = api_key
        self.album_ids = album_ids
        self.all_album_data = []
        self.refresh_rate_seconds = refresh_rate_hours * 3600  # Convert hours to seconds
        self.filetype_ignore_list = filetype_ignore_list
        self.refresh_thread = threading.Thread(target=self._auto_refresh)
        self.stop_event = threading.Event()
        
        # Initial asset load
        self.refresh_assets()
        
        # Start the background thread to refresh assets periodically
        self.refresh_thread.start()
        
    def _auto_refresh(self):
        """Background thread method to refresh assets periodically."""
        while not self.stop_event.wait(self.refresh_rate_seconds):
            _logger.info("Refreshing assets...")
            self.refresh_assets()
        
    def stop_refresh(self):
        """Stop the background refresh thread."""
        self.stop_event.set()
        self.refresh_thread.join()
        
    def get_resource_inst(self, path, environ):
        _logger.info("get_resource_inst('%s')" % path)
        self._count_get_resource_inst += 1
        root = RootCollection(environ)
        return root.resolve("", path)
    
    def refresh_assets(self):
        for album_id in self.album_ids:
            url = f"{self.immich_url}/api/albums/{album_id}"
            headers = {'x-api-key': f'{self.api_key}'}
            for attempt in range(3):  # Retry up to 3 times
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    break  # Break if the request is successful
                except requests.RequestException as e:
                    _logger.error(f"Error fetching album {album_id} (attempt {attempt + 1}): {e}")
                    time.sleep(2)  # Wait before retrying
            else:
                continue  # If we exhaust attempts, skip to the next album
            self.all_album_data.append(response.json())

        _logger.info(f"Loaded {sum(album['assetCount'] for album in self.all_album_data)} assets from the API.")
        
        
class RootCollection(DAVCollection):
    """Resolve top-level requests '/'."""

    def __init__(self, environ):
        super().__init__("/", environ)
        
    def _get_album(self, name):
        for album in self.provider.all_album_data:
            if album.get("albumName") == name:
                return album

    def get_member_names(self):
        return [entry['albumName'] for entry in self.provider.all_album_data]

    def get_member(self, name):
        return ImmichAlbumCollection(join_uri(self.path, name), self.environ, 
                                     next((entry for entry in self.provider.all_album_data 
                                           if entry['albumName'] == name), None))


class ImmichAlbumCollection(DAVCollection):
    def __init__(self, path: str, environ: dict, album: dict):
        super().__init__(path, environ)
        self.visibleMemberNames = ('videos', 'images')
        self.album = album
        
    def get_member_names(self):
        return self.visibleMemberNames
    
    def get_member(self, name):
        if name in self.visibleMemberNames:
            return ImmichAssetCollection(join_uri(self.path, name), self.environ, self.album)
        return None


class ImmichAssetCollection(DAVCollection):
    def __init__(self, path, environ, album):
        super().__init__(path, environ)
        self.album = album
        self.asset_map = self._sort_assets()
    
    def _sort_assets(self):
        imageAssets = {}
        videoAssets = {}
        
        for asset in self.album.get('assets', []):
            asset_type = asset.get('type')
            # Extract file extension and check against excluded_file_types
            file_extension = asset['originalFileName'].split(".")[-1].lower()
            
            if file_extension in self.provider.filetype_ignore_list:
                continue  # Skip this asset if its type is in the excluded list
            
            # Sort assets by type
            if asset_type == 'IMAGE':
                imageAssets[asset['originalFileName']] = asset
            elif asset_type == 'VIDEO':
                videoAssets[asset['originalFileName']] = asset
                
        return {
            "videos": videoAssets,
            "images": imageAssets,
        }

    def get_member_names(self):
        if self.name not in self.asset_map:
            raise ValueError(f"Unsupported member name: {self.name}")

        return sorted(self.asset_map[self.name].keys())

    def get_member(self, name):
        return ImmichAsset(join_uri(self.path, name), self.environ, self.asset_map[self.name].get(name))
        
        
class ImmichAsset(DAVNonCollection):
    def __init__(self, path, environ, asset):
        super().__init__(path, environ)
        self.asset = asset
        
    def get_content_length(self):
        try:
            return os.path.getsize(self.asset.get("originalPath"))
        except FileNotFoundError:
            _logger.error("Check if mountPath is correct")
            return None

    def get_content_type(self):
        return self.asset.get("originalMimeType")

    def get_creation_date(self):
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        return int(datetime.strptime(self.asset.get("fileCreatedAt"), date_format).timestamp())

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
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        return int(datetime.strptime(self.asset.get("fileModifiedAt"), date_format).timestamp())
        
    def get_content(self):
        return open(f"/{self.asset.get('originalPath')}", "rb")
    
    
def run_webdav_server():
    # Load all environment variables at once
    immich_url = os.getenv("IMMICH_URL")
    api_key = os.getenv("IMMICH_API_KEY")
    album_ids = [id.strip() for id in os.getenv("ALBUM_IDS", "").split(",")]
    refresh_rate_hours = int(os.getenv("REFRESH_RATE_HOURS", 1))  # Default to 1 hour
    port = int(os.getenv("WEBDAV_PORT", 1700))  # Allow port to be set via environment variable
    excluded_file_types = [id.strip().lower() for id in os.getenv("EXCLUDED_FILE_TYPES", "").split(",") if id.strip()]

    # Validate required environment variables
    if not immich_url or not api_key or not album_ids:
        raise ValueError("IMMICH_URL, IMMICH_API_KEY, and ALBUM_IDS must be set.")

    provider = ImmichProvider(immich_url, api_key, album_ids, refresh_rate_hours, excluded_file_types)

    config = {
        "host": "0.0.0.0",
        "port": port,
        "provider_mapping": {"/": provider},
        "simple_dc": {
            "user_mapping": {
                "*": True  # Allows anonymous access
                # You can use {"*": {"admin": {"password": "admin"}}} to add specific user credentials.
            }
        },
        'directory_browser': True,
        'verbose': 2,   # _logger level (0: None, 1: Basic, 2: Verbose)
    }

    app = WsgiDAVApp(config)
    
    server_args = {
        "bind_addr": (config["host"], port),
        "wsgi_app": app,
    }
    server = wsgi.Server(**server_args)

    try:
        _logger.info(f"Starting WebDAV server on port {port}...")
        server.start()
    except KeyboardInterrupt:
        _logger.info("Received Ctrl-C: stopping...")
    finally:
        provider.stop_refresh()
        server.stop()

if __name__ == "__main__":
    run_webdav_server()