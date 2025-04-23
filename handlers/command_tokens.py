import logging
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.wallet_api import fetch_wallet_token_balances
from formatters.address import format_address
from formatters.token_balance import fmt_token_balance_item
try:
    from config import TOKENS_PAGE_SIZE
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('Page size missing')
    TOKENS_PAGE_SIZE = 20
logger = logging.getLogger(__name__)
CALLBACK_TOKEN_BALANCE_MORE = 'tokbalmore_'


async def tokens_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /tokens, requires address arg. Uses fetch-all/paginate display."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_html('Usage: /tokens <code>address</code>')
        return
    addr = context.args[0]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(
        f'Processing /tokens request for user {user_id}, address: {addr}')
    sent_message = await update.effective_message.reply_text(
        f'Fetching token balances for {format_address(addr)}...',
        disable_notification=True)
    msg_id = sent_message.message_id
    context.user_data[f'tokens_addr_{user_id}'] = addr
    context.user_data[f'tokens_msgid_{user_id}_{addr}'] = msg_id
    full_token_list, error_msg = await fetch_wallet_token_balances(address=addr
        )
    if full_token_list is None:
        final_text = error_msg or 'API error.'
        await sent_message.edit_text(final_text)
        return
    if not full_token_list:
        final_text = f'No fungible tokens found for {format_address(addr)}.'
        await sent_message.edit_text(final_text)
        return
    logger.debug(f'Total tokens fetched for {addr}: {len(full_token_list)}')
    list_key = f'tokens_list_{user_id}_{addr}'
    offset_key = f'tokens_offset_{user_id}_{addr}'
    context.user_data[list_key] = full_token_list
    context.user_data[offset_key] = 0
    logger.debug(
        f'Stored full token list ({len(full_token_list)} items) and state for {user_id}_{addr}'
        )
    limit = TOKENS_PAGE_SIZE
    page_items = full_token_list[0:limit]
    current_offset = 0
    header = (
        f'💰 Token Balances ({current_offset + 1}-{current_offset + len(page_items)} of {len(full_token_list)}):'
        )
    message_parts = [header]
    for i, token_item in enumerate(page_items, start=1):
        try:
            line = fmt_token_balance_item(token_item, i)
            message_parts.append(f'\n{line}')
        except Exception as e:
            logger.error(f'Error fmt token item {i}: {e}')
            symbol = '[unknown]'
            try:
                symbol = token_item.get('attributes', {}).get('fungible_info',
                    {}).get('symbol', '[unknown]')
            except Exception:
                pass
            message_parts.append(
                f'\n{i}. Error formatting {html.escape(symbol)}')
    final_message_text = '\n'.join(message_parts)
    if len(full_token_list) > len(page_items):
        final_message_text += f"""

[Showing first {len(page_items)} of {len(full_token_list)} tokens found]"""
    if len(final_message_text) > 4050:
        final_message_text = final_message_text[:4050] + '\n[Msg truncated]'
    keyboard_buttons = []
    load_more_needed = len(full_token_list) > limit
    logger.debug(f'Load more condition: {load_more_needed}')
    if load_more_needed:
        context.user_data[offset_key] = limit
        load_more_cb = f'{CALLBACK_TOKEN_BALANCE_MORE}{addr}'
        load_more_button = InlineKeyboardButton('Load More Tokens ➡️',
            callback_data=load_more_cb)
        keyboard_buttons = [[load_more_button]]
    else:
        logger.info(f'All tokens shown for {addr} on first page.')
        context.user_data.pop(offset_key, None)
        context.user_data.pop(list_key, None)
        context.user_data.pop(msgid_key, None)
    reply_markup = InlineKeyboardMarkup(keyboard_buttons
        ) if keyboard_buttons else None
    logger.debug(
        f"Final keyboard: {reply_markup.to_json() if reply_markup else 'None'}"
        )
    try:
        await sent_message.edit_text(text=final_message_text, parse_mode=
            ParseMode.HTML, reply_markup=reply_markup,
            disable_web_page_preview=True)
    except BadRequest as e:
        if 'Message is not modified' in str(e):
            logger.info('Token balance page 1 not modified.')
        else:
            logger.error(f'Error editing token balances msg: {e}')
    except Exception as e:
        logger.error(f'Error editing token balances msg: {e}')
        await update.effective_message.reply_html(final_message_text,
            reply_markup=reply_markup)
