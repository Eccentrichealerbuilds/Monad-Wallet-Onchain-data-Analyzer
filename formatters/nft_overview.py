import html
import logging
from typing import Optional, Tuple
from datetime import datetime
from .address import format_address
from config import NETWORK
logger = logging.getLogger(__name__)


def fmt_nft_ovw(token_data: dict) ->Tuple[str, Optional[str]]:
    if not token_data or 'token' not in token_data:
        logger.warning(f'fmt_nft_ovw received invalid token_data: {token_data}'
            )
        return 'Error: Could not parse token data structure.', None
    token_info = token_data.get('token', {})
    market_info = token_data.get('market', {})
    collection_info = token_info.get('collection', {})
    name = token_info.get('name') or '𒈞𒈞𒈞𒈞𒈞'
    image_url = token_info.get('image') or '[No Image]'
    contract = token_info.get('contract', 'N/A')
    token_id = token_info.get('tokenId', 'N/A')
    token_standard = token_info.get('kind', 'N/A').upper()
    owner = token_info.get('owner', 'N/A')
    supply = token_info.get('supply')
    collection_name = collection_info.get('name') or '[No Collection]'
    royalty_bps = collection_info.get('royaltiesBps', None)
    royalty_percent = royalty_bps / 100.0 if royalty_bps else 0.0
    floor_price = market_info.get('floorAsk', {}).get('price', {}).get('amount'
        , {}).get('native', 'N/A')
    floor_curr = market_info.get('floorAsk', {}).get('price', {}).get(
        'currency', {}).get('symbol', '')
    top_bid_price = market_info.get('topBid', {}).get('price', {}).get('amount'
        , {}).get('native', 'N/A')
    top_bid_curr = market_info.get('topBid', {}).get('price', {}).get(
        'currency', {}).get('symbol', '')
    last_sale = token_info.get('lastSale', {})
    last_sale_price = last_sale.get('price', {}).get('amount', {}).get('native'
        , 'N/A')
    last_sale_curr = last_sale.get('price', {}).get('currency', {}).get(
        'symbol', '')
    last_sale_ts = last_sale.get('timestamp')
    last_sale_date = 'N/A'
    if last_sale_ts:
        try:
            last_sale_date = datetime.fromtimestamp(last_sale_ts).strftime(
                '%Y-%m-%d')
        except Exception:
            pass
    name_esc = html.escape(name)
    collection_name_esc = html.escape(collection_name)
    contract_esc = html.escape(contract)
    token_id_esc = html.escape(str(token_id))
    token_standard_esc = html.escape(token_standard)
    owner_esc = html.escape(owner)
    floor_curr_esc = html.escape(floor_curr)
    top_bid_curr_esc = html.escape(top_bid_curr)
    last_sale_curr_esc = html.escape(last_sale_curr)
    lines = []
    lines.append(f'▬▬ {name_esc} ▬▬')
    lines.append(f'  ☄➠ Collection: {collection_name_esc}')
    lines.append(f'  ☄➠ Owner: {owner_esc}')
    lines.append(f'  ☄➠ Token ID: {token_id_esc}')
    lines.append(f'  ☄➠ Standard: {token_standard_esc}')
    if supply:
        lines.append(f'  ☄➠ Supply: {supply}')
    lines.append(f'  ☄➠ Royalty: {royalty_percent}%')
    lines.append('')
    lines.append('    ▬▬▬▬▬ Market ▬▬▬▬▬▬')
    lines.append(f'  ☄➠ Floor: {floor_price} {floor_curr_esc}')
    lines.append(f'  ☄➠ Top Bid: {top_bid_price} {top_bid_curr_esc}')
    lines.append(
        f'  ☄➠ Last Sale: {last_sale_price} {last_sale_curr_esc} ({last_sale_date})'
        )
    caption = '\n'.join(lines)
    if len(caption) > 1000:
        caption = caption[:1000] + '\n[Details truncated]'
    image_final_url = image_url if image_url != '[No Image]' else None
    return caption, image_final_url
