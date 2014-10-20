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
from src.interface import CompositeTextGenerator

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
        downscale = lambda tag: pygame.transform.smoothscale( self.assets.get(tag), (30,30))
        
        base = resource.Prototype('resource')
        abstract = resource.Prototype('abstract')
        manufactured = resource.Prototype('manufactured')
        gathered = resource.Prototype('gathered')
        base.add_children( (abstract, manufactured, gathered))
        
        materials = resource.Prototype('materials')
        food = resource.Prototype('food')
        gathered.add_children( (materials, food))
        
        reeds = resource.Prototype('reeds', concrete=True)
        metal = resource.Prototype('metal', concrete=True)
        stone = resource.Prototype('stone', downscale('stone-icon'), concrete=True)
        wood = resource.Prototype('wood', downscale('wood-icon'), concrete=True)
        clay = resource.Prototype('clay', downscale('clay-icon'), concrete=True)
        materials.add_children( (reeds, metal, stone, wood, clay))
        
        meat = resource.Prototype('meat', downscale('meat-icon'), concrete=True)
        vegies = resource.Prototype('vegetables',  downscale('corn-icon'), concrete=True)
        fish = resource.Prototype('fish', concrete=True)
        food.add_children( (meat,vegies,fish))
        
        goods = resource.Prototype('goods')
        weapons = resource.Prototype('weapons')
        tools = resource.Prototype('tools')
        manufactured.add_children( (goods, weapons, tools))
        
        nothing = resource.Prototype('nothing', concrete=True)
        spirit = resource.Prototype('spirit',  downscale('spirit-icon'), concrete=True)
        abstract.add_children( (nothing, spirit))
        
        jewelry = resource.Prototype('jewelry', concrete=True)
        hides = resource.Prototype('hides',  downscale('fur-icon'), concrete=True)
        baskets = resource.Prototype('baskets', concrete=True)
        pottery = resource.Prototype('pottery', downscale('pot-icon'), concrete=True)        
        goods.add_children( (jewelry, hides, baskets, pottery))
        
        stoneweapons = resource.Prototype('stone_weapons', concrete=True)
        metalweapons = resource.Prototype('metal_weapons', concrete=True)
        weapons.add_children( (stoneweapons, metalweapons))
        
        basic_tools = resource.Prototype('basic_tools', concrete=True)
        metal_tools = resource.Prototype('metal_tools', downscale('mtool-icon'), concrete=True)
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
        testobj = actor.Actor(self.game, (-100, 0))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'hunt', 'domesticate', 'mine', 'cut-wood', 'gather-corn', 'make-pots', 'make-tools', 'gather-clay', 'meditate'])
        self.game.add_game_object(testobj)        
        testwidg = interface.ActorWidget( self.iface, testobj, self.assets.get("person"))
        self.iface.add_child( testwidg)

        #person2
        testobj = actor.Actor(self.game, (0, 0))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'hunt', 'domesticate', 'mine', 'cut-wood', 'gather-corn', 'make-pots', 'make-tools', 'gather-clay', 'meditate'])
        self.game.add_game_object(testobj)        
        testwidg = interface.ActorWidget( self.iface, testobj, self.assets.get("person"))
        self.iface.add_child( testwidg)
        
        #person3
        testobj = actor.Actor(self.game, (100, 0))
        testobj.abilities = testobj.abilities.union(['butcher', 'enlist', 'hunt', 'domesticate', 'mine', 'cut-wood', 'gather-corn', 'make-pots', 'make-tools', 'gather-clay', 'meditate'])
        self.game.add_game_object(testobj)        
        testwidg = interface.ActorWidget( self.iface, testobj, self.assets.get("person"))
        self.iface.add_child( testwidg)
        
        #snorgle
        testobj = self.director.add_herd( (0,0))
        
        #hut
        testobj = self.director.add_simple_structure( (-600, -200), 3, ('make-tools', 'make-pots', 'butcher'), self.assets.get('hut'))
        store1 = resource.ResourceStore(testobj, 10, ('pottery',), resource.ResourceStore.WAREHOUSE)
        store2 = resource.ResourceStore(testobj, float('inf'), ('meat', 'vegetables', 'fish', 'spirit'), resource.ResourceStore.WAREHOUSE)         
        store = resource.CompositeResourceStore(testobj, (store1,store2), resource.ResourceStore.WAREHOUSE)       
        testobj.set_storage(store)
        
        #farm
        testobj = self.director.add_simple_structure( (-400,  200), 1, ('gather-corn',), self.assets.get('farm'))
        testobj.set_reservoir(10, ('vegetables'), 0.01)
        
        #storehouse
        testobj = self.director.add_simple_structure( (-200, -200), 0, (), self.assets.get('storehouse'))
        testobj.set_warehouse(2, ('clay', 'wood', 'stone'))        
        
        #altar
        testobj = self.director.add_simple_structure( (0,  200), 1, ('meditate',), self.assets.get('altar'))
        testobj.set_reservoir(float('inf'), 'spirit', 0)        
        
        #claypit
        testobj = self.director.add_simple_structure( (200, -200), 1, ('gather-clay',), self.assets.get('claypit'))
        testobj.set_reservoir(10, 'clay', 0.01)
        
        #rock
        testobj = self.director.add_simple_structure( (400,  200), 1, ('mine',), self.assets.get('rock'))
        testobj.set_reservoir(20, 'stone', 0.001)
        
        #trees
        testobj = self.director.add_simple_structure( (600, -200), 2, ('cut-wood',), self.assets.get('tree'))
        testobj.set_reservoir(5, 'wood', 0.01)
        
        #hud
        panel = interface.Panel(self.iface, (0,0,800,50))
        gen = interface.CompositeTextGenerator([interface.StaticText('Foodbuffer: '), interface.LambdaTextGenerator(lambda: self.director.food_buffer)])
        text = interface.TextLabel(self.iface, (10,10), 'medfont', gen)
        panel.add_child(text)
        self.iface.add_child(panel)

        
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
        
        self.food_buffer = 0

    def create_resource_dump(self, pos, dumpThis):
        storage = game.ResourcePile(self.game, (30,30), pos, 1)
        storage.target_actions = storage.target_actions.union(('store'))
        dump = resource.ResourceStore(storage, dumpThis['qty'], (dumpThis['type'],), resource.ResourceStore.DUMP)
        dump.deposit( dumpThis)
        dump.set_delta(dumpThis['type'], -.001)        
        storage.set_storage(dump)
        self.game.add_game_object(storage)
        
        if self.iface is not None:
            res_prototype = self.game.resource_types.find(dumpThis['type'])
            widget = interface.ResourcePileWidget(self.iface, storage, res_prototype.sprite)
            self.iface.add_child( widget)

    def add_simple_structure(self, position, num_workspaces, actions, sprite):
        obj = game.StructureObject(self.game, (100,100), position, num_workspaces)
        obj.target_actions = obj.target_actions.union(actions)
        self.game.add_game_object(obj)
        
        if self.iface is not None:
            widget = interface.StructWidget( self.iface, obj, sprite)
            self.iface.add_child( widget)
            
        return obj
    
    def add_tagged_structure(self, position, tag):
        '''This needs to add interface objects'''
        
        
        if tag == 'rock':
            obj = self.director.add_simple_structure( position, 1, ('mine',), self.assets.get('rock'))
            obj.set_reservoir(5, 'stone', 0.001)            
        elif tag == 'tree':
            obj = self.director.add_simple_structure( position, 2, ('cut-wood',), self.assets.get('tree'))
            obj.set_reservoir(5, 'wood', 0.001)                
        elif tag == 'hut':
            obj = self.add_simple_structure( position, 4, ('butcher', 'enlist'), self.assets.get('hut'))
            obj.set_warehouse(10, ('wood', 'stone', 'meat'))

    def make_circuit(self, center, size=300):
        self.num_nodes = random.randrange(8,13)
        
        aspect = random.uniform(3.0/5, 5.0/3)
        basedir = random.uniform(0.0, 2*math.pi)        
        incr = 2*math.pi/self.num_nodes
        direc = [0]*self.num_nodes
        for i in xrange(self.num_nodes):
            direc[i] = i*incr + random.uniform(-incr/3.0, incr/3.0)
        
        nodes = []
        for i in xrange(self.num_nodes):
            l = size * random.uniform(1.0, 1.25)
            pos = vector.Vec2d(math.sin(direc[i])*l*aspect, -math.cos(direc[i])*l/aspect)
            
            cos = math.cos(basedir)
            sin = math.sin(basedir)
            pos = vector.Vec2d( pos[0]*cos - pos[1]*sin, pos[0]*sin + pos[1]*cos)
            pos += center
            
            nodes.append(pos)
            
        return nodes
            
    def add_herd(self, position, add_scavenger=True):
        circuit = self.make_circuit( position, 1000)
        num_followers = 3
        
        obj = game.HerdObject(self.game, circuit)
        self.game.add_game_object( obj)
       
        if add_scavenger:
            obj2 = game.ScavengerObject(self.game, obj)
            self.game.add_game_object(obj2)
            obj.set_scavenger( obj2)
            
            if self.iface is not None:
                widg = interface.SpriteWidget(self.iface, obj2, self.assets.get('wolf'))
                self.iface.add_child(widg)
                    
        return obj        

            
    def add_herd_follower(self, leader):
        fol_obj = game.HerdMember(leader)
        self.game.add_game_object( fol_obj)
        fol_obj.target_actions = fol_obj.target_actions.union(['hunt', 'domesticate'])
        
        if self.iface is not None:            
            fol_widget = interface.HerdMemberWidget(self.iface, fol_obj, self.assets.get('snorgle'), self.assets.get('baby-snorgle'))
            self.iface.add_child( fol_widget)
            
        return fol_obj
    
    def deposit_to_any_store(self, addThis):
        
        deposited = 0
        for obj in self.game._objects:
            if hasattr(obj, 'res_storage') and obj.res_storage.mode == resource.ResourceStore.WAREHOUSE:
                qty = min(addThis['qty'], obj.res_storage.get_available_space(addThis['type']))
                if qty > 0:
                    if obj.res_storage.deposit( {'type': addThis['type'], 'qty': qty}):
                        deposited += qty
                        addThis['qty'] -= qty
                        
            if addThis['qty'] <= 0:
                break
            
        return deposited
    
    def consume_from_any_store(self, consume_these, total_amount):
        
        consumed = 0
        candidates = []
        contents = {}
        ratios = {}
        for tag in consume_these:
            contents[tag] = 0
        
        for obj in self.game._objects:
            if hasattr(obj, 'res_storage') and obj.res_storage.mode in (resource.ResourceStore.WAREHOUSE, resource.ResourceStore.DUMP):
                for c in consume_these:
                    qty = obj.res_storage.get_available_contents(c)
                    if qty > 0:
                        contents[c] += qty
                        candidates.append( obj)
                        
        total = 0
        for tag in contents:
            total += contents[tag]
            
        if total == 0:
            return 0
            
        for tag in contents:
            ratios[tag] = float(contents[tag]) / total
            
        for tag in consume_these:
            withdraw_amount = ratios[tag] * total_amount
            for obj in candidates:
                qty = min(obj.res_storage.get_available_contents(tag), withdraw_amount)
                if qty > 0:
                    res = obj.res_storage.withdraw(tag, qty)
                    withdraw_amount -= res['qty']
                    consumed += res['qty']
                    
            if withdraw_amount <= 0:
                continue
            
        return consumed
    
    def calc_food_value(self, foods):
        
        assert( len(foods) == 3)        
        if hasattr(foods, 'values'):
            values = sorted(foods.values())
        else:
            values = sorted(foods)
            
        return 3*values[0] + 2*values[1] + values[2]
    
    def get_total_available_stored_resources(self, tag):
        qty = 0
        for obj in self.game._objects:
            if hasattr(obj, 'res_storage') and obj.res_storage.mode in (resource.ResourceStore.WAREHOUSE, resource.ResourceStore.DUMP):
                qty += obj.res_storage.get_available_contents(tag)
                
        return qty
    
    def buffer_food(self, units=1):
        '''withdraws up to 1 of each food resource from any storage available, increasing the food buffer by a corresponding amount.
        The total amount of buffer increase is depenedent on the number of food types available. More food types = a greater buffer'''
        
        contents = {}
        
        tags = ('meat', 'fish', 'vegetables')
        for tag in tags:
            contents[tag] = self.consume_from_any_store((tag,), units)

        total = self.calc_food_value(contents)
        self.food_buffer += total
        return total
    
    def consume_food(self, amount):
        
        while self.food_buffer < amount:
            increase = self.buffer_food()
            if increase == 0:
                return False
            
        self.food_buffer -= amount
        return True

def run():

    app = CivilisApp()
    app.start_activity(TestActivity, None)
    
    while app.update():
        app.draw()
        
    app.cleanup()
