"""Provides a caching image transformation class"""

import pygame
import autoloadcache

_SMOOTHSCALE = 0
_FLIP = 1
_ROTATE = 2
_SCALE2X = 3
_SCALE = 4
#_NUM_TRANSFORMS = 4

class TransformCache(object):
    """"Performs image transformations, cacheing the results for performance improvement"""

    def __init__(self):
        self._cache = autoloadcache.AutoLoadCache( self)
        self.set_rotation_interval( 7)

    def set_rotation_interval(self, interval):
        """Sets the interval used for simplifying rotation angles"""
        self.rot_interval = interval
        
    def _cache_load(self, key):
        """Autoloader method for cacheing"""    
        if key[0] == _SMOOTHSCALE:
            return pygame.transform.smoothscale( key[1], key[2])
        elif key[0] == _FLIP:
            return pygame.transform.flip( key[1], key[2], key[3])
        elif key[0] == _ROTATE:
            return pygame.transform.rotate( key[1], key[2])
        elif key[0] == _SCALE2X:
            return pygame.transform.scale2x( key[1])
        elif key[0] == _SCALE:
            return pygame.transform.scale( key[1], key[2])
            
    def smoothscale(self, surface, dimensions):
        """Performs a python smoothscale transformation"""
        return self._cache.get( (_SMOOTHSCALE, surface, dimensions))
        
    def flip(self, surface, xflip, yflip):
        """Performs a python flip transformation"""
        return self._cache.get( (_FLIP, surface, xflip, yflip))
        
    def rotate(self, surface, angle):
        """Performs a python rotation transformation
        
        The angle will be simplifying by clamping it to the rotation interval
        """
        angle = int(angle/self.rot_interval)*self.rot_interval
        angle = angle%360        
        return self._cache.get( (_ROTATE, surface, angle))
        
    def scale2x(self, surface):
        """Performs a python scale2x transformation"""
        return self._cache.get( (_SCALE2X, surface))
        
    def scale(self, surface, dimensions):
        """Performs a python scale transformation"""
        return self._cache.get( (_SCALE, surface, dimensions))