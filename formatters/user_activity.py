import html
import logging
from typing import Dict, Any
from datetime import datetime
from .address import format_address
logger = logging.getLogger(__name__)


def fmt_user_activity_item(activity: Dict[str, Any], index: int) ->str:
    if not activity:
        return f'{index}. Error: Empty activity data.'
    activity_type_raw = activity.get('type', 'N/A')
    activity_type_map = {'ask': 'List', 'ask_cancel': 'List Cancel', 'bid':
        'Bid', 'bid_cancel': 'Bid Cancel', 'sale': 'Sale', 'transfer':
        'Transfer', 'mint': 'Mint'}
    activity_type = activity_type_map.get(activity_type_raw,
        activity_type_raw.replace('_', ' ').capitalize())
    timestamp_str = activity.get('createdAt', '')
    tx_hash = activity.get('txHash')
    from_addr = activity.get('fromAddress')
    to_addr = activity.get('toAddress')
    maker_addr = activity.get('maker')
    price_info = activity.get('price', {})
    price_amount_native = price_info.get('amount', {}).get('native', None)
    price_amount_decimal = price_info.get('amount', {}).get('decimal', None)
    price_currency_symbol = price_info.get('currency', {}).get('symbol', '')
    price_str = ''
    if price_amount_native is not None:
        price_str = (
            f'{price_amount_decimal} {html.escape(price_currency_symbol)}')
    elif price_amount_decimal is not None:
        price_str = (
            f'{price_amount_decimal} {html.escape(price_currency_symbol)}')
    token_info = activity.get('token', {})
    collection_info = activity.get('collection', {})
    contract = activity.get('contract') or collection_info.get('collectionId',
        'N/A')
    token_id = token_info.get('tokenId', '?')
    token_name = token_info.get('tokenName') or '[No Name]'
    token_image = token_info.get('tokenImage') or '[No Image]'
    collection_name = collection_info.get('collectionName'
        ) or '[No Collection]'
    order_info = activity.get('order', {})
    order_id = order_info.get('id')
    order_source = order_info.get('source', {}).get('name', 'N/A')
    amount_raw = activity.get('amount', 1)
    is_airdrop = activity.get('isAirdrop', False)
    timestamp_dt = None
    if timestamp_str:
        try:
            timestamp_dt = datetime.fromisoformat(timestamp_str.replace('Z',
                '+00:00'))
        except ValueError:
            logger.warning(f'Could not parse timestamp: {timestamp_str}')
    time_display = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S %Z'
        ) if timestamp_dt else timestamp_str
    parts = []
    parts.append(f'{index}. 🔥 <b>{activity_type}</b>')
    parts.append(f'   🗓️ Time: {time_display}')
    parts.append(f'   🖼️ NFT: <i>{html.escape(token_name)}</i>')
    parts.append(f'   Coll: <i>{html.escape(collection_name)}</i>')
    parts.append(
        f"   ID: <code>{html.escape(contract or 'N/A')}:{html.escape(str(token_id))}</code>"
        )
    if token_image != '[No Image]':
        parts.append(f"   Image: <a href='{html.escape(token_image)}'>Link</a>"
            )
    if from_addr:
        parts.append(f'   🟣 From: <code>{html.escape(from_addr)}</code>')
    if to_addr:
        parts.append(f'   🟣 To: <code>{html.escape(to_addr)}</code>')
    if maker_addr and maker_addr != from_addr and maker_addr != to_addr:
        parts.append(f'   🟣 Maker: <code>{html.escape(maker_addr)}</code>')
    if price_str:
        parts.append(f'   💰 Price: {price_str}')
    if activity_type_raw in ['transfer', 'mint']:
        parts.append(f'   Amount/Qty: {amount_raw}')
    elif amount_raw != 1:
        parts.append(f'   Qty: {amount_raw}')
    if order_source != 'N/A':
        parts.append(f'   ☄➠ Source: {html.escape(order_source)}')
    if order_id:
        parts.append(f'   🟣 Order ID: <code>{html.escape(order_id)}</code>')
    if tx_hash:
        parts.append(f'   🟣 Tx Hash: <code>{html.escape(tx_hash)}</code>')
    if is_airdrop:
        parts.append(f'   Note: Airdrop 🎁')
    summary = '\n'.join(parts)
    return summary[:4050] + '...\n[Message truncated]' if len(summary
        ) > 4050 else summary
