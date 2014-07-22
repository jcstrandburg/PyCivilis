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
        
class TestMapWidget(interface.Widget):
    def __init__(self, manager):
        interface.Widget.__init__(self, manager, (0,0,800,600), interface.LAYER_BASE, interface.VIEW_FIXED)
        self._selectable = False

    def draw(self, viewport):
        pygame.draw.rect(viewport.surface, (150,50,150), self.get_disp_rect(viewport))
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 3:
            self.manager.do_action(self, MapMoveAction(event.gamepos))
            return True
        
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

        #self.iface.add_child( TestMapWidget(self.iface))
            
        self.container = interface.Panel( self.iface, (0,0,300,200))
            
        self.test1 = interface.TestWidget( self.iface, (50,50,100,30))
        self.test2 = interface.TestWidget( self.iface, (50,100,100,30))
        self.test3 = interface.TestWidget( self.iface, (50,150,100,30))
            
        self.container.add_child( self.test1)
        self.container.add_child( self.test2)
        self.container.add_child( self.test3)
        
        self.iface.add_child( self.container)        

        self.container2 = interface.DraggablePanel( self.iface, 
                            (350,100,375,200), view_style=interface.VIEW_FIXED)
        
        self.testa = interface.TestWidget( self.iface, (25,50,100,30))
        self.testb = interface.TestWidget( self.iface, (25,100,100,30))
        self.testc = interface.TestWidget( self.iface, (25,150,100,30))
        
        text = interface.StaticText("Lorem ipsum delores")
        basetext = interface.StaticText("Options: ")
        optionstext = interface.LambdaTextGenerator( lambda: self.options)
        comptext = interface.CompositeTextGenerator((basetext, optionstext))
        
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
        
        icon = interface.IconWidget(self.iface, self.icons[0], (400,500))
        #self.iface.add_child( icon)
        
        testobj = actor.Actor(self.game, (100,400))
        self.game.add_game_object(testobj)
        
        testwidg = interface.GameObjWidget( self.iface, testobj)
        self.iface.add_child( testwidg)       


    def update(self):
        self.ticker += 1
    
        application.Activity.update(self)
        self.iface.update( self.vp)
        self.game.update()        
        
        pos = (0, 150+75*math.sin(self.ticker/40.0))
        self.container.move_to( pos)
        
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
                            int(15*self.vp.scale), 4)

        self.iface.draw( self.vp)

    def handle_event(self, event):
        if hasattr( event, 'pos'):
            event.gamepos = self.vp.translate_point(event.pos, 
                                                    viewport.SCREEN_TO_GAME)
        if self.iface.handle_event( event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.vp.zoom_in()
            elif event.button == 5:
                self.vp.zoom_out()
            elif event.button == 3:
                '''options = []
                for x in range(self.options):
                    options.append({ "icon": self.icons[x],
                                     "action": TestContextAction("Action: "+str(x))})

                cm = interface.RadialContextMenu(self.iface, (450,450), options)
                self.iface.set_context_menu(cm)'''
                
                options = []
                for x in range(self.options):
                    options.append({ "text": "Option "+str(x),
                                     "action": TestContextAction("Action: "+str(x))})

                cm = interface.TextContextMenu(self.iface, (400,400), options)
                self.iface.set_context_menu(cm)
                
        if event.type == pygame.KEYDOWN:
            if event.key == K_COMMA:
                self.options = max(self.options-1, 1)
            elif event.key == K_PERIOD:
                self.options = min(self.options+1, 8)                
        
def run():

    print "k"
    app = CivilisApp()
    print "y"
    app.start_activity( WidgetActivity, None)
    
    print "wat"
    while app.update():
        app.draw()
        
    print "huh"
    app.cleanup()