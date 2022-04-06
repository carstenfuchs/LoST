import dbm.gnu
import json
import logging
import requests

from lost import settings
from lost.common import get_datetime_now, get_time_time
from lost.thread_tools import start_thread


logger = logging.getLogger("lost.network")
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

    def __init__(self, terminal, backlog_path='backlog.db'):
        # TODO: Can we employ connection pooling?
        self.terminal = terminal
        self.backlog = dbm.gnu.open(backlog_path, 'cs')
        self.time_next_backlog = 0
        self.time_last_sending = 0

    def shutdown(self):
        # TODO: Should use a context manager instead!
        # See https://realpython.com/python-with-statement/
        self.backlog.close()

    def send_to_Lori(self, smartcard_id):
        # This should never kick in, but let's throttle the number of network
        # transmissions and simultaneous threads anyway.
        now = get_time_time()
        if now - self.time_last_sending < 0.5:
            logger.error(f"send_to_Lori(): Throttling network transmissions, dropping {smartcard_id = }!")
            logger.error(f"    {self.time_last_sending = }, {now = }")
            return
        self.time_last_sending = now

        user_input = {
            'smartcard_id': smartcard_id,
            'local_ts': str(get_datetime_now()),  # local timestamp
            'backlog_count': 0,
        }

        # Add the user input that was made in the terminal.
        user_input.update(self.terminal.get_user_input())

        logger.info(f"send_to_Lori():")
        logger.info(f"    {user_input = }")

        start_thread(post_stamp_event, (user_input,), self.on_server_reply)

    def catch_up_backlog(self):
        """If there is anything in the backlog, try to file it now."""
        now = get_time_time()
        if now < self.time_next_backlog:
            return

        # It is unclear in which order the keys are returned, for details see:
        # https://docs.python.org/3/library/dbm.html#module-dbm.gnu
        unique_id = self.backlog.firstkey()

        if unique_id is None:
            # The backlog is empty. Unless something else happens that overrides this,
            # only try again much later.
            logger.info(f"catch_up_backlog(): The backlog is empty.")
            self.time_next_backlog = now + 24 * 3600
            return

        user_input_json = self.backlog[unique_id]
        del self.backlog[unique_id]
        self.backlog.sync()

        try:
            user_input = json.loads(user_input_json)
        except json.JSONDecodeError as e:
            logger.error(f"catch_up_backlog(): Invalid JSON in backlog: {e}")
            logger.error(f"    backlog['{unique_id.decode()}'] = '{user_input_json.decode()}'")
            self.time_next_backlog = now + 1
            return

        # Actually re-send old user input from the backlog.
        # Note that the interruption of network connectivity that caused the original
        # transmission to fail might still persist and thus cause new transmissions to
        # fail as well. Therefore, don't send items in the backlog in an overly quick
        # succession: They would just get reinserted.
        self.time_next_backlog = now + 2*REQUEST_TIMEOUT

        logger.info(f"catch_up_backlog():")
        logger.info(f"    {user_input = }")

        start_thread(post_stamp_event, (user_input,), self.on_server_reply)

    def on_server_reply(self, user_input, result, network_success):
        """
        A thread that was running `requests.post()` has finished with a reply or an error.
        """
        logger.info(f"on_server_reply():")
        logger.info(f"    {network_success = }")
        logger.info(f"    {user_input = }")
        logger.info(f"    {result = }")

        was_backlogged = (user_input['backlog_count'] > 0)

        if not network_success:
            # Something went wrong with the network transmission. For example, the network
            # connectivity might have been interrupted and the transmission timed out.
            # In any case, we must assume that the Lori server never received the message.
            # No matter if this was the first attempt of a user who is still attending the
            # terminal or an attempt to catch up with the backlog days later, we must put
            # the issue into the backlog to try again later.

            # if len(self.backlog) > 10000:
            #     pass

            user_input['backlog_count'] += 1

            now = get_time_time()
            unique_id = str(now)
            user_input_json = json.dumps(user_input)
            logger.info(f"    --> backlog['{unique_id}'] = '{user_input_json}'")

            self.backlog[unique_id] = user_input_json
            self.backlog.sync()
            self.time_next_backlog = now + 300.0

            result['extra_message'] = (
                "Der Lori-Server konnte nicht erreicht und die Eingabe demzufolge "
                "nicht verarbeitet werden. Die Eingabe wurde aber aufgezeichnet "
                "und die Verarbeitung wird sobald wie möglich automatisch nachgeholt."
            )

        if was_backlogged:
            # This is the reply to user input that was re-sent from the backlog.
            # No matter if it was now a success or another failure: the user has long left
            # and no one is watching the terminal's screen, so don't bother updating it.
            logger.info(f"    --> not updating the terminal")
            return

        self.terminal.on_server_reply_received(result)
