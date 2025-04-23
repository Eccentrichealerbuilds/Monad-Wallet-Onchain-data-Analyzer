import html
import logging
from typing import List, Dict, Any
from datetime import datetime
from .address import format_address
logger = logging.getLogger(__name__)


def fmt_nft_bid(bids_list: List[Dict[str, Any]], current_offset: int=0,
    limit: int=5) ->str:
    if not bids_list:
        return ('No further active bids found.' if current_offset > 0 else
            'No active bids (offers) found.')
    start_index = current_offset + 1
    items_to_format = bids_list[:limit]
    end_index = current_offset + len(items_to_format)
    header = f'<b>Active Bids ({start_index} - {end_index}):</b>\n'
    message_parts = [header]
    current_length = len(header)
    caption_limit = 1000
    processed_count = 0
    for i, bid in enumerate(items_to_format, start=start_index):
        price_info = bid.get('price', {})
        price_amount = price_info.get('amount', {}).get('native', 'N/A')
        price_currency = price_info.get('currency', {}).get('symbol', '')
        maker = format_address(bid.get('maker'))
        quantity = bid.get('quantityRemaining', 1)
        valid_until_ts = bid.get('validUntil')
        source = bid.get('source', {}).get('name', 'N/A')
        valid_until_str = 'N/A'
        if valid_until_ts:
            try:
                valid_until_dt = datetime.fromtimestamp(valid_until_ts)
                valid_until_str = valid_until_dt.strftime('%Y-%m-%d %H:%M')
            except Exception as ts_err:
                logger.warning(
                    f'Could not parse bid expiry ts {valid_until_ts}: {ts_err}'
                    )
        lines = []
        lines.append(f'🟣 <b>{price_amount} {html.escape(price_currency)}</b>')
        if quantity > 1:
            lines.append(f'☄➠ Quantity: {quantity}')
        lines.append(f'☄➠ By: {maker}')
        lines.append(f'☄➠ Expires:⏰ {valid_until_str}')
        lines.append(f'☄➠ Source: {html.escape(source)}')
        section = '\n'.join(f'   {line}' for line in lines)
        if current_length + len(section) + 3 > caption_limit:
            logger.info(
                f'Stopping bids formatting at item {i - 1} due to length limit.'
                )
            break
        message_parts.append(section)
        message_parts.append('')
        current_length += len(section) + 3
        processed_count += 1
    if processed_count < len(items_to_format):
        message_parts.append(
            f'\n[Showing top {processed_count} bids due to length limit]')
    full_message = '\n'.join(message_parts)
    return full_message[:1020] + '...\n[Caption truncated]' if len(full_message
        ) > 1024 else full_message
