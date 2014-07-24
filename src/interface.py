"""Framework for game interface."""

import pygame
from pygame.locals import *
import math
import types

#local imports
import vector
import viewport as viewport_mod #avoiding conflicts with variable names
import game

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
        self._motion_listeners = []
        
        self.fonts = {
            "smallfont": pygame.font.Font(None, 14),
            "medfont": pygame.font.Font(None, 22),
            "bigfont": pygame.font.Font(None, 30),
        }
    
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
        self._children.sort( key=lambda obj: obj.layer*1000)#probably need to use y in sorting also (not here, in viewport or something)
            
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
            if c._mouseover:
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
        elif event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
            #send event to all mouseover objects
            mouseovers = self._find_mouseovers()
            for m in mouseovers:
                if m.handle_event(event):
                    handled = True
                    break
                    
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.cancel_context_menu()
                if not handled:
                    self.selected_obj = None
        elif event.type == MOUSEMOTION:
            for widget in self._motion_listeners:
                handled = handled or widget.handle_event(event)
                if handled:
                    return handled
                
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
        
    def do_action(self, source_widget, action):
        """Runs the given action."""
        return action.do_action(source_widget, self, self.controller.game)

    def add_mousemotion_listener(self, widget):
        if widget not in self._motion_listeners:
            self._motion_listeners.append(widget)
        
    def remove_mousemotion_listener(self, widget):
        self._motion_listeners.remove(widget)

        
"""Abstract base class for interface actions."""        
class InterfaceAction(object):
    """Action handler for interface buttons and whatnot."""
    def __init__(self):
        pass
        
    def do_action(self, source_widget, interface, game):
        raise NotImplementedError("InterfaceAction.do_action")

        
"""Text generators for text label/button widgets"""
class TextGenerator(object):
    def __init__(self):
        pass

    def text_changed(self):
        raise NotImplementedError("TextGenerator.text_changed")
        
    def get_text(self):
        raise NotImplementedError("TextGenerator.get_text")
        
class StaticText(TextGenerator):
    def __init__(self, text):
        self._text = text
    
    def text_changed(self):
        return False
    
    def get_text(self):
        return self._text
        
class LambdaTextGenerator(TextGenerator):
    def __init__(self, lam):
        self._lambda = lam
        self._text = str(self._lambda())
    
    def text_changed(self):
        text2 = str(self._lambda())
        if text2 != self._text:
            self._text = text2
            return True
        return False
        
    def get_text(self):
        return self._text
        
class CompositeTextGenerator(TextGenerator):
    def __init__(self, generators):
        self._generators = tuple(generators)
        self._generate_text()

    def text_changed(self):
        for g in self._generators:
            if g.text_changed():
                self._generate_text()
                return True
        return False
        
    def _generate_text(self):
        self._text = ""
        for g in self._generators:
            self._text += g.get_text()
        
    def get_text(self):
        return self._text            
    
class WidgetBehavior(object):
    """Space positioners"""
    def _children_update_rect(self):
        for c in self._children:
            c.update_rect()
    
    def _absolute_update_rect(self):
        self._space_rect = self._base_rect
        self._children_update_rect()

    def _relative_update_rect(self):
        if self._parent is not None:
            self._space_rect = self._parent.translate_rect(self._base_rect)
        else:
            self._space_rect = self._base_rect
        self._children_update_rect()            
            
    """Viewport positioners"""
    
    def _absolute_get_disp_rect(self, viewport):
        return self._space_rect

    def _relative_get_disp_rect(self, viewport):
        return viewport.transform_rect( self._space_rect)           
    
    """Updater methods"""
    def _children_update(self, abs_mouse, rel_mouse):
        for c in self._children:
            mo = c.update(abs_mouse, rel_mouse)
            self._mouseover = self._mouseover or mo
        self._children.sort( key=lambda obj: obj.layer)
        return self._mouseover

    def _relative_update(self, abs_mouse, rel_mouse):
        self._mouseover = self._space_rect.collidepoint( rel_mouse)
        self._children_update(abs_mouse, rel_mouse)        
        return self._mouseover        
            
    def _absolute_update(self, abs_mouse, rel_mouse):
        self._mouseover = self._space_rect.collidepoint( abs_mouse)
        self._children_update(abs_mouse, rel_mouse)
        return self._mouseover        
        
    def _transparent_update(self, abs_mouse, rel_mouse):
        self._mouseover = False
        self._children_update(abs_mouse, rel_mouse)
        return self._mouseover        
        
    """Event handlers"""
    def _self_handle_event(self,event):
        handled = False
        if self._mouseover:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self._lclick_action is not None:
                        handled = handled or self.manager.do_action( self, self._lclick_action)
                    if self._selectable:
                        self.manager.selected_obj = self
                        handled = True
                elif event.button == 3:
                    if self._rclick_action is not None:
                        handled = handled or self.manager.do_action( self, self._rclick_action)                        
                
        return handled

    def _children_handle_event(self, event):
        for c in self._children:
            response = c.handle_event(event)
            if response:
                return response
        return False

    def _standard_event_handler(self, event):#children first, then me
        response = self._children_handle_event(event)
        if not response:
            response = self._self_handle_event(event)
        return response
        
    def _greedy_event_handler(self, event):
        response = self._self_handle_event(event)
        if not response:
            response = self._children_handle_event(event)
        return response

    def _deaf_event_handler(self, event):
        return self._children_handle_event(event)

    def _super_deaf_event_handler(self, event):
        return False
        
class BaseWidget(WidgetBehavior):
    
    def __init__(self, manager, rect, layer=LAYER_BASE):
        self.manager = manager    
        self.layer = layer
        self.selected = False
        self.finished = False
        self._mouseover = False
        self._base_rect = pygame.Rect(rect)
        self._parent = None
        self._selectable = True
        self._lclick_action = None
        self._rclick_action = None
        self._children = []
        self.clamp = False
        self.update_rect()

    def set_parent(self, p):
        self._parent = p
        self.get_disp_rect = types.MethodType(p.get_disp_rect.__func__, self)
        self.update_rect()
       
    def draw(self, viewport):
        raise NotImplementedError("BaseWidget.draw")
        
    def select(self):
        self.selected = True
    
    def deselect(self):
        self.selected = False

    def handle_event(self, event):
        """Handles a pygame input event."""
        
        handled = False
        if self.mouse_is_over():
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self._lclick_action is not None:
                        handled = handled or self.manager.do_action( self, self._lclick_action)
                    if self._selectable:
                        self.manager.selected_obj = self
                        handled = True
                elif event.button == 3:
                    if self._rclick_action is not None:
                        handled = handled or self.manager.do_action( self, self._rclick_action)                        
                
        return handled
        
    def move(self, offset):
        self._base_rect.move_ip( offset)
        self.update_rect()
        
    def move_to(self, pos):
        self._base_rect.topleft = pos
        self.update_rect()
        
    def center_on(self, pos):
        self._base_rect.center = pos
        self.update_rect()
            
    def set_lclick_action(self, action):
        self._lclick_action = action
        
    def set_rclick_action(self, action):
        self._rclick_action = action
            
    def draw(self, viewport):
        self._draw_self(viewport)
        for c in self._children:
            c.draw(viewport) 
        
    def add_child(self, widg):
        widg.set_parent( self)
        self._children.append(widg)
        
    def remove_child(self, widg):
        self._children.remove(widg)
        
    def translate_point(self, pos):
        return Vec2d(pos) + self._space_rect.topleft
        
    def translate_rect(self, rect):
        newrect = rect.move( self._space_rect.topleft)
            
        if self.clamp:
            return newrect.clamp( self._space_rect)
        else:
            return newrect        

class TestWidget(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._relative_update

    def _draw_self(self, viewport):
        screen = viewport.surface
        if self._mouseover:
            color = (255,255,100)
        elif self.selected:
            color = (255,255,255)
        else:
            color = (150,150,150)

        disp_rect = self.get_disp_rect(viewport)        
        pygame.draw.rect( viewport.surface, (0,0,0), disp_rect)
        pygame.draw.rect( viewport.surface, color, disp_rect.inflate((-2,-2)))

class TestPanel(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._transparent_update

    def _draw_self(self, viewport):
        framecolor = (0,0,0)
        disp_rect = self.get_disp_rect(viewport)        
        pygame.draw.rect( viewport.surface, framecolor, disp_rect)
        pygame.draw.rect( viewport.surface, (155,155,155), disp_rect.inflate(-4,-4))
        
class DragBar(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._relative_update

    def __init__(self, manager, rect):
        BaseWidget.__init__(self, manager, rect)
        self._dragging = False
        self._selectable = False
    
    def _draw_self(self, viewport):
        disp_rect = self.get_disp_rect(viewport)
        pygame.draw.rect( viewport.surface, (100,100,200), disp_rect)
        
    def handle_event(self, event):
        if self._mouseover and event.type == MOUSEBUTTONDOWN and event.button == 1:
            self._dragging = True
            self.manager.add_mousemotion_listener( self)
            return True
        elif self._mouseover and event.type == MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
            self.manager.remove_mousemotion_listener( self)
            return True
        elif event.type == MOUSEMOTION:
            if self._parent is not None:
                self._parent.move( event.rel)
                
class DragPanel(TestPanel):
    def __init__(self, manager, rect, layer=LAYER_BASE):
        TestPanel.__init__(self, manager, rect, layer)
        dragrect = pygame.Rect(rect).inflate( (-4,0))
        dragrect.topleft = (2,2)
        dragrect.h = 20
        self.add_child( DragBar(manager, dragrect))
        
class IconWidget(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._relative_update

    def __init__(self, manager, icon, center, layer=LAYER_IFACE):
        self.icon = icon
        rect = self.icon.get_rect()
        rect.center = center
        BaseWidget.__init__(self, manager, rect, layer)
        self._selectable = False
        
    def _draw_self(self, viewport):
        viewport.surface.blit(self.icon, self.get_disp_rect(viewport))
        
class RadialContextMenu(BaseWidget):
    """Base class for generic context menus, with options deployed 
    in a circular model."""
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._transparent_update
    
    def __init__(self, manager, center, objects):
        """Initializer. 
        
        Args:
            manager: InterfaceManager object
            center: The center of the menu in game coordinates
            objects: A list of dictionaries containing information about the 
                menu options.
        """
        self.icon_size = 1
        for obj in objects:
            icon = obj["icon"]
            self.icon_size = max(self.icon_size, icon.get_width(), icon.get_height())
            
        dist = math.sqrt( len(objects)-1)*self.icon_size/2
        self._radius = dist
        rect = pygame.Rect(0,0, 2*self.icon_size+self.icon_size, 2*self.icon_size+self.icon_size)
        rect.center = center
        
        BaseWidget.__init__(self, manager, rect, LAYER_IFACE)
        
        for i in range( len(objects)):
            angle = (2*i*math.pi)/len(objects)
            
            pos = (math.sin(angle)*dist, -math.cos(angle)*dist)
            item = IconWidget(manager, objects[i]["icon"], pos)
            item.set_lclick_action( objects[i]["action"])
            self.add_child( item)
        
    def _draw_self(self, viewport):
        point = viewport.translate_point( self._space_rect.center)
        if self._mouseover:
            color = (255,255,0)
        else:
            color = (255,255,255)
        if self._radius > 1:
            pygame.draw.circle( viewport.surface, color, point.int_tuple, 
                                int(self._radius*viewport.scale), 3)
        
    def translate_point(self, pos):
        return Vec2d(pos) + self._space_rect.center
        
    def translate_rect(self, rect):
        return rect.move( self._space_rect.center)
        
class TextLabel(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._transparent_update

    def __init__(self, manager, position, fontname, text_gen, layer=LAYER_IFACE):
        self._textgen = text_gen
        self._origin = position
        self._font = manager.fonts[fontname]
        self._regenerate()
        BaseWidget.__init__(self, manager, self._base_rect, layer)
        self._selectable = False        
        
    def _regenerate(self):
        text = self._textgen.get_text()
        self._img = self._font.render( text, True, (0,0,0))
        self._base_rect = self._img.get_rect()
        self._base_rect.topleft = self._origin
        
    def _draw_self(self, viewport):
        if self._textgen.text_changed():
            self._regenerate()
        disp_rect = self.get_disp_rect(viewport)
        viewport.surface.blit( self._img, disp_rect)

class TextButton(TextLabel):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._relative_update

    def __init__(self, manager, position, fontname, text_gen, action=None, layer=LAYER_IFACE):
        TextLabel.__init__(self, manager, position, fontname, text_gen, layer)
        self.set_lclick_action(action)        
        
    def _regenerate(self):
        text = self._textgen.get_text()
        self._mainimg = self._font.render( text, True, (0,0,0))
        self._altimg = self._font.render( text, True, (255,255,0))
        self._img = self._mainimg
        self._base_rect = self._mainimg.get_rect()
        self._base_rect.topleft = self._origin

    def _draw_self(self, viewport):
        self._img = self._altimg if self._mouseover else self._mainimg
        TextLabel._draw_self(self, viewport)
        
class GameObjWidget(BaseWidget):
    """Base class for all interface objects."""
    
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    update = BaseWidget._relative_update
    
    def __init__(self, manager, obj, layer=LAYER_BASE):
        BaseWidget.__init__(self,manager,obj.rect,layer)
        self._game_object = obj
        self._selectable = True
  
    def update(self, abs_mouse, rel_mouse):
        if self._base_rect.center != self._game_object.rect.center:
            self._base_rect.center = self._game_object.rect.center
            self.update_rect()
            BaseWidget._relative_update(self, abs_mouse, rel_mouse)
        
    def _draw_self(self, viewport):
        if self.selected:
            color = (255,255,255)
        else:
            color = (100,100,100)
    
        pygame.draw.rect(viewport.surface, color, 
                        self.get_disp_rect(viewport))
        
    def select(self):
        BaseWidget.select(self)
        self._game_object.select()
        
    def deselect(self):
        BaseWidget.deselect(self)
        self._game_object.select()
        
    def get_game_object(self):
        return self._game_object
        
    game_object = property( get_game_object)    