# Input coins you want to trade here. 
# reserve_balance: excess funds will be sent to your Binance wallet
# premium: value relative to binance market rate to setprices as marketmaker.
# min/max/stepsize need to be set from values from 
# https://api.binance.com/api/v1/exchangeInfo

coin_api_codes = {
   'AXE':{
      'coingecko_id':'axe',
      'binance_id':'',
      'paprika_id':'axe-axe',
      'name':'Axe'
   },
   'AWC':{
      'coingecko_id':'atomic-wallet-coin',
      'binance_id':'',
      'paprika_id':'awc-atomic-wallet-coin',
      'name':'Atomic Wallet Coin'
   },
   'BAT':{
      'coingecko_id':'basic-attention-token',
      'binance_id':'BAT',
      'paprika_id':'bat-basic-attention-token',
      'name':'Basic Attention Token'
   },
   'BCH':{
      'coingecko_id':'bitcoin-cash',
      'binance_id':'BCH',
      'paprika_id':'bch-bitcoin-cash',
      'name':'Bitcoin Cash'
   },
   'BOTS':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'BOTS'
   },
   'BTC':{
      'coingecko_id':'bitcoin',
      'binance_id':'BTC',
      'paprika_id':'btc-bitcoin',
      'name':'Bitcoin'
   },
   'BTCH':{
      'coingecko_id':'bitcoin-hush',
      'binance_id':'',
      'paprika_id':'',
      'name':'Bitcoin Hush'
   },
   'CHIPS':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'CHIPS'
   },
   'COQUI':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'COQUI'
   },
   'CRYPTO':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'CRYPTO'
   },
   'DAI':{
      'coingecko_id':'dai',
      'binance_id':'',
      'paprika_id':'dai-dai',
      'name':'Dai'
   },
   'DASH':{
      'coingecko_id':'dash',
      'binance_id':'DASH',
      'paprika_id':'dash-dash',
      'name':'Dash'
   },
   'DEX':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'DEX'
   },
   'DGB':{
      'coingecko_id':'digibyte',
      'binance_id':'',
      'paprika_id':'dgb-digibyte',
      'name':'DigiByte'
   },
   'DOGE':{
      'coingecko_id':'dogecoin',
      'binance_id':'DOGE',
      'paprika_id':'doge-dogecoin',
      'name':'Dogecoin'
   },
   'ETH':{
      'coingecko_id':'ethereum',
      'binance_id':'ETH',
      'paprika_id':'eth-ethereum',
      'name':'Ethereum'
   },
   'HUSH':{
      'coingecko_id':'hush',
      'binance_id':'',
      'paprika_id':'hush-hush',
      'name':'Hush'
   },
   'KMD':{
      'coingecko_id':'komodo',
      'binance_id':'KMD',
      'paprika_id':'kmd-komodo',
      'name':'Komodo'
   },
   'KMDICE':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'KMDICE'
   },
   'LABS':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'LABS'
   },
   'LINK':{
      'coingecko_id':'chainlink',
      'binance_id':'LINK',
      'paprika_id':'link-chainlink',
      'name':'ChainLink'
   },
   'LTC':{
      'coingecko_id':'litecoin',
      'binance_id':'LTC',
      'paprika_id':'ltc-litecoin',
      'name':'Litecoin'
   },
   'MORTY':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'MORTY'
   },
   'OOT':{
      'coingecko_id':'utrum',
      'binance_id':'',
      'paprika_id':'oot-utrum',
      'name':'Utrum'
   },
   'PAX':{
      'coingecko_id':'paxos-standard',
      'binance_id':'PAX',
      'paprika_id':'pax-paxos-standard-token',
      'name':'Paxos Standard'
   },
   'QTUM':{
      'coingecko_id':'qtum',
      'binance_id':'QTUM',
      'paprika_id':'qtum-qtum',
      'name':'Qtum'
   },
   'REVS':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'REVS'
   },
   'RVN':{
      'coingecko_id':'ravencoin',
      'binance_id':'RVN',
      'paprika_id':'rvn-ravencoin',
      'name':'Ravencoin'
   },
   'RFOX':{
      'coingecko_id':'redfox-labs',
      'binance_id':'',
      'paprika_id':'rfox-redfox-labs',
      'name':'RedFOX Labs'
   },
   'RICK':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'RICK'
   },
   'SUPERNET':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'SUPERNET'
   },
   'THC':{
      'coingecko_id':'hempcoin-thc',
      'binance_id':'',
      'paprika_id':'thc-hempcoin',
      'name':'HempCoin'
   },
   'USDC':{
      'coingecko_id':'usd-coin',
      'binance_id':'',
      'paprika_id':'usdc-usd-coin',
      'name':'USD Coin'
   },
   'TUSD':{
      'coingecko_id':'true-usd',
      'binance_id':'TUSD',
      'paprika_id':'tusd-trueusd',
      'name':'TrueUSD'
   },
   'VRSC':{
      'coingecko_id':'verus-coin',
      'binance_id':'',
      'paprika_id':'vrsc-verus-coin',
      'name':'Verus Coin'
   },
   'ZEC':{
      'coingecko_id':'zcash',
      'binance_id':'ZEC',
      'paprika_id':'zec-zcash',
      'name':'Zcash'
   },
   'ZEXO':{
      'coingecko_id':'zaddex',
      'binance_id':'',
      'paprika_id':'',
      'name':'Zaddex'
   },
   'ZILLA':{
      'coingecko_id':'chainzilla',
      'binance_id':'',
      'paprika_id':'',
      'name':'ChainZilla'
   }
}

cointags = []
binance_coins = []
paprika_coins = []
gecko_coins = []
gecko_ids = []
paprika_ids = []
for coin in coin_api_codes:
    cointags.append(coin)
    if coin == 'BTC' or coin_api_codes[coin]['binance_id'] != '':
        binance_coins.append(coin)
    if coin == 'BTC' or coin_api_codes[coin]['paprika_id'] != '':
        paprika_coins.append(coin)
        paprika_ids.append(coin_api_codes[coin]['paprika_id'])
    if coin == 'BTC' or coin_api_codes[coin]['coingecko_id'] != '':
        gecko_coins.append(coin)
        gecko_ids.append(coin_api_codes[coin]['coingecko_id'])

cex_names = ['Binance']