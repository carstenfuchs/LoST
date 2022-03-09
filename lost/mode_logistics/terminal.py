from datetime import datetime
from enum import Enum
import time
import requests

import settings
from thread_tools import start_thread


def post_stamp_event(smartcard_name):
    """Sends the smartcard details in a POST request to the server."""
    SERVER_NAME = settings.SERVER_ADDRESS[0]
    SERVER_PORT = settings.SERVER_ADDRESS[1]

    if SERVER_NAME == 'built-in':
        SERVER_NAME = 'localhost'

    try:
        r = requests.post(
            f"http://{SERVER_NAME}:{SERVER_PORT}{settings.SERVER_URL}",
            data={
                'terminal_name': settings.TERMINAL_NAME,
                'pwd': settings.TERMINAL_PASSWORD,
                'tag_id': str(smartcard_name),
            },
            timeout=8.0,
            verify=False,
        )
    except requests.exceptions.Timeout as e:
        return {'errors': [str(e)]}

    if r.status_code != 200:
        return {'errors': ["status != 200"]}

    try:
        json = r.json()
    except requests.exceptions.JSONDecodeError as e:
        return {'errors': [str(e)]}

    # The result of this thread is passed as a parameter to the callback
    # in the main thread.
    return json


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

    def __init__(self, root_window, smartcard_logfile):
        # Note that we should properly employ the Observer pattern rather than
        # taking the `root_window` here: The terminal model might have a lot
        # more observers than only that, e.g. LED lights on the RPi or the RFID
        # reader, audio outputs, door openers, etc.
        self.root_window = root_window
        self.smartcard_logfile = smartcard_logfile
        self.is_updating = False
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

    def on_smartcard_input(self, response, success):
        if self.state not in USER_INPUT_STATES:
            # Ignore any RFID tag input if we are not expecting any.
            return

        # TODO – but be careful to not have a runaway counter.
        #   (e.g. reset after 10 Minutes idle?)
        # if num_of_requests_in_flight >= 5:
        #     # While we should never get here to send another request while the
        #     # one before that is still in flight and has not yet timed out,
        #     # make sure that any unforeseen circumstances cannot create an
        #     # unlimited number of threads.
        #     return

        # Log the captured smartcard details.
        print(f"{datetime.now()} captured {response}", file=self.smartcard_logfile)

        # Send the smartcard details in a POST request to the server.
        start_thread(post_stamp_event, (response,), self.on_server_reply)

        self._set_state(State.WAIT_FOR_SERVER_REPLY)
        self.time_last_action = time.time()
        self.notify_observers()

    def on_server_reply(self, msg):
        # Log the captured smartcard details.
        print(f"{datetime.now()} server reply: {msg}", file=self.smartcard_logfile)

        self._set_state(State.DISPLAY_SERVER_REPLY)
        self.last_server_reply = msg
        self.time_last_action = time.time()
        self.notify_observers()

    def notify_observers(self):
        # Make sure that we don't accidentally enter infinite recursion.
        assert not self.is_updating
        self.is_updating = True
        self.root_window.update_to_model(self)
        self.is_updating = False
