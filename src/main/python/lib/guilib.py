#!/usr/bin/env python3
import re 
import os
import sys
import json
import time
import requests
from os.path import expanduser
from . import coinslib, rpclib, binance_api
from decimal import Decimal, ROUND_DOWN
import bitcoin
from bitcoin.wallet import P2PKHBitcoinAddress
from bitcoin.core import x
from bitcoin.core import CoreMainParams

class CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    BASE58_PREFIXES = {'PUBKEY_ADDR': 60,
                       'SCRIPT_ADDR': 85,
                       'SECRET_KEY': 188}
bitcoin.params = CoinParams

def get_radd_from_pub(pub):
    try:
        taker_addr = str(P2PKHBitcoinAddress.from_pubkey(x("02"+pub)))
    except:
        taker_addr = pub
    return str(taker_addr)

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

def get_creds(mm2_json_file):
    rpc_ip = ''
    userpass = ''
    print("getting creds")
    try:
        with open(mm2_json_file) as j:
            try:
                mm2json = json.load(j)
                if 'gui' in mm2json:
                    gui = mm2json['gui']
                else:
                    gui = ''
                if 'netid' in mm2json:
                    netid = mm2json['netid']
                else:
                    netid = 9999
                if 'passphrase' in mm2json:
                    passphrase = mm2json['passphrase']
                else:
                    passphrase = ''
                if 'rpc_password' in mm2json:
                    rpc_password = mm2json['rpc_password']
                    userpass = mm2json['rpc_password']
                else:
                    rpc_password = ''
                    userpass = ''
                if 'bn_key' in mm2json:
                    bn_key = mm2json['bn_key']
                else:
                    bn_key = ''
                if 'bn_secret' in mm2json:
                    bn_secret = mm2json['bn_secret']
                else:
                    bn_secret = ''
                if 'margin' in mm2json:
                    margin = mm2json['margin']
                else:
                    margin = 0
                if 'rpc_allow_ip' in mm2json:
                    rpc_ip = mm2json['rpc_allow_ip']
                else:
                    rpc_ip = '127.0.0.1'
                rpc_url = "http://"+rpc_ip+":7783"
                MM2_json_exists = True
            except Exception as e:
                print("assigning creds failed")
                print(e)
                rpc_url = ''
                rpc_password = ''
                userpass = ''
                passphrase = ''
                netid = 9999
                rpc_ip = ''
                bn_key = ''
                bn_secret = ''
                margin = 0
    except Exception as e:
        print("MM2json didnt open")
        print(e)
        rpc_url = ''
        userpass = ''
        rpc_password = ''
        passphrase = ''
        netid = 9999
        rpc_ip = ''
        bn_key = ''
        bn_secret = ''
        margin = 0
        pass
    return rpc_url, userpass, passphrase, netid, rpc_ip, bn_key, bn_secret, margin

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


def validate_ip(ip):
    ip_regex = '''^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
                    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
                    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
                    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'''
    if(re.search(ip_regex, ip)):  
        return True
    else:  
        return False

def get_unfinished_swaps(node_ip, user_pass):
    unfinished_swaps = []
    unfinished_swap_uuids = []
    recent_swaps = my_recent_swaps(node_ip, user_pass, 50).json()
    for swap in recent_swaps['result']['swaps']:
        swap_events = []
        for event in swap['events']:
            swap_events.append(event['event']['type'])
        if 'Finished' not in swap_events:
            unfinished_swaps.append(swap)
            unfinished_swap_uuids.append(swap['uuid'])
    return unfinished_swap_uuids, unfinished_swaps

def get_active_coins(node_ip, user_pass):
    active_cointags = []
    active_coins = rpclib.get_enabled_coins(node_ip, user_pass).json()
    if 'result' in active_coins:
        active_coins = active_coins['result']
        for coin in active_coins:
            active_cointags.append(coin['ticker'])
        return active_cointags 
    else:
      print(active_coins)