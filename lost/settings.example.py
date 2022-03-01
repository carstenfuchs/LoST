from pathlib import Path

# The terminal name is submitted along with the smartcard details to the
# server.
TERMINAL_NAME = 'entrance'

# In order to be able to recover from interruptions of network connectivity,
# all outgoing and incoming data is logged. Make sure the path is writable.
# SMARTCARD_LOGFILE_PATH = '/var/log/LoST/smartcards.log'
SMARTCARD_LOGFILE_PATH = Path(__file__).resolve().parent.parent / 'smartcards.log'

# The server address that captured smartcard details are posted to.
# To facilitate testing and development, use 'built-in' as the server name.
# This will start and use the server that is built into this program
# and that will reply with technically correct but otherwise contrived data.
# The testing server will be bound to 'localhost' and can act in place of a
# full Lori server when true content is not required.
# Examples:
#   # Starts and uses the built-in server at 'localhost':
#   SERVER_ADDRESS = ('built-in', 8000)
#   # Uses an external, different server at 'localhost':
#   SERVER_ADDRESS = ('localhost', 8000)
SERVER_ADDRESS = ('built-in', 8000)
