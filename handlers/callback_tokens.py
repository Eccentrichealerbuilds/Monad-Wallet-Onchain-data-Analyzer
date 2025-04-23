import logging
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from formatters.token_balance import fmt_token_balance_item
try:
    from config import TOKENS_PAGE_SIZE
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('Page size missing')
    TOKENS_PAGE_SIZE = 20
logger = logging.getLogger(__name__)
CALLBACK_TOKEN_BALANCE_MORE = 'tokbalmore_'


async def token_balance_more_callback(update: Update, context: ContextTypes
    .DEFAULT_TYPE) ->None:
    """Handles 'Load More Tokens' using stored list and offset."""
    query = update.callback_query
    callback_data = query.data
    user_id = query.from_user.id
    await query.answer('Loading more tokens...')
    try:
        addr = callback_data[len(CALLBACK_TOKEN_BALANCE_MORE):]
        assert addr
    except (AssertionError, ValueError, IndexError):
        logger.error(f'Invalid callback data: {callback_data}')
        return
    list_key = f'tokens_list_{user_id}_{addr}'
    offset_key = f'tokens_offset_{user_id}_{addr}'
    msgid_key = f'tokens_msgid_{user_id}_{addr}'
    full_token_list = context.user_data.get(list_key)
    current_offset = context.user_data.get(offset_key, 0)
    msg_id = context.user_data.get(msgid_key)
    if full_token_list is None or msg_id is None:
        logger.warning(
            f'State missing for user {user_id}, addr {addr} in token_balance_more_callback'
            )
        await query.edit_message_text(
            'Session expired or data lost. Please use /tokens again.',
            reply_markup=None)
        return
    limit = TOKENS_PAGE_SIZE
    next_offset = current_offset + limit
    page_items = full_token_list[current_offset:next_offset]
    if not page_items:
        logger.warning(
            f'Load more called for tokens, but no items found at offset {current_offset}'
            )
        await query.edit_message_text('No more tokens found.', reply_markup
            =None)
        context.user_data.pop(list_key, None)
        context.user_data.pop(offset_key, None)
        context.user_data.pop(msgid_key, None)
        return
    start_index = current_offset + 1
    header = (
        f'💰 Token Balances ({start_index}-{start_index + len(page_items) - 1} of {len(full_token_list)}):'
        )
    message_parts = [header]
    for i, token_item in enumerate(page_items, start=start_index):
        try:
            line = fmt_token_balance_item(token_item, i)
            message_parts.append(f'\n{line}')
        except Exception as e:
            logger.error(f'Error fmt token item {i}: {e}')
            message_parts.append(f'\n{i}. Error')
    final_message_text = '\n'.join(message_parts)
    if len(final_message_text) > 4050:
        final_message_text = final_message_text[:4050] + '\n[Truncated]'
    keyboard_buttons = []
    if next_offset < len(full_token_list):
        logger.info(
            f'More tokens exist for {addr} after offset {current_offset}.')
        context.user_data[offset_key] = next_offset
        load_more_cb = f'{CALLBACK_TOKEN_BALANCE_MORE}{addr}'
        load_more_button = InlineKeyboardButton('Load More Tokens ➡️',
            callback_data=load_more_cb)
        keyboard_buttons = [[load_more_button]]
    else:
        logger.info(f'End of token list reached for {addr}.')
        context.user_data.pop(offset_key, None)
    reply_markup = InlineKeyboardMarkup(keyboard_buttons
        ) if keyboard_buttons else None
    try:
        await context.bot.edit_message_text(text=final_message_text,
            chat_id=query.message.chat_id, message_id=msg_id, parse_mode=
            ParseMode.HTML, reply_markup=reply_markup,
            disable_web_page_preview=True)
    except BadRequest as e:
        if 'Message is not modified' in str(e):
            logger.info('Token balances page not modified.')
            await query.answer()
        else:
            logger.error(f'Error editing token balances page: {e}')
            await query.answer('Error.', show_alert=True)
    except Exception as e:
        logger.error(f'Error editing token balances page: {e}')
        await query.answer('Error.', show_alert=True)
