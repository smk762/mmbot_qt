Anatara Makerbot Overview
=========================

The Antara Makerbot includes a number of tabbed pages as below:
- Activate: For authentication, loading coins and selecting which trade
- Market: Displays average market prices from API data, and view/purchase of available trades on the MarketMaker orderbook.
- Wallet: Simple interface for sending, recieving and viewing the balances of activated coins.
- Marketmaker Trade: Shows depth and allows manual order placement of selected pairs via Marketmaker, and shows tables of pending orders and completd swaps.
- Binance Trade: Shows Binance balances, open orders, and allows manual order placement for selected pairs.
- Bot Trading: Allows automated order placement of activated coin pairs on Marketmaker, and optional "at market" countertrades on completion via Binance.
- Config: Sets the parameters (e.g. seed phrase) for Marketmaker, Bot trading (e.g. trading premium) and Binance API keys (optional).
- Logs: Two console panels, which display raw Marketmaker stdout logs, and trading operations (orders place/completed).

Each tab and it's capabilities will be described in detail below.

Activate
--------

If not already logged in, you will see the screen below:

.. image:: img/activate_login.jpg
    :width: 200px
    :align: center
    :height: 100px
    :alt: Activate (login) tab
