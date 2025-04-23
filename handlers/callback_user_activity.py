import logging
import asyncio
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_user_activity import fetch_user_activity
from formatters.user_activity import fmt_user_activity_item
try:
    from config import USER_ACTIVITY_PAGE_SIZE
except ImportError:
    USER_ACTIVITY_PAGE_SIZE = 15
logger = logging.getLogger(__name__)
CALLBACK_USER_ACTIVITY_MORE = 'useractmore_'


async def user_activity_more_callback(update: Update, context: ContextTypes
    .DEFAULT_TYPE) ->None:
    """Handles the 'Load More Activity' button click."""
    query = update.callback_query
    callback_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    await query.answer('Loading more activity...')
    try:
        addr = callback_data[len(CALLBACK_USER_ACTIVITY_MORE):]
        if not addr:
            raise ValueError('Address missing in callback data')
    except (ValueError, IndexError):
        logger.error(
            f'Could not parse address from user activity callback: {callback_data}'
            )
        await query.answer('Error processing request.', show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    logger.info(
        f'Processing Load More Activity for user {user_id}, address {addr}')
    cont_key = f'user_act_cont_{user_id}_{addr}'
    offset_key = f'user_act_offset_{user_id}_{addr}'
    current_ct = context.user_data.get(cont_key)
    current_offset = context.user_data.get(offset_key, 0)
    if not current_ct:
        logger.warning(
            f'Continuation token not found for user_act_{user_id}_{addr}')
        await query.answer(
            'Error: Could not find the next page data. Maybe expired?',
            show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    try:
        await query.message.delete()
        logger.info(f"Deleted previous 'Load More Activity' button message.")
    except Exception as e:
        logger.warning(f"Could not delete 'Load More Activity' message: {e}")
    limit = USER_ACTIVITY_PAGE_SIZE
    activity_page, next_continuation = await fetch_user_activity(user_address
        =addr, continuation_token=current_ct, limit=limit)
    if activity_page is None:
        error_msg = next_continuation or 'API error fetching more activity.'
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        return
    if not activity_page:
        logger.info(
            f'No further activity found for {addr} after token {current_ct}')
        await context.bot.send_message(chat_id=chat_id, text=
            '--- End of activity feed ---')
        context.user_data.pop(cont_key, None)
        context.user_data.pop(offset_key, None)
        return
    display_index = current_offset + 1
    logger.info(
        f'Sending next {len(activity_page)} activity events starting from index {display_index}'
        )
    for activity_item in activity_page:
        if not isinstance(activity_item, dict):
            continue
        try:
            activity_text = fmt_user_activity_item(activity_item, display_index
                )
            if len(activity_text) > 4050:
                activity_text = activity_text[:4050] + '\n[Truncated]'
        except Exception as fmt_err:
            logger.error(
                f'Error formatting user activity item {display_index}: {fmt_err}'
                )
            activity_text = f'{display_index}. Error formatting.'
        try:
            await context.bot.send_message(chat_id=chat_id, text=
                activity_text, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
        except Exception as send_err:
            logger.error(
                f'Error sending activity item {display_index}: {send_err}')
        display_index += 1
        await asyncio.sleep(0.05)
    if next_continuation:
        logger.info(f'More activity exists for {addr}. Storing state.')
        context.user_data[cont_key] = next_continuation
        context.user_data[offset_key] = display_index - 1
        load_more_cb_data = f'{CALLBACK_USER_ACTIVITY_MORE}{addr}'
        load_more_button = InlineKeyboardButton('Load More Activity ➡️',
            callback_data=load_more_cb_data)
        keyboard = InlineKeyboardMarkup([[load_more_button]])
        try:
            await context.bot.send_message(chat_id=chat_id, text=
                'Load more activity?', reply_markup=keyboard)
        except Exception as e:
            logger.error(f'Error sending Load More Activity button: {e}')
    else:
        logger.info(f'No more activity indicated for {addr}.')
        await context.bot.send_message(chat_id=chat_id, text=
            '--- End of activity feed ---')
        context.user_data.pop(cont_key, None)
        context.user_data.pop(offset_key, None)
