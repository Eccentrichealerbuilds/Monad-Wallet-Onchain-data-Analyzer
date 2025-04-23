import html
import logging
from typing import Optional, Tuple
from .address import format_address
logger = logging.getLogger(__name__)


def fmt_nft_list_item(nft_raw_item: dict, item_index: int) ->Tuple[str,
    Optional[str]]:
    token_data = nft_raw_item.get('token', {})
    ownership_data = nft_raw_item.get('ownership', {})
    name = token_data.get('name') or '[No Name]'
    contract = token_data.get('contract', 'N/A')
    token_id = token_data.get('tokenId', '?')
    collection_name = token_data.get('collection', {}).get('name'
        ) or '[No Collection]'
    image_url = token_data.get('imageSmall') or token_data.get('image')
    token_count_owned_str = ownership_data.get('tokenCount', '1')
    token_count_int = 1
    try:
        token_count_int = int(float(token_count_owned_str))
    except (ValueError, TypeError):
        logger.warning(
            f"Could not parse tokenCount '{token_count_owned_str}' as int. Defaulting to 1."
            )
        token_count_int = 1
    name_escaped = html.escape(name)
    collection_name_escaped = html.escape(collection_name)
    contract_escaped = html.escape(contract)
    token_id_escaped = html.escape(str(token_id))
    lines = [f'<b>{item_index}. 🟣{name_escaped}</b>',
        f'   ☄➠ Collection: <i>{collection_name_escaped}</i>',
        f'   ☄➠ ID: <code>{contract_escaped}:{token_id_escaped}</code>']
    if token_count_int > 1:
        lines.append(f'   ☄➠ Quantity: <b>{token_count_int}</b> ✨')
    text = '\n'.join(lines)
    if len(text) > 4000:
        text = text[:4000] + '...'
    return text, image_url if image_url else None
