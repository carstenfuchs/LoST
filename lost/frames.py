import queue
from babel.dates import format_datetime
from datetime import datetime
from tkinter import *
from tkinter import font
from tkinter import ttk
from terminal import State
from thread_tools import thread_queue


class ColorProvider:

    def __init__(self):
        self.count = 0
        self.colors = []

        for g in (0x00, 0x66, 0xCC):
            for b in (0x33, 0x99, 0xFF):
                self.colors.append('#{:02x}{:02x}{:02x}'.format(0, g, b))

    def get_bg_col(self):
        # r = lambda: randint(0, 255)
        # return '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
        self.count += 1
        return self.colors[self.count % len(self.colors)]


class FontProvider:

    def __init__(self):
        self.win_size_factor = 16.0
        self.fonts = {}

        # print("\nFont names:")
        # for n in font.names():
        #     print(f"  {n:18s} {font.nametofont(n).actual()}")

        # print("\nFont families:")
        # print(sorted(font.families()))

    def resize(self, window_height):
        """Updates the size of each font according to the new window height."""
        self.win_size_factor = window_height / 480.0 * 20.0

        for percent, font in self.fonts.items():
            font.config(size=-int(self.win_size_factor * percent / 100.0))

    def get_font(self, percent):
        if percent in self.fonts:
            return self.fonts[percent]

        f = font.nametofont('TkTextFont').copy()
        f.config(size=-int(self.win_size_factor * percent / 100.0))

        print(f"Adding font size {percent} %")
        self.fonts[percent] = f
        return f


cp = ColorProvider()
fp = FontProvider()


def adjust_wraplength(event):
    """
    Label widgets that support line wrapping can call this method on
    resize (<Configure>) events to have their wrap length updated.
    """
    # Also see https://stackoverflow.com/questions/62485520/how-to-wrap-the-text-in-a-tkinter-label-dynamically
    event.widget.config(wraplength=event.widget.winfo_width())


class RootWindow(Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("LoST - Lori Stempeluhr Terminal")
        self.geometry("640x480")

        if True:  # if localconfig.DEBUG:
            success_data = {
                'ma': "Konrad Zuse (F1234)",
            }
            messages = ["Die Karte wurde erfolgreich eingelesen und ordentlich und regelkonform verarbeitet. Das Ergebnis hat allerdings nicht zu einer Zeitmeldung geführt, sondern es lagen besondere Umstände vor, die hier gemeldet werden. (Beispiele: neue Karte, gesperrte Karte, …)"]
            errors = ["Ein technisches Problem hat das Auswerten der Karte verhindert. Das Einlesen wurde mit aktuellen Zeitpunkt aufgezeichnet und die Verarbeitung wird nach der Lösung des Problems automatisch nachgeholt."]

            self.bind('<Escape>', lambda x: self.destroy() if self.terminal.state == State.WELCOME else self.terminal.set_state(State.WELCOME))
            self.bind('<F1>', lambda x: self.terminal.set_state(State.WELCOME))
            self.bind('<F2>', lambda x: self.terminal.set_state(State.ENTER_START_OF_WORK_DETAILS))
            self.bind('<F3>', lambda x: self.terminal.set_state(State.ENTER_END_OF_WORK_DETAILS))
            self.bind('<F4>', lambda x: self.terminal.on_smartcard_input('ABCD', True))
            self.bind('<F5>', lambda x: self.terminal.on_server_reply(success_data))
            self.bind('<F6>', lambda x: self.terminal.on_server_reply({'messages': messages}))
            self.bind('<F7>', lambda x: self.terminal.on_server_reply({'errors': errors}))
            self.bind('<F8>', lambda x: self.terminal.on_server_reply({}))

        self.frame_Welcome = WelcomeFrame(self)
        self.frame_Arbeitsanfang = ArbeitsanfangFrame(self)
        self.frame_Arbeitsende = ArbeitsendeFrame(self)
        self.frame_WaitForServer = WaitForServerFrame(self)
        self.frame_DisplayServerReply = DisplayServerReplyFrame(self)
        self.active_frame = None

        self.terminal = None
        self.bind('<Configure>', self.on_resize)
        self.check_thread_queue()
        self.drive_terminal_clock()

    def on_resize(self, event):
        if event.widget == self:
            # print(event)
            fp.resize(event.height)

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


class WorkHoursReplyGrid(Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs, background=cp.get_bg_col())

        self.rowconfigure(0, weight=1)  # Anfang
        self.rowconfigure(1, weight=1)  # Ende
        self.rowconfigure(2, weight=1)  # Pause
        self.rowconfigure(3, weight=1)  # Ergebnis

        self.columnconfigure(0, weight=1)   # Labels (Anfang, Ende, Pause)
        self.columnconfigure(1, weight=1)   # Values (8:00, …)
        self.columnconfigure(2, weight=1)   # Notes (optional)

        for row_nr, col_text in enumerate(("Anfang", "Ende", "Pause", "Ergebnis")):
            l =  Label(self, text=col_text, background='orange', foreground='#66FF99', font=fp.get_font(100))
            l.grid(row=row_nr, column=0, sticky="NESW", padx=8, pady=1)

        for row_nr, col_text in enumerate(("8:00", "16:30", "0:30", "8:00")):
            l =  Label(self, text=col_text, background='orange', foreground='#66FF99', font=fp.get_font(100))
            l.grid(row=row_nr, column=1, sticky="E", padx=8)

        for row_nr, col_text in enumerate(("1", "2", "3", "3")):
            l =  Label(self, text=col_text, background='orange', foreground='#66FF99', font=fp.get_font(100))
            l.grid(row=row_nr, column=2, sticky="W", padx=8)

        # TODO: Pausenproblem?

    def update_to_model(self, terminal):
        pass


class DisplayServerReplyFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=cp.get_bg_col())

      # ROW_NR_TITLE_BAR     = 0
        ROW_NR_HEADLINE      = 0
        ROW_NR_BORDER_TOP    = 1
        ROW_NR_BODY          = 2   # shared by body_grid and msg_label
        ROW_NR_BORDER_BOTTOM = 3
        ROW_NR_EXTRA_MSG     = 4
        ROW_NR_OK_BUTTON     = 5
        ROW_NR_BOTTOM_SPACE  = 6

      # self.rowconfigure(ROW_NR_TITLE_BAR,     weight= 0)
        self.rowconfigure(ROW_NR_HEADLINE,      weight= 3, uniform='u')
        self.rowconfigure(ROW_NR_BORDER_TOP,    weight= 0)
        self.rowconfigure(ROW_NR_BODY,          weight=12, uniform='u')
        self.rowconfigure(ROW_NR_BORDER_BOTTOM, weight= 0)
        self.rowconfigure(ROW_NR_EXTRA_MSG,     weight= 3, uniform='u')
        self.rowconfigure(ROW_NR_OK_BUTTON,     weight= 2, uniform='u')
        self.rowconfigure(ROW_NR_BOTTOM_SPACE,  weight= 1, uniform='u')

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

      # title_bar = TitleBar(self, show_clock=False)
      # title_bar.grid(row=ROW_NR_TITLE_BAR, column=0, sticky="NESW")

        self.headline_label = Label(self, text="", background=cp.get_bg_col(), foreground='white', anchor='sw', font=fp.get_font(100))
        self.headline_label.grid(row=ROW_NR_HEADLINE, column=0, sticky="NESW", padx=8, pady=2)

        self.border_top = Frame(self, height=2, background='orange')
        self.border_top.grid(row=ROW_NR_BORDER_TOP, column=0, sticky="NESW")

        # The `body_grid` and the `msg_label` share the common row `ROW_NR_BODY`.
        self.body_grid = WorkHoursReplyGrid(self)
        self.body_grid.grid(row=ROW_NR_BODY, column=0, sticky="NESW", padx=8)

        self.msg_label = Label(self, text="", wraplength=300, justify='left', background=cp.get_bg_col(), foreground='white', anchor='w', font=fp.get_font(100))
        self.msg_label.grid(row=ROW_NR_BODY, column=0, sticky="EW", padx=8)
        self.msg_label.bind('<Configure>', adjust_wraplength)

        self.border_bottom = Frame(self, height=2, background='orange')
        self.border_bottom.grid(row=ROW_NR_BORDER_BOTTOM, column=0, sticky="NESW")

        self.extra_msg_label = Label(self, text="", wraplength=300, justify='left', background=cp.get_bg_col(), foreground='white', anchor='nw', font=fp.get_font(100))
        self.extra_msg_label.grid(row=ROW_NR_EXTRA_MSG, column=0, sticky="NESW", padx=8, pady=2)
        self.extra_msg_label.bind('<Configure>', adjust_wraplength)

        # The row with the "OK" button.
        buttons_row = Frame(self, background=cp.get_bg_col())
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=6)
        buttons_row.columnconfigure(1, weight=2)
        buttons_row.columnconfigure(2, weight=1)
        buttons_row.grid(row=ROW_NR_OK_BUTTON, column=0, sticky="NESW")

        ok_button = Button(
            buttons_row,
            text="OK",
            command=self.on_click_OK,
            font=fp.get_font(100),
            foreground='white',
            background='#666666',
            activeforeground='white',     # mouse hover color
            activebackground='#666666',   # mouse hover color
            highlightbackground='black',  # used as base color for the border?
        )
        ok_button.grid(row=0, column=1, sticky="NESW")

    def update_to_model(self, terminal):
        lsr = terminal.last_server_reply

        self.body_grid.grid_remove()
        self.msg_label.grid_remove()

        if 'ma' in lsr:
            self.headline_label.config(text=f"MA: {lsr['ma']}")
            self.body_grid.update_to_model(terminal)
            self.body_grid.grid()
            self.msg_label.config(text="")
            self.extra_msg_label.config(text="(keine extra_msg)")
        elif 'messages' in lsr:
            # Das Einscannen der Karte hat zwar nicht zu einer Aufzeichnung
            # eines Timestamps geführt, aber es handelte sich trotzdem um eine
            # ordentliche, regelkonforme Verarbeitung.
            self.headline_label.config(text="Verarbeitung durch den Lori-Server")
            self.msg_label.config(text="\n".join(lsr['messages']))
            self.msg_label.grid()
            self.extra_msg_label.config(text="(keine extra_msg)")
        else:   # 'errors' in lsr
            # Das Vorhandensein von 'errors' bedeutet, dass ein technisches
            # Problem das Auswerten der Karte verhindert hat. Das Einlesen
            # der Karte soll aufgezeichnet und später nachgeholt werden.
            self.headline_label.config(text="Ein Problem ist aufgetreten")
            self.msg_label.config(text="\n".join(lsr.get('errors', [""])) or "Die Ursache dieses Problems konnte nicht festgestellt werden.")
            self.msg_label.grid()
            self.extra_msg_label.config(text="Die Karte wurde korrekt eingelesen und aufgezeichnet. Die Übertragung wird bei nächster Gelegenheit automatisch nachgeholt.")

    def on_click_OK(self):
        self.winfo_toplevel().terminal.set_state(State.WELCOME)
