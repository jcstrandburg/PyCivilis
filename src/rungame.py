#global lib impports
import pygame
from pygame.locals import *
import math

#local imports
import application
import transform
import viewport
import resourcemanager
import gameobject
import interfaceobject
import renderer
import vector

class CivilisApp( application.Application):
    """Game specific Application class."""

    def __init__(self):
        application.Application.__init__(self)
        self._object_id = 0

    def make_object_id(self):
        self._object_id += 1
        return self._object_id-1

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

class TestObj1(interfaceobject.InterfaceObject):
    
    def __init__(self, renderer):
        interfaceobject.InterfaceObject.__init__(self, renderer, (0,0,100,100))
    
    def update(self, viewport, mousepos):
        interfaceobject.InterfaceObject.update(self, viewport, mousepos)

class ContextMenu(interfaceobject.InterfaceObject):
    def __init__(self, renderer, center, icons):
        interfaceobject.InterfaceObject.__init__(self, renderer, (0,0,10,10))
        self.center = vector.Vec2d(center)
        self.items = []
        
        for i in range( len(icons)):
            angle = (2*i*math.pi)/len(icons)
            dist = math.sqrt( len(icons)-1)*20
            pos = self.center + (math.sin(angle)*dist, -math.cos(angle)*dist)
            item = ContextMenuItem(None, pos, icons[i])
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
        pygame.draw.circle( viewport.surface, (255,255,255), self.center.int_tuple, 30)
        for item in self.items:
            item.draw(viewport)
        

class ContextMenuItem(interfaceobject.InterfaceObject):
    def __init__(self, renderer, pos, icon):
        interfaceobject.InterfaceObject.__init__(self, renderer, (0,0,40,40))
        self.rect.center = pos
        self.icon = icon
        
    def draw(self, viewport):
        viewport.surface.blit(self.icon, self.disp_rect)
        
    def select(self):
        interfaceobject.InterfaceObject.select(self)
        print("wat")
        
class TestRenderer(renderer.BaseRenderer):
    def __init__(self):
        self.img = pygame.Surface( (100,100))
        renderer.BaseRenderer.__init__(self)
        
    def generate_image(self, object):
        if object.selected:
            self.img.fill( (255,255,100))
        elif object.mouse_is_over():
            self.img.fill( (255,255,255))
        else:
            self.img.fill( (155,155,155))
            
        return self.img
        
class TestActivity1( application.Activity):
    """Test activity for debugging."""
    
    def on_create(self, config):
        application.Activity.on_create(self, config)
        self.controller.set_fps_cap( 100)
        self.vp = viewport.Viewport( self.controller.screen)
        self.vp.transform.set_rotation_interval( 5)
        self.counter = 1
        self.star_img = pygame.image.load( "res/test.bmp")
        self.star = gameobject.GameObject(self.controller)
        self.font = pygame.font.Font(None, 24)
        self.iface = InterfaceManager()
        
        #transform test variables
        self.angle = 0
        self.xflip = False
        self.yflip = False
        
        self.resources = resourcemanager.ResourceManager()
        self.resources.load_set("res/resources.txt")
        
        self.icons = []
        for i in xrange(8):
            tag = "ico" + str(i)
            self.icons.append(pygame.transform.smoothscale( self.resources.get(tag), (40,40)))
        
        renderer = TestRenderer()
        obj1 = TestObj1(renderer)
        obj1.rect.center = (100, 100)
        obj2 = TestObj1(renderer)
        obj2.rect.center = (150, 150)
        obj2.layer = 1
        obj3 = ContextMenu( None, (450,350), self.icons[:6])
        
        self.iface.add_object( obj1)
        self.iface.add_object( obj2)
        self.iface.add_object( obj3)

    def update(self):
        application.Activity.update(self)
        self.iface.update( self.vp)
        self.counter += 1
        
        pressed = pygame.key.get_pressed()
        if pressed[K_LEFTBRACKET]:
            self.angle += 1
        elif pressed[K_RIGHTBRACKET]:
            self.angle -= 1
            
        self.star.position = pygame.mouse.get_pos()
        
    def draw(self):
        application.Activity.draw(self)
        
        pos = pygame.mouse.get_pos()
        pygame.draw.circle( self.vp.surface, (255,255,255), pos, 
                            int(25*self.vp.scale), 1)
        
        pressed = pygame.key.get_pressed()
        if pressed[K_d]:
            self.vp.pan( (2,0))
        elif pressed[K_a]:
            self.vp.pan( (-2,0))
        elif pressed[K_s]:
            self.vp.pan( (0,2))
        elif pressed[K_w]:
            self.vp.pan( (0,-2))        

        #viewport translate and transform tests
        """text = "Scale: %2.2f, Angle %3.1f, Flip %d %d" % (self.vp.get_scale(), self.angle, self.xflip, self.yflip)
        img = self.font.render(text, False, (255,255,255))
        rect = img.get_rect()
        self.vp.surface.blit( img, rect)
        
        t = self.vp.transform
        star = t.smoothscale( self.star_img, 
                (int(self.star_img.get_width()*self.vp.get_scale()), 
                 int(self.star_img.get_height()*self.vp.get_scale())))
        star = t.rotate( star, self.angle)
        star = t.flip( star, self.xflip, self.yflip)

        rect = star.get_rect()
        rect.center = self.star.position
        self.vp.surface.blit( star, self.vp.transform_rect(rect))"""
        
        self.iface.draw( self.vp)
        
        for i in range( len(self.icons)):
            self.vp.surface.blit( self.icons[i], (300, 30+50*i, 40, 40))


    def handle_event(self, event):
        self.iface.handle_event( event)
    
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.vp.zoom_in()
            elif event.button == 5:
                self.vp.zoom_out()
                
        if event.type == pygame.KEYDOWN:
            if event.key == K_COMMA:
                self.xflip = not self.xflip
            elif event.key == K_PERIOD:
                self.yflip = not self.yflip
        
def run():

    app = CivilisApp()
    app.start_activity( TestActivity1, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()