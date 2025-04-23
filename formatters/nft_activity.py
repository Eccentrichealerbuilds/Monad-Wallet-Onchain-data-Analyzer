import html
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from .address import format_address
logger = logging.getLogger(__name__)


def fmt_nft_act(activity_list: List[Dict[str, Any]], current_offset: int=0,
    limit: int=5) ->str:
    if not activity_list:
        return ('No further activity found.' if current_offset > 0 else
            'No activity found for this token.')
    start_index = current_offset + 1
    items_to_format = activity_list[:limit]
    end_index = current_offset + len(items_to_format)
    header = f'<b>Recent Activity ({start_index} - {end_index}):</b>\n'
    message_parts = [header]
    current_length = len(header)
    caption_limit = 1000
    processed_count = 0
    for i, activity in enumerate(items_to_format, start=start_index):
        activity_type_raw = activity.get('type', 'N/A')
        activity_type = activity_type_raw.replace('_', ' ').capitalize()
        timestamp_str = activity.get('createdAt', '')
        tx_hash = activity.get('txHash')
        from_addr_raw = activity.get('fromAddress')
        to_addr_raw = activity.get('toAddress')
        maker_addr_raw = activity.get('maker')
        price_info = activity.get('price', {})
        price_amount = price_info.get('amount', {}).get('native', None)
        price_currency = price_info.get('currency', {}).get('symbol', '')
        price_str = (f'{price_amount} {html.escape(price_currency)}' if 
            price_amount is not None else '')
        order_source = activity.get('order', {}).get('source', {}).get('name',
            'N/A')
        timestamp_dt = None
        if timestamp_str:
            try:
                timestamp_dt = datetime.fromisoformat(timestamp_str.replace
                    ('Z', '+00:00'))
            except ValueError:
                logger.warning(f'Could not parse timestamp: {timestamp_str}')
        time_display = timestamp_dt.strftime('%Y-%m-%d %H:%M'
            ) if timestamp_dt else timestamp_str[:16]
        lines = []
        lines.append(f'🟣 <b>{activity_type}</b> ⏰{time_display}')
        actor = format_address(from_addr_raw or maker_addr_raw)
        if activity_type_raw == 'transfer':
            lines.append(f'☄➠ From: {format_address(from_addr_raw)}')
            lines.append(f'☄➠ To: {format_address(to_addr_raw)}')
            if activity.get('isAirdrop'):
                lines[-1] += ' (Airdrop)'
        elif activity_type_raw == 'mint':
            lines.append(f'☄➠ To: {format_address(to_addr_raw)}')
        elif activity_type_raw in ['ask', 'ask_cancel', 'bid', 'bid_cancel']:
            lines.append(f'☄➠ By: {actor}')
            if price_str:
                lines.append(f'☄➠ Price: {price_str}')
        elif activity_type_raw == 'sale':
            lines.append(f'☄➠ Seller: {format_address(from_addr_raw)}')
            lines.append(f'☄➠ Buyer: {format_address(to_addr_raw)}')
            if price_str:
                lines.append(f'☄➠ Price: {price_str}')
        else:
            if actor != 'N/A':
                lines.append(f'☄➠ Actor: {actor}')
            if price_str:
                lines.append(f'☄➠ Price: {price_str}')
        if order_source != 'N/A':
            lines.append(f'☄➠ Source: {html.escape(order_source)}')
        if tx_hash:
            lines.append(f'☄➠ Tx: <code>{html.escape(tx_hash[:10])}...</code>')
        section = '\n'.join(f'   {line}' for line in lines)
        if current_length + len(section) + 3 > caption_limit:
            logger.info(
                f'Stopping activity formatting at item {i - 1} due to length limit.'
                )
            break
        message_parts.append(section)
        message_parts.append('')
        current_length += len(section) + 3
        processed_count += 1
    if processed_count < len(items_to_format):
        message_parts.append(
            f'\n[Showing first {processed_count} activities due to length limit]'
            )
    full_message = '\n'.join(message_parts)
    return full_message[:1020] + '...\n[Caption truncated]' if len(full_message
        ) > 1024 else full_message
