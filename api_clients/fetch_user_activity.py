import logging
import asyncio
import functools
import requests
import json
from typing import Optional, List, Dict, Any, Tuple
from .me_helper import _fetch_page_m
from config import ME_API_KEY, NETWORK, ME_BASE_URL
logger = logging.getLogger(__name__)


async def fetch_user_activity(user_address: str, continuation_token:
    Optional[str]=None, limit: int=20) ->Tuple[Optional[List[Dict[str, Any]
    ]], Optional[str]]:
    if not ME_API_KEY:
        return None, 'Error: NFT API Key not configured.'
    if not user_address:
        return None, 'Error: User address not provided.'
    endpoint_tmpl = f'/v3/rtp/{NETWORK}/users/activity/v6'
    base_params = {'users': user_address, 'sortBy': 'eventTimestamp',
        'includeMetadata': True}
    items, next_ct_or_error = await _fetch_page_m(endpoint_tmpl=
        endpoint_tmpl, params=base_params, api_key=ME_API_KEY, ct=
        continuation_token, lmt=limit)
    if isinstance(items, list):
        return items, next_ct_or_error
    elif items is None:
        return None, next_ct_or_error
    else:
        logger.error(
            f'fetch_user_activity expected a list, but got {type(items)}')
        return None, 'Error: Unexpected data type received from API helper.'
