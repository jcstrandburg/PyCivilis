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
        
def run_tests(hard_fail=False):
    res = unittest.main(module=__name__, exit=False, failfast=hard_fail)
    
    count = res.result.errors + res.result.failures
    if hard_fail and count > 0:
        print "Hard failure, bailing out. There may be more failures"
        exit()
    
if __name__ == '__main__':
    run_tests()        