"""Framework for game interface."""

import pygame
from pygame.locals import *
import math
import game

#local imports
import vector

#layers
LAYER_BASE      = 0
LAYER_BG        = 10
LAYER_GAME_BG   = 20
LAYER_GAME_FG   = 30
LAYER_IFACE     = 40

class InterfaceManager( object):
    def __init__(self, controller):
        """"Initialize the InterfaceManager"""
        self._selected_obj = None
        self._children = []
        self.controller = controller
        self._context_menu = None
    
    def update(self, viewport):
        """Updates all child objects with the current mouse position etc..."""
        #resort objects by layer
        self._children.sort( key=lambda obj: obj.layer)#probably need to use y in sorting also
        mpos = pygame.mouse.get_pos()
        
        #remove "finished" objects
        i, j = 0, 0
        while j < len(self._children):
            if not self._children[j].finished:
                self._children[i] = self._children[j]
                i+=1        
            j += 1        
        del self._children[i:]
        
        if self._context_menu is not None:
            if self._context_menu.finished:
                self._context_menu = None
        
        for c in self._children:
            c.update( viewport, mpos)
            
    def set_context_menu(self, cmenu):
        """Cancels current context menu and sets a new one."""
        self.cancel_context_menu()
            
        self._context_menu = cmenu
        self.add_child( cmenu)
        
    def cancel_context_menu(self):
        """Removes current context menu."""
        print "wat", self._context_menu
        if self._context_menu is not None:
            self._children.remove( self._context_menu)
            self._context_menu = None
        
    def add_child(self, iobj):
        self._children.append(iobj)

    def remove_child(self, iojb):
        self._children.remove(iobj)
        
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
        handled = False    
        if event.type == KEYDOWN:
            if self._selected_obj is not None:
                handled =  self._selected_obj.handle_event(event)
        elif event.type == MOUSEBUTTONDOWN:
            mouseovers = self._find_mouseovers()
            for m in mouseovers:
                if m.handle_event(event):
                    handled = True
                    break
                    
            if event.button == 1:
                self.cancel_context_menu()
                
        return handled        
        
    def _set_selected_obj(self, sel):
        if self._selected_obj != sel:
            if self._selected_obj is not None:
                self._selected_obj.deselect()
            self._selected_obj = sel
            sel.select()
            
    def _get_selected_obj(self, sel):
        return self._selected_obj
        
    selected_obj = property( _get_selected_obj, _set_selected_obj)
        
    def do_action(self, action):
        """Runs the given action."""
        action.do_action(self, self.controller)

class InterfaceObject(object):
    """Base class for all interface objects."""
    
    def __init__(self, manager, renderer, obj_or_rect, layer=LAYER_BASE):
        self.layer = layer
        self.selected = False
        self._mouseover = False
        self._renderer = renderer
        self.finished = False
        self.manager = manager
        self.selectable = True
        
        if isinstance(obj_or_rect, game.GameObject):
            self._game_object = obj_or_rect
            self.rect = self._game_object
        else:
            self._game_object = None
            self.rect = pygame.Rect( obj_or_rect)
        self.disp_rect = self.rect            
        
        
    def mouse_is_over(self):
        """Returns true if the mouse is over this object."""
        return self._mouseover
        
    def update(self, viewport, mousepos):
        """Updates the display rect and mouseover status."""
        if self._game_object is not None:
            self.rect = self._game_object.rect
        self.disp_rect = viewport.transform_rect( self.rect)
        self._mouseover = self.disp_rect.collidepoint( mousepos)
        
    def draw(self, viewport):
        self._renderer.draw( viewport, self)
        
    def select(self):
        self.selected = True
        if self._game_object is not None:
            self._game_object.select()
    
    def deselect(self):
        self.selected = False
        if self._game_object is not None:
            self._game_object.deselect()

    def set_selected(self, sel):
        self._selected = sel
        
    def set_render_state(self, state):
        pass

    def handle_event(self, event):
        """Handles a pygame input event."""
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self._game_object is None and self.selectable:
                self.manager.selected_obj = self
            elif self._game_object is not None and self._game_object.selectable():
                self.manager.selected_obj = self
            return True
        elif event.type == MOUSEBUTTONDOWN and event.button == 3:
            if self._game_object is not None:
                print "attempting to get context menu from clicked item"
            return True
                
        return False
        
    def get_game_object(self):
        return self._game_object
        
    game_object = property( get_game_object)

class InterfaceAction(object):
    def __init__(self):
        pass
        
    def do_action(self, interface, game):
        raise NotImplementedError("do_action not implemented in base InterfaceAction")
        
class ContextMenu(InterfaceObject):
    def __init__(self, manager, center, objects):
        InterfaceObject.__init__(self, manager, None, (0,0,10,10), LAYER_IFACE)
        self.center = vector.Vec2d(center)
        self.items = []
        self.icon_size = 1
        
        for obj in objects:
            icon = obj["icon"]
            self.icon_size = max(self.icon_size, icon.get_width(), icon.get_height())
        
        for i in range( len(objects)):
            angle = (2*i*math.pi)/len(objects)
            dist = math.sqrt( len(objects)-1)*self.icon_size/2
            #dist = pow(len(objects)-1,0.625)*self.icon_size/2*0.8
            
            pos = self.center + (math.sin(angle)*dist, -math.cos(angle)*dist)
            item = ContextMenuItem(manager, pos, objects[i]["icon"], objects[i]["action"])
            self.items.append(item)
        
    def mouse_is_over(self):
        """Returns true if the mouse is over any of the menu items."""
        for item in self.items:
            if item.mouse_is_over():
                return True
        return False
        
    def update(self, viewport, mousepos):
        for item in self.items:
            item.update(viewport, mousepos)
            
    def handle_event(self, event):
        """Handles the given input event, 
        returning True if the event should be consumed."""
        print "Attempting to handle event in ContextMenu"
        for item in self.items:
            if item.mouse_is_over():
                if item.handle_event(event):
                    if item.finished:
                        self.finished = True
                    print "Context menu handled event"
                    return True                    
        return InterfaceObject.handle_event(self,event)
        
    def draw(self, viewport):
        point = viewport.translate_point( self.center).int_tuple
        if self.mouse_is_over():
            color = (255,255,0)
        else:
            color = (255,255,255)
        pygame.draw.circle( viewport.surface, color, point, 
                            int(0.5*self.icon_size*viewport.scale))
        for item in self.items:
            item.draw(viewport)
        

class ContextMenuItem(InterfaceObject):
    def __init__(self, manager, pos, icon, action=None):
        InterfaceObject.__init__(self, manager, icon_renderer, (0,0,40,40))
        self.rect.center = pos
        self.icon = icon
        self.action = action
        
    def handle_event(self, event):
        print "context menu item attempting event handling"
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.action is not None:
                self.manager.do_action( self.action)
            self.finished = True
            return True
            
        return False

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