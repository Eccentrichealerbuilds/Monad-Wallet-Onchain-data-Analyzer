from typing import Optional


def format_address(address: Optional[str]) ->str:
    if not address:
        return 'N/A'
    if len(address) > 15:
        return f'{address}'
    else:
        return address
