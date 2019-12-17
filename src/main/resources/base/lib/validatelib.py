#!/usr/bin/env python3
from . import coinslib

def validate_coins(coins_list):
    for coin in coins_list:
        if coin not in coinslib.cointags:
            return False, coin
    return True, coins_list

def validate_cex(cex_list):
    for cex in cex_list:
        if cex not in coinslib.cex_names:
            return False, cex
    return True, cex_list
