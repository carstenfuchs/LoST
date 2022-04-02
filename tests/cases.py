from unittest import TestCase

from lost import settings
from lost.server import start_testserver


class BuiltinServerTestCase(TestCase):
    """A test case that runs our built-in server in the background."""

    @classmethod
    def setUpClass(cls):
        assert settings.SERVER_ADDRESS[0] == 'built-in'
        cls._httpd = start_testserver(settings.SERVER_ADDRESS[1])

    @classmethod
    def tearDownClass(cls):
        cls._httpd.shutdown()
        cls._httpd.server_close()
