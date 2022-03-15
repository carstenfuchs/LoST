from enum import Enum
import time


class State(Enum):
    """The basic states that a terminal can enter."""

    WELCOME = 1
    WAIT_FOR_SERVER_REPLY = 2
    DISPLAY_SERVER_REPLY = 3


USER_INPUT_STATES = (
    State.WELCOME,
)


class Terminal:
    """
    This class represents a terminal, modeling its internal state.

    In the MVC pattern, this is the model.
    It must deal with many types and sources of input: events from the GUI,
    the RFID reader, incoming network messages, timers, special hardware (e.g.
    from the RPi's GPIO pins), etc.
    (In a sense, the model is itself a listener to input event providers.)
    """

    def __init__(self):
        self._observers = []
        self.is_updating = False
        self._set_state(State.WELCOME)

    def add_observer(self, obs):
        self._observers.append(obs)

    def clear_observers(self):
        self._observers.clear()

    def _set_state(self, state):
        self.state = state
        self.pause = None
        self.last_server_reply = None

    def expect_smartcard(self):
        return self.state in USER_INPUT_STATES

    def set_state(self, state):
        if state in USER_INPUT_STATES:
            self._set_state(state)
            self.notify_observers()

    def set_state_Wait_For_Sv_Reply(self):
        # The only reason for this function is so that the sm_mon doesn't need to import the State constants
        self.set_state(State.WAIT_FOR_SERVER_REPLY)

    def set_pause(self, pause):
        self.pause = pause
        self.notify_observers()

    def on_server_reply(self, msg):
        self._set_state(State.DISPLAY_SERVER_REPLY)
        self.last_server_reply = msg
        self.notify_observers()

    def notify_observers(self):
        # Make sure that we don't accidentally enter infinite recursion.
        assert not self.is_updating
        self.is_updating = True
        for obs in self._observers:
            obs.update_to_model(self)
        self.is_updating = False
