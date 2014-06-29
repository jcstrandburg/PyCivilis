"""Framework for interface objects."""

import pygame
from pygame.locals import *

class InterfaceObject(object):
    """Base class for all interface objects."""
    
    def __init__(self, renderer, rect):
        self.layer = 0
        self.selected = False
        self.rect = pygame.Rect(rect)
        self.disp_rect = self.rect
        self._mouseover = False
        self._renderer = renderer
        
    def mouse_is_over(self):
        """Returns true if the mouse is over this object."""
        return self._mouseover
        
    def update(self, viewport, mousepos):
        self.disp_rect = viewport.transform_rect( self.rect)
        self._mouseover = self.disp_rect.collidepoint( mousepos)
        
    def draw(self, viewport):
        self._renderer.draw( viewport, self)
        
    def select(self):
        self.selected = True
    
    def deselect(self):
        self.selected = False

    def set_selected(self, sel):
        self._selected = sel
        
    def set_render_state(self, state):
        pass

    def handle_event(self, event):
        """Handles a pygame input event."""
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.select()
            return True
