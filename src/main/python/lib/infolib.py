#!/usr/bin/env python3
import json
import coinslib, priceslib
import requests
from statistics import mean

'''
r = requests.get("https://api.coinpaprika.com/v1/coins")
paprika_coins = r.json()
r = requests.get("https://api.coingecko.com/api/v3/coins/list")
gecko_coins = r.json()
r = requests.get("https://api.binance.com/api/v1/ticker/allPrices")
binance_coins = r.json()

binance_api = []
for item in binance_coins:
    if item['symbol'][-3:] == 'BTC':
        print(item['symbol'][:-3])
        binance_api.append(item['symbol'][:-3])

gecko_api = []
for coin in gecko_coins:
    if coin['symbol'].upper() in coinslib.cointags:
        gecko_api.append(coin)

paprika_api = []
for coin in paprika_coins:
    if coin['symbol'].upper() in coinslib.cointags:
        paprika_api.append(coin)

api_codes = {}
for coin in coinslib.cointags:
    name1 = ''
    name2 = ''
    gecko_id = ''
    paprika_id = ''
    binance_id = ''
    if coin in binance_api:
        binance_id = coin
    for item in gecko_api:
        if coin.lower() == item['symbol']:
            gecko_id = item['id']
            name1 = item['name']
    for item in paprika_api:
        if coin == item['symbol']:
            paprika_id = item['id']
            name2 = item['name']
    if name1 == name2:
        name = name1
    elif name1 == '':
        name = name2
    elif name2 == '':
        name = name1
    else:
        name = name1 +" || "+ name2

    api_codes[coin] = {
        "coingecko_id":gecko_id,
        "binance_id":binance_id,
        "paprika_id":paprika_id,
        "name":name
    }
print(api_codes)

coin_explorers = {}

for coin in coinslib.cointags:
    if coinslib.coin_activation[coin]['type'] == 'erc20':
        tx_explorer = "https://etherscan.io/tx"
        addr_explorer = "https://etherscan.io/address"
    elif coinslib.coin_activation[coin]['type'] == 'smartchain':
        tx_explorer = "https://"+coin.lower()+".explorer.dexstats.info/tx"
        addr_explorer = "https://"+coin.lower()+".explorer.dexstats.info/address"
    else:
        tx_explorer = ""
        addr_explorer = ""
    coin_explorers[coin] = {
        "tx_explorer":tx_explorer,
        "addr_explorer":addr_explorer
    }

print(coin_explorers)
'''

print(priceslib.get_prices_data())


'''
i = 0
for coin in coinslib.coin_api_codes:
    api_id = coinslib.coin_api_codes[coin]['paprika_id']
    if api_id != '':
        i += 1
        r = requests.get("https://api.coinpaprika.com/v1/tickers/"+api_id).json()
        print(r)
print(i)
'''