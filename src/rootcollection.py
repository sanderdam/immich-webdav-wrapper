from wsgidav.util import join_uri

from wsgidav.dav_provider import  DAVCollection
from immichalbumcollection import ImmichAlbumCollection
from immichtagcollection import ImmichTagCollection

class RootCollection(DAVCollection):
    """Resolve top-level requests '/'."""

    def __init__(self, environ, immich_url, api_key):
        super().__init__("/", environ)
        self.rootFolders = ['albums', 'tags']
        self.immich_url = immich_url
        self.api_key = api_key

    def get_member_names(self):
        return self.rootFolders

        #return [entry['albumName'] for entry in self.provider.all_album_data]

    def get_member(self, name):
        if name not in self.rootFolders:
            return None
        
        if name == 'albums':
            return ImmichAlbumCollection("/albums", self.environ,self.immich_url, self.api_key)
        
        if name == 'tags':
            return ImmichTagCollection("/tags", self.environ,self.immich_url, self.api_key)
        
        #return ImmichAlbumCollection(join_uri(self.path, name), self.environ,
        #                             next((entry for entry in self.provider.all_album_data 
        #                                   if entry['albumName'] == name), None), 
        #                             self.flatten_structure)