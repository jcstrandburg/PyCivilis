#global lib impports
import copy
import pygame
from pygame.locals import *

#local imports
import application
import viewport
import vector
import assetmanager
import game
import interface
import actor
import resource

class CivilisApp( application.Application):
    """Game specific Application class."""
    def __init__(self):
        application.Application.__init__(self)
        self._object_id = 0

    def make_object_id(self):
        self._object_id += 1
        return self._object_id-1


class DictEvent(object):
    '''This is a big ugly hack designed to force pygame events to have dictionaries so you can add new attributes to them.'''
    def __init__(self, event):
        slots = ('type', 'gain', 'state', 'unicode', 'key', 'mod', 'pos', 'rel', 'buttons', 'button', 'joy', 'axis', 'value', 'ball', 'hat', 'size', 'w', 'h', 'code')
        for s in slots:
            if hasattr(event, s):
                self.__dict__[s] = getattr(event, s)

            
class TestActivity( application.Activity):
    """Test activity for debugging."""
    
    def make_resource_tree(self):
        base = resource.Prototype('resource')
        abstract = resource.Prototype('abstract')
        manufactured = resource.Prototype('manufactured')
        gathered = resource.Prototype('gathered')
        base.add_children( (abstract, manufactured, gathered))
        
        materials = resource.Prototype('materials')
        food = resource.Prototype('food')
        gathered.add_children( (materials, food))
        
        reeds = resource.Prototype('reeds')
        metal = resource.Prototype('metal')
        stone = resource.Prototype('stone', pygame.transform.smoothscale( self.assets.get('stone-icon'), (30,30)))
        wood = resource.Prototype('wood', pygame.transform.smoothscale( self.assets.get('wood-icon'), (30,30)))
        clay = resource.Prototype('clay')
        materials.add_children( (reeds, metal, stone, wood, clay))
        
        meat = resource.Prototype('meat', pygame.transform.smoothscale( self.assets.get('meat-icon'), (30,30)))
        vegies = resource.Prototype('vegetables')
        fish = resource.Prototype('fish')
        food.add_children( (meat,vegies,fish))
        
        goods = resource.Prototype('goods')
        weapons = resource.Prototype('weapons')
        tools = resource.Prototype('tools')
        manufactured.add_children( (goods, weapons, tools))
        
        nothing = resource.Prototype('nothing')
        spirit = resource.Prototype('spirit')
        abstract.add_children( (nothing, spirit))
        
        jewelry = resource.Prototype('jewelry')
        hides = resource.Prototype('hides')
        baskets = resource.Prototype('baskets')
        goods.add_children( (jewelry, hides, baskets))
        
        stoneweapons = resource.Prototype('stone_weapons')
        metalweapons = resource.Prototype('metal_weapons')
        weapons.add_children( (stoneweapons, metalweapons))
        
        basic_tools = resource.Prototype('basic_tools')
        metal_tools = resource.Prototype('metal_tools')
        tools.add_children( (basic_tools, metal_tools))
        
        return base

    
    def on_create(self, config):
        application.Activity.on_create(self, config)
        self.controller.set_fps_cap( 50)
        self.vp = viewport.Viewport( self.controller.screen)
        self.vp.transform.set_rotation_interval( 5)

        self.assets = assetmanager.AssetManager()
        self.assets.load_set("res/assets.txt")
        
        self.font = pygame.font.Font(None, 24)
        self.iface = interface.InterfaceManager(self)
        self.game = game.Game()
        self.director = GameDirector(self.game, self.iface, self.assets)
        self.game.director = self.director
        self.ticker = 1
        self.options = 5
        
        self.game.resource_types = self.make_resource_tree()
        
        self.icons = []
        for i in xrange(8):
            tag = "ico" + str(i)
            self.icons.append(pygame.transform.smoothscale( self.assets.get(tag), (40,40)))

        self.map = interface.MapWidget(self.iface, self.game)
        self.iface.add_child(self.map)
        
        #person
        testobj = actor.Actor(self.game, (-200, 0))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'hunt', 'domesticate', 'mine', 'cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = interface.ActorWidget( self.iface, testobj, self.assets.get("person"))
        self.iface.add_child( testwidg)

        #person2
        testobj = actor.Actor(self.game, (-100, -200))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'hunt', 'domesticate', 'mine', 'cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = interface.ActorWidget( self.iface, testobj, self.assets.get("person"))
        self.iface.add_child( testwidg)
        
        #person3
        testobj = actor.Actor(self.game, (-150, -200))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'hunt', 'domesticate', 'mine', 'cut-wood'])
        self.game.add_game_object(testobj)        
        testwidg = interface.ActorWidget( self.iface, testobj, self.assets.get("person"))
        self.iface.add_child( testwidg)
        
        #snorgle
        testobj = game.HerdObject(self.game, (-150, -150))
        testobj.target_actions = testobj.target_actions.union(['hunt', 'domesticate'])        
        self.game.add_game_object( testobj)
        testwidg = interface.HerdWidget(self.iface, testobj, self.assets.get('snorgle'), pygame.transform.smoothscale( self.assets.get('meat-icon'), (30,30)))
        self.iface.add_child( testwidg)
        
        #hut2
        '''testobj = game.StructureObject(self.game, (100,100), (280, -280), 4)
        testobj.target_actions = testobj.target_actions.union(['butcher', 'enlist'])
        testobj.set_storage(7, ('stone', 'wood', 'meat'))        
        self.game.add_game_object(testobj)        
        testwidg = interface.StructWidget( self.iface, testobj, self.assets.get("hut"))
        self.iface.add_child( testwidg)'''
        
        #hut
        testobj = game.StructureObject(self.game, (100,100), (125, -125), 4)
        testobj.target_actions = testobj.target_actions.union(['butcher', 'enlist'])
        testobj.set_storage(1, ('stone', 'wood', 'meat'))
        self.game.add_game_object(testobj)
        testwidg = interface.StructWidget( self.iface, testobj, self.assets.get("hut"))
        self.iface.add_child( testwidg)
        
        #rock
        testobj = game.StructureObject(self.game, (100,100), (-200, 170), 1)
        testobj.target_actions = testobj.target_actions.union(['mine'])
        testobj.set_reservoir(4, 'stone', 0)
        self.game.add_game_object(testobj)
        testwidg = interface.StructWidget( self.iface, testobj, self.assets.get("rock"))
        self.iface.add_child( testwidg)
        
        #trees
        testobj = game.StructureObject(self.game, (100,100), (200, 170), 2)
        testobj.target_actions = testobj.target_actions.union(['mine'])
        testobj.set_reservoir(5, 'stone', 0)
        self.game.add_game_object(testobj)
        testwidg = interface.StructWidget( self.iface, testobj, self.assets.get("tree"))
        self.iface.add_child( testwidg)

    def create_resource_dump(self, pos, resource):
        storage = game.ResourcePile(self.game, (30,30), pos, 1)
        storage.target_actions = storage.target_actions.union(('store'))
        storage.set_storage(resource['qty'], [resource['type']])
        storage.res_storage.deposit( resource)
        storage.res_storage.set_delta(resource['type'], -.001)
        self.game.add_game_object(storage)
        resource = self.game.resource_types.find(resource['type'])
        widget = interface.ResourcePileWidget(self.iface, storage, resource.sprite)
        self.iface.add_child( widget)
        
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
        event = DictEvent(event)

        if hasattr( event, 'pos'):
            gamepos = self.vp.translate_point(event.pos, viewport.SCREEN_TO_GAME)
            event.gamepos = gamepos
                                                    
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
                

class GameDirector(object):
    '''Generic factory/game state mutator'''

    def __init__(self, game_mgr, iface_mgr, asset_mgr):
        self.game = game_mgr
        self.iface = iface_mgr
        self.assets = asset_mgr

    def create_resource_dump(self, pos, resource):
        storage = game.ResourcePile(self.game, (30,30), pos, 1)
        storage.target_actions = storage.target_actions.union(('store'))
        storage.set_storage(resource['qty'], [resource['type']])
        storage.res_storage.deposit( resource)
        storage.res_storage.set_delta(resource['type'], -.001)
        self.game.add_game_object(storage)
        resource = self.game.resource_types.find(resource['type'])
        widget = interface.ResourcePileWidget(self.iface, storage, resource.sprite)
        self.iface.add_child( widget)

#    def add_structure(self, position, workspaces, actions, 
                
def run():

    app = CivilisApp()
    app.start_activity(TestActivity, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()
