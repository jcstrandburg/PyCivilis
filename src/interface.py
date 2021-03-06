"""Framework for game interface."""

import pygame
from pygame.locals import *
import math
import sets

#local imports
import vector
import viewport as viewport_mod #avoiding conflicts with variable names
import game
import actor

#layers
LAYER_BASE          = 0
LAYER_BG            = 10
LAYER_GAME_BG       = 20
LAYER_GAME_FG       = 30
LAYER_IFACE         = 40
LAYER_IFACE_LOWER   = 40
LAYER_IFACE_UPPER   = 50

#event handling flags
EVENT_UNHANDLED         = 0
EVENT_HANDLED           = 1
EVENT_PRESERVE_CONTEXT  = 2


tester = sets.Set()

class InterfaceManager( object):
    """Class that manages and controls a generic interface system."""

    def __init__(self, controller):
        """"Initialize the InterfaceManager"""
        self._selected_obj = None
        self._children = []
        self._new_children = []
        self.controller = controller
        self._context_menu = None
        self._selection_menu = None
        self._motion_listeners = []
        
        self.fonts = {
            "smallfont": pygame.font.Font(None, 16),
            "medfont": pygame.font.Font(None, 22),
            "bigfont": pygame.font.Font(None, 30),
        }
    
    def update(self, viewport):
        """Updates all child objects with the current mouse position etc..."""
        
        if len(self._new_children) > 0:
            self._children.extend(self._new_children)
            self._new_children[:] = []
        
        #remove "finished" objects
        self._children[:] = [child for child in self._children if not child.finished]
        
        if self._context_menu is not None:
            if self._context_menu.finished:
                self.cancel_context_menu()
                
        for c in self._children:
            c.update( viewport, pygame.mouse.get_pos())
            
        #resort objects by layer/position
        self._children.sort( key=lambda obj: obj.layer *100000 + obj._disp_rect.bottom )
            
    def set_context_menu(self, cmenu):
        """Cancels current context menu and sets a new one."""
        self.cancel_context_menu()
            
        self._context_menu = cmenu
        self.add_child( cmenu)
        
    def cancel_context_menu(self):
        
        """Removes current context menu."""
        if self._context_menu is not None:
            self._context_menu.finished = True
            self._context_menu = None
            
    def set_selection_menu(self, smenu):
        if self._selection_menu is not None:
            self._children.remove( self._selection_menu)
            self._selection_menu = None
        
        if smenu is not None:
            self._selection_menu = smenu
            self.add_child( smenu)
        
    def add_child(self, widget):
        self._new_children.append(widget)
        
    def remove_child(self, widget):
        self._children.remove(widget)
        
    def draw(self, viewport):
        """Draws all child objects."""
        for c in self._children:
            c.draw( viewport)
        
    def _find_mouseovers(self):
        """Returns a list of elements under the mouse object,
        sorted by layer (higher layers occur first in list."""
        mouseovers = []
        for c in self._children:
            if c._mouseover:
                mouseovers.append( c)

        return sorted(mouseovers, key=lambda obj: (-obj.layer, -obj._space_rect.bottom))
                
    def handle_event(self, event):
        """Attempts to handle a pygame input event by sending it
        to all appropriate interface objects for the given event type.
        Will immediately return True on finding an object that handles
        the event, or return false if the event was not handled."""
        handled = EVENT_UNHANDLED        
        
        if event.type == KEYDOWN:
            #send event to selected object
            if self._selected_obj is not None:
                handled =  self.selected_obj.handle_event(event)
        elif event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
            #send event to all mouseover objects
            mouseovers = self._find_mouseovers()
            for m in mouseovers:
                handled = handled | m.handle_event(event)
                if handled:
                    break
        elif event.type == MOUSEMOTION:
            for widget in self._motion_listeners:
                handled = handled | widget.handle_event(event)
                if handled:
                    return handled

        if not handled:
            if event.type == MOUSEBUTTONDOWN:
                '''if event.button in (1,3):
                    self.cancel_context_menu()'''                
                if event.button == 1:
                    self.selected_obj = None

        if event.type == MOUSEBUTTONDOWN and not (handled & EVENT_PRESERVE_CONTEXT):
            if event.button in (1,3):
                self.cancel_context_menu()  

            
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

        
class InterfaceAction(object):
    """Abstract base class for interface actions. Serves as an 
    action handler for interface buttons and whatnot."""
    
    def __init__(self):
        pass
        
    def do_action(self, source_widget, interface, game):
        raise NotImplementedError("InterfaceAction.do_action")


class CloseAction(InterfaceAction):
    '''Generic InterfaceAction for closing/finishing an interface item'''
    
    def __init__(self, target):
        InterfaceAction.__init__(self)
        self.target = target
        
    def do_action(self, source_widget, interface, game):
        self.target.finished = True

        
class TextGenerator(object):
    """Text generators for text label/button widgets"""
    
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
    """Container class for all base widget behaviors."""

    
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
        
    def _fixedsize_get_disp_rect(self, viewport):
        rect = self._space_rect.copy()
        rect.center = viewport.translate_point( rect.center)
        return rect
    
    """Updater methods"""
    def _opaque_update(self, viewport, mousepos):
        self._mouseover = self._disp_rect.collidepoint( mousepos)
        
    def _transparent_update(self, viewport, mousepos):
        self._mouseover = False
        
    """Event handlers"""
    def _self_handle_event(self,event):
        handled = EVENT_UNHANDLED
        if self._mouseover:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self._lclick_action is not None:
                        handled = handled | self.manager.do_action( self, self._lclick_action)
                    if self._selectable:
                        self.manager.selected_obj = self
                        handled = EVENT_HANDLED
                elif event.button == 3:
                    if self._rclick_action is not None:
                        handled = handled | self.manager.do_action( self, self._rclick_action)                        
                
        return handled

    def _children_handle_event(self, event):
        for c in self._children:
            response = c.handle_event(event)
            if response:
                return response
        return EVENT_UNHANDLED

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
        return EVENT_UNHANDLED
   
   
class BaseWidget(WidgetBehavior):
    
    def __init__(self, manager, rect, layer=LAYER_BASE):
        self.manager = manager    
        self.layer = layer
        self.selected = False
        self.finished = False
        self._mouseover = False
        self._base_rect = pygame.Rect(rect)
        self._disp_rect = self._space_rect = self._base_rect
        self._parent = None
        self._selectable = True
        self._lclick_action = None
        self._rclick_action = None
        self._children = []
        self._new_children = []
        self.clamp = False
        self.update_rect()

    def set_parent(self, p):
        self._parent = p
        self.update_rect()
        
    def select(self):
        self.selected = True
        sel_menu = self.get_selection_menu()
        self.manager.set_selection_menu( sel_menu)
    
    def deselect(self):
        self.selected = False
        self.manager.set_selection_menu( None)
        
    def get_selection_menu(self):
        return None
        
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
        self._draw_self(viewport, self._disp_rect)
        for c in self._children:
            c.draw(viewport)
            
    def alt_draw(self, viewport):
        self._draw_self(viewport, self.get_disp_rect(viewport))
        for c in self._children:
            c.alt_draw(viewport)
            
    def update(self, viewport, mousepos):
        
        if len(self._new_children) > 0:
            self._children.extend(self._new_children)
            self._new_children[:] = []
        
        self._disp_rect = self.get_disp_rect(viewport)
        self._update_handler(viewport, mousepos)
        for c in self._children:
            mo = c.update(viewport, mousepos)
            self._mouseover = self._mouseover or mo
        self._children.sort( key=lambda obj: obj.layer)
        return self._mouseover
        
    def add_child(self, widg):
        widg.set_parent( self)
        self._new_children.append(widg)
        
    def remove_child(self, widg):
        self._children.remove(widg)
        
    def translate_point(self, pos):
        return vector.Vec2d(pos) + self._space_rect.topleft
        
    def translate_rect(self, rect):
        newrect = rect.move( self._space_rect.topleft)
            
        if self.clamp:
            return newrect.clamp( self._space_rect)
        else:
            return newrect
 
 
class MapWidget(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    _update_handler = BaseWidget._opaque_update

    def __init__(self, manager, game):
        self.img = manager.controller.assets.get("water_tile")
        self.img2 = manager.controller.assets.get("grass_tile")
        self.img3 = manager.controller.assets.get("desert_tile")
        
        self.transitions = []
        for i in xrange(256):
            tag = "trans_%03d" % (i,)
            self.transitions.append(manager.controller.assets.get(tag))
        
        self.game = game
        map = self.game.map
        
        dims = map.size
        wdims = (dims[0]*200, dims[1]*200)
        
        BaseWidget.__init__(self, manager, (-wdims[0]/2,-wdims[1]/2,wdims[0],wdims[1]), LAYER_BASE)
        self._selectable = False
        self.buffered_map = None
        self.buffered_topleft = None
        self.buffered_botright = None
        self.tile_size = 200
        
    def _buffer_map(self, viewport, disp_rect, topleft, botright):
        if self.buffered_map is None:
            self.buffered_map = pygame.Surface(viewport.surface.get_size())
            
        #if self.buffered_topleft == topleft and self.buffered_botright == botright:
        #    return
        self.buffered_topleft = topleft
        self.buffered_botright = botright
            
            
        self.buffered_map.fill((0,0,0,0))
        img1 = viewport.transform.scale(self.img, viewport.scale)
        img2 = viewport.transform.scale(self.img2, viewport.scale)
        img3 = viewport.transform.scale(self.img3, viewport.scale)

        map_size = self.game.map.size        
        offset_x = map_size[0]/2
        offset_y = map_size[1]/2
        limit1 = (topleft[0]/200 + offset_x, topleft[1]/200 + offset_y)
        limit2 = (botright[0]/200 + offset_x, botright[1]/200 + offset_y)

        x1 = max(0, int(math.floor(limit1[0]-0.5)))
        y1 = max(0, int(math.floor(limit1[1]-0.5)))
        x2 = min(map_size[0], int(math.ceil(limit2[0]+0.5)))
        y2 = min(map_size[1], int(math.ceil(limit2[1]+0.5)))
        
        x_range = xrange(x1,x2)
        y_range = xrange(y1,y2)
        
        for u in x_range:
            for v in y_range:
                tile = self.game.map.get_terrain_at((u,v))
                if tile == 0:
                    img = img1
                elif tile == 1:
                    img = img2
                elif tile == 2:
                    img = img3
                else:
                    img = None
                    
                dim = img.get_rect()
                pos = (disp_rect.x + u*dim.w, disp_rect.y + v*dim.h)
                self.buffered_map.blit( img, pos)
                
                if tile != 1:
                    trans = self.game.map.get_tile_at((u,v))
                    if trans != 0:
                        trans_tile = self.transitions[trans]
                        trans_tile = viewport.transform.scale(trans_tile, viewport.scale)
                        self.buffered_map.blit( trans_tile, pos)
                                    
        
        
    def _draw_self(self, viewport, disp_rect):
        size = viewport.surface.get_size()
        limit1 = viewport.translate_point((0,0), viewport_mod.SCREEN_TO_GAME)
        limit2 = viewport.translate_point((size[0], size[1]), viewport_mod.SCREEN_TO_GAME)
        
        self._buffer_map(viewport, disp_rect, limit1, limit2)
        viewport.surface.blit(self.buffered_map, (0,0))

        
    def _self_handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 3:
            sel = self.game.selected_obj
            if sel is not None and hasattr(sel, "set_order"):
                pressed = pygame.key.get_pressed()
                order = actor.PathToOrder(sel, event.gamepos)
                if pressed[K_LSHIFT] or pressed[K_RSHIFT]:
                    sel.queue_order( order)
                else:
                    sel.set_order( order)                 
                
                return EVENT_HANDLED
        return BaseWidget._self_handle_event(self, event)
            
            
class TestWidget(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._opaque_update

    def __init__(self, manager, rect, layer=LAYER_IFACE_UPPER):    
        BaseWidget.__init__(self, manager, rect, layer)     
    
    def _draw_self(self, viewport, rect):
        if self._mouseover:
            color = (255,255,100)
        elif self.selected:
            color = (255,255,255)
        else:
            color = (150,150,150)

        pygame.draw.rect( viewport.surface, (0,0,0), rect)
        pygame.draw.rect( viewport.surface, color, rect.inflate((-2,-2)))

        
class Panel(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._transparent_update

    def __init__(self, manager, rect, layer=LAYER_IFACE_UPPER):    
        BaseWidget.__init__(self, manager, rect, layer)
    
    def _draw_self(self, viewport, rect):
        if self._mouseover:
            framecolor = (255,255,255)
        else:
            framecolor = (0,0,0)
        pygame.draw.rect( viewport.surface, framecolor, rect)
        pygame.draw.rect( viewport.surface, (155,155,155), rect.inflate(-4,-4))
        
        
class DragBar(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._opaque_update

    def __init__(self, manager, rect):
        BaseWidget.__init__(self, manager, rect)
        self._dragging = False
        self._selectable = False
    
    def _draw_self(self, viewport, rect):
        pygame.draw.rect( viewport.surface, (100,100,200), rect)
        
    def _self_handle_event(self, event):
        if self._mouseover and event.type == MOUSEBUTTONDOWN and event.button == 1:
            self._dragging = True
            self.manager.add_mousemotion_listener( self)
            return EVENT_HANDLED
        elif self._mouseover and event.type == MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
            self.manager.remove_mousemotion_listener( self)
            return EVENT_HANDLED
        elif event.type == MOUSEMOTION:
            if self._parent is not None:
                self._parent.move( event.abs_motion)
                return EVENT_HANDLED
        return BaseWidget._self_handle_event(self, event)
        
                
class DragPanel(Panel):

    def __init__(self, manager, rect, layer=LAYER_IFACE_UPPER):
        Panel.__init__(self, manager, rect, layer)
        dragrect = pygame.Rect(rect).inflate( (-4,0))
        dragrect.topleft = (2,2)
        dragrect.h = 20
        self.add_child( DragBar(manager, dragrect))
        
        
class IconWidget(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._opaque_update

    def __init__(self, manager, icon, center, layer=LAYER_IFACE):
        self.icon = icon
        rect = self.icon.get_rect()
        rect.center = center
        BaseWidget.__init__(self, manager, rect, layer)
        self._selectable = False
        
    def _draw_self(self, viewport, rect):
        viewport.surface.blit(self.icon, rect)
        
        
class TextLabel(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._transparent_update

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
        
    def _draw_self(self, viewport, rect):
        if self._textgen.text_changed():
            self._regenerate()
        viewport.surface.blit( self._img, rect)

        
class TextButton(TextLabel):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._opaque_update

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

    def _draw_self(self, viewport, rect):
        self._img = self._altimg if self._mouseover else self._mainimg
        TextLabel._draw_self(self, viewport, rect)
        
        
class RadialContextMenu(BaseWidget):
    """Base class for generic context menus, with options deployed 
    in a circular model."""
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._transparent_update
    
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
        
    def _draw_self(self, viewport, rect):
        point = rect.center
        if self._mouseover:
            color = (255,255,0)
        else:
            color = (255,255,255)
        if self._radius > 1:
            pygame.draw.circle( viewport.surface, color, point,
                                int(self._radius*viewport.scale), 3)
        
    def translate_point(self, pos):
        return vector.Vec2d(pos) + self._space_rect.center
        
    def translate_rect(self, rect):
        return rect.move( self._space_rect.center)
 
 
class TextContextMenu(BaseWidget):
    """Base class for generic context menus, with options deployed 
    in a circular model."""
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._absolute_get_disp_rect
    _update_handler = BaseWidget._transparent_update

    def __init__(self, manager, origin, objects):
        """Initializer. 
        
        Args:
            manager: InterfaceManager object
            origin: The upper left corner of the menu
            objects: A list of dictionaries containing information about the 
                menu options.
        """
        font = manager.fonts["smallfont"]
        itemheight = font.get_height()+3
            
        #pre build all the menu items, keep a running max width
        items = []
        width = 0
        for i in range( len(objects)):
            tb = TextContextItem(manager, (3,3+i*itemheight), "smallfont", 
                                StaticText( objects[i]["text"]), objects[i]["action"])
            width = max(width, tb._base_rect.width)
            items.append( tb)
            
        #build the base rectangle and then run the base widget initializer
        rect = pygame.Rect(0,0,width+6, itemheight*len(objects)+6)
        rect.topleft = origin
        BaseWidget.__init__(self, manager, rect, LAYER_IFACE)
        
        for i in items:
            self.add_child( i)
        
    def _draw_self(self, viewport, rect):
        pygame.draw.rect(viewport.surface, (150,150,150), rect)

        
class TextContextItem(TextButton):
    get_disp_rect = BaseWidget._absolute_get_disp_rect

    
class GameObjWidget(BaseWidget):
    #update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    _update_handler = BaseWidget._opaque_update
    
    def __init__(self, manager, obj_or_rect, rect=None, layer=LAYER_GAME_FG):
        if isinstance(obj_or_rect, game.GameObject):
            if rect is None:
                rect = obj_or_rect.rect
            else:
                rect.center = obj_or_rect.rect.center
            self._game_object = obj_or_rect
            self._selectable = obj_or_rect.selectable            
        else:
            self._game_object = None
            self._selectable = False
            rect = obj_or_rect            
        BaseWidget.__init__(self,manager,rect,layer)


    def update(self, viewport, mousepos):
        BaseWidget.update(self, viewport, mousepos)
        if self._game_object is not None:
            self.finished = self._game_object.finished

    def update_rect(self):
        if self._game_object is not None:
            self._space_rect.center = self.game_object.rect.center
        self._children_update_rect()
        
    def _update_handler(self, viewport, mousepos):
        if self._game_object is not None:
            if self._base_rect.midbottom != self._game_object.rect.midbottom:
                self._base_rect.midbottom = self._game_object.rect.midbottom
                self.update_rect()
        BaseWidget._opaque_update(self, viewport, mousepos)
        
    def _draw_self(self, viewport, rect):
        if self._mouseover:
            color = (255,255,0)
        elif self.selected:
            color = (255,255,255)
        else:
            color = (100,100,100)
        pygame.draw.rect(viewport.surface, color, rect, 2)
        
    def select(self):
        if self._selectable:
            BaseWidget.select(self)
            if self._game_object is not None:
                self._game_object.select()
        
    def deselect(self):
        BaseWidget.deselect(self)
        if self._game_object is not None: 
            self._game_object.deselect()
        
    def get_game_object(self):
        return self._game_object
        
    def _self_handle_event(self, event):
        if self._mouseover and event.type == MOUSEBUTTONDOWN and event.button == 3 and self._game_object is not None:
            game = self.manager.controller.game
            if game.selected_obj is not None and game.selected_obj != self.game_object:
                builder = OrderMenuBuilder(self.game_object, game.selected_obj)
                return builder.make_menu(event, self.manager)
        return BaseWidget._self_handle_event(self, event)
        
    game_object = property( get_game_object)
 
 
class OrderMenuBuilder(object):
    def __init__(self, target, selected):
        self.builder = actor.OrderBuilder(selected, target)
        self.options = self.builder.get_options()

    def make_menu(self, event, interface):
        if len(self.options) == 0:
            return False

        if len(self.options) >= 1:
            items = []
            for o in self.options:
                action = OrderBuilderAction(self.builder, o)
                item = {"text": o, "action": action}
                items.append( item)
            cm = TextContextMenu(interface, event.pos, items)
            interface.set_context_menu(cm)
            return EVENT_HANDLED | EVENT_PRESERVE_CONTEXT
        elif len(self.options) == 1:
            option = self.options.pop()
            self.builder.do_order(option)
            return EVENT_HANDLED
        else:
            return EVENT_UNHANDLED
            

        
class OrderBuilderAction(InterfaceAction):
    def __init__(self, builder, ordertag):
        self.tag = ordertag
        self.builder = builder
        
    def do_action(self, source_widget, interface, game):
        self.builder.do_order( self.tag)
        return True

        
class SpriteWidget(GameObjWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect

    def __init__(self, manager, obj_or_rect, img):
        self.img = img
        if self.img is not None:
            rect = self.img.get_rect()
        else:
            rect = None
    
        GameObjWidget.__init__(self, manager, obj_or_rect, rect, LAYER_GAME_FG)
        
    def _draw_self(self, viewport, disp_rect):
        if self.img is not None:
            img = viewport.transform.scale(self.img, viewport.scale)
            viewport.surface.blit(img, disp_rect)
        
        if self._mouseover:
            pygame.draw.rect(viewport.surface, (255,255,0), disp_rect, 1)
        elif self.selected:
            pygame.draw.rect(viewport.surface, (255,255,255), disp_rect, 1)
            
            
class InvisWidget(BaseWidget):
    update_rect = BaseWidget._relative_update_rect
    handle_event = BaseWidget._standard_event_handler
    get_disp_rect = BaseWidget._relative_get_disp_rect
    _update_handler = BaseWidget._opaque_update
    
    def _draw_self(self, viewport, rect):
        pygame.draw.rect( viewport.surface, (255,255,255), rect, 4)


class WorkspaceWidget(GameObjWidget):
    def __init__(self, manager, obj, rect=None, layer=LAYER_GAME_FG):
        GameObjWidget.__init__(self, manager, obj, rect, layer)
        self.img = manager.controller.assets.get("workspace")

    def _draw_self(self, viewport, disp_rect):
        img = viewport.transform.scale(self.img, viewport.scale)
        #viewport.surface.blit(img, disp_rect)
        
        color = (255,255,255) if self.game_object.reserved else (100,100,100)
        pygame.draw.ellipse(viewport.surface, color, disp_rect, 1)


class BuildingPlacerWidget(GameObjWidget):
    def __init__(self, mgr, obj, rect):
        GameObjWidget.__init__(self, mgr, obj, rect)
        self.valid_pos = False
    
    def update(self, viewport, mousepos):
        GameObjWidget.update(self, viewport, mousepos)
        topleft = self._space_rect.topleft
        botright = self._space_rect.bottomright
        self.valid_pos = self.game_object.game.map.game_area_clear(topleft, botright)
    
    def _draw_self(self, viewport, disp_rect):
        color = (0,255,0) if self.valid_pos else (255,0,0)
        pygame.draw.rect(viewport.surface, color, disp_rect, 2)
        
    def _self_handle_event(self, event):
        if self._mouseover and event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.valid_pos:
                    self.game_object.place_structure()
                return EVENT_HANDLED
            elif event.button == 3:
                self.game_object.finished = True
                return EVENT_HANDLED

        return GameObjWidget._self_handle_event(self, event)

        
class StructWidget(SpriteWidget):

    def __init__(self, manager, obj, img):
        SpriteWidget.__init__(self, manager, obj, img)
        self._selectable = True

        for w in obj.workspaces:
            c = vector.Vec2d(w.rect.center) - obj.rect.center
            newrect = w.rect.copy()
            newrect.center = c
            
            gw = WorkspaceWidget(manager, w, newrect, LAYER_GAME_FG)
            self.add_child( gw)
        
    def get_selection_menu(self):
        panel = Panel(self.manager, (0,0,200,600))
        headline = CompositeTextGenerator( (StaticText("Available: "), LambdaTextGenerator(lambda: self._game_object.get_available_space(None))))
        text = TextLabel(self.manager, (30, 30), 'medfont', headline)
        panel.add_child( text)
        offset = 1
        
        store = self._game_object.res_storage
        if store is not None:
            for key in store._accepts:
                text = TextLabel(self.manager, (30, 30+offset*30), 'medfont', CompositeTextGenerator([StaticText(key+': '), LambdaTextGenerator(lambda bound_key=key: "%.1f"%store.get_actual_contents(bound_key))]))
                panel.add_child( text)
                offset += 1
                
        return panel

class ResourcePileWidget( SpriteWidget):
    def _draw_self(self, viewport, disp_rect):
        SpriteWidget._draw_self(self, viewport, disp_rect)
        bar_rect = disp_rect.copy()
        bar_rect.h = 4*viewport.scale
        bar_rect.bottom = disp_rect.bottom
        rstore = self._game_object.res_storage
        ratio = (rstore.get_actual_contents(None)/rstore.get_capacity())
        ratio = 1.0-self._game_object.decay_timer
        bar_rect.w = int(bar_rect.w * ratio)
        bar_rect.w = max(1, bar_rect.w)
        pygame.draw.rect(viewport.surface, (255,0,0), bar_rect, 0)

    def get_selection_menu(self):
        panel = Panel(self.manager, (0,0,200,600))
        headline = CompositeTextGenerator( (StaticText("Available: "), LambdaTextGenerator(lambda: self._game_object.get_available_space(None))))
        text = TextLabel(self.manager, (30, 30), 'medfont', headline)
        panel.add_child( text)
        
        store = self._game_object.res_storage
        if store is not None:
            offset = 1
            for key in store._accepts:
                text = TextLabel(self.manager, (30, 30+offset*30), 'medfont', CompositeTextGenerator([StaticText(key), LambdaTextGenerator(lambda bound_key=key: "%.3f"%store.get_actual_contents(bound_key))]))
                panel.add_child( text)
                offset += 1

        return panel

class ActorWidget(SpriteWidget):
    
    def __init__(self, manager, obj, img):
        carry_rect = pygame.Rect(8,40,30,30)
        self.carry_widget = SpriteWidget(manager, carry_rect, None)
        self.carry_widget._selectable = False
        
        SpriteWidget.__init__(self, manager, obj, img)
        self.add_child(self.carry_widget)        
    
    def _draw_self(self, viewport, disp_rect):
        load = self._game_object.carrying
        if load is not None:
            color = (load['qty']*200, 0, 0)
            #pygame.draw.rect( viewport.surface, color, disp_rect, 0)
            img = self._game_object.game.resource_types.find(load['type']).sprite
            self.carry_widget.img = img            
        else:
            self.carry_widget.img = None
        SpriteWidget._draw_self(self, viewport, disp_rect)

    def get_selection_menu(self):
        panel = Panel(self.manager, (0,50,200,600))
        statusgen = CompositeTextGenerator( (StaticText("O: "), LambdaTextGenerator(lambda: str(self.game_object.get_order_status()))))
        statustext = TextLabel(self.manager, (10, 30), 'smallfont', statusgen)
        headline = CompositeTextGenerator( (StaticText("Carrying: "), LambdaTextGenerator(lambda: str(self.game_object.carrying))))
        text = TextLabel(self.manager, (10, 60), 'medfont', headline)        
        panel.add_child( text)
        panel.add_child( statustext)

        return panel


class HerdMemberWidget(SpriteWidget):
    def __init__(self, manager, gameobj, sprite1, sprite2):
        SpriteWidget.__init__(self, manager, gameobj, sprite1)
        self.altsprite = sprite2

    def _draw_self(self, viewport, disp_rect):
        if self.game_object._render_state['adult']:
            SpriteWidget._draw_self(self, viewport, disp_rect)
        else:
            img = viewport.transform.scale(self.altsprite, viewport.scale)
            viewport.surface.blit(img, disp_rect)
    
    def get_selection_menu(self):
        panel = Panel(self.manager, (0,0,200,600))
        headline = CompositeTextGenerator( (StaticText("Valid: "), LambdaTextGenerator(lambda: self._game_object.finished)))
        text = TextLabel(self.manager, (30, 30), 'medfont', headline)
        panel.add_child( text)

        return panel
    

class HerdWidget(SpriteWidget):
    def __init__(self, manager, gameobj, sprite):
        SpriteWidget.__init__(self, manager, gameobj, sprite)
            
    def get_selection_menu(self):
        panel = Panel(self.manager, (0,0,200,600))
        headline = CompositeTextGenerator( (StaticText("Meat: "), LambdaTextGenerator(lambda: self._game_object.get_meat())))
        text = TextLabel(self.manager, (30, 30), 'medfont', headline)
        panel.add_child( text)

        return panel
            