import logging
import asyncio
import functools
import requests
import json
import base64
import time
from typing import Optional, List, Dict, Any, Tuple, Set
from telegram import Bot
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from config import WALLET_API_KEY, WALLET_API_BASE_URL
from formatters.address import format_address
logger = logging.getLogger(__name__)
WALLET_API_CHAIN_ID = 'monad-test-v2'
PAGE_SIZE = 100
PROGRESS_UPDATE_INTERVAL_PAGES = 10
PROGRESS_UPDATE_INTERVAL_SECONDS = 30
GLOBAL_SCAN_ACTIVE_KEY = 'global_scan_active'
SCAN_ACTIVE_USER_KEY_TPL = 'scan_active_{user_id}'


async def _fetch_tx_page(url: str, api_key: str) ->Tuple[Optional[List[Dict
    [str, Any]]], Optional[str]]:
    if not api_key:
        return None, 'API Key missing'
    auth_string = f'{api_key}:'
    try:
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
    except Exception as e:
        logger.error(f'Failed to encode auth key for tx fetch: {e}')
        return None, 'Auth Encoding Error'
    headers = {'accept': 'application/json', 'X-Env': 'testnet',
        'Authorization': f'Basic {encoded_auth}'}
    try:
        loop = asyncio.get_running_loop()
        func_call = functools.partial(requests.get, url, headers=headers,
            timeout=30)
        response = await loop.run_in_executor(None, func_call)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            tx_list = data.get('data', [])
            next_url = data.get('links', {}).get('next')
            return tx_list, next_url
        else:
            logger.error(f'Tx page unexpected format (expected dict): {data}')
            return None, 'Unexpected API response format (expected dict)'
    except requests.exceptions.RequestException as e:
        logger.error(f'Tx page fetch error: {e}')
        status_code = 'N/A'
        error_detail = ''
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            logger.error(f'API Status: {status_code}')
            try:
                err_detail_json = e.response.json()
                detail_msg = '[No specific detail]'
                errors_list = err_detail_json.get('errors')
                if isinstance(errors_list, list) and errors_list:
                    detail_msg = errors_list[0].get('detail', str(
                        err_detail_json))
                else:
                    detail_msg = err_detail_json.get('message', str(
                        err_detail_json))
                error_detail = f': {detail_msg}'
                logger.error(f'API Body (JSON): {err_detail_json}')
            except json.JSONDecodeError:
                error_text = e.response.text
                error_detail = f': {error_text[:100]}...' if error_text else ''
                logger.error(f'API Body (non-JSON): {error_text}')
        return None, f'API Error ({status_code}){error_detail}'
    except Exception as e:
        logger.exception('Unexpected error fetching tx page')
        return None, 'Unexpected Error during page fetch'


async def fetch_all_transaction_targets(user_id: int, address: str, context:
    ContextTypes.DEFAULT_TYPE, chat_id: int, status_message_id: int) ->None:
    if not WALLET_API_KEY:
        logger.error('Wallet API Key missing for tx scan.')
        return
    interacted_addresses: Set[str] = set()
    total_txns_processed: int = 0
    page_num: int = 1
    last_update_time: float = time.monotonic()
    bot: Bot = context.bot
    scan_failed = False
    user_scan_key = SCAN_ACTIVE_USER_KEY_TPL.format(user_id=user_id)
    endpoint_tmpl = f'/wallets/{address}/transactions'
    params = {'filter[chain_ids]': WALLET_API_CHAIN_ID, 'page[size]': PAGE_SIZE
        }
    try:
        initial_req = requests.Request('GET', WALLET_API_BASE_URL.rstrip(
            '/') + endpoint_tmpl, params=params).prepare()
        current_url: Optional[str] = initial_req.url
    except Exception as url_err:
        logger.error(f'Failed to prepare initial URL: {url_err}')
        await bot.edit_message_text('Error preparing scan.', chat_id=
            chat_id, message_id=status_message_id)
        raise
    logger.info(
        f'Starting full transaction scan for {address} (User: {user_id})')
    try:
        while current_url:
            logger.debug(
                f'Attempting to fetch tx page {page_num} for {address}')
            tx_list_page, next_page_url = await _fetch_tx_page(current_url,
                WALLET_API_KEY)
            if tx_list_page is None:
                error_msg = next_page_url or 'Unknown API error.'
                logger.error(f'Stopping scan: {error_msg}')
                await bot.edit_message_text(f'⚠️ Scan failed: {error_msg}',
                    chat_id=chat_id, message_id=status_message_id)
                scan_failed = True
                break
            if not tx_list_page:
                logger.info(
                    f'Reached end of transaction history page {page_num}.')
                break
            page_processed_count = 0
            for tx in tx_list_page:
                if isinstance(tx, dict) and tx.get('type') == 'transactions':
                    sent_to = tx.get('attributes', {}).get('sent_to')
                    if sent_to:
                        interacted_addresses.add(sent_to.lower())
                    page_processed_count += 1
            total_txns_processed += page_processed_count
            logger.debug(
                f'Page {page_num}: Processed {page_processed_count} txns. Total unique: {len(interacted_addresses)}'
                )
            current_time = time.monotonic()
            if (page_num % PROGRESS_UPDATE_INTERVAL_PAGES == 0 or 
                current_time - last_update_time >
                PROGRESS_UPDATE_INTERVAL_SECONDS):
                progress_text = f"""🔬 Scanning... (Page: {page_num})
Txns checked: ~{total_txns_processed}
Unique found: {len(interacted_addresses)}"""
                try:
                    await bot.edit_message_text(progress_text, chat_id=
                        chat_id, message_id=status_message_id)
                    last_update_time = current_time
                    logger.debug('Progress update edit successful.')
                except BadRequest as e:
                    if 'Message is not modified' not in str(e):
                        logger.error(f'Failed progress edit (BadRequest): {e}')
                except Exception as e:
                    logger.error(f'Failed progress edit (Other Error): {e}')
            current_url = next_page_url
            page_num += 1
            if current_url:
                await asyncio.sleep(0.6)
        if not scan_failed:
            logger.info(
                f'Scan completed successfully for {address}. Total unique: {len(interacted_addresses)}'
                )
            final_text = f"""✅ Scan Complete for {format_address(address)}!

Total Transactions Processed: {total_txns_processed}
Unique Addresses Interacted With: <b>{len(interacted_addresses)}</b>"""
            await bot.edit_message_text(final_text, chat_id=chat_id,
                message_id=status_message_id, parse_mode=ParseMode.HTML)
    except Exception as loop_err:
        logger.exception(
            f'Error occurred inside transaction scan loop for {address}')
        scan_failed = True
        try:
            await bot.edit_message_text(
                f'An internal error occurred during the scan loop.',
                chat_id=chat_id, message_id=status_message_id)
        except Exception:
            pass
        raise
