from datetime import datetime
import dbm.gnu
import logging
import requests
import time

from lost import settings
from lost.thread_tools import start_thread


logger = logging.getLogger("lost.network")
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
            allow_redirects=False,
            verify=False,
        )

        # With `allow_redirects=True`, Requests turns POST requests that are
        # redirected automatically into GET requests when following them:
        #   - https://github.com/psf/requests/issues/3107
        #   - https://github.com/psf/requests/issues/5494
        # Therefore, we must implement POST-redirects ourselves.
        count = 5
        while count > 0 and r.status_code in (301, 302, 307, 308):
            count -= 1
            r = requests.post(
                r.headers['Location'],
                data=data,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                verify=False,
            )

    except requests.exceptions.ConnectionError as e:
        return user_input, {'error': f"ConnectionError: {e}"}, False

    except requests.exceptions.Timeout as e:
        return user_input, {'error': f"Timeout: {e}"}, False

    except requests.exceptions.RequestException as e:
        return user_input, {'error': f"RequestException: {e}"}, False

    if r.status_code != 200:
        return user_input, {'error': f"The HTTP status response code was {r.status_code}, expected 200 (OK)."}, False

    try:
        json_dict = r.json()
    except requests.exceptions.JSONDecodeError as e:
        return user_input, {'error': f"JSONDecodeError: {e}"}, False

    # The results of this thread are passed as parameters to the callback
    # in the main thread.
    return user_input, json_dict, True


class NetworkHandler:

    def __init__(self, terminal):
        # TODO: Can we employ connection pooling?
        self.terminal = terminal
        self.backlog = dbm.gnu.open('backlog.db', 'cs')
        self.time_next_backlog = 0
        self.time_last_sending = 0

    def shutdown(self):
        # TODO: Should use a context manager instead!
        # See https://realpython.com/python-with-statement/
        self.backlog.close()

    def send_to_Lori(self, smartcard_id):
        # This should never kick in, but let's throttle the number of network
        # transmissions and simultaneous threads anyway.
        now = time.time()
        if now - self.time_last_sending < 0.5:
            logger.error(f"send_to_Lori: Throttling network transmissions, dropping {smartcard_id = }!")
            return
        self.time_last_sending = now

        user_input = {
            'smartcard_id': smartcard_id,
            'local_ts': str(datetime.now()),  # local timestamp
        }

        # Add the user input that was made in the terminal.
        user_input.update(self.terminal.get_user_input())

        logger.info(f"send_to_Lori:")
        logger.info(f"    {user_input = }")

        is_backlog = False
        start_thread(post_stamp_event, (user_input, is_backlog), self.on_server_reply)

    def on_server_reply(self, user_input, result, network_success):
        logger.info(f"on_server_reply: {'success' if network_success else 'FAILURE'}")
        logger.info(f"    {user_input = }")
        logger.info(f"    {result = }")

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
