from datetime import datetime
import requests

import settings
from thread_tools import start_thread


def post_stamp_event(smartcard_name):
    """Sends the smartcard details in a POST request to the server."""
    SERVER_NAME = settings.SERVER_ADDRESS[0]
    SERVER_PORT = settings.SERVER_ADDRESS[1]

    if SERVER_NAME == 'built-in':
        SERVER_NAME = 'localhost'

    try:
        r = requests.post(
            f"http://{SERVER_NAME}:{SERVER_PORT}{settings.SERVER_URL}",
            data={
                'terminal_name': settings.TERMINAL_NAME,
                'pwd': settings.TERMINAL_PASSWORD,
                'tag_id': str(smartcard_name),
            },
            timeout=8.0,
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
        self.logfile = open(settings.SMARTCARD_LOGFILE_PATH, mode='a', buffering=1)
        self.terminal = terminal

    def send_to_Lori(self, smartcard_name):
        print(f"{datetime.now()} captured {smartcard_name}", file=self.logfile)
        # TODO – but be careful to not have a runaway counter.
        #   (e.g. reset after 10 Minutes idle?)
        # if num_of_requests_in_flight >= 5:
        #     # While we should never get here to send another request while the
        #     # one before that is still in flight and has not yet timed out,
        #     # make sure that any unforeseen circumstances cannot create an
        #     # unlimited number of threads.
        #     return
        start_thread(post_stamp_event, (smartcard_name,), self.on_server_reply)

    def on_server_reply(self, msg):
        print(f"{datetime.now()} server reply: {msg}", file=self.logfile)
        self.terminal.on_server_reply_received(msg)
