#!/usr/bin/env python
from frames import RootWindow
from server import start_testserver
from sm_card import SmartcardMonitor
from terminal import Terminal


root_window = RootWindow()

terminal = Terminal(root_window)

# Initial setup of the listeners (the GUI).
terminal.notify_observers()

# The root window needs to know the terminal so that event handlers can access it
# in order to implement the effects of the handled events.
# (The terminal in turn will notify its observers about its changed state.)
root_window.terminal = terminal

# print(font.names())
# for n in font.names():
#     # font.nametofont(n)['size'] = 12
#     print(font.nametofont(n).actual())
# print(font.families())

scmon = SmartcardMonitor()
scmon.init(terminal.on_smartcard_input)

use_server = True
if use_server:
    httpd = start_testserver()

root_window.mainloop()

if use_server:
    httpd.shutdown()
    httpd.server_close()

scmon.shutdown()

# It's not really necessary here, but let's explicitly reset the root window's
# reference to the terminal in order to break the circular dependency.
root_window.terminal = None
