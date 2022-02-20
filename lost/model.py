from enum import Enum


class State(Enum):
    """The basic states that a terminal can enter."""

    WELCOME = 1
    ENTER_START_OF_WORK_DETAILS = 2
    ENTER_END_OF_WORK_DETAILS = 3


class Model:
    """
    This class represents a terminal, modeling its complete internal state.
    In the MVC pattern, this is the model.
    """

    def __init__(self, root_window):
        self.root_window = root_window
        self.is_updating = False

        self.state = State.WELCOME
        self.sow_type = None
        self.department = None
        self.pause = None

    def set_state(self, state):
        self.state = state
        self.sow_type = None
        self.department = None
        self.pause = None
        self.notify_observers()

    def set_sow_type(self, sow):
        assert sow in (None, 'schicht', 'jetzt')
        self.sow_type  = sow
        self.notify_observers()

    def set_department(self, dept):
        self.department = dept
        self.notify_observers()

    def set_pause(self, pause):
        self.pause = pause
        self.notify_observers()

    def notify_observers(self):
        # Make sure that we don't accidentally enter infinite recursion.
        assert not self.is_updating
        self.is_updating = True
        self.root_window.update_to_model(self)
        self.is_updating = False
