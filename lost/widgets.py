import logging
import os
import subprocess
import time
from datetime import datetime
from shutil import disk_usage
from tkinter import *
from tkinter import font as tkfont
# from tkinter import ttk

import settings


logger = logging.getLogger("lost.gui")


class ColorProvider:

    def __init__(self):
        self.count = 0
        self.colors = []

        for g in (0x00, 0x22, 0x44):
            for b in (0x33, 0x66, 0x99):
                self.colors.append('#{:02x}{:02x}{:02x}'.format(0, g, b))

    def get_bg_col(self, default='black'):
        if settings.DEBUG:
            # r = lambda: randint(0, 255)
            # return '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
            self.count += 1
            return self.colors[self.count % len(self.colors)]

        return default


class FontProvider:

    def __init__(self):
        self.win_size_factor = 16.0
        self.fonts = {}

        # logger.debug("\nFont names:")
        # for n in tkfont.names():
        #     logger.debug(f"  {n:18s} {tkfont.nametofont(n).actual()}")

        # logger.debug("\nFont families:")
        # logger.debug(sorted(tkfont.families()))

    def resize(self, window_height):
        """Updates the size of each font according to the new window height."""
        self.win_size_factor = window_height / 480.0 * 25.0

        for percent, font in self.fonts.items():
            font.config(size=-int(self.win_size_factor * percent / 100.0))

    def get_font(self, percent):
        if percent in self.fonts:
            return self.fonts[percent]

        f = tkfont.nametofont('TkTextFont').copy()
        f.config(size=-int(self.win_size_factor * percent / 100.0))

        logger.debug(f"Adding font size {percent} %")
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


class TouchButton(Button):

    def __init__(self, parent, font_size=100, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.config(
            font=fp.get_font(font_size),
            foreground='white',
            background='#555555',
            activeforeground='white',     # mouse hover color
            activebackground='#555555',   # mouse hover color
            highlightbackground='black',  # used as base color for the border?
        )

    def set_active(self, active):
        bg = '#3380E6' if active else '#555555'
        self.config(
            background=bg,
            activebackground=bg,
          # highlightbackground='red',
        )


class TitleBar(Frame):

    def __init__(self, parent, show_clock=True, border_color='#3380E6', *args, **kwargs):
        super().__init__(parent, *args, **kwargs, background=cp.get_bg_col())

        self.columnconfigure(0, weight=1, uniform='u')   # "Rofu Kinderland"
        self.columnconfigure(1, weight=1, uniform='u')   # HH:MM
        self.columnconfigure(2, weight=1, uniform='u')   # "Lori"

        rofu_label = Label(self, text="Rofu Kinderland", foreground='white', background=cp.get_bg_col(), font=fp.get_font(60))
        rofu_label.grid(row=0, column=0, sticky="W", padx=10, pady=8)

        self.clock = Label(self, foreground='white', background=cp.get_bg_col(), font=fp.get_font(60))
        self.clock.grid(row=0, column=1, padx=5, pady=8)

        lori_label = Label(self, text="Lori", foreground='white', background=cp.get_bg_col(), font=fp.get_font(60))
        lori_label.grid(row=0, column=2, sticky="E", padx=10, pady=8)

        bottom_border = Frame(self, height=2, background=border_color)
        bottom_border.grid(row=1, column=0, columnspan=3, sticky="NESW")

        self.bind('<Button-1>', self.on_LMB_click)

        if show_clock:
            self.update_clock()

    def on_LMB_click(self, event):
        self.winfo_toplevel().terminal.set_state_welcome()

    def update_clock(self):
        self.clock.config(text=datetime.now().strftime("%H:%M"))
        self.after(1000, self.update_clock)


class PauseButtonsRow(Frame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.columnconfigure([0, 1, 2, 3, 4, 5], weight=1, uniform='pause_btn')

        # Have the grid span the full height of the frame
        # (instead of only the minimal height to enclose its children).
        self.rowconfigure(0, weight=1)

        button_labels = ('0:00', '0:15', '0:30', '0:45', '1:00', '+15')
        self.buttons = [TouchButton(self, text=label) for label in button_labels]

        for nr, btn in enumerate(self.buttons):
            btn.grid(row=0, column=nr, sticky="NESW")
            btn.bind('<Button-1>', self.on_LMB_click)

    def update_to_model(self, terminal):
        p_str = ''
        if terminal.pause is not None:
            p_str = f"{terminal.pause // 60}:{terminal.pause % 60:02}"

        for btn in self.buttons:
            btn.set_active(btn.cget('text') == p_str)

    def on_LMB_click(self, event):
        text = event.widget.cget('text')
        mdl_pause = self.winfo_toplevel().terminal.pause

        if mdl_pause == 120 + 45 and text == '0:45':
            # A pause of 2:45 hours followed by a click on '0:45' opens the system panel.
            logger.info("Invoking the system panel.")
            self.winfo_toplevel().terminal.set_state_system_panel()
            return

        if text == '+15':
            if mdl_pause is None:
                mdl_pause = 15
            else:
                mdl_pause = min(mdl_pause + 15, 180)
        else:
            p = int(text[:-3])*60 + int(text[-2:])
            mdl_pause = None if mdl_pause == p else p

        self.winfo_toplevel().terminal.set_pause(mdl_pause)


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
        self.columnconfigure(2, weight=2)   # Notes (optional)

        self.time_labels = []
        self.note_labels = []

        for row_nr, col_text in enumerate(("Anfang", "Ende", "Pause", "Ergebnis")):
            l = Label(self, text=col_text, background=cp.get_bg_col(), foreground='white', font=fp.get_font(120))
            l.grid(row=row_nr, column=0, sticky="NSW", padx=0, pady=1)

        for row_nr in range(4):
            l = Label(self, text="", background=cp.get_bg_col(), foreground='white', font=fp.get_font(120))
            l.grid(row=row_nr, column=1, sticky="E", padx=8)
            self.time_labels.append(l)

        for row_nr in range(4):
            l = Label(self, text="", background=cp.get_bg_col(), foreground='#666666', font=fp.get_font(70))
            l.grid(row=row_nr, column=2, sticky="W", padx=(24, 8))
            self.note_labels.append(l)

    def update_to_model(self, terminal):
        lsr = terminal.last_server_reply
        feedback = lsr.get('feedback', {})
        empty = "____"

        anfang = feedback.get('anfang')
        if anfang:
            self.time_labels[0].config(text=anfang, foreground='white')
            self.note_labels[0].config(text="ok")
        else:
            self.time_labels[0].config(text=empty, foreground='#666666')
            self.note_labels[0].config(text="noch nicht ableitbar")

        ende = feedback.get('ende')
        if ende:
            self.time_labels[1].config(text=ende, foreground='white')
            self.note_labels[1].config(text="ok")
        else:
            self.time_labels[1].config(text=empty, foreground='#666666')
            self.note_labels[1].config(text="noch nicht ableitbar")

        pause = feedback.get('pause')
        if pause:
            self.time_labels[2].config(text=pause, foreground='white')
        else:
            self.time_labels[2].config(text=empty, foreground='#666666')

        pause_error = feedback.get('pause_error')
        if pause_error:
            self.note_labels[2].config(text="Problem")
            self.note_labels[2].config(foreground='#CC0000')
        else:
            self.note_labels[2].config(text="ok" if pause else "noch nicht ableitbar")
            self.note_labels[2].config(foreground='#666666')

        result = feedback.get('result')
        if result:
            self.time_labels[3].config(text=result, foreground='white')
            self.note_labels[3].config(text="")
        else:
            self.time_labels[3].config(text=empty, foreground='#666666')
            self.note_labels[3].config(text="")


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
        self.rowconfigure(ROW_NR_HEADLINE,      weight=4, uniform='u')
        self.rowconfigure(ROW_NR_BORDER_TOP,    weight=0)
        self.rowconfigure(ROW_NR_BODY,          weight=9, uniform='u')
        self.rowconfigure(ROW_NR_BORDER_BOTTOM, weight=0)
        self.rowconfigure(ROW_NR_EXTRA_MSG,     weight=3, uniform='u')
        self.rowconfigure(ROW_NR_OK_BUTTON,     weight=3, uniform='u')
        self.rowconfigure(ROW_NR_BOTTOM_SPACE,  weight=1, uniform='u')

        # Have the grid span the full width of the frame
        # (instead of only the minimal width to enclose its children).
        self.columnconfigure(0, weight=1)

      # title_bar = TitleBar(self, show_clock=False)
      # title_bar.grid(row=ROW_NR_TITLE_BAR, column=0, sticky="NESW")

        PAD_X = (20, 8)

        self.headline_label = Label(self, text="", background=cp.get_bg_col(), foreground='white', anchor='sw', font=fp.get_font(150))
        self.headline_label.grid(row=ROW_NR_HEADLINE, column=0, sticky="NESW", padx=PAD_X, pady=2)

        self.border_top = Frame(self, height=2, background='orange')
        self.border_top.grid(row=ROW_NR_BORDER_TOP, column=0, sticky="NESW")

        # The `body_grid` and the `msg_label` share the common row `ROW_NR_BODY`.
        self.body_grid = WorkHoursReplyGrid(self)
        self.body_grid.grid(row=ROW_NR_BODY, column=0, sticky="NESW", padx=PAD_X, pady=10)

        self.msg_label = Label(self, text="", wraplength=300, justify='left', background=cp.get_bg_col(), foreground='white', anchor='w', font=fp.get_font(100))
        self.msg_label.grid(row=ROW_NR_BODY, column=0, sticky="EW", padx=PAD_X)
        self.msg_label.bind('<Configure>', adjust_wraplength)

        self.border_bottom = Frame(self, height=2, background='orange')
        self.border_bottom.grid(row=ROW_NR_BORDER_BOTTOM, column=0, sticky="NESW")

        self.extra_msg_label = Label(self, text="", wraplength=300, justify='left', background=cp.get_bg_col(), foreground='white', anchor='w', font=fp.get_font(100))
        self.extra_msg_label.grid(row=ROW_NR_EXTRA_MSG, column=0, sticky="NESW", padx=PAD_X, pady=2)
        self.extra_msg_label.bind('<Configure>', adjust_wraplength)

        # The row with the "OK" button.
        buttons_row = Frame(self, background=cp.get_bg_col())
        # Have the grid span the full height of its frame (which in turn is
        # fully NESW-expanded to its parent cell below). Without `rowconfigure()`,
        # the grid would only get the height of its children.
        buttons_row.rowconfigure(0, weight=1)
        buttons_row.columnconfigure(0, weight=10)
        buttons_row.columnconfigure(1, weight=2)
        buttons_row.grid(row=ROW_NR_OK_BUTTON, column=0, sticky="NESW", padx=(PAD_X[0], PAD_X[0]))

        ok_button = TouchButton(buttons_row, text="OK", command=self.on_click_OK)
        ok_button.grid(row=0, column=1, sticky="NESW")

    def update_to_model(self, terminal):
        lsr = terminal.last_server_reply

        self.body_grid.grid_remove()
        self.msg_label.grid_remove()

        if 'ma' in lsr:
            feedback = lsr.get('feedback', {})
            self.headline_label.config(text=lsr['ma'])
            self.border_top.config(background='#00FF66')
            self.body_grid.update_to_model(terminal)
            self.body_grid.grid()
            self.msg_label.config(text="")
            self.border_bottom.config(background='#00FF66')
            self.extra_msg_label.config(text=feedback.get('pause_error'))
        elif 'messages' in lsr:
            # Das Einscannen der Karte hat zwar nicht zu einer Aufzeichnung
            # eines Timestamps geführt, aber es handelte sich trotzdem um eine
            # ordentliche, regelkonforme Verarbeitung.
            self.headline_label.config(text="Verarbeitung durch den Lori-Server")
            self.border_top.config(background='#FFFF00')
            self.msg_label.config(text="\n".join(lsr['messages']))
            self.msg_label.grid()
            self.border_bottom.config(background='#FFFF00')
            self.extra_msg_label.config(text="")
        else:   # 'errors' in lsr
            # Das Vorhandensein von 'errors' bedeutet, dass ein technisches
            # Problem das Auswerten der Karte verhindert hat. Das Einlesen
            # der Karte soll aufgezeichnet und später nachgeholt werden.
            self.headline_label.config(text="Ein Problem ist aufgetreten")
            self.border_top.config(background='#FF0000')
            self.msg_label.config(text="\n".join(lsr.get('errors', [""])) or "Die Ursache dieses Problems konnte nicht festgestellt werden.")
            self.msg_label.grid()
            self.border_bottom.config(background='#FF0000')
            self.extra_msg_label.config(text="Die Karte wurde korrekt eingelesen und aufgezeichnet. Die Übertragung wird bei nächster Gelegenheit automatisch nachgeholt.")

    def on_click_OK(self):
        self.winfo_toplevel().terminal.set_state_welcome()


def fmt_bytes(size, decimal_places=2):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0

    return f"{size:.{decimal_places}f} {unit:3}"


class SystemPanelFrame(Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, background=cp.get_bg_col())

        self.rowconfigure(0, weight=0)               # title bar
        self.rowconfigure(1, weight=3, uniform='u')  # headline
        self.rowconfigure(2, weight=2, uniform='u')  # quit program
        self.rowconfigure(3, weight=2, uniform='u')  # system shutdown
        self.rowconfigure(4, weight=1, uniform='u')  # vertical space
        self.rowconfigure(5, weight=2, uniform='u')  # "back" button
        self.rowconfigure(6, weight=1, uniform='u')  # vertical space

        self.columnconfigure(0, weight=1, uniform='a')  # buttons
        self.columnconfigure(1, weight=1, uniform='a')  # system info text

        title_bar = TitleBar(self, show_clock=True, border_color='#FF7722')
        title_bar.grid(row=0, column=0, columnspan=2, sticky="NESW")

        headline_label = Label(self, text="System", foreground='white', background=cp.get_bg_col(), anchor='w', font=fp.get_font(150))
        headline_label.grid(row=1, column=0, columnspan=2, sticky="NESW", padx=10)

        quit_button = TouchButton(self, text="Programm beenden", anchor='w', command=self.on_click_quit_program)
        quit_button.grid(row=2, column=0, sticky="NESW", padx=10)
        shut_button = TouchButton(self, text="System herunterfahren", anchor='w', command=self.on_click_shutdown)
        shut_button.grid(row=3, column=0, sticky="NESW", padx=10)
        back_button = TouchButton(self, text="← zurück zum Terminal", anchor='w', command=self.on_click_back)
        back_button.grid(row=5, column=0, sticky="NESW", padx=10)

        # The `rowspan` below seems to adversely affect the `uniform='u'` above.
        # A bug in Tkinter?
        self.sysinfo_label = Label(self, text="", foreground='#FF7722', justify='left', anchor='n', background=cp.get_bg_col(), font=fp.get_font(70))
        self.sysinfo_label.grid(row=2, rowspan=4, column=1, sticky="NESW", padx=(0, 10))

        self.time_updated = None
        self.update_system_info()

    def update_to_model(self, terminal):
        self.time_updated = time.time()

    def on_click_quit_program(self):
        logger.info("Quitting program.")
        self.winfo_toplevel().destroy()

    def on_click_shutdown(self):
        logger.info("System shutdown initiated.")
        # The shutdown is delayed by one minute as that gives us a chance to gracefully
        # exit the program and the user a chance to cancel.
        subprocess.run(['shutdown', '--poweroff', '+1'])
        self.winfo_toplevel().destroy()

    def on_click_back(self):
        self.winfo_toplevel().terminal.set_state_welcome()

    def update_system_info(self):
        self.after(1000, self.update_system_info)

        if self.time_updated is None:
            return

        if time.time() - self.time_updated > 30.0:
            return

        # A lot is left to be done here, especially about proper exception handling and
        # error checking. Regarding additional features, see:
        #   - https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd
        #   - https://znil.net/index.php/Temperatur_/_Spannung_etc._des_Raspberry_Pi_selbst_auslesen
        #   - https://raspberrypi.stackexchange.com/questions/105811/measuring-the-cpu-temp-and-gpu-temp-in-bash-and-python-3-5-3-pi-2-3b-3b-4b

        sysinfo = ""
        sysinfo += f"System load:\n{os.getloadavg()}\n"

        disk_total, disk_used, disk_free = disk_usage("/")
        sysinfo += f"\nDisk usage:\n{fmt_bytes(disk_used)} used\n{fmt_bytes(disk_free)} free\n"

        with open("/sys/class/thermal/thermal_zone0/temp") as temp_file:
            # https://www.elektronik-kompendium.de/sites/raspberry-pi/1911241.htm
            # https://raspberrypi.stackexchange.com/questions/41784/temperature-differences-between-cpu-gpu
            cpu_temp = temp_file.readline().strip()

        sysinfo += f"\nCPU core temperature:\n{float(cpu_temp)/1000} °C\n"
        sysinfo += f"\nGPU core temperature:\nunavailable\n"

        self.sysinfo_label.config(text=sysinfo)
