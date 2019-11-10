#!/usr/bin/env python3
import json
import requests
from . import coinslib, guilib, binance_api

def get_binance_addr(cointag):
    try:
        if cointag == "BCH":
            deposit_addr = binance_api.get_deposit_addr(cointag+"ABC")
        else:
            deposit_addr = binance_api.get_deposit_addr(cointag)
    except:
        deposit_addr == ''
        pass
    return deposit_addr