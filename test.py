#!/usr/bin/env python3
import unittest
from lost import settings


settings.DEBUG = True
settings.SERVER_ADDRESS
# LOGFILE_PATH = Path(__file__).resolve().parent.parent / 'lost.log'
settings.TERMINAL_MODE = 'logistics'
settings.TERMINAL_NAME = 'Buchhaltung'
settings.TERMINAL_PASSWORD = "vf6r4cnf3 password for testing only, don't use!"
settings.SERVER_ADDRESS = ('built-in', 38004)
settings.SERVER_URL = '/stempeluhr/event/submit/'


# python -m unittest discover --start-directory tests

loader = unittest.TestLoader()
test_name = None
# test_name = "tests.test_class_NetworkHandler.Test_post_stamp_event.test_no_connection"

if test_name:
    suite = loader.loadTestsFromName(test_name)
else:
    start_dir = 'tests'
    suite = loader.discover(start_dir)

runner = unittest.TextTestRunner()
runner.run(suite)
