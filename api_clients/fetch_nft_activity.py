import logging
import urllib.parse
from typing import Optional, List, Dict, Any, Tuple
from .me_helper import _fetch_page_m
from config import ME_API_KEY, NETWORK
logger = logging.getLogger(__name__)


async def fetch_token_activity(contract_address: str, token_id: str,
    continuation_token: Optional[str]=None, limit: int=20) ->Tuple[Optional
    [List[Dict[str, Any]]], Optional[str]]:
    if not ME_API_KEY:
        return None, 'Error: NFT API Key not configured.'
    if not contract_address or token_id is None:
        return None, 'Error: Contract address and Token ID required.'
    nft_id_raw = f'{contract_address}:{token_id}'
    try:
        nft_id_encoded = urllib.parse.quote(nft_id_raw)
    except Exception as e:
        logger.error(f'Failed to encode NFT identifier {nft_id_raw}: {e}')
        return None, 'Error: Could not encode NFT identifier.'
    endpoint_tmpl = f'/v3/rtp/{NETWORK}/tokens/{nft_id_encoded}/activity/v5'
    base_params = {'sortBy': 'eventTimestamp', 'includeMetadata': True}
    items, next_ct_or_error = await _fetch_page_m(endpoint_tmpl=
        endpoint_tmpl, params=base_params, api_key=ME_API_KEY, ct=
        continuation_token, lmt=limit)
    if isinstance(items, list):
        return items, next_ct_or_error
    elif items is None:
        return None, next_ct_or_error
    else:
        logger.error(
            f'fetch_token_activity expected a list, but got {type(items)}')
        return None, 'Error: Unexpected data type received from API helper.'
