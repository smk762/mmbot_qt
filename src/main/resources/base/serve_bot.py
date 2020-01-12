#!/usr/bin/env python3
from typing import Optional, List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from starlette.status import HTTP_401_UNAUTHORIZED
from threading import Thread
import asyncio
import logging
#import sqlite3
import datetime
from lib import rpclib, botlib, coinslib, priceslib, validatelib, binance_api
import time
import json
import sys
import os
import uvicorn
from decimal import Decimal

# what does bot do when mm2 is down? Respawn, or exit (could leave open orders)?


## ALTERNATIVE APIS
### DEX: https://api.blocknet.co/#xbridge-api / https://github.com/blocknetdx/dxmakerbot requires syncd local nodes

# todo: detect Ctrl-C or bot exit/death, then cancel all orders. blocking thread might allow this?
# in thread, check strategies. for active strategies, last refresh time, and refresh interval. If time to refresh, refresh.

## JSON Schemas
    

'''
    path = ./strategies/{strategy_name}.json

    strategy = {
        "name": str,
        "strategy_type": str,
        "sell_list": list,
        "buy_list": list,
        "margin": float,
        "refresh_interval": int,
        "balance_pct": int,
        "cex_countertrade": list,
        "reference_api": str
    }
'''


'''
    path = ./history/{strategy_name}.json

    history = { 
        "num_sessions": dict,
        "sessions":{
            "1":{
                "started": timestamp,
                "duration": int,
                "mm2_open_orders": list,
                "mm2_swaps_in_progress": dict,
                "mm2_swaps_completed": dict,
                "cex_open_orders": dict,
                "cex_swaps_in_progress": dict,
                "cex_swaps_completed": dict,
                "balance_deltas": dict,
            }
        },
        "last_refresh": int,
        "total_mm2_swaps_completed": int,
        "total_cex_swaps_completed": int,
        "total_balance_deltas": dict,
        "status":str
    }
'''

'''
    cached in mem

    prices = {
        coingecko:{},
        coinpaprika:{},
        binance:{},
        average:{}
    }
'''
root_config_path = sys.argv[1]
config_folders = ['strategies', 'history']

bot_data = {}
mm2_orderbook_data = {}
balances_data = {
    "mm2": {},
    "Binance": {}
}
prices_data = {
    "Binance":{

    },
    "paprika":{

    },
    "gecko":{

    },
    "average":{

    }
}
addresses_data = {}

def colorize(string, color):
    colors = {
        'black':'\033[30m',
        'red':'\033[31m',
        'green':'\033[32m',
        'orange':'\033[33m',
        'blue':'\033[34m',
        'purple':'\033[35m',
        'cyan':'\033[36m',
        'lightgrey':'\033[37m',
        'darkgrey':'\033[90m',
        'lightred':'\033[91m',
        'lightgreen':'\033[92m',
        'yellow':'\033[93m',
        'lightblue':'\033[94m',
        'pink':'\033[95m',
        'lightcyan':'\033[96m',
    }
    if color not in colors:
        return str(string)
    else:
        return colors[color] + str(string) + '\033[0m'

def sec_to_hms(sec):
    hms = ''
    if sec > 3600:
        hms = str(int(sec/3600))+'h, '
        sec = sec%3600
        hms += str(int(sec/60))+'m, '
        hms += str(sec%60)+'s'
    elif sec > 60:
        hms = str(int(sec/60))+'m, '
        hms += str(sec%60)+'s'
    else:
        hms += str(sec%60)+'s'
    return hms

### THREAD Classes

class price_update_thread(object):
    def __init__(self, interval=60):
        self.interval = interval
        self.signal = True
        thread = Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        global prices_data
        while self.signal == True:
            prices_data = priceslib.prices_loop()
            time.sleep(self.interval)

class bot_update_thread(object):
    def __init__(self, interval=30):
        self.interval = interval
        self.signal = True
        thread = Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        global bot_data
        while self.signal == True:
            bot_data = botlib.bot_loop(mm2_ip, mm2_rpc_pass, bn_key, bn_secret, balances_data, prices_data, config_path)
            time.sleep(self.interval)

class orderbook_update_thread(object):
    def __init__(self, interval=10):
        self.interval = interval
        self.signal = True
        thread = Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        global mm2_orderbook_data
        while self.signal == True:
            mm2_orderbook_data = botlib.orderbook_loop(mm2_ip, mm2_rpc_pass, config_path)
            time.sleep(self.interval)

class bn_balances_update_thread(object):
    def __init__(self, interval=10):
        self.interval = interval
        self.signal = True
        thread = Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        global balances_data
        while self.signal == True:
            bn_balances_data = botlib.bn_balances_loop(bn_key, bn_secret)
            balances_data["Binance"].update(bn_balances_data)
            time.sleep(self.interval)

class mm2_balances_update_thread(object):
    def __init__(self, interval=10):
        self.interval = interval
        self.signal = True
        thread = Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        global balances_data
        while self.signal == True:
            active_coins = rpclib.check_active_coins(mm2_ip, mm2_rpc_pass)
            for coin in active_coins:
                mm2_coin_balance_data = botlib.mm2_balances_loop(mm2_ip, mm2_rpc_pass, coin)
                balances_data["mm2"].update(mm2_coin_balance_data)
            time.sleep(self.interval)

class addresses_thread(object):
    def __init__(self):
        self.signal = True       
        thread = Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        global addresses_data
        while self.signal == True:
            addresses_data = botlib.get_user_addresses(mm2_ip, mm2_rpc_pass, bn_key, bn_secret)


### API CALLS

# TODO: add https://documenter.getpostman.com/view/8180765/SVfTPnM8?version=latest#intro

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Welcome to Antara Markerbot API. See /docs for all methods"}

@app.get("/api_version")
async def api_version():
    return {"version": "0.0.1"}

# Get creds from app
@app.post("/set_creds")
async def set_creds(ip: str, rpc_pass: str, key: str, secret: str, username: str):
    global mm2_ip
    global mm2_rpc_pass
    global bn_key
    global bn_secret
    global config_path
    mm2_ip = 'http://'+ip+':7783'
    mm2_rpc_pass = rpc_pass
    bn_key = key
    bn_secret = secret
    config_path = root_config_path+username+"/"
    for folder in config_folders:
        if not os.path.exists(config_path+folder):
            os.makedirs(config_path+folder)
    json_files = [ x for x in os.listdir(config_path+'history') if x.endswith("json") ]
    for json_file in json_files:
        with open(config_path+"history/"+json_file, 'r') as hist:
            history = json.loads(hist.read())
        if history['Status'] == 'active':
            history.update({'Status':"inactive"})
        with open(config_path+"history/"+json_file, 'w+') as f:
            f.write(json.dumps(history, indent=4))
    if 'mm2_balance_thread' in globals():
        bn_balance_thread.signal = False
    if 'bn_balance_thread' in globals():
        bn_balance_thread.signal = False
    if 'prices_thread' in globals():
        prices_thread.signal = False
    if 'orderbook_thread' in globals():
        orderbook_thread.signal = False
    if 'bot_thread' in globals():
        bot_thread.signal = False
    mm2_balance_thread = mm2_balances_update_thread()
    bn_balance_thread = bn_balances_update_thread()
    orderbook_thread = orderbook_update_thread()
    prices_thread = price_update_thread()
    bot_thread = bot_update_thread()        

@app.post("/logout")
async def logout():
    pass

# TABLE FORMATTED 

@app.get("/table/mm2_open_orders")
async def mm2_open_orders_table():
    strat_open_orders = {}
    table_data = []
    json_files = [ x for x in os.listdir(config_path+'history') if x.endswith("json") ]
    for json_file in json_files:
        with open(config_path+"history/"+json_file, 'r') as hist:
            history = json.loads(hist.read())
            if len(history['Sessions']) > 0:
                strat_open_orders[json_file[:-5]] = history['Sessions'][str(len(history['Sessions'])-1)]["MM2 open orders"]

    orders = rpclib.my_orders(mm2_ip, mm2_rpc_pass).json()
    if 'error' in orders:
        return orders
    if 'maker_orders' in orders['result']:
        maker_orders = orders['result']['maker_orders']
    if 'taker_orders' in orders['result']:
        taker_orders = orders['result']['taker_orders']
    if len(maker_orders)+len(taker_orders) == 0:
        resp = {
            "response": "success",
            "message":"No open orders!",
            "table_data": table_data
        }
    else:
        for item in maker_orders:
            for strategy in strat_open_orders:
                if item in strat_open_orders[strategy]:
                    strat = strategy
                else: strat = '-'
            role = "Maker"
            base = maker_orders[item]['base']
            base_amount = round(float(maker_orders[item]['available_amount']),8)
            rel = maker_orders[item]['rel']
            rel_amount = round(float(maker_orders[item]['price'])*float(maker_orders[item]['available_amount']),8)
            sell_price = round(float(maker_orders[item]['price']),8)
            buy_price = round(float(1/float(sell_price)),8)
            timestamp = int(maker_orders[item]['created_at']/1000)
            created_at = datetime.datetime.fromtimestamp(timestamp)
            num_matches = len(maker_orders[item]['matches'])
            started_swaps = len(maker_orders[item]['started_swaps'])
            table_data.append({
                    "Strategy":strat,
                    "Role":role,
                    "Buy Coin":rel,
                    "Buy Volume":rel_amount,
                    "Buy Price":sell_price,
                    "Sell Coin":base,
                    "Sell Volume":base_amount,
                    "Sell Price":buy_price,
                    "Order UUID":item,
                    "Created At":created_at,
                    "Num Matches":num_matches,
                    "Started Swaps":started_swaps,
                })
        for item in taker_orders:
            for strategy in strat_open_orders:
                if item in strat_open_orders[strategy]:
                    strat = strategy
                else: strat = '-'
            role = "Taker"
            timestamp = int(taker_orders[item]['created_at']/1000)
            created_at = datetime.datetime.fromtimestamp(timestamp)
            base = taker_orders[item]['request']['base']
            rel = taker_orders[item]['request']['rel']
            base_amount = round(float(taker_orders[item]['request']['base_amount']),8)
            rel_amount = round(float(taker_orders[item]['request']['rel_amount']),8)
            buy_price = round(float(taker_orders[item]['request']['rel_amount'])/float(taker_orders[item]['request']['base_amount']),8)
            sell_price = round(float(1/float(buy_price)),8)
            table_data.append({
                    "Strategy":strat,
                    "Role":role,
                    "Buy Coin":base,
                    "Buy Volume":base_amount,
                    "Buy Price":buy_price,
                    "Sell Coin":rel,
                    "Sell Volume":rel_amount,
                    "Sell Price":sell_price,
                    "Order UUID":item,
                    "Created At":created_at,
                    "Num Matches":"-",
                    "Started Swaps":"-",
                })
        resp = {
            "response": "success",
            "message": "Open orders table data found.",
            "table_data": table_data
        }
    return resp

@app.get("/table/mm2_orderbook/{base}/{rel}")
async def mm2_orderbook_pair_table(base, rel):
    pair_book = rpclib.orderbook(mm2_ip, mm2_rpc_pass, base, rel).json()
    if 'error' in pair_book:
        return pair_book
    elif len(pair_book['asks']) > 0:
        table_data = []
        for item in pair_book['asks']:
            basevolume = round(float(item['maxvolume']), 8)
            relprice = round(float(item['price']), 8)
            order_value = round(float(item['price'])*float(item['maxvolume']), 8)
            try:
                api_price = prices_data['average'][base]['BTC']/prices_data['average'][rel]['BTC']
            except:
                api_price = '-'
            table_data.append({
                    "Buy Coin":base,
                    "Sell Coin":rel,
                    base+" Volume":basevolume,
                    rel+" Price per "+base:relprice,
                    "API Average Price":api_price,
                    "Order Value in "+rel:order_value,
                    "Age":item['age'],
                    "Pubkey":item['pubkey'],
                })
        resp = {
            "response": "success",
            "message": "Orderbook table data found.",
            "table_data": table_data
        }
        return resp

    else:
        resp = {
            "response": "success",
            "message":"No "+base+"/"+rel+" orders in orderbook",
            "table_data": []
        }
        return resp

@app.get("/table/binance_open_orders")
async def binance_open_orders():
    table_data = []
    open_orders = binance_api.get_open_orders(bn_key, bn_secret)
    for item in open_orders:
        print(item)
        if 'orderId' in item:
            order_id = item['orderId']
            side = item['side']
            symbol = item['symbol']
            price = item['price']
            qty = item['origQty']
            filled = item['executedQty']
            time = datetime.datetime.fromtimestamp(int(item['time']/1000))
            table_data.append({
                    "Order ID": order_id,
                    "Side": side,
                    "Pair": symbol,
                    "Price":price,
                    "Qty":qty,
                    "Filled":filled,
                    "Time":time
                })
    return {"table_data":table_data}

@app.get("/table/get_binance_depth/{symbol}")
async def get_binance_depth(symbol):
    table_data = []
    depth = binance_api.get_depth(bn_key, symbol, 20)
    for item in depth['bids']:
        price = float(item[0])
        volume = float(item[1])
        table_data.append({
                "Pair": symbol,
                "Price": "{:.8f}".format(price),
                "Volume": volume,
                "Bid/Ask":'Bid'
            })
    for item in depth['asks']:
        price = float(item[0])
        volume = float(item[1])
        table_data.append({
                "Pair": symbol,
                "Price": "{:.8f}".format(price),
                "Volume": volume,
                "Bid/Ask":'Ask'
            })
    return {"table_data":table_data}

@app.get("/table/mm2_history")
async def mm2_history_table():
    table_data = []
    swaps_info = rpclib.my_recent_swaps(mm2_ip, mm2_rpc_pass, limit=9999, from_uuid='').json()
    if 'result' in swaps_info:
        for swap in swaps_info['result']['swaps']:
            trade_addr = ''
            for event in swap['events']:
                event_type = event['event']['type']
                if event_type in rpclib.error_events:
                    event_type = 'Failed'
                    break
                if swap['type'] == 'Taker':
                    if event_type == 'MakerPaymentReceived':
                        trade_addr = event['event']['data']['from'][0]
                elif swap['type'] == 'Maker':
                    if event_type == 'TakerFeeValidated':
                        trade_addr = event['event']['data']['from'][0]
            status = event_type
            role = swap['type']
            uuid = swap['uuid']
            my_amount = round(float(swap['my_info']['my_amount']),8)
            my_coin = swap['my_info']['my_coin']
            other_amount = round(float(swap['my_info']['other_amount']),8)
            other_coin = swap['my_info']['other_coin']
            started_at = datetime.datetime.fromtimestamp(round(swap['my_info']['started_at']/1000)*1000)
            if swap['type'] == 'Taker':
                buy_price = round(float(swap['my_info']['my_amount'])/float(swap['my_info']['other_amount']),8)
                sell_price = '-'
            else:
                buy_price = '-'
                sell_price = round(float(swap['my_info']['other_amount'])/float(swap['my_info']['my_amount']),8)
            table_data.append({
                    "Start Time":started_at,
                    "Role":role,
                    "Status":status,
                    "Buy Coin":other_coin,
                    "Buy Amount":other_amount,
                    "Buy Price":buy_price,
                    "Sell Coin":my_coin,
                    "Sell Amount":my_amount,
                    "Sell Price":sell_price,
                    "Trade Address":trade_addr,
                    "UUID":uuid
                })
    return {"table_data":table_data}

@app.get("/table/strategies_history")
async def strategies_history_table():
    table_data = []
    json_files = [ x for x in os.listdir(config_path+'history') if x.endswith("json") ]
    for json_file in json_files:
        with open(config_path+"history/"+json_file, 'r') as hist:
            history = json.loads(hist.read())
        for session in history['Sessions']:
            for uuid in history['Sessions'][session]['MM2 swaps completed']:
                swap_info = history['Sessions'][session]['MM2 swaps completed'][uuid]
                table_data.append({
                        "Start Time": datetime.datetime.fromtimestamp(round(swap_info["Start time"]/1000)*1000),
                        "API":"MM2",
                        "Buy Coin":swap_info["Recieved coin"],
                        "Buy Amount":swap_info["Recieved amount"],
                        "Sell Coin":swap_info["Sent amount"],
                        "Sell Amount":swap_info["Sent amount"],
                        "MM2 UUID":uuid,
                        "Binance OrderID":"-",
                        "Status": "Complete"
                    })
                for symbol in history['Sessions'][session]['CEX open orders']['Binance'][uuid]:
                    order_info = history['Sessions'][session]['CEX open orders']['Binance'][uuid][symbol]
                    if 'side' in order_info:
                        if order_info['side'] == 'BUY':
                            swap_rec_coin = binance_api.binance_pair_info[symbol]['baseAsset']
                            swap_spent_coin = binance_api.binance_pair_info[symbol]['quoteAsset']
                            swap_rec_amount = order_info["origQty"]
                            if float(order_info["origQty"])*float(order_info["price"]) != 0:
                                swap_spent_amount = "{:.10f}".format(round(float(order_info["origQty"])*float(order_info["price"]),10))
                            else:
                                swap_rec_amount = 0
                        elif order_info['side'] == 'SELL':
                            swap_spent_coin = binance_api.binance_pair_info[symbol]['baseAsset']
                            swap_rec_coin = binance_api.binance_pair_info[symbol]['quoteAsset']
                            swap_spent_amount = order_info["origQty"]
                            if float(order_info["origQty"])*float(order_info["price"]) != 0:
                                swap_rec_amount = "{:.10f}".format(round(float(order_info["origQty"])*float(order_info["price"]),10))
                            else:
                                swap_rec_amount = 0
                        table_data.append({
                                "Start Time": datetime.datetime.fromtimestamp(round(order_info["time"]/1000)),
                                "API":"Binance",
                                "Buy Coin":swap_rec_coin,
                                "Buy Amount":swap_rec_amount,
                                "Sell Coin":swap_spent_coin,
                                "Sell Amount":swap_spent_amount,
                                "MM2 UUID":uuid,
                                "Binance OrderID":order_info["orderId"],
                                "Status": "Incomplete"
                            })
                    else:
                        print("Error with Binance Order: "+str(order_info))
                for symbol in history['Sessions'][session]['CEX swaps completed']['Binance'][uuid]:
                    order_info = history['Sessions'][session]['CEX swaps completed']['Binance'][uuid][symbol]
                    if order_info['side'] == 'BUY':
                        swap_rec_coin = binance_api.binance_pair_info[symbol]['baseAsset']
                        swap_spent_coin = binance_api.binance_pair_info[symbol]['quoteAsset']
                        swap_rec_amount = order_info["executedQty"]
                        swap_spent_amount = order_info["cummulativeQuoteQty"]
                    elif order_info['side'] == 'SELL':
                        swap_spent_coin = binance_api.binance_pair_info[symbol]['baseAsset']
                        swap_rec_coin = binance_api.binance_pair_info[symbol]['quoteAsset']
                        swap_spent_amount = order_info["executedQty"]
                        swap_rec_amount = order_info["cummulativeQuoteQty"]
                    table_data.append({
                            "Start Time": datetime.datetime.fromtimestamp(round(order_info["time"]/1000)),
                            "API":"Binance",
                            "Buy Coin":swap_rec_coin,
                            "Buy Amount":swap_rec_amount,
                            "Sell Coin":swap_spent_coin,
                            "Sell Amount":swap_spent_amount,
                            "MM2 UUID":uuid,
                            "Binance OrderID":order_info["orderId"],
                            "Status": "Complete"
                        })
    return {"table_data":table_data}

@app.get("/table/bot_strategies")
async def bot_strategies():
    json_files = [ x for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    strategies = []
    for json_file in json_files:
        with open(config_path+'strategies/'+json_file) as strat:
            strategy = json.loads(strat.read())
            with open(config_path+"history/"+json_file, 'r') as hist:
                history = json.loads(hist.read())
            if history['Status'] != 'archived':
                strategy.update({
                        "Sessions":len(history['Sessions']),
                        "Last refresh":datetime.datetime.fromtimestamp(history['Last refresh']),
                        "Status":history['Status']
                    })
                active_coins = botlib.mm2_active_coins(mm2_ip, mm2_rpc_pass)
                strategy_coins = list(set(strategy['Sell list']+strategy['Buy list']))
                for coin in strategy_coins:
                    if coin not in active_coins:
                        strategy.update({"Status":"MM2 coin not activated - ["+coin+"]"})
                        break
                strategies.append(strategy)
    return {"table_data":strategies}

@app.get("/table/bot_strategy/summary/{strategy_name}")
async def bot_strategy_summary(strategy_name):
    strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    if len(strategies) == 0:
        resp = {
            "response": "error",
            "message": "No strategies found!",
            "table_data": []
        }
    elif strategy_name not in strategies:
        resp = {
            "response": "error",
            "message": "Strategy '"+strategy_name+"' not found!",
            "table_data": []
        }
    else:
        table_data = []
        with open(config_path+"/history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        i = 0
        total_duration = 0
        for session in history['Sessions']:
            duration = history['Sessions'][session]['Duration']
            started = int(history['Sessions'][session]['Started'])
            started_at = datetime.datetime.fromtimestamp(started)
            total_duration += duration
            cex_unfinished = history['Sessions'][session]["Session CEX swaps unfinished"]
            cex_completed = history['Sessions'][session]["Session CEX swaps completed"]
            session_data = {
                "Name":strategy_name,
                "Session":i,
                "Started":started_at,
                "Duration":sec_to_hms(duration),
                "MM2 swaps":history['Sessions'][session]["Session MM2 swaps completed"],
                "CEX swaps":str(cex_completed)+"/"+str(cex_unfinished+cex_completed)
            }
            delta_coins = list(history['Sessions'][session]['Balance Deltas'].keys())
            delta_coins.sort()
            for coin in delta_coins:
                if float(history['Sessions'][session]['Balance Deltas'][coin]) != 0:
                    session_data.update({coin:"{:.10f}".format(round(float(history['Sessions'][session]['Balance Deltas'][coin]),10))})
                else:
                    session_data.update({coin:0})
            cex_err = []
            for uuid in history['Sessions'][session]["CEX open orders"]["Binance"]:
                for symbol in history['Sessions'][session]["CEX open orders"]["Binance"][uuid]:
                    if 'orderId' not in history['Sessions'][session]["CEX open orders"]["Binance"][uuid][symbol]:
                        cex_err.append(history['Sessions'][session]["CEX open orders"]["Binance"][uuid][symbol]['error'])
            session_data.update({"CEX errors":cex_err})
            table_data.append(session_data)
            i += 1
        total_cex_completed = history['Total CEX swaps completed']
        total_cex_unfinished = history['Total CEX swaps unfinished']
        total_data = {
            "Name":strategy_name,
            "Session":"Total",
            "Started":'-',
            "Duration":sec_to_hms(total_duration),
            "MM2 swaps":history['Total MM2 swaps completed'],
            "CEX swaps":str(total_cex_completed)+"/"+str(total_cex_completed+total_cex_unfinished),
            
        }
        delta_coins = list(history['Total balance deltas'].keys())
        delta_coins.sort()
        for coin in delta_coins:
            if float(history['Total balance deltas'][coin]) != 0:
                total_data.update({coin:"{:.10f}".format(round(float(history['Total balance deltas'][coin]),10))})
            else:
                total_data.update({coin:0})
        total_data.update({"CEX errors":"-"})
        table_data.append(total_data)
        resp = {
            "response": "success",
            "message": "History found for strategy: "+strategy_name,
            "table_data": table_data
        }
    return resp

# CACHED DATA

@app.get("/all_balances")
async def all_balances():
    return balances_data

@app.get("/all_prices")
async def all_prices():
    return prices_data

@app.get("/prices/{coin}")
async def coin_prices(coin):
    coin = coin.upper()
    if coin == 'ALL':
        resp = {
            "response": "success",
            "message": coin+" price data found",
            "price_data": prices_data,
        }
    elif coin in prices_data['average']:
        coin_price_data = {
            "Binance":{coin:prices_data["Binance"][coin]},
            "paprika":{coin:prices_data['paprika'][coin]},
            "gecko":{coin:prices_data['gecko'][coin]},
            "average":{coin:prices_data['average'][coin]}
        }
        resp = {
            "response": "success",
            "message": coin+" price data found",
            "price_data": coin_price_data,
        }
    else:
        resp = {
            "response": "error",
            "message": coin+" price data not found!"
        }        
    return resp

@app.get("/all_addresses")
async def all_addresses():
    return addresses_data

@app.get("/mm2_balance/{coin}")
async def mm2_balance(coin):
    resp = rpclib.my_balance(mm2_ip, mm2_rpc_pass, coin).json()
    return resp

@app.get("/coins/list")
async def list_coins():
    resp = {
        "response": "success",
        "message": "Coins list found",
        "coins_list": coinslib.cointags
    }
    return resp

@app.get("/cex/list")
async def list_cex():
    resp = {
        "response": "success",
        "message": "Cex list found",
        "cex_list": coinslib.cex_names
    }
    return resp

@app.get("/mm2_orderbook")
async def show_mm2_orderbook():
    resp = {
        "response": "success",
        "orderbook": mm2_orderbook_data
    }        
    return resp

# STRATEGIES

@app.post("/strategies/create")
async def create_strategy(*, name: str, strategy_type: str, sell_list: str, 
                          buy_list: str, margin: float = 5, refresh_interval: int = 30,
                          balance_pct: int = 100, cex_list: str = "Binance"):
    """
    Creates a new trading strategy definition.
    - **name**: Each strategy must have a name. E.g. KMD
    - **strategy_type**: A valid strategy name. E.g. Margin
    - **sell_list**: a comma delimited list of tickers. E.g. KMD,BTC,ETH
    - **buy_list**: a comma delimited list of tickers. E.g. KMD,BTC,ETH
    - **margin** (float): percentage to set sell orders above market (margin), or buy orders below market (arbitrage). E.g. 5 
    - **refresh_interval** (integer): time in minutes between refreshing prices and updating orders.
    - **balance_pct** (integer): percentage of available balance to use for trades. E.g. 100
    - **buy_list**: a comma delimited list of centralised exchanges. E.g. Binance,Coinbase

    """
    valid_strategies = ['margin', 'arbitrage']
    if name == 'all':
        resp = {
            "response": "error",
            "message": "Strategy name 'all' is reserved, use a different name.",
        }
    elif strategy_type in valid_strategies:
        sell_list = sell_list.upper().split(',')
        buy_list = buy_list.upper().split(',')
        cex_list = cex_list.title().split(',')
        valid_coins = validatelib.validate_coins(list(set(sell_list+buy_list)))
        valid_cex = validatelib.validate_cex(list(set(cex_list)))
        if not valid_coins[0]:
            resp = {
                "response": "error",
                "message": "'"+valid_coins[1]+"' is an invalid ticker. Check /coins/list for valid options, and enter them as comma delimiter with no spaces."
            }
            return resp
        if not valid_cex[0]:
            resp = {
                "response": "error",
                "message": "'"+valid_cex[1]+"' is an invalid CEX. Check /cex/list for valid options, and enter them as comma delimiter with no spaces."
            }
            return resp

        strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
        if name in strategies:
            resp = {
                "response": "error",
                "message": "Strategy '"+name+"' already exists - if not in table, it may be archived. Try another name."
            }
            return resp
        else:
            strategy = botlib.init_strategy(name, strategy_type, sell_list, buy_list, margin, refresh_interval, balance_pct, cex_list, config_path)

            resp = {
                "response": "success",
                "message": "Strategy '"+name+"' created",
                "parameters": strategy
            }
    else:
        resp = {
            "response": "error",
            "message": "Strategy type '"+strategy_type+"' is invalid. Options are: "+str(valid_strategies),
            "valid_strategies": {
                "margin": "This strategy will place setprice (sell) orders on mm2 at market price plus margin. On completion of a swap, if Binance keys are valid, a countertrade will be performed at market.",
                "arbitrage": "This strategy scans the mm2 orderbook periodically. If a trade below market price minus margin is detected, a buy order is submitted. On completion of a swap, if Binance keys are valid, a counter sell will be submitted."
            }
        }
    return resp

@app.get("/strategies/active")
async def active_strategies():
    json_files = [ x for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    count = 0
    strategies = []
    for json_file in json_files:
        with open(config_path+'history/'+json_file) as j:
            history = json.loads(j.read())
        if history["status"] == 'active':
            with open(config_path+'strategies/'+json_file) as j:
                strategy = json.loads(j.read())
            count += 1
            strategies.append(strategy)
    resp = {
        "response": "success",
        "message": str(count)+" strategies active",
        "active_strategies": strategies
    }
    return resp


@app.post("/strategies/session/{strategy_name}/{session_num}")
async def strategy_session(strategy_name, session_num):
    strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    if len(strategies) == 0:
        resp = {
            "response": "error",
            "message": "No strategies found!"
        }
    elif strategy_name not in strategies:
        resp = {
            "response": "error",
            "message": "Strategy '"+strategy_name+"' not found!"
        }
    else:
        with open(config_path+"/history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        if session_num in history['Sessions']:
            session = history['Sessions'][session_num]
            resp = {
                "response": "success",
                "message": "History found for strategy: "+strategy_name,
                "history": session
            }
        else:
            resp = {
                "response": "error",
                "message": "Session history "+str(session_num)+" not found for strategy: "+strategy_name
            }            
    return resp


@app.post("/strategies/history/{strategy_name}")
async def strategy_history(strategy_name):
    strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    if len(strategies) == 0:
        resp = {
            "response": "error",
            "message": "No strategies found!"
        }
    elif strategy_name == 'all':
        histories = []
        for strategy in strategies:
            with open(config_path+"/history/"+strategy+".json", 'r') as f:
                history = json.loads(f.read())
            histories.append(history)
        resp = {
            "response": "success",
            "message": str(len(strategies))+" sessions found!",
            "histories": histories
        }
    elif strategy_name not in strategies:
        resp = {
            "response": "error",
            "message": "Strategy '"+strategy_name+"' not found!"
        }
    else:
        with open(config_path+"/history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        resp = {
            "response": "success",
            "message": "History found for strategy: "+strategy_name,
            "history": history
        }
    return resp

@app.post("/strategies/start/{strategy_name}")
async def start_strategy(strategy_name):
    strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    if strategy_name in strategies:
        with open(config_path+"/strategies/"+strategy_name+".json", 'r') as f:
            strategy = json.loads(f.read())
        with open(config_path+"/history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        if strategy['Type'] == "margin":
            botlib.init_session(strategy_name, strategy, history, config_path)
            resp = {
                "response": "success",
                "message": "Strategy '"+strategy['Name']+"' started!",
            }
        elif strategy['Type'] == "arbitrage":
            botlib.init_session(strategy_name, strategy, history, config_path)
            resp = {
                "response": "success",
                "message": "Strategy '"+strategy['Name']+"' started",
            }
        else:
            resp = {
                "response": "error",
                "message": "Strategy type '"+strategy['Type']+"' not recognised!"
            }
    else:
        resp = {
            "response": "error",
            "message": "Strategy '"+strategy_name+"' not found!"
        }
    return resp

@app.post("/strategies/stop/{strategy_name}")
async def stop_strategy(strategy_name):
    strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    if strategy_name == 'all':
        histories = []
        for strategy in strategies:
            with open(config_path+"/history/"+strategy+".json", 'r') as f:
                history = json.loads(f.read())
            with open(config_path+"/strategies/"+strategy+".json", 'r') as f:
                strat = json.loads(f.read())
            if history['Status'] == 'active':
                history.update({"Status":"inactive"})
                history = botlib.cancel_strategy(mm2_ip, mm2_rpc_pass, history, strat)
                with open(config_path+"/history/"+strategy+".json", 'w+') as f:
                    f.write(json.dumps(history, indent=4))
                histories.append(history)
        resp = {
            "response": "success",
            "message": "All active strategies stopped!",
            "status": histories
        }
    elif strategy_name not in strategies:
        resp = {
            "response": "error",
            "message": "Strategy '"+strategy_name+"' not found!"
        }
    else:
        with open(config_path+"/history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        history.update({"Status":"inactive"})
        with open(config_path+"/history/"+strategy_name+".json", 'w+') as f:
            f.write(json.dumps(history, indent=4))
        # get current order uuids
        history = botlib.cancel_session_orders(mm2_ip, mm2_rpc_pass, history)
        resp = {
            "response": "success",
            "message": "Strategy '"+strategy_name+"' stopped",
            "status": history
        }
    return resp

@app.post("/strategies/delete/{strategy_name}")
async def delete_strategy(strategy_name):
    strategies = [ x[:-5] for x in os.listdir(config_path+'strategies') if x.endswith("json") ]
    if strategy_name in strategies:
        with open(config_path+"/strategies/"+strategy_name+".json", 'r') as f:
            strategy = json.loads(f.read())
        with open(config_path+"/history/"+strategy_name+".json", 'r') as f:
            history = json.loads(f.read())
        history.update({"Status":"archived"})
        history = botlib.cancel_strategy(mm2_ip, mm2_rpc_pass, history, strategy)
        with open(config_path+"/history/"+strategy_name+".json", 'w+') as f:
            f.write(json.dumps(history, indent=4))
        resp = {
            "response": "success",
            "message": "Strategy '"+strategy_name+"' archived"
        }
    else:
        resp = {
            "response": "error",
            "message": "Strategy '"+strategy_name+"' not found!"
        }
    return resp


# REVIEW

@app.post("/binance_prices/{base}/{rel}")
async def binance_prices(base, rel):
    base = base.upper()
    rel = rel.upper()
    prices = priceslib.get_binance_price(base, rel, prices_data)
    resp = {
        "response": "success",
        "message": base+"/"+rel+" price data found",
        "binance_prices": prices
    }
    return prices


def main():
   # bot_thread = threading.Thread(target=bot_loop, args=())
   # prices_thread = threading.Thread(target=prices_loop, args=())
   pass

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''
method: start_trade strategy: marketmaking``margin: 10 tickers_base: [BTC, KMD] tickers_rel: [VRSC]
method: get_trading_status -> result: success list_of_strategies_working: [1,2,3]


stop_strategy strategy_id -> result
started_strategies_list -> list_with_ids 
history_strategies_list -> displaying `active` and `history` (stopped) of strategies
strategy_info strategy_id -> info with params and some events maybe (at least amount of events)
strategy_events strategy_id <depth> -> displaying events (trades/transfers and etc) for strategy with optional depth (amount of last events to show) argument
'''

# strategies examples - https://github.com/CoinAlpha/hummingbot/tree/master/documentation/docs/strategies

## API methods

# start_trading(sell_list, buy_list, margin, refresh_interval=30 (optional, minutes), balance_pct=100 (optional, default 100), cex_countertrade=None (optional, cex_name or None).
# if cex not None, check if cex_auth is ok.
# if refresh interval expires while swap in progress, wait before cancel.
# monitor trade status periodically, emit on updates. 
# emits bot history json - see mmbot_qt for format. if json contains initiated swaps, after finish/ order cancel, store locally on client.

# get_strategy_status(strategy_id, verbose=False)
# forces update and emit of bot history json for id. Return enough to get more info from mm2 if verbose=True.

# get_completed_trades_history(limit=10, from='', verbose=False)
# returns bot history json for last "limit" trades. Augment via mm2 for more data if verbose=True

# show_strategy(strategy_id)
# returns strategy_input_params, pending_trade_ids, completed_trade_ids, aggregated_balance_deltas

# stop_trading(strategy_id, force=False)
# check for in progress cex/mm2 trades. Cancel if None. If not None, schedule for cancel once in progress tradess complete.
# If force is true, cancel regardless.

# get_active_strategies()
# show list of strategies currently in progress.

# arbitrage(cex_list, coin_pair, min_profit_pct)
# for a given coin_pair (e.g. KMDBTC), monitor all cex on the list, and mm2 for prices. If price differential between exchanges exceeds min_profit_pct, execute matching trades to take advantage.
