#!/usr/bin/env python3
import os
from os.path import expanduser
import time
import json
import hmac
import hashlib
import requests
import sys
from urllib.parse import urljoin, urlencode
from . import coinslib

# Get and set config
cwd = os.getcwd()
home = expanduser("~")

# from https://code.luasoftware.com/tutorials/cryptocurrency/python-connect-to-binance-api/

# fee = 0.1% or less (using bnb or large volume)

base_url = 'https://api.binance.com'

class BinanceException(Exception):
    def __init__(self, status_code, data):
        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"
        super().__init__(message)

def get_serverTime():
    path =  '/api/v1/time'
    params = None

    timestamp = int(time.time() * 1000)

    url = urljoin(base_url, path)
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        print(f"diff={timestamp - data['serverTime']}ms")
    else:
        raise BinanceException(status_code=r.status_code, data=r.json())

def get_price(api_key, ticker_pair):
    path = '/api/v3/ticker/price'
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair
    }
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def get_historicalTrades(api_key, ticker_pair):
    path = '/api/v3/historicalTrades'
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair
    }
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    return r.json()


def get_depth(api_key, ticker_pair, limit):
    path = '/api/v3/depth'
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'limit': limit
    }
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()
    else:
        raise BinanceException(status_code=r.status_code, data=r.json())

def get_open_orders(api_key, api_secret):
    path = '/api/v3/openOrders'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'recvWindow': 5000,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def create_buy_order(api_key, api_secret, ticker_pair, qty, price):
    path = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'side': 'BUY',
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': qty,
        'price': price,
        'recvWindow': 5000,
        'timestamp': timestamp
    }

    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    return r.json()

def create_sell_order(api_key, api_secret, ticker_pair, qty, price):
    print("Selling "+str(qty)+" "+ticker_pair+" on Binance at "+str(price))
    path = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'side': 'SELL',
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': qty,
        'price': price,
        'recvWindow': 5000,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    return r.json()



def create_buy_order_at_market(api_key, api_secret, ticker_pair, qty):
    path = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'side': 'BUY',
        'type': 'MARKET',
        'quantity': qty,
        'recvWindow': 5000,
        'timestamp': timestamp
    }

    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    return r.json()

def create_sell_order_at_market(api_key, api_secret, ticker_pair, qty):
    path = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'side': 'SELL',
        'type': 'MARKET',
        'quantity': qty,
        'recvWindow': 5000,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    return r.json()



def get_account_info(api_key, api_secret):
    path = '/api/v3/account'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'recvWindow': 5000,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    return r.json()

def get_order(api_key, api_secret, ticker_pair, order_id):
    path = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'orderId': order_id,
        'recvWindow': 5000,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()

def delete_order(api_key, api_secret, ticker_pair, order_id):
    path = '/api/v3/order'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'symbol': ticker_pair,
        'orderId': order_id,
        'recvWindow': 5000,
        'timestamp': timestamp
    }

    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    url = urljoin(base_url, path)
    r = requests.delete(url, headers=headers, params=params)
    if r.status_code == 200:
        data = r.json()
        return data
    else:
        raise BinanceException(status_code=r.status_code, data=r.json())

def get_deposit_addr(api_key, api_secret, asset):
    path = '/wapi/v3/depositAddress.html'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'asset': asset,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    return r.json()

# Only rteturns from single symbol :(
def get_binance_orders_history(api_key, api_secret, symbol):
    path = '/api/v3/allOrders'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'timestamp': timestamp,
        'symbol': symbol
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.get(url, headers=headers, params=params)
    return r.text
    

# Returns error 500 at the moment
def asset_detail(api_key, api_secret):
    path = '/wapi/v3/assetDetail.html'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    return r.json()

def withdraw(api_key, api_secret, asset, addr, amount):
    path = '/wapi/v3/withdraw.html'
    timestamp = int(time.time() * 1000)
    headers = {
        'X-MBX-APIKEY': api_key
    }
    params = {
        'asset': asset,
        'address': addr,
        'amount': amount,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    return r.json()

def round_to_step(symbol, qty):
    stepSize = binance_pair_info[symbol]['stepSize']
    return round(float(qty)/float(stepSize))*float(stepSize)

def get_exchange_info():
    resp = requests.get("https://api.binance.com/api/v1/exchangeInfo").json()
    binance_pairs = []
    supported_binance_pairs = []
    binance_pair_info = {}
    base_asset_info = {}
    quoteAssets = []
    for item in resp['symbols']:
        symbol = item['symbol']
        status = item['status']
        baseAsset = item['baseAsset']
        quoteAsset = item['quoteAsset']
        for filter_types in item['filters']:
            if filter_types['filterType'] == 'LOT_SIZE':
                minQty = filter_types['minQty']
                maxQty = filter_types['maxQty']
                stepSize = filter_types['stepSize']
            if filter_types['filterType'] == 'MIN_NOTIONAL':
                minNotional = filter_types['minNotional']
        if status == "TRADING":
            base_asset_info.update({
                baseAsset:{
                    'minQty':float(minQty),
                    'maxQty':float(maxQty),
                    'stepSize':float(stepSize)
                }
            })
            binance_pair_info.update({
                symbol:{
                    'baseAsset':baseAsset,
                    'quoteAsset':quoteAsset,
                    'minQty':float(minQty),
                    'maxQty':float(maxQty),
                    'minNotional':float(minNotional),
                    'stepSize':float(stepSize)
                }
            })
            binance_pairs.append(symbol)
            if quoteAsset not in quoteAssets:
                quoteAssets.append(quoteAsset)

    for base in base_asset_info:
        quotes = []
        available_pairs = []
        for rel in quoteAssets:
            if base+rel in binance_pairs:
                symbol = base+rel
                available_pairs.append(symbol)
            elif rel+base in binance_pairs:
                symbol = rel+base
                available_pairs.append(symbol)
            else:
                for quote in quoteAssets:
                    if base+quote in quoteAssets:
                        symbol = rel+base
                        available_pairs.append(symbol)
                        quotes.append(quote)
                    elif quote+base in quoteAssets:
                        symbol = base+rel
                        available_pairs.append(symbol)
                        quotes.append(quote)
        available_pairs.sort()
        base_asset_info[base].update({'available_pairs':available_pairs})
        base_asset_info[base].update({'quote_assets':quotes})
    for base in coinslib.coin_api_codes:
        if base in base_asset_info:
            supported_binance_pairs += base_asset_info[base]['available_pairs']
    supported_binance_pairs = list(set(supported_binance_pairs))
    binance_pairs.sort()
    supported_binance_pairs.sort()
    quoteAssets.sort()
    return binance_pairs, base_asset_info, quoteAssets, binance_pair_info, supported_binance_pairs


exch_info = get_exchange_info()
binance_pairs = exch_info[0]
base_asset_info = exch_info[1]
quoteAssets = exch_info[2]
binance_pair_info = exch_info[3]
supported_binance_pairs = exch_info[4]

def get_binance_balances(key, secret):
    binance_balances = {}
    acct_info = get_account_info(key, secret)
    if 'balances' in acct_info:
        for item in acct_info['balances']:
            coin = item['asset']
            available = float(item['free'])
            locked = float(item['locked'])
            balance = locked + available
            resp = get_deposit_addr(key, secret, coin)
            if 'address' in resp:
                addr_text = resp['address']
            else:
                addr_text = 'Address not found - create it at Binance.com'
            binance_balances.update({coin:{
                    'available':available,
                    'locked':locked,
                    'total':balance,
                    'address':addr_text
                }
            })
    return binance_balances


def get_binance_addresses(key, secret):
    binance_addresses = {}
    acct_info = get_account_info(key, secret)
    if 'balances' in acct_info:
        for item in acct_info['balances']:
            coin = item['asset']
            resp = get_deposit_addr(key, secret, coin)
            if 'address' in resp:
                addr_text = resp['address']
            else:
                addr_text = 'Address not found - create it at Binance.com'
            address = addr_text
            binance_addresses.update({coin:address})
    return binance_addresses

