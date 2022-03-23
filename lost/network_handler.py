from datetime import datetime
import dbm.gnu
import requests
import time

import settings
from thread_tools import start_thread


REQUEST_TIMEOUT = 8.0


def post_stamp_event(user_input, is_backlog):
    """Sends the smartcard details in a POST request to the server."""
    SERVER_NAME = settings.SERVER_ADDRESS[0]
    SERVER_PORT = settings.SERVER_ADDRESS[1]

    if SERVER_NAME == 'built-in':
        SERVER_NAME = 'localhost'

    data = user_input.copy()
    data.update(
        {
            'terminal_name': settings.TERMINAL_NAME,
            'terminal_pwd': settings.TERMINAL_PASSWORD,
            'is_backlog': is_backlog,
        }
    )

    try:
        r = requests.post(
            f"http://{SERVER_NAME}:{SERVER_PORT}{settings.SERVER_URL}",
            data=data,
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.exceptions.Timeout as e:
        return user_input, {'errors': [str(e)]}, False

    if r.status_code != 200:
        return user_input, {'errors': ["status != 200"]}, False

    try:
        json = r.json()
    except requests.exceptions.JSONDecodeError as e:
        return user_input, {'errors': [str(e)]}, True

    # The results of this thread are passed as parameters to the callback
    # in the main thread.
    return user_input, json, True


class NetworkHandler:

    def __init__(self, terminal):
        # TODO: Can we employ connection pooling?
        self.terminal = terminal
        self.backlog = dbm.gnu.open('backlog.db', 'cs')
        self.time_next_backlog = 0
        self.time_last_sending = 0
        self.logfile = open(settings.SMARTCARD_LOGFILE_PATH, mode='a', buffering=1)

    def shutdown(self):
        # TODO: Should use a context manager instead!
        # See https://realpython.com/python-with-statement/
        self.logfile.close()
        self.backlog.close()

    def send_to_Lori(self, smartcard_id):
        print(f"{datetime.now()} captured {smartcard_id}", file=self.logfile)

        # This should never kick in, but let's throttle the number of network
        # transmissions and simultaneous threads anyway.
        now = time.time()
        if now - self.time_last_sending < 0.5:
            print("Throttling network transmissions, DROPPING data!", file=self.logfile)
            return
        self.time_last_sending = now

        user_input = {
            'smartcard_id': smartcard_id,
            'local_ts': str(datetime.now()),  # local timestamp
        }

        # Add the user input that was made in the terminal.
        user_input.update(self.terminal.get_user_input())

        is_backlog = False
        start_thread(post_stamp_event, (user_input, is_backlog), self.on_server_reply)

    def on_server_reply(self, user_input, result, network_success):
        print(f"{datetime.now()} server reply: {result}", file=self.logfile)

        if not network_success:
            # Something went wrong with the network transmission. Very likely, the network
            # connectivity was interrupted, the transmission timed out and the Lori server
            # never received the message. Thus, try again later.
            now = time.time()
            unique_id = user_input['local_ts']
            self.backlog[unique_id] = json.dumps(user_input)
            self.backlog.sync()
            self.time_next_backlog = max(self.time_next_backlog, now + 300.0)

        # if the user_input['local_ts'] is older than 1 minute:
        #     # Either don't show anything at all or just show something simple, such as
        #     # "Backlog: Eingabe zur Mitarbeiterkarte 1234 von 11:11 Uhr erfolgreich nachgetragen."
        #     return

        self.terminal.on_server_reply_received(result)

    def catch_up_backlog(self):
        """If there is anything in the backlog, try to file it now."""
        if not self.backlog:
            return

        now = time.time()
        if now < self.time_next_backlog:
            return

        unique_id, user_input_json = self.backlog.popitem()   # LIFO, unfortunately.
        self.backlog.sync()
        self.time_next_backlog = max(self.time_next_backlog, now + 2*REQUEST_TIMEOUT)

        user_input = json.load(user_input_json)
        is_backlog = True
        start_thread(post_stamp_event, (user_input, is_backlog), self.on_server_reply)
