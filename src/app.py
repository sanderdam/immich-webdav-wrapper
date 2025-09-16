import logging
import os
from immichprovider import ImmichProvider
from cheroot import wsgi
from datetime import datetime
from dateutil.parser import *
from dotenv import load_dotenv
from wsgidav.wsgidav_app import WsgiDAVApp

from wsgidav import util

_logger = util.get_module_logger(__name__)
_logger.setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

def run_webdav_server():
    # Load all environment variables at once
    immich_url = os.getenv("IMMICH_URL")
    api_key = os.getenv("IMMICH_API_KEY")
    album_ids_env = os.getenv("ALBUM_IDS")
    album_ids = [id.strip() for id in album_ids_env.split(",") if id.strip()] if album_ids_env else []
    refresh_rate_hours = int(os.getenv("REFRESH_RATE_HOURS", 1))  # Default to 1 hour
    port = int(os.getenv("WEBDAV_PORT", 1700))  # Allow port to be set via environment variable
    excluded_file_types = [id.strip().lower() for id in os.getenv("EXCLUDED_FILE_TYPES", "").split(",") if id.strip()]
    flatten_structure = os.getenv("FLATTEN_ASSET_STRUCTURE", "false").lower() == "true"  # Load flatten structure option

    # Validate required environment variables
    if not immich_url or not api_key:
        raise ValueError("IMMICH_URL and IMMICH_API_KEY must be set.")

    provider = ImmichProvider(immich_url, api_key, album_ids, refresh_rate_hours, excluded_file_types, flatten_structure)

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