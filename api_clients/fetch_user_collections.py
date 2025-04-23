import logging
import asyncio
import functools
import requests
import json
from typing import Optional, List, Dict, Any, Tuple
from config import ME_API_KEY, NETWORK, ME_BASE_URL
logger = logging.getLogger(__name__)


async def fetch_user_collections(user_address: str, offset: int=0, limit: int=5
    ) ->Tuple[Optional[List[Dict[str, Any]]], Optional[Any]]:
    """
    Fetches a page of collection aggregate stats for a specific user.
    Uses offset pagination. Does NOT explicitly disable spam filtering.
    """
    if not ME_API_KEY:
        return None, 'Error: NFT API Key not configured.'
    if not user_address:
        return None, 'Error: User address not provided.'
    endpoint_tmpl = f'/v3/rtp/{NETWORK}/users/{user_address}/collections/v3'
    headers = {'accept': '*/*', 'Authorization': f'Bearer {ME_API_KEY}'}
    current_params = {'limit': limit, 'offset': offset, 'includeTopBid': 
        True, 'includeLiquidCount': True}
    url = ME_BASE_URL + endpoint_tmpl
    logger.info(f'Requesting User Collections: Offset={offset}, Limit={limit}')
    try:
        loop = asyncio.get_running_loop()
        func_call = functools.partial(requests.get, url, headers=headers,
            params=current_params, timeout=15)
        response = await loop.run_in_executor(None, func_call)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and 'collections' in data:
            collection_list = data.get('collections', [])
            has_more = len(collection_list) == limit
            logger.debug(
                f'Fetched {len(collection_list)} collections. Has More: {has_more}'
                )
            return collection_list, has_more
        else:
            logger.error(
                f'Unexpected User Collections API response format: {data}')
            return None, 'Error: Unexpected API response format.'
    except requests.exceptions.RequestException as e:
        logger.error(f'User Collections API request error: {e}')
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            logger.error(f'API Status: {status_code}')
            try:
                err_detail = e.response.json()
                detail_msg = err_detail.get('message') or str(err_detail.
                    get('error')) or str(err_detail)
                logger.error(f'API Body: {err_detail}')
                return None, f'API Error ({status_code}): {detail_msg}'
            except json.JSONDecodeError:
                logger.error(f'API Body (non-JSON): {e.response.text}')
                return None, f'API Error ({status_code}).'
        return None, f'Error communicating with API.'
    except Exception as e:
        logger.exception(f'Unexpected error in fetch_user_collections')
        return None, f'An unexpected error occurred.'
