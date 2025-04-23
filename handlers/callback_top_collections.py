import logging
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_trending_collections import fetch_trending_collections, VALID_PERIODS, VALID_SORT_BY
from formatters.trending_collection_summary import fmt_trending_collection_summary
logger = logging.getLogger(__name__)
CALLBACK_SORT_PREFIX = 'topcoll_sort_'
CALLBACK_PERIOD_PREFIX = 'topcoll_period_'
CALLBACK_LIMIT_PREFIX = 'topcoll_limit_'
PERIOD_OPTIONS = ['1h', '6h', '1d', '7d', '30d']
LIMIT_OPTIONS = [10, 20, 30]
BUTTONS_PER_ROW = 4


async def top_collections_callback(update: Update, context: ContextTypes.
    DEFAULT_TYPE) ->None:
    """Handles Sort, Period, and Limit selections, then fetches and displays."""
    query = update.callback_query
    if not query or not query.message:
        logger.error('Callback missing query/message.')
        return
    await query.answer()
    callback_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    msg_id = query.message.message_id
    logger.info(
        f'Processing topcoll callback for user {user_id}: {callback_data}')
    state_key_sort = f'topcoll_sort_{user_id}'
    state_key_period = f'topcoll_period_{user_id}'
    try:
        if callback_data.startswith(CALLBACK_SORT_PREFIX):
            selected_sort = callback_data[len(CALLBACK_SORT_PREFIX):]
            assert selected_sort in VALID_SORT_BY
            context.user_data[state_key_sort] = selected_sort
            context.user_data.pop(state_key_period, None)
            logger.debug(f'User {user_id} selected sort: {selected_sort}')
            kb_rows = []
            btn_row = []
            for period in PERIOD_OPTIONS:
                if period in VALID_PERIODS:
                    btn_row.append(InlineKeyboardButton(period.upper(),
                        callback_data=f'{CALLBACK_PERIOD_PREFIX}{period}'))
                if len(btn_row) >= BUTTONS_PER_ROW:
                    kb_rows.append(btn_row)
                    btn_row = []
            if btn_row:
                kb_rows.append(btn_row)
                markup = InlineKeyboardMarkup(kb_rows)
            await query.edit_message_text(
                f'🕒 Sort: {selected_sort.capitalize()}. Select period:',
                reply_markup=markup)
        elif callback_data.startswith(CALLBACK_PERIOD_PREFIX):
            current_sort = context.user_data.get(state_key_sort)
            if not current_sort:
                raise ValueError('Sort missing')
            selected_period = callback_data[len(CALLBACK_PERIOD_PREFIX):]
            assert selected_period in VALID_PERIODS
            context.user_data[state_key_period] = selected_period
            logger.debug(f'User {user_id} selected period: {selected_period}')
            kb_rows = []
            btn_row = []
            for limit_val in LIMIT_OPTIONS:
                btn_row.append(InlineKeyboardButton(str(limit_val),
                    callback_data=f'{CALLBACK_LIMIT_PREFIX}{limit_val}'))
            if len(btn_row) > 0:
                kb_rows.append(btn_row)
            markup = InlineKeyboardMarkup(kb_rows)
            await query.edit_message_text(
                f'🔢 Sort: {current_sort.capitalize()}, Period: {selected_period.upper()}. Select limit:'
                , reply_markup=markup)
        elif callback_data.startswith(CALLBACK_LIMIT_PREFIX):
            current_sort = context.user_data.get(state_key_sort)
            current_period = context.user_data.get(state_key_period)
            if not current_sort or not current_period:
                raise ValueError('Sort/Period missing')
            try:
                selected_limit = int(callback_data[len(CALLBACK_LIMIT_PREFIX):]
                    )
                assert selected_limit in LIMIT_OPTIONS
            except (ValueError, AssertionError):
                raise ValueError('Invalid limit')
            logger.debug(
                f'User {user_id} selected limit: {selected_limit}. Fetching...'
                )
            await query.edit_message_text(
                f'⏳ Fetching Top {selected_limit} ({current_period}/{current_sort.capitalize()})...'
                , reply_markup=None)
            collections_list, error_msg = await fetch_trending_collections(
                period=current_period, limit=selected_limit, sort_by=
                current_sort)
            context.user_data.pop(state_key_sort, None)
            context.user_data.pop(state_key_period, None)
            if collections_list is None:
                await query.edit_message_text(error_msg or 'Failed fetch.')
                return
            if not collections_list:
                await query.edit_message_text('No results found.')
                return
            header = (
                f'🔥 <b>Top {len(collections_list)} ({current_period} / by {current_sort.capitalize()})</b> 🔥'
                )
            message_parts = [header]
            for i, coll_data in enumerate(collections_list, start=1):
                try:
                    line = fmt_trending_collection_summary(coll_data, i,
                        current_period, current_sort)
                except Exception as e:
                    logger.error(f'Error fmt trend item {i}: {e}')
                    line = f'{i}. Error.'
                message_parts.append(f'\n{line}')
            final_message_text = '\n'.join(message_parts)
            if len(final_message_text) > 4050:
                final_message_text = final_message_text[:4050
                    ] + '\n[Message truncated]'
            await query.edit_message_text(text=final_message_text,
                parse_mode=ParseMode.HTML, disable_web_page_preview=True,
                reply_markup=None)
        else:
            logger.warning(f'Unhandled callback: {callback_data}')
            await query.answer('Cannot process.', show_alert=True)
    except (AssertionError, ValueError) as e:
        logger.warning(f'Invalid state/selection: {e}')
        await query.answer(f'Error: {e}. Start again.', show_alert=True)
    except BadRequest as e:
        if 'Message is not modified' in str(e):
            logger.info('Topcoll msg not modified.')
            await query.answer()
        else:
            logger.error(f'Error editing topcoll msg: {e}')
            await query.answer('Error.', show_alert=True)
    except Exception as e:
        logger.exception(f'Error in top_collections_callback')
        await query.answer('Error.', show_alert=True)
        context.user_data.pop(state_key_sort, None)
        context.user_data.pop(state_key_period, None)
