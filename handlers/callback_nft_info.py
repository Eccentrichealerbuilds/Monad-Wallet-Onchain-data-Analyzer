import logging
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_nft_overview import fetch_nft_overview
from formatters.nft_overview import fmt_nft_ovw
logger = logging.getLogger(__name__)
CALLBACK_INFO = 'nftinfo_'
CALLBACK_BIDS_INITIAL = 'nftbids_'
CALLBACK_ACTIVITY_INITIAL = 'nftact_'


async def info_btn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE
    ) ->None:
    """Handles 'Info' button clicks & 'Back' clicks TO Overview (from Bids/Activity)."""
    query = update.callback_query
    await query.answer('Fetching details...')
    callback_data = query.data
    logger.info(f'Processing info callback: {callback_data}')
    try:
        prefix, nft_id = callback_data.split('_', 1)
        contract, tokenid = nft_id.split(':', 1)
    except (ValueError, IndexError):
        logger.error(f'Invalid format: {callback_data}')
        await query.edit_message_text('Error: Invalid ID.')
        return
    token_data, error = await fetch_nft_overview(contract, tokenid)
    if token_data is None:
        await query.edit_message_text(f'Error fetching details: {error}')
        return
    caption, image_url = fmt_nft_ovw(token_data)
    offers_cb = f'{CALLBACK_BIDS_INITIAL}{nft_id}'
    activity_cb = f'{CALLBACK_ACTIVITY_INITIAL}{nft_id}'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Offers',
        callback_data=offers_cb), InlineKeyboardButton('Activity',
        callback_data=activity_cb)]])
    try:
        if image_url:
            media = InputMediaPhoto(media=image_url, caption=caption,
                parse_mode=ParseMode.HTML)
            await query.edit_message_media(media=media, reply_markup=keyboard)
        else:
            await query.edit_message_text(text=caption, parse_mode=
                ParseMode.HTML, reply_markup=keyboard,
                disable_web_page_preview=True)
    except BadRequest as e:
        if 'Message is not modified' in str(e):
            logger.info('Overview msg not modified.')
            await query.answer()
        elif 'Wrong type' in str(e):
            logger.warning(
                f'Wrong type error for image: {image_url}. Falling back.')
            await query.edit_message_text(text=caption, parse_mode=
                ParseMode.HTML, reply_markup=keyboard,
                disable_web_page_preview=True)
        else:
            logger.error(f'Error editing overview: {e}')
            await query.answer('Error.', show_alert=True)
    except Exception as e:
        logger.error(f'Unexpected error editing overview: {e}')
        await query.answer('Error.', show_alert=True)
