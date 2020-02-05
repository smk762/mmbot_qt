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

_User settings (wallet seed, api keys etc) are encrypted and stored on your device, with your password as the decryption key _

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
 #### Wallet
 #### Strategies
 #### Prices
 #### History
 #### Config
 #### Logs
 
 
