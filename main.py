import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, PicklePersistence, MessageHandler, filters
from telegram.constants import ChatType
import config

# Commands
from handlers.commands import start_command, balance_command, nfts_command
from handlers.command_top_collections import top_collections_command
from handlers.command_user_activity import user_activity_command
from handlers.command_tokens import tokens_command
from handlers.command_tx_count import transaction_count_command
from handlers.command_unique_contracts import unique_contracts_command
from handlers.command_help import list_commands_handler # For /commands
# Callbacks
from handlers.callback_nft_info import info_btn_callback
from handlers.callback_nft_bids import bids_btn_callback
from handlers.callback_nft_activity import activity_btn_callback
from handlers.callback_collection_list import collections_list_more_callback, back_to_coll_list_callback
from handlers.callback_collection_items import collection_items_btn_callback
from handlers.callback_top_collections import top_collections_callback
from handlers.callback_user_activity import user_activity_more_callback
from handlers.callback_tokens import token_balance_more_callback
# Rate Limiter
from handlers.rate_limiter import check_rate_limit
# Error Handler
from handlers.error import error_handler

# --- Logging Setup ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING); logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
# --- End Logging Setup ---

# --- Validation & Persistence ---
if not config.BOT_TOKEN: logger.critical("CRITICAL: Bot token missing."); sys.exit(1)
if not config.ME_API_KEY: logger.warning("Warning: ME API Key missing.")
if not config.WALLET_API_KEY: logger.warning("Warning: Wallet API Key (WK) missing.")
persistence_file = Path(__file__).parent / "bot_persistence.pkl"; persistence = PicklePersistence(filepath=persistence_file)
logger.info(f"Using persistence file: {persistence_file}")
# --- End Validation & Persistence ---

def main() -> None:
    """Sets up the Application and runs the bot."""
    logger.info("Starting bot application...")
    application = ( Application.builder() .token(config.BOT_TOKEN) .persistence(persistence) .build() )

    # GROUP 0: General handlers like Rate Limiter
    application.add_handler(MessageHandler(filters.COMMAND, check_rate_limit), group=0)

    # GROUP 1: Specific Command Handlers (Run after Group 0)
    application.add_handler(CommandHandler("start", start_command), group=1)
    application.add_handler(CommandHandler("balance", balance_command), group=1)
    application.add_handler(CommandHandler("nfts", nfts_command), group=1)
    application.add_handler(CommandHandler("topcollections", top_collections_command), group=1)
    application.add_handler(CommandHandler("mynftactivity", user_activity_command), group=1)
    application.add_handler(CommandHandler("tokens", tokens_command), group=1)
    application.add_handler(CommandHandler("transactioncount", transaction_count_command), group=1)
    application.add_handler(CommandHandler("uniquecontracts", unique_contracts_command), group=1)
    application.add_handler(CommandHandler("commands", list_commands_handler), group=1) # Moved to group 1

    # GROUP 1: Callback Query Handlers
    application.add_handler(CallbackQueryHandler(info_btn_callback, pattern=r"^nftinfo_"), group=1)
    application.add_handler(CallbackQueryHandler(bids_btn_callback, pattern=r"^nftbids_"), group=1)
    application.add_handler(CallbackQueryHandler(bids_btn_callback, pattern=r"^nftbidsmore_"), group=1)
    application.add_handler(CallbackQueryHandler(activity_btn_callback, pattern=r"^nftact_"), group=1)
    application.add_handler(CallbackQueryHandler(activity_btn_callback, pattern=r"^nftactmore_"), group=1)
    application.add_handler(CallbackQueryHandler(collections_list_more_callback, pattern=r"^nftcollmore$"), group=1)
    application.add_handler(CallbackQueryHandler(collection_items_btn_callback, pattern=r"^nftcoll_"), group=1)
    application.add_handler(CallbackQueryHandler(collection_items_btn_callback, pattern=r"^nftcollitems_more_"), group=1) # Placeholder
    application.add_handler(CallbackQueryHandler(back_to_coll_list_callback, pattern=r"^back_to_coll_list_"), group=1)
    application.add_handler(CallbackQueryHandler(top_collections_callback, pattern=r"^topcoll_"), group=1)
    application.add_handler(CallbackQueryHandler(user_activity_more_callback, pattern=r"^useractmore_"), group=1)
    application.add_handler(CallbackQueryHandler(token_balance_more_callback, pattern=r"^tokbalmore_"), group=1)

    # Error Handler (Runs in its own context)
    application.add_error_handler(error_handler)
    logger.info("Bot polling started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot polling stopped.")

if __name__ == "__main__":
    main()
