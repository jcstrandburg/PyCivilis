#global lib impports
import pygame
import random
import math
import os.path
import numpy
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
import tech
import tilemap
import path

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


class AstarActivity( application.Activity):
    
    tile_size = 40
    
    def on_create(self, config):
        self.screen = self.controller.screen
        
        self.tiles = numpy.random.randint(0,3,(20,20))
        shape = self.tiles.shape
        for y in xrange(shape[0]):
            for x in xrange(shape[1]):
                if self.tiles[y][x] == 2:
                    self.tiles[y][x] = 0
                    
        self.origin = (0,0)
        self.dest = (19,19)
        self.path = None
        
    def handle_event(self, event):
        pos = pygame.mouse.get_pos()
        x, y = pos[0]/self.tile_size, pos[1]/self.tile_size
        
        if event.type == pygame.MOUSEBUTTONDOWN:            
            
            if event.button == 1:
                self.tiles[y][x] = 1
            elif event.button == 3:
                self.tiles[y][x] = 0
        if event.type == pygame.KEYDOWN:
            if event.key == K_SPACE:
                self.find_path()
            elif event.key == K_1:
                self.origin = x,y
            elif event.key == K_2:
                self.dest = x,y
            elif event.key == K_a:
                self.show_walkability()

    def find_path(self):
        pathmap = path.PathMap(self.tiles)
        path_finder = path.PathFinder(self.origin, self.dest, pathmap)
        self.path = path_finder.find_path(False)
        self.simple_path = path_finder.simplify(self.path)
        if self.path is None:
            print "No path found"
        else:
            print len(self.path)

    def show_walkability(self):
        pathmap = path.PathMap(self.tiles)
        print pathmap.walkable(self.origin, self.dest)
                
    def update(self):
        pass
    
    def draw(self):
        shape = self.tiles.shape
        
        full = (0,0,0)
        empty = (200,200,240)
        
        for y in xrange(shape[0]):
            for x in xrange(shape[1]):
                disp_rect = pygame.Rect(x*self.tile_size,y*self.tile_size,self.tile_size,self.tile_size)
        
                tile = self.tiles[y][x]
                if tile:
                    color = full
                else:
                    color = empty
                pygame.draw.rect(self.screen, color, disp_rect)
                
        pygame.draw.circle(self.screen, (255,0,0), (self.origin[0]*self.tile_size + self.tile_size/2, self.origin[1]*self.tile_size + self.tile_size/2), self.tile_size/2)
        pygame.draw.circle(self.screen, (0,0,255), (self.dest[0]*self.tile_size + self.tile_size/2, self.dest[1]*self.tile_size + self.tile_size/2), self.tile_size/2)
        
        if self.path is not None:
            points = [(p[0]*self.tile_size + self.tile_size/2, p[1]*self.tile_size + self.tile_size/2) for p in self.path]
            pygame.draw.lines(self.screen, (0,125,0), False, points)
            
            points = [(p[0]*self.tile_size + self.tile_size/2, p[1]*self.tile_size + self.tile_size/2) for p in self.simple_path]
            pygame.draw.lines(self.screen, (0,0,200), False, points)            


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
        carcass = resource.Prototype('carcass', downscale('carcass-icon'), concrete=True)
        gathered.add_children( (materials, food, carcass))
        
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
        self.director = GameDirector(self.game, self.iface, self.assets, self.vp)
        self.game.director = self.director
        self.ticker = 1
        self.options = 5
        self.game.map = tilemap.Map((16,16))        
        
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
        
        #test buildings
        self.director.add_tagged_structure((-100, -200), "hut")
        self.director.add_tagged_structure((-300, 800), "farm")
        #self.director.add_tagged_structure((-50, -200), "storehouse")
        self.director.add_tagged_structure((-50, 400), "altar")
        self.director.add_tagged_structure((-800, 550), "claypit")
        self.director.add_tagged_structure((-350, -50), "rock")
        self.director.add_tagged_structure((-1100, 600), "tree")
        
        #hud
        panel = interface.Panel(self.iface, (0,0,800,30))
        gen = interface.CompositeTextGenerator([interface.StaticText('Foodbuffer: '), interface.LambdaTextGenerator(lambda: self.director.food_buffer)])
        text = interface.TextLabel(self.iface, (10,10), 'medfont', gen)
        panel.add_child(text)
        gen = interface.CompositeTextGenerator([
                    interface.StaticText('Spirit: '), 
                    interface.LambdaTextGenerator(lambda: self.director.get_total_available_stored_resources(('spirit',))),
                    ])
        text = interface.TextLabel(self.iface, (400,10), 'medfont', gen)
        panel.add_child(text)        
        button = interface.TextButton(self.iface, (550,10), 'medfont', interface.StaticText('Research'), ResearchMenuAction())
        panel.add_child(button)
        button = interface.TextButton(self.iface, (700,10), 'medfont', interface.StaticText('Build'), BuildMenuAction())
        panel.add_child(button)        
        self.iface.add_child(panel)
        
    def update(self):
        self.ticker += 1
        application.Activity.update(self)
        self.iface.update( self.vp)
        self.game.update()
        self.game.director.update()

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
            elif event.key == K_SPACE:
                topleft = self.vp.translate_point(pygame.mouse.get_pos(), viewport.SCREEN_TO_GAME)
                print str(topleft-(100,100)) + " | " + str(topleft+(100,100))
                print self.game.map.game_area_clear(topleft-(100,100), topleft+(100,100))
            elif event.key == K_1:
                pos = self.vp.translate_point(pygame.mouse.get_pos(), viewport.SCREEN_TO_GAME)
                print self.game.map.get_tile_at(self.game.map.game_coords_to_map(pos))
            elif event.key == K_ESCAPE:
                self.finish()
            elif event.key == K_m:
                self.game.map = tilemap.Map((16,16))
            elif event.key == K_n:
                self.game.map.grow_grass()
            elif event.key == K_k:
                self.game.map.save("map.txt")
            elif event.key == K_l:
                self.game.map.load("map.txt")
            elif event.key == K_TAB:
                testobj = game.BuildingPlacer(self.game, self.mouse_obj, "hut")
                self.game.add_game_object(testobj)        
                testwidg = interface.BuildingPlacerWidget(self.iface, testobj, pygame.Rect(0, 0, 200,200))
                self.iface.add_child(testwidg)                
            elif event.key == K_F1:
                i = 0
                while True:
                    path = "screen%d.png" % i
                    if not os.path.isfile(path):
                        pygame.image.save(self.vp.surface, path)
                        break
                    i += 1

class ResearchMenuAction(interface.InterfaceAction):
            
    def do_action(self, source_widget, interface, game):
        game.director.show_research_menu()
        
class ResearchItemAction(interface.InterfaceAction):
    
    def __init__(self, tag):
        interface.InterfaceAction.__init__(self)
        self.tag = tag        
        
    def do_action(self, source_widget, interface, game):

        director = game.director
        techmgr = director.tech
        spirit = director.get_total_available_stored_resources(('spirit',))
        print spirit        
        tech = techmgr.get_tech(self.tag)
        
        if tech.cost <= spirit:
            techmgr.research(self.tag)
            consumed = director.consume_from_any_store(('spirit',), tech.cost)
            if director.research_menu is not None:
                director.research_menu.finished = True
            director.show_research_menu()        

        
class BuildMenuAction(interface.InterfaceAction):
            
    def do_action(self, source_widget, interface, game):
        game.director.show_build_menu()        

        
class BuildItemAction(interface.InterfaceAction):
    
    def __init__(self, tag):
        interface.InterfaceAction.__init__(self)
        self.tag = tag        
        
    def do_action(self, source_widget, interface, game):
        director = game.director
        director.start_structure_build(self.tag)
        director.build_menu.finished = True
            

class GameDirector(object):
    '''Generic factory/game state mutator'''

    def __init__(self, game_mgr, iface_mgr, asset_mgr, viewport=None):
        self.game = game_mgr
        self.iface = iface_mgr
        self.assets = asset_mgr
        self.viewport = viewport
        
        #mouse follower object
        self.mouse_obj = game.GameObject(self.game, (0,0), (0,0), float('inf'))
        self.game.add_game_object(self.mouse_obj)
        
        self.food_buffer = 0
        self.tech = tech.CivilisTechManager()
        self.research_menu = None
        
    def update(self):
        self.mouse_obj.position = self.viewport.translate_point(pygame.mouse.get_pos(), viewport.SCREEN_TO_GAME)

    def show_research_menu(self):
        self.research_menu = panel = interface.Panel(self.iface, (100,100,600,600))
        self.iface.add_child(panel)

        panel.add_child(interface.TextButton(self.iface, (550, 10), 'smallfont', interface.StaticText('close'), interface.CloseAction(panel)))
        
        avails = self.tech.available_techs()
        offset = 1
        for tag in avails:
            tech = self.tech.get_tech(tag)
            string = "%d: %s" % (tech.cost, tech.tag)
            gen = interface.StaticText(string)
            offset += 1
            text = interface.TextButton(self.iface, (30, offset*25), 'medfont', gen, ResearchItemAction(tech.tag))
            panel.add_child(text)
            
    def show_build_menu(self):
        self.build_menu = panel = interface.Panel(self.iface, (100,100,600,600))
        self.iface.add_child(panel)

        panel.add_child(interface.TextButton(self.iface, (550, 10), 'smallfont', interface.StaticText('close'), interface.CloseAction(panel)))
        
        tags = ('hut', 'rock', 'tree', 'farm', 'storehouse', 'altar', 'claypit', 'rock', 'tree')
        offset = 1
        for tag in tags:
            string = tag
            gen = interface.StaticText(string)
            offset += 1
            text = interface.TextButton(self.iface, (30, offset*25), 'medfont', gen, BuildItemAction(tag))
            panel.add_child(text)

    def start_structure_build(self, tag):
        testobj = game.BuildingPlacer(self.game, self.mouse_obj, tag)
        self.game.add_game_object(testobj)        
        testwidg = interface.BuildingPlacerWidget(self.iface, testobj, pygame.Rect(0, 0, 200,200))
        self.iface.add_child(testwidg)            

    def create_resource_dump(self, pos, dumpThis):
        storage = game.ResourcePile(self.game, pos, dumpThis, 0.001)
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
            obj = self.add_simple_structure( position, 1, ('mine',), self.assets.get('rock'))
            obj.set_reservoir(5, 'stone', 0.001)            
        elif tag == 'tree':
            obj = self.add_simple_structure( position, 2, ('cut-wood',), self.assets.get('tree'))
            obj.set_reservoir(5, 'wood', 0.001)                
        elif tag == 'hut':
            obj = self.add_simple_structure( position, 4, ('butcher', 'enlist'), self.assets.get('hut'))
            store1 = resource.ResourceStore(obj, 5, ('pottery', 'hides'), resource.ResourceStore.WAREHOUSE)
            store2 = resource.ResourceStore(obj, float('inf'), ('meat', 'vegetables', 'fish', 'spirit'), resource.ResourceStore.WAREHOUSE)         
            store = resource.CompositeResourceStore(obj, (store1,store2), resource.ResourceStore.WAREHOUSE)       
            obj.set_storage(store)            
        elif tag == "farm":
            obj = self.add_simple_structure( position, 1, ('gather-corn',), self.assets.get('farm'))
            obj.set_reservoir(10, ('vegetables'), 0.01)
        elif tag == "storehouse":
            obj = self.add_simple_structure( position, 0, (), self.assets.get('storehouse'))
            obj.set_warehouse(2, ('clay', 'wood', 'stone'))
        elif tag == "altar":
            obj = self.add_simple_structure( position, 1, ('meditate',), self.assets.get('altar'))
            obj.set_reservoir(float('inf'), 'spirit', 0)        
        elif tag == "claypit":
            obj = self.add_simple_structure( position, 1, ('gather-clay',), self.assets.get('claypit'))
            obj.set_reservoir(10, 'clay', 0.01)
        elif tag == "rock":
            obj = self.add_simple_structure( position, 1, ('mine',), self.assets.get('rock'))
            obj.set_reservoir(20, 'stone', 0.001)
        elif tag == "tree":
            obj = self.add_simple_structure( position, 2, ('cut-wood',), self.assets.get('tree'))
            obj.set_reservoir(5, 'wood', 0.01)
        else:
            raise ValueError("Invalid tag "+tag)
            
        return obj

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
