import requests
import json
import os
import logging
import asyncio
import functools
from typing import Optional, List, Dict, Any, Tuple
from config import ME_BASE_URL
logger = logging.getLogger(__name__)


async def _fetch_page_m(endpoint_tmpl: str, params: dict, api_key: str, ct:
    Optional[str]=None, lmt: int=20) ->Tuple[Optional[Any], Optional[str]]:
    if not api_key:
        return None, 'Error: API Key not configured.'
    if not ME_BASE_URL:
        return None, 'Error: Base API URL not configured.'
    headers = {'accept': '*/*', 'Authorization': f'Bearer {api_key}'}
    current_params = params.copy()
    current_params['limit'] = lmt
    if ct:
        current_params['continuation'] = ct
    url = ME_BASE_URL + endpoint_tmpl
    log_ct = f', Continuation={ct[:10]}...' if ct else ', Page 1'
    log_ep_parts = endpoint_tmpl.split('/')
    log_ep = log_ep_parts[-1] if log_ep_parts[-1] else log_ep_parts[-2]
    logger.info(f'Requesting ME API: Endpoint={log_ep}, Limit={lmt}{log_ct}')
    try:
        loop = asyncio.get_running_loop()
        func_call = functools.partial(requests.get, url, headers=headers,
            params=current_params, timeout=15)
        response = await loop.run_in_executor(None, func_call)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            data_key = next((k for k in ['tokens', 'collections',
                'activities', 'orders'] if k in data), None)
            if data_key:
                item_list = data.get(data_key, [])
                next_ct = data.get('continuation')
                logger.debug(
                    f"Received {len(item_list)} items from {log_ep}. Next continuation: {'Yes' if next_ct else 'No'}"
                    )
                return item_list, next_ct
            else:
                is_error_structure = ('statusCode' in data and 'error' in
                    data and 'message' in data)
                if is_error_structure:
                    logger.warning(
                        f"API Error Response received for {log_ep}. Status: {data.get('statusCode')}"
                        )
                    logger.warning(f'API Error Content: {data}')
                    detail_msg = data.get('message') or data.get('error'
                        ) or str(data)
                    return (None,
                        f"API Error ({data.get('statusCode', 'N/A')}): {detail_msg}"
                        )
                else:
                    logger.info(
                        f'Received single object response for {log_ep}.')
                    return data, None
        else:
            logger.error(
                f'Unexpected API response format (expected dict, got {type(data)}): {data}'
                )
            return None, 'Error: Unexpected API response format.'
    except requests.exceptions.Timeout:
        logger.error(f'API request timeout for {log_ep}: {url}')
        return None, 'Error: API request timed out.'
    except requests.exceptions.RequestException as e:
        logger.error(f'API request error for {log_ep}: {e}')
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
        logger.exception(f'Unexpected error in _fetch_page_m for {log_ep}')
        return None, f'An unexpected error occurred.'
