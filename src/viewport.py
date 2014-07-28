"""
Provides a class that manages the camera and screen
"""

from vector import Vec2d
import transform

SCREEN_TO_GAME = 0
GAME_TO_SCREEN = 1

class Viewport(object):

    """Class that acts as a camera viewport
    
    This class manages a zoom, pan, and a screen surface.
    """

    def __init__(self, surface):
        """Initializes the viewport with the given surface as the screen."""
        self.surface = surface
        self._zoom = 0
        self.center = Vec2d(surface.get_width()/2, surface.get_height()/2)        
        self._pan = Vec2d(0,0)
        self._zoomcache = {}
        self.transform = transform.TransformCache()

        self.MAXZOOM = 4
        self.MINZOOM = -4

    def clear(self, color=(0,0,0)):
        """Clear the screen surface."""
        self.surface.fill( color)
        
    def pan(self, coords):
        """Scroll the camera over by the given amount."""
        self._pan += coords

    def zoom(self, zlev):
        """Increments the zoom level by the given amount."""
        self._zoom = min( self.MAXZOOM, max( self.MINZOOM, self._zoom+zlev))
        print self._zoom, self.scale
        
    def zoom_in(self):
        """Zooms in 1 level."""
        self.zoom( 1)
        
    def zoom_out(self):
        """Zooms out 1 level."""
        self.zoom( -1)
        
    def translate_point(self, pos, mode=GAME_TO_SCREEN):
        """Translates and returns the given position.
        
        Uses the viewport's pan and zoom to translate the given coordinates,
        then returns the translation. Depending on the mode parameter the 
        translation is either from game to screen coords or screen to game coords.
        """
        if mode == GAME_TO_SCREEN:
            return self.center + (-self._pan+pos)*self.scale
        
            '''newpos = Vec2d(pos)*self.scale - self._pan
            return newpos + self.center'''
        elif mode == SCREEN_TO_GAME:
            return (-self.center + pos)/self.scale + self._pan
        
            '''newpos = Vec2d(pos)/self.scale + self._pan
            return newpos - self.center'''
        else:
            raise ValueError("Invalid mode paramater "+str(mode))
        
    def transform_rect(self, rect, mode=GAME_TO_SCREEN):
        """Translates and returns the given rectangle.
        
        Uses the viewport's pan and zoom to translate the given rectangle, then 
        returns the translation. Depending on the mode parameter the translation 
        is either from game to screen coords or screen to game coords.
        """    
        point = self.translate_point( rect.center, mode)
        newrect = rect.copy()
        newrect.width *= self.scale
        newrect.height *= self.scale
        newrect.center = point
        return newrect
        
    def get_scale(self):
        """Returns the viewport's scale factor based on zoom."""
        '''if self._zoom >= 0:
            return self._zoom+1
        else:
            return 1.0/(1-self._zoom)'''
        #return pow( 2, 0.5*self._zoom)
        return pow( 2, self._zoom)
        
    scale = property(get_scale)
