import logging
import time
from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop
logger = logging.getLogger(__name__)
RATE_LIMIT_SECONDS = 10


async def check_rate_limit(update: Update, context: ContextTypes.DEFAULT_TYPE
    ) ->None:
    """
    Checks if the user has sent a command too recently.
    If rate limited, replies and stops further handlers.
    Otherwise, updates the timestamp.
    """
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    current_time = time.monotonic()
    last_cmd_time_key = f'last_cmd_time_{user_id}'
    last_command_time = context.user_data.get(last_cmd_time_key, 0)
    elapsed = current_time - last_command_time
    if elapsed < RATE_LIMIT_SECONDS:
        wait_time = RATE_LIMIT_SECONDS - elapsed
        logger.info(f'User {user_id} rate limited. Wait {wait_time:.1f}s.')
        try:
            await update.message.reply_text(
                f'⏳ Please wait {wait_time:.1f} more seconds before sending another command.'
                )
        except Exception as e:
            logger.error(f'Failed to send rate limit message: {e}')
        raise ApplicationHandlerStop
    else:
        logger.debug(
            f'User {user_id} passed rate limit check. Updating timestamp.')
        context.user_data[last_cmd_time_key] = current_time
        return
