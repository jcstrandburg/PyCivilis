"""Framework for game interface."""

import pygame
from pygame.locals import *
import math
import game

#local imports
import vector
import viewport as viewport_mod #avoiding conflicts with variable names

#layers
LAYER_BASE      = 0
LAYER_BG        = 10
LAYER_GAME_BG   = 20
LAYER_GAME_FG   = 30
LAYER_IFACE     = 40

#viewport transform modes
VIEW_FIXED      = 1001
VIEW_RELATIVE   = 1002


class InterfaceManager( object):
    """Class that manages and controls a generic interface system."""

    def __init__(self, controller):
        """"Initialize the InterfaceManager"""
        self._selected_obj = None
        self._children = []
        self.controller = controller
        self._context_menu = None
    
    def update(self, viewport):
        """Updates all child objects with the current mouse position etc..."""
        
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
                self.cancel_context_menu()

        abs_mouse = pygame.mouse.get_pos()
        rel_mouse = viewport.translate_point( abs_mouse, viewport_mod.SCREEN_TO_GAME)
                
        for c in self._children:
            c.update( abs_mouse, rel_mouse)
            
        #resort objects by layer/position
        self._children.sort( key=lambda obj: obj.layer*1000 + obj._space_rect.center[1])#probably need to use y in sorting also            
            
    def set_context_menu(self, cmenu):
        """Cancels current context menu and sets a new one."""
        self.cancel_context_menu()
            
        self._context_menu = cmenu
        self.add_child( cmenu)
        
    def cancel_context_menu(self):
        """Removes current context menu."""
        if self._context_menu is not None:
            self._children.remove( self._context_menu)
            self._context_menu = None
        
    def add_child(self, widget):
        self._children.append(widget)
        
    def remove_child(self, widget):
        self._children.remove(widget)
        
    def draw(self, viewport):
        """Draws all child objects."""
        for c in self._children:
            c.draw( viewport)
        
    def _find_mouseovers(self):
        """Returns a list of elements under the mouse object,
        sorted by layer (higher layers occur first in list."""
        retval = []
        for c in self._children:
            if c.mouse_is_over():
                retval.append( c)

        return sorted(retval, key=lambda obj: -obj.layer)
                
    def handle_event(self, event):
        """Attempts to handle a pygame input event by sending it
        to all appropriate interface objects for the given event type.
        Will immediately return True on finding an object that handles
        the event, or return false if the event was not handled."""
        handled = False        
        
        if event.type == KEYDOWN:
            #send event to selected object
            if self._selected_obj is not None:
                handled =  self.selected_obj.handle_event(event)
        elif event.type == MOUSEBUTTONDOWN:
            #send event to all mouseover objects
            mouseovers = self._find_mouseovers()
            for m in mouseovers:
                if m.handle_event(event):
                    handled = True
                    break
                    
            if event.button == 1:
                self.cancel_context_menu()
                if not handled:
                    self.selected_obj = None
                
        return handled        
        
    def _set_selected_obj(self, sel):
        if self._selected_obj != sel:
            if self._selected_obj is not None:
                self._selected_obj.deselect()
            self._selected_obj = sel
            if sel is not None:
                sel.select()
            
    def _get_selected_obj(self):
        return self._selected_obj
        
    selected_obj = property( _get_selected_obj, _set_selected_obj)
        
    def do_action(self, action):
        """Runs the given action."""
        action.do_action(self, self.controller.game)

        
class Widget(object):
    
    def __init__(self, manager, rect, layer=LAYER_BASE, view_style=VIEW_RELATIVE):
        self.manager = manager    
        self.layer = layer
        self.selected = False
        self.finished = False
        self._mouseover = False
        self._base_rect = pygame.Rect(rect)
        self._parent = None
        self.view_style = view_style
        self.update_rect()

    def set_parent(self, p):
        self._parent = p
        self.update_rect()
        
    def update_rect(self):
        if self._parent is not None:
            self._space_rect = self._parent.translate_rect( self._base_rect)
        else:
            self._space_rect = self._base_rect
        
    def mouse_is_over(self):
        """Returns true if the mouse is over this object."""
        return self._mouseover
        
    def update(self, abs_mouse, rel_mouse):
        """Updates the display rect and mouseover status."""
        mousepos = rel_mouse if self.view_style == VIEW_RELATIVE else abs_mouse
        self._mouseover = self._space_rect.collidepoint( mousepos)
        
    def draw(self, viewport):
        pass
        
    def select(self):
        self.selected = True
    
    def deselect(self):
        self.selected = False

    def handle_event(self, event):
        """Handles a pygame input event."""
        if self.mouse_is_over():
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.manager.selected_obj = self
                return True
                
        return False
        
    def move(self, offset):
        self._base_rect.move_ip( offset)
        self.update_rect()
        
    def move_to(self, pos):
        self._base_rect.topleft = pos
        self.update_rect()
        
    def center_on(self, pos):
        self._base_rect.center = pos
        self.update_rect()
        
    def get_disp_rect(self, viewport):
        if self.view_style == VIEW_FIXED:
            return self._space_rect
        else:
            return viewport.transform_rect( self._space_rect)
        
class TestWidget(Widget):

    def draw(self, viewport):
        screen = viewport.surface
        if self.mouse_is_over():
            color = (255,255,100)
        elif self.selected:
            color = (255,255,255)
        else:
            color = (150,150,150)
            
        pygame.draw.rect( screen, color, self.get_disp_rect(viewport))
        
class Container(Widget):
    def __init__(self, manager, rect, layer=LAYER_BASE, view_style=VIEW_RELATIVE):
        self._children = []
        self._zoom = 0
        Widget.__init__(self, manager, rect, layer, view_style)
        
    def update_rect(self):
        Widget.update_rect(self)
            
        for c in self._children:
            c.update_rect()
        
    def update(self, abs_mouse, rel_mouse):
        Widget.update(self, abs_mouse, rel_mouse)

        for c in self._children:
            c.update(abs_mouse, rel_mouse)

        #resort by layer and display position
        self._children.sort( key=lambda obj: obj.layer*1000 + obj._space_rect.center[1])#probably need to use y in sorting also                        
            
    def draw(self, viewport):
        for c in self._children:
            c.draw(viewport) 

    def handle_event(self, event):
        for c in self._children:
            consumed = c.handle_event(event)
            if consumed:
                return consumed

        return consumed
        
    def add_child(self, widg):
        widg.set_parent( self)
        widg.view_style = self.view_style
        self._children.append(widg)
        
    def remove_child(self, widg):
        self._children.remove(widg)
        
    def translate_point(self, pos):
        return Vec2d(pos) + self._space_rect.topleft
        
    def translate_rect(self, rect):
        return rect.move( self._space_rect.topleft)

class TestContainer(Container):
    def draw(self, viewport):
        pygame.draw.rect( viewport.surface, (100,0,0), self.get_disp_rect(viewport))
        Container.draw(self, viewport) 


        
"""
Junk
"""

class InterfaceObject(object):
    """Base class for all interface objects."""
    
    def __init__(self, manager, renderer, obj_or_rect, 
                layer=LAYER_BASE, absolutepos=False):
                
        self.layer = layer
        self.selected = False
        self._mouseover = False
        self._renderer = renderer
        self.finished = False
        self.manager = manager
        self.selectable = True
        self.absolutepos = absolutepos
        
        print obj_or_rect.__class__.__name__
        if isinstance(obj_or_rect, game.GameObject):
            self._game_object = obj_or_rect
            self.rect = self._game_object.rect
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
    """Action handler for interface buttons and whatnot."""
    def __init__(self):
        pass
        
    def do_action(self, interface, game):
        raise NotImplementedError("InterfaceAction.do_action")
        
class ContextMenu(InterfaceObject):
    """Base class for generic context menus, with options deployed 
    in a circular model."""

    def __init__(self, manager, center, objects):
        """Initializer. 
        
        Args:
            manager: InterfaceManager object
            center: The center of the menu in game coordinates
            objects: A list of dictionaries containing information about the 
                menu options.
        """
    
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
        InterfaceObject.update(self, viewport, mousepos)
        for item in self.items:
            item.update(viewport, mousepos)
            
    def handle_event(self, event):
        """Handles the given input event, 
        returning True if the event should be consumed."""
        for item in self.items:
            if item.mouse_is_over():
                if item.handle_event(event):
                    if item.finished:
                        self.finished = True
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
    """Base class for icon based context menu items."""

    def __init__(self, manager, pos, icon, action=None):
        InterfaceObject.__init__(self, manager, icon_renderer, (0,0,40,40))
        self.rect.center = pos
        self.icon = icon
        self.action = action
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.action is not None:
                self.manager.do_action( self.action)
            self.finished = True
            return True
            
        return False

class BaseRenderer(object):
    """Base class for renderer objects, which serve as single source
    cached renderers for complex interface objects."""
    
    def __init__(self):
        pass
        
    def draw(self, viewport, object):
        img = self.generate_image( object)
        img = viewport.transform.smoothscale(img, viewport.scale)
        viewport.surface.blit( img, object.disp_rect)
        
    def generate_image(self, object):
        raise NotImplementedError("generate_image not implemented for BaseRenderer")        
        
class IconRenderer(BaseRenderer):
    """Simple icon based renderer."""

    def generate_image(self,object):
        return object.icon


        
icon_renderer = IconRenderer()
