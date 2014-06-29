"""Framework for game interface."""

import pygame
from pygame.locals import *
import math

#local imports
import vector

class InterfaceManager( object):
    def __init__(self):
        self._selected_obj = None
        self._children = []
    
    def update(self, viewport):
        #resort objects by layer
        self._children.sort( key=lambda obj: obj.layer)
        mpos = pygame.mouse.get_pos()
        for c in self._children:
            c.update( viewport, mpos)
        
    def add_object(self, iobj):
        self._children.append(iobj)
        
    def draw(self, viewport):
        for c in self._children:
            c.draw( viewport)
        
    def _find_mouseovers(self):
        retval = []
        for c in self._children:
            if c.mouse_is_over():
                retval.append( c)

        return sorted(retval, key=lambda obj: -obj.layer)
                
    def handle_event(self, event):
        if event.type == KEYDOWN:
            if self._selected_obj is not None:
                self._selected_obj.handle_event(event)
            pass
        elif event.type == MOUSEBUTTONDOWN:
            mouseovers = self._find_mouseovers()
            for m in mouseovers:
                if m.handle_event(event):
                    if m.selected and m != self._selected_obj:
                        if self._selected_obj is not None:
                            self._selected_obj.deselect()
                        self._selected_obj = m
                    return

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

class InterfaceAction(object):
    def __init__(self):
        pass
        
    def do_action(self, interface, game):
        raise NotImplementedError("do_action not implemented in base InterfaceAction")
        
class ContextMenu(InterfaceObject):
    def __init__(self, renderer, center, icons):
        InterfaceObject.__init__(self, renderer, (0,0,10,10))
        self.center = vector.Vec2d(center)
        self.items = []
        
        for i in range( len(icons)):
            angle = (2*i*math.pi)/len(icons)
            dist = math.sqrt( len(icons)-1)*20
            pos = self.center + (math.sin(angle)*dist, -math.cos(angle)*dist)
            item = ContextMenuItem(pos, icons[i])
            self.items.append(item)
        
    def mouse_is_over(self):
        for item in self.items:
            if item.mouse_is_over():
                return True
        return False
        
    def update(self, viewport, mousepos):
        for item in self.items:
            item.update(viewport, mousepos)
            
    def handle_event(self, event):
        for item in self.items:
            if item.mouse_is_over():
                item.handle_event(event)
        
    def draw(self, viewport):
        point = viewport.translate_point( self.center).int_tuple
        pygame.draw.circle( viewport.surface, (255,255,255), point, int(30*viewport.scale))
        for item in self.items:
            item.draw(viewport)
        

class ContextMenuItem(InterfaceObject):
    def __init__(self, pos, icon):
        InterfaceObject.__init__(self, icon_renderer, (0,0,40,40))
        self.rect.center = pos
        self.icon = icon
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            print "Item clicked"+str(self.rect.center)
            return True

class BaseRenderer(object):
    def __init__(self):
        pass
        
    def draw(self, viewport, object):
        img = self.generate_image( object)
        img = viewport.transform.smoothscale(img, viewport.scale)
        viewport.surface.blit( img, object.disp_rect)
        
    def generate_image(self, object):
        raise NotImplementedError("generate_image not implemented for BaseRenderer")        
        
class IconRenderer(BaseRenderer):
    def generate_image(self,object):
        return object.icon
        
icon_renderer = IconRenderer()