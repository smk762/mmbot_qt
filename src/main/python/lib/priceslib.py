#!/usr/bin/env python3
import json
import time
import requests
from . import coinslib, rpclib, binance_api
from statistics import mean

def get_forex(base='USD'):
    url = 'https://api.exchangerate-api.com/v4/latest/'+base
    r = requests.get(url)
    return r

# TODO: parse https://api.coingecko.com/api/v3/coins/list for supported coins api-codes
def gecko_fiat_prices(coin_ids, fiat):
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = dict(ids=str(coin_ids),vs_currencies=fiat)
    r = requests.get(url=url, params=params)
    return r

# TODO: parse https://api.coinpaprika.com/v1/coins for supported coins api-codes
def gecko_paprika_price(coin_id):
    url = 'https://api.coinpaprika.com/v1/ticker/'+coin_id
    r = requests.get(url)
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

def get_kmd_mm2_price(node_ip, user_pass, coin):
    kmd_orders = rpclib.orderbook(node_ip, user_pass, coin, 'KMD').json()
    kmd_value = 0
    min_kmd_value = 999999999999999999
    total_kmd_value = 0
    max_kmd_value = 0
    kmd_volume = 0
    print(kmd_orders)
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
        min_kmd_value = ''
        median_kmd_value = ''
        max_kmd_value = ''
    return min_kmd_value, median_kmd_value, max_kmd_value

def get_prices_data(node_ip, user_pass, coins_list):
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
            binance_prices[binance_id] = {
                "btc":float(item['price'])
            }
    binance_ids = []
    for coin in coinslib.coin_api_codes:
        binance_id = coinslib.coin_api_codes[coin]['binance_id']
        if binance_id != '':
            binance_ids.append(binance_id)

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
            gecko_usd = float(gecko_prices[gecko_id]['usd'])
            gecko_btc = float(gecko_prices[gecko_id]['btc'])
            btc_prices.append(gecko_btc)
            usd_prices.append(gecko_usd)
        else:
            gecko_usd = ''
            gecko_btc = ''
        if paprika_id != '':
            paprika_usd = float(paprika_prices[paprika_id]['usd'])
            paprika_btc = float(paprika_prices[paprika_id]['btc'])
            btc_prices.append(paprika_btc)
            usd_prices.append(paprika_usd)
        else:
            paprika_usd = ''
            paprika_btc = ''
        if binance_id != '':
            binance_btc = float(binance_prices[binance_id]['btc'])
            btc_prices.append(binance_btc)
        else:
            binance_btc = ''
        if len(btc_prices) > 0:
            average_btc = mean(btc_prices)
            range_btc = max(btc_prices)-min(btc_prices)
        else:
            average_btc = ''
            range_btc = ''
        if len(usd_prices) > 0:
            average_usd = mean(usd_prices)
            range_usd = max(usd_prices)-min(usd_prices)
        else:
            average_usd = ''
            range_usd = ''
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
        if prices_data[coin]["average_btc"] != '':
            coin_kmd_price = prices_data[coin]["average_btc"]/kmd_btc_price
        else:
            coin_kmd_price = ''
        prices_data[coin].update({"kmd_price":coin_kmd_price})
    for coin in prices_data: 
        if coin in coins_list and prices_data[coin]["average_btc"] != '':
            if coin != 'KMD':
                mm2_kmd_price = get_kmd_mm2_price(node_ip, user_pass, coin)
                if mm2_kmd_price[1] != '':
                    prices_data[coin].update({'mm2_kmd_price':mm2_kmd_price[1]})
                    prices_data[coin].update({'mm2_btc_price':prices_data[coin]["average_btc"]/mm2_kmd_price[1]})
                    prices_data[coin].update({'mm2_usd_price':prices_data[coin]["average_usd"]/mm2_kmd_price[1]})
                else:
                    prices_data[coin].update({'mm2_kmd_price':''})
                    prices_data[coin].update({'mm2_btc_price':''})
                    prices_data[coin].update({'mm2_usd_price':''})                    
                time.sleep(0.02)
            else:
                prices_data[coin].update({'mm2_kmd_price':1})
                prices_data[coin].update({'mm2_btc_price':prices_data[coin]["average_btc"]})
                prices_data[coin].update({'mm2_usd_price':prices_data[coin]["average_usd"]})
        else:
            prices_data[coin].update({'mm2_kmd_price':''})
            prices_data[coin].update({'mm2_btc_price':''})
            prices_data[coin].update({'mm2_usd_price':''})
        sources = []
        if prices_data[coin]["paprika_btc"] != '':
            sources.append('CoinPaprika')
        if prices_data[coin]["gecko_btc"] != '':
            sources.append('CoinGecko')
        if len(sources) == 0:
            sources = ''
        prices_data[coin].update({'sources':sources})

    return prices_data

def build_prices_data(node_ip, user_pass, cointag_list=''):
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

