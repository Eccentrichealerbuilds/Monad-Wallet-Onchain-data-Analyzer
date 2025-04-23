import html
import logging
from typing import Dict, Any
logger = logging.getLogger(__name__)


def fmt_user_collection_summary(collection_item: Dict[str, Any]) ->str:
    if not collection_item:
        return 'Error: Empty collection data.'
    collection_info = collection_item.get('collection', {})
    ownership_info = collection_item.get('ownership', {})
    name = collection_info.get('name') or '[No Collection Name]'
    collection_id = collection_info.get('id', 'N/A')
    floor_ask = collection_info.get('floorAskPrice', {})
    floor_price_info = floor_ask.get('amount', {})
    floor_price = floor_price_info.get('native', 'N/A')
    floor_curr = floor_ask.get('currency', {}).get('symbol', '')
    user_token_count = ownership_info.get('tokenCount', 'N/A')
    user_on_sale_count = ownership_info.get('onSaleCount', 'N/A')
    name_esc = html.escape(name)
    floor_curr_esc = html.escape(floor_curr)
    text = f'  🟣 {name_esc}\n'
    text += f'   ➤➣ Items Owned: {user_token_count}\n'
    text += f'   ➤➣ Listed: {user_on_sale_count}\n'
    text += f'   ➤➣ Floor: {floor_price} {floor_curr_esc}'
    return text
