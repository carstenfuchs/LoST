from enum import Enum
from lost.modes.base_terminal import BaseTerminal


class State(Enum):
    """The basic states that a terminal can enter."""

    WELCOME = 1
    WAIT_FOR_SERVER_REPLY = 2
    DISPLAY_SERVER_REPLY = 3
    SYSTEM_PANEL = 4


USER_INPUT_STATES = (
    State.WELCOME,
    State.SYSTEM_PANEL,
)


class Terminal(BaseTerminal):
    """This class represents a terminal for office personnel."""

    def __init__(self):
        super().__init__()
        self._set_state(State.WELCOME)

    def _set_state(self, state):
        self.state = state
        self.pause = None
        self.last_server_reply = None

    def get_user_input(self):
        return {
            'pause': self.pause,
        }

    def set_state(self, state):
        if state in USER_INPUT_STATES:
            self._set_state(state)
            self.notify_observers()

    def set_state_welcome(self):
        self._set_state(State.WELCOME)
        self.notify_observers()

    def set_state_system_panel(self):
        self._set_state(State.SYSTEM_PANEL)
        self.notify_observers()

    def set_pause(self, pause):
        self.pause = pause
        self.notify_observers()

    def is_expecting_smartcard(self):
        # Overrides the method in the parent class.
        return self.state in USER_INPUT_STATES

    def on_server_post_sent(self):
        # Overrides the method in the parent class.
        self.set_state(State.WAIT_FOR_SERVER_REPLY)

    def on_server_reply_received(self, reply):
        # Overrides the method in the parent class.
        self._set_state(State.DISPLAY_SERVER_REPLY)
        self.last_server_reply = reply
        self.notify_observers()
