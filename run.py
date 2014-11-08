import sys
import cProfile
import os.path
import src.rungame
import src.unittests
import res.make_trans


if not os.path.isfile("res/trans/trans_000.png"):
    res.make_trans.main('res/', 'res/trans/')

src.unittests.run_tests(True)
src.rungame.run()
#do_profile()
