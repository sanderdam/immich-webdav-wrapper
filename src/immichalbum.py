from wsgidav.dav_provider import DAVCollection
from wsgidav.util import join_uri
from immichassetcollection import ImmichAssetCollection
from immichasset import ImmichAsset
from immichapifunctions import *

class ImmichAlbum(DAVCollection):
    def __init__(self, path: str, environ: dict, albumName:str, immich_url, api_key):
        super().__init__(path, environ)
        self.immich_url = immich_url
        self.api_key = api_key
        self.albumName = albumName

    def _get_album_by_albumName(self):
        url = f"{self.immich_url}/api/albums"
        albums = fetch_with_retries(url, self.api_key)
        album = next((album for album in albums if album.get('albumName', '') == self.albumName), None)
        return album
    
    def _get_assets_by_album_id(self, album_id:str):
        url = f"{self.immich_url}/api/albums/" + album_id
        album = fetch_with_retries(url, self.api_key)
        assets = album.get('assets', [])
        return assets
        
    def get_member_names(self):
        
        album = self._get_album_by_albumName();
        album_id = album.get('id', '')
        
        assets = self._get_assets_by_album_id(album_id)
        assetNames = [asset.get('originalFileName', '') for asset in assets]
        return assetNames
    
    def get_member(self, name):

        return ImmichAsset(join_uri(self.path, name), self.environ, None)