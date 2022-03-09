#!/usr/bin/env python
import settings
from mode_logistics.gui import RootWindow
from mode_logistics.terminal import Terminal
from server import start_testserver
from sm_card import SmartcardMonitor


smartcard_logfile = open(settings.SMARTCARD_LOGFILE_PATH, mode='a', buffering=1)

root_window = RootWindow()

terminal = Terminal(root_window, smartcard_logfile)

# Initial setup of the listeners (the GUI).
terminal.notify_observers()

# The root window needs to know the terminal so that event handlers can access it
# in order to implement the effects of the handled events.
# (The terminal in turn will notify its observers about its changed state.)
root_window.terminal = terminal

scmon = SmartcardMonitor()
scmon.init(terminal.on_smartcard_input)

USE_SERVER = (settings.SERVER_ADDRESS[0] == 'built-in')
if USE_SERVER:
    httpd = start_testserver(settings.SERVER_ADDRESS[1])

root_window.mainloop()

if USE_SERVER:
    httpd.shutdown()
    httpd.server_close()

scmon.shutdown()

# It's not really necessary here, but let's explicitly reset the root window's
# reference to the terminal in order to break the circular dependency.
root_window.terminal = None

smartcard_logfile.close()
