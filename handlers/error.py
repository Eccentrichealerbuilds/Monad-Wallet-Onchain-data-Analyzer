import logging
from telegram import Update
from telegram.ext import ContextTypes
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE
    ) ->None:
    logger.error('Exception while handling an update:', exc_info=context.error)
