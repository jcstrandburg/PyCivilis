#global lib impports
import pygame
from pygame.locals import *

#local imports
import application
import viewport
import resourcemanager
import game
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

class ActorWidget( interface.SpriteWidget):
    
    def _draw_self(self, viewport, disp_rect):
        load = self._game_object.carrying
        if load is not None:
            color = (load['qty']*200, 0, 0)
            pygame.draw.rect( viewport.surface, color, disp_rect, 0)
        interface.SpriteWidget._draw_self(self, viewport, disp_rect)

            
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

        #self.container2 = interface.DragPanel( self.iface, 
        #                    (400,10,375,200))
        #self.testa = interface.TestWidget( self.iface, (25,50,100,30))
        #self.testb = interface.TestWidget( self.iface, (25,100,100,30))
        #self.testc = interface.TestWidget( self.iface, (25,150,100,30))
        
        text = interface.StaticText("Lorem ipsum delores")
        basetext = interface.StaticText("Options: ")
        optionstext = interface.LambdaTextGenerator( lambda: self.options)

        #self.text3 = interface.TextLabel( self.iface, (135,150), "bigfont", text)
        
        #self.container2.add_child( self.testa)
        #self.container2.add_child( self.testb)
        #self.container2.add_child( self.testc)
        #self.container2.add_child( self.text3)
        #self.iface.add_child( self.container2)

        self.map = interface.MapWidget(self.iface, self.game)
        self.iface.add_child(self.map)
        
        #person
        testobj = actor.Actor(self.game, (-200, -200))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'mine', 'cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = ActorWidget( self.iface, testobj, self.resources.get("person"))
        self.iface.add_child( testwidg)

        #person2
        testobj = actor.Actor(self.game, (-100, -200))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'mine', 'cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = ActorWidget( self.iface, testobj, self.resources.get("person"))
        self.iface.add_child( testwidg)        
        
        #person3
        testobj = actor.Actor(self.game, (-150, -200))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'mine', 'cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = ActorWidget( self.iface, testobj, self.resources.get("person"))
        self.iface.add_child( testwidg)        
        
        #hut2
        testobj = game.StructureObject(self.game, (100,100), (280, -280), 4)
        testobj.target_actions = testobj.target_actions.union(['butcher', 'enlist'])
        testobj.set_storage(10, ('stone', 'wood'))        
        self.game.add_game_object(testobj)        
        testwidg = interface.StructWidget( self.iface, testobj, self.resources.get("hut"))
        self.iface.add_child( testwidg)
        
        #hut
        testobj = game.StructureObject(self.game, (100,100), (200, -200), 4)
        testobj.target_actions = testobj.target_actions.union(['butcher', 'enlist'])
        testobj.set_storage(10, ('stone', 'wood'))        
        self.game.add_game_object(testobj)        
        testwidg = interface.StructWidget( self.iface, testobj, self.resources.get("hut"))
        self.iface.add_child( testwidg)
        
        #rock
        testobj = game.StructureObject(self.game, (100,100), (-200, 170), 1)
        testobj.target_actions = testobj.target_actions.union(['mine'])
        self.game.add_game_object(testobj)
        testwidg = interface.StructWidget( self.iface, testobj, self.resources.get("rock"))
        self.iface.add_child( testwidg)
        
        #trees
        testobj = game.StructureObject(self.game, (100,100), (200, 170), 2)
        testobj.target_actions = testobj.target_actions.union(['cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = interface.StructWidget( self.iface, testobj, self.resources.get("tree"))
        self.iface.add_child( testwidg)
        

    def update(self):
        self.ticker += 1
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
                
        if event.type == pygame.KEYDOWN:
            if event.key == K_COMMA:
                self.options = max(self.options-1, 1)
            elif event.key == K_PERIOD:
                self.options = min(self.options+1, 8)
            elif event.key == K_ESCAPE:
                self.finish()
            elif event.key == K_z:
                x = self.game.selected_obj
                if hasattr(x, "res_storage"):
                    x.res_storage.deposit( 'wood', 1)
                else:
                    print "I can't find it"
            elif event.key == K_x:
                x = self.game.selected_obj
                if hasattr(x, "res_storage"):
                    x.res_storage.deposit( 'stone', 1)
                else:
                    print "I can't find it"
                
def run():

    app = CivilisApp()
    app.start_activity( WidgetActivity, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()