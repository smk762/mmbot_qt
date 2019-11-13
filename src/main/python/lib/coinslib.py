# Input coins you want to trade here. 
# reserve_balance: excess funds will be sent to your Binance wallet
# premium: value relative to binance market rate to setprices as marketmaker.
# min/max/stepsize need to be set from values from 
# https://api.binance.com/api/v1/exchangeInfo

coin_activation = {
   'AXE':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10057'},
         {'url':'electrum2.cipig.net:10057'},
         {'url':'electrum3.cipig.net:10057'}
      ],
      'type':'utxo',
   },
   'AWC':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'BAT':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'BCH':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electron.coinucopia.io:50001'},
         {'url':'bch.imaginary.cash:50001'},
         {'url':'wallet.satoshiscoffeehouse.com:50001'},
         {'url':'electroncash.dk:50001'},
         {'url':'electron-cash.dragon.zone:50001'}
      ],
      'type':'utxo'
   },
   'BOTS':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10007'},
         {'url':'electrum2.cipig.net:10007'},
         {'url':'electrum3.cipig.net:10007'}
      ],
      'type':'smartchain'
   },
   'BTC':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10000'},
         {'url':'electrum2.cipig.net:10000'},
         {'url':'electrum3.cipig.net:10000'}
      ],
      'type':'utxo'
   },
   'BTCH':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10020'},
         {'url':'electrum2.cipig.net:10020'},
         {'url':'electrum3.cipig.net:10020'}
      ],
      'type':'smartchain'
   },
   'CHIPS':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10053'},
         {'url':'electrum2.cipig.net:10053'},
         {'url':'electrum3.cipig.net:10053'}
      ],
      'type':'smartchain'
   },
   'COMMOD':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10022'},
         {'url':'electrum2.cipig.net:10022'},
         {'url':'electrum3.cipig.net:10022'}
      ],
      'type':'smartchain'
   },
   'COQUI':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10011'},
         {'url':'electrum2.cipig.net:10011'},
         {'url':'electrum3.cipig.net:10011'}
      ],
      'type':'smartchain'
   },
   'CRYPTO':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10008'},
         {'url':'electrum2.cipig.net:10008'},
         {'url':'electrum3.cipig.net:10008'}
      ],
      'type':'smartchain'
   },
   'DAI':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'DASH':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10061'},
         {'url':'electrum2.cipig.net:10061'},
         {'url':'electrum3.cipig.net:10061'}
      ],
      'type':'utxo'
   },
   'DEX':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10006'},
         {'url':'electrum2.cipig.net:10006'},
         {'url':'electrum3.cipig.net:10006'}
      ],
      'type':'smartchain'
   },
   'DGB':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10059'},
         {'url':'electrum2.cipig.net:10059'},
         {'url':'electrum3.cipig.net:10059'}
      ],
      'type':'utxo'
   },
   'DOGE':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10060'},
         {'url':'electrum2.cipig.net:10060'},
         {'url':'electrum3.cipig.net:10060'}
      ],
      'type':'utxo'
   },
   'ETH':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'HUSH':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10064'},
         {'url':'electrum2.cipig.net:10064'},
         {'url':'electrum3.cipig.net:10064'}
      ],
      'type':'smartchain'
   },
   'KMD':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10001'},
         {'url':'electrum2.cipig.net:10001'},
         {'url':'electrum3.cipig.net:10001'}
      ],
      'type':'smartchain'
   },
   'KMDICE':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10031'},
         {'url':'electrum2.cipig.net:10031'},
         {'url':'electrum3.cipig.net:10031'}
      ],
      'type':'smartchain'
   },
   'LABS':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10019'},
         {'url':'electrum2.cipig.net:10019'},
         {'url':'electrum3.cipig.net:10019'}
      ],
      'type':'smartchain'
   },
   'LINK':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'LTC':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum-ltc.bysh.me:50001'},
         {'url':'electrum.ltc.xurious.com:50001'},
         {'url':'ltc.rentonisk.com:50001'},
         {'url':'backup.electrum-ltc.org:50001'}
      ],
      'type':'utxo'
   },
   'MORTY':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10018'},
         {'url':'electrum2.cipig.net:10018'},
         {'url':'electrum3.cipig.net:10018'}
      ],
      'type':'smartchain'
   },
   'OOT':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.utrum.io:10088'},
         {'url':'electrum2.utrum.io:10088'}
      ],
      'type':'smartchain'
   },
   'PAX':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'QTUM':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'s1.qtum.info:50001'},
         {'url':'s2.qtum.info:50001'},
         {'url':'s3.qtum.info:50001'},
         {'url':'s4.qtum.info:50001'},
         {'url':'s5.qtum.info:50001'},
         {'url':'s6.qtum.info:50001'},
         {'url':'s7.qtum.info:50001'},
         {'url':'s8.qtum.info:50001'},
         {'url':'s9.qtum.info:50001'}
      ],
      'type':'utxo'
   },
   'REVS':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10003'},
         {'url':'electrum2.cipig.net:10003'},
         {'url':'electrum3.cipig.net:10003'}
      ],
      'type':'smartchain'
   },
   'RVN':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10051'},
         {'url':'electrum2.cipig.net:10051'},
         {'url':'electrum3.cipig.net:10051'}
      ],
      'type':'utxo'
   },
   'RFOX':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10034'},
         {'url':'electrum2.cipig.net:10034'},
         {'url':'electrum3.cipig.net:10034'}
      ],
      'type':'smartchain'
   },
   'RICK':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10017'},
         {'url':'electrum2.cipig.net:10017'},
         {'url':'electrum3.cipig.net:10017'}
      ],
      'type':'smartchain'
   },
   'SUPERNET':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10005'},
         {'url':'electrum2.cipig.net:10005'},
         {'url':'electrum3.cipig.net:10005'}
      ],
      'type':'smartchain'
   },
   'THC':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'165.22.52.123:10022'},
         {'url':'157.230.45.184:10022'}
      ],
      'type':'smartchain'
   },
   'USDC':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'TUSD':{
      'activate_with':'electrum',
      'electrum':[
         'http://eth1.cipig.net:8555',
         'http://eth2.cipig.net:8555',
         'http://eth3.cipig.net:8555'
      ],
      'contract':'0x8500AFc0bc5214728082163326C2FF0C73f4a871',
      'type':'erc20'
   },
   'VRSC':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'el0.vrsc.0x03.services:10000'},
         {'url':'el1.vrsc.0x03.services:10000'},
         {'url':'electrum1.cipig.net:10021'},
         {'url':'electrum2.cipig.net:10021'},
         {'url':'electrum3.cipig.net:10021'}
      ],
      'type':'smartchain'
   },
   'WLC':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10014'},
         {'url':'electrum2.cipig.net:10014'},
         {'url':'electrum3.cipig.net:10014'}
      ],
      'type':'smartchain'
   },
   'ZEC':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum3.cipig.net:10058'},
         {'url':'electrum3.cipig.net:10058'},
         {'url':'electrum3.cipig.net:10058'}
      ],
      'type':'utxo'
   },
   'ZEXO':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10035'},
         {'url':'electrum2.cipig.net:10035'},
         {'url':'electrum3.cipig.net:10035'}
      ],
      'type':'smartchain'
   },
   'ZILLA':{
      'activate_with':'electrum',
      'electrum':[
         {'url':'electrum1.cipig.net:10028'},
         {'url':'electrum2.cipig.net:10028'},
         {'url':'electrum3.cipig.net:10028'}
      ],
      'type':'smartchain'
   }
}

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
      'binance_id':'BCHABC',
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
   'COMMOD':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'COMMOD'
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
   'WLC':{
      'coingecko_id':'',
      'binance_id':'',
      'paprika_id':'',
      'name':'WLC'
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

coin_explorers = {
   'AXE':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':''
   },
   'AWC':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'BAT':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'BCH':{
      'tx_explorer':'https://explorer.bitcoin.com/bch/tx',
      'addr_explorer':''
   },
   'BOTS':{
      'tx_explorer':'https://bots.explorer.dexstats.info/tx',
      'addr_explorer':'https://bots.explorer.dexstats.info/address'
   },
   'BTC':{
      'tx_explorer':'https://explorer.bitcoin.com/btc/tx',
      'addr_explorer':''
   },
   'BTCH':{
      'tx_explorer':'https://btch.explorer.dexstats.info/tx',
      'addr_explorer':'https://btch.explorer.dexstats.info/address'
   },
   'CHIPS':{
      'tx_explorer':'https://chips.explorer.dexstats.info/tx',
      'addr_explorer':'https://chips.explorer.dexstats.info/address'
   },
   'COMMOD':{
      'tx_explorer':'https://commod.explorer.dexstats.info/tx',
      'addr_explorer':'https://commod.explorer.dexstats.info/address'
   },
   'COQUI':{
      'tx_explorer':'https://coqui.explorer.dexstats.info/tx',
      'addr_explorer':'https://coqui.explorer.dexstats.info/address'
   },
   'CRYPTO':{
      'tx_explorer':'https://crypto.explorer.dexstats.info/tx',
      'addr_explorer':'https://crypto.explorer.dexstats.info/address'
   },
   'DAI':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'DASH':{
      'tx_explorer':'https://explorer.dash.org/tx',
      'addr_explorer':''
   },
   'DEX':{
      'tx_explorer':'https://dex.explorer.dexstats.info/tx',
      'addr_explorer':'https://dex.explorer.dexstats.info/address'
   },
   'DGB':{
      'tx_explorer':'https://digiexplorer.info/tx',
      'addr_explorer':''
   },
   'DOGE':{
      'tx_explorer':'https://live.blockcypher.com/doge/tx',
      'addr_explorer':''
   },
   'ETH':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'HUSH':{
      'tx_explorer':'https://hush.explorer.dexstats.info/tx',
      'addr_explorer':'https://hush.explorer.dexstats.info/address'
   },
   'KMD':{
      'tx_explorer':'https://kmd.explorer.dexstats.info/tx',
      'addr_explorer':'https://kmd.explorer.dexstats.info/address'
   },
   'KMDICE':{
      'tx_explorer':'https://kmdice.explorer.dexstats.info/tx',
      'addr_explorer':'https://kmdice.explorer.dexstats.info/address'
   },
   'LABS':{
      'tx_explorer':'https://labs.explorer.dexstats.info/tx',
      'addr_explorer':'https://labs.explorer.dexstats.info/address'
   },
   'LINK':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'LTC':{
      'tx_explorer':'https://live.blockcypher.com/ltc/tx',
      'addr_explorer':''
   },
   'MORTY':{
      'tx_explorer':'https://morty.explorer.dexstats.info/tx',
      'addr_explorer':'https://morty.explorer.dexstats.info/address'
   },
   'OOT':{
      'tx_explorer':'https://oot.explorer.dexstats.info/tx',
      'addr_explorer':'https://oot.explorer.dexstats.info/address'
   },
   'PAX':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'QTUM':{
      'tx_explorer':'https://qtum.info/tx',
      'addr_explorer':''
   },
   'REVS':{
      'tx_explorer':'https://revs.explorer.dexstats.info/tx',
      'addr_explorer':'https://revs.explorer.dexstats.info/address'
   },
   'RVN':{
      'tx_explorer':'https://ravencoin.network/tx',
      'addr_explorer':''
   },
   'RFOX':{
      'tx_explorer':'https://rfox.explorer.dexstats.info/tx',
      'addr_explorer':'https://rfox.explorer.dexstats.info/address'
   },
   'RICK':{
      'tx_explorer':'https://rick.explorer.dexstats.info/tx',
      'addr_explorer':'https://rick.explorer.dexstats.info/address'
   },
   'SUPERNET':{
      'tx_explorer':'https://supernet.explorer.dexstats.info/tx',
      'addr_explorer':'https://supernet.explorer.dexstats.info/address'
   },
   'THC':{
      'tx_explorer':'https://thc.explorer.dexstats.info/tx',
      'addr_explorer':'https://thc.explorer.dexstats.info/address'
   },
   'USDC':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'TUSD':{
      'tx_explorer':'https://etherscan.io/tx',
      'addr_explorer':'https://etherscan.io/address'
   },
   'VRSC':{
      'tx_explorer':'https://vrsc.explorer.dexstats.info/tx',
      'addr_explorer':'https://vrsc.explorer.dexstats.info/address'
   },
   'WLC':{
      'tx_explorer':'https://wlc.explorer.dexstats.info/tx',
      'addr_explorer':'https://wlc.explorer.dexstats.info/address'
   },
   'ZEC':{
      'tx_explorer':'https://explorer.zcha.in/transactions',
      'addr_explorer':''
   },
   'ZEXO':{
      'tx_explorer':'https://zexo.explorer.dexstats.info/tx',
      'addr_explorer':'https://zexo.explorer.dexstats.info/address'
   },
   'ZILLA':{
      'tx_explorer':'https://zilla.explorer.dexstats.info/tx',
      'addr_explorer':'https://zilla.explorer.dexstats.info/address'
   }
}

cointags = []
for ticker in coin_activation:
    cointags.append(ticker)

binance_coins = []
for coin in coin_api_codes:
    if coin == 'BTC' or coin_api_codes[coin]['binance_id'] != '':
        binance_coins.append(coin)
print(binance_coins)