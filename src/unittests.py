import unittest, re

class SimpleTest(unittest.TestCase):
    
    def test_something(self):
        self.assertTrue(True)
    
    def test_somewhere(self):
        self.assertGreater(5, 3, "It's higher")

    def test_someone(self):
        self.assertLess(5, 7, "It's higher")

class OtherSimpleTest(unittest.TestCase):
    def test_1(self):
        self.assertFalse(False)

    def test_2(self):
        self.assertTrue(True, "Hey dummy")



        
def run_tests(hard_fail=False):
    res = unittest.main(module=__name__, exit=False, failfast=hard_fail)
    
    count = res.result.errors + res.result.failures
    if hard_fail and count > 0:
        print "Hard failure, bailing out. There may be more failures"
        exit()
    
if __name__ == '__main__':
    run_tests()        