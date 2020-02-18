from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import requests
from . import guilib, rpclib, binance_api, priceslib, coinslib
import datetime
import time
import logging
from .util import populate_table

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# THREADED OPERATIONS

# request and cache external balance and pricing data in thread
class cachedata_thread(QThread):
    update_data = pyqtSignal(dict, dict)
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            try:
                prices_data = requests.get('http://127.0.0.1:8000/all_prices').json()
                balances_data = requests.get('http://127.0.0.1:8000/all_balances').json()
                self.update_data.emit(prices_data, balances_data)
            except Exception as e:
                pass
                logger.info('cache_data error')
                logger.info(e)
            time.sleep(5)

# request and cache external balance and pricing data in thread
class consoleLogs_thread(QThread):
    update_logs = pyqtSignal()
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            try:
                self.update_logs.emit()
            except Exception as e:
                pass
                logger.info('console_log error')
                logger.info(e)
            time.sleep(1)

# Process mm2 coin activation
class activation_thread(QThread):
    activate = pyqtSignal(str)
    def __init__(self, creds, coins_to_activate):
        QThread.__init__(self)
        self.coins =  coins_to_activate
        self.creds = creds

    def __del__(self):
        self.wait()

    def run(self):
        active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        for coin in self.coins:
            if coin[0] not in active_coins:
                r = rpclib.electrum(self.creds[0], self.creds[1], coin[0])
                logger.info(guilib.colorize("Activating "+coin[0]+" with electrum", 'cyan'))
                self.activate.emit(coin[0])

class api_request_thread(QThread):
    update_data = pyqtSignal(object, object, object, str, str, str)
    def __init__(self, endpoint, table, msg_lbl, msg, row_filter):
        QThread.__init__(self)
        self.endpoint = endpoint
        self.table = table
        self.msg_lbl = msg_lbl
        self.msg = msg
        self.row_filter = row_filter

    def __del__(self):
        self.wait()

    def run(self):
        url = "http://127.0.0.1:8000/"+self.endpoint
        r = requests.get(url)
        self.update_data.emit(r, self.table, self.msg_lbl, self.msg, self.row_filter, self.endpoint)

class addr_request_thread(QThread):
    resp = pyqtSignal(dict, str)
    def __init__(self, creds_5, creds_6, coin):
        QThread.__init__(self)
        self.coin = coin
        self.creds_5 = creds_5
        self.creds_6 = creds_6

    def __del__(self):
        self.wait()

    def run(self):
        r = binance_api.get_deposit_addr(self.creds_5, self.creds_6, self.coin)
        self.resp.emit(r, self.coin)


def request_table_data(endpoint, table, msg_lbl='', msg='', row_filter=''):
    # start in other thread
    table_request_thread = api_request_thread(endpoint, table, msg_lbl, msg, row_filter)
    table_request_thread.update_data.connect(populate_table)
    table_request_thread.start()