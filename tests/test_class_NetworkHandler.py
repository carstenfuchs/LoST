from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase
import json, logging, tempfile

from lost import common, network_handler, settings
from lost.network_handler import post_stamp_event, NetworkHandler
from lost.modes.base_terminal import BaseTerminal
from lost.thread_tools import thread_queue
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
        expected.update(
            {
                "is_backlog": "False",
                "terminal_name": "Buchhaltung",
                "terminal_pwd": "vf6r4cnf3 password for testing only, don't use!",
                "echo_server_note": "This reply is an echo of the received data, plus this message.",
            }
        )
        del expected['pause']

        self.assertEqual(result, expected)
        self.assertIs(network_success, True)


class TestTerminal(BaseTerminal):
    """A minimal implementation of the `BaseTerminal`, just as required for tests."""

    def get_user_input(self):
        return {
            'department': "Test Labs",
            'pause': 30,
        }

    def on_server_reply_received(self, reply):
        self.last_server_reply = reply


class Test_NetworkHandler_sending(BuiltinServerTestCase):
    """
    A test case for the sending-related portions of the `NetworkHandler` class.

    This requires dealing with the thread for `post_stamp_event()` and the test echo
    server in order to learn and verify the actually sent data.
    """

    def setUp(self):
        common.FAKE_DATETIME_FOR_TESTS = datetime(2022, 4, 2, 18, 12, 00)
        common.FAKE_TIMETIME_FOR_TESTS = 3

        backlog_path = Path(tempfile.gettempdir()) / "tmp_LoST_test_backlog.db"
        backlog_path.unlink(missing_ok=True)

        self.trm = TestTerminal()
        self.nwh = NetworkHandler(self.trm, backlog_path=str(backlog_path))
        assert thread_queue.empty()

    def tearDown(self):
        self.nwh.shutdown()
        common.FAKE_DATETIME_FOR_TESTS = None
        common.FAKE_TIMETIME_FOR_TESTS = None

    def test_simple_round_trip(self):
        with self.assertLogs(logger='lost', level=logging.DEBUG) as cm:
            self.nwh.send_to_Lori("brand-new smartcard")

        self.assertEqual(
            cm.output,
            [
                "INFO:lost.network:send_to_Lori():",
                "INFO:lost.network:    user_input = {'smartcard_id': 'brand-new smartcard', 'local_ts': '2022-04-02 18:12:00', 'department': 'Test Labs', 'pause': 30}",
            ],
        )

        callback, args = thread_queue.get(block=True)
        (user_input, result, network_success) = args

        # The `user_input` was assembled in `send_to_Lori()`, passed into the
        # `post_stamp_event()` thread and passed back from it unchanged, just in case
        # it must be put into the backlog.
        self.assertEqual(
            user_input,
            {
                # These were directly from `send_to_Lori()`.
                'smartcard_id': "brand-new smartcard",
                'local_ts': "2022-04-02 18:12:00",
                # These were added by the terminal's `get_user_input()`.
                'department': "Test Labs",
                'pause': 30,
            }
        )

        # The `result` is the received data from our test server, which just echoes
        # whatever it received. Note the strings even for numbers and booleans.
        self.assertEqual(
            result,
            {
                # These were directly from `send_to_Lori()`.
                'smartcard_id': "brand-new smartcard",
                'local_ts': "2022-04-02 18:12:00",
                # These were added by the terminal's `get_user_input()`.
                'department': "Test Labs",
                'pause': '30',
                # These were added by the `post_stamp_event()` function.
                'terminal_name': "Buchhaltung",
                'terminal_pwd': "vf6r4cnf3 password for testing only, don't use!",
                'is_backlog': 'False',
                # This was added by the echo server.
                'echo_server_note': "This reply is an echo of the received data, plus this message.",
            }
        )

        self.assertEqual(callback, self.nwh.on_server_reply)
        self.assertIs(network_success, True)

    def test_throttling_sends_and_threads(self):
        with self.assertLogs(logger="lost", level=logging.DEBUG) as cm:
            self.nwh.send_to_Lori("brand-new smartcard")
            callback, args = thread_queue.get(block=True)

            common.FAKE_DATETIME_FOR_TESTS += timedelta(seconds=0.4)
            common.FAKE_TIMETIME_FOR_TESTS += 0.4
            self.nwh.send_to_Lori("brand-new smartcard")

            common.FAKE_DATETIME_FOR_TESTS += timedelta(seconds=0.2)
            common.FAKE_TIMETIME_FOR_TESTS += 0.2
            self.nwh.send_to_Lori("brand-new smartcard")
            callback, args = thread_queue.get(block=True)

        self.assertEqual(
            cm.output,
            [
                "INFO:lost.network:send_to_Lori():",
                "INFO:lost.network:    user_input = {'smartcard_id': 'brand-new smartcard', 'local_ts': '2022-04-02 18:12:00', 'department': 'Test Labs', 'pause': 30}",
                "ERROR:lost.network:send_to_Lori(): Throttling network transmissions, dropping smartcard_id = 'brand-new smartcard'!",
                "ERROR:lost.network:    self.time_last_sending = 3, now = 3.4",
                "INFO:lost.network:send_to_Lori():",
                "INFO:lost.network:    user_input = {'smartcard_id': 'brand-new smartcard', 'local_ts': '2022-04-02 18:12:00.600000', 'department': 'Test Labs', 'pause': 30}",
            ],
        )

    def test_too_early_for_backlog(self):
        tnb = common.FAKE_TIMETIME_FOR_TESTS + 1.0
        self.nwh.time_next_backlog = tnb
        self.nwh.catch_up_backlog()
        self.assertEqual(self.nwh.time_next_backlog, tnb)

    def test_backlog_is_empty(self):
        with self.assertLogs(logger="lost", level=logging.DEBUG) as cm:
            self.nwh.catch_up_backlog()

        self.assertEqual(
            cm.output,
            [
                "INFO:lost.network:catch_up_backlog(): The backlog is empty.",
            ],
        )
        self.assertEqual(len(self.nwh.backlog), 0)
        self.assertEqual(self.nwh.time_next_backlog, 86403)

    def test_backlog_has_invalid_item(self):
        self.nwh.backlog['some_unique_id'] = ">>> invalid JSON <<<"

        with self.assertLogs(logger="lost", level=logging.DEBUG) as cm:
            self.nwh.catch_up_backlog()

        self.assertEqual(
            cm.output,
            [
                "ERROR:lost.network:catch_up_backlog(): Invalid JSON in backlog: Expecting value: line 1 column 1 (char 0)",
                "ERROR:lost.network:    backlog['some_unique_id'] = '>>> invalid JSON <<<'",
            ],
        )
        self.assertEqual(len(self.nwh.backlog), 0)
        self.assertEqual(self.nwh.time_next_backlog, 3 + 1)

    def test_backlog_round_trip(self):
        backlogged_user_input = {
            'str_value': "a string value",
            'int_value': 1234,
            'bool_value': True,
            'float_value': 3.1415926,
        }
        self.nwh.backlog['some_unique_id'] = json.dumps(backlogged_user_input)

        with self.assertLogs(logger="lost", level=logging.DEBUG) as cm:
            self.nwh.catch_up_backlog()

        # Note how the int, bool and float types survived the conversion to and from JSON!
        self.assertEqual(
            cm.output,
            [
                "INFO:lost.network:catch_up_backlog():",
                "INFO:lost.network:    user_input = {'str_value': 'a string value', 'int_value': 1234, 'bool_value': True, 'float_value': 3.1415926}",
            ],
        )
        self.assertEqual(len(self.nwh.backlog), 0)
        self.assertEqual(self.nwh.time_next_backlog, 3 + 16)

        callback, args = thread_queue.get(block=True)
        (user_input, result, network_success) = args

        # What went into the backlog made it well to the server (and back).
        self.assertEqual(user_input, backlogged_user_input)

        # The `result` is the received data from our test server, which just echoes
        # whatever it received. Note the strings even for numbers and booleans.
        self.assertEqual(
            result,
            {
                # These were from the backlog.
                'str_value': "a string value",
                'int_value': '1234',
                'bool_value': 'True',
                'float_value': '3.1415926',
                # These were added by the `post_stamp_event()` function.
                'terminal_name': "Buchhaltung",
                'terminal_pwd': "vf6r4cnf3 password for testing only, don't use!",
                'is_backlog': 'True',
                # This was added by the echo server.
                'echo_server_note': "This reply is an echo of the received data, plus this message.",
            }
        )

        self.assertEqual(callback, self.nwh.on_server_reply)
        self.assertIs(network_success, True)


class Test_NetworkHandler_other(TestCase):
    """
    A test case for all other (non-sending-related) portions of the `NetworkHandler` class.

    These tests neither require a testing server running in the background nor dealing with
    any thread-related issues.
    """

    def setUp(self):
        common.FAKE_DATETIME_FOR_TESTS = datetime(2022, 4, 2, 18, 12, 00)
        common.FAKE_TIMETIME_FOR_TESTS = 3

        self.backlog_path = Path(tempfile.gettempdir()) / "tmp_LoST_test_backlog.db"
        self.backlog_path.unlink(missing_ok=True)

        self.trm = TestTerminal()
        self.nwh = NetworkHandler(self.trm, backlog_path=str(self.backlog_path))

    def tearDown(self):
        self.nwh.shutdown()
        common.FAKE_DATETIME_FOR_TESTS = None
        common.FAKE_TIMETIME_FOR_TESTS = None

    def test_backlog_persistency(self):
        s = "This must still be there in a new `NetworkHandler` instance!"
        self.nwh.backlog['is persistent'] = s
        self.nwh.shutdown()
        self.nwh = NetworkHandler(self.trm, backlog_path=str(self.backlog_path))

        self.assertEqual(self.nwh.backlog['is persistent'], s.encode())

    def test_successful_server_reply(self):
        user_input = "not used in this test"
        result = "passed to the terminal"
        success = True

        with self.assertLogs(logger="lost", level=logging.DEBUG) as cm:
            self.nwh.on_server_reply(user_input, result, success)

        self.assertEqual(
            cm.output,
            [
                "INFO:lost.network:on_server_reply():",
                "INFO:lost.network:    network_success = True",
                "INFO:lost.network:    user_input = 'not used in this test'",
                "INFO:lost.network:    result = 'passed to the terminal'",
            ],
        )
        self.assertEqual(self.trm.last_server_reply, result)
