import unittest

import resource
import game
import actor

class ResourceStoreTest(unittest.TestCase):
    def setUp(self):
        self.store1 = resource.ResourceStore(None, 10, ['stone','wood'], True, True)
        self.store2 = resource.ResourceStore(None, 10, ['stone','wood'], True, True)
        self.store3 = resource.ResourceStore(None, 1, ['clay'], True, True)
        self.store3.set_delta('clay', 0.4)
        self.store4 = resource.ResourceStore(None, 1, ['clay'], True, True)
        self.store4.deposit({'type':'clay', 'qty':1})
        self.store4.set_delta('clay', -0.4)
        
    def test_setup(self):
        self.assertTrue(self.store1.allow_forage)
        self.assertTrue(self.store1.allow_deposit)
        
        self.assertEqual( self.store1.get_capacity(), 10)        
        
    def test_simple_deposit(self):
        self.store1.deposit({'type':'stone', 'qty':2})
        self.store1.deposit({'type':'wood', 'qty':4})
        
        self.assertEqual( self.store1.get_actual_contents(None), 6)
        self.assertEqual( self.store1.get_actual_contents('stone'), 2)
        self.assertEqual( self.store1.get_actual_contents('wood'), 4)
        self.assertEqual( self.store1.get_actual_contents('tools'), 0)
        
        self.assertEqual( self.store1.get_unclaimed_contents(None), 6)
        self.assertEqual( self.store1.get_unclaimed_contents('stone'), 2)
        self.assertEqual( self.store1.get_unclaimed_contents('wood'), 4)
        self.assertEqual( self.store1.get_unclaimed_contents('tools'), 0)

        self.assertEqual( self.store1.get_available_contents(None), 6)
        self.assertEqual( self.store1.get_available_contents('stone'), 2)
        self.assertEqual( self.store1.get_available_contents('wood'), 4)
        self.assertEqual( self.store1.get_available_contents('tools'), 0)
        
        self.assertEqual( self.store1.get_available_space(None), 4)
        self.assertEqual( self.store1.get_available_space('stone'), 4)
        self.assertEqual( self.store1.get_available_space('wood'), 4)
        self.assertEqual( self.store1.get_available_space('tools'), 0)
    
    def test_reserve_storage(self):
        self.store2.deposit({'type':'stone', 'qty':2})
        self.store2.deposit({'type':'wood', 'qty':4})        
        
        self.store2.update()
        res = self.store2.reserve_storage('tools', 1)
        self.assertIsNone(res)

        self.assertEqual(self.store2.get_available_space('wood'), 4)        
        res1 = self.store2.reserve_storage('wood', 2)
        self.assertIsNotNone( res1)
        self.assertTrue( res1.ready)
        
        self.assertEqual(self.store2.get_available_space('stone'), 2)        
        res2 = self.store2.reserve_storage('stone', 2)
        self.assertIsNotNone( res2)
        self.assertTrue( res2.ready)

        self.assertEqual(self.store2.get_available_space('wood'), 0)
        res3 = self.store2.reserve_storage('wood', 2)
        self.assertIsNone(res3, 'Reservation should have failed')
        
        res2.release()
        self.store2.update()
        res3 = self.store2.reserve_storage('stone', 2)
        self.assertIsNotNone( res3)
        self.assertTrue( res3.ready)
        
    def test_reserve_resources(self):
        store = resource.ResourceStore(None, 10, ['stone','wood'], True, True)
        store.set_delta('stone', 0.001)
        
        store.deposit({'type':'stone', 'qty':4})
        self.assertAlmostEqual(store.get_available_contents('stone'), 4, delta=0.01)        
        res1 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), 3, delta=0.01)
        res2 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), 2, delta=0.01)
        res3 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), 1, delta=0.01)
        res4 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), 0, delta=0.01)
        res5 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), -1, delta=0.01)
        res6 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), -2, delta=0.01)
        res7 = store.reserve_resources('stone', 1)
        self.assertAlmostEqual(store.get_available_contents('stone'), -3, delta=0.01)

        self.assertIsNotNone(res1)
        self.assertIsNotNone(res2)
        self.assertIsNotNone(res3)
        self.assertIsNotNone(res4)
        self.assertIsNotNone(res5)
        self.assertIsNotNone(res6)
        self.assertIsNotNone(res7)

        self.assertTrue(res1.ready)
        self.assertTrue(res2.ready)
        self.assertTrue(res3.ready)
        self.assertTrue(res4.ready)
        self.assertFalse(res5.ready)
        self.assertFalse(res6.ready)
        self.assertFalse(res7.ready)
        
        store.deposit({'type':'stone', 'qty':1})
        store.update()        
        self.assertAlmostEqual(store.get_available_contents('stone'), -2, delta=0.01)
        self.assertTrue(res5.ready)
        self.assertFalse(res6.ready)
        self.assertFalse(res7.ready)
        
        res1.release()
        store.update()
        self.assertAlmostEqual(store.get_available_contents('stone'), -1, delta=0.01)        
        self.assertTrue(res6.ready)
        self.assertFalse(res7.ready)
        
    def test_regeneration(self):
        self.assertEqual(self.store3.get_actual_contents('clay'), 0)
        self.store3.update()
        self.assertAlmostEqual(self.store3.get_actual_contents('clay'), .4, delta=.001)
        self.store3.update()
        self.assertAlmostEqual(self.store3.get_actual_contents('clay'), .8, delta=.001)
        self.store3.update()
        self.assertAlmostEqual(self.store3.get_actual_contents('clay'), 1, msg='contents should have maxed at 1', delta=.001)
        self.store3.update()
        self.assertAlmostEqual(self.store3.get_actual_contents('clay'), 1, msg='contents should have remained 1', delta=.001)
        
    def test_decay(self):
        self.assertEqual(self.store4.get_actual_contents('clay'), 1)
        self.store4.update()
        self.assertAlmostEqual(self.store4.get_actual_contents('clay'), .6, delta=.001)        
        self.store4.update()
        self.assertAlmostEqual(self.store4.get_actual_contents('clay'), .2, delta=.001)        
        self.store4.update()
        self.assertAlmostEqual(self.store4.get_actual_contents('clay'), .0, delta=.001)        
        self.store4.update()
        self.assertAlmostEqual(self.store4.get_actual_contents('clay'), .0, delta=.001)        

class ExtendedResourceStoreTest(unittest.TestCase):
    def setUp(self):
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
        stone = resource.Prototype('stone', concrete=True)
        wood = resource.Prototype('wood', concrete=True)
        clay = resource.Prototype('clay', concrete=True)
        materials.add_children( (reeds, metal, stone, wood, clay))
        
        meat = resource.Prototype('meat', concrete=True)
        vegies = resource.Prototype('vegetables', concrete=True)
        fish = resource.Prototype('fish', concrete=True)
        food.add_children( (meat,vegies,fish))
        
        goods = resource.Prototype('goods')
        weapons = resource.Prototype('weapons')
        tools = resource.Prototype('tools')
        manufactured.add_children( (goods, weapons, tools))
        
        nothing = resource.Prototype('nothing', concrete=True)
        spirit = resource.Prototype('spirit', concrete=True)
        abstract.add_children( (nothing, spirit))
        
        jewelry = resource.Prototype('jewelry', concrete=True)
        hides = resource.Prototype('hides', concrete=True)
        baskets = resource.Prototype('baskets', concrete=True)
        goods.add_children( (jewelry, hides, baskets))
        
        stoneweapons = resource.Prototype('stone_weapons', concrete=True)
        metalweapons = resource.Prototype('metal_weapons', concrete=True)
        weapons.add_children( (stoneweapons, metalweapons))
        
        basic_tools = resource.Prototype('basic_tools', concrete=True)
        metal_tools = resource.Prototype('metal_tools', concrete=True)
        tools.add_children( (basic_tools, metal_tools))

        self.rtree = base

    def test_composition(self):
        store = resource.CompositeResourceStore()
        sub1 = resource.ResourceStore(None, 4, ['stone'])
        sub2 = resource.ResourceStore(None, 3, ['metal'])
        sub3 = resource.ResourceStore(None, 2, ['wood'])
        sub4 = resource.ResourceStore(None, 1, ['clay'])
        store.add_stores( (sub1, sub2, sub3, sub4))
        
        self.assertTrue( sub1.accepts('stone'))
        self.assertFalse( sub1.accepts('fish'))
        self.assertTrue( store.accepts('stone'))
        self.assertTrue( sub2.accepts('metal'))
        self.assertFalse( sub2.accepts('fish'))
        self.assertTrue( store.accepts('metal'))
        self.assertTrue( sub3.accepts('wood'))
        self.assertFalse( sub3.accepts('fish'))
        self.assertTrue( store.accepts('wood'))
        self.assertTrue( sub4.accepts('clay'))
        self.assertFalse( sub4.accepts('fish'))
        self.assertTrue( store.accepts('clay'))

        self.assertEqual(store.get_capacity(), 10)        
        self.assertTrue( sub2.deposit({'type':'metal', 'qty':1}))
        self.assertTrue( sub1.deposit({'type':'stone', 'qty':1}))
        self.assertFalse( sub3.deposit({'type':'meat', 'qty':1}))
        self.assertTrue( store.deposit({'type':'stone', 'qty':1}))
        
        self.assertEqual(store.get_actual_contents('clay'), 0) 
        self.assertEqual(store.get_actual_contents('metal'), 1) 
        self.assertEqual(store.get_actual_contents('stone'), 2) 
        self.assertEqual(store.get_actual_contents('wood'), 0) 
        self.assertEqual(store.get_actual_contents('meat'), 0)
        
        self.assertEqual(store.get_available_space('clay'), 1)
        self.assertEqual(store.get_available_space('metal'), 2)
        self.assertEqual(store.get_available_space('stone'), 2)
        self.assertEqual(store.get_available_space('wood'), 2)
        self.assertEqual(store.get_available_space('meat'), 0)


    def test_composition_overlap(self):
        store = resource.CompositeResourceStore()
        sub1 = resource.ResourceStore(None, 2, ['stone','wood'])
        sub2 = resource.ResourceStore(None, 2, ['stone'])
        self.assertRaises( ValueError, store.add_stores, (sub1, sub2))
        
    def test_multiple_contents(self):
        store1 = resource.ResourceStore(None, 10, ['stone', 'wood', 'clay', 'metal'])
        store2 = resource.ResourceStore(None, 10, ['vegetables', 'fish', 'meat'])
        store = resource.CompositeResourceStore( (store1, store2))
        
        self.assertTrue(store.deposit({'type':'wood', 'qty':5}))
        self.assertTrue(store.deposit({'type':'metal', 'qty':2}))        
        self.assertTrue(store.deposit({'type':'fish', 'qty':1}))
        self.assertTrue(store.deposit({'type':'meat', 'qty':3}))
        
        all = self.rtree.flatten_tree_concrete()
        food = self.rtree.find('food').flatten_tree_concrete()
        materials = self.rtree.find('materials').flatten_tree_concrete()
        misc1 = ['stone','clay','vegetables']
        misc2 = ['wood','fish','meat']
        misc3 = ['stone', 'wood']
        
        self.assertEqual( store1.get_actual_contents(all), 7)
        self.assertEqual( store2.get_actual_contents(all), 4)
        self.assertEqual( store.get_actual_contents(all), 11)
        self.assertEqual( store1.get_actual_contents(food), 0)
        self.assertEqual( store2.get_actual_contents(food), 4)
        self.assertEqual( store.get_actual_contents(food), 4)
        self.assertEqual( store1.get_actual_contents(materials), 7)
        self.assertEqual( store2.get_actual_contents(materials), 0)
        self.assertEqual( store.get_actual_contents(materials), 7)
        self.assertEqual( store1.get_actual_contents(misc1), 0)
        self.assertEqual( store2.get_actual_contents(misc1), 0)
        self.assertEqual( store.get_actual_contents(misc1), 0)
        self.assertEqual( store1.get_actual_contents(misc2), 5)
        self.assertEqual( store2.get_actual_contents(misc2), 4)
        self.assertEqual( store.get_actual_contents(misc2), 9)
        self.assertEqual( store1.get_actual_contents(misc3), 5)
        self.assertEqual( store2.get_actual_contents(misc3), 0)
        self.assertEqual( store.get_actual_contents(misc3), 5)
        
        res1 = store.reserve_resources('wood', 2)
        res2 = store.reserve_resources('fish', 1)
        res3 = store.reserve_resources('meat', 2)
         
        self.assertIsNotNone( res1)
        self.assertEqual( res1.qty, 2)
        self.assertIsNotNone( res2)
        self.assertEqual( res2.tag, 'fish')
        self.assertEqual( res2.qty, 1)
        self.assertEqual( res2.ready, True)
        self.assertIsNotNone( res3)
        self.assertEqual( res3.tag, 'meat')        
        self.assertEqual( res3.qty, 2)
        self.assertEqual( res3.ready, True)        

        self.assertEqual( store1.get_available_contents(all), 5)
        self.assertEqual( store2.get_available_contents(all), 1)
        self.assertEqual( store.get_available_contents(all), 6)
        self.assertEqual( store1.get_available_contents(food), 0)
        self.assertEqual( store2.get_available_contents(food), 1)        
        self.assertEqual( store.get_available_contents(food), 1)
        self.assertEqual( store1.get_available_contents(materials), 5)
        self.assertEqual( store2.get_available_contents(materials), 0)        
        self.assertEqual( store.get_available_contents(materials), 5)
        self.assertEqual( store1.get_available_contents(misc1), 0)
        self.assertEqual( store2.get_available_contents(misc1), 0)        
        self.assertEqual( store.get_available_contents(misc1), 0)
        self.assertEqual( store1.get_available_contents(misc2), 3)
        self.assertEqual( store2.get_available_contents(misc2), 1)        
        self.assertEqual( store.get_available_contents(misc2), 4)
        self.assertEqual( store1.get_available_contents(misc3), 3)
        self.assertEqual( store2.get_available_contents(misc3), 0)        
        self.assertEqual( store.get_available_contents(misc3), 3)        


class ResourceTreeTests(unittest.TestCase):
    def setUp(self):
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
        stone = resource.Prototype('stone', concrete=True)
        wood = resource.Prototype('wood', concrete=True)
        clay = resource.Prototype('clay', concrete=True)
        materials.add_children( (reeds, metal, stone, wood, clay))
        
        meat = resource.Prototype('meat', concrete=True)
        vegies = resource.Prototype('vegetables', concrete=True)
        fish = resource.Prototype('fish', concrete=True)
        food.add_children( (meat,vegies,fish))
        
        goods = resource.Prototype('goods')
        weapons = resource.Prototype('weapons')
        tools = resource.Prototype('tools')
        manufactured.add_children( (goods, weapons, tools))
        
        nothing = resource.Prototype('nothing', concrete=True)
        spirit = resource.Prototype('spirit', concrete=True)
        abstract.add_children( (nothing, spirit))
        
        jewelry = resource.Prototype('jewelry', concrete=True)
        hides = resource.Prototype('hides', concrete=True)
        baskets = resource.Prototype('baskets', concrete=True)
        goods.add_children( (jewelry, hides, baskets))
        
        stoneweapons = resource.Prototype('stone_weapons', concrete=True)
        metalweapons = resource.Prototype('metal_weapons', concrete=True)
        weapons.add_children( (stoneweapons, metalweapons))
        
        basic_tools = resource.Prototype('basic_tools', concrete=True)
        metal_tools = resource.Prototype('metal_tools', concrete=True)
        tools.add_children( (basic_tools, metal_tools))

        self.rtree = base   
    
    def test_downstream(self):
        tools = self.rtree.find('tools')
        gathered = self.rtree.find('gathered')
        abstract = self.rtree.find('abstract')
        
        self.assertIsNotNone( tools)
        self.assertIsNotNone( gathered)
        self.assertIsNotNone( abstract)
        
        self.assertIsNotNone( tools.find('basic_tools'))
        self.assertIsNotNone( tools.find('metal_tools'))
        self.assertIsNotNone( gathered.find('materials'))
        self.assertIsNotNone( gathered.find('clay'))
        self.assertIsNotNone( abstract.find('spirit'))
        self.assertIsNotNone( abstract.find('nothing'))
        
        self.assertIsNone( self.rtree.find('beefsquatch'))
        self.assertIsNone( tools.find('clay'))
        self.assertIsNone( gathered.find('resource'))
        self.assertIsNone( abstract.find('wood'))
        
    def test_upstream(self):
        clay = self.rtree.find('clay')
        basic_tools = self.rtree.find('basic_tools')
        hides = self.rtree.find('hides')

        self.assertIsNotNone(clay)
        self.assertIsNotNone(basic_tools)
        self.assertIsNotNone(hides)


        self.assertIsNone(clay.find_parent('reeds'))
        self.assertIsNone(clay.find_parent('meat'))
        self.assertIsNone(basic_tools.find_parent('materials'))
        self.assertIsNone(basic_tools.find_parent('metal_tools'))
        
        self.assertIsNotNone( clay.find_parent('materials'))      
        self.assertIsNotNone( clay.find_parent('gathered'))      
        self.assertIsNotNone( clay.find_parent('resource'))
        self.assertIsNotNone( basic_tools.find_parent('tools'))
        self.assertIsNotNone( basic_tools.find_parent('manufactured'))
        self.assertIsNotNone( basic_tools.find_parent('resource'))
        self.assertIsNotNone( hides.find_parent('goods'))
        self.assertIsNotNone( hides.find_parent('manufactured'))
        self.assertIsNotNone( hides.find_parent('resource'))
        
    def test_descendants(self):
        emptyset = set()
        
        materials = self.rtree.find('materials')
        elements = set(materials.flatten_tree())
        self.assertEqual( elements.difference(['materials', 'clay', 'reeds', 'metal', 'stone', 'wood']), emptyset)
        
        gathered = self.rtree.find('gathered')
        elements = set(gathered.flatten_tree_concrete())
        self.assertEqual( elements.difference(['clay','reeds','metal','stone','wood','meat','fish','vegetables']), emptyset)
 
        abstract = self.rtree.find('abstract')
        elements = set(abstract.flatten_tree())
        self.assertIn( 'spirit', elements)
        self.assertIn( 'nothing', elements)
        self.assertNotIn( 'clay', elements)

class MockOrder(actor.BaseOrder):
    def __init__(self, actor_, limit):
        actor.BaseOrder.__init__(self, actor_)
        self.counter = 0
        self.limit = limit

    def do_step(self):
        self.counter += 1
        if self.counter >= self.limit:
            self.completed = True

class MockFailOrder(actor.BaseOrder):
    def do_step(self):
        self.valid = False

class MockStatefulOrder1(actor.StatefulSuperOrder):
    def __init__(self, actor_):
        actor.StatefulSuperOrder.__init__(self, actor_, 'state1')
        self.actor.donesies = False

    def start_state1(self):
        return MockOrder(self.actor, 1)

    def complete_state1(self):
        self.actor.donesies = True
        self.completed = True
    
class MockStatefulOrder2(actor.StatefulSuperOrder):
    def __init__(self, actor_):
        actor.StatefulSuperOrder.__init__(self, actor_, 'state1')
        self.actor.donesies = False

    def start_state1(self):
        return MockOrder(self.actor, 1)

class MockStatefulOrder3(actor.StatefulSuperOrder):
    def __init__(self, actor_):
        actor.StatefulSuperOrder.__init__(self, actor_, 'brood')    
        self.actor.mood = 'vacant'

    def start_brood(self):
        return MockOrder(self.actor, 1)
   
    def complete_brood(self):
        self.actor.mood = 'depressed'
        self.set_state('ponder')

    def start_ponder(self):
        return MockOrder(self.actor, 2)

    def complete_ponder(self):
        self.actor.mood = 'pensive'
        self.set_state('improve')

    def start_improve(self):
        return MockFailOrder(self.actor)

    def complete_improve(self):
        self.actor.mood = 'optimistic'
        self.set_state('take_action')

    def start_take_action(self):
        return MockOrder(self.actor, 1)

    def complete_take_action(self):
        self.actor.mood = 'satisfied'
        self.completed = True

class MockStatefulOrder4(MockStatefulOrder3):
    def fail_improve(self):
        self.actor.mood = 'determined'
        self.set_state('take_action')

class MockMultiMoveOrder(actor.StatefulSuperOrder):
    def __init__(self, actor_):
        actor.StatefulSuperOrder.__init__(self, actor_, 'move1')

    def start_move1(self):
        return actor.SimpleMoveOrder(self.actor, (3,0))

    def complete_move1(self):
        self.set_state('move2')

    def start_move2(self):
        return actor.SimpleMoveOrder(self.actor, (3,4))

    def complete_move2(self):
        self.set_state('move3')

    def start_move3(self):
        return actor.SimpleMoveOrder(self.actor, (0,0))

    def complete_move3(self):
        self.completed = True
    
class RevisedOrderTests(unittest.TestCase):
    def setUp(self):
        self.game = game.Game()
        self.actor = actor.Actor(self.game, (0,0))

    def test_simple_mock_order(self):
        mo = MockOrder(self.actor, 5)
        for i in range(5):
            self.assertFalse(mo.completed)
            self.assertTrue(mo.valid)
            mo.do_step()
        self.assertTrue(mo.valid)
        self.assertTrue(mo.completed)

    def test_stateful_order_mocked(self):
        mo = MockStatefulOrder1(self.actor)
        self.assertTrue(mo.valid)
        self.assertFalse(mo.completed)
        self.assertFalse( self.actor.donesies)
        mo.do_step()
        self.assertTrue(mo.valid)
        self.assertTrue(mo.completed)
        self.assertTrue( self.actor.donesies)

        #grind out some more steps to make sure it doesn't blow up
        for i in range(5):
            mo.do_step()

        mo = MockStatefulOrder2(self.actor)
        self.assertTrue(mo.valid)
        self.assertFalse(mo.completed)
        self.assertFalse( self.actor.donesies)
        mo.do_step()
        self.assertFalse(mo.valid)
        self.assertFalse(mo.completed)

        #grind out some more steps to make sure it doesn't blow up
        for i in range(5):
            mo.do_step()

        mo = MockStatefulOrder3(self.actor)
        self.assertEqual(self.actor.mood, 'vacant')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'depressed')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'depressed')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'pensive')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'pensive')
        self.assertFalse( mo.valid)
        self.assertFalse( mo.completed)

        #grind out some more steps to make sure it doesn't blow up
        for i in range(5):
            mo.do_step()

        mo = MockStatefulOrder4(self.actor)
        self.assertEqual(self.actor.mood, 'vacant')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'depressed')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'depressed')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'pensive')
        mo.do_step()
        self.assertEqual(self.actor.mood, 'determined')
        self.assertTrue( mo.valid)
        self.assertFalse( mo.completed)
        mo.do_step()
        self.assertEqual(self.actor.mood, 'satisfied')
        self.assertTrue( mo.valid)
        self.assertTrue( mo.completed)

        #grind out some more steps to make sure it doesn't blow up
        for i in range(5):
            mo.do_step()

    def test_simple_move_order(self):
        self.actor.position = (0,0)
        self.actor.move_speed = 0.5
        mo = actor.SimpleMoveOrder(self.actor, (5,0), 2.0)

        self.assertEqual( self.actor.position, (0,0))
        self.assertFalse( mo.completed)
        self.assertTrue( mo.valid)
        mo.do_step()
        self.assertFalse( mo.completed)
        self.assertTrue( mo.valid)
        self.assertEqual( self.actor.position, (1,0))
        mo.do_step()
        self.assertEqual( self.actor.position, (2,0))
        self.assertFalse( mo.completed)
        self.assertTrue( mo.valid)
        mo.do_step()
        self.assertEqual( self.actor.position, (3,0))
        self.assertFalse( mo.completed)
        self.assertTrue( mo.valid)
        mo.do_step()
        self.assertEqual( self.actor.position, (4,0))
        self.assertFalse( mo.completed)
        self.assertTrue( mo.valid)
        mo.do_step()
        self.assertEqual( self.actor.position, (5,0))
        self.assertTrue( mo.completed)
        self.assertTrue( mo.valid)


    def test_stateful_move_order(self):
        self.actor.position = (0,0)
        self.actor.move_speed = 1.0

        mo = MockMultiMoveOrder(self.actor)
    
        for i in range(3):
            mo.do_step()

        self.assertTrue(mo.valid)
        self.assertFalse(mo.completed)
        self.assertEqual(self.actor.position, (3,0))

        for i in range(4):
            mo.do_step()

        self.assertTrue(mo.valid)
        self.assertFalse(mo.completed)
        self.assertEqual(self.actor.position, (3,4))

        for i in range(5):
            mo.do_step()

        self.assertTrue(mo.valid)
        self.assertTrue(mo.completed)
        self.assertEqual(self.actor.position, (0,0))

class GameResourceSeekTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_find_forage(self):
        self.game = game.Game()

        #dummy storage, this should not show up in find_forage
        testobj = game.StructureObject(self.game, (100,100), (125, -125), 4)
        testobj.target_actions = testobj.target_actions.union(['butcher', 'enlist'])
        testobj.set_storage(1, ('stone', 'wood'))
        self.game.add_game_object(testobj)
        self.game.update()

        self.assertIsNone(self.game.find_forage((0,0), 'stone', 1))

        store1 = game.StructureObject(self.game, (100,100), (-200, 170), 1)
        store1.target_actions = store1.target_actions.union(['mine'])
        store1.set_reservoir(2, 'stone', 0)
        self.game.add_game_object(store1)

        store2 = game.StructureObject(self.game, (100,100), (100, 100), 1)
        store2.target_actions = store2.target_actions.union(['mine'])
        store2.set_reservoir(2, 'wood', 0)
        self.game.add_game_object(store2)

        target = self.game.find_forage((0,0), 'stone', 1)
        self.assertEqual(target, store1)

        target = self.game.find_forage((0,0), 'wood', 1)
        self.assertEqual(target, store2)

        store3 = game.StructureObject(self.game, (100,100), (-10, -10), 1)
        store3.target_actions = store3.target_actions.union(['mine'])
        store3.set_reservoir(2, 'stone', 0)
        self.game.add_game_object(store3)

        target = self.game.find_forage((0,0), 'stone', 1)
        self.assertEqual(target, store3)
        
def run_tests(hard_fail=False):
    res = unittest.main(module=__name__, exit=False, failfast=hard_fail)
    
    count = res.result.errors + res.result.failures
    if hard_fail and count > 0:
        print "Hard failure, bailing out. There may be more failures"
        exit()
    
if __name__ == '__main__':
    run_tests()        
