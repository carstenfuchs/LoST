import queue
from babel.dates import format_datetime
from datetime import datetime
from tkinter import *
from tkinter import ttk
from terminal import State
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


class TitleBar(Frame):

    def __init__(self, parent, show_clock=True, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, relief=RAISED, borderwidth=1)   #, background="#CCCCCC")

        self.columnconfigure(0, weight=1, uniform='u')   # "Rofu Kinderland"
        self.columnconfigure(1, weight=1, uniform='u')   # HH:MM
        self.columnconfigure(2, weight=1, uniform='u')   # "Lori"

        rofu_label = Label(self, text="Rofu Kinderland")
        rofu_label.grid(row=0, column=0, sticky="W", padx=5, pady=8)

        self.clock = Label(self)
        self.clock.grid(row=0, column=1, padx=5, pady=8)

        lori_label = Label(self, text="Lori")
        lori_label.grid(row=0, column=2, sticky="E", padx=5, pady=8)

        if False:
            rofu_label.config(background="#ffeeaa")
            self.clock.config(background="#34A2FE")
            lori_label.config(background="#FFCCCC")

        self.bind('<Button-1>', self.on_LMB_click)

        if show_clock:
            self.update_clock()

    def on_LMB_click(self, event):
        self.winfo_toplevel().terminal.set_state(State.WELCOME)

    def update_clock(self):
        self.clock.config(text=datetime.now().strftime("%H:%M"))
        self.after(1000, self.update_clock)


class WelcomeFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=None)

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

        self.time_label = Label(self, text="", background="#66CCFF")
        self.time_label.grid(row=2, column=0, sticky="NESW")

        self.date_label = Label(self, text="", background="cyan")
        self.date_label.grid(row=3, column=0, sticky="NESW")

        buttons_row = Frame(self, background='#ffeeaa')
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=1, uniform='space')
        buttons_row.columnconfigure(1, weight=2, uniform='button')    # [Anfang]
        buttons_row.columnconfigure(2, weight=1, uniform='space')
        buttons_row.columnconfigure(3, weight=2, uniform='button')    # [Ende]
        buttons_row.columnconfigure(4, weight=1, uniform='space')
        buttons_row.grid(row=5, column=0, sticky="NESW")

        anfang_button = Button(buttons_row, text="Anfang", command=self.on_click_Arbeitsanfang)
        anfang_button.grid(row=0, column=1, sticky="NESW")

        ende_button = Button(buttons_row, text="Ende", command=self.on_click_Arbeitsende)
        ende_button.grid(row=0, column=3, sticky="NESW")

        if False:
            # Helpers, only useful for debugging.
            Label(self, text="1", background="green").grid(row=1, column=0, sticky="NESW")
            Label(self, text="4", background="blue").grid(row=4, column=0, sticky="NESW")
            Label(self, text="6", background="red").grid(row=6, column=0, sticky="NESW")

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
        super().__init__(*args, **kwargs, background='lime')
        # self.config['background'] = 'yellow'

        self.rowconfigure(0, weight=0)  # title bar
        self.rowconfigure(1, weight=1)  # vertical space
        self.rowconfigure(2, weight=1)  # "Arbeitsanfang"
        self.rowconfigure(3, weight=1)  # vertical space
        self.rowconfigure(4, weight=1)  # buttons row
        self.rowconfigure(5, weight=1)  # vertical space

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

        title_bar = TitleBar(self)
        title_bar.grid(row=0, column=0, sticky="NESW")

        anf_label = Label(self, text="Arbeitsanfang", background="#66CCFF")
        anf_label.grid(row=2, column=0, sticky="NESW")

        buttons_row = Frame(self, background='#ffeeaa')
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=1, uniform='space')
        buttons_row.columnconfigure(1, weight=2, uniform='button')    # [Schicht]
        buttons_row.columnconfigure(2, weight=1, uniform='space')
        buttons_row.columnconfigure(3, weight=2, uniform='button')    # [jetzt]
        buttons_row.columnconfigure(4, weight=1, uniform='space')
        buttons_row.grid(row=4, column=0, sticky="NESW")

        self.schicht_button = Button(buttons_row, text="gemäß\nSchichtplanung", command=self.on_click_Anfang_Schicht)
        self.schicht_button.grid(row=0, column=1, sticky="NESW")

        self.jetzt_button = Button(buttons_row, text="» jetzt «", command=self.on_click_Anfang_Jetzt)
        self.jetzt_button.grid(row=0, column=3, sticky="NESW")

        if False:
            # set debug colors
            pass

    def update_to_model(self, terminal):
        active_col = '#66CCFF'
        inactive_col = '#666666'

        self.schicht_button.config(
            background=active_col if terminal.sow_type == 'schicht' else inactive_col,
            activebackground=active_col if terminal.sow_type == 'schicht' else inactive_col,   # mouse hover color
          # highlightbackground='red',      # used as base color for the border?
        )

        self.jetzt_button.config(
            background=active_col if terminal.sow_type == 'jetzt' else inactive_col,
            activebackground=active_col if terminal.sow_type == 'jetzt' else inactive_col,   # mouse hover color
          # highlightbackground='red',      # used as base color for the border?
        )

    def on_click_Anfang_Jetzt(self):
        self.winfo_toplevel().terminal.set_sow_type('jetzt')

    def on_click_Anfang_Schicht(self):
        self.winfo_toplevel().terminal.set_sow_type('schicht')


class DepartmentButtonsGrid(Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
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
                btn = Button(self, text=dept_name)
                btn.grid(row=row_nr, column=col_nr, sticky="NESW")
                btn.bind('<Button-1>', self.on_LMB_click)
                self.buttons.append(btn)

    def update_to_model(self, terminal):
        active_col = '#66CCFF'
        inactive_col = '#666666'
        dept_str = terminal.department

        for btn in self.buttons:
            btn.config(
                background=active_col if btn.cget('text') == dept_str else inactive_col,
                activebackground=active_col if btn.cget('text') == dept_str else inactive_col,   # mouse hover color
              # highlightbackground='red',      # used as base color for the border?
            )

    def on_LMB_click(self, event):
        text = event.widget.cget('text')
        mdl = self.winfo_toplevel().terminal
        mdl.set_department(None if text == mdl.department else text)


class PauseButtonsRow(Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.columnconfigure([0, 1, 2, 3, 4, 5], weight=1, uniform='pause_btn')

        # Have the grid span the full height of the frame
        # (instead of only the minimal height to enclose its children).
        self.rowconfigure(0, weight=1)

        button_labels = ('0:00', '0:15', '0:30', '0:45', '1:00', '+15')
        self.buttons = [Button(self, text=label) for label in button_labels]

        for nr, btn in enumerate(self.buttons):
            btn.grid(row=0, column=nr, sticky="NESW")
            btn.bind('<Button-1>', self.on_LMB_click)

    def update_to_model(self, terminal):
        active_col = '#66CCFF'
        inactive_col = '#666666'

        p_str = ''
        if terminal.pause is not None:
            p_str = f"{terminal.pause // 60}:{terminal.pause % 60:02}"

        for btn in self.buttons:
            btn.config(
                background=active_col if btn.cget('text') == p_str else inactive_col,
                activebackground=active_col if btn.cget('text') == p_str else inactive_col,   # mouse hover color
              # highlightbackground='red',      # used as base color for the border?
            )

    def on_LMB_click(self, event):
        text = event.widget.cget('text')
        mdl_pause = self.winfo_toplevel().terminal.pause

        if text == '+15':
            if mdl_pause is None:
                mdl_pause = 15
            else:
                mdl_pause = min(mdl_pause + 15, 180)
        else:
            p = int(text[:-3])*60 + int(text[-2:])
            mdl_pause = None if mdl_pause == p else p

        self.winfo_toplevel().terminal.set_pause(mdl_pause)


class ArbeitsendeFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background='lime')
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

        ende_label = Label(self, text="Arbeitsende", background="#66CCFF")
        ende_label.grid(row=2, column=0, sticky="NESW")

        self.dept_label = Label(self, text="Bereich", background="#66CCFF")
        self.dept_label.grid(row=4, column=0, sticky="NESW")

        self.dept_grid = DepartmentButtonsGrid(self)
        self.dept_grid.grid(row=5, column=0, sticky="NESW")

        self.pause_label = Label(self, text="Pause", background="#66CCFF")
        self.pause_label.grid(row=7, column=0, sticky="NESW")

        self.pause_buttons = PauseButtonsRow(self)
        self.pause_buttons.grid(row=8, column=0, sticky="NESW")

        if False:
            # set debug colors
            pass

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


class WaitForServerFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background='black')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.msg_label = Label(self, text="", background='black', foreground='white')
        self.msg_label.grid(row=0, column=0)
        self.timer_id = None

    def update_to_model(self, terminal):
        self.msg_label.config(text="")
        if self.timer_id:
            # The timer is always expected to expire before this function is called again.
            # Still, check if a timer is pending and cancel it explicitly, just in case.
            self.after_cancel(self.timer_id)
        self.timer_id = self.after(2000, self.update_message)

    def update_message(self):
        self.timer_id = None
        self.msg_label.config(text="Warte auf Antwort vom Lori-Server …")


class DisplayServerReplyFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background='black')

        self.rowconfigure(0, weight= 0)               # title bar
        self.rowconfigure(1, weight=12, uniform='u')  # vertical space
        self.rowconfigure(2, weight= 2, uniform='u')  # buttons row
        self.rowconfigure(3, weight= 1, uniform='u')  # vertical space

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

        title_bar = TitleBar(self, show_clock=False)
        title_bar.grid(row=0, column=0, sticky="NESW")

        buttons_row = Frame(self, background='black')
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=6)
        buttons_row.columnconfigure(1, weight=2)
        buttons_row.columnconfigure(2, weight=1)
        buttons_row.grid(row=2, column=0, sticky="NESW")

        self.msg_label = Label(self, text="", background='black', foreground='#66FF99')
        self.msg_label.grid(row=1, column=0, sticky="W", padx=8)

        ok_button = Button(
            buttons_row,
            text="OK",
            command=self.on_click_OK,
            font=('TkTextFont', 18),
            foreground='white',
            background='#666666',
            activeforeground='white',     # mouse hover color
            activebackground='#666666',   # mouse hover color
            highlightbackground='black',  # used as base color for the border?
        )
        ok_button.grid(row=0, column=1, sticky="NESW")

    def update_to_model(self, terminal):
        self.msg_label.config(text=terminal.last_server_reply)

    def on_click_OK(self):
        self.winfo_toplevel().terminal.set_state(State.WELCOME)
