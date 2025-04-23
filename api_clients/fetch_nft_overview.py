import logging
from typing import Optional, List, Dict, Any, Tuple
from .me_helper import _fetch_page_m
from config import ME_API_KEY, NETWORK
logger = logging.getLogger(__name__)


async def fetch_nft_overview(contract_address: str, token_id: str) ->Tuple[
    Optional[Dict[str, Any]], Optional[str]]:
    if not ME_API_KEY:
        return None, 'Error: NFT API Key not configured.'
    if not contract_address or token_id is None:
        return None, 'Error: Contract address and Token ID required.'
    endpoint_tmpl = f'/v3/rtp/{NETWORK}/tokens/v6'
    base_params = {'collection': contract_address, 'tokenId': token_id,
        'includeTopBid': True, 'includeAttributes': True, 'includeLastSale':
        True, 'normalizeRoyalties': True}
    item_list, result_or_error = await _fetch_page_m(endpoint_tmpl=
        endpoint_tmpl, params=base_params, api_key=ME_API_KEY, lmt=1)
    if item_list is None:
        return None, result_or_error
    elif isinstance(item_list, list) and len(item_list) > 0:
        if isinstance(item_list[0], dict):
            return item_list[0], None
        else:
            logger.error(
                f'Received non-dict item in list for NFT overview: {item_list[0]}'
                )
            return None, 'Error: Unexpected item format in API response.'
    elif isinstance(item_list, list) and len(item_list) == 0:
        logger.warning(f'NFT not found for {contract_address}:{token_id}')
        return None, f'NFT details not found ({contract_address}:{token_id}).'
    else:
        logger.error(
            f'Unexpected result type from helper for NFT overview: {type(item_list)}'
            )
        return None, 'Error: Unexpected result from API helper.'
