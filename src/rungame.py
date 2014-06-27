#global lib impports
import pygame
from pygame.locals import *

#local imports
import application
import transform
import viewport
import resourcemanager
import gameobject

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
        self._children.sort( key=lambda obj: obj.layer)
        
    def add_object(self, iobj):
        self._children[-1] = iobj
        
    def draw(self, viewport):
        for c in self._children:
            c.draw( viewport)
        
    def _find_mouseovers(self):
        retval = []
        for c in self._children:
            if c.mouse_is_over():
                retval[-1] = c

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
                    if m.is_selected() and m != self._selected_obj:
                        if self._selected_obj is not None:
                            self._selected_obj.deselect()
                        self._selected_obj = m

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
        
        #transform test variables
        self.angle = 0
        self.xflip = False
        self.yflip = False
        
        self.resources = resourcemanager.ResourceManager()
        self.resources.load_set("res/resources.txt")
        star = self.resources.get("star")
        

    def update(self):
        application.Activity.update(self)
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
                            int(10*self.vp.scale), 1)
        
        pressed = pygame.key.get_pressed()
        if pressed[K_d]:
            self.vp.pan( (2,0))
        elif pressed[K_a]:
            self.vp.pan( (-2,0))
        elif pressed[K_s]:
            self.vp.pan( (0,2))
        elif pressed[K_w]:
            self.vp.pan( (0,-2))
        
        text = "Scale: %2.2f, Angle %3.1f, Flip %d %d" % (self.vp.get_scale(), self.angle, self.xflip, self.yflip)
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
        #rect.center = self.vp.translate( rect.center)
        self.vp.surface.blit( star, self.vp.translate_rect(rect))


    def handle_event(self, event):
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