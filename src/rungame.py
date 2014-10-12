#global lib impports
import copy
import pygame
import random
import math
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

class CircuitFollower(object):
    def __init__(self, herd):
        self.move_speed = 1.0
        self.herd = herd
        self.target = self.herd.position
        self.position = self.herd.position
        
    def update(self):
        diff = self.target - self.position
        if diff.length <= self.move_speed:
            x = 30
            self.target = self.herd.position + (random.uniform(-x,x), random.uniform(-x,x))
        else:
            self.position = self.position.interpolate_to( self.target, self.move_speed/diff.length)

class CircuitHerd(object):
    def __init__(self, circuit):
        self.move_speed = 1.5
        self.circuit = circuit
        self.position = circuit[0]
        self.node = 0
    
    def update(self):
        diff = self.circuit[self.node] - self.position
        if diff.length <= self.move_speed:
            self.node = (self.node + 1)%len(self.circuit)
        else:
            print diff.length
            self.position = self.position.interpolate_to( self.circuit[self.node], self.move_speed/diff.length)

class CircuitActivity( application.Activity):
    
    def on_create(self, config):
        self.screen = self.controller.screen
        
        self.make_circuit()
        
    def make_circuit(self):
        self.num_nodes = 10
        center = self.screen.get_rect().center
        
        aspect = random.uniform(2.0/4, 4.0/2)
        basedir = random.uniform(0.0, 2*math.pi)        
        incr = 2*math.pi/self.num_nodes
        direc = [0]*self.num_nodes
        for i in xrange(self.num_nodes):
            direc[i] = i*incr + random.uniform(-incr/3.0, incr/3.0)
        
        self.nodes = []
        for i in xrange(self.num_nodes):
            l = 200 * random.uniform(1.0, 1.25)
            pos = vector.Vec2d(math.sin(direc[i])*l*aspect, -math.cos(direc[i])*l/aspect)
            
            cos = math.cos(basedir)
            sin = math.sin(basedir)
            pos = vector.Vec2d( pos[0]*cos - pos[1]*sin, pos[0]*sin + pos[1]*cos)
            pos += center
            
            self.nodes.append(pos)
        
        #herd stuff
        self.num_followers = 4
        self.herd = CircuitHerd(self.nodes)
        self.followers = [CircuitFollower(self.herd) for i in xrange(self.num_followers)]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == K_SPACE:
                self.make_circuit()
                
    def update(self):
        self.herd.update()
        for fol in self.followers:
            fol.update()
    
    def draw(self):
        rect = self.screen.get_rect()
        center = rect.center
        
        for i in xrange(len(self.nodes)-1):
            pos1 = self.nodes[i]
            pos2 = self.nodes[i+1]
            
            pygame.draw.line(self.screen, (0,0,0), pos1.int_tuple, pos2.int_tuple)
        
        for n in self.nodes:
            pos = n
            pygame.draw.circle(self.screen, (0,50,200), pos.int_tuple, 10)
            
        pygame.draw.circle(self.screen, (250,250,250), self.herd.position.int_tuple, 8)
        for fol in self.followers:
            pygame.draw.circle(self.screen, (250,250,0), fol.position.int_tuple, 5)            
            

            
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
        testobj = self.director.add_herd( (0,0))
        
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
        testobj = self.director.add_simple_structure( (-200, 170), 1, ('mine',), self.assets.get('rock'))
        testobj.set_reservoir(4, 'stone', 0.001)
        
        #trees
        testobj = self.director.add_simple_structure( (200,170), 2, ('cut-wood',), self.assets.get('tree'))
        testobj.set_reservoir(5, 'wood', 0.01)


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
            self.vp.pan( (5/self.vp.scale,0))
        elif pressed[K_a]:
            self.vp.pan( (-5/self.vp.scale,0))
        if pressed[K_s]:
            self.vp.pan( (0,5/self.vp.scale))
        elif pressed[K_w]:
            self.vp.pan( (0,-5/self.vp.scale))

            
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

    def add_simple_structure(self, position, num_workspaces, actions, sprite):
        obj = game.StructureObject(self.game, (100,100), position, num_workspaces)
        obj.target_actions = obj.target_actions.union(actions)
        self.game.add_game_object(obj)
        widget = interface.StructWidget( self.iface, obj, sprite)
        self.iface.add_child( widget)
        return obj
    
    def add_tagged_structure(self, position, tag):
        if tag == 'rock':
            obj = self.director.add_simple_structure( position, 1, ('mine',), self.assets.get('rock'))
            obj.set_reservoir(5, 'stone', 0.001)            
        elif tag == 'tree':
            obj = self.director.add_simple_structure( position, 2, ('cut-wood',), self.assets.get('tree'))
            obj.set_reservoir(5, 'wood', 0.001)                
        elif tag == 'hut':
            obj = self.add_simple_structure( position, 4, ('butcher', 'enlist'), self.assets.get('hut'))
            obj.set_storage(10, ('wood', 'stone', 'meat'))

    def make_circuit(self, center):
        self.num_nodes = random.randrange(8,13)
        
        aspect = random.uniform(3.0/5, 5.0/3)
        basedir = random.uniform(0.0, 2*math.pi)        
        incr = 2*math.pi/self.num_nodes
        direc = [0]*self.num_nodes
        for i in xrange(self.num_nodes):
            direc[i] = i*incr + random.uniform(-incr/3.0, incr/3.0)
        
        nodes = []
        for i in xrange(self.num_nodes):
            l = 300 * random.uniform(1.0, 1.25)
            pos = vector.Vec2d(math.sin(direc[i])*l*aspect, -math.cos(direc[i])*l/aspect)
            
            cos = math.cos(basedir)
            sin = math.sin(basedir)
            pos = vector.Vec2d( pos[0]*cos - pos[1]*sin, pos[0]*sin + pos[1]*cos)
            pos += center
            
            nodes.append(pos)
            
        return nodes
            
    def add_herd(self, position):
        circuit = self.make_circuit( position)
        num_followers = 3
        
        obj = game.HerdObject(self.game, circuit)
        self.game.add_game_object( obj)

            
    def add_herd_follower(self, leader):
        fol_obj = game.HerdMember(leader)
        self.game.add_game_object( fol_obj)
        fol_obj.target_actions = fol_obj.target_actions.union(['hunt', 'domesticate'])            
        fol_widget = interface.HerdMemberWidget(self.iface, fol_obj, self.assets.get('snorgle'), self.assets.get('baby-snorgle'))
        self.iface.add_child( fol_widget)
        return fol_obj    
            
            

def run():

    app = CivilisApp()
    app.start_activity(TestActivity, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()
