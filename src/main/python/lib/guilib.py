#!/usr/bin/env python3
import re 
import os
import sys
import json
import time
import requests
import subprocess
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

## MM2 management
def start_mm2(logfile='mm2_output.log'):
    if os.path.isfile(script_path+"/bin/mm2"):
        mm2_output = open(script_path+"/bin/"+logfile,'w+')

        subprocess.Popen([script_path+"/bin/mm2"], stdout=mm2_output, stderr=mm2_output, universal_newlines=True)
        time.sleep(1)
    else:
        with open(script_path+"/bin/"+logfile,'w+') as f:
            f.write("\nmm2 binary not found in "+script_path+"/bin!")
            f.write("\nExiting...\n")
        print(colorize("\nmm2 binary not found in "+script_path+"/bin!", 'red'))
        print(colorize("See https://developers.komodoplatform.com/basic-docs/atomicdex/atomicdex-setup/get-started-atomicdex.html for install instructions.", 'orange'))
        print(colorize("Exiting...\n", 'blue'))

def validate_ip(ip):
    ip_regex = '''^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
                    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
                    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.( 
                    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'''
    if(re.search(ip_regex, ip)):  
        return True
    else:  
        return False
