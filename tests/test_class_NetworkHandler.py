from lost import network_handler, settings
from lost.network_handler import post_stamp_event #, NetworkHandler
from tests.cases import BuiltinServerTestCase


class Test_post_stamp_event(BuiltinServerTestCase):
    """A test case for the `post_stamp_event()` function."""

    def send_post(self):
        user_in={
            'smartcard_id': 'brand-new smartcard',
            'local_ts': '2022-03-30 16:56:37.157814',
            'pause': None,
        }

        user_out, result, network_success = post_stamp_event(
            user_input=user_in,
            is_backlog=False,
        )

        # The `post_stamp_event()` function always returns the user input that it got
        # in the first place. This is necessary because it usually runs within a thread
        # and the user input must still be known when the thread returns.
        self.assertEqual(user_out, user_in)

        return user_out, result, network_success

    def test_no_connection(self):
        old_address = settings.SERVER_ADDRESS
        settings.SERVER_ADDRESS = ('unknownhost', 80)

        user_out, result, network_success = self.send_post()
        settings.SERVER_ADDRESS = old_address

        self.assertEqual(list(result.keys()), ['error'])
        self.assertIn("ConnectionError:", result['error'])
        self.assertIn("Failed to establish a new connection: [Errno -2] Name or service not known", result['error'])
        self.assertIs(network_success, False)

    def test_bad_port(self):
        old_address = settings.SERVER_ADDRESS
        settings.SERVER_ADDRESS = ('localhost', 9999)

        user_out, result, network_success = self.send_post()
        settings.SERVER_ADDRESS = old_address

        self.assertEqual(list(result.keys()), ['error'])
        self.assertIn("ConnectionError:", result['error'])
        self.assertIn("Failed to establish a new connection: [Errno 111] Connection refused", result['error'])
        self.assertIs(network_success, False)

    def test_timeout(self):
        old_timeout = network_handler.REQUEST_TIMEOUT
        network_handler.REQUEST_TIMEOUT = 0.001
        old_url = settings.SERVER_URL
        settings.SERVER_URL = '/timeout/'

        user_out, result, network_success = self.send_post()
        network_handler.REQUEST_TIMEOUT = old_timeout
        settings.SERVER_URL = old_url

        self.assertEqual(list(result.keys()), ['error'])
        self.assertIn("Timeout:", result['error'])
        self.assertIn("Read timed out. (read timeout=0.001)", result['error'])
        self.assertIs(network_success, False)

    def test_RequestException(self):
        old_address = settings.SERVER_ADDRESS
        settings.SERVER_ADDRESS = ('', 80)

        user_out, result, network_success = self.send_post()
        settings.SERVER_ADDRESS = old_address

        self.assertEqual(list(result.keys()), ['error'])
        self.assertIn("RequestException: Invalid URL", result['error'])
        self.assertIn("No host supplied", result['error'])
        self.assertIs(network_success, False)

    def test_redirect(self):
        old_url = settings.SERVER_URL
        settings.SERVER_URL = '/old/path/now/redirected/'

        user_out, result, network_success = self.send_post()
        settings.SERVER_URL = old_url

        self.assertEqual(result, {'success': 'The redirect went well!'})
        self.assertIs(network_success, True)

    def test_wrong_url_404(self):
        """Even if the server is accessible, the URL might still not exist."""
        old_url = settings.SERVER_URL
        settings.SERVER_URL = '/wrong/path/'

        user_out, result, network_success = self.send_post()
        settings.SERVER_URL = old_url

        self.assertEqual(list(result.keys()), ['error'])
        self.assertIn("The HTTP status response code was 404, expected 200 (OK).", result['error'])
        self.assertIs(network_success, False)

    def test_unexpected_reply(self):
        """Even if we receive a reply, it might be something that is not JSON, e.g. HTML."""
        old_url = settings.SERVER_URL
        settings.SERVER_URL = '/non-json-reply/'

        user_out, result, network_success = self.send_post()
        settings.SERVER_URL = old_url

        self.assertEqual(list(result.keys()), ['error'])
        self.assertIn("JSONDecodeError:", result['error'])
        self.assertIs(network_success, False)

    def test_all_OK(self):
        """Makes sure that a plain round-trip without errors is possible."""
        user_out, result, network_success = self.send_post()

        # The test server just echoes the received data.
        # Note that the `pause` was never sent and that value `False` was turned into a string.
        expected = user_out.copy()
        expected.update({'is_backlog': "False", 'terminal_name': "Buchhaltung", 'terminal_pwd': "vf6r4cnf3 password for testing only, don't use!"})
        del expected['pause']

        self.assertEqual(result, expected)
        self.assertIs(network_success, True)
