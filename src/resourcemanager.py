"""
Provides a framework for a lazy loading resource management system.
"""

import pygame
import os

class ResourceException(Exception):
    pass

class _Resource(object):

    """Simple wrapper class for containing resource handles"""
    
    def __init__(self, path, type):
        self.filepath = path
        self.type = type
        self.resource = None
        
class ImageLoader(object):
    """Simple resource loader class that loads images"""
    def load(self, path):
        return pygame.image.load(path)

class SoundLoader(object):
    """Simple sound loader class that loads audio files"""
    def load(self, path):
        return pygame.mixer.Sound(path)
        
class ResourceManager(object):
    """Lazy loading resource manager class
    
    Class that performs management and lazy loading 
    of resources from tags read from resource set files
    """

    def __init__(self):
        """Initializes the resource manager with loaders for
        images and audio files
        """
        self._resources = {} 
        self._loaders = {}
        
        self.add_resource_loader( "image", ImageLoader())
        
    def load_set(self, path):
        """Loads a set of resource tags from the given path
        
        Loads the resource set file at the given path. All resources
        are assumed to be in the same directory as the resource set file.
        The resources will not be completely loaded until specifically
        requested via the ResourceManager.get method.
        
        Resources are listed in the resource set file as follows:
        resourcetype tag path
        """
    
        basepath = os.path.split(path)[0]
        
        file = open(path, "r")
        for line in file:
            tokens = line.split()
            if len( tokens) != 3:
                raise Exception( "Invalid resource line {" + line + "}")

            type = tokens[0]    
            tag = tokens[1]
            path = os.path.join( basepath, tokens[2])
            self._resources[ tag] = _Resource( path, type)
        
    def add_resource_loader(self, type, loader):
        """Adds a loader class for the given resource type"""
        self._loaders[type] = loader
        
    def _get_loader(self, type):
        pass
        
    def get(self, tag):
        """Loads and returns the requested resource by tag.
        
        If the requested resource has already been loaded it
        will be cached, and this version will be returned rather
        than reloaded.
        
        Raises:
            ResourceException: If no resource is found for the given tag
            or no loader is found for the resource type of the requested
            resource.
        """
        
        try:
            res = self._resources[tag]
        except KeyError:
            raise ResourceException( "Unkown resource tag: "+tag)        
        
        if res.resource is None:
            try:
                loader = self._loaders[res.type]
            except KeyError:
                raise ResourceException( "Unrecognised type: " 
                    + res.type)
            res.resource = loader.load( res.filepath)
        return res.resource
        
    