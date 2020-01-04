#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from . import rpclib, priceslib, binance_api

# CACHE DATA LOOPS

def start_mm2_bot_loop(creds, buy_coins, sell_coins, cancel_previous, trade_max):
    for base in sell_coins:
        for rel in buy_coins:
            if base != rel:
                pass
                    # detect unfinished swaps

def orderbook_loop(mm2_ip, mm2_rpc_pass, config_path ):
    print("starting orderbook loop")
    active_coins = mm2_active_coins(mm2_ip, mm2_rpc_pass)
    orderbook_data = []
    for base in active_coins:
        for rel in active_coins:
            if base != rel:
                orderbook_pair = get_mm2_pair_orderbook(mm2_ip, mm2_rpc_pass, base, rel)
                orderbook_data.append(orderbook_pair)
    print("orderbook loop completed")
    return orderbook_data
    
def bot_loop(mm2_ip, mm2_rpc_pass, prices_data, config_path):
    print("starting bot loop")
    strategies = [ x[:-5] for x in os.listdir(config_path+'/strategies') if x.endswith("json") ]
    bot_data = "bot data placeholder"
    for strategy_name in strategies:
        with open(config_path+"history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        if history['Status'] == 'active':
            print("Active strategy: "+strategy_name)
            with open(config_path+"strategies/"+strategy_name+".json", 'r') as f:
                strategy = json.loads(f.read())
            # check refresh interval vs last refresh
            if history['Last refresh'] == 0 or history['Last refresh'] + strategy['Refresh interval']*2 < int(time.time()):
                active_coins = mm2_active_coins(mm2_ip, mm2_rpc_pass)
                strategy_coins = list(set(strategy['Sell list']+strategy['Buy list']))
                inactive_skip = False
                for coin in strategy_coins:
                    if coin not in active_coins:
                        inactive_skip = True
                        break
                if not inactive_skip:
                    print("*** Refreshing strategy: "+strategy_name+" ***")
                    history.update({'Last refresh':int(time.time())})
                    # cancel old orders
                    history = cancel_session_orders(history)
                    # place fresh orders
                    history = submit_strategy_orders(mm2_ip, mm2_rpc_pass, strategy, history)
                    # update session history
                    with open(config_path+"history/"+strategy_name+".json", 'w+') as f:
                         f.write(json.dumps(history, indent=4))
                else:
                    print("Skipping strategy "+strategy_name+": MM2 coins not active ")
    print("bot loop completed")
    return bot_data

def mm2_balances_loop(mm2_ip, mm2_rpc_pass, coin):
    # get mm2 balance
    balance_info = rpclib.my_balance(mm2_ip, mm2_rpc_pass, coin).json()
    if 'balance' in balance_info:
        address = balance_info['address']
        coin = balance_info['coin']
        total = balance_info['balance']
        locked = balance_info['locked_by_swaps']
        available = float(total) - float(locked)
        mm2_coin_balance_data = {
            coin: {
                    "address":address,
                    "total":total,
                    "locked":locked,
                    "available":available,
                }                
            }
    return mm2_coin_balance_data

def bn_balances_loop(bn_key, bn_secret):
    # get binance balances
    binance_balances = binance_api.get_binance_balances(bn_key, bn_secret)
    bn_balances_data = {}
    for coin in binance_balances:
        address = binance_balances[coin]['address']
        available = binance_balances[coin]['available']
        locked = binance_balances[coin]['locked']
        total = binance_balances[coin]['total']
        bn_balances_data.update({coin: {
            "address":address,
            "total":total,
            "locked":locked,
            "available":available,
            }                
        })
    return bn_balances_data

# MISC

def mm2_active_coins(mm2_ip, mm2_rpc_pass):
    active_coins = []
    active_coins_data = rpclib.get_enabled_coins(mm2_ip, mm2_rpc_pass).json()
    if 'result' in active_coins_data:
        for coin in active_coins_data['result']:
            active_coins.append(coin['ticker'])
    return active_coins

# STRATEGIES

def submit_strategy_orders(mm2_ip, mm2_rpc_pass, strategy, history):
    prices_data = priceslib.prices_loop()
    print("*** submitting strategy orders ***")
    print("Strategy: "+str(strategy))
    if strategy['Type'] == 'margin':
        history = run_margin_strategy(mm2_ip, mm2_rpc_pass, strategy, history, prices_data)
    elif strategy['Type'] == 'arbitrage':
        history = run_arb_strategy(mm2_ip, mm2_rpc_pass, strategy, history)
    return history

def run_arb_strategy(mm2_ip, mm2_rpc_pass, strategy, history):
    orderbook_data = orderbook_loop(mm2_ip, mm2_rpc_pass)
    prices_data = priceslib.prices_loop()
    # check balances
    balances = {}
    for base in strategy['Buy list']:
        for rel in strategy['Sell list']:
            if base != rel:
                best_price = 999999999999999999999999999999999
                # get binance price
                binance_prices = priceslib.get_binance_price(base, rel, prices_data)
                # TODO: get bid and ask for binance, not just simple price.
                if 'direct' in binance_prices:
                    print("Binance Price (direct): "+str(binance_prices['direct']))
                    # TODO: check this for price compare later with direct pair
                if 'indirect' in binance_prices:
                    for quote in binance_prices['indirect']:
                        print("Binance Price (indirect via "+quote+"): "+str(binance_prices['indirect'][quote]))
                        price = binance_prices['indirect'][quote][base+rel]
                        if price < best_price:
                            best_price = binance_prices['indirect'][quote][base+rel]
                            best_symbol = quote
                print("Binance Best Price (via "+quote+"): "+str(best_price))
                print("mm2 offers: "+base+rel)
                for pair in orderbook_data:
                    if base+rel in pair:
                        bids = pair[base+rel]['asks']
                        asks = pair[base+rel]['bids']
                print("BIDS")
                for item in bids:
                    mm2_price = float(item['price'])
                    pct = best_price/mm2_price-1
                    print(str(item)+"  (pct vs binance best = "+str(pct)+"%)")
                print("ASKS")
                for item in asks:
                    mm2_price = float(item['price'])
                    pct = best_price/mm2_price-1
                    print(str(item)+"  (pct vs binance best = "+str(pct)+"%)")
                print("---------------------------------------------------------")
            # check if any mm2 orders under binance price
            pass

def run_margin_strategy(mm2_ip, mm2_rpc_pass, strategy, history, prices_data):
    uuids = []
    for rel in strategy['Buy list']:
        for base in strategy['Sell list']:
            if base != rel:
                # in case prices data not yet populated
                if base in prices_data['average']:
                    base_btc_price = prices_data['average'][base]['BTC']
                    rel_btc_price = prices_data['average'][rel]['BTC']
                    # todo: make fin safe (no float)
                    rel_price = (base_btc_price/rel_btc_price)*(1+strategy['Margin']/100)
                    base_balance_info = rpclib.my_balance(mm2_ip, mm2_rpc_pass, base).json()
                    available_base_balance = float(base_balance_info["balance"]) - float(base_balance_info["locked_by_swaps"])
                    basevolume = available_base_balance * strategy['Balance pct']/100
                    print("trade price: "+base+" (base) / "+rel+" (rel) "+str(rel_price)+" volume = "+str(basevolume))
                    # place new order
                    # TODO: check if order swap in progress or finished. If finished, initiate CEX countertrade.
                    if strategy['Balance pct'] != 100:
                        resp = rpclib.setprice(mm2_ip, mm2_rpc_pass, base, rel, basevolume, rel_price, False, True)
                    else:
                        resp = rpclib.setprice(mm2_ip, mm2_rpc_pass, base, rel, basevolume, rel_price, True, True)
                    print("Setprice Order created: " + str(resp.json()))
                    uuid = resp.json()['result']['uuid']
                    uuids.append(uuid)
                else:
                    print("No price data yet...")
    history['Sessions'][str(len(history['Sessions'])-1)]['MM2 open orders'] = uuids
    return history
    # update session history with open orders

def cancel_session_orders(history):
    print("cancelling session orders")
    session = history['Sessions'][str(len(history['Sessions'])-1)]
    if 'binance' in session['CEX open orders']:
        binance_orders = session['CEX open orders']['binance']
        for symbol in binance_orders:
            order_id = binance_orders[symbol]
            binance_api.delete_order(bn_key, bn_secret, symbol, order_id)
    # add other cex when integrated
    mm2_order_uuids = session['MM2 open orders']
    for order_uuid in mm2_order_uuids:
        # TODO: dont cancel if in progress, until in progress complete.
        rpclib.cancel_uuid(mm2_ip, mm2_rpc_pass, order_uuid)
    history['Sessions'][str(len(history['Sessions'])-1)]['MM2 open orders'] = []
    history['Sessions'][str(len(history['Sessions'])-1)]['CEX open orders']['binance'] = []
    return history

def cancel_strategy(history):
    if len(history['Sessions']) > 0:
        sessions = history['Sessions']
        session = history['Sessions'][str(len(history['Sessions'])-1)]
        started_at = session['Started']
        duration = int(time.time()) - started_at
        session.update({"Duration":duration})
        mm2_open_orders = session["MM2 open orders"]
        for order_uuid in mm2_open_orders:
            rpclib.cancel_uuid(mm2_ip, mm2_rpc_pass, order_uuid)
        cex_open_orders = session["CEX open orders"]
        for order in cex_open_orders:
            if 'binance' in cex_open_orders:
                for symbol in cex_open_orders['binance']:
                    order_id = cex_open_orders['binance'][symbol]
                    binance_api.delete_order(bn_key, bn_secret, symbol, order_id)
        mm2_swaps_in_progress = session["MM2 swaps in progress"]
        for swap in mm2_swaps_in_progress:
            # alreay cancelled, move to completed, and mark as "cancelled while in progress"
            pass
        cex_swaps_in_progress = session["CEX swaps in progress"]
        for swap in cex_swaps_in_progress:
            # already cancelled, move to completed, and mark as "cancelled while in progress"
            pass

        mm2_swaps_completed = session["MM2 swaps completed"]
        for swap in mm2_swaps_completed:
            print(swap)
            '''
            # calculate deltas
            spent_coin = 
            recieved_coin = 
            spent_amount = 
            recieved_amount = 
            session["Balance Deltas"][spent_coin]-spent_amount
            session["Balance Deltas"][recieved_coin]+recieved_amount
            # DEX FEES?
            # CEX FEES?
            '''
        cex_swaps_completed = session["CEX swaps completed"]
        for swap in cex_swaps_completed:
            # calculate deltas
            print(swap)
            '''
            spent_coin = 
            recieved_coin = 
            spent_amount = 
            recieved_amount = 
            session["Balance Deltas"][spent_coin]-spent_amount
            session["Balance Deltas"][recieved_coin]+recieved_amount
            '''
        sessions.update({str(len(history['Sessions'])-1):session})
        history.update({"Sessions":sessions})
    return history

# STRATEGY INITIALIZATION

def init_history_file(name, strategy_coins, config_path):
    balance_deltas = {}
    for strategy_coin in strategy_coins:
        balance_deltas.update({strategy_coin:0})
    history = { 
        "Sessions":{},
        "Last refresh": 0,
        "Total MM2 swaps completed": 0,
        "Total CEX swaps completed": 0,
        "Total balance deltas": balance_deltas,
        "Status":"inactive"
    }
    with open(config_path+"history/"+name+".json", 'w+') as f:
        f.write(json.dumps(history, indent=4))

def init_strategy_file(name, strategy_type, rel_list, base_list, margin, refresh_interval, balance_pct, cex_list, config_path):
    strategy = {
        "Name":name,
        "Type":strategy_type,
        "Sell list":rel_list,
        "Buy list":base_list,
        "Margin":margin,
        "Refresh interval":refresh_interval,
        "Balance pct":balance_pct,
        "CEX countertrade list":cex_list
    }
    with open(config_path+"strategies/"+name+'.json', 'w+') as f:
        f.write(json.dumps(strategy, indent=4))

    if not os.path.exists(config_path+"history/"+name+".json"):
        strategy_coins = list(set(rel_list+base_list))
        init_history_file(name, strategy_coins, config_path)
    return strategy

def init_session(strategy_name, strategy, history, config_path):
    history.update({"Status":"active"})
    # init balance datas
    balance_deltas = {}
    for rel in strategy["Sell list"]:
        balance_deltas.update({rel:0})
    for base in strategy["Buy list"]:
        if base not in strategy["Sell list"]:
            balance_deltas.update({base:0})
    # init session
    sessions = history['Sessions']
    sessions.update({str(len(sessions)):{
            "Started":int(time.time()),
            "Duration":0,
            "MM2 open orders": {},
            "MM2 swaps in progress": {},
            "MM2 swaps completed": {},
            "CEX open orders": {},
            "CEX swaps in progress": {},
            "CEX swaps completed": {},
            "Balance Deltas": balance_deltas,
        }})
    history.update({"Sessions":sessions})
    with open(config_path+"history/"+strategy_name+".json", 'w+') as f:
        f.write(json.dumps(history, indent=4))
    with open(config_path+"strategies/"+strategy_name+".json", 'w+') as f:
        f.write(json.dumps(strategy, indent=4))

# REVIEW 

def get_mm2_pair_orderbook(mm2_ip, mm2_rpc_pass, base, rel):
    orderbook = rpclib.orderbook(mm2_ip, mm2_rpc_pass, base, rel).json()
    asks = []
    bids = []
    orderbook_pair = {
        base+rel: {
            "asks":asks,
            "bids":bids
        }
    }
    if 'asks' in orderbook:
        for order in orderbook['asks']:
            ask = {
                "base": base,
                "rel": rel,
                "price": order['price'],
                "max_volume":order['maxvolume'],
                "age":order['age']
            }
            asks.append(ask)
    if 'bids' in orderbook:
        for order in orderbook['bids']:
            bid = {
                "base": base,
                "rel": rel,
                "price": order['price'],
                "max_volume":order['maxvolume'],
                "age":order['age']
            }
            bids.append(bid)
        orderbook_pair = {
            base+rel: {
                "asks":asks,
                "bids":bids
            }
        }
    return orderbook_pair

def get_user_addresses(mm2_ip, mm2_rpc_pass, bn_key, bn_secret):
    bn_addr = binance_api.get_binance_addresses(bn_key, bn_secret)
    mm2_addr = rpclib.all_addresses(mm2_ip, mm2_rpc_pass)
    addresses = {
        'binance': bn_addr ,
        'mm2': mm2_addr
    }
    return addresses