#global lib impports
import pygame
from pygame.locals import *
import math
import sys

#local imports
import application
import transform
import viewport
import resourcemanager
import game
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

class TestInterfaceObj1(interface.InterfaceObject):
    
    def __init__(self, manager, renderer, obj=None):
        if obj is not None:
            interface.InterfaceObject.__init__(self, manager, renderer, obj)
        else:
            interface.InterfaceObject.__init__(self, manager, renderer, (0,0,100,100))
    
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

class TestContextAction(interface.InterfaceAction):
    def __init__(self, message):
        self.message = message
        interface.InterfaceAction.__init__(self)
        
    def do_action(self, interface, game):
        print "interface action: "+self.message

class TestGameObject(game.GameObject):
    def update(self):
        game.GameObject.update(self)
        self.rect.move_ip( (1,1))

    def selectable(self):
        return True
        
    def select(self):
        game.GameObject.select(self)
        print "Game object selected"
        
    def deselect(self):
        game.GameObject.deselect(self)
        print "Game object deselected"
        
class TestActivity1( application.Activity):
    """Test activity for debugging."""
    
    def on_create(self, config):
        application.Activity.on_create(self, config)
        self.controller.set_fps_cap( 20)
        self.vp = viewport.Viewport( self.controller.screen)
        self.vp.transform.set_rotation_interval( 5)
        self.counter = 1
        self.star_img = pygame.image.load( "res/test.bmp")
        self.font = pygame.font.Font(None, 24)
        self.iface = interface.InterfaceManager(self)
        self.game = game.Game()
        
        #transform test variables
        self.angle = 0
        self.xflip = False
        self.yflip = False
        self.sz = 3
        
        self.resources = resourcemanager.ResourceManager()
        self.resources.load_set("res/resources.txt")
        
        self.icons = []
        for i in xrange(8):
            tag = "ico" + str(i)
            self.icons.append(pygame.transform.smoothscale( self.resources.get(tag), (40,40)))

        gobj = TestGameObject(self.game)
        self.game.add_game_object( gobj)
            
        renderer = TestRenderer()
        obj1 = TestInterfaceObj1(self.iface, renderer, gobj)
        obj1.rect.center = (100, 100)
        obj2 = TestInterfaceObj1(self.iface, renderer)
        obj2.rect.center = (150, 150)
        obj2.layer = 1
        
        self.iface.add_child( obj1)
        self.iface.add_child( obj2)

    def update(self):
        application.Activity.update(self)
        self.iface.update( self.vp)
        self.game.update()        
        self.counter += 1
        
        pressed = pygame.key.get_pressed()
        if pressed[K_LEFTBRACKET]:
            self.angle += 1
        elif pressed[K_RIGHTBRACKET]:
            self.angle -= 1
            
        if pressed[K_d]:
            self.vp.pan( (2,0))
        elif pressed[K_a]:
            self.vp.pan( (-2,0))
        elif pressed[K_s]:
            self.vp.pan( (0,2))
        elif pressed[K_w]:
            self.vp.pan( (0,-2))  
        
    def draw(self):
        application.Activity.draw(self)
        
        pos = pygame.mouse.get_pos()
        pygame.draw.circle( self.vp.surface, (255,255,255), pos, 
                            int(25*self.vp.scale), 1)

        self.iface.draw( self.vp)

    def handle_event(self, event):
        if self.iface.handle_event( event):
            print "handled"
            return
    
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.vp.zoom_in()
            elif event.button == 5:
                self.vp.zoom_out()
            elif event.button == 3:
            
                '''if self.iface._selected_obj is not None and self.iface._selected_obj.game_object is not None:
                    if self.iface._selected_obj.accepts_orders:
                        print "wat"'''
            
                
                options = []
                for x in range(self.sz):
                    options.append({ "icon": self.icons[x],
                                     "action": TestContextAction("clicky "+str(x))})
                                     
                cmenu = interface.ContextMenu(self.iface, event.pos, options)            
                self.iface.set_context_menu(cmenu)
            elif event.button == 1:
                self.iface.cancel_context_menu()
                
        if event.type == pygame.KEYDOWN:
            if event.key == K_COMMA:
                self.sz -= 1
                print self.sz
            elif event.key == K_PERIOD:
                self.sz += 1
                print self.sz
        
def run():

    app = CivilisApp()
    app.start_activity( TestActivity1, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()