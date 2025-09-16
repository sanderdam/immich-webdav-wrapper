from wsgidav.dav_provider import DAVCollection
from immichasset import ImmichAsset
from wsgidav.util import join_uri

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