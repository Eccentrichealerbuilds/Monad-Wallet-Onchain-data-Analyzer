import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from api_clients.fetch_nft_bids import fetch_token_bids
from formatters.nft_bids import fmt_nft_bid
logger = logging.getLogger(__name__)
CALLBACK_BIDS_INITIAL = 'nftbids_'
CALLBACK_BIDS_MORE = 'nftbidsmore_'
CALLBACK_INFO = 'nftinfo_'


async def bids_btn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE
    ) ->None:
    """Handles 'Offers' button clicks & 'Load More Bids' clicks."""
    query = update.callback_query
    callback_data = query.data
    user_id = query.from_user.id
    logger.info(f'Processing bids callback for user {user_id}: {callback_data}'
        )
    page_offset = 0
    current_ct = None
    if callback_data.startswith(CALLBACK_BIDS_INITIAL):
        await query.answer('Fetching bids...')
        nft_id = callback_data[len(CALLBACK_BIDS_INITIAL):]
        context.user_data.pop(f'bids_cont_{user_id}_{nft_id}', None)
        context.user_data.pop(f'bids_offset_{user_id}_{nft_id}', None)
    elif callback_data.startswith(CALLBACK_BIDS_MORE):
        await query.answer('Fetching more bids...')
        nft_id = callback_data[len(CALLBACK_BIDS_MORE):]
        current_ct = context.user_data.get(f'bids_cont_{user_id}_{nft_id}')
        page_offset = context.user_data.get(f'bids_offset_{user_id}_{nft_id}',
            0)
        if not current_ct:
            logger.warning(
                f'Continuation token not found for bids_{nft_id}, user {user_id}'
                )
            await query.answer(
                'Error: Could not find next page data. Try again.',
                show_alert=True)
            return
    else:
        logger.warning(
            f'Unknown bids action prefix in callback: {callback_data}')
        await query.answer('Unknown action.', show_alert=True)
        return
    try:
        contract, tokenid = nft_id.split(':', 1)
    except ValueError:
        logger.error(f'Invalid nft_id format in bids callback: {nft_id}')
        await query.edit_message_text('Error: Invalid NFT identifier.')
        return
    items_per_page = 5
    bids_list, next_ct = await fetch_token_bids(contract, tokenid,
        continuation_token=current_ct, limit=items_per_page)
    if bids_list is None:
        error_msg = f'Error fetching bids: {next_ct}'
        try:
            if query.message.photo:
                await query.edit_message_caption(caption=error_msg)
            else:
                await query.edit_message_text(text=error_msg)
        except Exception as e:
            logger.error(f'Failed to edit message with bids error: {e}')
        return
    bids_text = fmt_nft_bid(bids_list, current_offset=page_offset, limit=
        items_per_page)
    buttons_row = []
    back_cb = f'{CALLBACK_INFO}{nft_id}'
    buttons_row.append(InlineKeyboardButton('⬅️ Back', callback_data=back_cb))
    if next_ct:
        next_offset = page_offset + len(bids_list)
        user_data_key_ct = f'bids_cont_{user_id}_{nft_id}'
        user_data_key_offset = f'bids_offset_{user_id}_{nft_id}'
        context.user_data[user_data_key_ct] = next_ct
        context.user_data[user_data_key_offset] = next_offset
        logger.info(
            f'Stored bids continuation for user {user_id}, nft {nft_id}. Next offset: {next_offset}'
            )
        more_bids_cb = f'{CALLBACK_BIDS_MORE}{nft_id}'
        buttons_row.append(InlineKeyboardButton('More Bids ➡️',
            callback_data=more_bids_cb))
    else:
        context.user_data.pop(f'bids_cont_{user_id}_{nft_id}', None)
        context.user_data.pop(f'bids_offset_{user_id}_{nft_id}', None)
        logger.info(
            f'Reached end of bids for user {user_id}, nft {nft_id}. Cleared state.'
            )
    keyboard = InlineKeyboardMarkup([buttons_row])
    try:
        if query.message.photo:
            await query.edit_message_caption(caption=bids_text,
                reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text=bids_text, parse_mode=
                ParseMode.HTML, reply_markup=keyboard,
                disable_web_page_preview=True)
    except BadRequest as e:
        if 'Message is not modified' in str(e):
            logger.info('Bids message not modified.')
            await query.answer()
        else:
            logger.error(f'Error editing msg for bids: {e}')
            await query.answer('Error displaying bids.', show_alert=True)
    except Exception as e:
        logger.error(f'Error editing msg for bids: {e}')
        await query.answer('Error displaying bids.', show_alert=True)
