import logging
import asyncio
import html
from typing import Optional, Tuple, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_user_collections import fetch_user_collections
from formatters.user_collection_summary import fmt_user_collection_summary
from .commands import _send_collection_list_page
try:
    from config import COLLECTIONS_PAGE_SIZE
except ImportError:
    logging.warning('Page size missing')
    COLLECTIONS_PAGE_SIZE = 20
logger = logging.getLogger(__name__)
CALLBACK_COLLECTION_MORE = 'nftcollmore'
CALLBACK_COLLECTION_ITEMS = 'nftcoll_'
CALLBACK_COLLECTION_LIST_BACK = 'back_to_coll_list_'


async def collections_list_more_callback(update: Update, context:
    ContextTypes.DEFAULT_TYPE) ->None:
    """Handles 'Load More Collections' click by deleting previous batch & calling helper."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer('Loading more collections...')
    addr = context.user_data.get(f'coll_list_addr_{user_id}')
    current_offset = context.user_data.get(f'coll_list_offset_{user_id}')
    user_data_key_msgids = f'coll_page_msgids_{user_id}'
    previous_msg_ids = context.user_data.get(user_data_key_msgids, [])
    if addr is None or current_offset is None:
        logger.warning(
            f'State missing for {user_id} in more collections callback')
        await query.answer('Session expired. Use /nfts again.', show_alert=True
            )
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    logger.info(
        f'Deleting {len(previous_msg_ids)} previous collection messages for user {user_id}'
        )
    deleted_count = 0
    for msg_id in previous_msg_ids:
        try:
            await context.bot.delete_message(chat_id=query.message.chat_id,
                message_id=msg_id)
            deleted_count += 1
        except Exception as e:
            logger.warning(
                f'Could not delete previous collection message {msg_id}: {e}')
    logger.info(f'Deleted {deleted_count}/{len(previous_msg_ids)} messages.')
    context.user_data.pop(user_data_key_msgids, None)
    await _send_collection_list_page(chat_id=query.message.chat_id, user_id
        =user_id, address=addr, context=context, offset=current_offset)


async def back_to_coll_list_callback(update: Update, context: ContextTypes.
    DEFAULT_TYPE) ->None:
    """Handles 'Back to Collections' click by deleting item msgs & calling helper for page 1."""
    query = update.callback_query
    user_id = query.from_user.id
    if not query.message:
        logger.warning('BackToColl callback without message.')
        await query.answer('Error.', show_alert=True)
        return
    await query.answer('Loading collections list...')
    callback_data = query.data
    try:
        prefix_len = len(CALLBACK_COLLECTION_LIST_BACK)
        collection_id = callback_data[prefix_len:]
        if not collection_id:
            raise ValueError('Collection ID missing')
        logger.info(f'BackToColl requested for collection: {collection_id}')
    except Exception as e:
        logger.error(
            f'Could not parse collection_id from back callback {callback_data}: {e}'
            )
        await query.answer('Error processing request.', show_alert=True)
        return
    addr = context.user_data.get(f'current_nfts_addr_{user_id}')
    if not addr:
        logger.warning(f'Address not found for user {user_id}')
        await query.answer('Session expired.', show_alert=True)
        return
    item_msg_ids_key = f'coll_items_msgids_{user_id}_{collection_id}'
    item_msg_ids = context.user_data.get(item_msg_ids_key, [])
    logger.info(
        f'Deleting {len(item_msg_ids)} previous item messages for user {user_id}, coll {collection_id}'
        )
    deleted_count = 0
    for msg_id in item_msg_ids:
        try:
            await context.bot.delete_message(chat_id=query.message.chat_id,
                message_id=msg_id)
            deleted_count += 1
        except Exception as e:
            logger.warning(f'Could not delete item message {msg_id}: {e}')
    logger.info(f'Deleted {deleted_count}/{len(item_msg_ids)} messages.')
    context.user_data.pop(item_msg_ids_key, None)
    context.user_data.pop(f'coll_items_cont_{user_id}_{collection_id}', None)
    context.user_data.pop(f'coll_items_offset_{user_id}_{collection_id}', None)
    logger.info(
        f'Resending collection list page 0 for user {user_id}, address {addr}')
    await _send_collection_list_page(chat_id=query.message.chat_id, user_id
        =user_id, address=addr, context=context, offset=0)
