import logging
import html
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

try:
    from config import BOT_COMMANDS
except ImportError:
    BOT_COMMANDS = {"commands": "Displays this list."}
    logging.error("Could not import BOT_COMMANDS from config.")

logger = logging.getLogger(__name__)

async def list_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a formatted list of available bot commands."""
    if not update.effective_message:
        return 

    logger.info(f"User {update.effective_user.id} requested /commands")

    message_parts = ["<b>Available Commands:</b>"]

    sorted_commands = sorted(BOT_COMMANDS.keys())

    for command_name in sorted_commands:
        description = BOT_COMMANDS.get(command_name, "No description available.")
        message_parts.append(f"\n/<code>{html.escape(command_name)}</code> - {html.escape(description)}")

    final_text = "\n".join(message_parts)

    await update.effective_message.reply_html(final_text)

