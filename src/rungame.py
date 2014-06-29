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
import vector
import interface

class CivilisApp( application.Application):
    """Game specific Application class."""

    def __init__(self):
        application.Application.__init__(self)
        self._object_id = 0

    def make_object_id(self):
        self._object_id += 1
        return self._object_id-1

class TestObj1(interface.InterfaceObject):
    
    def __init__(self, renderer):
        interface.InterfaceObject.__init__(self, renderer, (0,0,100,100))
    
    def update(self, viewport, mousepos):
        interface.InterfaceObject.update(self, viewport, mousepos)
        
class TestRenderer(interface.BaseRenderer):
    def __init__(self):
        self.img1 = pygame.Surface( (100,100))
        self.img1.fill( (255,255,100))
        self.img2 = pygame.Surface( (100,100))
        self.img2.fill( (255,255,255))
        self.img3 = pygame.Surface( (100,100))
        self.img3.fill( (155,155,155))       
        
        interface.BaseRenderer.__init__(self)
        
    def generate_image(self, object):
        if object.selected:
            return self.img1
        elif object.mouse_is_over():
            return self.img2
        else:
            return self.img3
        
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
        self.iface = interface.InterfaceManager()
        
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
        obj3 = interface.ContextMenu( None, (450,350), self.icons[:6])
        
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
        
        """for i in range( len(self.icons)):
            self.vp.surface.blit( self.icons[i], (300, 30+50*i, 40, 40))"""


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