"""Provides a caching image transformation class"""

import pygame
import autoloadcache

_SMOOTHSCALE = 0
_FLIP = 1
_ROTATE = 2
_SCALE2X = 3
_SCALE = 4
_HALO = 5
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
        elif key[0] == _HALO:
            return self._do_halo( key[1], key[2], key[3])
            
    def _do_halo(self, surface, thickness, border_color):
        """Transform function that creates a halo around the given image. Currently
        has an issue where the halo is not rendered correctly around the corners of the
        image. This could be solved by checking the alpha of the final image before setting
        it, and refusing to put pixels of lesser alpha than what is already there."""
    
        newsurf = pygame.Surface((surface.get_width()+2*thickness, 
                                    surface.get_height()+2*thickness), 
                                    pygame.SRCALPHA)
        newsurf.blit( surface, (thickness,thickness))
        a_thresh = 200
        
        cols = []
        for i in xrange(thickness):
            alpha = int(a_thresh * (1-float(i)/thickness))
            color = pygame.Color(border_color[0], border_color[1], border_color[2], alpha)
            cols.append(color)
        
        for x in xrange(surface.get_width()):
            #top border of halo
            for y in xrange(surface.get_height()):
                color = surface.get_at( (x,y))
                if color.a > a_thresh:
                    for i in range(thickness):
                        newsurf.set_at((x+thickness,y+i), cols[thickness-i-1])
                    break
                    
            #bottom border of halo
            for y in xrange(surface.get_height()-1, -1, -1):
                color = surface.get_at( (x,y))
                if color.a > a_thresh:
                    for i in range(thickness):
                        newsurf.set_at((x+thickness,y+thickness+i+1), cols[i])
                    break

        for y in xrange(surface.get_height()):
            #left border of halo
            for x in xrange(surface.get_width()):
                color = surface.get_at( (x,y))
                if color.a > a_thresh:
                    for i in range(thickness):
                        newsurf.set_at((x+i,y+thickness), cols[thickness-i-1])
                    break
                    
            #fight border of halo
            for x in xrange(surface.get_width()-1, -1, -1):
                color = surface.get_at( (x,y))
                if color.a > a_thresh:
                    for i in range(thickness):
                        newsurf.set_at((x+thickness+i+1,y+thickness), cols[i])
                    break

                    
        return newsurf
    
        #return pygame.transform.laplacian(surface)
            
    def smoothscale(self, surface, dim_or_scale, cached=True):
        """Performs a pygame smoothscale transformation"""
        if not hasattr(dim_or_scale, "__getitem__"):
            dim_or_scale = (int(surface.get_width()*dim_or_scale),
                            int(surface.get_height()*dim_or_scale))

        return self._trans_func[cached]( (_SMOOTHSCALE, surface, dim_or_scale))
        
    def flip(self, surface, xflip, yflip, cached=True):
        """Performs a pygame flip transformation"""
        return self._trans_func[cached]( (_FLIP, surface, xflip, yflip))
        
    def rotate(self, surface, angle, cached=True):
        """Performs a pygame rotation transformation
        
        The angle will be simplifying by clamping it to the rotation interval
        """
        angle = int(angle/self.rot_interval)*self.rot_interval
        angle = angle%360        
        return self._trans_func[cached]( (_ROTATE, surface, angle))
        
    def scale2x(self, surface, cached=True):
        """Performs a pygame scale2x transformation"""
        return self._trans_func[cached]( (_SCALE2X, surface))
        
    def scale(self, surface, dim_or_scale, cached=True):
        """Performs a pygame scale transformation"""
        if not hasattr(dim_or_scale, "__getitem__"):
            dim_or_scale = (int(surface.get_width()*dim_or_scale),
                            int(surface.get_height()*dim_or_scale))
        
        return self._trans_func[cached]( (_SCALE, surface, dim_or_scale))
        
    def halo(self, surface, thickness, color=(240,240,50), cached=True):
        """Performs a pygame scale2x transformation"""
        return self._trans_func[cached]( (_HALO, surface, thickness, color))