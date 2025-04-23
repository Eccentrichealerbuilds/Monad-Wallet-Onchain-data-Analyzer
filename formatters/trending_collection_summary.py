import logging
import html
from typing import Dict, Any, Optional
logger = logging.getLogger(__name__)


def format_large_number(num: Optional[float]) ->str:
    if num is None:
        return 'N/A'
    try:
        num = float(num)
        if abs(num) < 0.01 and num != 0:
            return f'{num:.4f}'
        if abs(num) < 1000:
            return f'{num:.2f}' if num != int(num) else f'{int(num)}'
        if abs(num) < 1000000:
            return f'{num / 1000:.1f}K'
        if abs(num) < 1000000000:
            return f'{num / 1000000:.1f}M'
        return f'{num / 1000000000:.1f}B'
    except (ValueError, TypeError):
        logger.warning(f'Could not format number: {num}')
        return 'N/A'


def fmt_trending_collection_summary(collection_data: Dict[str, Any], index:
    int, period: str, sort_by: str) ->str:
    if not collection_data:
        return f'{index}. Error: Empty data.'
    name = collection_data.get('name') or '[No Name]'
    collection_id = collection_data.get('id', 'N/A')
    volume = collection_data.get('volume')
    sales_count = collection_data.get('count')
    volume_change_pct = collection_data.get('volumePercentChange')
    floor_price = collection_data.get('floorAsk', {}).get('price', {}).get(
        'amount', {}).get('native', 'N/A')
    floor_curr = collection_data.get('floorAsk', {}).get('price', {}).get(
        'currency', {}).get('symbol', '')
    top_bid_data = collection_data.get('topBid')
    top_bid_price = 'N/A'
    top_bid_curr = ''
    if top_bid_data and top_bid_data.get('price'):
        top_bid_price = top_bid_data.get('price', {}).get('amount', {}).get(
            'native', 'N/A')
        top_bid_curr = top_bid_data.get('price', {}).get('currency', {}).get(
            'symbol', '')
    owner_count = collection_data.get('ownerCount')
    vol_str = format_large_number(volume)
    sales_str = format_large_number(float(sales_count)
        ) if sales_count is not None else 'N/A'
    floor_str = format_large_number(floor_price)
    top_bid_str = format_large_number(top_bid_price)
    owners_str = format_large_number(owner_count)
    vol_change_str = f'{volume_change_pct:+.1f}%' if isinstance(
        volume_change_pct, (int, float)) else 'N/A'
    name_esc = html.escape(name)
    floor_curr_esc = html.escape(floor_curr)
    top_bid_curr_esc = html.escape(top_bid_curr)
    period_label = period
    line1 = f'{index}.   <b>🟣{name_esc}</b>'
    if sort_by == 'volume':
        line2 = (
            f'   ☄➠ Vol({period_label}): {vol_str} {floor_curr_esc} ({vol_change_str})'
            )
        line2 += f'\n  ☄➠ Sales: {sales_str}'
    elif sort_by == 'sales':
        line2 = f'   ☄➠ Sales({period_label}): {sales_str}'
        line2 += f' \n ☄➠ Vol: {vol_str} {floor_curr_esc} ({vol_change_str})'
    else:
        line2 = (
            f'   ☄➠ Vol({period_label}): {vol_str} {floor_curr_esc} ({vol_change_str})'
            )
        line2 += f' \n ☄➠ Sales: {sales_str}'
    line3 = f'   ☄➠ Floor: {floor_str} {floor_curr_esc}'
    line3 += f'\n  ☄➠ Bid: {top_bid_str} {top_bid_curr_esc}'
    line3 += f'\n  ☄➠ Owners: {owners_str}'
    return f'{line1}\n{line2}\n{line3}'
