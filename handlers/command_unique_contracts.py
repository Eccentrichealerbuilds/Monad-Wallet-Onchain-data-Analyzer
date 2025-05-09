import logging
import asyncio
import time
import html
from collections import deque
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError, BadRequest
from api_clients.fetch_all_transactions import fetch_all_transaction_targets
from formatters.address import format_address
logger = logging.getLogger(__name__)
SCAN_TIMEOUT_SECONDS = 300
USER_SCAN_COOLDOWN_SECONDS = 600
GLOBAL_SCAN_ACTIVE_KEY = 'global_scan_active'
SCAN_QUEUE_KEY = 'scan_queue'
LAST_SCAN_TIME_KEY = 'last_scan_time_{user_id}'


async def _run_scan_and_manage_queue(user_id: int, address: str, context:
    ContextTypes.DEFAULT_TYPE, chat_id: int, status_message_id: int) ->None:
    """Wrapper: Runs scan, handles timeout/errors, manages queue."""
    is_scan_successful = False
    scan_task_name = f'ScanUniqueContracts_{user_id}'
    application = context.application
    try:
        logger.info(f"Background task '{scan_task_name}' started for {address}"
            )
        await asyncio.wait_for(fetch_all_transaction_targets(user_id,
            address, context, chat_id, status_message_id), timeout=
            SCAN_TIMEOUT_SECONDS)
        logger.info(
            f"Background task '{scan_task_name}' finished successfully for {address}"
            )
        is_scan_successful = True
    except asyncio.TimeoutError:
        logger.warning(f"Scan task '{scan_task_name}' timed out for {address}")
        try:
            await context.bot.edit_message_text(
                f'⚠️ Scan timed out (5 min) for {format_address(address)}.',
                chat_id=chat_id, message_id=status_message_id)
        except Exception as e:
            logger.error(f'Failed edit on timeout: {e}')
    except Exception as e:
        logger.exception(
            f"Unexpected error during task '{scan_task_name}' for {address}")
        try:
            await context.bot.edit_message_text(
                'An unexpected error occurred during the scan.', chat_id=
                chat_id, message_id=status_message_id)
        except Exception:
            pass
    finally:
        logger.debug(f"Entering finally block for task '{scan_task_name}'")
        context.user_data[LAST_SCAN_TIME_KEY.format(user_id=user_id)
            ] = time.time()
        logger.debug(f'Updated last scan time for user {user_id}')
        context.bot_data.setdefault(SCAN_QUEUE_KEY, deque())
        queue = context.bot_data[SCAN_QUEUE_KEY]
        next_task_started = False
        if queue:
            next_task_info = queue.popleft()
            next_user_id, next_chat_id, next_msg_id, next_addr = next_task_info
            logger.info(
                f'Popped user {next_user_id} from queue (size now {len(queue)}). Launching their scan.'
                )
            try:
                context.user_data[LAST_SCAN_TIME_KEY.format(user_id=
                    next_user_id)] = time.time()
                await context.bot.edit_message_text(
                    f'✅ Your turn! Starting scan for {format_address(next_addr)}...'
                    , chat_id=next_chat_id, message_id=next_msg_id)
                context.bot_data[GLOBAL_SCAN_ACTIVE_KEY] = True
                application.create_task(_run_scan_and_manage_queue(
                    next_user_id, next_addr, context, next_chat_id,
                    next_msg_id), name=f'ScanUniqueContracts_{next_user_id}')
                next_task_started = True
            except Exception as e:
                logger.exception(
                    f'Failed to start next scan for user {next_user_id}')
        if not next_task_started:
            context.bot_data[GLOBAL_SCAN_ACTIVE_KEY] = False
            logger.info(
                f'Scan queue empty or next start failed. Global scan lock released by user {user_id}.'
                )


async def unique_contracts_command(update: Update, context: ContextTypes.
    DEFAULT_TYPE):
    """Handles /uniquecontracts: Checks limits, queues if busy, launches scan."""
    if not update.message or not update.effective_user:
        return
    if not context.args:
        await update.message.reply_html(
            'Provide address: /uniquecontracts <code>address</code>')
        return
    addr = context.args[0]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_time = time.time()
    logger.info(
        f'Processing /uniquecontracts for user {user_id}, address: {addr}')
    last_scan_time = context.user_data.get(LAST_SCAN_TIME_KEY.format(
        user_id=user_id), 0)
    if current_time - last_scan_time < USER_SCAN_COOLDOWN_SECONDS:
        wait_hours = (USER_SCAN_COOLDOWN_SECONDS - (current_time -
            last_scan_time)) / 3600
        await update.message.reply_text(
            f'⏳ Scan limit: 1 per 10mins. Wait {wait_hours:.1f}h.')
        return
    context.bot_data.setdefault(SCAN_QUEUE_KEY, deque())
    context.bot_data.setdefault(GLOBAL_SCAN_ACTIVE_KEY, False)
    queue = context.bot_data[SCAN_QUEUE_KEY]
    if any(item[0] == user_id for item in queue):
        logger.info(f'User {user_id} already in queue.')
        pos = next((i + 1 for i, item in enumerate(queue) if item[0] ==
            user_id), '?')
        await update.message.reply_text(
            f'You are already in the queue (Position: #{pos}). Please wait.')
        return
    if context.bot_data[GLOBAL_SCAN_ACTIVE_KEY] and context.bot_data.get(
        'current_scan_user_id') == user_id:
        logger.info(
            f'User {user_id} tried to start scan while theirs is active.')
        await update.message.reply_text('Your scan is already in progress.')
        return
    status_message = await update.message.reply_text(
        f'⏱️ Queued scan request for {format_address(addr)}...')
    if context.bot_data[GLOBAL_SCAN_ACTIVE_KEY]:
        logger.info(f'Scanner busy. Adding user {user_id} for {addr} to queue.'
            )
        queue_item = user_id, chat_id, status_message.message_id, addr
        queue.append(queue_item)
        queue_pos = len(queue)
        await status_message.edit_text(
            f"""⌛ Scanner busy. Added to queue.
Your position: #{queue_pos}""")
        return
    logger.info(
        f'Scanner free. Starting scan immediately for user {user_id}, addr {addr}'
        )
    context.bot_data[GLOBAL_SCAN_ACTIVE_KEY] = True
    context.bot_data['current_scan_user_id'] = user_id
    context.user_data[LAST_SCAN_TIME_KEY.format(user_id=user_id)
        ] = current_time
    await status_message.edit_text(
        f"""🔬 Starting transaction scan for {format_address(addr)}...
This may take minutes.
Progress updates appear here."""
        )
    context.application.create_task(_run_scan_and_manage_queue(user_id=
        user_id, address=addr, context=context, chat_id=chat_id,
        status_message_id=status_message.message_id), name=
        f'ScanUniqueContracts_{user_id}')
    logger.debug(f'Command handler finished for {addr}, task launched.')
