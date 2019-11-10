#!/usr/bin/env python3
import json
import requests
from . import coinslib, guilib, binance_api

def gecko_fiat_prices(gecko_ids, fiat):
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = dict(ids=str(gecko_ids),vs_currencies=fiat)
    r = requests.get(url=url, params=params)
    return r

def get_btc_price(cointag):
    if cointag == 'BTC':
        return 1
    if cointag == 'BCH':
        btc_price = binance_api.get_price('BCHABCBTC')
    else:
        btc_price = binance_api.get_price(cointag+'BTC')
    if 'price' in btc_price:
        return btc_price['price']
    else:
        return 0