import os
import json
from .enc import decrypt_mm2_json
from . import binance_api
import logging
logger = logging.getLogger(__name__)

def decrypt_creds(username, password, config_path):
    # create .enc if new user
    authenticated = False
    if not os.path.isfile(config_path+username+"_MM2.enc"):
        with open(config_path+username+"_MM2.enc", 'w') as f:
            f.write('')
    # create MM2.json if first run
    if not os.path.isfile(config_path+"MM2.json"):
        with open(config_path+"MM2.json", 'w') as f:
            f.write('')
    # decrypt user MM2.json
    else:
        with open(config_path+username+"_MM2.enc", 'r') as f:
            encrypted_mm2_json = f.read()
        if encrypted_mm2_json != '':
            mm2_json_decrypted = decrypt_mm2_json(encrypted_mm2_json, password)
            try:
                with open(config_path+"MM2.json", 'w') as j:
                    j.write(mm2_json_decrypted.decode())
                authenticated = True
            except:
                # did not decode, bad password
                logger.info("decrypting failed")
                pass
    jsonfile = config_path+"MM2.json"
    try:
        creds = get_creds(jsonfile)
    except Exception as e:
        logger.info("get_credentials failed")
        logger.info(e)
        creds = ['','','','','','','','','','','']
    return authenticated, creds

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
                if 'bot_mode' in mm2json:
                    bot_mode = mm2json['bot_mode']
                else:
                    bot_mode = ''
                if 'countertrade_timeout' in mm2json:
                    countertrade_timeout = mm2json['countertrade_timeout']
                else:
                    countertrade_timeout = 30
                if 'login_timeout' in mm2json:
                    login_timeout = mm2json['login_timeout']
                else:
                    login_timeout = 10
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
                bot_mode = ''
                countertrade_timeout = 30
                login_timeout = 10
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
        bot_mode = ''
        countertrade_timeout = 30
        login_timeout = 10
    return rpc_url, userpass, passphrase, netid, rpc_ip, bn_key, bn_secret, margin, bot_mode, countertrade_timeout, login_timeout

def check_binance_auth(key, secret):
    binance_acct = binance_api.get_account_info(key, secret)
    if 'code' in binance_acct:
        authenticated = False
        err = binance_acct['msg']
    else:
        authenticated = True
        err = ''
    return authenticated, err