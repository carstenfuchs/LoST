from enum import Enum
import time
from modes.base_terminal import BaseTerminal


class State(Enum):
    """The basic states that a terminal can enter."""

    WELCOME = 1
    ENTER_START_OF_WORK_DETAILS = 2
    ENTER_END_OF_WORK_DETAILS = 3
    WAIT_FOR_SERVER_REPLY = 4
    DISPLAY_SERVER_REPLY = 5
    SYSTEM_PANEL = 6


USER_INPUT_STATES = (
    State.WELCOME,
    State.ENTER_START_OF_WORK_DETAILS,
    State.ENTER_END_OF_WORK_DETAILS,
)


class Terminal(BaseTerminal):
    """This class represents a terminal for logistics personnel."""

    def __init__(self):
        super().__init__()
        self._set_state(State.WELCOME)
        self.time_last_action = time.time()

    def _set_state(self, state):
        self.state = state
        self.sow_type = None
        self.department = None
        self.pause = None
        self.last_server_reply = None

    def set_state(self, state):
        # This function is only to be called from the touch screen GUI.
        # TODO: This is not quite true – also the smartcard reader is a kind of GUI!
        if state in USER_INPUT_STATES:
            self._set_state(state)
            self.time_last_action = time.time()
            self.notify_observers()

    def set_state_welcome(self):
        self._set_state(State.WELCOME)
        self.time_last_action = time.time()
        self.notify_observers()

    def set_state_system_panel(self):
        self._set_state(State.SYSTEM_PANEL)
        self.time_last_action = time.time()
        self.notify_observers()

    def set_sow_type(self, sow):
        assert sow in (None, 'schicht', 'jetzt')
        self.sow_type  = sow
        self.time_last_action = time.time()
        self.notify_observers()

    def set_department(self, dept):
        self.department = dept
        self.time_last_action = time.time()
        self.notify_observers()

    def set_pause(self, pause):
        self.pause = pause
        self.time_last_action = time.time()
        self.notify_observers()

    def process_clocktick(self):
        time_idle = time.time() - self.time_last_action
        if time_idle > 30.0:
            self._set_state(State.WELCOME)
            self.time_last_action = time.time()
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
        self.time_last_action = time.time()
        self.notify_observers()
