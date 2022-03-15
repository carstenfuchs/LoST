#!/usr/bin/env python
import queue

import settings
from network_handler import NetworkHandler
from server import start_testserver
from sm_card import SmartcardMonitor
from thread_tools import thread_queue


if settings.TERMINAL_MODE == 'logistics':
    from modes.logistics_gui import RootWindow
    from modes.logistics_terminal import Terminal
elif settings.TERMINAL_MODE == 'office':
    from modes.office_gui import RootWindow
    from modes.office_terminal import Terminal
else:
    assert False, "Unknown terminal mode."


class MainConnector:
    """This class helps with things that occur in one place but belong in another."""

    def __init__(self):
        self.sc_mon = None
        self.nw_handler = None

    def _check_thread_queue(self):
        """
        Checks if a thread has put something into the `thread_queue`.

        When a thread has experienced an event that it wants to pass to the main thread,
        for example when a smartcard has been read or a server reply been received, it put
        a callback into the queue for us the pick up and process here, as in the main
        thread we are free to update the terminal, the GUI and any other state.
        """
        for count in range(5):
            try:
                callback, args = thread_queue.get(block=False)
            except queue.Empty:
                break
            callback(*args)

    def on_clock_tick(self):
        """
        This function accounts for resources that must be periodically updated.

        The timers for periodic clock ticks happen to be kept in and driven by the GUI.
        As we also need them for non-GUI related tasks, we have the GUI periodically call
        this function (in the main thread) where we forward the clock ticks as needed.
        """
        # Check for events from other threads, e.g. smartcard reads or server replies.
        self._check_thread_queue()

    def simulate_smartcard_input(self, smartcard_id):
        self.sc_mon.on_smartcard_input(smartcard_id, True)


terminal = Terminal()
main_con = MainConnector()

# The root window, the network handler and the smartcard monitor all need to
# know the terminal so that their event handlers can access it when
# implementing the effects of the handled events.
# (The terminal in turn will notify its observers about its changed state.)
root_window = RootWindow(terminal, main_con)
network_handler = NetworkHandler(terminal)
sc_mon = SmartcardMonitor(terminal, network_handler)

# The terminal could have numerous additional observers. Examples include:
# LED lights on the Raspberry Pi, LED lights on the smartcard reader, audio
# signals, state loggers, door openers, etc.
terminal.add_observer(root_window)

# Initial setup of the observers (the GUI).
terminal.notify_observers()

# The main connector must know the pieces to connect.
main_con.sc_mon = sc_mon

USE_SERVER = (settings.SERVER_ADDRESS[0] == 'built-in')
if USE_SERVER:
    httpd = start_testserver(settings.SERVER_ADDRESS[1])

root_window.mainloop()

if USE_SERVER:
    httpd.shutdown()
    httpd.server_close()

main_con.sc_mon = None
terminal.clear_observers()
sc_mon.shutdown()
