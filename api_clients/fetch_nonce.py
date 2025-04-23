import logging
from web3 import Web3
from web3.exceptions import InvalidAddress
from .rpc_setup import w3
from typing import Optional, Tuple
logger = logging.getLogger(__name__)


def fetch_address_nonce(address: str) ->Tuple[Optional[int], Optional[str]]:
    """
    Fetches the nonce (outgoing transaction count) for a given address via RPC.

    Args:
        address: The wallet address to query.

    Returns:
        A tuple: (nonce_count or None, error_message or None)
    """
    if not w3:
        return None, 'Error: RPC connection not available.'
    try:
        checksum_address = Web3.to_checksum_address(address)
        nonce = w3.eth.get_transaction_count(checksum_address)
        logger.debug(f'Successfully fetched nonce {nonce} for {address}')
        return nonce, None
    except InvalidAddress:
        logger.warning(f'Invalid address format for nonce check: {address}')
        return None, f'Error: Invalid address format provided.'
    except Exception as e:
        logger.error(f'Error fetching nonce via RPC for {address}: {e}')
        return None, f'An unexpected RPC error occurred while fetching nonce.'
