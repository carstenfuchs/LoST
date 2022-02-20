#!/usr/bin/env python
from tkinter import *
from tkinter import font
from tkinter import ttk

from frames import WelcomeFrame, ArbeitsanfangFrame, ArbeitsendeFrame
from terminal import Terminal, State


class RootWindow(Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("LoST - Lori Stempeluhr Terminal")
        self.geometry("640x480")

        if True:  # if localconfig.quit_with_ESC:
            self.bind('<Escape>', lambda x: self.destroy())

        self.frame_Welcome = WelcomeFrame(self)
        self.frame_Arbeitsanfang = ArbeitsanfangFrame(self)
        self.frame_Arbeitsende = ArbeitsendeFrame(self)
        self.active_frame = None

        self.terminal = None
        self.drive_terminal_clock()

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

root_window.mainloop()

# It's not really necessary here, but let's explicitly reset the root window's
# reference to the terminal in order to break the circular dependency.
root_window.terminal = None
