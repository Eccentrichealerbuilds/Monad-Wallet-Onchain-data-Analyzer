import logging
import asyncio
import html
from typing import Optional, Tuple, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_user_nfts import fetch_user_nfts
from formatters.nft_list_item import fmt_nft_list_item
try:
    from config import COLLECTIONS_PAGE_SIZE as ITEMS_PER_PAGE
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('Page size missing')
    ITEMS_PER_PAGE = 10
logger = logging.getLogger(__name__)
CALLBACK_COLLECTION_ITEMS_INITIAL = 'nftcoll_'
CALLBACK_COLLECTION_ITEMS_MORE = 'nftcollitems_more_'
CALLBACK_INFO = 'nftinfo_'
CALLBACK_COLLECTION_LIST_BACK = 'back_to_coll_list_'


async def collection_items_btn_callback(update: Update, context:
    ContextTypes.DEFAULT_TYPE) ->None:
    """Handles click on '[View My Items]' button below a collection summary.
       Sends item list page 1 as new messages.
    """
    query = update.callback_query
    callback_data = query.data
    user_id = query.from_user.id
    logger.debug(f'User {user_id} triggered coll items cb: {callback_data}')
    logger.debug(f'User {user_id} user_data: {context.user_data}')
    current_offset = 0
    current_ct = None
    collection_id = None
    is_initial_load = False
    if callback_data.startswith(CALLBACK_COLLECTION_ITEMS_INITIAL):
        await query.answer('Fetching collection items...')
        is_initial_load = True
        try:
            collection_id = callback_data.split('_', 1)[1]
        except IndexError:
            logger.error(
                f'Could not extract collection_id from {callback_data}')
            await query.answer('Error.', show_alert=True)
            return
        context.user_data.pop(f'coll_items_cont_{user_id}_{collection_id}',
            None)
        context.user_data.pop(f'coll_items_offset_{user_id}_{collection_id}',
            None)
        context.user_data.pop(f'coll_items_msgids_{user_id}_{collection_id}',
            None)
    else:
        logger.warning(f'Unknown action prefix: {callback_data}')
        await query.answer('Unknown action.', show_alert=True)
        return
    if not collection_id:
        logger.error(f'Failed to get collection_id')
        await query.answer('Error.', show_alert=True)
        return
    addr = context.user_data.get(f'current_nfts_addr_{user_id}')
    if not addr:
        logger.error(f'Address missing for {user_id}')
        await query.answer('Session expired.', show_alert=True)
        return
    ack_text = (
        f'Fetching items for <code>{html.escape(collection_id)}</code>...')
    ack_msg = await context.bot.send_message(chat_id=query.message.chat_id,
        text=ack_text, parse_mode=ParseMode.HTML)
    nfts_page, next_continuation = await fetch_user_nfts(user_address=addr,
        collection_id_filter=collection_id, continuation_token=current_ct,
        limit=ITEMS_PER_PAGE)
    try:
        await ack_msg.delete()
    except Exception as e:
        logger.warning(f'Could not delete items ack msg: {e}')
    if nfts_page is None:
        error_msg = next_continuation or 'API error.'
        await context.bot.send_message(chat_id=query.message.chat_id, text=
            error_msg)
        return
    if not nfts_page:
        empty_text = (
            f'No owned items found in collection <code>{html.escape(collection_id)}</code>.'
            )
        kb = [[InlineKeyboardButton('⬅️ Back to Collections', callback_data
            =f'{CALLBACK_COLLECTION_LIST_BACK}{collection_id}')]]
        await context.bot.send_message(chat_id=query.message.chat_id, text=
            empty_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=
            ParseMode.HTML)
        return
    sent_item_msg_ids = []
    display_index = current_offset + 1
    logger.info(
        f'Displaying items {display_index}-{display_index + len(nfts_page) - 1} for collection {collection_id}'
        )
    for nft_item in nfts_page:
        if not isinstance(nft_item, dict):
            logger.warning(f'Skipping non-dict item: {nft_item}')
            continue
        token_data = nft_item.get('token', {})
        contract = token_data.get('contract')
        token_id = token_data.get('tokenId')
        if not contract or token_id is None:
            logger.warning(f'Skipping item missing ID: {nft_item}')
            continue
        try:
            nft_text, _ = fmt_nft_list_item(nft_item, display_index)
        except Exception as fmt_err:
            logger.error(
                f'Error fmt item {display_index} ({contract}:{token_id}): {fmt_err}'
                )
            nft_text = f'{display_index}. Error'
        info_callback_data = f'{CALLBACK_INFO}{contract}:{token_id}'
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Info',
            callback_data=info_callback_data)]])
        try:
            sent_msg = await context.bot.send_message(chat_id=query.message
                .chat_id, text=nft_text, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True)
            sent_item_msg_ids.append(sent_msg.message_id)
        except Exception as send_err:
            logger.error(
                f'Error sending item {display_index} ({contract}:{token_id}): {send_err}'
                )
        display_index += 1
        await asyncio.sleep(0.05)
    nav_buttons = [InlineKeyboardButton('⬅️ Back to Collections',
        callback_data=f'{CALLBACK_COLLECTION_LIST_BACK}{collection_id}')]
    nav_text = '[End of items for this collection]'
    if next_continuation:
        logger.info(f'More items exist for collection {collection_id}.')
        context.user_data[f'coll_items_cont_{user_id}_{collection_id}'
            ] = next_continuation
        context.user_data[f'coll_items_offset_{user_id}_{collection_id}'
            ] = display_index - 1
        nav_text = '[More items exist...]'
    else:
        context.user_data.pop(f'coll_items_cont_{user_id}_{collection_id}',
            None)
        context.user_data.pop(f'coll_items_offset_{user_id}_{collection_id}',
            None)
    nav_keyboard = InlineKeyboardMarkup([nav_buttons])
    try:
        final_nav_msg = await context.bot.send_message(chat_id=query.
            message.chat_id, text=nav_text, reply_markup=nav_keyboard)
        sent_item_msg_ids.append(final_nav_msg.message_id)
    except Exception as e:
        logger.error(f'Failed to send item nav message: {e}')
    context.user_data[f'coll_items_msgids_{user_id}_{collection_id}'
        ] = sent_item_msg_ids
    logger.debug(
        f'Stored {len(sent_item_msg_ids)} item view message IDs for user {user_id}, coll {collection_id}'
        )
