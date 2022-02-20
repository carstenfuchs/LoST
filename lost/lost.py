#!/usr/bin/env python
from tkinter import *
from tkinter import font
from tkinter import ttk
from frames import TopBar, WelcomeFrame, ArbeitsanfangFrame, ArbeitsendeFrame
from model import Model, Intention


class RootWindow(Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("LoST - Lori Stempeluhr Terminal")
        self.geometry("640x480")

        if True:  # if localconfig.quit_with_ESC:
            self.bind('<Escape>', lambda x: self.destroy())

        # top_bar = TopBar(self)
        # top_bar.pack(fill=X)

        self.frame_Welcome = WelcomeFrame(self)
        self.frame_Arbeitsanfang = ArbeitsanfangFrame(self)
        self.frame_Arbeitsende = ArbeitsendeFrame(self)
        self.active_frame = None

    def update_to_model(self, model):
        #print("update_to_model")
        #print(f"{model.intention = }")
        next_frame = self.frame_Welcome
        if model.intention == Intention.ENTER_START_OF_WORK_DETAILS:
            next_frame = self.frame_Arbeitsanfang
        elif model.intention == Intention.ENTER_END_OF_WORK_DETAILS:
            next_frame = self.frame_Arbeitsende

        if hasattr(next_frame, "update_to_model"):
            next_frame.update_to_model(model)

        if self.active_frame == next_frame:
            return

        #print("Setting new frame!")
        if self.active_frame is not None:
            self.active_frame.pack_forget()

        self.active_frame = next_frame
        self.active_frame.pack(side=TOP, fill=BOTH, expand=True) #, padx=3, pady=3)


root_window = RootWindow()

model = Model(root_window)
model.notify_observers()

# The root window needs to know the model so that event handlers can access it
# in order to implement the effects of the event.
# (The model in turn will notify its observers about its changed state.)
root_window.model = model

# print(font.names())
# for n in font.names():
#     # font.nametofont(n)['size'] = 12
#     print(font.nametofont(n).actual())
# print(font.families())

root_window.mainloop()

# It's not really necessary here, but let's explicitly reset the root window's
# reference to the model in order to break the circular dependency.
root_window.model = None
