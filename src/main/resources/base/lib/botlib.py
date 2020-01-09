#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from . import rpclib, priceslib, binance_api

#  LOOPS

def orderbook_loop(mm2_ip, mm2_rpc_pass, config_path):
    active_coins = mm2_active_coins(mm2_ip, mm2_rpc_pass)
    orderbook_data = []
    for base in active_coins:
        for rel in active_coins:
            if base != rel:
                orderbook_pair = get_mm2_pair_orderbook(mm2_ip, mm2_rpc_pass, base, rel)
                orderbook_data.append(orderbook_pair)
    return orderbook_data
    
def bot_loop(mm2_ip, mm2_rpc_pass, bn_key, bn_secret, balances_data, prices_data, config_path):
    print("starting bot loop")
    strategies = [ x[:-5] for x in os.listdir(config_path+'/strategies') if x.endswith("json") ]
    bot_data = "bot data placeholder"
    for strategy_name in strategies:
        with open(config_path+"history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        if history['Status'] == 'active':
            session_start = history['Sessions'][str(len(history['Sessions'])-1)]['Started']
            history['Sessions'][str(len(history['Sessions'])-1)].update({"Duration":int(time.time())-session_start})
            print("Active strategy: "+strategy_name)
            with open(config_path+"strategies/"+strategy_name+".json", 'r') as f:
                strategy = json.loads(f.read())
            history = update_session_swaps(mm2_ip, mm2_rpc_pass, bn_key, bn_secret, balances_data, strategy, history)
            history = get_binance_orders_status(bn_key, bn_secret, history)
            print("session swaps updated")
            print("update total balanace deltas")
            history = calc_total_balance_deltas(strategy, history)
            print("total deltas updated")
            # check refresh interval vs last refresh
            refresh_time = history['Last refresh'] + strategy['Refresh interval']*60
            if history['Last refresh'] == 0 or refresh_time < int(time.time()) or history['Last refresh'] < session_start:
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
                    history = cancel_session_orders(mm2_ip, mm2_rpc_pass, history)
                    # place fresh orders
                    history = submit_strategy_orders(mm2_ip, mm2_rpc_pass, config_path, strategy, history)
                    # update session history
                else:
                    print("Skipping strategy "+strategy_name+": MM2 coins not active ")
            else:
                time_left = (history['Last refresh'] + strategy['Refresh interval']*60 - int(time.time()))/60
                print("Skipping strategy "+strategy_name+": waiting for refresh interval in "+str(time_left)+" min")
            with open(config_path+"history/"+strategy_name+".json", 'w+') as f:
                 f.write(json.dumps(history, indent=4))
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
    else:
        print(balance_info)
        mm2_coin_balance_data = {
            coin: {
                    "address":'-',
                    "total":'-',
                    "locked":'-',
                    "available":'-',
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

def submit_strategy_orders(mm2_ip, mm2_rpc_pass, config_path, strategy, history):
    prices_data = priceslib.prices_loop()
    print("*** submitting strategy orders ***")
    print("Strategy: "+str(strategy))
    if strategy['Type'] == 'margin':
        history = run_margin_strategy(mm2_ip, mm2_rpc_pass, strategy, history, prices_data)
    elif strategy['Type'] == 'arbitrage':
        history = run_arb_strategy(mm2_ip, mm2_rpc_pass, config_path, strategy, history)
    return history

def run_arb_strategy(mm2_ip, mm2_rpc_pass, config_path, strategy, history):
    orderbook_data = orderbook_loop(mm2_ip, mm2_rpc_pass, config_path)
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

def get_mm2_swap_status(mm2_ip, mm2_rpc_pass, swap):
    swap_data = rpclib.my_swap_status(mm2_ip, mm2_rpc_pass, swap).json()
    for event in swap_data['result']['events']:
        if event['event']['type'] in rpclib.error_events: 
            status = 'Failed'
            break
        if event['event']['type'] == 'Finished':
            status = 'Finished'
        else:
            status = event['event']['type']
    return status, swap_data['result']

def update_session_swaps(mm2_ip, mm2_rpc_pass, bn_key, bn_secret, balances_data, strategy, history):
    for session in history['Sessions']:
        mm2_order_uuids = history['Sessions'][session]['MM2 open orders']
        for order_uuid in mm2_order_uuids:
            print("order: "+order_uuid)
            order_info = rpclib.order_status(mm2_ip, mm2_rpc_pass, order_uuid).json()
            if 'order' in order_info:
                swaps = order_info['order']['started_swaps']
                print("swaps: "+str(swaps))
                for swap in swaps:
                    if swap not in history['Sessions'][session]['MM2 swaps in progress']:
                        history['Sessions'][session]['MM2 swaps in progress'].append(swap)
            elif 'error' in order_info:
                print("order_info error: "+str(order_info))
                mm2_order_uuids.remove(order_uuid)
            else:
                print("order_info: "+str(order_info))
        swaps_in_progress = history['Sessions'][session]['MM2 swaps in progress']
        for swap in swaps_in_progress:
            swap_status = get_mm2_swap_status(mm2_ip, mm2_rpc_pass, swap)
            status = swap_status[0]
            swap_data = swap_status[1]
            print(swap+" status: "+status)
            if status == 'Finished':
                print("adding to session deltas")
                if "my_info" in swap_data:
                    print("updating session deltas history")
                    history['Sessions'][session]['MM2 swaps completed'].update({
                                                        swap:{
                                                            "Recieved coin":swap_data["my_info"]["other_coin"],
                                                            "Recieved amount":float(swap_data["my_info"]["other_amount"]),
                                                            "Sent coin":swap_data["my_info"]["my_coin"],
                                                            "Sent amount":float(swap_data["my_info"]["my_amount"]),
                                                            "Start time":swap_data["my_info"]["started_at"]
                                                        }
                                                    })
                    swaps_in_progress.remove(swap)
                    print("init cex counterswap")
                    history = start_cex_counterswap(bn_key, bn_secret, strategy, history, balances_data, session, swap)
                    print("submitted cex counterswap")
                else:
                    print(swap+" data: "+str(swap_data))
            elif status == 'Failed':
                swaps_in_progress.remove(swap)
        history['Sessions'][session]['MM2 swaps in progress'] = swaps_in_progress
        history['Sessions'][session]['MM2 open orders'] = mm2_order_uuids
    return history

def get_binance_orders_status(bn_key, bn_secret, history):
    for session in history['Sessions']:
        if "Binance" in history['Sessions'][session]["CEX open orders"]:
            for mm2_uuid in history['Sessions'][session]["CEX open orders"]["Binance"]:
                add_symbols = []
                rem_symbols = []
                for symbol in history['Sessions'][session]["CEX open orders"]["Binance"][mm2_uuid]:
                    if 'orderId' in history['Sessions'][session]["CEX open orders"]["Binance"][mm2_uuid][symbol]:
                        orderID = history['Sessions'][session]["CEX open orders"]["Binance"][mm2_uuid][symbol]['orderId']
                        resp = binance_api.get_order(bn_key, bn_secret, symbol, orderID)
                        print(resp)
                        if "status" in resp:
                            if resp['status'] == 'FILLED':
                                # move to "completed"
                                if mm2_uuid not in history['Sessions'][session]["CEX swaps completed"]["Binance"]:
                                    history['Sessions'][session]["CEX swaps completed"]["Binance"].update({mm2_uuid:{}})
                                history['Sessions'][session]["CEX swaps completed"]["Binance"][mm2_uuid].update({symbol:resp})
                                # remove from open
                                rem_symbols.append(symbol)
                            else:
                                add_symbols.append({symbol:resp})
                        else:
                            print(resp)
                for symbol_resp in add_symbols:
                    history['Sessions'][session]["CEX open orders"]["Binance"][mm2_uuid].update(symbol_resp)
                for symbol_resp in rem_symbols:
                    if symbol in history['Sessions'][session]["CEX open orders"]["Binance"][mm2_uuid]:
                        history['Sessions'][session]["CEX open orders"]["Binance"][mm2_uuid].pop(symbol)
    return history

def start_cex_counterswap(bn_key, bn_secret, strategy, history, balances_data, session_num, mm2_swap_uuid):
    mm2_swap_data = history['Sessions'][session_num]['MM2 swaps completed'][mm2_swap_uuid]
    replenish_coin = mm2_swap_data["Sent coin"]
    replenish_amount = float(mm2_swap_data["Sent amount"])
    spend_coin = mm2_swap_data["Recieved coin"]
    spend_amount = float(mm2_swap_data["Recieved amount"])
    if "Binance" in strategy["CEX countertrade list"]:
        symbols = binance_api.get_binance_countertrade_symbols(bn_key, bn_secret, balances_data["Binance"], replenish_coin, spend_coin, replenish_amount, spend_amount)
        if symbols[0] is not False:
            if symbols[0] == symbols[1]:
                history = start_direct_trade(bn_key, bn_secret, strategy, history, session_num, mm2_swap_uuid,
                                   replenish_coin, spend_coin, replenish_amount, spend_amount, symbols[0])
            else:
                history = start_indirect_trade(bn_key, bn_secret, strategy, history, session_num, mm2_swap_uuid,
                                     replenish_coin, spend_coin, replenish_amount, spend_amount, symbols[0], symbols[1])
        else:
            print("countertrade symbols not found")
    return history

def start_direct_trade(bn_key, bn_secret, strategy, history, session_num, mm2_swap_uuid,
                       replenish_coin, spend_coin, replenish_amount, spend_amount, symbol):
    margin = strategy["Margin"]
    replenish_amount = binance_api.round_to_tick(symbol, replenish_amount)
    spend_amount = binance_api.round_to_tick(symbol, spend_amount)
    if mm2_swap_uuid not in history['Sessions'][session_num]["CEX open orders"]["Binance"]:
        history['Sessions'][session_num]["CEX open orders"]["Binance"].update({mm2_swap_uuid:{}})
    if binance_api.binance_pair_info[symbol]['quoteAsset'] == replenish_coin:
        # E.g. Replenish BTC, Spend KMD
        # Spend Amount = 10000 (KMD)
        # replenish_amount = 0.777 (BTC)
        # symbol = KMDBTC
        # quoteAsset = BTC
        # Margin = 2%
        price = float(replenish_amount)/float(spend_amount)*(100+margin)/100
        price = binance_api.round_to_tick(symbol, price)
        # Sell 10000 KMD for 0.79254 BTC
        resp = binance_api.create_sell_order(bn_key, bn_secret, symbol, spend_amount, price)
        history['Sessions'][session_num]["CEX open orders"]["Binance"][mm2_swap_uuid].update({symbol: resp})
    else:
        # E.g. Replenish KMD, Spend BTC
        # replenish_amount = 10000 (KMD)
        # Spend Amount = 0.777 (BTC)
        # symbol = KMDBTC
        # quoteAsset = BTC
        # Margin = 2%
        price = float(replenish_amount)/float(spend_amount)*(100-margin)/100
        price = binance_api.round_to_tick(symbol, price)
        # Replenish 10000 KMD, spending 0.7614 BTC
        resp = binance_api.create_buy_order(bn_key, bn_secret, symbol, replenish_amount, price)
        history['Sessions'][session_num]["CEX open orders"]["Binance"][mm2_swap_uuid].update({symbol: resp})
    return history

def start_indirect_trade(bn_key, bn_secret, strategy, history, session_num, mm2_swap_uuid,
                         replenish_coin, spend_coin, replenish_amount, spend_amount, spend_symbol, replenish_symbol):

    margin = strategy["Margin"]
    mm2_trade_price = replenish_amount/spend_amount
    inverse_mm2_trade_price = spend_amount/replenish_amount

    margin_trade_buy_price = mm2_trade_price*(100-margin)/100
    margin_trade_sell_price = mm2_trade_price*(100+margin)/100

    # E.g. Spend KMD, Replenish DASH
    # replenish_amount = 1 (DASH)
    # Spend Amount = 100 (KMD)
    # replenish_symbol = DASHBTC
    # spend_symbol = KMDBTC
    # quoteAsset = BTC
    # Margin = 2%

    # i.e KMDBTC price
    spend_quote_price = float(binance_api.get_price(bn_key, spend_symbol)['price'])
    spend_quote_amount = binance_api.round_to_tick(spend_symbol, spend_amount*spend_quote_price)

    # i.e DASHBTC price
    replenish_quote_price = float(binance_api.get_price(bn_key, replenish_symbol)['price'])
    rep_quote_amount = binance_api.round_to_tick(spend_symbol, spend_amount*spend_quote_price)

    # i.e. DASHKMD price (should be close to mm2_trade price after margin applied)
    rep_spend_price = replenish_quote_price/spend_quote_price

    # i.e. KMDDASH price (should be close to inverse mm2_trade price after margin applied)
    spend_rep_price = spend_quote_price/replenish_quote_price

    if mm2_swap_uuid not in history['Sessions'][session_num]["CEX open orders"]["Binance"]:
        history['Sessions'][session_num]["CEX open orders"]["Binance"].update({mm2_swap_uuid:{}})
    while float(rep_quote_amount) > float(spend_quote_amount)*(100+margin)/100:
        replenish_quote_price = replenish_quote_price*0.999
        replenish_amount = binance_api.round_to_tick(replenish_symbol, replenish_amount)
        rep_quote_amount = spend_amount*spend_quote_price
    # Replenish spent BTC, spending DASH
    resp = binance_api.create_sell_order(bn_key, bn_secret, spend_symbol, float(spend_amount), spend_quote_price)
    history['Sessions'][session_num]["CEX open orders"]["Binance"][mm2_swap_uuid].update({spend_symbol: resp})
    # Replenish 100 KMD, spending BTC 
    resp = binance_api.create_buy_order(bn_key, bn_secret, replenish_symbol, float(replenish_amount), replenish_quote_price)
    history['Sessions'][session_num]["CEX open orders"]["Binance"][mm2_swap_uuid].update({replenish_symbol: resp})
    return history

def calc_total_balance_deltas(strategy, history):
    strategy_coins = list(set(strategy['Sell list']+strategy['Buy list']))

    total_balance_deltas = {}
    total_cex_completed_swaps = 0
    total_mm2_completed_swaps = 0

    for strategy_coin in strategy_coins:
        total_balance_deltas.update({strategy_coin:0})

    for session in history['Sessions']:
        session_balance_deltas = {}
        for strategy_coin in strategy_coins:
            session_balance_deltas.update({strategy_coin:0})

        mm2_swaps = history['Sessions'][session]['MM2 swaps completed']
        total_mm2_completed_swaps += len(mm2_swaps)

        binance_swaps = history['Sessions'][session]["CEX swaps completed"]["Binance"]
        for uuid in binance_swaps:
            for symbol in binance_swaps[uuid]:
                total_cex_completed_swaps += len(binance_swaps)
                if binance_api.binance_pair_info[symbol]['quoteAsset'] not in session_balance_deltas:
                    session_balance_deltas.update({strategy_coin:0})
                if binance_api.binance_pair_info[symbol]['quoteAsset'] not in total_balance_deltas:
                    total_balance_deltas.update({strategy_coin:0})

        for swap_uuid in mm2_swaps:
            swap_info = mm2_swaps[swap_uuid]
            swap_rec_coin = swap_info["Recieved coin"]
            swap_rec_amount = swap_info["Recieved amount"]
            swap_spent_coin = swap_info["Sent coin"]
            swap_spent_amount = swap_info["Sent amount"]

            session_balance_deltas[swap_rec_coin] += swap_rec_amount
            session_balance_deltas[swap_spent_coin] -= swap_spent_amount
            total_balance_deltas[swap_rec_coin] += swap_rec_amount
            total_balance_deltas[swap_spent_coin] -= swap_spent_amount

        for uuid in binance_swaps:
            for symbol in binance_swaps[uuid]:
                swap_info = binance_swaps[uuid][symbol]
                print(swap_info['side']+" "+swap_info['symbol'])
                if swap_info['side'] == 'BUY':
                    swap_rec_coin = binance_api.binance_pair_info[symbol]['baseAsset'] 
                    swap_spent_coin = binance_api.binance_pair_info[symbol]['quoteAsset']
                    swap_rec_amount = swap_info["executedQty"]
                    swap_spent_amount = swap_info["cummulativeQuoteQty"]
                elif swap_info['side'] == 'SELL':
                    swap_spent_coin = binance_api.binance_pair_info[symbol]['baseAsset'] 
                    swap_rec_coin = binance_api.binance_pair_info[symbol]['quoteAsset']
                    swap_spent_amount = swap_info["executedQty"]
                    swap_rec_amount = swap_info["cummulativeQuoteQty"]
                print("Rec: "+swap_rec_amount+swap_rec_coin)
                print("Sent: "+swap_spent_amount+swap_spent_coin)
                print(swap_spent_coin)
            session_balance_deltas[swap_rec_coin] += float(swap_rec_amount)
            session_balance_deltas[swap_spent_coin] -= float(swap_spent_amount)
            total_balance_deltas[swap_rec_coin] += float(swap_rec_amount)
            total_balance_deltas[swap_spent_coin] -= float(swap_spent_amount)

        history["Sessions"][session].update({"Balance Deltas": session_balance_deltas})

    history.update({
            "Total MM2 swaps completed": total_mm2_completed_swaps,
            "Total CEX swaps completed": total_cex_completed_swaps,
            "Total balance deltas": total_balance_deltas,
        })
    return history

def cancel_strategy(mm2_ip, mm2_rpc_pass, history, strategy):
    if len(history['Sessions']) > 0:
        session = history['Sessions'][str(len(history['Sessions'])-1)]
        # calc session duration
        started_at = session['Started']
        last_refresh = history["Last refresh"]
        if last_refresh - int(time.time()) > strategy["Refresh interval"]*60:
            duration = last_refresh - started_at
        else:
            duration = int(time.time()) - started_at
        session.update({"Duration":duration})
        # cancel mm2 orders
        mm2_open_orders = session["MM2 open orders"]
        for order_uuid in mm2_open_orders:
            rpclib.cancel_uuid(mm2_ip, mm2_rpc_pass, order_uuid)
        session.update({"MM2 open orders":[]})
        history['Sessions'].update({str(len(history['Sessions'])-1):session})
    return history

def cancel_session_orders(mm2_ip, mm2_rpc_pass, history):
    print("cancelling session orders")
    session = str(len(history['Sessions'])-1)
    # Cancel MM2 Orders
    mm2_order_uuids = history['Sessions'][str(len(history['Sessions'])-1)]['MM2 open orders']
    print(mm2_order_uuids)
    for order_uuid in mm2_order_uuids:
        print(order_uuid)
        order_info = rpclib.order_status(mm2_ip, mm2_rpc_pass, order_uuid).json()
        swap_in_progress = False
        if 'order' in order_info:
            swaps = order_info['order']['started_swaps']
            print(swaps)
            # updates swaps
            for swap in swaps:
                swap_status = get_mm2_swap_status(mm2_ip, mm2_rpc_pass, swap)
                status = swap_status[0]
                swap_data = swap_status[1]
                print(swap+": "+status)
                if status != 'Finished' and status != 'Failed':
                    # swap in progress
                    swap_in_progress = True
                    if swap not in history['Sessions'][session]['MM2 swaps in progress']:
                        history['Sessions'][session]['MM2 swaps in progress'].append(swap)
        else:
            print(order_info)
        if not swap_in_progress:
            rpclib.cancel_uuid(mm2_ip, mm2_rpc_pass, order_uuid)

    history['Sessions'][str(len(history['Sessions'])-1)]['MM2 open orders'] = []
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
            "MM2 open orders": [],
            "MM2 swaps in progress": [],
            "MM2 swaps completed": {},
            "CEX open orders": {
                    "Binance": {}
                },
            "CEX swaps completed": {
                    "Binance": {}
                },
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
        "Binance": bn_addr ,
        'mm2': mm2_addr
    }
    return addresses