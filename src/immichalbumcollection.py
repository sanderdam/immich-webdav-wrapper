from wsgidav.dav_provider import DAVCollection
from wsgidav.util import join_uri
from immichassetcollection import ImmichAssetCollection
from immichalbum import ImmichAlbum
from immichasset import ImmichAsset
from immichapifunctions import *

class ImmichAlbumCollection(DAVCollection):
    def __init__(self, path: str, environ: dict, immich_url, api_key):
        super().__init__(path, environ)
        self.immich_url = immich_url
        self.api_key = api_key

    def _get_all_albums(self):
        url = f"{self.immich_url}/api/albums"
        albums = fetch_with_retries(url, self.api_key)        
        return albums
        
    def get_member_names(self):
        self.albums = self._get_all_albums()
        albums_sorted = sorted([album.get('albumName', '').replace('>','_') for album in self.albums])
        return albums_sorted
    
    def get_member(self, name):        
        return ImmichAlbum(join_uri(self.path, name), self.environ, name,self.immich_url, self.api_key)
        
        #return ImmichAsset(join_uri(self.path, name), self.environ, None)
        #if self.flatten_structure:
        #    # If flatten_structure is True, return the asset directly
        #    asset = self._get_all_assets().get(name)
        #    
        #else:
        #    # If flatten_structure is False, return the subcollections (images, videos)
        #    if name in self.visibleMemberNames:
        #        return ImmichAssetCollection(join_uri(self.path, name), self.environ, self.album)
        #    return None

    def _get_all_assets(self):
        """Return a dictionary of all assets (both images and videos) for the album."""
        all_assets = {}
        for asset in self.album.get('assets', []):
            
            # Extract file extension and check against excluded_file_types
            file_extension = asset['originalFileName'].split(".")[-1].lower()
            
            if file_extension in self.provider.filetype_ignore_list:
                continue  # Skip this asset if its type is in the excluded list
            
            asset_name = asset['originalFileName']
            all_assets[asset_name] = asset
        return all_assets