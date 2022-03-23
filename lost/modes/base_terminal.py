from enum import Enum
import time


class BaseTerminal:
    """
    This class represents a terminal, modeling its internal state.

    In the MVC pattern, this is the “model”. It is modified by external “controllers”
    whenever they received an event that should lead to a new state. Examples include
    events in the GUI, captures in the smartcard reader or incoming server replies.
    Arbitrary other input providers such as the Raspberry Pi's GPIO pins, fingerprint
    sensors etc. are possible as well.

    Changes in the state of the terminal are communicated to all interested parties
    (the views) that have registered themselves as observers of the terminal.

    Some of the methods are intended for user code that is oblivious of the concrete
    terminal class it is dealing with, for example the `SmartcardMonitor` or the
    `NetworkHandler`. Child classes are expected to override these methods.
    """

    def __init__(self):
        self._observers = []
        self._is_updating = False

    def add_observer(self, obs):
        self._observers.append(obs)

    def clear_observers(self):
        self._observers.clear()

    def notify_observers(self):
        # Make sure that we don't accidentally enter infinite recursion.
        assert not self._is_updating
        self._is_updating = True
        for obs in self._observers:
            obs.update_to_model(self)
        self._is_updating = False

    def get_user_input(self):
        # Child classes are expected to override this method!
        return {}

    def set_state_welcome(self):
        # Child classes are expected to override this method!
        pass

    def set_state_system_panel(self):
        # Child classes are expected to override this method!
        pass

    def is_expecting_smartcard(self):
        # Child classes are expected to override this method!
        return False

    def on_server_post_sent(self):
        # Child classes are expected to override this method!
        pass

    def on_server_reply_received(self, reply):
        # Child classes are expected to override this method!
        pass
