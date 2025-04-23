import logging
import html
from typing import Dict, Any
logger = logging.getLogger(__name__)


def fmt_token_balance_item(item_data: Dict[str, Any], index: int) ->str:
    if not item_data:
        return f'{index}. Error: Empty token data.'
    attrs = item_data.get('attributes', {})
    finfo = attrs.get('fungible_info', {})
    impl = finfo.get('implementations', [{}])[0]
    name = finfo.get('name') or '[No Name]'
    symbol = finfo.get('symbol') or '???'
    qty_raw = attrs.get('quantity', {}).get('int')
    decimals = impl.get('decimals')
    balance_str = 'N/A'
    if qty_raw is not None and decimals is not None:
        try:
            decimals_int = int(decimals)
            balance_float = int(qty_raw) / 10 ** decimals_int
            if balance_float == 0:
                balance_str = '0'
            elif abs(balance_float) < 1e-06:
                balance_str = f'{balance_float:.8f}'.rstrip('0').rstrip('.')
            else:
                balance_str = f'{balance_float:.6f}'.rstrip('0').rstrip('.')
        except Exception as e:
            logger.warning(
                f'Could not calculate balance for {symbol} (Qty: {qty_raw}, Dec: {decimals}): {e}'
                )
            balance_str = '[Calc Error]'
    elif qty_raw is not None:
        balance_str = qty_raw
    name_esc = html.escape(name)
    symbol_esc = html.escape(symbol)
    text = f"""<pre>
╔════════════════════════════╗
║ 💜  {index}. <b>{symbol_esc}</b> ({name_esc})           
║ 💜  Balance: {balance_str}                    
╚════════════════════════════╝
</pre>"""
    return text
