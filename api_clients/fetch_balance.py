import logging
from web3 import Web3
from web3.exceptions import InvalidAddress
from .rpc_setup import w3
logger = logging.getLogger(__name__)


def fetch_native_balance(address: str) ->str:
    if not w3:
        return 'Error: RPC connection not available.'
    try:
        checksum_address = Web3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_native = w3.from_wei(balance_wei, 'ether')
        balance_str = '{:f}'.format(balance_native.normalize())
        return f'Balance: {balance_str} MON'
    except InvalidAddress:
        logger.warning(f'Invalid address format received: {address}')
        return f'Error: Invalid address format provided.'
    except Exception as e:
        logger.error(f'Error fetching balance via RPC for {address}: {e}')
        return f'An unexpected error occurred while fetching balance.'
