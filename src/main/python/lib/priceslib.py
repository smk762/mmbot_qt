#!/usr/bin/env python3
import json
import requests
from . import coinslib, guilib, binance_api

def get_forex(base=USD):
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
    url = 'ttps://api.coinpaprika.com/v1/ticker/'+coin_id
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

