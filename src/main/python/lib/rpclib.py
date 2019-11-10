#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import subprocess
from os.path import expanduser
from . import coinslib, guilib, binance_api

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

maker_success_events = ['Started', 'Negotiated', 'TakerFeeValidated', 'MakerPaymentSent', 'TakerPaymentReceived', 'TakerPaymentWaitConfirmStarted',
                        'TakerPaymentValidatedAndConfirmed', 'TakerPaymentSpent', 'Finished']

maker_errors_events = ['StartFailed', 'NegotiateFailed', 'TakerFeeValidateFailed', 'MakerPaymentTransactionFailed', 'MakerPaymentDataSendFailed',
                      'TakerPaymentValidateFailed', 'TakerPaymentSpendFailed', 'MakerPaymentRefunded', 'MakerPaymentRefundFailed']

taker_success_events = ['Started', 'Negotiated', 'TakerFeeSent', 'MakerPaymentReceived', 'MakerPaymentWaitConfirmStarted',
                        'MakerPaymentValidatedAndConfirmed', 'TakerPaymentSent', 'TakerPaymentSpent', 'MakerPaymentSpent', 'Finished']

taker_errors_events = ['StartFailed', 'NegotiateFailed', 'TakerFeeSendFailed', 'MakerPaymentValidateFailed', 'TakerPaymentTransactionFailed',
                      'TakerPaymentDataSendFailed', 'TakerPaymentWaitForSpendFailed', 'MakerPaymentSpendFailed', 'TakerPaymentRefunded',
                      'TakerPaymentRefundFailed']

error_events = list(set(taker_errors_events + maker_errors_events))

#TODO: Review methods for optional params handling.

def buy(node_ip, user_pass, base, rel, basevolume, relprice):
    params ={'userpass': user_pass,
             'method': 'buy',
             'base': base,
             'rel': rel,
             'volume': basevolume,
             'price': relprice,}
    r = requests.post(node_ip,json=params)
    return r    

def cancel_all(node_ip, user_pass):
    params = {'userpass': user_pass,
              'method': 'cancel_all_orders',
              'cancel_by': {"type":"All"},}
    r = requests.post(node_ip,json=params)
    return r

def cancel_uuid(node_ip, user_pass, order_uuid):
    params = {'userpass': user_pass,
              'method': 'cancel_order',
              'uuid': order_uuid,}
    r = requests.post(node_ip,json=params)
    return r

def coins_needed_for_kick_start(node_ip, user_pass, order_uuid):
    params = {'userpass': user_pass,
              'method': 'coins_needed_for_kick_start'}
    r = requests.post(node_ip,json=params)
    return r

def disable_coin(node_ip, user_pass, coin):
    params = {'userpass': user_pass,
              'method': 'disable_coin',
              'coin': coin}
    r = requests.post(node_ip,json=params)
    return r

def electrum(node_ip, user_pass, cointag, tx_history=True):
    coin = coinslib.coins[cointag]
    if 'contract' in coin:
        params = {'userpass': user_pass,
                  'method': 'enable',
                  'urls':coin['electrum'],
                  'coin': cointag,
                  'swap_contract_address': coin['contract'],
                  'mm2':1,
                  'tx_history':tx_history,}
    else:
        params = {'userpass': user_pass,
                  'method': 'electrum',
                  'servers':coin['electrum'],
                  'coin': cointag,
                  'mm2':1,
                  'tx_history':tx_history,}
    r = requests.post(node_ip, json=params)
    return r

def enable(node_ip, user_pass, cointag, tx_history=True):
    coin = coinslib.coins[cointag]
    params = {'userpass': user_pass,
              'method': 'enable',
              'coin': cointag,
              'mm2':1,  
              'tx_history':tx_history,}
    r = requests.post(node_ip, json=params)
    return r

def get_enabled_coins(node_ip, user_pass):
    params = {'userpass': user_pass,
              'method': 'get_enabled_coins'}
    r = requests.post(node_ip, json=params)
    return r

def get_fee(node_ip, user_pass, coin):
    params = {'userpass': user_pass,
              'method': 'get_trade_fee',
              'coin': coin
              }
    r = requests.post(node_ip,json=params)
    return r

def help_mm2(node_ip, user_pass):
    params = {'userpass': user_pass, 'method': 'help'}
    r = requests.post(node_ip, json=params)
    return r.text

def import_swaps(node_ip, user_pass, coin):
    params = {'userpass': user_pass,
              'method': 'import_swaps',
              'swaps': swaps
              }
    r = requests.post(node_ip,json=params)
    return r

def my_balance(node_ip, user_pass, cointag):
    params = {'userpass': user_pass,
              'method': 'my_balance',
              'coin': cointag,}
    r = requests.post(node_ip, json=params)
    return r

def my_orders(node_ip, user_pass):
    params = {'userpass': user_pass, 'method': 'my_orders',}
    r = requests.post(node_ip, json=params)
    return r

def my_recent_swaps(node_ip, user_pass, limit=10, from_uuid=''):
    if from_uuid=='':
        params = {'userpass': user_pass,
                  'method': 'my_recent_swaps',
                  'limit': int(limit),}
        
    else:
        params = {'userpass': user_pass,
                  'method': 'my_recent_swaps',
                  "limit": int(limit),
                  "from_uuid":from_uuid,}
    r = requests.post(node_ip,json=params)
    return r

def my_swap_status(node_ip, user_pass, swap_uuid):
    params = {'userpass': user_pass,
              'method': 'my_swap_status',
              'params': {"uuid": swap_uuid},}
    r = requests.post(node_ip,json=params)
    return r

def my_tx_history(node_ip, user_pass, coin, limit=10, from_id=''):
    method_params = {"uuid": swap_uuid,
                     "coin": coin,
                     "limit": limit,
                     }
    if from_id != '':
        method_params.update({"from_id":from_id})
    params = {'userpass': user_pass,
              'method': 'my_tx_history',
              'params': method_params
                }
    r = requests.post(node_ip,json=params)
    return r

def order_status(node_ip, user_pass, uuid):
    params = {'userpass': user_pass,
              'method': 'order_status',
              'uuid': uuid,}
    r = requests.post(node_ip, json=params)
    return r

def orderbook(node_ip, user_pass, base, rel):
    params = {'userpass': user_pass,
              'method': 'orderbook',
              'base': base, 'rel': rel,}
    r = requests.post(node_ip, json=params)
    return r

def recover_stuck_swap(node_ip, user_pass, uuid):
    params = {'userpass': user_pass,
              'method': 'recover_funds_of_swap',
              'params': {'uuid':uuid}
              }
    r = requests.post(node_ip, json=params)
    return r    

def sell(node_ip, user_pass, base, rel, basevolume, relprice):
    params ={'userpass': user_pass,
             'method': 'sell',
             'base': base,
             'rel': rel,
             'volume': basevolume,
             'price': relprice,}
    r = requests.post(node_ip,json=params)
    return r    

def send_raw_transaction(node_ip, user_pass, cointag, rawhex):
    params = {'userpass': user_pass,
              'method': 'send_raw_transaction',
              'coin': cointag, "tx_hex":rawhex,}
    r = requests.post(node_ip, json=params)
    return r

def setprice(node_ip, user_pass, base, rel, basevolume, relprice, trademax=False, cancel_previous=True):
    params = {'userpass': user_pass,
              'method': 'setprice',
              'base': base,
              'rel': rel,
              'volume': basevolume,
              'price': relprice,
              'max':trademax,
              'cancel_previous':cancel_previous,}
    r = requests.post(node_ip, json=params)
    return r

def set_required_confirmations(node_ip, user_pass, cointag, confirmations):
    params = {'userpass': user_pass,
              'method': 'set_required_confirmations',
              'coin': cointag,
              'confirmations':confirmations,}
    r = requests.post(node_ip, json=params)
    return r

def stop_mm2(node_ip, user_pass):
    params = {'userpass': user_pass, 'method': 'stop'}
    try:
        r = requests.post(node_ip, json=params)
        msg = "MM2 stopped. "
    except:
        msg = "MM2 was not running. "
    return msg

def check_mm2_status(node_ip, user_pass):
    try: 
        help_mm2(node_ip, user_pass)
        return True
    except Exception as e:
        return False

def version(node_ip, user_pass):
    params = {'userpass': user_pass, 'method': 'version',}
    r = requests.post(node_ip, json=params)
    return r


def check_active_coins(node_ip, user_pass):
    active_cointags = []
    active_coins = get_enabled_coins(node_ip, user_pass).json()
    if 'result' in active_coins:
        active_coins = active_coins['result']
        for coin in active_coins:
            active_cointags.append(coin['ticker'])
        return active_cointags 
    else:
      print(active_coins)

def withdraw(node_ip, user_pass, cointag, address, amount, maxvolume=False):
    params = {'userpass': user_pass,
              'method': 'withdraw',
              'coin': cointag,
              'to': address,
              'amount': amount,}
    if maxvolume:
        params.update({"maxvolume":maxvolume})
    r = requests.post(node_ip, json=params)
    return r 

# deprecated?
def cancel_pair(node_ip, user_pass, base, rel):
    params = {'userpass': user_pass,
              'method': 'cancel_all_orders',
              'cancel_by': {
                    "type":"Pair",
                    "data":{"base":base,"rel":rel},
                    },}
    r = requests.post(node_ip,json=params)
    return r

def build_coins_data(node_ip, user_pass, cointag_list=''):
  try:
      if cointag_list == '':
          cointag_list = coinslib.cointags
      if 'KMD' not in cointag_list:
          cointag_list.append('KMD')
      coins_data = {}
      cointags = []
      gecko_ids = []
      print(guilib.colorize('Getting prices from Binance...', 'yellow'))
      for coin in cointag_list:
          coins_data[coin] = {}
          cointags.append(coin)
          coins_data[coin]['BTC_price'] = float(guilib.get_btc_price(coin))
          coins_data[coin]['price_source'] = 'binance'
          time.sleep(0.05)
      # Get Coingecko API ids
      print(guilib.colorize('Getting prices from CoinGecko...', 'pink'))
      gecko_coins_list = requests.get(url='https://api.coingecko.com/api/v3/coins/list').json()
      for gecko_coin in gecko_coins_list:
        try:
          if gecko_coin['symbol'].upper() in cointags:
              # override to avoid batcoin and dex
              if gecko_coin['symbol'].upper() == 'BAT':
                  coins_data[gecko_coin['symbol'].upper()]['gecko_id'] = 'basic-attention-token'
                  gecko_ids.append('basic-attention-token')
              elif gecko_coin['symbol'].upper() in ['DEX', 'CRYPTO']:
                  pass
              else:
                  coins_data[gecko_coin['symbol'].upper()]['gecko_id'] = gecko_coin['id']
                  gecko_ids.append(gecko_coin['id'])
        except Exception as e:
          print(colorize("error getting coingecko price for "+gecko_coin, 'red'))
          print(colorize(e, 'red'))
          pass
      # Get fiat price on Coingecko
      gecko_prices = gecko_fiat_prices(",".join(gecko_ids), 'usd,aud,btc').json()
      for coin_id in gecko_prices:
          for coin in coins_data:
              if 'gecko_id' in coins_data[coin]:
                  if coins_data[coin]['gecko_id'] == coin_id:
                      coins_data[coin]['AUD_price'] = gecko_prices[coin_id]['aud']
                      coins_data[coin]['USD_price'] = gecko_prices[coin_id]['usd']
                      if coins_data[coin]['BTC_price'] == 0:
                          coins_data[coin]['BTC_price'] = gecko_prices[coin_id]['btc']
                          coins_data[coin]['price_source'] = 'coingecko'
              else:
                  coins_data[coin]['AUD_price'] = 0
                  coins_data[coin]['USD_price'] = 0
      print(guilib.colorize('Getting prices from mm2 orderbook...', 'cyan'))
      for coin in coins_data:
          if coins_data[coin]['BTC_price'] == 0:
              mm2_kmd_price = get_kmd_mm2_price(node_ip, user_pass, coin)
              coins_data[coin]['KMD_price'] = mm2_kmd_price[1]
              coins_data[coin]['price_source'] = 'mm2_orderbook'
              coins_data[coin]['BTC_price'] = mm2_kmd_price[1]*coins_data['KMD']['BTC_price']
              coins_data[coin]['AUD_price'] = mm2_kmd_price[1]*coins_data['KMD']['AUD_price']
              coins_data[coin]['USD_price'] = mm2_kmd_price[1]*coins_data['KMD']['USD_price']
      for coin in coins_data:
          if coin == 'RICK' or coin == 'MORTY':
              coins_data[coin]['BTC_price'] = 0
              coins_data[coin]['AUD_price'] = 0
              coins_data[coin]['USD_price'] = 0
              coins_data[coin]['KMD_price'] = 0
              coins_data[coin]['price_source'] = 'mm2_orderbook'
      return coins_data
  except Exception as e:
    print(e)


def get_kmd_mm2_price(node_ip, user_pass, coin):
    kmd_orders = orderbook(node_ip, user_pass, coin, 'KMD').json()
    kmd_value = 0
    min_kmd_value = 999999999999999999
    total_kmd_value = 0
    max_kmd_value = 0
    kmd_volume = 0
    num_asks = len(kmd_orders['asks'])
    for asks in kmd_orders['asks']:
        kmd_value = float(asks['maxvolume']) * float(asks['price'])
        if kmd_value < min_kmd_value:
            min_kmd_value = kmd_value
        elif kmd_value > max_kmd_value:
            max_kmd_value = kmd_value
        total_kmd_value += kmd_value
        kmd_volume += float(asks['maxvolume'])
    if num_asks > 0:
        median_kmd_value = total_kmd_value/kmd_volume
    else:
        median_kmd_value = 0
    return min_kmd_value, median_kmd_value, max_kmd_value

def get_unfinished_swaps(node_ip, user_pass):
    unfinished_swaps = []
    unfinished_swap_uuids = []
    recent_swaps = my_recent_swaps(node_ip, user_pass, 50).json()
    for swap in recent_swaps['result']['swaps']:
        swap_events = []
        for event in swap['events']:
            swap_events.append(event['event']['type'])
        if 'Finished' not in swap_events:
            unfinished_swaps.append(swap)
            unfinished_swap_uuids.append(swap['uuid'])
    return unfinished_swap_uuids, unfinished_swaps
