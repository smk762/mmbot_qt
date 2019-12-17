#!/usr/bin/env python3
import json
import requests
from . import coinslib, guilib, binance_api
   

def start_mm2_bot_loop(creds, buy_coins, sell_coins, cancel_previous, trade_max):
    for base in self.sell_coins:
        for rel in self.buy_coins:
            if base != rel:
                pass
                    # detect unfinished swaps