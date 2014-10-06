import unittest

import resource

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
        
        store.deposit({'type':'stone', 'qty':4})
        self.assertEqual(store.get_available_contents('stone'), 4)        
        res1 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), 3)
        res2 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), 2)
        res3 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), 1)        
        res4 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), 0)      
        res5 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), -1)
        res6 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), -2)
        res7 = store.reserve_resources('stone', 1)
        self.assertEqual(store.get_available_contents('stone'), -3)

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
        self.assertEqual(store.get_available_contents('stone'), -2)
        self.assertTrue(res5.ready)
        self.assertFalse(res6.ready)
        self.assertFalse(res7.ready)
        
        res1.release()
        store.update()
        self.assertEqual(store.get_available_contents('stone'), -1)        
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

    '''
    Testing ideas:
    
    I nixed overlapping acceptance sets.'''        
        
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
 
        print "store1 reservations"
        print store1._resource_reservations
        print "store2 reservations"
        print store2._resource_reservations
        
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
        #self.assertEqual( store.get_available_contents(all), 6)
        self.assertEqual( store1.get_available_contents(food), 0)
        #self.assertEqual( store2.get_available_contents(food), 1)        
        #self.assertEqual( store.get_available_contents(food), 1)
        self.assertEqual( store1.get_available_contents(materials), 5)
        #self.assertEqual( store2.get_available_contents(materials), 0)        
        #self.assertEqual( store.get_available_contents(materials), 5)
        self.assertEqual( store1.get_available_contents(misc1), 0)
        #self.assertEqual( store2.get_available_contents(misc1), 0)        
        #self.assertEqual( store.get_available_contents(misc1), 0)
        self.assertEqual( store1.get_available_contents(misc2), 3)
        #self.assertEqual( store2.get_available_contents(misc2), 1)        
        #self.assertEqual( store.get_available_contents(misc2), 4)
        self.assertEqual( store1.get_available_contents(misc3), 3)
        #self.assertEqual( store2.get_available_contents(misc3), 0)        
        #self.assertEqual( store.get_available_contents(misc3), 3)        
        
        
        
    '''def test_resource_subtypes1(self):
        store = resource.ResourceStore(None, 10, ['food', 'materials'])
        store.deposit( {'type':'meat', 'qty': 2})
        store.deposit( {'type':'fish', 'qty': 1})
        store.deposit( {'type':'metal', 'qty': 3})
        store.deposit( {'type':'reeds', 'qty': 3})
        self.assertEqual( store.get_actual_contents( 'food'), 3)
        self.assertEqual( store.get_actual_contents( 'fish'), 1)
        self.assertEqual( store.get_actual_contents( 'clay'), 0)
        self.assertEqual( store.get_actual_contents( 'materials'), 3)
        self.assertEqual( store.get_available_space( 'food'), 1)
        self.assertEqual( store.get_available_space( 'materials'), 1)
        self.assertEqual( store.get_available_space( 'meat'), 1)
        self.assertEqual( store.get_available_space( 'metal'), 1)
        self.assertEqual( store.get_available_space( 'weapons'), 0)

    def test_resource_subtypes2(self):
        store = resource.ResourceStore(None, 10, ['resource'])
        store.deposit({'type':'clay', 'qty':2})
        self.assertEqual( store.get_available_contents( 'resource'), 2)
        self.assertEqual( store.get_available_contents( 'gathered'), 2)
        self.assertEqual( store.get_available_contents( 'materials'), 2)
        self.assertEqual( store.get_available_contents( 'clay'), 2)
        self.get_actual_contents( store.get_available_space( 'clay'), 8)
        self.get_actual_contents( store.get_available_space( 'weapons'), 8)
        self.get_actual_contents( store.get_available_space( 'resource'), 8)
        self.get_actual_contents( store.get_available_space( 'meat'), 8)
        self.get_actual_contents( store.get_available_space( 'gathered'), 8)
        self.get_actual_contents( store.get_available_space( 'resource'), 8)
        self.get_actual_contents( store.get_available_space( 'materials'), 8)

    def test_subtype_transactions(self):
        store = resource.ResourceStore(None, 10, ['resource'])
        self.assertFalse( store.deposit({'type':'materials', 'qty':1}))
        self.assertFalse( store.deposit({'type':'gathered', 'qty':1}))
        self.assertFalse( store.deposit({'type':'food', 'qty':1}))
        self.assertTrue( store.deposit({'type':'clay', 'qty':1}))
        self.assertIsNone( store.withdraw('resource', 1))
        self.assertIsNone( store.withdraw('gathered', 1))
        self.assertIsNone( store.withdraw('materials', 1))
        self.assertIsNone( store.withdraw('clay', 1))'''

class ResourceTree(unittest.TestCase):
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
        
        
        
        
        
        
def run_tests(hard_fail=False):
    res = unittest.main(module=__name__, exit=False, failfast=hard_fail)
    
    count = res.result.errors + res.result.failures
    if hard_fail and count > 0:
        print "Hard failure, bailing out. There may be more failures"
        exit()
    
if __name__ == '__main__':
    run_tests()        
