from babel.dates import format_datetime
from datetime import datetime
from tkinter import *
# from tkinter import ttk

from lost.modes.logistics_terminal import State
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
            self.bind('<F2>', lambda x: self.terminal.set_state(State.ENTER_START_OF_WORK_DETAILS))
            self.bind('<F3>', lambda x: self.terminal.set_state(State.ENTER_END_OF_WORK_DETAILS))
            self.bind('<F5>', lambda x: self.terminal.on_server_reply_received(success_reply))
            self.bind('<F6>', lambda x: self.terminal.on_server_reply_received(messages_reply))
            self.bind('<F7>', lambda x: self.terminal.on_server_reply_received(errors_reply))
            self.bind('<F8>', lambda x: self.terminal.on_server_reply_received({}))
            self.bind('<F9>', lambda x: self.main_con.simulate_smartcard_input('Sonderkarte: Verbindungstest'))
            self.bind('<F12>', lambda x: self.terminal.set_state_system_panel())

        self.frame_Welcome = WelcomeFrame(self)
        self.frame_Arbeitsanfang = ArbeitsanfangFrame(self)
        self.frame_Arbeitsende = ArbeitsendeFrame(self)
        self.frame_WaitForServer = WaitForServerFrame(self)
        self.frame_DisplayServerReply = DisplayServerReplyFrame(self)
        self.frame_SystemPanel = SystemPanelFrame(self)
        self.active_frame = None

        self.bind('<Configure>', self.on_resize)
        self.drive_main_connector()
        self.drive_terminal_clock()

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
        elif terminal.state == State.SYSTEM_PANEL:
            next_frame = self.frame_SystemPanel

        if hasattr(next_frame, "update_to_model"):
            next_frame.update_to_model(terminal)

        if self.active_frame == next_frame:
            return

        #print("Setting new frame!")
        if self.active_frame is not None:
            self.active_frame.pack_forget()

        self.active_frame = next_frame
        self.active_frame.pack(side=TOP, fill=BOTH, expand=True) #, padx=3, pady=3)


class WelcomeFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=cp.get_bg_col())

        self.rowconfigure(0, weight=0)  # title bar
        self.rowconfigure(1, weight=1)  # vertical space
        self.rowconfigure(2, weight=1)  # HH:MM
        self.rowconfigure(3, weight=1)  # day, month
        self.rowconfigure(4, weight=1)  # vertical space
        self.rowconfigure(5, weight=1)  # buttons row
        self.rowconfigure(6, weight=1)  # vertical space

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

        title_bar = TitleBar(self, show_clock=False)
        title_bar.grid(row=0, column=0, sticky="NESW")

        self.time_label = Label(self, text="", foreground='white', background=cp.get_bg_col(), font=fp.get_font(250))
        self.time_label.grid(row=2, column=0, sticky="NESW")

        self.date_label = Label(self, text="", anchor='n', foreground='#666666', background=cp.get_bg_col(), font=fp.get_font(120))
        self.date_label.grid(row=3, column=0, sticky="NESW")

        buttons_row = Frame(self, background=cp.get_bg_col())
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=3, uniform='space')
        buttons_row.columnconfigure(1, weight=2, uniform='button')    # [Anfang]
        buttons_row.columnconfigure(2, weight=1, uniform='space')
        buttons_row.columnconfigure(3, weight=2, uniform='button')    # [Ende]
        buttons_row.columnconfigure(4, weight=3, uniform='space')
        buttons_row.grid(row=5, column=0, sticky="NESW")

        anfang_button = TouchButton(buttons_row, text="Anfang", command=self.on_click_Arbeitsanfang)
        anfang_button.grid(row=0, column=1, sticky="NESW")

        ende_button = TouchButton(buttons_row, text="Ende", command=self.on_click_Arbeitsende)
        ende_button.grid(row=0, column=3, sticky="NESW")

        self.update_clock()

    def on_click_Arbeitsanfang(self):
        self.winfo_toplevel().terminal.set_state(State.ENTER_START_OF_WORK_DETAILS)

    def on_click_Arbeitsende(self):
        self.winfo_toplevel().terminal.set_state(State.ENTER_END_OF_WORK_DETAILS)

    def update_clock(self):
        now = datetime.now()
        # https://stackoverflow.com/questions/985505/locale-date-formatting-in-python
        self.time_label.config(text=format_datetime(now, 'HH:mm', locale='de_DE'))
        self.date_label.config(text=format_datetime(now, 'EEEE, d. MMMM', locale='de_DE'))  # Mittwoch, 5. August
        self.after(1000, self.update_clock)


class ArbeitsanfangFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=cp.get_bg_col())
        # self.config['background'] = 'yellow'

        self.rowconfigure(0, weight=0)  # title bar
        self.rowconfigure(1, weight=2)  # vertical space
        self.rowconfigure(2, weight=2)  # "Arbeitsanfang"
        self.rowconfigure(3, weight=1)  # vertical space
        self.rowconfigure(4, weight=1)  # buttons row
        self.rowconfigure(5, weight=3)  # vertical space

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

        title_bar = TitleBar(self)
        title_bar.grid(row=0, column=0, sticky="NESW")

        anf_label = Label(self, text="Arbeitsanfang", foreground='white', background=cp.get_bg_col(), font=fp.get_font(150))
        anf_label.grid(row=2, column=0, sticky="NESW")

        buttons_row = Frame(self, background=cp.get_bg_col())
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=4, uniform='space')
        buttons_row.columnconfigure(1, weight=2, uniform='button')    # [Schicht]
        buttons_row.columnconfigure(2, weight=1, uniform='space')
        buttons_row.columnconfigure(3, weight=2, uniform='button')    # [jetzt]
        buttons_row.columnconfigure(4, weight=4, uniform='space')
        buttons_row.grid(row=4, column=0, sticky="NESW")

        self.schicht_button = TouchButton(buttons_row, text="gemäß\nSchicht", command=self.on_click_Anfang_Schicht)
        self.schicht_button.grid(row=0, column=1, sticky="NESW")

        self.jetzt_button = TouchButton(buttons_row, text="» jetzt «", command=self.on_click_Anfang_Jetzt)
        self.jetzt_button.grid(row=0, column=3, sticky="NESW")

    def update_to_model(self, terminal):
        self.schicht_button.set_active(terminal.sow_type == 'schicht')
        self.jetzt_button.set_active(terminal.sow_type == 'jetzt')

    def on_click_Anfang_Jetzt(self):
        self.winfo_toplevel().terminal.set_sow_type('jetzt')

    def on_click_Anfang_Schicht(self):
        self.winfo_toplevel().terminal.set_sow_type('schicht')


class DepartmentButtonsGrid(Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, background=cp.get_bg_col())
        self.buttons = []

        self.departments = (
            ("Fuhrpark", "Montage", "Reinigung", "Sonderaufgaben", "Verdichtung"),
            ("Kommissionieren", "Online-Logistik", "Retouren", "Transporter", "Verschiebung"),
            ("Leitstand", "Post", "Rüsten", "", "Wareneingang"),
        )

        self.rowconfigure(
            list(range(len(self.departments))),
            weight=1,
            uniform='dept_row',
        )

        self.columnconfigure(
            list(range(max(len(row) for row in self.departments))),
            weight=1,
            uniform='dept_col',
        )

        for row_nr, row in enumerate(self.departments):
            for col_nr, dept_name in enumerate(row):
                if not dept_name:
                    continue
                btn = TouchButton(self, font_size=70, text=dept_name)
                btn.grid(row=row_nr, column=col_nr, sticky="NESW")
                btn.bind('<Button-1>', self.on_LMB_click)
                self.buttons.append(btn)

    def update_to_model(self, terminal):
        for btn in self.buttons:
            btn.set_active(btn.cget('text') == terminal.department)

    def on_LMB_click(self, event):
        text = event.widget.cget('text')
        mdl = self.winfo_toplevel().terminal
        mdl.set_department(None if text == mdl.department else text)


class ArbeitsendeFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=cp.get_bg_col())
        # self.config['background'] = 'yellow'

        self.rowconfigure(0, weight=0)  # title bar
        self.rowconfigure(1, weight=1)  # vertical space
        self.rowconfigure(2, weight=1)  # "Arbeitsende"
        self.rowconfigure(3, weight=1)  # vertical space
        self.rowconfigure(4, weight=1)  # "Bereich"
        self.rowconfigure(5, weight=1)  # Bereich buttons grid
        self.rowconfigure(6, weight=1)  # vertical space
        self.rowconfigure(7, weight=1)  # "Pause"
        self.rowconfigure(8, weight=1)  # pause buttons row
        self.rowconfigure(9, weight=1)  # vertical space

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

        title_bar = TitleBar(self)
        title_bar.grid(row=0, column=0, sticky="NESW")

        ende_label = Label(self, text="Arbeitsende", foreground='white', background=cp.get_bg_col(), font=fp.get_font(150))
        ende_label.grid(row=2, column=0, sticky="NESW")

        self.dept_label = Label(self, text="Bereich", foreground='#3380E6', background=cp.get_bg_col(), font=fp.get_font(100))
        self.dept_label.grid(row=4, column=0, sticky="NESW")

        self.dept_grid = DepartmentButtonsGrid(self)
        self.dept_grid.grid(row=5, column=0, sticky="NESW")

        self.pause_label = Label(self, text="Pause", foreground='#3380E6', background=cp.get_bg_col(), font=fp.get_font(100))
        self.pause_label.grid(row=7, column=0, sticky="NESW")

        self.pause_buttons = PauseButtonsRow(self)
        self.pause_buttons.grid(row=8, column=0, sticky="NESW")

    def update_to_model(self, terminal):
        dept_str = "Bereich"
        if terminal.department is not None:
            dept_str += f" {terminal.department}"

        self.dept_label.config(text=dept_str)
        self.dept_grid.update_to_model(terminal)

        p_str = "Pause"
        if terminal.pause is not None:
            p_str += f" {terminal.pause // 60}:{terminal.pause % 60:02}"

        self.pause_label.config(text=p_str)
        self.pause_buttons.update_to_model(terminal)
