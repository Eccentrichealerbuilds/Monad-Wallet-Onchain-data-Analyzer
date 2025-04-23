import os
import sys
import logging
from dotenv import load_dotenv
logger = logging.getLogger(__name__)
load_dotenv()
BOT_TOKEN = os.getenv('T')
RPC_URL = os.getenv('R')
ME_API_KEY = os.getenv('MEK')
WALLET_API_KEY = os.getenv('WK')
NETWORK = 'monad-testnet'
WALLET_API_CHAIN_ID = 'monad-test-v2'
ME_BASE_URL = 'https://api-mainnet.magiceden.dev'
WALLET_API_BASE_URL = 'https://api.zerion.io/v1/'
if not BOT_TOKEN:
    logger.critical('CRITICAL: Bot token missing.')
    sys.exit(1)
if not RPC_URL:
    logger.critical('CRITICAL: RPC URL missing.')
    sys.exit(1)
if not ME_API_KEY:
    logger.warning('Warning: ME API Key missing.')
if not WALLET_API_KEY:
    logger.warning('Warning: Wallet API Key (WK) missing.')
try:
    COLLECTIONS_PAGE_SIZE = int(os.getenv('COLLECTIONS_PAGE_SIZE', 20))
except ValueError:
    logger.warning('Invalid page size')
    COLLECTIONS_PAGE_SIZE = 20
try:
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 10))
except ValueError:
    logger.warning('Invalid page size')
    ITEMS_PER_PAGE = 10
try:
    USER_ACTIVITY_PAGE_SIZE = int(os.getenv('USER_ACTIVITY_PAGE_SIZE', 15))
except ValueError:
    logger.warning('Invalid page size')
    USER_ACTIVITY_PAGE_SIZE = 15
try:
    TOKENS_PAGE_SIZE = int(os.getenv('TOKENS_PAGE_SIZE', 20))
except ValueError:
    logger.warning('Invalid page size')
    TOKENS_PAGE_SIZE = 20
try:
    TOP_COLL_LIMIT = int(os.getenv('TOP_COLL_LIMIT', 10))
except ValueError:
    logger.warning('Invalid limit')
    TOP_COLL_LIMIT = 10
try:
    TOP_COLL_RESULTS_PER_PAGE = int(os.getenv('TOP_COLL_RESULTS_PER_PAGE', 15))
except ValueError:
    logger.warning('Invalid page size')
    TOP_COLL_RESULTS_PER_PAGE = 30


BOT_COMMANDS = {
    "start":        "🟣 Starts the bot and shows welcome message.",
    "balance":      "🟣 Checks native token (MON) balance.\n☄➠ Usage: /balance <address>",
    "tokens":       "🟣 Lists other token balances (ERC20s).\n☄➠ Usage: /tokens <address>",
    "nfts":         "🟣 Shows summary of NFT collections owned.\n☄➠ Usage: /nfts <address>",
    "mynftactivity":"🟣 Shows recent NFT activity for wallet.\n☄➠ Usage: /mynftactivity <address>",
    "topcollections":"🟣 Shows top collections by volume/sales.\n☄➠ Interactive usage, no address needed.",
    "transactioncount":"🟣 Shows Nonce (outgoing tx count).\n☄➠ Usage: /transactioncount <address>",
    "uniquecontracts":"🟣 Scans all txs for unique interactions.\n☄➠ Can be slow. Usage: /uniquecontracts <address>",
    "commands":     "🟣 Displays this list of available commands."
}
