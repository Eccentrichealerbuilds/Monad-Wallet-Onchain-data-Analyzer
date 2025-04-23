import logging
import asyncio
import functools
import requests
import json
from typing import Optional, List, Dict, Any, Tuple
from config import ME_API_KEY, NETWORK, ME_BASE_URL
logger = logging.getLogger(__name__)
VALID_PERIODS = ['5m', '10m', '30m', '1h', '6h', '1d', '24h', '7d', '30d']
VALID_SORT_BY = ['volume', 'sales']


async def fetch_trending_collections(period: str='1d', limit: int=10,
    sort_by: str='volume') ->Tuple[Optional[List[Dict[str, Any]]], Optional
    [str]]:
    """Fetches trending collections based on specified period and sorting."""
    if not ME_API_KEY:
        return None, 'Error: NFT API Key not configured.'
    if not ME_BASE_URL:
        return None, 'Error: Base API URL not configured.'
    if period not in VALID_PERIODS:
        logger.warning(f'Invalid period: {period}, using 1d')
        period = '1d'
    if sort_by not in VALID_SORT_BY:
        logger.warning(f'Invalid sortBy: {sort_by}, using volume')
        sort_by = 'volume'
    api_max_limit = 50
    if not 1 <= limit <= api_max_limit:
        logger.warning(f'Limit {limit} outside 1-{api_max_limit}, clamping.')
        limit = max(1, min(limit, api_max_limit))
    endpoint_tmpl = f'/v3/rtp/{NETWORK}/collections/trending/v1'
    headers = {'accept': '*/*', 'Authorization': f'Bearer {ME_API_KEY}'}
    params = {'period': period, 'limit': limit, 'sortBy': sort_by,
        'normalizeRoyalties': True, 'useNonFlaggedFloorAsk': False}
    url = ME_BASE_URL + endpoint_tmpl
    logger.info(
        f'Requesting Trending Collections: Period={period}, Sort={sort_by}, Limit={limit}'
        )
    try:
        loop = asyncio.get_running_loop()
        func_call = functools.partial(requests.get, url, headers=headers,
            params=params, timeout=20)
        response = await loop.run_in_executor(None, func_call)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and 'collections' in data:
            collection_list = data.get('collections', [])
            logger.debug(
                f'Fetched {len(collection_list)} trending collections.')
            return collection_list, None
        elif isinstance(data, dict) and ('statusCode' in data or 'message' in
            data):
            err_msg = data.get('message', str(data.get('error',
                'Unknown API Error')))
            logger.error(f'API error response (Structure 1): {data}')
            return None, f'API Error: {err_msg}'
        else:
            logger.error(f'Unexpected API response format: {data}')
            return None, 'Error: Unexpected API response format.'
    except requests.exceptions.Timeout:
        logger.error(f'API timeout: {url}')
        return None, 'Error: API request timed out.'
    except requests.exceptions.RequestException as e:
        logger.error(f'API request error: {e}')
        error_detail = ''
        status_code = 'N/A'
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            logger.error(f'API Status: {status_code}')
            try:
                err_detail_json = e.response.json()
                logger.error(f'API Response Body (JSON): {err_detail_json}')
                detail_msg = err_detail_json.get('message') or str(
                    err_detail_json.get('error')) or json.dumps(err_detail_json
                    )
                error_detail = f': {detail_msg}'
            except json.JSONDecodeError:
                error_text = e.response.text
                logger.error(f'API Response Body (non-JSON): {error_text}')
                error_detail = f': {error_text}' if error_text else ''
        return None, f'API Error ({status_code}){error_detail}. See logs.'
    except Exception as e:
        logger.exception(f'Unexpected error in fetch_trending_collections')
        return None, f'An unexpected error occurred.'
