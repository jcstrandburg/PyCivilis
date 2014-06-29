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
        self._trans_func = {True: self._cache.get, False: self._cache_load}

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
            
    def smoothscale(self, surface, dim_or_scale, cached=True):
        """Performs a python smoothscale transformation"""
        if not hasattr(dim_or_scale, "__getitem__"):
            dim_or_scale = (int(surface.get_width()*dim_or_scale),
                            int(surface.get_height()*dim_or_scale))

        return self._trans_func[cached]( (_SMOOTHSCALE, surface, dim_or_scale))
        
    def flip(self, surface, xflip, yflip, cached=True):
        """Performs a python flip transformation"""
        return self._trans_func[cached]( (_FLIP, surface, xflip, yflip))
        
    def rotate(self, surface, angle, cached=True):
        """Performs a python rotation transformation
        
        The angle will be simplifying by clamping it to the rotation interval
        """
        angle = int(angle/self.rot_interval)*self.rot_interval
        angle = angle%360        
        return self._trans_func[cached]( (_ROTATE, surface, angle))
        
    def scale2x(self, surface, cached=True):
        """Performs a python scale2x transformation"""
        return self._trans_func[cached]( (_SCALE2X, surface))
        
    def scale(self, surface, dim_or_scale, cached=True):
        """Performs a python scale transformation"""
        if not hasattr(dim_or_scale, "__getitem__"):
            dim_or_scale = (int(surface.get_width()*dim_or_scale),
                            int(surface.get_height()*dim_or_scale))
        
        return self._trans_func[cached]( (_SCALE, surface, dim_or_scale))