import logging
from typing import Optional, List, Dict, Any, Tuple
from .me_helper import _fetch_page_m
from config import ME_API_KEY, NETWORK
logger = logging.getLogger(__name__)


async def fetch_user_nfts(user_address: str, continuation_token: Optional[
    str]=None, limit: int=10, collection_id_filter: Optional[str]=None
    ) ->Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Fetches a page of NFTs owned by a specific user, optionally filtered by collection.
    """
    if not ME_API_KEY:
        return None, 'Error: NFT API Key not configured.'
    if not user_address:
        return None, 'Error: User address not provided.'
    endpoint_tmpl = f'/v3/rtp/{NETWORK}/users/{user_address}/tokens/v7'
    base_params = {'sortBy': 'acquiredAt', 'sortDirection': 'desc'}
    if collection_id_filter:
        base_params['collection'] = collection_id_filter
        logger.info(
            f'Filtering user NFTs by collection: {collection_id_filter}')
    items, next_ct_or_error = await _fetch_page_m(endpoint_tmpl=
        endpoint_tmpl, params=base_params, api_key=ME_API_KEY, ct=
        continuation_token, lmt=limit)
    if isinstance(items, list):
        return items, next_ct_or_error
    elif items is None:
        return None, next_ct_or_error
    else:
        logger.error(f'fetch_user_nfts expected list, got {type(items)}')
        return None, 'Error: Unexpected data type from helper.'
