#!/usr/bin/env python
import settings
from mode_logistics.gui import RootWindow
from mode_logistics.terminal import Terminal
from network_handler import NetworkHandler
from server import start_testserver
from sm_card import SmartcardMonitor


terminal = Terminal()

# The root window, the network handler and the smartcard monitor all need to
# know the terminal so that their event handlers can access it when
# implementing the effects of the handled events.
# (The terminal in turn will notify its observers about its changed state.)
root_window = RootWindow(terminal)
network_handler = NetworkHandler(terminal)
sc_mon = SmartcardMonitor(terminal, network_handler)

# The terminal could have numerous additional observers. Examples include:
# LED lights on the Raspberry Pi, LED lights on the smartcard reader, audio
# signals, state loggers, door openers, etc.
terminal.add_observer(root_window)

# Initial setup of the observers (the GUI).
terminal.notify_observers()

USE_SERVER = (settings.SERVER_ADDRESS[0] == 'built-in')
if USE_SERVER:
    httpd = start_testserver(settings.SERVER_ADDRESS[1])

root_window.mainloop()

if USE_SERVER:
    httpd.shutdown()
    httpd.server_close()

terminal.clear_observers()
sc_mon.shutdown()
