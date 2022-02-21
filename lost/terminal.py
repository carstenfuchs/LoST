from enum import Enum
import time


class State(Enum):
    """The basic states that a terminal can enter."""

    WELCOME = 1
    ENTER_START_OF_WORK_DETAILS = 2
    ENTER_END_OF_WORK_DETAILS = 3
    WAIT_FOR_SERVER_REPLY = 4
    DISPLAY_SERVER_REPLY = 5


USER_INPUT_STATES = (
    State.WELCOME,
    State.ENTER_START_OF_WORK_DETAILS,
    State.ENTER_END_OF_WORK_DETAILS,
)


class Terminal:
    """
    This class represents a terminal, modeling its complete internal state.

    In the MVC pattern, this is the model.
    It must deal with many types and sources of input: events from the GUI,
    the RFID reader, incoming network messages, timers, special hardware (e.g.
    from the RPi's GPIO pins), etc.
    (In a sense, the model is itself a listener to input event providers.)
    """

    def __init__(self, root_window):
        # Note that we should properly employ the Observer pattern rather than
        # taking the `root_window` here: The terminal model might have a lot
        # more observers than only that, e.g. LED lights on the RPi or the RFID
        # reader, audio outputs, door openers, etc.
        self.root_window = root_window
        self.is_updating = False
        self._set_state(State.WELCOME)
        self.time_last_action = time.time()

    def _set_state(self, state):
        self.state = state
        self.sow_type = None
        self.department = None
        self.pause = None

    def set_state(self, state):
        # This function is only to be called from the touch screen GUI.
        if state in USER_INPUT_STATES:
            self._set_state(state)
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

    def process_RFID_tag_input(self, key):
        if self.state not in USER_INPUT_STATES:
            # Ignore any RFID tag input if we are not expecting any.
            return

        # TODO: Send message to server ...
        self._set_state(State.WAIT_FOR_SERVER_REPLY)
        self.time_last_action = time.time()
        self.notify_observers()

    def process_server_reply(self, msg):
        # self.last_server_message = msg
        self._set_state(State.DISPLAY_SERVER_REPLY)
        self.time_last_action = time.time()
        self.notify_observers()

    def notify_observers(self):
        # Make sure that we don't accidentally enter infinite recursion.
        assert not self.is_updating
        self.is_updating = True
        self.root_window.update_to_model(self)
        self.is_updating = False
