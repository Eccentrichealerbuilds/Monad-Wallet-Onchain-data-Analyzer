import logging
from web3 import Web3
from config import RPC_URL
logger = logging.getLogger(__name__)
w3 = None
if not RPC_URL:
    logger.error('RPC_URL not found in config.')
else:
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            logger.error(
                f'Failed to connect to RPC endpoint defined in config.')
            w3 = None
        else:
            logger.info(f'Successfully connected to RPC endpoint.')
    except Exception as e:
        logger.error(f'Error initializing Web3 connection: {e}')
        w3 = None
