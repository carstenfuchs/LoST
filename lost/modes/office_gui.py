from babel.dates import format_datetime
from datetime import datetime
from tkinter import *
# from tkinter import ttk

from lost.modes.office_terminal import State
from lost.widgets import adjust_wraplength, cp, fp, DisplayServerReplyFrame, PauseButtonsRow, SystemPanelFrame, TitleBar, TouchButton, WaitForServerFrame


class RootWindow(Tk):

    def __init__(self, terminal, main_con, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.terminal = terminal
        self.main_con = main_con

        self.title("LoST - Lori Stempeluhr Terminal")

        # The native resolution of the official Raspberry Pi Touch Display
        # (https://www.raspberrypi.com/products/raspberry-pi-touch-display/)
        # is 800 x 480 pixels, so let's pick that as the default size.
        self.geometry("800x480")

        if True:  # if localconfig.DEBUG:
            success_reply = {
                'ma': "Konrad Zuse (lokales erzeugtes Beispiel)",
                'now': "not used at this time",
                'feedback': {
                    'anfang': "8:00",
                    'ende': None,
                    'pause': None,
                    'pause_error': "Eine Netzwerkübertragung hat nicht stattgefunden.",
                    'result': None,
                },
            }

            messages_reply = {
                'messages': [
                    "Dies ist ein Beispiel für eine Rückmeldung vom Lori-Server vom " \
                    "Typ „messages“. Dazu wurde eine auf dem Terminal vorbereitete " \
                    "Antwort eingestellt, eine echte Netzwerkübertragung hat nicht stattgefunden.",
                ],
            }

            errors_reply = {
                'errors': [
                    "Dies ist ein Beispiel für eine Meldung vom Typ „errors“. "
                    "Sie kann lokal vom Terminal oder vom Lori-Server ausgehen. "
                    "Dazu wurde eine auf dem Terminal vorbereitete Antwort eingestellt, "
                    "eine echte Netzwerkübertragung hat nicht stattgefunden.",
                ],
                'detail_info': "optionale Detailangaben, z.B. Timeout, unbekanntes Terminal o.ä.",
            }

            self.bind('<Escape>', lambda x: self.destroy() if self.terminal.state == State.WELCOME else self.terminal.set_state(State.WELCOME))
            self.bind('<F1>', lambda x: self.terminal.set_state(State.WELCOME))
            self.bind('<F5>', lambda x: self.terminal.on_server_reply_received(success_reply))
            self.bind('<F6>', lambda x: self.terminal.on_server_reply_received(messages_reply))
            self.bind('<F7>', lambda x: self.terminal.on_server_reply_received(errors_reply))
            self.bind('<F8>', lambda x: self.terminal.on_server_reply_received({}))
            self.bind('<F9>', lambda x: self.main_con.simulate_smartcard_input('ABCD'))
          # self.bind('<F10>', lambda x: self.main_con.simulate_server_reply())
            self.bind('<F12>', lambda x: self.terminal.set_state_system_panel())

        self.frame_Welcome = WelcomeFrame(self)
        self.frame_WaitForServer = WaitForServerFrame(self)
        self.frame_DisplayServerReply = DisplayServerReplyFrame(self)
        self.frame_SystemPanel = SystemPanelFrame(self)
        self.active_frame = None

        self.bind('<Configure>', self.on_resize)
        self.drive_main_connector()

    def on_resize(self, event):
        if event.widget == self:
            # print(event)
            fp.resize(event.height)

    def drive_main_connector(self):
        """
        Forward clock tick events to the main connector.

        In a Tkinter program, GUI functions like this are the natural place to receive
        timer events. As these events are also needed elsewhere (in non-GUI code), we pass
        them to the main connector that will further distribute them.
        """
        self.main_con.on_clock_tick()
        self.after(100, self.drive_main_connector)

    def update_to_model(self, terminal):
        next_frame = self.frame_Welcome
        if terminal.state == State.WAIT_FOR_SERVER_REPLY:
            next_frame = self.frame_WaitForServer
        elif terminal.state == State.DISPLAY_SERVER_REPLY:
            next_frame = self.frame_DisplayServerReply
        elif terminal.state == State.SYSTEM_PANEL:
            next_frame = self.frame_SystemPanel

        if hasattr(next_frame, "update_to_model"):
            next_frame.update_to_model(terminal)

        if self.active_frame == next_frame:
            return

        if self.active_frame is not None:
            self.active_frame.pack_forget()

        self.active_frame = next_frame
        self.active_frame.pack(side=TOP, fill=BOTH, expand=True)


class WelcomeFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=cp.get_bg_col())

        self.rowconfigure(0, weight=0)  # title bar
        self.rowconfigure(1, weight=1)  # vertical space
        self.rowconfigure(2, weight=1)  # HH:MM
        self.rowconfigure(3, weight=1)  # day, month
        self.rowconfigure(4, weight=1)  # vertical space
        self.rowconfigure(5, weight=1)  # pause label
        self.rowconfigure(6, weight=1)  # pause buttons
        self.rowconfigure(7, weight=1)  # vertical space

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

        title_bar = TitleBar(self, show_clock=False)
        title_bar.grid(row=0, column=0, sticky="NESW")

        self.time_label = Label(self, text="", foreground='white', background=cp.get_bg_col(), font=fp.get_font(250))
        self.time_label.grid(row=2, column=0, sticky="NESW")

        self.date_label = Label(self, text="", anchor='n', foreground='#666666', background=cp.get_bg_col(), font=fp.get_font(120))
        self.date_label.grid(row=3, column=0, sticky="NESW")

        self.pause_label = Label(self, text="Pause", foreground='#3380E6', background=cp.get_bg_col(), font=fp.get_font(120))
        self.pause_label.grid(row=5, column=0, sticky="NESW")

        self.pause_buttons = PauseButtonsRow(self)
        self.pause_buttons.grid(row=6, column=0, sticky="NESW")

        self.update_clock()

    def update_clock(self):
        now = datetime.now()
        # https://stackoverflow.com/questions/985505/locale-date-formatting-in-python
        self.time_label.config(text=format_datetime(now, 'HH:mm', locale='de_DE'))
        self.date_label.config(text=format_datetime(now, 'EEEE, d. MMMM', locale='de_DE'))  # Mittwoch, 5. August
        self.after(1000, self.update_clock)

    def update_to_model(self, terminal):
        p_str = "Pause"
        if terminal.pause is not None:
            p_str += f" {terminal.pause // 60}:{terminal.pause % 60:02}"

        self.pause_label.config(text=p_str)
        self.pause_buttons.update_to_model(terminal)
