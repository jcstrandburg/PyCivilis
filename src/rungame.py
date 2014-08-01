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
import actor

class CivilisApp( application.Application):
    """Game specific Application class."""
    def __init__(self):
        application.Application.__init__(self)
        self._object_id = 0

    def make_object_id(self):
        self._object_id += 1
        return self._object_id-1

class TestContextAction2(interface.InterfaceAction):
    def __init__(self):
        interface.InterfaceAction.__init__(self)
        
    def do_action(self, interface, game):
        sobj = interface.selected_obj
        if sobj is not None and sobj.game_object is not None:
            sobj.game_object.rect.move_ip((-100,-100))
        
"""        
class TestRenderer(interface.BaseRenderer):
    def __init__(self):
        size = (50,50)
    
        self.img1 = pygame.Surface( size)
        self.img1.fill( (255,255,100))
        pygame.draw.rect(self.img1, (0,0,0), self.img1.get_rect(), 1)
        pygame.draw.circle(self.img1, (50,50,50), self.img1.get_rect().center, 10)
        
        self.img2 = pygame.Surface( size)
        self.img2.fill( (255,255,255))
        pygame.draw.rect(self.img2, (0,0,0), self.img2.get_rect(), 1)
        pygame.draw.circle(self.img2, (50,50,50), self.img2.get_rect().center, 10)
        
        self.img3 = pygame.Surface( size)
        self.img3.fill( (155,155,155))
        pygame.draw.rect(self.img3, (0,0,0), self.img3.get_rect(), 1)
        pygame.draw.circle(self.img3, (50,50,50), self.img3.get_rect().center, 10)
        
        interface.BaseRenderer.__init__(self)
        
    def generate_image(self, object):
        if object.selected:
            return self.img1
        elif object.mouse_is_over():
            return self.img2
        else:
            return self.img3"""
            
class IncrementText(interface.TextGenerator):
    def __init__(self, x):
        self.x = x

    def text_changed(self):
        self.x += 1
        return True
        
    def get_text(self):
        return str(self.x)
        
class TestContextAction(interface.InterfaceAction):
    def __init__(self, message):
        self.message = message
        interface.InterfaceAction.__init__(self)
        
    def do_action(self, src_widget, interface, game):
        print "interface action: "+self.message
        return True
        
class TestObject(game.GameObject):
    def update(self):
        self.position += (1,0)

class MapMoveAction(interface.InterfaceAction):
    def __init__(self, coords):
        self._coords = coords
        
    def do_action(self, src_widget, interface, game):
        obj = interface.selected_obj
        if hasattr(obj, "game_object"):
            obj.game_object.set_order(actor.MoveOrder(obj.game_object, game, self._coords))
        
'''class TestMapWidget(interface.Widget):
    def __init__(self, manager):
        interface.Widget.__init__(self, manager, (0,0,800,600), interface.LAYER_BASE, interface.VIEW_FIXED)
        self._selectable = False

    def draw(self, viewport):
        pygame.draw.rect(viewport.surface, (150,50,150), self.get_disp_rect(viewport))
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 3:
            self.manager.do_action(self, MapMoveAction(event.gamepos))
            return True'''
        
class WidgetActivity( application.Activity):
    """Test activity for debugging."""
    
    def on_create(self, config):
        application.Activity.on_create(self, config)
        self.controller.set_fps_cap( 50)
        self.vp = viewport.Viewport( self.controller.screen)
        self.vp.transform.set_rotation_interval( 5)
        
        self.font = pygame.font.Font(None, 24)
        self.iface = interface.InterfaceManager(self)
        self.game = game.Game()
        self.ticker = 1
        self.options = 5

        self.resources = resourcemanager.ResourceManager()
        self.resources.load_set("res/resources.txt")
        
        self.icons = []
        for i in xrange(8):
            tag = "ico" + str(i)
            self.icons.append(pygame.transform.smoothscale( self.resources.get(tag), (40,40)))

        self.container2 = interface.DragPanel( self.iface, 
                            (400,10,375,200))
        self.testa = interface.TestWidget( self.iface, (25,50,100,30))
        self.testb = interface.TestWidget( self.iface, (25,100,100,30))
        self.testc = interface.TestWidget( self.iface, (25,150,100,30))
        
        text = interface.StaticText("Lorem ipsum delores")
        basetext = interface.StaticText("Options: ")
        optionstext = interface.LambdaTextGenerator( lambda: self.options)
        inctext = IncrementText(0)
        comptext = interface.CompositeTextGenerator((basetext, inctext))
        
        self.text1 = interface.TextLabel( self.iface, (135,50), "medfont", comptext)
        self.text2 = interface.TextButton( self.iface, (135,100), "medfont", text, TestContextAction("Clicky"))
        self.text3 = interface.TextLabel( self.iface, (135,150), "bigfont", text)
        
        self.container2.add_child( self.testa)
        self.container2.add_child( self.testb)
        self.container2.add_child( self.testc)
        self.container2.add_child( self.text1)
        self.container2.add_child( self.text2)
        self.container2.add_child( self.text3)
        
        self.iface.add_child( self.container2)
        
        testobj = actor.Actor(self.game, (-100, 0))
        testobj.target_orders = testobj.target_orders.union(['a','b','c'])        
        testobj.ability_orders = testobj.ability_orders.union(['c','d'])
        self.game.add_game_object(testobj)        
        testwidg = interface.GameObjWidget( self.iface, testobj)
        self.iface.add_child( testwidg)

        testobj = actor.Actor(self.game, (100, 0))
        testobj.target_orders = testobj.target_orders.union(['a','b','d'])
        testobj.ability_orders = testobj.ability_orders.union(['a','b','d'])
        self.game.add_game_object(testobj)        
        testwidg = interface.GameObjWidget( self.iface, testobj)
        self.iface.add_child( testwidg)        

        testobj = actor.Actor(self.game, (-100, 200))
        testobj.target_orders = testobj.target_orders.union(['a','c','d'])
        testobj.ability_orders = testobj.ability_orders.union(['b','d'])
        self.game.add_game_object(testobj)        
        testwidg = interface.GameObjWidget( self.iface, testobj)
        self.iface.add_child( testwidg)   
        
        testobj = actor.Actor(self.game, (100, 200))
        testobj.target_orders = testobj.target_orders.union(['c','d'])
        testobj.ability_orders = testobj.ability_orders.union(['a','b','d'])
        self.game.add_game_object(testobj)        
        testwidg = interface.GameObjWidget( self.iface, testobj)
        self.iface.add_child( testwidg)           
        

    def update(self):
        self.ticker += 1
    
        application.Activity.update(self)
        self.iface.update( self.vp)
        self.game.update()        
        
        pos = (0, 150+75*math.sin(self.ticker/40.0))
        #self.container.move_to( pos)
        
        pressed = pygame.key.get_pressed()
            
        if pressed[K_d]:
            self.vp.pan( (2,0))
        elif pressed[K_a]:
            self.vp.pan( (-2,0))
        if pressed[K_s]:
            self.vp.pan( (0,2))
        elif pressed[K_w]:
            self.vp.pan( (0,-2))
            
    def draw(self):
        application.Activity.draw(self)
        
        pos = pygame.mouse.get_pos()
        pygame.draw.circle( self.vp.surface, (255,255,255), pos, 
                            int(15*self.vp.scale), int(self.vp.scale*4))

        self.iface.draw( self.vp)

    def handle_event(self, event):
        if hasattr( event, 'pos'):
            event.gamepos = self.vp.translate_point(event.pos, 
                                                    viewport.SCREEN_TO_GAME)
                                                    
        if hasattr( event, 'rel'):
            event.rel_motion = (round(event.rel[0]/self.vp.scale),
                                round(event.rel[1]/self.vp.scale))
            event.abs_motion = event.rel
                                                    
        if self.iface.handle_event( event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.vp.zoom_in()
            elif event.button == 5:
                self.vp.zoom_out()
            elif event.button == 3:
                so = self.game.selected_obj
                if so is not None and hasattr(so, "set_order"):
                    so.set_order( actor.MoveOrder(so,self.game,event.gamepos))
                else:
                    options = []
                    for x in range(self.options):
                        options.append({ "icon": self.icons[x],
                                         "text": "Option "+str(x),
                                         "action": TestContextAction("Action: "+str(x))})

                    #cm = interface.RadialContextMenu(self.iface, event.pos, options)
                    cm = interface.TextContextMenu(self.iface, event.pos, options)
                    self.iface.set_context_menu(cm)                
                
        if event.type == pygame.KEYDOWN:
            if event.key == K_COMMA:
                self.options = max(self.options-1, 1)
            elif event.key == K_PERIOD:
                self.options = min(self.options+1, 8)
                
class ViewportActivity( application.Activity):
    """Test activity for debugging."""
    
    def on_create(self, config):
        application.Activity.on_create(self, config)
        self.controller.set_fps_cap( 50)
        self.vp = viewport.Viewport( self.controller.screen)
        self.vp.transform.set_rotation_interval( 5)
        
        self.iface = interface.InterfaceManager(self)
        self.game = game.Game()

        self.resources = resourcemanager.ResourceManager()
        self.resources.load_set("res/resources.txt")

        self.iface.add_child(interface.VPWidget(self.iface, (-40, -40)))
        self.iface.add_child(interface.VPWidget(self.iface, (-40, 0)))
        self.iface.add_child(interface.VPWidget(self.iface, (-40, 40)))
        self.iface.add_child(interface.VPWidget(self.iface, (0, -40)))
        self.iface.add_child(interface.VPWidget(self.iface, (0, 0)))
        self.iface.add_child(interface.VPWidget(self.iface, (0, 40)))
        self.iface.add_child(interface.VPWidget(self.iface, (40, -40)))
        self.iface.add_child(interface.VPWidget(self.iface, (40, 0)))
        self.iface.add_child(interface.VPWidget(self.iface, (40, 40)))
        
    def update(self):
        application.Activity.update(self)
        self.iface.update( self.vp)
        self.game.update()        
        
        pressed = pygame.key.get_pressed()
            
        if pressed[K_d]:
            self.vp.pan( (2,0))
        elif pressed[K_a]:
            self.vp.pan( (-2,0))
        if pressed[K_s]:
            self.vp.pan( (0,2))
        elif pressed[K_w]:
            self.vp.pan( (0,-2))
            
    def draw(self):
        application.Activity.draw(self)
        
        pos = pygame.mouse.get_pos()
        pygame.draw.circle( self.vp.surface, (255,255,255), pos, 
                            int(15*self.vp.scale), int(self.vp.scale*4))

        self.iface.draw( self.vp)

    def handle_event(self, event):
        if hasattr( event, 'pos'):
            event.gamepos = self.vp.translate_point(event.pos, 
                                                    viewport.SCREEN_TO_GAME)
                                                    
        if hasattr( event, 'rel'):
            event.rel_motion = (round(event.rel[0]/self.vp.scale),
                                round(event.rel[1]/self.vp.scale))
            event.abs_motion = event.rel
                                                    
        if self.iface.handle_event( event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.vp.zoom_in()
            elif event.button == 5:
                self.vp.zoom_out()
            elif event.button == 3:
                self.icon.center_on( event.gamepos)
                
        if event.type == pygame.KEYDOWN:
            if event.key == K_COMMA:
                self.options = max(self.options-1, 1)
            elif event.key == K_PERIOD:
                self.options = min(self.options+1, 8)            
        
def run():

    app = CivilisApp()
    app.start_activity( WidgetActivity, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()