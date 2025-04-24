# Monad Testnet Telegram Bot

## Overview

This comprehensive Telegram bot serves as an interactive companion for users engaging with the Monad Testnet ecosystem. Developed by **Eccentric Healer**, it provides real-time insights into wallet assets, NFT portfolio details, market trends, and user activity.

The bot is built with Python using the `python-telegram-bot` library and leverages direct Monad RPC interaction (`web3.py`) along with integrations for NFT/market data (Magic Eden RTPv3 API) and detailed wallet positions (Zerion v1 API). It features a modular codebase, asynchronous operation, data persistence, and command rate limiting.
https://docs.google.com/document/d/1-G7b9TmIV3ztbxRpitjd-AsuURaYoiMV/edit?usp=drivesdk&ouid=104809867151114974374&rtpof=true&sd=true

## Features

* **Wallet Information:**
    * `/balance <address>`: Check native MON balance (via RPC).
    * `/tokens <address>`: List fungible token balances (ERC20s etc.) with client-side pagination (via Zerion API).
    * `/transactioncount <address>`: Display the Nonce (outgoing transaction count) for a wallet (via RPC).
* **NFT Portfolio (`/nfts <address>`):**
    * Displays NFT holdings grouped by collection (via Magic Eden API).
    * Presents each collection in a separate message with summary data (Owned, Listed, Floor) and a "[View My Items]" button.
    * Supports pagination for collections ("Load More Collections" clears previous batch).
    * "[View My Items]" button displays the first page of individual NFTs within that collection, each with an "Info" button.
    * Includes a "Back to Collections" button for navigation.
* **NFT Details:**
    * **Info Button:** Shows a detailed overview of an NFT (image/fallback, metadata, market stats).
    * **Offers Button:** Displays a paginated list of current bids/offers for the NFT.
    * **Activity Button:** Displays a paginated list of recent on-chain activity for the NFT.
* **Market & Activity:**
    * `/topcollections`: Interactive command to view top trending collections by Volume or Sales over selectable time periods (1h, 6h, 1d, 7d, 30d). Fetches Top 50 and displays results in a paginated, editable message.
    * `/mynftactivity <address>`: Shows a paginated feed of a user's recent NFT activity (sales, lists, bids, transfers, mints).
* **Advanced Analysis:**
    * `/uniquecontracts <address>`: Initiates a background scan of *all* user transactions (via Wallet API) to count unique interacted addresses. Provides periodic progress updates via message edits. Includes 24h cooldown, 5min timeout, and global lock for stability.
* **Bot Features:**
    * Command Rate Limiting (~5 seconds per user).
    * User/Bot Data Persistence (`bot_persistence.pkl`).
    * Modular Code Structure (`api_clients`, `formatters`, `handlers`, `utils`).

## Technologies Used

* Python 3.8+
* `python-telegram-bot` (v20+)
* `web3py`
* `requests`
* `python-dotenv`
* Magic Eden API (RTP v3)
* Zerion API (v1)
* Monad Testnet RPC

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-name>
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Linux/macOS
    # OR
    .\venv\Scripts\activate # On Windows
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create Environment File:**
    * Create a file named `.env` in the project root directory.
    * Add your API keys and RPC URL to this file:
        ```env
        T=YOUR_TELEGRAM_BOT_TOKEN
        R=YOUR_MONAD_TESTNET_RPC_URL
        MEK=YOUR_MAGIC_EDEN_API_KEY
        WK=YOUR_WALLET_API_KEY_(ZERION)
        # Optional: Define page sizes if you want to override defaults
        # COLLECTIONS_PAGE_SIZE=20
        # ITEMS_PER_PAGE=10
        # USER_ACTIVITY_PAGE_SIZE=15
        # TOKENS_PAGE_SIZE=20
        # TOP_COLL_RESULTS_PER_PAGE=15
        # TOP_COLL_FETCH_LIMIT=50
        ```
5.  **Run the bot:**
    ```bash
    python3 main.py
    ```

## Configuration

* API Keys and RPC URL are configured via the `.env` file.
* The `config.py` file loads these environment variables and sets default page sizes and API identifiers. Page sizes can be overridden by setting the corresponding variables in the `.env` file (e.g., `COLLECTIONS_PAGE_SIZE=15`).

## Usage

Interact with the bot on Telegram. Use the `/commands` command within the bot to see a list of available commands and their descriptions:

* `/start` - Starts the bot and shows welcome message.
* `/balance <address>` - Checks native token (MON) balance.
* `/tokens <address>` - Lists other token balances (ERC20s).
* `/nfts <address>` - Shows summary of NFT collections owned.
* `/mynftactivity <address>` - Shows recent NFT activity for wallet.
* `/topcollections` - Shows top collections by volume/sales (interactive).
* `/transactioncount <address>` - Shows Nonce (outgoing tx count).
* `/uniquecontracts <address>` - Scans all txs for unique interactions (can be slow).
* `/commands` - Displays this list of available commands.
## Project Structure

```
MONALYZER 
├── api_clients/
│   ├── __init__.py
│   ├── fetch_*.py
│   └── ...
├── formatters/
│   ├── __init__.py
│   ├── fmt_*.py
│   └── ...
├── handlers/
│   ├── __init__.py
│   ├── command_*.py
│   ├── callback_*.py
│   └── ...
├── utils/
│   └── __init__.py
├── .env
├── bot_persistence.pkl
├── config.py
├── main.py
└── requirements.txt
```

## Developer

* **Eccentric Healer**
* Telegram: `@eccentric_healer`
* Twitter: `@eccentrichealer`
* Discord: `eccentric.healer`
