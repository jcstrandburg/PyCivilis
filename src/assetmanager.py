"""
Provides a framework for a lazy loading asset management system.
"""

import pygame
import os

class AssetException(Exception):
    pass

class _Asset(object):

    """Simple wrapper class for containing asset handles"""
    
    def __init__(self, path, type):
        self.filepath = path
        self.type = type
        self.asset = None
        
class ImageLoader(object):
    """Simple asset loader class that loads images"""
    def load(self, path):
        return pygame.image.load(path)

class SoundLoader(object):
    """Simple sound loader class that loads audio files"""
    def load(self, path):
        return pygame.mixer.Sound(path)
        
class AssetManager(object):
    """Lazy loading asset manager class
    
    Class that performs management and lazy loading 
    of assets from tags read from asset set files
    """

    def __init__(self):
        """Initializes the asset manager with loaders for
        images and audio files
        """
        self._assets = {} 
        self._loaders = {}
        
        self.add_asset_loader( "image", ImageLoader())
        
    def load_set(self, path):
        """Loads a set of asset tags from the given path
        
        Loads the asset set file at the given path. All assets
        are assumed to be in the same directory as the asset set file.
        The assets will not be completely loaded until specifically
        requested via the AssetManager.get method.
        
        Assets are listed in the asset set file as follows:
        assettype tag path
        """
    
        basepath = os.path.split(path)[0]
        
        file = open(path, "r")
        for line in file:
            tokens = line.split()
            if len(tokens) > 0:#skip blank lines
                if len( tokens) != 3:
                    raise Exception( "Invalid asset line {" + line + "}")

                type = tokens[0]    
                tag = tokens[1]
                path = os.path.join( basepath, tokens[2])
                self._assets[ tag] = _Asset( path, type)
        
    def add_asset_loader(self, type, loader):
        """Adds a loader class for the given asset type"""
        self._loaders[type] = loader
        
    def _get_loader(self, type):
        pass
        
    def get(self, tag):
        """Loads and returns the requested asset by tag.
        
        If the requested asset has already been loaded it
        will be cached, and this version will be returned rather
        than reloaded.
        
        Raises:
            AssetException: If no asset is found for the given tag
            or no loader is found for the asset type of the requested
            asset.
        """
        
        try:
            handle = self._assets[tag]
        except KeyError:
            raise AssetException( "Unkown asset tag: "+tag)        
        
        if handle.asset is None:
            try:
                loader = self._loaders[handle.type]
            except KeyError:
                raise AssetException( "Unrecognised type: " 
                    + handle.type)
            handle.asset = loader.load( handle.filepath)
        return handle.asset
        
    