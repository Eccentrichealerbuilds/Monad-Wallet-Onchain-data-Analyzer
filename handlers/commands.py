import logging
import asyncio
import html
from typing import Optional, Tuple, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_balance import fetch_native_balance
from api_clients.fetch_user_collections import fetch_user_collections
from formatters.address import format_address
from formatters.user_collection_summary import fmt_user_collection_summary
try:
    from config import COLLECTIONS_PAGE_SIZE
except ImportError:
    logging.warning('Page size missing')
    COLLECTIONS_PAGE_SIZE = 20
logger = logging.getLogger(__name__)
CALLBACK_COLLECTION_ITEMS = 'nftcoll_'
CALLBACK_COLLECTION_MORE = 'nftcollmore'


async def _send_collection_list_page(chat_id: int, user_id: int, address:
    str, context: ContextTypes.DEFAULT_TYPE, offset: int=0) ->None:
    """Fetches, formats, sends collection page (multi-message), stores sent msg IDs."""
    limit = COLLECTIONS_PAGE_SIZE
    logger.info(
        f'Sending collection page for user {user_id}, addr {address}, offset {offset}'
        )
    collections_page, has_more = await fetch_user_collections(user_address=
        address, offset=offset, limit=limit)
    if collections_page is None:
        error_msg = has_more or 'API error.'
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        return
    if not collections_page:
        empty_msg = ('No collections found.' if offset == 0 else
            'No more collections found.')
        await context.bot.send_message(chat_id=chat_id, text=empty_msg)
        context.user_data.pop(f'coll_list_offset_{user_id}', None)
        context.user_data.pop(f'coll_list_addr_{user_id}', None)
        context.user_data.pop(f'coll_page_msgids_{user_id}', None)
        context.user_data.pop(f'coll_list_last_offset_{user_id}', None)
        return
    context.user_data[f'coll_list_last_offset_{user_id}'] = offset
    logger.debug(f'Stored last coll list offset {offset} for user {user_id}')
    current_index = offset + 1
    logger.info(f'Displaying {len(collections_page)} summaries.')
    sent_message_ids = []
    for item in collections_page:
        if not isinstance(item, dict) or 'collection' not in item:
            continue
        coll_id = item.get('collection', {}).get('id')
        final_text = f'{current_index}. Error'
        keyboard = None
        button_data_to_add = None
        if coll_id:
            try:
                formatted_summary = fmt_user_collection_summary(item)
                final_text = f'{current_index}. {formatted_summary}'
                if len(final_text) > 4050:
                    final_text = final_text[:4050] + '\n[T]'
                button_data_to_add = {'index': current_index, 'id': coll_id}
            except Exception as fmt_err:
                logger.error(
                    f'Fmt err helper {current_index} ({coll_id}): {fmt_err}')
                final_text = (
                    f'{current_index}. Error: <code>{html.escape(coll_id)}</code>'
                    )
        else:
            final_text = f'{current_index}. Error-Missing ID'
            logger.warning('Skipping item missing ID')
        if button_data_to_add:
            view_items_cb = (
                f"{CALLBACK_COLLECTION_ITEMS}{button_data_to_add['id']}")
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(
                'View Items', callback_data=view_items_cb)]])
        try:
            sent_msg = await context.bot.send_message(chat_id=chat_id, text
                =final_text, parse_mode=ParseMode.HTML, reply_markup=
                keyboard, disable_web_page_preview=True)
            sent_message_ids.append(sent_msg.message_id)
        except Exception as send_err:
            logger.error(
                f'Error sending coll summary {current_index} ({coll_id}): {send_err}'
                )
        current_index += 1
        await asyncio.sleep(0.05)
    user_data_key_msgids = f'coll_page_msgids_{user_id}'
    if has_more is True:
        next_offset = offset + len(collections_page)
        context.user_data[f'coll_list_offset_{user_id}'] = next_offset
        context.user_data[f'coll_list_addr_{user_id}'] = address
        load_more_button = InlineKeyboardButton('Load More Collections ➡️',
            callback_data=CALLBACK_COLLECTION_MORE)
        keyboard = InlineKeyboardMarkup([[load_more_button]])
        try:
            sent_button_msg = await context.bot.send_message(chat_id=
                chat_id, text='Load more collections?', reply_markup=keyboard)
            sent_message_ids.append(sent_button_msg.message_id)
        except Exception as e:
            logger.error(f'Error sending Load More button: {e}')
        context.user_data[user_data_key_msgids] = sent_message_ids
        logger.debug(
            f'Stored {len(sent_message_ids)} msg IDs page offset {offset}')
    else:
        logger.info(f'No more collections indicated.')
        context.user_data.pop(f'coll_list_offset_{user_id}', None)
        context.user_data.pop(f'coll_list_addr_{user_id}', None)
        context.user_data.pop(user_data_key_msgids, None)
        context.user_data.pop(f'coll_list_last_offset_{user_id}', None)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    lines = [
        f"🟣 HI, {user.mention_html()}!",
        "🟣 WELCOME TO THE NO.1",
        "<b>🟣 M O N A D</b> WALLET ANALYZER BOT.",
        "🟣 Use /commands to view all features."
    ]

    msg = await context.bot.send_message(chat_id=chat_id, text="Starting...", parse_mode=ParseMode.HTML)

    full_text = ""
    for line in lines:
        full_text += line + "\n"
        await asyncio.sleep(0.5)
        await msg.edit_text(full_text.strip(), parse_mode=ParseMode.HTML)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.effective_message.reply_html(
            'Usage: /balance <code>address</code>')
        return
    addr = context.args[0]
    user_id = update.effective_user.id
    logger.info(f'Processing /balance user {user_id}, addr: {addr}')
    loop = asyncio.get_running_loop()
    res_txt = 'An error occurred.'
    try:
        res_txt = await loop.run_in_executor(None, fetch_native_balance, addr)
    except Exception as e:
        logger.error(f'Error exec fetch_native_balance: {e}')
    formatted_balance = f'🟣 Balance for {format_address(addr)}\n'
    formatted_balance += f'➤➣ {res_txt}'
    await update.effective_message.reply_html(formatted_balance)


async def nfts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.message.reply_html('Usage: /nfts <code>address</code>')
        return
    addr = context.args[0]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(f'Processing /nfts request user {user_id}, addr: {addr}')
    context.user_data[f'current_nfts_addr_{user_id}'] = addr
    ack_msg = await update.effective_message.reply_html(
        f'Fetching collections for {format_address(addr)}...')
    await _send_collection_list_page(chat_id, user_id, addr, context, offset=0)
    try:
        await ack_msg.delete()
    except Exception as del_err:
        logger.warning(f'Could not delete nfts ack msg: {del_err}')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Exception handling update:', exc_info=context.error)
