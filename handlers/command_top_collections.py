import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
logger = logging.getLogger(__name__)
CALLBACK_SORT_PREFIX = 'topcoll_sort_'


async def top_collections_command(update: Update, context: ContextTypes.
    DEFAULT_TYPE):
    """Handles the /topcollections command - Starts the interactive selection."""
    logger.info(
        f'Received /topcollections command from user {update.effective_user.id}'
        )
    keyboard = [[InlineKeyboardButton('Sort by Volume 📈', callback_data=
        f'{CALLBACK_SORT_PREFIX}volume'), InlineKeyboardButton(
        'Sort by Sales 📊', callback_data=f'{CALLBACK_SORT_PREFIX}sales')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '📊 Choose sorting criteria for Top Collections:', reply_markup=
        reply_markup)
