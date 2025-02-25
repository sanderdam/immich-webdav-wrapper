# Immich WebDAV Server

This project provides a WebDAV server that interfaces with the [Immich API](https://github.com/immich-app/immich) to access and serve media assets stored within specified albums. The server allows you to view and interact with album content (photos and videos) in a WebDAV-compatible client. The server periodically refreshes the list of assets to keep the content up to date with the Immich backend.

## Features

- Connects to an Immich instance and fetches media assets from specified albums.
- Supports periodic asset refreshing to sync with changes on the Immich server.
- Exposes albums and assets in a WebDAV server, accessible via WebDAV clients.
- Allows exclusion of specific file types through environment configuration.
- Offers support for basic file operations such as reading content, fetching metadata, and file organization based on file types (e.g., images and videos).

## Requirements

- **Python 3.8+**
- `cheroot`
- `requests`
- `python-dotenv`
- `wsgidav`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Configuration
```bash
Configuration is managed through a .env file in the project directory. Required variables are:
IMMICH_URL="https://your-immich-instance.com"
IMMICH_API_KEY="your_api_key_here"
ALBUM_IDS="album_id1, album_id2"
REFRESH_RATE_HOURS=1
EXCLUDED_FILE_TYPES="png,jpg"
FLATTEN_ASSET_STRUCTURE=true
```

- `IMMICH_URL`: Base URL of your Immich instance.
- `IMMICH_API_KEY`: API key for authentication with Immich.
- `ALBUM_IDS`: Comma-separated list of album IDs to be fetched. If empty, then all albums will be fetched.
- `REFRESH_RATE_HOURS`: Interval (in hours) for refreshing album data.
- `EXCLUDED_FILE_TYPES`: Comma-separated list of file extensions to ignore.
- `FLATTEM_ASSET_STRUCTURE`: Determines whether assets are organized in a flat directory structure or within content-type-specific subdirectories in the WebDAV server.

## Code Overview

### Main Components

- `ImmichProvider`: The main DAVProvider subclass that handles API requests to Immich. It periodically fetches and stores album data.
- `RootCollection`: Handles the root level of the WebDAV directory and organizes albums into collections.
- `ImmichAlbumCollection`: Represents individual albums and organizes assets by type (e.g., images, videos).
- `ImmichAssetCollection`: Groups assets by file type, handling asset retrieval and sorting.
- `ImmichAsset`: Represents an individual asset file and provides access to file metadata and content.

### Asset Refreshing

Assets are fetched from Immich through the `refresh_assets` method in `ImmichProvider`. The method retries up to three times if there are connection issues. It runs in a separate thread and refreshes periodically based on `REFRESH_RATE_HOURS`.

### WebDAV Server Setup

The `run_webdav_server` function initializes the WebDAV server using WsgiDAV with settings from the `.env` file. It maps the root directory (`/`) to the `ImmichProvider` instance, allowing access to albums through WebDAV.

## Running the Server

To start the server, use:

```bash
python <script_name>.py
```

The WebDAV server will start on the port specified by `WEBDAV_PORT`.

## Logging and Troubleshooting

- Logs are written to the console with INFO-level logging by default.
- Asset fetching and server start/stop events are logged for monitoring purposes.
- Errors encountered during album fetching are retried, and a failure message is logged if all retries fail.

## Stopping the Server

To gracefully stop the server, press `Ctrl+C` in the terminal. This will stop the WebDAV server and terminate the asset refresh thread.

## Notes

- Ensure the `.env` file contains valid API credentials and album IDs.
- WebDAV clients may require specific credentials or configurations to access the server.

## License

This project is open-source. Please refer to the [LICENSE](./LICENSE) file for more details.
