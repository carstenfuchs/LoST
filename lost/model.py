from enum import Enum


class Intention(Enum):
    """The overall intention for which the terminal is used."""
    ARBEITS_ANFANG = 1
    ARBEITS_ANFANG_SCHICHT = 2
    ARBEITS_ANFANG_JETZT = 3
    ARBEITS_ENDE = 4


class Model:

    def __init__(self, root_window):
        self.root_window = root_window
        self.is_updating = False

        self.intention = None
        self.department = None
        self.pause = None

    def set_intention(self, intention):
        self.intention = intention
        self.department = None
        self.pause = None
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
