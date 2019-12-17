#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import subprocess
from os.path import expanduser
# from . import coinslib, binance_api

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

def coins_needed_for_kick_start(node_ip, user_pass):
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
    coin = coinslib.coin_activation[cointag]
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
    if from_id != '':
        method_params.update({"from_id":from_id})
    params = {'userpass': user_pass,
              'method': 'my_tx_history',
              "coin": coin,
              "limit": limit
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

def get_mm2_balances(node_ip, user_pass, active_coins):
    balances_data = {}
    for coin in active_coins:
        balances_data[coin] = {}
        balance_info = my_balance(node_ip, user_pass, coin).json()
        if 'address' in balance_info:
            address = balance_info['address']
            balance = round(float(balance_info['balance']),8)
            locked = round(float(balance_info['locked_by_swaps']),8)
            available = balance - locked
            balances_data[coin].update({
                'address':address,
                'balance':balance,
                'locked':locked,
                'available':available
            })
    return balances_data

def check_active_coins(node_ip, user_pass):
    active_cointags = []
    active_coins = get_enabled_coins(node_ip, user_pass).json()['result']
    for coin in active_coins:
        active_cointags.append(coin['ticker'])
    return active_cointags 