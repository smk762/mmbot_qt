#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import subprocess
from os.path import expanduser
from . import coinslib, rpclib, binance_api

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

maker_success_events = ['Started', 'Negotiated', 'TakerFeeValidated', 'MakerPaymentSent', 'TakerPaymentReceived', 'TakerPaymentWaitConfirmStarted',
                        'TakerPaymentValidatedAndConfirmed', 'TakerPaymentSpent', 'Finished']

maker_errors_events = ['StartFailed', 'NegotiateFailed', 'TakerFeeValidateFailed', 'MakerPaymentTransactionFailed', 'MakerPaymentDataSendFailed',
                      'TakerPaymentValidateFailed', 'TakerPaymentSpendFailed', 'MakerPaymentRefunded', 'MakerPaymentRefundFailed', 'TakerPaymentWaitConfirmFailed', 'MakerPaymentWaitRefundStarted']

taker_success_events = ['Started', 'Negotiated', 'TakerFeeSent', 'MakerPaymentReceived', 'MakerPaymentWaitConfirmStarted',
                        'MakerPaymentValidatedAndConfirmed', 'TakerPaymentSent', 'TakerPaymentSpent', 'MakerPaymentSpent', 'Finished']

taker_errors_events = ['StartFailed', 'NegotiateFailed', 'TakerFeeSendFailed', 'MakerPaymentValidateFailed', 'TakerPaymentTransactionFailed',
                      'TakerPaymentDataSendFailed', 'TakerPaymentWaitForSpendFailed', 'MakerPaymentSpendFailed', 'TakerPaymentRefunded',
                      'TakerPaymentRefundFailed', 'MakerPaymentWaitConfirmFailed', 'TakerPaymentWaitRefundStarted']

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

def import_swaps(node_ip, user_pass, swaps):
    params = {'userpass': user_pass,
              'method': 'import_swaps',
              'swaps': [swaps]
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
    r = requests.post(node_ip, json=params)
    return r 

def withdraw_max(node_ip, user_pass, cointag, address, maxvolume=True):
    params = {'userpass': user_pass,
              'method': 'withdraw',
              'coin': cointag,
              'to': address,
              'max':maxvolume,}
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

# parse out user order uuids as a list
def get_mm2_order_uuids(node_ip, user_pass):
    orders = my_orders(node_ip, user_pass).json()
    mm2_order_uuids = []
    if 'maker_orders' in orders['result']:
        maker_orders = orders['result']['maker_orders']
        for item in maker_orders:
            mm2_order_uuids.append(item)
    if 'taker_orders' in orders['result']:
        taker_orders = orders['result']['taker_orders']
        for item in taker_orders:
            mm2_order_uuids.append(item)
    return mm2_order_uuids

def get_mm2_swap_events(events):
    event_types = []
    failed = False
    fail_event = False
    finished = False
    for event in events:
        event_types.append(event['event']['type'])
        if event['event']['type'] in error_events: 
            failed = True
            fail_event = event['event']['type']
        if event['event']['type'] == 'Finished':
            finished = event['timestamp']
    return failed, fail_event, finished, event_types

def get_trade_fee(coin):
    r = requests.get("http://127.0.0.1:8000/mm2_trade_fee/"+coin)
    if r.status_code == 200:
        trade_fee = t.text
    else: 
        trade_fee = 0.001
    return trade_fee

def process_mm2_buy(mm2_ip, mm2_pass, base, rel, vol, price):
    trade_val = round(float(price)*float(vol),8)
    trade_fee = get_trade_fee(rel)
    trade_vol = vol - float(trade_fee)*2
    resp = buy(mm2_ip, mm2_pass, base, rel, trade_vol, price).json()
    if 'error' in resp:
        while resp['error'].find("too low, required") > -1:
            time.sleep(0.01)
            logger.info("trade_vol error: "+str(resp['error']))
            logger.info("reducing trade vol 1% and trying again...")
            trade_vol = trade_vol*0.99
            resp = buy(mm2_ip, mm2_pass, base, rel, trade_vol, price).json()
            if 'error' not in resp:
                break
        if resp['error'].find("larger than available") > -1:
            msg = "Insufficient funds to complete order."
        else:
            msg = resp
    elif 'result' in resp:
        logger.info("Buying "+str(trade_vol)+" "+base +" for "+" "+str(trade_val)+" "+rel+" (fee estimate: "+str(trade_fee)+" "+rel+")")
        msg = "Order Submitted.\n"
        msg += "Buying "+str(trade_vol)+" "+base +"\nfor\n"+" "+str(trade_val)+" "+rel+"\nFee estimate: "+str(trade_fee)+" "+rel
    return msg