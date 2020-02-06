Anatara Makerbot Overview
=========================

The Antara Makerbot includes a number of tabbed pages as summarised below.

###### _Some tabs are only accessible if coin(s) have been activated, and valid Binance API keys are required to enable some functions._

**Table of Contents**

* **[Activate](#activate)** - For login authentication, and loading coins to use in Marketmaker.
* **[Marketmaker](#marketmaker)** - Allows manual order placement of selected pairs via Marketmaker, and shows a table of open orders.
* **[Binance](#binance)** - View Binance balances, open orders, and perform manual order placement for pair symbols.
* **[Wallet](#wallet)** - Simple interface for sending, recieving and viewing the balances of Marketmaker activated coins.
* **[Strategies](#strategies)** - Create automated buy/sell strategies with selected coin pairs on Marketmaker, including countertrades on completion via Binance (if API keys and funds available).
* **[Prices](#prices)** - Shows pricing data from CoinGecko / CoinPaprika / Binance APIs, along with mean weighted price (in KMD) of open offers in Marketmaker orderbook.
* **[History](#history)** - View Marketmaker trade history, and history of trades performed using automated strategies.
* **[Config](#config)** - Set parameters (e.g. seed phrase) for Marketmaker,and Binance API keys (optional). A tool to recover stuck swaps is also available.
* **[Logs](#logs)** - Two console panels, displaying mm2 logs, and mmbot_api logs.
 
 #### Activate
 Upon loading the Makerbot app, you'll see a login page.
 ![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/makerbot_login.png "Makerbot login page")

To create a new user, simply enter a username, along with password. If the username has not previously been used on the computer you have installed the app on, you'll be given the option to create a new user, then generate a wallet seed phrase and set some other settings in the [config tab](#config). 

_User settings (wallet seed, api keys etc) are encrypted and stored on your device, with your password as the decryption key_

Once the user has been created, enter your username and password to access the activation page. 
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/activating.png "Makerbot coin activation page")

Here you can select the coins to activate by clicking on the coin's checkbox. The activation lists are categorised by coin type (KMD/Smartchain, UTXO or ETH/ERC20). 

Via the bar at the top, the coins lists can be filtered by using the search input, and bulk selections can be made for the subsets of coins which are compatible with Binance or the CoinGecko and CoinPaprika price APIs.

Once you've made your selection, click the Activate button to begin activating coins. 

_Note: Some tabs require one or more coins to be activated before they are accessible_
 
 #### Marketmaker
The Marketmaker tab features two drop down menus to select coins for buy / sell, with your current balance of the selected coins displayed alongside their respective logos.
 
Changing the dropdown coin selection will populate the orderbook table with available trades - clicking on a row will populate the price input, and clicking the percentage buttons will populate the sell quantity input (though you can also input price and amount manually to create a new order).

Changing an input value for price / buy qty / sell qty will automatically update other input fields so you can see, for example, how many DASH you will recieve for the input quantity of KMD for a given price.
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/mm_orderbook.png "Marketmaker Trade Page")

Any open orders you have in the orderbook will also be displayed in the lower table. By selecting a row in the table, you can view or cancel the order (or all orders) clicking the buttons at the bottom.
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/open_orders.png "Marketmaker Open Orders")
 
 #### Binance
 The Binance tab requires valid API keys to be setup in the [config tab](#config) for full functionality (though this is not required to use the Makerbot app for manual trades or to send/recieve funds). With or without API keys, you can check the current price and depth of a supported pair of coins.
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/binance_depth.png "Binance Depth")

If you have setup API keys, this tab will also display the balance of coins in your Binance account...
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/bn_bal.png "Binance balances")

...and any open orders you have placed via Binance. 
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/bn_orders.png "Binance Open Orders")
 
Below the balances table, the Binance recieving address for a given coin can be seen by selecting it in the dropdown menu (or clicking a row in the balances table). Click the QR code button to reveal a scanable QR code of the address to make a deposit.

![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/bn_withdraw.png "Binance Open Orders")
 
You also have the option to withdraw funds from Binance and send them to any valid address, by using the inputs at the bottom of the balances table.
 
 #### Wallet

The wallet tab is exactly what it sounds like. Here you can send / recieve coins in your Marketmaker wallet. Balances are listed in a table on the left, with USD, BTC, and KMD values for each coin and your portfolio as a whole for reference. 
 
![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/wallet.png "Marketmaker Wallet Tab")
 
Transaction history is available by clicking on your address, which will open it on a block explorer. There is also a QR code button to display a scanable QR code for recieving funds.
 
 #### Strategies
In this tab, you can set automated strategies for trading between subsets of activated coins at a preset margin. There are two modes: Margin and Arbitrage. Valid API keys must be set in the [config tab](#config) to allow CEX countertrades to be performed.

Margin mode creates Maker orders on the Marketmaker orderbook, and once an order is matched and completed, it will initiate a counter trade on Binance (with other CEX integrations planned for future releases). 

Arbitrage mode will periodically scan the Marketmaker orderbook and compare available orders against potential counter trades on Binance (or other CEX platforms - in future). If an arbitrage opportunity is detected, the qualifying Marketmaker trade will initiate, and once completed, initiate a CEX countertrade.

_Note: Trades of less than $10 in value do not initiate a countertrade._

As CEX platforms are generally limited in trade pairs, countertrades initiated after a Marketmaker swap are likely to require two CEX trades via a common quote asset. Consider the two examples below, with the strategy margin percentage is set to 5%.

Direct counter trade (BTC to KMD):
* For convenience, assume the Binance price for KMDBTC is 0.0001 (10,000 KMD per BTC)
* Marketmaker bot creates a Maker order with selling 1 BTC for 10,500 KMD. The order is matched and the swap completes.
* Binance has a KMDBTC pair, so a direct trade is possible.
* A CEX counter trade is submitted to with the price set to buy 1 BTC for 10,000 KMD, netting 500 KMD profit.

Indirect counter trade (ZEC to KMD):
* For convenience, assume the Binance price for KMDBTC is 0.0001 (10,000 KMD per BTC), and the ZECBTC price is 0.001 (1000 ZEC per BTC)
* Marketmaker bot trade selling 1 ZEC for 105 KMD completes.
* Binance does not have a KMDZEC pair, so a direct trade is not possible.
* There is a KMDBTC pair, and a ZECBTC pair though, so the countertrade can be done via BTC.
* The strategy margin percentage is set to 5%, so the first leg of the CEX counter trade is submitted to with the price set to sell 100 KMD for 0.01 BTC.
* The second leg of the CEX countertrade buys 1 ZEC for 0.01 BTC.

_Note: CEX countertrades will require sufficient available balance in CEX wallets to be performed.

In both cases, the coin sold in the Marketmaker trade is replenished by purchasing the equvalent amount via Binance, which is paid for by selling the equivalent amount of the coin recieved in the Makertmaker swap via Binance (after applying the strategy margin percentage). 

As a result your Binance balance for coin A decreases and for coin B it increases, with the opposite being true for the respective balances in Marketmaker, with with a modest 5% bonus above the trade value.

_Note: Due to the enforced quantity and price increments on Binance (and other CEX platforms), it is rarely so exact as Marketmaker trade price and volumes are generally of greater precision. As a result, countertrades are performed as close as possible to the original Marketmaker price & amount that is allowable on the CEX platform. This will often cause the 5% bonus to be partially spread across the coins involved in the trade._ 

The Bot strategy summary table will display the status of Marketmaker trades and their countertrades, along with the delta values of each coin involed in the trades for each bot trading session and cummulatively over time. 

 
 #### Prices
 
 #### History
 
 #### Config
 
 #### Logs
 
This tab shows the raw output logs from the mm2 binary (top table) and the makerbot API (bottom table) for convenience, and to assist in debugging.

![alt text](https://raw.githubusercontent.com/smk762/mmbot_qt/api/docs/img/logs.png "Logs Tab")

 
 
