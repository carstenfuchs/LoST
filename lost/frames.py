from babel.dates import format_datetime
from datetime import datetime
from tkinter import *
from tkinter import ttk
from model import Intention


class TopBar(Frame):

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
        # reset GUI
        self.winfo_toplevel().model.set_intention(None)

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

        title_bar = TopBar(self, show_clock=False)
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
        self.winfo_toplevel().model.set_intention(Intention.ARBEITS_ANFANG)

    def on_click_Arbeitsende(self):
        self.winfo_toplevel().model.set_intention(Intention.ARBEITS_ENDE)

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

        title_bar = TopBar(self)
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

    def update_to_model(self, model):
        active_col = '#66CCFF'
        inactive_col = '#666666'

        self.schicht_button.config(
            background=active_col if model.intention == Intention.ARBEITS_ANFANG_SCHICHT else inactive_col,
            activebackground=active_col if model.intention == Intention.ARBEITS_ANFANG_SCHICHT else inactive_col,   # mouse hover color
          # highlightbackground='red',      # used as base color for the border?
        )

        self.jetzt_button.config(
            background=active_col if model.intention == Intention.ARBEITS_ANFANG_JETZT else inactive_col,
            activebackground=active_col if model.intention == Intention.ARBEITS_ANFANG_JETZT else inactive_col,   # mouse hover color
          # highlightbackground='red',      # used as base color for the border?
        )

    def on_click_Anfang_Jetzt(self):
        self.winfo_toplevel().model.set_intention(Intention.ARBEITS_ANFANG_JETZT)

    def on_click_Anfang_Schicht(self):
        self.winfo_toplevel().model.set_intention(Intention.ARBEITS_ANFANG_SCHICHT)


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

    def update_to_model(self, model):
        active_col = '#66CCFF'
        inactive_col = '#666666'
        dept_str = model.department

        for btn in self.buttons:
            btn.config(
                background=active_col if btn.cget('text') == dept_str else inactive_col,
                activebackground=active_col if btn.cget('text') == dept_str else inactive_col,   # mouse hover color
              # highlightbackground='red',      # used as base color for the border?
            )

    def on_LMB_click(self, event):
        text = event.widget.cget('text')
        mdl = self.winfo_toplevel().model
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

    def update_to_model(self, model):
        active_col = '#66CCFF'
        inactive_col = '#666666'

        p_str = ''
        if model.pause is not None:
            p_str = f"{model.pause // 60}:{model.pause % 60:02}"

        for btn in self.buttons:
            btn.config(
                background=active_col if btn.cget('text') == p_str else inactive_col,
                activebackground=active_col if btn.cget('text') == p_str else inactive_col,   # mouse hover color
              # highlightbackground='red',      # used as base color for the border?
            )

    def on_LMB_click(self, event):
        text = event.widget.cget('text')
        mdl_pause = self.winfo_toplevel().model.pause

        if text == '+15':
            if mdl_pause is None:
                mdl_pause = 15
            else:
                mdl_pause = min(mdl_pause + 15, 180)
        else:
            p = int(text[:-3])*60 + int(text[-2:])
            mdl_pause = None if mdl_pause == p else p

        self.winfo_toplevel().model.set_pause(mdl_pause)


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

        title_bar = TopBar(self)
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

    def update_to_model(self, model):
        dept_str = "Bereich"
        if model.department is not None:
            dept_str += f" {model.department}"

        self.dept_label.config(text=dept_str)
        self.dept_grid.update_to_model(model)

        p_str = "Pause"
        if model.pause is not None:
            p_str += f" {model.pause // 60}:{model.pause % 60:02}"

        self.pause_label.config(text=p_str)
        self.pause_buttons.update_to_model(model)


class SendingFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background='#333333')

        sending_label = Label(self, text="Sende …", background="blue", foreground="#FFCCCC")
        sending_label.pack(side=TOP, fill=BOTH, expand=True)


class FeedbackFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background='#33AA66')

        sending_label = Label(self, text="Sende …", background="green", foreground="white")
        sending_label.pack(side=TOP, fill=BOTH, expand=True)
