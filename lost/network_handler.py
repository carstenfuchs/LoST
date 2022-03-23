from datetime import datetime
import requests

import settings
from thread_tools import start_thread


REQUEST_TIMEOUT = 8.0


def post_stamp_event(user_input):
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
        return ({'errors': [str(e)]},)

    if r.status_code != 200:
        return ({'errors': ["status != 200"]},)

    try:
        json = r.json()
    except requests.exceptions.JSONDecodeError as e:
        return ({'errors': [str(e)]},)

    # The result of this thread is passed as a parameter to the callback
    # in the main thread.
    return (json,)


class NetworkHandler:

    def __init__(self, terminal):
        # TODO: Can we employ connection pooling?
        self.terminal = terminal
        self.logfile = open(settings.SMARTCARD_LOGFILE_PATH, mode='a', buffering=1)

    def shutdown(self):
        # TODO: Should use a context manager instead!
        # See https://realpython.com/python-with-statement/
        self.logfile.close()

    def send_to_Lori(self, smartcard_id):
        print(f"{datetime.now()} captured {smartcard_id}", file=self.logfile)
        # TODO – but be careful to not have a runaway counter.
        #   (e.g. reset after 10 Minutes idle?)
        # if num_of_requests_in_flight >= 5:
        #     # While we should never get here to send another request while the
        #     # one before that is still in flight and has not yet timed out,
        #     # make sure that any unforeseen circumstances cannot create an
        #     # unlimited number of threads.
        #     return

        user_input = {
            'smartcard_id': smartcard_id,
            'local_ts': str(datetime.now()),  # local timestamp
        }

        # Add the user input that was made in the terminal.
        user_input.update(self.terminal.get_user_input())

        start_thread(post_stamp_event, (user_input,), self.on_server_reply)

    def on_server_reply(self, msg):
        print(f"{datetime.now()} server reply: {msg}", file=self.logfile)
        self.terminal.on_server_reply_received(msg)
