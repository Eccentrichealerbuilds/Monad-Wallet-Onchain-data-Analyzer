import logging
import asyncio
import functools
import requests
import json
import base64
from typing import Optional, List, Dict, Any, Tuple
from config import WALLET_API_KEY, WALLET_API_BASE_URL
logger = logging.getLogger(__name__)
WALLET_API_CHAIN_ID = 'monad-test-v2'


async def fetch_wallet_token_balances(address: str, chain_id: str=
    WALLET_API_CHAIN_ID) ->Tuple[Optional[List[Dict[str, Any]]], Optional[str]
    ]:
    if not WALLET_API_KEY:
        return None, 'Error: Wallet API Key (WK) not configured.'
    if not WALLET_API_BASE_URL:
        return None, 'Error: Wallet API Base URL not configured.'
    if not address:
        return None, 'Error: Wallet address not provided.'
    auth_string = f'{WALLET_API_KEY}:'
    try:
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers = {'accept': 'application/json', 'X-Env': 'testnet',
            'Authorization': f'Basic {encoded_auth}'}
    except Exception as e:
        logger.error(f'Failed auth key encode: {e}')
        return None, 'Error: Failed API auth.'
    endpoint_tmpl = f'/wallets/{address}/positions/'
    params = {'filter[chain_ids]': chain_id, 'filter[trash]': 'no_filter',
        'filter[positions]': 'only_simple', 'currency': 'usd', 'sort': 'value'}
    url = WALLET_API_BASE_URL.rstrip('/') + endpoint_tmpl
    logger.info(
        f'Requesting ALL Wallet API Positions: Addr={address}, Chain={chain_id}'
        )
    try:
        loop = asyncio.get_running_loop()
        func_call = functools.partial(requests.get, url, headers=headers,
            params=params, timeout=30)
        response = await loop.run_in_executor(None, func_call)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and 'data' in data:
            position_items = data.get('data', [])
            if not isinstance(position_items, list):
                logger.error(
                    f"Wallet API positions 'data' is not list: {position_items}"
                    )
                return None, 'Error: Unexpected response structure.'
            fungible_tokens = [item for item in position_items if 
                isinstance(item, dict) and item.get('type') == 'positions' and
                item.get('attributes', {}).get('fungible_info')]
            logger.debug(
                f'Fetched {len(fungible_tokens)} total fungible tokens.')
            return fungible_tokens, None
        else:
            logger.error(
                f'Unexpected Wallet API positions response format: {data}')
            return None, 'Error: Unexpected API response format.'
    except requests.exceptions.Timeout:
        logger.error(f'Wallet API timeout: {url}')
        return None, 'Error: API request timed out.'
    except requests.exceptions.RequestException as e:
        logger.error(f'Wallet API positions request error: {e}')
        error_detail = ''
        status_code = 'N/A'
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            logger.error(f'API Status: {status_code}')
            try:
                err_detail_json = e.response.json()
                detail_msg = err_detail_json.get('errors', [{}])[0].get(
                    'detail', str(err_detail_json))
                logger.error(f'API Body: {err_detail_json}')
                error_detail = f': {detail_msg}'
            except json.JSONDecodeError:
                error_detail = ''
                logger.error(f'API Body (non-JSON): {e.response.text}')
        return (None,
            f'Error communicating with Wallet API ({status_code}){error_detail}.'
            )
    except Exception as e:
        logger.exception(f'Unexpected error in fetch_wallet_token_balances')
        return None, f'An unexpected error occurred.'
