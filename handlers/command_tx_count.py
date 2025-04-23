import logging
import asyncio
import html
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from api_clients.fetch_nonce import fetch_address_nonce
from formatters.address import format_address
logger = logging.getLogger(__name__)


async def transaction_count_command(update: Update, context: ContextTypes.
    DEFAULT_TYPE):
    """Handles the /transactioncount command (shows Nonce), requires address arg."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_html(
            'Usage: /transactioncount <code>address</code>')
        return
    addr = context.args[0]
    user_id = update.effective_user.id
    logger.info(
        f'Processing /transactioncount request for user {user_id}, address: {addr}'
        )
    loop = asyncio.get_running_loop()
    reply_text = 'An error occurred.'
    try:
        nonce_count, error_msg = await loop.run_in_executor(None,
            fetch_address_nonce, addr)
        if error_msg:
            reply_text = error_msg
        elif nonce_count is not None:
            reply_text = (
                f'Nonce / Outgoing Tx Count for {format_address(addr)}: <b>{nonce_count}</b>'
                )
        else:
            logger.error(f'fetch_address_nonce returned None, None')
            reply_text = 'Failed to retrieve nonce.'
    except Exception as e:
        logger.error(f'Error exec fetch_address_nonce: {e}')
        reply_text = 'An error occurred.'
    await update.effective_message.reply_html(reply_text)
