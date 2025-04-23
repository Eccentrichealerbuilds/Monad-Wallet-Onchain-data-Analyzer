import logging
import asyncio
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_user_activity import fetch_user_activity
from formatters.address import format_address
from formatters.user_activity import fmt_user_activity_item
try:
    from config import USER_ACTIVITY_PAGE_SIZE
except ImportError:
    USER_ACTIVITY_PAGE_SIZE = 15
logger = logging.getLogger(__name__)
CALLBACK_USER_ACTIVITY_MORE = 'useractmore_'


async def user_activity_command(update: Update, context: ContextTypes.
    DEFAULT_TYPE):
    """Handles /mynftactivity, requires address arg."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_html(
            'Usage: /mynftactivity <code>address</code>')
        return
    addr = context.args[0]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(
        f'Processing /mynftactivity for user {user_id}, address: {addr}')
    ack_msg = await update.effective_message.reply_text(
        f'Fetching activity for {format_address(addr)}...',
        disable_notification=True)
    limit = USER_ACTIVITY_PAGE_SIZE
    activity_page, next_continuation = await fetch_user_activity(user_address
        =addr, limit=limit)
    if activity_page is None:
        error_msg = next_continuation or 'API error.'
        await ack_msg.edit_text(error_msg)
        return
    if not activity_page:
        await ack_msg.edit_text(
            f'No recent activity found for {format_address(addr)}.')
        return
    try:
        await ack_msg.delete()
    except Exception as del_err:
        logger.warning(f'Could not delete activity ack msg: {del_err}')
    current_index = 1
    logger.info(
        f'Sending first {len(activity_page)} activity events for {addr}')
    for item in activity_page:
        if not isinstance(item, dict):
            continue
        try:
            activity_text = fmt_user_activity_item(item, current_index)
            if len(activity_text) > 4050:
                activity_text = activity_text[:4050] + '\n[Truncated]'
            await update.effective_message.reply_html(activity_text,
                disable_web_page_preview=True)
        except Exception as fmt_send_err:
            logger.error(
                f'Error formatting/sending user activity item {current_index}: {fmt_send_err}'
                )
        current_index += 1
        await asyncio.sleep(0.05)
    if next_continuation:
        logger.info(f'More activity exists for {addr}. Storing state.')
        context.user_data[f'user_act_cont_{user_id}_{addr}'
            ] = next_continuation
        context.user_data[f'user_act_offset_{user_id}_{addr}'
            ] = current_index - 1
        cb_data = f'{CALLBACK_USER_ACTIVITY_MORE}{addr}'
        btn = InlineKeyboardButton('Load More Activity ➡️', callback_data=
            cb_data)
        kb = InlineKeyboardMarkup([[btn]])
        try:
            await update.effective_message.reply_text('Load more activity?',
                reply_markup=kb)
        except Exception as e:
            logger.error(f'Error sending Load More Activity button: {e}')
    else:
        logger.info(f'No more activity found.')
        context.user_data.pop(f'user_act_cont_{user_id}_{addr}', None)
        context.user_data.pop(f'user_act_offset_{user_id}_{addr}', None)
