#!/usr/bin/env python3
import json
import time
import requests
from . import coinslib, rpclib, binance_api
from statistics import mean
import datetime

def get_forex(base='USD'):
    print("getting forex")
    url = 'https://api.exchangerate-api.com/v4/latest/'+base
    r = requests.get(url)
    return r

# TODO: parse https://api.coingecko.com/api/v3/coins/list for supported coins api-codes
def gecko_fiat_prices(coin_ids, fiat):
    print("getting gecko api prices")
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = dict(ids=str(coin_ids),vs_currencies=fiat)
    r = requests.get(url=url, params=params)
    return r

# TODO: parse https://api.coinpaprika.com/v1/coins for supported coins api-codes
def get_paprika_price(coin_id):
    print("getting paprika api prices")
    url = 'https://api.coinpaprika.com/v1/ticker/'+coin_id
    r = requests.get(url)
    return r

def get_paprika_history(coin_id, since='year_ago', quote='usd'):
    intervals = ['5m', '10m', '15m', '30m', '45m', '1h', '2h', '3h', '6h', '12h', '24h', '1d', '7d', '14d', '30d', '90d', '365d']
    quotes = ['usd', 'btc']
    now = datetime.datetime.now()
    timestamp = datetime.datetime.timestamp(now)
    if since == 'day_ago':
        timestamp = timestamp-(24*60*60)
        interval = '15m'
    elif since == 'week_ago':
        timestamp = timestamp-(7*24*60*60)
        interval = '2h'
    elif since == 'month_ago':
        timestamp = timestamp-(30*24*60*60)
        interval = '6h'
    elif since == '3_month_ago':
        timestamp = timestamp-(3*30*24*60*60)
        interval = '12h'
    elif since == '6_month_ago':
        timestamp = timestamp-(6*30*24*60*60)
        interval = '1d'
    elif since == 'year_ago':
        timestamp = timestamp-(365*24*60*60)
        interval = '1d'
    url = "https://api.coinpaprika.com/v1/tickers/"+coin_id+"/historical?start="+str(int(timestamp))+"&quote="+quote+"&interval="+interval
    print(url)
    print("getting paprika api history")
    r = requests.get(url)
    return r.json()

def get_btc_price(api_key, cointag):
    print("getting binance btc price for "+cointag)
    if cointag == 'BTC':
        return 1
    if cointag == 'BCH':
        btc_price = binance_api.get_price(api_key, 'BCHABCBTC')
    else:
        btc_price = binance_api.get_price(api_key, cointag+'BTC')
    if 'price' in btc_price:
        return float(btc_price['price'])
    else:
        return 0

def get_kmd_mm2_price(node_ip, user_pass, coin):
    try:
        print("getting kmd mm2 prices")
        kmd_orders = rpclib.orderbook(node_ip, user_pass, coin, 'KMD').json()
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
            min_kmd_value = 'No Data'
            median_kmd_value = 'No Data'
            max_kmd_value = 'No Data'
        return min_kmd_value, median_kmd_value, max_kmd_value
    except:
        min_kmd_value = 'No Data'
        median_kmd_value = 'No Data'
        max_kmd_value = 'No Data'
        return min_kmd_value, median_kmd_value, max_kmd_value

def get_prices_data(node_ip, user_pass, coins_list):
    print("getting prices data")
    binance_ids = []
    binance_prices = {}
    binance_data = requests.get("https://api.binance.com/api/v1/ticker/allPrices").json()
    for coin in coinslib.coin_api_codes:
        binance_id = coinslib.coin_api_codes[coin]['binance_id']
        if binance_id != '':
            binance_ids.append(binance_id+"BTC")
    for item in binance_data:
        if item['symbol'] in binance_ids:
            binance_id = item['symbol'][:-3]
            if binance_id == 'BTC':
                binance_prices[binance_id] = {
                    "btc":1
                }
            else:
                binance_prices[binance_id] = {
                    "btc":float(item['price'])
                }

    gecko_ids = []
    for coin in coinslib.coin_api_codes:
        gecko_id = coinslib.coin_api_codes[coin]['coingecko_id']
        if gecko_id != '':
            gecko_ids.append(gecko_id)
    gecko_prices = gecko_fiat_prices(",".join(gecko_ids), 'usd,btc').json()

    paprika_data = requests.get("https://api.coinpaprika.com/v1/tickers?quotes=USD%2CBTC").json()
    paprika_ids = []
    for coin in coinslib.coin_api_codes:
        paprika_id = coinslib.coin_api_codes[coin]['paprika_id']
        if paprika_id != '':
            paprika_ids.append(paprika_id)

    paprika_prices = {}
    for item in paprika_data:
        if item['id'] in paprika_ids:
            paprika_prices[item['id']] = {
                "usd":float(item['quotes']['USD']['price']),
                "btc":float(item['quotes']['BTC']['price'])
            }

    prices_data = {}
    for coin in coinslib.coin_api_codes:
        btc_prices = []
        usd_prices = []
        gecko_id = coinslib.coin_api_codes[coin]['coingecko_id']
        paprika_id = coinslib.coin_api_codes[coin]['paprika_id']
        binance_id = coinslib.coin_api_codes[coin]['binance_id']
        if gecko_id != '':
            try:
                gecko_usd = float(gecko_prices[gecko_id]['usd'])
                gecko_btc = float(gecko_prices[gecko_id]['btc'])
                btc_prices.append(gecko_btc)
                usd_prices.append(gecko_usd)
            except:
                gecko_usd = 'No Data'
                gecko_btc = 'No Data'
        else:
            gecko_usd = 'No Data'
            gecko_btc = 'No Data'
        if paprika_id != '':
            try:
                paprika_usd = float(paprika_prices[paprika_id]['usd'])
                paprika_btc = float(paprika_prices[paprika_id]['btc'])
                btc_prices.append(paprika_btc)
                usd_prices.append(paprika_usd)
            except:
                gecko_usd = 'No Data'
                gecko_btc = 'No Data'
        else:
            paprika_usd = 'No Data'
            paprika_btc = 'No Data'
        if binance_id != '':
            try:
                binance_btc = float(binance_prices[binance_id]['btc'])
                btc_prices.append(binance_btc)
            except:
                binance_btc = 'No Data'
        else:
            binance_btc = 'No Data'
        if len(btc_prices) > 0:
            average_btc = mean(btc_prices)
            range_btc = max(btc_prices)-min(btc_prices)
        else:
            average_btc = 'No Data'
            range_btc = 'No Data'
        if len(usd_prices) > 0:
            average_usd = mean(usd_prices)
            range_usd = max(usd_prices)-min(usd_prices)
        else:
            average_usd = 'No Data'
            range_usd = 'No Data'
        prices_data[coin] = {
            "gecko_usd":gecko_usd,
            "gecko_btc":gecko_btc,
            "paprika_usd":paprika_usd,
            "paprika_btc":paprika_btc,
            "binance_btc":binance_btc,
            "average_btc":average_btc,
            "range_btc":range_btc,
            "average_usd":average_usd,
            "range_usd":range_usd
        }
    kmd_btc_price = prices_data["KMD"]["average_btc"]
    for coin in prices_data:
        if prices_data[coin]["average_btc"] != 'No Data':
            coin_kmd_price = prices_data[coin]["average_btc"]/kmd_btc_price
        else:
            coin_kmd_price = 'No Data'
        prices_data[coin].update({"kmd_price":coin_kmd_price})
    # MM2 prices
    for coin in prices_data: 
        if coin in coins_list and prices_data[coin]["average_btc"] != 'No Data':
            if coin != 'KMD':
                mm2_kmd_price = get_kmd_mm2_price(node_ip, user_pass, coin)
                if mm2_kmd_price[1] != 'No Data':
                    prices_data[coin].update({'mm2_kmd_price':mm2_kmd_price[1]})
                    prices_data[coin].update({'mm2_btc_price':mm2_kmd_price[1]*prices_data["KMD"]["average_btc"]})
                    prices_data[coin].update({'mm2_usd_price':mm2_kmd_price[1]*prices_data["KMD"]["average_usd"]})
                else:
                    prices_data[coin].update({'mm2_kmd_price':'No Data'})
                    prices_data[coin].update({'mm2_btc_price':'No Data'})
                    prices_data[coin].update({'mm2_usd_price':'No Data'})                    
                time.sleep(0.02)
            else:
                prices_data[coin].update({'mm2_kmd_price':1})
                prices_data[coin].update({'mm2_btc_price':prices_data[coin]["average_btc"]})
                prices_data[coin].update({'mm2_usd_price':prices_data[coin]["average_usd"]})
        else:
            prices_data[coin].update({'mm2_kmd_price':'No Data'})
            prices_data[coin].update({'mm2_btc_price':'No Data'})
            prices_data[coin].update({'mm2_usd_price':'No Data'})
        sources = []
        if prices_data[coin]["binance_btc"] != 'No Data':
            sources.append('Binance')
        if prices_data[coin]["paprika_btc"] != 'No Data':
            sources.append('CoinPaprika')
        if prices_data[coin]["gecko_btc"] != 'No Data':
            sources.append('CoinGecko')
        if len(sources) == 0:
            sources = 'No Data'
        prices_data[coin].update({'sources':sources})

    return prices_data
