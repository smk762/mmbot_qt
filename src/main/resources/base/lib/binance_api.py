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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}
    elif r.status_code == 400:
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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}


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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}
    else:
        return r.json()

def create_buy_order(api_key, api_secret, ticker_pair, qty, price):
    print("Buying "+str(round_to_step(ticker_pair, qty))+" "+ticker_pair+" on Binance at "+str(round_to_tick(ticker_pair, price)))
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
        'quantity': round_to_step(ticker_pair, qty),
        'price': round_to_tick(ticker_pair, price),
        'recvWindow': 5000,
        'timestamp': timestamp
    }

    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    print(r.json())
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}
    else:
        return r.json()

def create_sell_order(api_key, api_secret, ticker_pair, qty, price):
    print("Selling "+str(round_to_step(ticker_pair, qty))+" "+ticker_pair+" on Binance at "+str(round_to_tick(ticker_pair, price)))
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
        'quantity': round_to_step(ticker_pair, qty),
        'price': round_to_tick(ticker_pair, price),
        'recvWindow': 5000,
        'timestamp': timestamp
    }
    query_string = urlencode(params)
    params['signature'] = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    url = urljoin(base_url, path)
    r = requests.post(url, headers=headers, params=params)
    print(r.json())
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}
    else:
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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}

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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}



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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}

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
    elif r.status_code == 401:
        return {"Error: Unauthorised"}


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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}

# Only returns from single symbol :(
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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}
    

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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}


def recent_trades(api_key, api_secret):
    path = '/api/v3/trades'
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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}

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
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401:
        return {"Error: Unauthorised"}

def round_to_step(symbol, qty):
    stepSize = '{:.8f}'.format(binance_pair_info[symbol]['stepSize'])
    precision = str(stepSize).replace('.','').find('1')
    new_qty = '{:.8f}'.format(round(float(qty),precision))
    return new_qty

def round_to_tick(symbol, price):
    tickSize = '{:.8f}'.format(binance_pair_info[symbol]['tickSize'])
    precision = str(tickSize).replace('.','').find('1')
    new_price = '{:.8f}'.format(round(float(price),precision))
    return new_price

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
            if filter_types['filterType'] == 'PRICE_FILTER':
                tickSize = filter_types['tickSize']
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
                    'stepSize':float(stepSize),
                    'tickSize':float(tickSize)
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

def get_binance_balances(key, secret):
    binance_balances = {}
    acct_info = get_account_info(key, secret)
    if 'balances' in acct_info:
        for item in acct_info['balances']:
            coin = item['asset']
            available = float(item['free'])
            locked = float(item['locked'])
            balance = locked + available
            binance_balances.update({coin:{
                    'available':available,
                    'locked':locked,
                    'total':balance
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

def get_binance_common_quoteAsset(base, rel):
    available_base_pairs = base_asset_info[base]['available_pairs']
    available_base_quote_assets = []
    for symbol in available_base_pairs:
        available_base_quote_assets.append(binance_pair_info[symbol]['quoteAsset'])
    available_rel_pairs = base_asset_info[rel]['available_pairs']
    available_rel_quote_assets = []
    for symbol in available_rel_pairs:
        available_rel_quote_assets.append(binance_pair_info[symbol]['quoteAsset'])
    return list(set(available_base_quote_assets)&set(available_rel_quote_assets))    

# For a given trade pair, determine if direct trade possible, or if a common quote asset is avaiable.
def get_binance_countertrade_symbols(bn_key, bn_secret, binance_balances, replenish_coin, spend_coin, replenish_coin_amount, spend_coin_amount):
    available_replenish_coin_pairs = base_asset_info[replenish_coin]['available_pairs']
    available_spend_coin_pairs = base_asset_info[spend_coin]['available_pairs']
    print("**** "+str(binance_balances))
    if replenish_coin not in binance_balances or spend_coin not in binance_balances:
        binance_balances = get_binance_balances(bn_key, bn_secret)
        print("## "+str(binance_balances))
    replenish_coin_bal = binance_balances[replenish_coin]['available']
    spend_coin_bal = binance_balances[spend_coin]['available']

    if replenish_coin in quoteAssets:
        # check if direct spend_coin trade possible
        for symbol in available_spend_coin_pairs:
            if binance_pair_info[symbol]['quoteAsset'] == replenish_coin:
                print("Direct trade symbol found (replenish_coin quote): "+symbol)
                return symbol, symbol
    if spend_coin in quoteAssets:
        # check if direct replenish_coin trade possible
        for symbol in available_replenish_coin_pairs:
            if binance_pair_info[symbol]['quoteAsset'] == spend_coin:
                print("Direct trade symbol found (spend_coin quote): "+symbol)
                return symbol, symbol

    # no common pair, check for common quote asset
    print("No common trade symbol, checking for common quote asset...")
    for replenish_coin_symbol in available_replenish_coin_pairs:
        replenish_coin_quoteAsset = binance_pair_info[replenish_coin_symbol]['quoteAsset']
        for spend_coin_symbol in available_spend_coin_pairs:
            spend_coin_quoteAsset = binance_pair_info[spend_coin_symbol]['quoteAsset']
            if spend_coin_quoteAsset == replenish_coin_quoteAsset:
                # calculate required quote asset value for trade, check if balance sufficient.
                quoteAsset_balance = binance_balances[replenish_coin_quoteAsset]['available']
                replenish_coin_symbol_market_price = get_price(bn_key, replenish_coin_symbol)['price']
                quoteAsset_req = float(replenish_coin_amount)*float(replenish_coin_symbol_market_price)
                if quoteAsset_req < quoteAsset_balance:
                    print("Indirect countertrading with "+replenish_coin_quoteAsset)
                    print("spend_coin_symbol: "+spend_coin_symbol)
                    print("replenish_coin_symbol: "+replenish_coin_symbol)
                    return spend_coin_symbol, replenish_coin_symbol
                else:
                    print("Not enough "+replenish_coin_quoteAsset+" balance to countertrade! "+str(quoteAsset_req)+" needed, "+str(quoteAsset_balance)+" available")
    # If no match is found
    return False, False

exch_info = get_exchange_info()
binance_pairs = exch_info[0]
base_asset_info = exch_info[1]
quoteAssets = exch_info[2]
binance_pair_info = exch_info[3]
supported_binance_pairs = exch_info[4]
