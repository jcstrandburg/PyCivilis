import sys
import src.rungame
import src.unittests
import cProfile

src.unittests.run_tests(False)
src.rungame.run()
#do_profile()
