#!/usr/bin/env python
import queue

from tkinter import *
from tkinter import font
from tkinter import ttk

from frames import WelcomeFrame, ArbeitsanfangFrame, ArbeitsendeFrame, WaitForServerFrame, DisplayServerReplyFrame
from server import start_testserver
from sm_card import SmartcardMonitor
from terminal import Terminal, State
from thread_tools import thread_queue


class RootWindow(Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("LoST - Lori Stempeluhr Terminal")
        self.geometry("640x480")

        if True:  # if localconfig.DEBUG:
            self.bind('<Escape>', lambda x: self.destroy())
            self.bind('<F1>', lambda x: self.terminal.process_RFID_tag_input('F1'))
            self.bind('<F2>', lambda x: self.terminal.process_server_reply('server message'))

        self.frame_Welcome = WelcomeFrame(self)
        self.frame_Arbeitsanfang = ArbeitsanfangFrame(self)
        self.frame_Arbeitsende = ArbeitsendeFrame(self)
        self.frame_WaitForServer = WaitForServerFrame(self)
        self.frame_DisplayServerReply = DisplayServerReplyFrame(self)
        self.active_frame = None

        self.terminal = None
        self.check_thread_queue()
        self.drive_terminal_clock()

    def check_thread_queue(self):
        """
        Checks if a thread has put something into the `thread_queue`.

        When a thread had finished its work, it has put a callback into the
        queue for us the pick up and process here in the main thread where we
        can freely update the GUI.
        """
        for count in range(5):
            try:
                callback, args = thread_queue.get(block=False)
            except queue.Empty:
                break
            callback(*args)

        # Check the `thread_queue` again in 100 ms.
        self.after(100, self.check_thread_queue)

    def drive_terminal_clock(self):
        if self.terminal is not None:
            self.terminal.process_clocktick()
        self.after(500, self.drive_terminal_clock)

    def update_to_model(self, terminal):
        #print("update_to_model")
        #print(f"{terminal.state = }")
        next_frame = self.frame_Welcome
        if terminal.state == State.ENTER_START_OF_WORK_DETAILS:
            next_frame = self.frame_Arbeitsanfang
        elif terminal.state == State.ENTER_END_OF_WORK_DETAILS:
            next_frame = self.frame_Arbeitsende
        elif terminal.state == State.WAIT_FOR_SERVER_REPLY:
            next_frame = self.frame_WaitForServer
        elif terminal.state == State.DISPLAY_SERVER_REPLY:
            next_frame = self.frame_DisplayServerReply

        if hasattr(next_frame, "update_to_model"):
            next_frame.update_to_model(terminal)

        if self.active_frame == next_frame:
            return

        #print("Setting new frame!")
        if self.active_frame is not None:
            self.active_frame.pack_forget()

        self.active_frame = next_frame
        self.active_frame.pack(side=TOP, fill=BOTH, expand=True) #, padx=3, pady=3)


root_window = RootWindow()

terminal = Terminal(root_window)
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
