from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString

from thread_tools import thread_queue


class SmartcardMonitor:

    def __init__(self, terminal, network_handler):
        self.terminal = terminal
        self.network_handler = network_handler
        self.cardmonitor = CardMonitor()
        self.cardobserver = LoSTCardObserver(self.on_smartcard_input)
        self.cardmonitor.addObserver(self.cardobserver)

    def shutdown(self):
        self.cardmonitor.deleteObserver(self.cardobserver)
        self.cardobserver = None
        self.cardmonitor = None

    def on_smartcard_input(self, response, success):
        """
        This function is called when a smartcard has been read by the `LoSTCardObserver`.
        It is a callback that runs in the program's main thread.
        """
        if not self.terminal.expect_smartcard():
            return

        # Send the smartcard details in a POST request to the server.
        self.network_handler.send_to_Lori(response)
        self.terminal.set_state_Wait_For_Sv_Reply()


# https://stackoverflow.com/questions/13051167/apdu-command-to-get-smart-card-uid
# https://stackoverflow.com/questions/9514684/what-apdu-command-gets-card-id
# https://stackoverflow.com/questions/29819356/apdu-for-getting-uid-from-mifare-desfire
# https://de.wikipedia.org/wiki/Application_Protocol_Data_Unit
GET_UID = [
    0xFF,   # CLA  class
    0xCA,   # INS  instruction
    0x00,   # P1   first parameter
    0x00,   # P2   second parameter
    0x00,   # Le   length expected
    # Le == 0x00 means that the full length is to be returned:
    #   - for ISO 14443-A: single 4 bytes, double 7 bytes, triple 10 bytes,
    #   - for ISO 14443-B: 4 bytes PUPI,
    #   - for ISO 15693: 8 bytes UID
]


class LoSTCardObserver(CardObserver):
    """
    A card observer is notified when cards are added to
    or removed from a smart card reader in the system.
    """
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def update(self, observable, actions):
        # `observable` is the CardMonitor instance.
        (addedCards, removedCards) = actions

        for card in addedCards:
            if not card.atr:
                continue

            # The ATR can be decoded at https://smartcard-atr.apdu.fr/
            print(f'Smartcard: [💳] user inserted card "{toHexString(card.atr)}"')

            card.connection = card.createConnection()
            card.connection.connect()
            response, sw1, sw2 = card.connection.transmit(GET_UID)
            card.connection.disconnect()

            success = sw1 in (0x90, 0x61)
            print(f'Smartcard: [💳] read card UID: status 0x{sw1:02x} 0x{sw2:02x}, result "{toHexString(response)}"')

            # We are running in a worker thread of the `CardMonitor` here.
            # Thus, put the callback and the results into the queue, to be
            # picked up and processed in the main thread later.
            thread_queue.put((self.callback, (response, success)))

        for card in removedCards:
            print(f'Smartcard: [--] user removed card "{toHexString(card.atr)}"')
