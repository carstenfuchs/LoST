from unittest import TestCase
from lost.modes.office_terminal import State, Terminal


class TestOfficeTerminal(TestCase):

    def test_new_terminal(self):
        terminal = Terminal()

        self.assertEqual(terminal.state, State.WELCOME)
        self.assertIsNone(terminal.pause)
        self.assertIsNone(terminal.last_server_reply)
