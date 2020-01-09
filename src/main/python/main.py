#!/usr/bin/env python3
from fbs_runtime.application_context.PyQt5 import ApplicationContext
import os
import sys
import stat
import json
import requests
from os.path import expanduser
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from lib import guilib, rpclib, coinslib, wordlist, enc, priceslib, binance_api, botlib
import qrcode
import random
from ui import resources
import datetime
import time
from dateutil import parser
from zipfile import ZipFile 
import platform
import subprocess
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Point import Point
import decimal

'''
# TODOS #
 - create tablification scripts for data returned from api or mm2.
 - remove code deprecated by API
 - autoactivate coins needing kickstart
 - https://api.hitbtc.com/
 - https://documenter.getpostman.com/view/8180765/SVfTPnM8?version=latest#intro
 - Add orderbook table view from API loop

'''

home = expanduser("~")

# Attempt to suppress console window in windows version. TODO: not working, find another way.
if platform.system() == 'Windows':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

# scaling for high DPI vs SD monitors. Awaiting feedback from other users if any buttons etc are too small.
os.environ["QT_SCALE_FACTOR"] = "1"  
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# graph foreground / background colors
pg.setConfigOption('background', (64,64,64))
pg.setConfigOption('foreground', (78,155,46))

# Setup local settings config ini.
QSettings.setDefaultFormat(QSettings.IniFormat)
QCoreApplication.setOrganizationName("KomodoPlatform")
QCoreApplication.setApplicationName("AntaraMakerbot")
settings = QSettings()
ini_file = settings.fileName()
config_path = settings.fileName().replace("AntaraMakerbot.ini", "")

os.environ['MM_CONF_PATH'] = config_path+"MM2.json"

# Detect existing registered users
if settings.value('users') is None:
    settings.setValue("users", [])

def get_time_str():
    return str(datetime.datetime.fromtimestamp(int(time.time())))

# https://en.bitcoin.it/wiki/Proper_Money_Handling_%28JSON-RPC%29
def JSONtoAmount(value):
    return long(round(value * 1e8))
def AmountToJSON(amount):
    return float(amount / 1e8)

def ETH_JSONtoAmount(value):
    return long(round(value * 1e18))
def ETH_AmountToJSON(amount):
    return float(amount / 1e18)

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
                time.sleep(10)
            except Exception as e:
                print('cache_data error')
                print(e)
                pass

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
                print(guilib.colorize("Activating "+coin[0]+" with electrum", 'cyan'))
                self.activate.emit(coin[0])

# Get price graph history
class graph_history_thread(QThread):
    get_history = pyqtSignal(str, str, list, list, list)
    def __init__(self, coin, coin_id, quote):
        QThread.__init__(self)
        self.coin = coin
        self.coin_id = coin_id
        self.quote = quote

    def __del__(self):
        self.wait()

    def run(self): 
        if self.quote == 'KMD':
            kmd_btc_price =priceslib.get_paprika_price(coinslib.coin_api_codes['KMD']['paprika_id']).json()['price_btc']
            history = priceslib.get_paprika_history(self.coin_id, 'year_ago', 'BTC')
            kmd_history = priceslib.get_paprika_history(coinslib.coin_api_codes['KMD']['paprika_id'], 'year_ago', 'BTC')
        else:
            history = priceslib.get_paprika_history(self.coin_id, 'year_ago', self.quote)
        x = []
        x_str = []
        y = []
        time_ticks = []
        val_ticks = []
        self.xy = {}
        last_time = ''
        item_count = 0
        for item in history:
            # Calculate historical price in KMD
            if self.quote == 'KMD':
                kmd_btc_price = kmd_history[item_count]['price']
                price_point = float(item['price'])/float(kmd_btc_price)
                item_count += 1
            else:
                price_point = item['price']
            # add value to y axis list
            y.append(price_point)
            
            dt = parser.parse(item['timestamp'])

            # add timestamp and timestring (for labels) to x axis list
            x.append(int(datetime.datetime.timestamp(dt)))
            x_str.append(item['timestamp'])
            # derive time label ticks based on history timespan
            month = time.ctime(int(datetime.datetime.timestamp(dt))).split(" ")[1]
            if month != last_time:
                if last_time != '':
                    time_ticks.append((int(datetime.datetime.timestamp(dt)),month))
                last_time = month
        # emit signal to draw graph with xy data
        self.get_history.emit(self.coin, self.quote, x, y, time_ticks)

# Creates a QR code from a string. Can misbehave if pixmap area size not ideal.
class QR_image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QImage(size, size, QImage.Format_RGB16)
        self._image.fill(Qt.white)

    def pixmap(self):
        return QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            Qt.black)

    def save(self, stream, kind=None):
        pass

class ScrollMessageBox(QMessageBox):
    def __init__(self, json_data, *args, **kwargs):
        QMessageBox.__init__(self, *args, **kwargs)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        scroll.setWidget(self.content)
        lay = QVBoxLayout(self.content)
        json_lines = json.dumps(json_data, indent=4)
        msg_data = QTextEdit(json_lines, self)
        msg_data.setReadOnly(True)
        lay.addWidget(msg_data)
        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:600 px; min-height: 800px}")

# UI Class

class Ui(QTabWidget):
    def __init__(self, ctx):
        super(Ui, self).__init__() 
        # Load the User interface from file
        uifile = QFile(":/ui/makerbot_gui_dark_v4a.ui")
        uifile.open(QFile.ReadOnly)
        uic.loadUi(uifile, self) 
        self.ctx = ctx 
        self.show() 
        # define mm2 binary path
        try:
            self.mm2_bin = self.ctx.get_resource('mm2')
        except:
            self.mm2_bin = self.ctx.get_resource('mm2.exe')
        # define local bot api script
        self.bot_api = self.ctx.get_resource('serve_bot.py')
        # define coins file path and set envornment variable for mm2 launch
        self.coins_file = self.ctx.get_resource('coins')
        os.environ['MM_COINS_PATH'] = self.coins_file
        # define qss (stylesheet) path and apply styling. 
        self.qss_file = self.ctx.get_resource('Darkeum.qss')
        with open(self.qss_file, 'r') as file:
            qss = file.read()
            self.setStyleSheet(qss)
                
        self.setWindowTitle("Komodo Platform's Antara Makerbot")
        self.setWindowIcon(QIcon(':/32/img/32/kmd.png'))
        self.authenticated = False
        self.mm2_downloading = False
        self.bot_trading = False
        self.countertrade_delay_limit = 1800

        self.last_price_update = 0
        self.prices_data = {
            "gecko":{},
            "paprika":{},
            "Binance":{},
            "average":{}
        }
        self.balances_data = {
            "mm2": {},
            "Binance": {}
        }

        # dict for the checkbox and combobox elements use on the coins activation page. Might be a better way to do this.
        self.gui_coins = {
            "BTC": {
                "checkbox": self.checkBox_btc, 
                "combo": self.btc_combo,    
            },
            "ETH": {
                "checkbox": self.checkBox_eth, 
                "combo": self.eth_combo,
            },
            "KMD": {
                "checkbox": self.checkBox_kmd, 
                "combo": self.kmd_combo,
            },
            "LABS": {
                "checkbox": self.checkBox_labs, 
                "combo": self.labs_combo,
            },
            "BCH": {
                "checkbox": self.checkBox_bch, 
                "combo": self.bch_combo,
            },
            "BAT": {
                "checkbox": self.checkBox_bat, 
                "combo": self.bat_combo,
            },
            "DOGE": {
                "checkbox": self.checkBox_doge, 
                "combo": self.doge_combo,
            },
            "DGB": {
                "checkbox": self.checkBox_dgb, 
                "combo": self.dgb_combo,
            },
            "DASH": {
                "checkbox": self.checkBox_dash, 
                "combo": self.dash_combo,
            },
            "LTC": {
                "checkbox": self.checkBox_ltc, 
                "combo": self.ltc_combo,
            },
            "ZEC": {
                "checkbox": self.checkBox_zec, 
                "combo": self.zec_combo,
            },
            "QTUM": {
                "checkbox": self.checkBox_qtum, 
                "combo": self.qtum_combo,
            },
            "AXE": {
                "checkbox": self.checkBox_axe, 
                "combo": self.axe_combo,
            },
            "VRSC": {
                "checkbox": self.checkBox_vrsc, 
                "combo": self.vrsc_combo,
            },
            "RFOX": {
                "checkbox": self.checkBox_rfox, 
                "combo": self.rfox_combo,
            },
            "ZILLA": {
                "checkbox": self.checkBox_zilla, 
                "combo": self.zilla_combo,
            },
            "HUSH": {
                "checkbox": self.checkBox_hush, 
                "combo": self.hush_combo,
            },
            "OOT": {
                "checkbox": self.checkBox_oot, 
                "combo": self.oot_combo,
            },
            "USDC": {
                "checkbox": self.checkBox_usdc, 
                "combo": self.usdc_combo,
            },
            "AWC": {
                "checkbox": self.checkBox_awc, 
                "combo": self.awc_combo,
            },
            "TUSD": {
                "checkbox": self.checkBox_tusd, 
                "combo": self.tusd_combo,
            },
            "PAX": {
                "checkbox": self.checkBox_pax, 
                "combo": self.pax_combo,
            },
            "RICK": {
                "checkbox": self.checkBox_rick, 
                "combo": self.rick_combo,
            },
            "MORTY": {
                "checkbox": self.checkBox_morty, 
                "combo": self.morty_combo,
            },
            "DAI": {
                "checkbox": self.checkBox_dai, 
                "combo": self.dai_combo,
            },
            "RVN": {
                "checkbox": self.checkBox_rvn, 
                "combo": self.rvn_combo,
            },
            "BOTS":{ 
                "checkbox":self.checkBox_bots, 
                "combo":self.bots_combo, 
            },
            "BTCH":{ 
                "checkbox":self.checkBox_btch, 
                "combo":self.btch_combo, 
            },
            "CHIPS":{ 
                "checkbox":self.checkBox_chips, 
                "combo":self.chips_combo, 
            },
            "COQUI":{ 
                "checkbox":self.checkBox_coqui, 
                "combo":self.coqui_combo, 
            },
            "CRYPTO":{ 
                "checkbox":self.checkBox_crypto, 
                "combo":self.crypto_combo, 
            },
            "DEX":{ 
                "checkbox":self.checkBox_dex, 
                "combo":self.dex_combo, 
            },
            "KMDICE":{ 
                "checkbox":self.checkBox_kmdice, 
                "combo":self.kmdice_combo, 
            },
            "LINK":{ 
                "checkbox":self.checkBox_link, 
                "combo":self.link_combo, 
            },
            "REVS":{ 
                "checkbox":self.checkBox_revs, 
                "combo":self.revs_combo, 
            },
            "SUPERNET":{ 
                "checkbox":self.checkBox_supernet, 
                "combo":self.supernet_combo, 
            },
            "THC":{ 
                "checkbox":self.checkBox_thc, 
                "combo":self.thc_combo, 
            },
            "ZEXO":{ 
                "checkbox":self.checkBox_zexo, 
                "combo":self.zexo_combo, 
            },
        }               
        self.show_login_tab()
                
    # once cachedata thred returns data, update balances, logs and tables as periodically.
    def update_cachedata(self, prices_dict, balances_dict):
        self.prices_data = prices_dict
        self.balances_data['mm2'].update(balances_dict['mm2'])
        self.balances_data["Binance"].update(balances_dict["Binance"])
        baserel = self.get_base_rel_from_combos(self.orderbook_sell_combo, self.orderbook_buy_combo, 'mm2')
        base = baserel[0]
        rel = baserel[1]
        self.update_mm2_orderbook_labels(base, rel)
        self.update_mm2_balance_table()
        self.update_mm2_wallet_labels()
        baserel = self.get_base_rel_from_combos(self.binance_base_combo, self.binance_rel_combo, "Binance")
        base = baserel[0]
        rel = baserel[1]
        self.update_binance_balance_table()
        self.update_prices_table()
        self.update_mm2_trade_history_table()
        self.update_strategies_table()
        self.view_strat_summary()
        self.update_mm2_orders_table()

        # TODO: Add gui update functions as req here.

    ## MM2 management
    # start MM2 for specific user
    def start_mm2(self, logfile='mm2_output.log'):
        try:
            mm2_output = open(config_path+self.username+"_"+logfile,'w+')
            subprocess.Popen([self.mm2_bin], stdout=mm2_output, stderr=mm2_output, universal_newlines=True)
            time.sleep(1)
        except Exception as e:
            QMessageBox.information(self, "Progress status", 'No mm2!')
            print(e)

    def start_api(self, logfile='bot_api_output.log'):
        try:
            bot_api_output = open(config_path+self.username+"_"+logfile,'w+')
            subprocess.Popen([self.bot_api, config_path+self.username+"/"], stdout=bot_api_output, stderr=bot_api_output, universal_newlines=True)
            time.sleep(2)
            requests.post('http://127.0.0.1:8000/set_creds?ip='+self.creds[4]+'&rpc_pass='+self.creds[1]+'&key='+self.creds[5]+'&secret='+self.creds[6])
        except Exception as e:
            print('bot not start')
            print(e)

    def launch_mm2(self):
        if self.username in settings.value('users'):
            self.username_input.setText('')
            self.password_input.setText('')
            # hide login page, show activation page
            self.stacked_login.setCurrentIndex(1)
            if self.creds[0] != '':
                version = ''
                stopped = False
                while version == '':
                    # check if mm2 running, and stop if it is.
                    if not stopped:
                        try:
                            rpclib.stop_mm2(self.creds[0], self.creds[1])
                        except:
                            stopped = True
                            pass
                    try:
                        self.start_mm2()
                        time.sleep(0.6)
                        version = rpclib.version(self.creds[0], self.creds[1]).json()['result']
                        self.mm2_version_lbl.setText("MarketMaker version: "+version+" ")
                    except Exception as e:
                        print('mm2 not start')
                        print(e)
                    try:
                        self.start_api()
                        time.sleep(0.6)
                        version = requests.get('http://127.0.0.1:8000/api_version').json()['version']
                        print(version)
                        self.api_version_lbl.setText("Makerbot API version: "+version+" ")
                    except Exception as e:
                        print('bot not start')
                        print(e)
                        # TODO: MESSAGEBOX AND EXIT
                # purge MM2.json cleartext
                with open(config_path+"MM2.json", 'w+') as j:
                    j.write('')
                self.show_activation_tab()
                # stop zombie orders / strats
                self.stop_all_strats()
                rpclib.cancel_all(self.creds[0], self.creds[1]).json()
                # start data caching loop in other thread
                self.datacache_thread = cachedata_thread()
                self.datacache_thread.update_data.connect(self.update_cachedata)
                self.datacache_thread.start()
            else:
                self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))

    def decrypt_creds(self):
        # create .enc if new user
        if not os.path.isfile(config_path+self.username+"_MM2.enc"):
            with open(config_path+self.username+"_MM2.enc", 'w') as f:
                f.write('')
        # create MM2.json if first run
        if not os.path.isfile(config_path+"MM2.json"):
            with open(config_path+"MM2.json", 'w') as f:
                f.write('')
        # decrypt user MM2.json
        else:
            with open(config_path+self.username+"_MM2.enc", 'r') as f:
                encrypted_mm2_json = f.read()
            if encrypted_mm2_json != '':
                mm2_json_decrypted = enc.decrypt_mm2_json(encrypted_mm2_json, self.password)
                try:
                    with open(config_path+"MM2.json", 'w') as j:
                        j.write(mm2_json_decrypted.decode())
                    self.authenticated = True
                except:
                    # did not decode, bad password
                    print("decrypting failed")
                    pass
        jsonfile = config_path+"MM2.json"
        try:
            self.creds = guilib.get_creds(jsonfile)
        except Exception as e:
            print("get_credentials failed")
            print(e)
            self.creds = ['','','','','','','','','','']
            pass

    ## File operations
    def saveFileDialog(self):
        filename = ''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save Trade data to CSV","","Text Files (*.csv)", options=options)
        return fileName

    # Table operations
    def export_table(self):
        #TODO: add sender, get headers dynamically
        table_csv = 'Date, Status, Sell coin, Sell volume, Buy coin, Buy volume, Sell price, UUID\r\n'
        for i in range(self.mm2_trades_table.rowCount()):
            row_list = []
            for j in range(self.mm2_trades_table.columnCount()):
                try:
                    row_list.append(self.mm2_trades_table.item(i,j).text())
                except:
                    pass
            table_csv += ','.join(row_list)+'\r\n'
        now = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(now)
        filename = self.saveFileDialog()
        if filename != '':
            with open(filename, 'w') as f:
                f.write(table_csv)

    def clear_table(self, table):
        row = 0
        row_count = table.rowCount()
        col_count = table.columnCount()
        while row_count > row:
            row_items = []
            for i in range(col_count):
                row_items.append(QTableWidgetItem(''))
            col = 0
            for cell in row_items:
                table.setItem(row,col,cell)
                col += 1
            row += 1

    def populate_table(self, endpoint, table, msg_lbl='', msg='', row_filter=''):
        url = "http://127.0.0.1:8000/"+endpoint
        r = requests.get(url)
        if r.status_code == 200:
            table.setSortingEnabled(False)
            self.clear_table(table)
            data = r.json()['table_data']
            table.setRowCount(len(data))
            row = 0
            if len(data) > 0:
                headers = list(data[0].keys())
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                for item in data:
                    row_data = list(item.values())
                    if row_filter == '':
                        self.add_row(row, row_data, table)
                        row += 1
                    else:
                        filter_param = row_filter.split('|')
                        filter_col_num = filter_param[0]
                        filter_col_text = filter_param[1]
                        filter_type = filter_param[2]
                        if str(row_data[int(filter_col_num)]) == str(filter_col_text):
                            if filter_type == 'INCLUDE':
                                self.add_row(row, row_data, table)
                                row += 1
                        else:
                            if filter_type == 'EXCLUDE':
                                self.add_row(row, row_data, table)
                                row += 1
            table.setRowCount(row)
            table.setSortingEnabled(True)
            table.resizeColumnsToContents()
            if msg_lbl != '':
                if len(data) == 0:
                    msg = "No results in table..."
                msg_lbl.setText(msg)

    def add_row(self, row, row_data, table, bgcol='', align=''):
        col = 0
        for cell_data in row_data:
            cell = QTableWidgetItem(str(cell_data))
            table.setItem(row,col,cell)
            if align == '':
                cell.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)  
            elif align == 'left':
                cell.setTextAlignment(Qt.AlignLeft|Qt.AlignVCenter)  
            elif align == 'right':
                cell.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)  
            if bgcol != '' :
                table.item(row,col).setBackground(bgcol)
            col += 1

    def colorize_row(self, table, row, bgcol):
        for col in range(table.columnCount()):
            table.item(row,col).setForeground(bgcol)

    def get_cell_val(self, table, row='', column=''):
        if row == '':
           row = table.currentRow() 
        if column == '':
           column = table.currentColumn() 
        if table.currentRow() != -1:
            if table.item(row,column).text() != '':
                return float(table.item(row,column).text())
            else:
                return 0
        else:
            return 0

    def find_in_table(self, table, text):
        for i in range(table.rowCount()):
            for j in range(table.columnCount()):
                if table.item(i,j) is not None:
                    if text == table.item(i,j).text():
                        return i,j
        return -1, -1

    # spinbox operations
    def binance_bid_price_update(self):
        selected_row = self.binance_depth_table_bid.currentRow()
        if selected_row != -1 and self.binance_depth_table_bid.item(selected_row,1) is not None:
            price = self.binance_depth_table_bid.item(selected_row,1).text()
            self.binance_price_spinbox.setValue(float(price))
            #self.binance_depth_table_ask.clearSelection()

    def binance_ask_price_update(self):
        selected_row = self.binance_depth_table_ask.currentRow()
        if selected_row != -1 and self.binance_depth_table_ask.item(selected_row,1) is not None:
            price = self.binance_depth_table_ask.item(selected_row,1).text()
            self.binance_price_spinbox.setValue(float(price))
            #self.binance_depth_table_bid.clearSelection()

    # Selection menu operations
    def update_combo(self,combo,options,selected):
        combo.clear()
        options.sort()
        combo.addItems(options)
        if selected in options:
            for i in range(combo.count()):
                if combo.itemText(i) == selected:
                    combo.setCurrentIndex(i)
        else:
            combo.setCurrentIndex(0)
            selected = combo.itemText(combo.currentIndex())
        return selected

    def get_base_rel_from_combos(self, base_combo, rel_combo, api='mm2'):
        base = ''
        base_index = base_combo.currentIndex()
        if base_index != -1:
            base = base_combo.itemText(base_index)
        rel = ''
        rel_index = rel_combo.currentIndex()
        if rel_index != -1:
            rel = rel_combo.itemText(rel_index)
        if api == 'mm2':
            active_coins_selection = self.active_coins[:]
            if len(active_coins_selection) > 0:
                rel = self.update_combo(rel_combo,active_coins_selection,rel)
                active_coins_selection.remove(rel)
                base = self.update_combo(base_combo,active_coins_selection,base)
        elif api == "Binance":
            base_coins_selection = list(set(list(binance_api.base_asset_info.keys())) & set(self.active_coins[:]))
            if len(base_coins_selection) > 0:                
                base = self.update_combo(base_combo,base_coins_selection,base)
                rel_coins_selection = binance_api.base_asset_info[base]['quote_assets']
                rel = self.update_combo(rel_combo,rel_coins_selection,rel)
        return base, rel

    def update_active(self):
        self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        for coin in self.gui_coins:
            if coin in self.active_coins:
                self.gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(78, 154, 6)")
            else:
                self.gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(52, 101, 164)")

    ## TABS ##
    def show_login_tab(self):
        self.stacked_login.setCurrentIndex(0)
        self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        self.username_input.setFocus()

    def show_activation_tab(self):
        self.update_active()
        self.update_activation_labels()
        self.update_activation_menu()

    def show_mm2_orderbook_tab(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            # get/populate coin combo box selections
            baserel = self.get_base_rel_from_combos(self.orderbook_sell_combo, self.orderbook_buy_combo, 'mm2')
            base = baserel[0]
            rel = baserel[1]
            # refresh tables
            self.populate_table("table/mm2_orderbook/"+rel+"/"+base, self.orderbook_table, self.orderbook_msg_lbl, "Click a row to buy "+rel+" from the Antara Marketmaker orderbook")
            self.update_mm2_orders_table()
            # Update labels
            self.update_mm2_orderbook_labels(base, rel)

    def show_binance_trading_tab(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            tickers = coinslib.binance_coins
            if tickers is not None:
                # wallet combobox
                self.update_combo(self.binance_asset_comboBox,tickers,tickers[0])
                # trade combobox
                baserel = self.get_base_rel_from_combos(self.binance_base_combo, self.binance_rel_combo, "Binance")
                base = baserel[0]
                rel = baserel[1]
                step_size = binance_api.base_asset_info[base]['stepSize']
                min_qty = binance_api.base_asset_info[base]['minQty']
                max_qty = binance_api.base_asset_info[base]['maxQty']
                self.binance_base_amount_spinbox.setSingleStep(float(step_size))
                self.binance_base_amount_spinbox.setRange(float(min_qty), float(max_qty))
                self.update_binance_depth_table()
                self.update_binance_orders_table()
                self.update_binance_labels(base, rel)

    def show_mm2_wallet_tab(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            self.wallet_recipient.setFocus()
            if self.wallet_combo.currentIndex() != -1:
                selected = self.wallet_combo.itemText(self.wallet_combo.currentIndex())
            else:
                selected = self.wallet_combo.itemText(0)
            self.update_combo(self.wallet_combo,self.active_coins,selected)
            self.update_mm2_wallet_labels()
            self.update_mm2_balance_table()

    def show_strategies_tab(self):
        self.update_strategies_table()
        self.populate_strategy_lists()

    def show_prices_tab(self):
        self.update_prices_table()
        self.update_price_history_graph()

    def show_history_tab(self):
        print('show_history_tab')
        self.update_mm2_trade_history_table()
        self.update_binance_trade_history_table()

    def show_config_tab(self):
        # populate credentials and config settings form fields
        if self.creds[0] != '':
            self.rpcpass_text_input.setText(self.creds[1])
            self.seed_text_input.setText(self.creds[2])
            self.netid_input.setValue(self.creds[3])
            self.rpc_ip_text_input.setText(self.creds[4])
            self.binance_key_text_input.setText(self.creds[5])
            self.binance_secret_text_input.setText(self.creds[6])
            self.countertrade_timeout_input.setValue(float(self.creds[9]))
            if self.creds[8] == "Marketmaker & Binance":
                self.bot_mode_comboBox.setCurrentIndex(1)
            else:
                self.bot_mode_comboBox.setCurrentIndex(0)

            if self.creds[4] == '127.0.0.1':
                self.checkbox_local_only.setChecked(True)
            else:
                self.checkbox_local_only.setChecked(False)

    def show_logs_tab(self):
        logfile='mm2_output.log'
        mm2_output = open(config_path+self.username+"_"+logfile,'r')
        with mm2_output as f:
            log_text = f.read()
            lines = f.readlines()
            self.scrollbar = self.console_logs.verticalScrollBar()
            self.console_logs.setStyleSheet("color: rgb(0, 0, 0); background-color: rgb(186, 189, 182);")
            self.console_logs.setPlainText(log_text)
            self.scrollbar.setValue(10000)

    ## LOGIN / ACTIVATE TAB FUNCTIONS
    def login(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        if self.username == '' or self.password == '' and not self.authenticated:
            QMessageBox.information(self, 'Login failed!', 'username and password fields can not be blank!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            self.decrypt_creds()
            if self.authenticated:   
                self.launch_mm2()
            elif self.username in settings.value('users'):
                QMessageBox.information(self, 'Login failed!', 'Incorrect username or password...', QMessageBox.Ok, QMessageBox.Ok)        
            else:
                resp = QMessageBox.information(self, 'User not found', 'Create new user?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if resp == QMessageBox.Yes:
                    settings.setValue('users', settings.value('users')+[self.username])
                    self.authenticated = True
                    self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))
                elif resp == QMessageBox.No:
                    QMessageBox.information(self, 'Login failed!', 'Incorrect username or password...', QMessageBox.Ok, QMessageBox.Ok)        

    def activate_coins(self):
        coins_to_activate = []
        autoactivate = []
        self.buy_coins = []
        self.sell_coins = []
        for coin in self.gui_coins:
            combo = self.gui_coins[coin]['combo']
            checkbox = self.gui_coins[coin]['checkbox']
            # update buy/sell and autoactivate lists.
            if checkbox.isChecked():
                autoactivate.append(coin)
                if coin not in self.active_coins:
                    coins_to_activate.append([coin,combo])
            if combo.itemText(combo.currentIndex()) == 'Buy':
                self.buy_coins.append(coin)
            elif combo.itemText(combo.currentIndex()) == 'Sell':
                self.sell_coins.append(coin)
            elif combo.itemText(combo.currentIndex()) == 'Buy/Sell':
                self.buy_coins.append(coin)
                self.sell_coins.append(coin)
            activate_list = {
                "autoactivate":autoactivate,
                "buy_coins":self.buy_coins,
                "sell_coins":self.sell_coins
            }
        with open(config_path+self.username+"_coins.json", 'w') as j:
            j.write(json.dumps(activate_list))
        # Activate selected coins in separate thread
        self.activate_thread = activation_thread(self.creds, coins_to_activate)
        self.activate_thread.activate.connect(self.update_active)
        self.activate_thread.start()
        # TODO: autoactivate coins needing kickstart
        print("Kickstart coins: "+str(rpclib.coins_needed_for_kick_start(self.creds[0], self.creds[1]).json()))
        self.show_activation_tab()

    def update_activation_labels(self):
        for coin in self.gui_coins:
            self.gui_coins[coin]['checkbox'].hide()
            coin_label_txt = coinslib.coin_api_codes[coin]['name']
            coin_label_api = ""
            if coinslib.coin_api_codes[coin]['binance_id'] != '':
                coin_label_api += "ᵇ"
            if coinslib.coin_api_codes[coin]['coingecko_id'] != '':
                coin_label_api += "ᵍ"
            if coinslib.coin_api_codes[coin]['paprika_id'] != '':
                coin_label_api += "ᵖ"
            if coin_label_api != "":
                coin_label_api = " ⁽"+coin_label_api+"⁾"
            self.gui_coins[coin]['checkbox'].setText(coin_label_txt+coin_label_api)

    def update_activation_menu(self):
        display_coins_erc20 = []
        display_coins_utxo = []
        display_coins_smartchain = []
        search_txt = self.search_activate.text().lower()
        for coin in self.gui_coins:
            self.gui_coins[coin]['combo'].hide()
            if coin.lower().find(search_txt) > -1 or self.gui_coins[coin]['checkbox'].text().lower().find(search_txt) > -1 or len(search_txt) == 0:
                if coinslib.coin_activation[coin]['type'] == 'utxo':
                    display_coins_utxo.append(coin)
                elif coinslib.coin_activation[coin]['type'] == 'erc20':
                    display_coins_erc20.append(coin)
                elif coinslib.coin_activation[coin]['type'] == 'smartchain':
                    display_coins_smartchain.append(coin)
            display_coins_erc20.sort()
            display_coins_utxo.sort()
            display_coins_smartchain.sort()
            self.populate_activation_menu(display_coins_smartchain, self.smartchains_layout)
            self.populate_activation_menu(display_coins_erc20, self.erc20_layout)
            self.populate_activation_menu(display_coins_utxo, self.utxo_layout)

    def populate_activation_menu(self, display_coins, layout):
        if os.path.exists(config_path+self.username+"_coins.json"):
            with open(config_path+self.username+"_coins.json", 'r') as j:
                user_coins = json.loads(j.read())
                user_autoactivate = user_coins['autoactivate']
                user_buy_coins = user_coins['buy_coins']
                user_sell_coins = user_coins['sell_coins']
        else:
            user_autoactivate = []
            user_buy_coins = []
            user_sell_coins = []

        row = 0
        for coin in display_coins:
            self.gui_coins[coin]['checkbox'].show()
            self.gui_coins[coin]['combo'].show()
            layout.addWidget(self.gui_coins[coin]['checkbox'], row, 0, 1, 1)
            layout.addWidget(self.gui_coins[coin]['combo'], row, 1, 1, 1)
            # set checkbox to ticked if in autoactivate list
            if coin in user_autoactivate:
                self.gui_coins[coin]['checkbox'].setChecked(True)
            else:
                self.gui_coins[coin]['checkbox'].setChecked(False)
            # set combobox value base on presence in user's buy / sell lists
            if coin in user_buy_coins and coin in user_sell_coins:
                self.gui_coins[coin]['combo'].setCurrentIndex(3)
            elif coin in user_buy_coins:
                self.gui_coins[coin]['combo'].setCurrentIndex(1)
            elif coin in user_sell_coins:
                self.gui_coins[coin]['combo'].setCurrentIndex(2)
            else:
                self.gui_coins[coin]['combo'].setCurrentIndex(0)
            # set icon
            icon = QIcon()
            icon.addPixmap(QPixmap(":/32/img/32/"+coin.lower()+".png"), QIcon.Normal, QIcon.Off)
            self.gui_coins[coin]['checkbox'].setIcon(icon)
            row += 1

    def select_all(self, state, cointype):
        for coin in self.gui_coins:
            if coinslib.coin_activation[coin]['type'] == cointype:
                self.gui_coins[coin]['checkbox'].setChecked(state)

    def select_all_smart(self):
        state = self.checkBox_all_smartchains.isChecked()
        self.select_all(state, 'smartchain')

    def select_all_erc20(self):
        state = self.checkBox_all_erc20.isChecked()
        self.select_all(state, 'erc20')

    def select_all_utxo(self):
        state = self.checkBox_all_utxo.isChecked()
        self.select_all(state, 'utxo')

    def select_all_api(self):
        filter_list = []
        if self.checkBox_binance_compatible_checkbox.isChecked():
            filter_list.append("ᵇ")
        if self.checkBox_gecko_compatible_checkbox.isChecked():
            filter_list.append("ᵍ")
        if self.checkBox_paprika_compatible_checkbox.isChecked():
            filter_list.append("ᵖ")
        for coin in self.gui_coins:
            include_coin = ['True']
            for apitype in filter_list:
                if self.gui_coins[coin]['checkbox'].text().find(apitype) != -1:
                    include_coin.append('True')
                else:
                    include_coin.append('False')
            if 'False' not in include_coin:
                self.gui_coins[coin]['checkbox'].setChecked(True)
            else:
                self.gui_coins[coin]['checkbox'].setChecked(False)

    ## MARKETMAKER TAB FUNCTIONS
    def update_mm2_balance_from_thread(self, bal_info):
        if 'coin' in bal_info:
            coin = bal_info['coin']
            address = bal_info['address']
            total = bal_info['balance']
            locked = bal_info['locked_by_swaps']
            available = float(bal_info['balance']) - float(bal_info['locked_by_swaps'])
            self.balances_data["mm2"].update({coin: {
                    "address":address,
                    "total":total,
                    "locked":locked,
                    "available":available,
                    }                
                })

    def update_mm2_balance_table(self): 
        self.clear_table(self.wallet_balances_table)
        self.wallet_balances_table.setSortingEnabled(False)
        row_count = len(self.active_coins)
        self.wallet_balances_table.setRowCount(row_count)
        row = 0
        usd_total = 0
        btc_total = 0
        for coin in self.active_coins:
            usd_val = '-'
            btc_val = '-'
            try:
                total = self.balances_data['mm2'][coin]['total']
                if coin in self.prices_data['average']:
                    usd_price = self.prices_data['average'][coin]['USD']
                    btc_price = self.prices_data['average'][coin]['BTC']
                    try:
                        usd_val = round(float(usd_price)*float(total),4)
                        btc_val = round(float(btc_price)*float(total),8)
                        usd_total += usd_val
                        btc_total += btc_val
                    except Exception as e:
                        # no float value for coin
                        pass
                balance_row = [coin, total, usd_val, btc_val]
                self.add_row(row, balance_row, self.wallet_balances_table)
                row += 1
            except Exception as e:
                print("mm2_bal_tbl err: "+str(e))
                balance_row = [coin, "-", '-', '-']
                self.add_row(row, balance_row, self.wallet_balances_table)
                row += 1
        self.wallet_usd_total.setText("Total USD Value: $"+str(round(usd_total,4)))
        self.wallet_btc_total.setText("Total BTC Value: "+str(round(btc_total,8)))
        self.wallet_balances_table.setSortingEnabled(True)
        self.wallet_balances_table.resizeColumnsToContents()
        self.wallet_balances_table.sortItems(3, Qt.DescendingOrder)

    def update_mm2_trades_table(self):
        swaps_info = rpclib.my_recent_swaps(self.creds[0], self.creds[1], limit=9999, from_uuid='').json()
        row = 0
        self.mm2_trades_table.setSortingEnabled(False)
        row_count = len(swaps_info['result']['swaps'])
        self.mm2_trades_table.setRowCount(row_count)
        for swap in swaps_info['result']['swaps']:
            for event in swap['events']:
                event_type = event['event']['type']
                if event_type in rpclib.error_events:
                    event_type = 'Failed'
                    break
            status = event_type
            role = swap['type']
            uuid = swap['uuid']
            my_amount = round(float(swap['my_info']['my_amount']),8)
            my_coin = swap['my_info']['my_coin']
            other_amount = round(float(swap['my_info']['other_amount']),8)
            other_coin = swap['my_info']['other_coin']
            started_at = datetime.datetime.fromtimestamp(round(swap['my_info']['started_at']/1000)*1000)
            if swap['type'] == 'Taker':
                buy_price = round(float(swap['my_info']['my_amount'])/float(swap['my_info']['other_amount']),8)
                sell_price = '-'
            else:
                buy_price = '-'
                sell_price = round(float(swap['my_info']['other_amount'])/float(swap['my_info']['my_amount']),8)
            trade_row = [started_at, role, status, other_coin, other_amount, buy_price, my_coin, my_amount, sell_price, uuid]
            self.add_row(row, trade_row, self.mm2_trades_table)
            row += 1
        self.mm2_trades_table.setSortingEnabled(True)
        self.mm2_trades_table.resizeColumnsToContents()

    def update_mm2_orders_table(self):
        self.populate_table("table/mm2_open_orders", self.mm2_orders_table, self.mm2_orders_msg_lbl, "Highlight a row to select for cancelling order")
        for row in range(self.mm2_orders_table.rowCount()):
            if self.mm2_orders_table.item(row, 10).text() != '0':
                self.colorize_row(self.mm2_orders_table, row, QColor(218, 255, 127))
            

    def update_mm2_orderbook_labels(self, base, rel):
        self.orderbook_buy_amount_lbl.setText(""+rel+" Buy Amount")
        self.orderbook_sell_amount_lbl.setText(""+base+" Sell Amount")
        self.orderbook_price_lbl.setText(""+rel+" Buy Price in "+base)
        self.orderbook_sell_bal_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+base.lower()+".png\"/></p></body></html>")
        self.orderbook_buy_bal_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+rel.lower()+".png\"/></p></body></html>")
        self.orderbook_send_order_btn.setText("Buy "+rel)
        if base in self.balances_data['mm2']:
            locked_text = round(float(self.balances_data['mm2'][base]['locked']),8)
            balance = round(float(self.balances_data['mm2'][base]['total']),8)
        else:
            locked_text = round(float(0),8)
            balance = round(float(0),8)
        self.orderbook_sell_balance_lbl.setText("Available: "+str(balance)+" "+base)
        self.orderbook_sell_locked_lbl.setText("Locked: "+str(locked_text)+" "+base)
        if rel in self.balances_data['mm2']:
            locked_text = round(float(self.balances_data['mm2'][rel]['locked']),8)
            balance = round(float(self.balances_data['mm2'][rel]['total']),8)
        else:
            locked_text = round(float(0),8)
            balance = round(float(0),8)
        self.orderbook_buy_balance_lbl.setText("Available: "+str(balance)+" "+rel)
        self.orderbook_buy_locked_lbl.setText("Locked: "+str(locked_text)+" "+rel)
        
    # Order form button slots
    def mm2_orderbook_get_price(self):
        print('get_price_from_orderbook')        
        selected_row = self.orderbook_table.currentRow()
        if selected_row != -1 and self.orderbook_table.item(selected_row,1) is not None:
            buy_coin = self.orderbook_table.item(selected_row,0).text()
            sell_coin = self.orderbook_table.item(selected_row,1).text()
            volume = self.orderbook_table.item(selected_row,2).text()
            price = self.orderbook_table.item(selected_row,3).text()
            self.orderbook_buy_price_spinbox.setValue(float(price))
            value = self.orderbook_table.item(selected_row,4).text()

    def mm2_orderbook_combo_box_switch(self):
        print('combo_box_switch')
        active_coins_selection = self.active_coins[:]
        index = self.orderbook_buy_combo.currentIndex()
        if index != -1:
            old_rel = self.orderbook_buy_combo.itemText(index)
        else:
            old_rel = ''
        index = self.orderbook_sell_combo.currentIndex()
        if index != -1:
            old_base = self.orderbook_sell_combo.itemText(index)
        else:
            old_base = ''
        if old_base == old_rel:
            old_base = ''
        rel = self.update_combo(self.orderbook_buy_combo,active_coins_selection,old_base)
        active_coins_selection.remove(rel)
        base = self.update_combo(self.orderbook_sell_combo,active_coins_selection,old_rel)
        self.orderbook_buy_price_spinbox.setValue(0)
        self.orderbook_buy_amount_spinbox.setValue(0)
        self.orderbook_sell_amount_spinbox.setValue(0)
        self.show_mm2_orderbook_tab()

    def mm2_orderbook_combo_box_change(self):
        self.orderbook_buy_price_spinbox.setValue(0)
        self.orderbook_buy_amount_spinbox.setValue(0)
        self.orderbook_sell_amount_spinbox.setValue(0)
        self.show_mm2_orderbook_tab()

    def mm2_orderbook_sell_pct(self, val):
        self.orderbook_sell_amount_spinbox.setValue(val)
        if self.orderbook_buy_price_spinbox.value() != 0:
            price = self.orderbook_buy_price_spinbox.value()
            self.orderbook_buy_amount_spinbox.setValue(val/price)

    def get_bal_pct(self, pct):
        bal = round(float(self.orderbook_sell_balance_lbl.text().split()[1]),8)
        return bal*pct/100

    def bal_25pct(self):
        val = self.get_bal_pct(25)
        self.mm2_orderbook_sell_pct(val)

    def bal_50pct(self):
        val = self.get_bal_pct(50)
        self.mm2_orderbook_sell_pct(val)

    def bal_75pct(self):
        val = self.get_bal_pct(75)
        self.mm2_orderbook_sell_pct(val)

    def bal_100pct(self):
        val = self.get_bal_pct(100)
        self.mm2_orderbook_sell_pct(val)

    # Dynamic order form price spinbox slots
    def update_mm2_orderbook_amounts(self, source=''):
        if source == '':
            sent_by = self.sender().objectName()
        else:
            sent_by = source
        print("update mm2 values amounts (source: "+sent_by+")")
        orderbook_price_val = self.orderbook_buy_price_spinbox.value()
        orderbook_sell_amount_val = self.orderbook_sell_amount_spinbox.value()
        orderbook_buy_amount_val = self.orderbook_buy_amount_spinbox.value()
        if sent_by == 'orderbook_buy_price_spinbox':
            if orderbook_price_val != 0:
                if orderbook_buy_amount_val != 0:
                    orderbook_sell_amount_val = orderbook_buy_amount_val*orderbook_price_val
                    self.orderbook_sell_amount_spinbox.setValue(orderbook_sell_amount_val)
                elif orderbook_sell_amount_val != 0:
                    orderbook_buy_amount_val = orderbook_sell_amount_val/orderbook_price_val
                    self.orderbook_buy_amount_spinbox.setValue(orderbook_buy_amount_val)
        elif sent_by == 'orderbook_sell_amount_spinbox':
            if orderbook_sell_amount_val != 0:
                if orderbook_price_val != 0:
                    orderbook_buy_amount_val = orderbook_sell_amount_val/orderbook_price_val
                    self.orderbook_buy_amount_spinbox.setValue(orderbook_buy_amount_val)
        elif sent_by == 'orderbook_buy_amount_spinbox':
            if orderbook_buy_amount_val != 0:
                if orderbook_price_val != 0:                
                    orderbook_sell_amount_val = orderbook_buy_amount_val*orderbook_price_val
                    self.orderbook_sell_amount_spinbox.setValue(orderbook_sell_amount_val)

    def mm2_orderbook_buy_price_changed(self):
        self.update_mm2_orderbook_amounts('orderbook_buy_price_spinbox')

    def mm2_orderbook_buy_amount_changed(self):
        self.update_mm2_orderbook_amounts('orderbook_buy_amount_spinbox')

    def mm2_orderbook_sell_amount_changed(self):
        self.update_mm2_orderbook_amounts('orderbook_sell_amount_spinbox')

    def mm2_orderbook_buy(self):
        index = self.orderbook_sell_combo.currentIndex()
        rel = self.orderbook_sell_combo.itemText(index)
        index = self.orderbook_buy_combo.currentIndex()
        base = self.orderbook_buy_combo.itemText(index)
        price = self.orderbook_buy_price_spinbox.value()
        vol = self.orderbook_buy_amount_spinbox.value()
        trade_val = round(float(price)*float(vol),8)
        resp = rpclib.buy(self.creds[0], self.creds[1], base, rel, vol, price).json()
        log_msg = "Buying "+str(vol)+" "+base +" for "+" "+str(trade_val)+" "+rel
        if 'error' in resp:
            if resp['error'].find("larger than available") > -1:
                msg = "Insufficient funds to complete order."
            else:
                msg = resp
        elif 'result' in resp:
            msg = "Order Submitted.\n"
            msg += "Buying "+str(vol)+" "+base +"\nfor\n"+" "+str(trade_val)+" "+rel
        else:
            msg = resp
        QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)
        self.update_trading_log('mm2', log_msg, str(resp))

    def mm2_view_order(self):
        cancel = True
        selected_row = self.mm2_orders_table.currentRow()
        if self.mm2_orders_table.item(selected_row,7) is not None:
            mm2_order_uuid = self.mm2_orders_table.item(selected_row,7).text()
            order_info = rpclib.order_status(self.creds[0], self.creds[1], mm2_order_uuid).json()
            result = ScrollMessageBox(order_info)
            result.exec_()
            #QMessageBox.information(self, 'MM2 Order Info', json.dumps(order_info, indent=4), QMessageBox.Ok, QMessageBox.Ok)

    def mm2_cancel_order(self):
        cancel = True
        selected_row = self.mm2_orders_table.currentRow()
        if self.mm2_orders_table.item(selected_row,7) is not None:
            mm2_order_uuid = self.mm2_orders_table.item(selected_row,7).text()
            order_info = rpclib.order_status(self.creds[0], self.creds[1], mm2_order_uuid).json()
            if len(order_info['order']['started_swaps']) != 0:
                swaps_in_progress = {}
                for swap_uuid in order_info['order']['started_swaps']:
                    swap_status = rpclib.my_swap_status(self.creds[0], self.creds[1], swap_uuid).json()
                    # TODO: Need an order with started swaps to test this further.
                    print(swap_status)
                if len(swaps_in_progress) != 0:
                    msg = "This order has swaps in progress, are you sure you want to cancel it?"
                    msg += "\nSwaps in progress: \n"
                    for swap in swaps_in_progress:
                        msg += swap+": "+swaps_in_progress[swap]
                    confirm = QMessageBox.question(self, 'Cancel Order', msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                    if confirm == QMessageBox.No:
                        cancel = False
                    elif confirm == QMessageBox.Cancel:
                        cancel = False
            if cancel:
                resp = rpclib.cancel_uuid(self.creds[0], self.creds[1], mm2_order_uuid).json()
                msg = ''
                if 'result' in resp:
                    if resp['result'] == 'success':
                        msg = "Order "+mm2_order_uuid+" cancelled"
                    else:
                        msg = resp
                else:
                    msg = resp
                log_msg = "Cancelling mm2 order "+mm2_order_uuid+"..."
                self.update_trading_log("mm2", log_msg, str(resp))
                QMessageBox.information(self, 'Order Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)
        self.show_mm2_orderbook_tab()

    def mm2_cancel_all_orders(self):
        pending = 0
        cancel = True
        if self.mm2_trades_table.rowCount() != 0:
            for i in range(self.mm2_trades_table.rowCount()):
                if self.mm2_trades_table.item(i,2).text() != 'Finished' and self.mm2_trades_table.item(i,2).text() != 'Failed':
                    print(self.mm2_trades_table.item(i,2).text())
                    pending += 1
            if pending > 0:
                msg = str(pending)+" order(s) have swaps in progress, are you sure you want to cancel all?"
                confirm = QMessageBox.question(self, 'Confirm Cancel Orders', msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                if confirm == QMessageBox.No:
                    cancel = False
                elif confirm == QMessageBox.Cancel:
                    cancel = False
            if cancel:
                resp = rpclib.cancel_all(self.creds[0], self.creds[1]).json()
                msg = ''
                if 'result' in resp:
                    if resp['result'] == 'success':
                        msg = "All your mm2 orders have been cancelled"
                    else:
                        msg = resp
                else:
                    msg = resp
                log_msg = "Cancelling all mm2 orders..."
                QMessageBox.information(self, 'MM2 Orders Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)
                self.update_trading_log("mm2", log_msg, str(resp))
        else:
            QMessageBox.information(self, 'Order Cancelled', 'You have no orders!', QMessageBox.Ok, QMessageBox.Ok)
        self.show_mm2_orderbook_tab()
   
    ## Binance Tab
    def bn_update_balance_from_thread(self, bal_info):
        print('bn update_balance_from_thread')
        for coin in bal_info:
            total = bal_info[coin]['total']
            locked = bal_info[coin]['locked']
            available = bal_info[coin]['available']
            self.balances_data["Binance"].update({coin: {
                    "total":total,
                    "locked":locked,
                    "available":available,
                    "address":"Loading...",
                    }                
                })

    def binance_combo_box_change(self):
        self.binance_price_spinbox.setValue(0)
        self.binance_base_amount_spinbox.setValue(0)
        self.binance_quote_amount_spinbox.setValue(0)
        self.show_binance_trading_tab()

    def update_binance_labels(self, base, rel):
        # Quote coin icon and balances
        self.binance_quote_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+rel.lower()+".png\"/></p></body></html>")
        if rel in self.balances_data["Binance"]:
            locked_text = "Locked: "+str(round(float(self.balances_data["Binance"][rel]['locked']),8))
            balance = "Balance: "+str(round(float(self.balances_data["Binance"][rel]['total']),8))
        else:
            locked_text = ""
            balance = "loading balance..."
        self.binance_quote_balance_lbl.setText(balance)
        self.binance_quote_locked_lbl.setText(locked_text)
        # Base coin icon and balances
        self.binance_base_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+base.lower()+".png\"/></p></body></html>")
        if base in self.balances_data["Binance"]:
            locked_text = "Locked: "+str(round(float(self.balances_data["Binance"][base]['locked']),8))
            balance = "Balance: "+str(round(float(self.balances_data["Binance"][base]['total']),8))
        else:
            locked_text = ""
            balance = "loading balance..."
        self.binance_base_balance_lbl.setText(balance)
        self.binance_base_locked_lbl.setText(locked_text)
        self.update_binance_addr()

    def update_binance_wallet(self):
        selected_row = self.binance_balances_table.currentRow()
        if selected_row != -1 and self.binance_balances_table.item(selected_row,0) is not None:
            coin = self.binance_balances_table.item(selected_row,0).text()
            self.update_combo(self.binance_asset_comboBox,coinslib.binance_coins,coin)
            self.update_binance_addr()

    def update_binance_addr(self):
        # TODO: Isn't this cached?
        # Wallet address
        index = self.binance_asset_comboBox.currentIndex()
        coin = self.binance_asset_comboBox.itemText(index)
        resp = binance_api.get_deposit_addr(self.creds[5], self.creds[6], coin)
        if 'address' in resp:
            addr_text = resp['address']
        else:
            addr_text = 'Address not found - create it at Binance.com'
        self.binance_addr_lbl.setText(addr_text)
        self.binance_addr_coin_lbl.setText("Binance "+str(coin)+" Address")

    def update_binance_orders_table(self):
        print('update_binance_orders_table')
        # populate binance depth table
        self.populate_table("table/binance_open_orders", self.binance_orders_table, self.binance_orders_msg_lbl, "")

    def show_qr_popup(self):
        # create popup for Binance address QR code
        coin = self.binance_addr_coin_lbl.text().split()[1]
        addr_txt = self.binance_addr_lbl.text()
        qr_img = qrcode.make(addr_txt, image_factory=QR_image)
        self.qr_lbl = QLabel(self)
        self.qr_lbl.setText(addr_txt)
        self.qr_img_lbl = QLabel(self)
        self.qr_img_lbl.setPixmap(qr_img.pixmap())
        msgBox = QMessageBox(QMessageBox.NoIcon, "Binance "+coin+" Address QR Code ", addr_txt)
        l = msgBox.layout()
        l.addWidget(self.qr_img_lbl,0, 0, 1, l.columnCount(), Qt.AlignCenter)
        l.addWidget(self.qr_lbl,1, 0, 1, l.columnCount(), Qt.AlignCenter)
        msgBox.addButton("Close", QMessageBox.NoRole)
        print("show Binance QR code msgbox")
        msgBox.exec()

    def update_binance_balance_table(self):
        self.clear_table(self.binance_balances_table)
        row_count = len(self.balances_data["Binance"])
        self.binance_balances_table.setRowCount(row_count)
        self.binance_balances_table.setSortingEnabled(False)
        row = 0
        if row_count == 0:
            self.binance_balances_msg_lbl.setText('Balances loading...')
        else:
            self.binance_balances_msg_lbl.setText('')
            for coin in self.balances_data["Binance"]:
                available = float(self.balances_data["Binance"][coin]['available'])
                total = float(self.balances_data["Binance"][coin]['total'])
                locked = float(self.balances_data["Binance"][coin]['locked'])
                balance_row = [coin, total, available, locked]
                self.add_row(row, balance_row, self.binance_balances_table)
                row += 1
        self.binance_balances_table.setSortingEnabled(True)
        self.binance_balances_table.sortItems(1, Qt.DescendingOrder)
        self.binance_balances_table.resizeColumnsToContents()

    def update_binance_depth_table(self):
        index = self.binance_base_combo.currentIndex()
        base = self.binance_base_combo.itemText(index)
        index = self.binance_rel_combo.currentIndex()
        rel = self.binance_rel_combo.itemText(index)
        self.binance_price_spinbox.setValue(0)
        self.binance_price_lbl.setText("Price ("+rel+" per "+base+")")
        self.binance_base_amount_lbl.setText("Amount ("+base+")")
        self.binance_quote_amount_lbl.setText("Amount ("+rel+")")
        ticker_pair = base+rel
        # populate binance depth table
        self.populate_table("table/get_binance_depth/"+ticker_pair,
                            self.binance_depth_table_bid,
                            "",
                            "",
                            "3|Bid|INCLUDE")
        self.populate_table("table/get_binance_depth/"+ticker_pair,
                            self.binance_depth_table_ask,
                            "",
                            "",
                            "3|Ask|INCLUDE")
        # apply BG color
        for row in range(self.binance_depth_table_ask.rowCount()):
            if self.binance_depth_table_ask.item(row,3) is not None:
                bgcol = QColor(164, 0, 0)
                for col in range(self.binance_depth_table_ask.columnCount()):
                    self.binance_depth_table_ask.item(row,col).setBackground(bgcol)

        for row in range(self.binance_depth_table_bid.rowCount()):
            if self.binance_depth_table_bid.item(row,3) is not None:
                bgcol = QColor(78, 154, 6)
                for col in range(self.binance_depth_table_bid.columnCount()):
                    self.binance_depth_table_bid.item(row,col).setBackground(bgcol)
        # update button text
        self.binance_sell_btn.setText("Sell "+base)
        self.binance_buy_btn.setText("Buy "+base)

    def update_binance_price_val(self):
        # sets trade price to selected/clicked row on depth tables
        selected_row = self.binance_depth_table.currentRow()
        price = self.binance_depth_table.item(selected_row,1).text()
        order_type = self.binance_depth_table.item(selected_row,3).text()
        self.binance_price_spinbox.setValue(float(price))

    # Dynamic order form price spinbox slots
    def update_binance_orderbook_amounts(self, source=''):
        if source == '':
            sent_by = self.sender().objectName()
        else:
            sent_by = source
        print("update binance values amounts (source: "+sent_by+")")
        index = self.binance_base_combo.currentIndex()
        baseAsset = self.binance_base_combo.itemText(index)
        index = self.binance_rel_combo.currentIndex()
        quoteAsset = self.binance_rel_combo.itemText(index)
        symbol = baseAsset+quoteAsset
        price_val = self.binance_price_spinbox.value()
        quote_amount_val = self.binance_quote_amount_spinbox.value()
        base_amount_val = self.binance_base_amount_spinbox.value()
        if sent_by == 'binance_price_spinbox':
            if price_val != 0:
                if base_amount_val != 0:
                    quote_amount_val = base_amount_val*price_val
                    self.binance_quote_amount_spinbox.setValue(quote_amount_val)
                elif quote_amount_val != 0:
                    base_amount_val = binance_api.round_to_step(symbol, quote_amount_val/price_val)
                    self.binance_base_amount_spinbox.setValue(base_amount_val)
        elif sent_by == 'binance_quote_amount_spinbox':
            if quote_amount_val != 0:
                if price_val != 0:
                    base_amount_val = binance_api.round_to_step(symbol, quote_amount_val/price_val)
                    self.binance_base_amount_spinbox.setValue(base_amount_val)
        elif sent_by == 'binance_base_amount_spinbox':
            if base_amount_val != 0:
                if price_val != 0:                
                    quote_amount_val = base_amount_val*price_val
                    self.binance_quote_amount_spinbox.setValue(quote_amount_val)

    def binance_price_changed(self):
        self.update_binance_orderbook_amounts('binance_price_spinbox')

    def binance_quote_amount_changed(self):
        self.update_binance_orderbook_amounts('binance_quote_amount_spinbox')

    def binance_base_amount_changed(self):
        self.update_binance_orderbook_amounts('binance_base_amount_spinbox')

    def binance_buy(self):
        qty = '{:.8f}'.format(self.binance_base_amount_spinbox.value())
        quote_qty = '{:.8f}'.format(self.binance_quote_amount_spinbox.value())
        price = '{:.8f}'.format(self.binance_price_spinbox.value())
        index = self.binance_base_combo.currentIndex()
        baseAsset = self.binance_base_combo.itemText(index)
        index = self.binance_rel_combo.currentIndex()
        quoteAsset = self.binance_rel_combo.itemText(index)
        symbol = baseAsset+quoteAsset
        print(binance_api.binance_pair_info[symbol])
        min_notional = float(binance_api.binance_pair_info[symbol]['minNotional'])
        if float(quote_qty) < min_notional:
            QMessageBox.information(self, 'Buy Order Failed', "Trade value must be over "+str(min_notional)+" "+quoteAsset, QMessageBox.Ok, QMessageBox.Ok)
        else:
            resp = binance_api.create_buy_order(self.creds[5], self.creds[6], symbol, qty, price)
            log_msg = "Buy order submitted! "+str(qty)+" "+baseAsset+" at "+str(price)+" "+quoteAsset+" (Total: "+str(float(qty)*float(price))+" "+quoteAsset+")"
            if 'orderId' in resp:
                msg = "Buy order submitted!\n "+str(qty)+" "+baseAsset+" at "+str(price)+" "+quoteAsset+"\nTotal: "+str(float(qty)*float(price))+" "+quoteAsset
                QMessageBox.information(self, 'Buy Order Sent', msg, QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, 'Buy Order Failed', str(resp), QMessageBox.Ok, QMessageBox.Ok)
            self.update_trading_log('Binance', log_msg, str(resp))
        self.update_binance_orders_table()

    def binance_sell(self):
        qty = '{:.8f}'.format(self.binance_base_amount_spinbox.value())
        quote_qty = '{:.8f}'.format(self.binance_quote_amount_spinbox.value())
        price = '{:.8f}'.format(self.binance_price_spinbox.value())
        index = self.binance_base_combo.currentIndex()
        baseAsset = self.binance_base_combo.itemText(index)
        index = self.binance_rel_combo.currentIndex()
        quoteAsset = self.binance_rel_combo.itemText(index)
        symbol = baseAsset+quoteAsset
        min_notional = binance_api.binance_pair_info[symbol]['minNotional']
        if float(quote_qty) < float(min_notional):
            QMessageBox.information(self, 'Buy Order Failed', "Trade value must be over "+str(min_notional)+" "+quoteAsset, QMessageBox.Ok, QMessageBox.Ok)
        else:
            resp = binance_api.create_sell_order(self.creds[5], self.creds[6], symbol, qty, price)
            log_msg = "Sell order submitted! "+str(qty)+" "+baseAsset+" at "+str(price)+" "+quoteAsset+" (Total: "+str(float(qty)*float(price))+" "+quoteAsset+")"
            if 'orderId' in resp:
                msg = "Sell order submitted!\n "+str(qty)+" "+baseAsset+" at "+str(price)+" "+quoteAsset+"\nTotal: "+str(float(qty)*float(price))+" "+quoteAsset
                QMessageBox.information(self, 'Sell Order Sent', msg, QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, 'Sell Order Failed', str(resp), QMessageBox.Ok, QMessageBox.Ok)
            self.update_trading_log('Binance', log_msg, str(resp))
        self.update_binance_orders_table()

    

    def binance_withdraw(self):
        index = self.binance_asset_comboBox.currentIndex()
        coin = self.binance_asset_comboBox.itemText(index)
        addr = self.binance_withdraw_addr_lineEdit.text()
        amount = self.binance_withdraw_amount_spinbox.value()
        msg = ''
        confirm_msg = 'Confirm withdraw:\n\n'
        confirm_msg += str(amount)+' '+coin+' to '+addr+'\n\n'
        confirm_msg += "Check https://www.binance.com/en/fee/schedule for withdrawl fee details\n\n"
        confirm = QMessageBox.question(self, "Confirm withdraw?", confirm_msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
        if confirm == QMessageBox.Yes:
            proceed = True
        else:
            proceed = False
        if proceed:
            resp = binance_api.withdraw(self.creds[5], self.creds[6], coin, addr, amount)
            if 'id' in resp:
                txid = resp['id']
                msg += "Sent!\n"
            else:
                msg += str(resp)
            QMessageBox.information(self, 'Binance Withdraw', str(msg), QMessageBox.Ok, QMessageBox.Ok)

    def binance_cancel_selected_order(self):
        selected_row = self.binance_orders_table.currentRow()
        if self.binance_orders_table.item(selected_row,0) is not None:
            order_id = self.binance_orders_table.item(selected_row,0).text()
            ticker_pair = self.binance_orders_table.item(selected_row,2).text()
            resp = binance_api.delete_order(self.creds[5], self.creds[6], ticker_pair, order_id)
            msg = ''
            if "status" in resp:
                if resp["status"] == "CANCELED":
                    msg = "Order "+order_id+" cancelled"
                else:
                    msg = resp
            else:
                msg = resp
            log_msg = "Cancelling Binance order "+str(order_id)+" ("+ticker_pair+")"
            self.update_trading_log("Binance", log_msg, str(resp))
            QMessageBox.information(self, 'Order Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)      
        else:
            QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        self.update_binance_orders_table()

    def binance_cancel_all_orders(self):
        open_orders = binance_api.get_open_orders(self.creds[5], self.creds[6])
        order_ids = []
        for item in open_orders:
            order_ids.append([item['orderId'],item['symbol']])
        for order_id in order_ids:
            resp = binance_api.delete_order(self.creds[5], self.creds[6], order_id[1], order_id[0])
            log_msg = "Cancelling Binance order "+str(order_id[0])+" ("+order_id[1]+")"
            self.update_trading_log("Binance", log_msg, str(resp))
            time.sleep(0.05)
            self.update_binance_orders_table()
        QMessageBox.information(self, 'Order Cancelled', 'All orders cancelled!', QMessageBox.Ok, QMessageBox.Ok)

    ## Prices Tab
    def update_price_history_graph(self):
        print("update_price_history_graph")
        index = self.history_quote_combobox.currentIndex()
        if index == -1:
            index = 0
        quote = self.history_quote_combobox.itemText(index)

        index = self.history_coin_combobox.currentIndex()
        if index == -1:
            coin = self.update_combo(self.history_coin_combobox,coinslib.paprika_coins,0)
        else:
            coin = self.history_coin_combobox.itemText(index)
        coin_id = coinslib.coin_api_codes[coin]['paprika_id']
        self.draw_graph_thread = graph_history_thread(coin ,coin_id, quote)
        self.draw_graph_thread.get_history.connect(self.draw_price_history_graph)
        self.draw_graph_thread.start()
        # activate "loading" overlay

    def draw_price_history_graph(self, coin, quote, x, y, time_ticks):
        # deactivate "loading" overlay
        
        print('drawing graph')
        self.binance_history_graph.clear()
        price_curve = self.binance_history_graph.plot(
                x,
                y, 
                pen={'color':(78,155,46)},
                fillLevel=0, brush=(50,50,200,100),
            )
        self.binance_history_graph.setXRange(min(x),max(x), padding=0)
        self.binance_history_graph.setYRange(0,max(y)*1.1, padding=0)
        self.binance_history_graph.addItem(price_curve)
        if quote == 'USD':
            self.binance_history_graph.setLabel('left', '$USD')
        elif quote == 'KMD':
            self.binance_history_graph.setLabel('left', 'KMD')
        else:
            self.binance_history_graph.setLabel('left', 'BTC')
        self.binance_history_graph.setLabel('bottom', '', units=None)
        self.binance_history_graph.showGrid(x=True, y=True, alpha=0.2)
        price_ticks = self.binance_history_graph.getAxis('left')
        date_ticks = self.binance_history_graph.getAxis('bottom')    
        date_ticks.setTicks([time_ticks])
        date_ticks.enableAutoSIPrefix(enable=False)
        self.binance_history_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+coin.lower()+".png\"/></p></body></html>")
        if coin in self.prices_data:
            usd_price = self.prices_data['average'][coin]['USD']
            btc_price = self.prices_data['average'][coin]['BTC']
        elif coinslib.coin_api_codes[coin]['paprika_id'] != '':
            price = priceslib.get_paprika_price(coinslib.coin_api_codes[coin]['paprika_id']).json()
            usd_price = float(price['price_usd'])
            btc_price = float(price['price_btc'])
        elif coinslib.coin_api_codes[coin]['coingecko_id'] != '':
            coin_id = coinslib.coin_api_codes[self.coin]['coingecko_id']
            price = priceslib.gecko_fiat_prices(coinslib.coin_api_codes[coin]['coingecko_id'], 'usd,btc').json()
            usd_price = float(price[coin_id]['usd'])
            btc_price = float(price[coin_id]['btc'])
        else:
            usd_price = 'No Data'
            btc_price = 'No Data'
        if quote == 'USD':
            txt='<div style="text-align: center"><span style="color: #FFF;font-size:10pt;">Current USD Price: $'+str(usd_price)+'</span></div>'
        if quote == 'KMD':
            kmd_price = priceslib.get_paprika_price(coinslib.coin_api_codes['KMD']['paprika_id']).json()['price_btc']
            kmd_price = float(btc_price)/float(kmd_price)
            txt='<div style="text-align: center"><span style="color: #FFF;font-size:10pt;">Current KMD Price: '+str(kmd_price)+'</span></div>'
        else:
            txt='<div style="text-align: center"><span style="color: #FFF;font-size:10pt;">Current BTC Price: $'+str(btc_price)+'</span></div>'
        text = pg.TextItem(html=txt, anchor=(0,0), border='w', fill=(0, 0, 255, 100))
        self.binance_history_graph.addItem(text)
        text.setPos(min(x)+(max(x)-min(x))*0.02,max(y))

    ## WALLET TAB
    def update_mm2_wallet_from_thread(self, bal_info):
        coin = bal_info['coin']
        address = bal_info['address']
        total = bal_info['balance']
        locked = bal_info['locked_by_swaps']
        available = float(bal_info['balance']) - float(bal_info['locked_by_swaps'])
        self.balances_data["mm2"].update({coin: {
                "address":address,
                "total":total,
                "locked":locked,
                "available":available,
                }                
            })
        if coin != '' and address != '':
            self.update_mm2_wallet_labels()

    def update_mm2_wallet_labels(self):
        index = self.wallet_combo.currentIndex()
        if index != -1:
            coin = self.wallet_combo.itemText(index)
            self.wallet_coin_img.setText("<html><head/><body><p><img src=\":/300/img/300/"+coin.lower()+".png\"/></p></body></html>")
            if coin in self.balances_data["mm2"]:
                address = self.balances_data["mm2"][coin]["address"]
                total = self.balances_data["mm2"][coin]["total"]
                locked = self.balances_data["mm2"][coin]["locked"]
                available = self.balances_data["mm2"][coin]["available"]
                if coinslib.coin_explorers[coin]['addr_explorer'] != '':
                    self.wallet_address.setText("<a href='"+coinslib.coin_explorers[coin]['addr_explorer']+"/"+address+"'><span style='text-decoration: underline; color:#eeeeec;'>"+address+"</span></href>")
                else:
                    self.wallet_address.setText(address)            
                self.wallet_balance.setText(total)
                self.wallet_locked_by_swaps.setText("locked by swaps: "+str(locked))
                # TODO: add value in KMD
                if coin in self.prices_data['average']:
                    usd_price = self.prices_data['average'][coin]['USD']
                    btc_price = self.prices_data['average'][coin]['BTC']
                    try:
                        usd_val = round(float(usd_price)*float(total),4)
                        btc_val = round(float(btc_price)*float(total),8)
                        self.wallet_usd_value.setText("$"+str(usd_val)+" USD")
                        self.wallet_btc_value.setText(str(btc_val)+" BTC")
                    except Exception as e:
                        print('update wallet labels err')
                        print(e)
                        self.wallet_btc_value.setText("")
                        self.wallet_usd_value.setText("")
                        pass
                else:
                    print('no price data for '+coin)
                    self.wallet_btc_value.setText("")
                    self.wallet_usd_value.setText("")

    def show_mm2_qr_popup(self):
        index = self.wallet_combo.currentIndex()
        coin = self.wallet_combo.itemText(index)
        addr_txt = self.wallet_address.text()
        qr_img = qrcode.make(addr_txt, image_factory=QR_image)
        self.qr_lbl = QLabel(self)
        self.qr_lbl.setText(addr_txt)
        self.qr_img_lbl = QLabel(self)
        self.qr_img_lbl.setPixmap(qr_img.pixmap())
        msgBox = QMessageBox(QMessageBox.NoIcon, "MM2 "+coin+" Address QR Code ", addr_txt)
        l = msgBox.layout()
        l.addWidget(self.qr_img_lbl,0, 0, 1, l.columnCount(), Qt.AlignCenter)
        l.addWidget(self.qr_lbl,1, 0, 1, l.columnCount(), Qt.AlignCenter)
        msgBox.addButton("Close", QMessageBox.NoRole)
        msgBox.exec()

    def select_wallet_from_table(self):
        selected_row = self.wallet_balances_table.currentRow()
        if selected_row != -1 and self.wallet_balances_table.item(selected_row,0) is not None:
            coin = self.wallet_balances_table.item(selected_row,0).text()
            self.wallet_balances_table.setRangeSelected(QTableWidgetSelectionRange(selected_row, 0, selected_row, 3), False)
            self.update_combo(self.wallet_combo,self.active_coins,coin)
            self.show_mm2_wallet_tab()

    # process withdrawl from wallet tab
    def send_funds(self):
        index = self.wallet_combo.currentIndex()
        cointag = self.wallet_combo.itemText(index)
        recipient_addr = self.wallet_recipient.text()
        amount = self.wallet_amount.text()
        confirm = QMessageBox.question(self, 'Confirm send?', "Confirm sending "+str(amount)+" "+cointag+" to "+recipient_addr+"?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            msg = ''
            resp = rpclib.withdraw(self.creds[0], self.creds[1], cointag, recipient_addr, amount).json()
            if 'error' in resp:
                print(resp['error'])
                if resp['error'].find("Invalid Address!") > -1:
                    msg += "Invalid Address"
                elif resp['error'].find("Not sufficient balance!") > -1:
                    msg += "Insufficient balance"
                elif resp['error'].find("less than dust amount") > -1:
                    msg += "Transaction value too small!"
                else:
                    msg = str(resp['error'])
            elif 'tx_hex' in resp:
                raw_hex = resp['tx_hex']
                resp = rpclib.send_raw_transaction(self.creds[0], self.creds[1], cointag, raw_hex).json()
                # hyperlink tx in explorer if url in coinslib
                if 'tx_hash' in resp:
                    txid = resp['tx_hash']
                    if recipient_addr.startswith('0x'):
                        txid_str = '0x'+txid
                    else:
                        txid_str = txid
                    if coinslib.coin_explorers[cointag]['tx_explorer'] != '':
                        msg = "Sent! \n<a href='"+coinslib.coin_explorers[cointag]['tx_explorer']+"/"+txid_str+"'>[Link to block explorer]</a>"
                    else:
                        msg = "Sent! \nTXID: ["+txid_str+"]"
                self.wallet_recipient.setText("")
                self.wallet_amount.setValue(0)
            else:
                msg = str(resp)
            QMessageBox.information(self, 'Wallet transaction', msg, QMessageBox.Ok, QMessageBox.Ok)
            balance_info = self.balances_data['mm2'][cointag]
            print(balance_info)
            if 'address' in balance_info:
                address = balance_info['address']
                balance = round(float(balance_info['balance']),8)
                locked = round(float(balance_info['locked']),8)
                available_balance = round(float(balance_info['available']),8)
                self.wallet_balance.setText(str(balance_text))
            self.update_mm2_wallet_labels()

    ## STRATEGIES TAB
    def populate_strategy_lists(self):
        self.strat_buy_list.clear()
        self.strat_sell_list.clear()
        self.strat_cex_list.clear()
        for item in self.active_coins:
            buy_list_item = QListWidgetItem(item)
            buy_list_item.setTextAlignment(Qt.AlignHCenter)
            self.strat_buy_list.addItem(buy_list_item)
            sell_list_item = QListWidgetItem(item)
            sell_list_item.setTextAlignment(Qt.AlignHCenter)
            self.strat_sell_list.addItem(sell_list_item)
        cex_list = requests.get('http://127.0.0.1:8000/cex/list').json()['cex_list']
        for item in cex_list:
            list_item = QListWidgetItem(item)
            list_item.setTextAlignment(Qt.AlignHCenter)
            self.strat_cex_list.addItem(list_item)

    def update_strategies_table(self):
        self.populate_table("table/bot_strategies", self.strategies_table, self.strategies_msg_lbl, "Highlight a row to view strategy trade summary")
        for row in range(self.strategies_table.rowCount()):
            if self.strategies_table.item(row, 10).text() == 'active':
                self.colorize_row(self.strategies_table, row, QColor(218, 255, 127))
            elif self.strategies_table.item(row, 10).text() != 'inactive':
                self.colorize_row(self.strategies_table, row, QColor(255, 233, 127))
        self.strategies_table.clearSelection()

    def create_strat(self):
        params = 'name='+self.strat_name.text()
        index = self.strat_type_combo.currentIndex()
        strat_type = self.strat_type_combo.itemText(index)
        params += '&strategy_type='+strat_type
        buy_list = []
        for item in self.strat_buy_list.selectedItems():
            buy_list.append(item.text())
        sell_list = []
        for item in self.strat_sell_list.selectedItems():
            sell_list.append(item.text())
        cex_list = []
        for item in self.strat_cex_list.selectedItems():
            cex_list.append(item.text())
        buy_items = ','.join(buy_list)
        sell_items = ','.join(sell_list)
        cex_items = ','.join(cex_list)
        params += '&sell_list='+sell_items
        params += '&buy_list='+buy_items
        params += '&margin='+str(self.strat_margin_spinbox.value())
        params += '&refresh_interval='+str(self.strat_refresh_spinbox.value())
        params += '&balances_pct='+str(self.strat_bal_pct_spinbox.value())
        params += '&cex_list='+cex_items
        print('http://127.0.0.1:8000/strategies/create?'+params)
        resp = requests.post('http://127.0.0.1:8000/strategies/create?'+params).json()
        QMessageBox.information(self, 'Create Bot Strategy', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.show_strategies_tab()


    def start_strat(self):
        selected_row = self.strategies_table.currentRow()
        if selected_row != -1 and self.strategies_table.item(selected_row,0) is not None:
            strategy_name = self.strategies_table.item(selected_row,0).text()
            resp = requests.post('http://127.0.0.1:8000/strategies/start/'+strategy_name).json()
        else:
            resp = {
                "response": "error",
                "message": "No strategy row selected!"
            }
        QMessageBox.information(self, 'Strategy '+strategy_name+' started', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.update_strategies_table()

    def stop_strat(self):
        selected_row = self.strategies_table.currentRow()
        if selected_row != -1 and self.strategies_table.item(selected_row,0) is not None:
            strategy_name = self.strategies_table.item(selected_row,0).text()
            resp = requests.post('http://127.0.0.1:8000/strategies/stop/'+strategy_name).json()
            QMessageBox.information(self, 'Strategy '+strategy_name+' stopped', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        else:
            resp = {
                "response": "error",
                "message": "No strategy row selected!"
            }
            QMessageBox.information(self, 'Strategy stop error', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.update_strategies_table()

    def stop_all_strats(self):
        resp = requests.post('http://127.0.0.1:8000/strategies/stop/all').json()

    def view_strat_session(self):
        selected_row = self.strat_summary_table.currentRow()
        if self.strat_summary_table.item(selected_row,1) is not None:
            session_num = self.strat_summary_table.item(selected_row,1).text()
            session_name = self.strat_summary_table.item(selected_row,0).text()
            session_info = requests.post('http://127.0.0.1:8000/strategies/session/'+session_name+'/'+session_num).json()
            result = ScrollMessageBox(session_info)
            result.exec_()

    def view_strat_summary(self):
        selected_row = self.strategies_table.currentRow()
        if selected_row != -1 and self.strategies_table.item(selected_row,0) is not None:
            strategy_name = self.strategies_table.item(selected_row,0).text()
            if self.summary_hide_empty_checkbox.isChecked():
                self.populate_table("table/bot_strategy/summary/"+strategy_name, self.strat_summary_table, "", "", "4|0|EXCLUDE")
            else:
                self.populate_table("table/bot_strategy/summary/"+strategy_name, self.strat_summary_table)
            for row in range(self.strat_summary_table.rowCount()):
                if self.strat_summary_table.item(row, 4).text() != '0':
                    self.colorize_row(self.strat_summary_table, row, QColor(218, 255, 127))

    def delete_strat(self):
        selected_row = self.strategies_table.currentRow()
        if selected_row != -1 and self.strategies_table.item(selected_row,0) is not None:
            strategy_name = self.strategies_table.item(selected_row,0).text()
            resp = requests.post('http://127.0.0.1:8000/strategies/delete/'+strategy_name).json()
        else:
            resp = {
                "response": "error",
                "message": "No strategy row selected!"
            }
        QMessageBox.information(self, 'Archive Bot Strategy', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.update_strategies_table()

    ## HISTORY
    def mm2_view_swap(self):
        cancel = True
        selected_row = self.mm2_trades_table.currentRow()
        if self.mm2_trades_table.item(selected_row,10) is not None:
            swap_uuid = self.mm2_trades_table.item(selected_row,10).text()
            swap_info = rpclib.my_swap_status(self.creds[0], self.creds[1], swap_uuid).json()
            result = ScrollMessageBox(swap_info)
            result.exec_()

    ## CONFIG
    def set_localonly(self):
        # TODO: should this just be default, without remote option?
        local_only = self.checkbox_local_only.isChecked()
        if local_only:
            rpc_ip = '127.0.0.1'
            self.rpc_ip_text_input.setReadOnly(True)
            self.rpc_ip_text_input.setText(rpc_ip)
        else:
            self.rpc_ip_text_input.setReadOnly(False)

    def save_config(self):
        # update user config and credentials
        msg = ''
        gui = 'Makerbot v0.0.1'
        passphrase = self.seed_text_input.toPlainText()
        rpc_password = self.rpcpass_text_input.text()
        rpc_ip = self.rpc_ip_text_input.text()
        local_only = self.checkbox_local_only.isChecked()
        if local_only:
            rpc_ip = '127.0.0.1'
        ip_valid = guilib.validate_ip(rpc_ip)
        if not ip_valid:
            msg += 'RPC IP is invalid! \n'
        binance_key = self.binance_key_text_input.text()
        binance_secret = self.binance_secret_text_input.text()
        margin = float(self.creds[7])
        netid = self.netid_input.text()
        index = self.bot_mode_comboBox.currentIndex()
        bot_mode = self.bot_mode_comboBox.itemText(index)
        countertrade_timeout = float(self.countertrade_timeout_input.text())
        if passphrase == '':
            msg += 'No seed phrase input! \n'
        if rpc_password == '':
            msg += 'No RPC password input! \n'
        if rpc_ip == '':
            msg += 'No RPC IP input! \n'
        if msg == '':
            overwrite = True
            if os.path.isfile(config_path+self.username+"_MM2.enc"):
                confirm = QMessageBox.question(self, 'Confirm overwrite', "Existing settings detected. Overwrite?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if not confirm == QMessageBox.Yes:
                    overwrite = False
            if overwrite:
                passwd, ok = QInputDialog.getText(self, 'Enter Password', 'Enter your login password: ')
                if ok:
                    if passwd == self.password:
                        data = {}
                        data.update({"gui":gui})
                        data.update({"rpc_password":rpc_password})
                        data.update({"netid":int(netid)})
                        data.update({"passphrase":passphrase})
                        data.update({"userhome":home})
                        data.update({"rpc_local_only":local_only})
                        data.update({"rpc_allow_ip":rpc_ip})
                        data.update({"bn_key":binance_key})
                        data.update({"bn_secret":binance_secret})
                        data.update({"margin":margin})
                        data.update({"countertrade_timeout":countertrade_timeout})
                        data.update({"bot_mode":bot_mode})
                        data.update({"dbdir":config_path+"DB"})
                        # encrypt and store the config / credentials
                        enc_data = enc.encrypt_mm2_json(json.dumps(data), passwd)
                        with open(config_path+self.username+"_MM2.enc", 'w') as j:
                            j.write(bytes.decode(enc_data))
                        QMessageBox.information(self, 'Settings file created', "Settings updated. Please login again.", QMessageBox.Ok, QMessageBox.Ok)

                        print("stop_mm2 with old creds")
                        try:
                            rpclib.stop_mm2(self.creds[0], self.creds[1])
                        except Exception as e:
                            print("cache error")
                            print(e)
                            pass
                        self.authenticated = False
                        self.show_login_tab()

                    else:
                        QMessageBox.information(self, 'Password incorrect!', 'Password incorrect!', QMessageBox.Ok, QMessageBox.Ok)
                        pass
        else:
            QMessageBox.information(self, 'Validation failed', msg, QMessageBox.Ok, QMessageBox.Ok)
            pass
    
    # Generate wallet seed
    # TODO: add other languages
    def generate_seed(self):
        seed_words_list = []
        while len(seed_words_list) < 24:
            word = random.choice(wordlist.wordlist)
            if word not in seed_words_list:
                seed_words_list.append(word)
        seed_phrase = " ".join(seed_words_list)
        self.seed_text_input.setText(seed_phrase)

    ## LOGS


    ### FUCTIONS TO REVIEW ###

    def stop_bot_trading(self):
        self.bot_trade_thread.stop()
        bot_order_count = self.bot_mm2_orders_table.rowCount()
        if bot_order_count > 0:
            resp = QMessageBox.information(self, 'Cancel orders?', 'Cancel all orders?\nAlternatively, you can cancel individually\nby selecting orders from the open orders table. ', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if resp == QMessageBox.Yes:
                self.mm2_cancel_all_orders()
        self.bot_status_lbl.setText("STOPPED")
        self.bot_status_lbl.setStyleSheet("color: rgb(164, 0, 0);\nbackground-color: rgb(177, 179, 186);")
        log_msg = get_time_str()+" Bot stopped"
        log_row = QListWidgetItem(log_msg)
        log_row.setForeground(QColor('#267F00'))
        self.trading_logs_list.addItem(log_row)

    def start_bot_trading(self):
        buys = 0
        sells = 0
        for coin in self.buy_coins:
            if coin in coinslib.binance_coins and coin in self.active_coins:
                buys += 1
        for coin in self.sell_coins:
            if coin in coinslib.binance_coins and coin in self.active_coins:
                sells += 1
        if (buys == 1 and sells == 1 and buy_coins != sell_coins) or (buys > 0 and sells > 0):
            print("starting bot")            
            self.bot_trade_thread = bot_trading_thread(self.creds, self.sell_coins, self.buy_coins, self.active_coins)
            self.bot_trade_thread.check_status.connect(self.check_mm_bot_order_swaps)
            self.bot_trade_thread.trigger.connect(self.update_bot_log)
            self.bot_trade_thread.start()
            self.bot_status_lbl.setText("ACTIVE")
            self.bot_status_lbl.setStyleSheet('color: #043409;\nbackground-color: rgb(166, 215, 166);')
            log_msg = get_time_str()+" Bot started"
            log_row = QListWidgetItem(log_msg)
            log_row.setForeground(QColor('#267F00'))
            self.trading_logs_list.addItem(log_row)
        else:
            msg = 'Please activate at least one sell coin and at least one different buy coin (Binance compatible). '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))

    def update_bot_log(self, uuid, log_msg, log_result=''):
        log_row = QListWidgetItem(log_msg)
        log_row.setForeground(QColor('#00137F'))
        self.trading_logs_list.addItem(log_row)
        if log_result != '':
            log_row = QListWidgetItem(">>> "+str(log_result))
            log_row.setForeground(QColor('#7F0000'))
            self.trading_logs_list.addItem(log_row)

    def update_trading_log(self, sender, log_msg, log_result=''):
        timestamp = int(time.time())
        time_str = datetime.datetime.fromtimestamp(timestamp)
        prefix = str(time_str)+" ("+sender+"): "
        log_msg = prefix+log_msg
        log_row = QListWidgetItem(log_msg)
        log_row.setForeground(QColor('#00137F'))
        self.trading_logs_list.addItem(log_row)
        if log_result != '':
            log_row = QListWidgetItem(">>> "+str(log_result))
            log_row.setForeground(QColor('#7F0000'))
            self.trading_logs_list.addItem(log_row)

    def recover_swap(self):
        # TODO: add input to allow import of swap json for failed swap
        uuid = self.swap_recover_uuid.text()
        resp = rpclib.recover_stuck_swap(self.creds[0], self.creds[1], uuid).json()
        QMessageBox.information(self, 'Recover Stuck Swap', str(resp), QMessageBox.Ok, QMessageBox.Ok)

    def update_prices_table(self):
        self.prices_table.setSortingEnabled(False)
        headers = ['COIN', 'Binance BTC', 'Gecko BTC', 'Paprika BTC', 'Average BTC', 'Binance TUSD', 'Gecko USD', 'Paprika USD', 'Average USD']
        self.prices_table.setColumnCount(len(headers))
        self.prices_table.setHorizontalHeaderLabels(headers)
        self.clear_table(self.prices_table)
        self.prices_table.setRowCount(len(self.prices_data['average']))
        row = 0
        for coin in self.prices_data['average']:
            bn_btc_price = '-'
            bn_tusd_price = '-'
            gk_btc_price = '-'
            gk_usd_price = '-'
            pk_btc_price = '-'
            pk_usd_price = '-'
            average_btc_price = '-'
            average_usd_price = '-'
            if coin in self.prices_data['average']:
                if 'BTC' in self.prices_data['average'][coin]:
                    average_btc_price = self.prices_data['average'][coin]['BTC']
                if 'USD' in self.prices_data['average'][coin]:
                    average_usd_price = self.prices_data['average'][coin]['USD']
            if coin in self.prices_data["Binance"]:
                if 'BTC' in self.prices_data["Binance"][coin]:
                    bn_btc_price = self.prices_data["Binance"][coin]['BTC']
                if 'TUSD' in self.prices_data["Binance"][coin]:
                    bn_tusd_price = self.prices_data["Binance"][coin]['TUSD']
            if coin in self.prices_data['gecko']:
                if 'BTC' in self.prices_data['gecko'][coin]:
                    gk_btc_price = self.prices_data['gecko'][coin]['BTC']
                if 'USD' in self.prices_data['gecko'][coin]:
                    gk_usd_price = self.prices_data['gecko'][coin]['USD']
            if coin in self.prices_data['paprika']:
                if 'BTC' in self.prices_data['paprika'][coin]:
                    pk_btc_price = self.prices_data['paprika'][coin]['BTC']
                if 'USD' in self.prices_data['paprika'][coin]:
                    pk_usd_price = self.prices_data['paprika'][coin]['USD']
            price_row = [coin, bn_btc_price, gk_btc_price, pk_btc_price, average_btc_price, bn_tusd_price, gk_usd_price, pk_usd_price, average_usd_price]
            self.add_row(row, price_row, self.prices_table)
            row += 1
        self.prices_table.setSortingEnabled(True)
        self.prices_table.resizeColumnsToContents()
        self.prices_table.sortItems(0, Qt.AscendingOrder)

    def update_mm2_trade_history_table(self):
        if self.mm2_hide_failed_checkbox.isChecked():
            self.populate_table("table/mm2_history", self.mm2_trades_table, self.mm2_trades_msg_lbl, "", "2|Failed|EXCLUDE")
        else:
            self.populate_table("table/mm2_history", self.mm2_trades_table, self.mm2_trades_msg_lbl, "")
        for row in range(self.mm2_trades_table.rowCount()):
            if self.mm2_trades_table.item(row, 2).text() == 'Finished':
                self.colorize_row(self.mm2_trades_table, row, QColor(218, 255, 127))
            elif self.mm2_trades_table.item(row, 2).text() == 'Failed':
                self.colorize_row(self.mm2_trades_table, row, QColor(255, 127, 127))
            else:
                self.colorize_row(self.mm2_trades_table, row, QColor(255, 233, 127))

    def update_binance_trade_history_table(self):
        # Will need to be tracked locally. API endpoint is per symbol
        pass

    # runs each time the tab is changed to populate the items on that tab
    def prepare_tab(self):
        try:
            self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        except:
            # if not logged in, no creds
            pass
        QCoreApplication.processEvents()
        if self.authenticated:
            print("authenticated")
            self.stacked_login.setCurrentIndex(1)
            index = self.currentIndex()
            if self.creds[0] == '':
                QMessageBox.information(self, 'Settings for user "'+self.username+'" not found!', "Settings not found. Please fill in the config form, save your settings and restart Antara Makerbot.", QMessageBox.Ok, QMessageBox.Ok)
                self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))              
            elif index == 0:
                # activate
                print('show_activation_tab')
                self.show_activation_tab()
            elif index == 1:
                # order book
                print('show_mm2_orderbook_tab')
                self.show_mm2_orderbook_tab()
            elif index == 2:
                # binance acct
                print('show_binance_tab')
                self.show_binance_trading_tab()
            elif index == 3:
                # wallet
                print('show_mm2_wallet_tab')
                self.show_mm2_wallet_tab()
            elif index == 4:
                # strategies
                print('show_strategies_tab')
                self.show_strategies_tab()
            elif index == 5:
                # Prices
                print('show_prices_tab')
                self.show_prices_tab()
            elif index == 6:
                # history
                print('show_history_tab')
                self.show_history_tab()
            elif index == 7:
                # config
                print('show_config_tab')
                self.show_config_tab()
            elif index == 8:
                # logs
                print('show_logs_tab')
                self.show_logs_tab()
        else:
            print('show_activation_tab - login')
            self.stacked_login.setCurrentIndex(0)
            index = self.currentIndex()
            if index != 0:
                QMessageBox.information(self, 'Unauthorised access!', 'You must be logged in to access this tab', QMessageBox.Ok, QMessageBox.Ok)
            self.show_login_tab()

    # inactive functions, might be useful later
    def update_dl_progressbar(self, value):
        self.dl_progressBar.setValue(value)
        if value == 100:
            QMessageBox.information(self, "Progress status", 'Download complete!')

    def export_logs(self):
        pass

    # parse out user order uuids as a list
    def get_mm2_order_uuids(self):
        orders = rpclib.my_orders(self.creds[0], self.creds[1]).json()
        mm2_order_uuids = []
        if 'maker_orders' in orders['result']:
            maker_orders = orders['result']['maker_orders']
            for item in maker_orders:
                mm2_order_uuids.append(item)
        if 'taker_orders' in orders['result']:
            taker_orders = orders['result']['taker_orders']
            for item in taker_orders:
                mm2_order_uuids.append(item)
        return mm2_order_uuids

    def get_mm2_swap_events(self, events):
        event_types = []
        failed = False
        fail_event = False
        finished = False
        for event in events:
            event_types.append(event['event']['type'])
            if event['event']['type'] in rpclib.error_events: 
                failed = True
                fail_event = event['event']['type']
            if event['event']['type'] == 'Finished':
                finished = event['timestamp']
        return failed, fail_event, finished, event_types

    def check_mm_bot_order_swaps(self):
        for mm2_order_uuid in self.get_mm2_order_uuids():
            order_info = rpclib.order_status(self.creds[0], self.creds[1], mm2_order_uuid).json()
            if "order" in order_info:
                if 'started_swaps' in order_info['order']:
                    # scan maker swaps, log events and add to bot swap history if finished successfully.
                    for swap in order_info['order']['started_swaps']:
                        completed = False
                        if mm2_order_uuid not in self.bot_swap_history:
                            self.bot_swap_history[mm2_order_uuid] = {}
                            self.bot_swap_history[mm2_order_uuid]["mm2_swaps"] = {}
                        if swap not in self.bot_swap_history[mm2_order_uuid]["mm2_swaps"]:
                            swaps_info = rpclib.my_swap_status(self.creds[0], self.creds[1], swap).json()
                            if 'my_info' in swaps_info['result']:
                                base = swaps_info['result']['my_info']['my_coin']
                                rel = swaps_info['result']['my_info']['other_coin']
                                base_amount = float(swaps_info['result']['my_info']['my_amount'])
                                rel_amount = float(swaps_info['result']['my_info']['other_amount'])
                                swap_result = self.get_mm2_swap_events(swaps_info['result']['events'])
                                for i in range(self.mm2_trades_table.rowCount()):
                                    if self.mm2_trades_table.item(i,2) is not None:
                                        if self.mm2_trades_table.item(i,9).text() == swap and self.mm2_trades_table.item(i,2).text() != swap_result:
                                            if swap_result[0]:
                                                log_msg = "Swap "+swap+" has failed at event "+swap_result[1]+"!"
                                            elif 'Finished' not in swap_result[3]:
                                                log_msg = "Swap ["+swap+"]: "+str(base_amount)+" "+base+" for "+str(rel_amount)+" "+rel+" in progress at event: "+str(swap_result[3][-1])+"..."
                                            else:
                                                log_msg = "Swap "+swap+" has completed! Recieved "+str(rel_amount)+" "+rel+" for "+str(base_amount)+" "+base
                                                completed = True
                                            self.update_trading_log("bot", log_msg)
                                if completed:
                                    self.bot_swap_history[mm2_order_uuid].update({
                                            "mm2_rel":rel,
                                            "mm2_base":base,
                                            "bot_mode":self.creds[8],
                                            "time":get_time_str(),
                                            "mm2_swaps": {
                                                swap: {
                                                    "mm2_swap_rel_amount":rel_amount,
                                                    "mm2_swap_base_amount":base_amount,
                                                    "binance_countertrades":{},
                                                }
                                            }

                                    })
                                    # Initiate Binance countertrade if completed recently.
                                    if int(time.time()) < int(swap_result[2])/1000 + self.countertrade_delay_limit*60:
                                        if self.bot_swap_history[mm2_order_uuid]["bot_mode"] == 'Marketmaker & Binance':
                                            if len(self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"]) == 0:
                                                log_msg = "Initiating Binance countertrade for swap ["+swap+"]: "+str(base_amount)+" "+base+" for "+str(rel_amount)+" "+rel+"..."
                                                self.update_trading_log("bot", log_msg)
                                                self.start_binance_countertrade(base, rel, round(float(base_amount), 8), round(float(rel_amount),8), mm2_order_uuid, swap)
                                            else:
                                                print("countertrade already submitted")
                                        else:
                                            print("Bot mode: "+self.bot_swap_history[mm2_order_uuid]["bot_mode"]+" (not countertrading)")
                                    else:
                                        print("Countertrade delay limit: ("+str(self.countertrade_delay_limit)+" min) expired - not countertrading.")
                            else:
                                print(guilib.colorize("No info in swap ["+swap+"] yet.", 'blue'))
                        else:
                            print(guilib.colorize("Swap ["+swap+"] was already completed", 'blue'))
                        QCoreApplication.processEvents()
            else:
                print(guilib.colorize(order_info, 'red'))
        self.update_mm2_trades_table()

    # update bot swap history json when Binance trade initiated.
    def update_bot_swap_history(self, mm2_order_uuid, selected_symbol, binance_orderId, order_type, coin, amount, swap):
        log_msg = "Binance countertrade "+order_type+" order submitted! "
        resp = str(amount)+" "+coin+" at market via ["+selected_symbol+"]"
        self.update_trading_log('Bot', log_msg, str(resp))
        if "binance_countertrades" not in self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]:
            self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"] = {}
        self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"].update({
            str(binance_orderId): {
                "symbol":selected_symbol,
                "type":order_type,
                "coin":coin,
                "amount":amount,
                "status":"SENT"
            }
        })        

    # check if binance trade is complete
    def check_binance_bot_counterorders(self):
        row_count = 0
        for mm2_order_uuid in self.bot_swap_history:
            if len(self.bot_swap_history[mm2_order_uuid]['mm2_swaps']) > 0:
                for swap in self.bot_swap_history[mm2_order_uuid]['mm2_swaps']:
                    for orderId in self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"]:
                        row_count += 1
                        symbol = self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['symbol']
                        status = self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['status']
                        resp = binance_api.get_order(self.creds[5], self.creds[6], symbol, orderId)
                        if 'status' in resp:
                            if resp['status'] == 'FILLED' and status != 'BINANCE COUNTERTRADE COMPLETE':
                                # update bot history json, and write to console log
                                binance_orderId = resp['orderId']
                                log_msg = "Binance countertrade complete! OrderID ["+str(resp['orderId'])+"]: "+resp['side']+" "+str(resp['executedQty'])+" "+str(resp['symbol'])
                                self.update_trading_log("Bot", log_msg)
                                self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId].update({
                                        "status":"BINANCE COUNTERTRADE COMPLETE"
                                })
                                self.write_bot_swap_history()
                                order_info = rpclib.order_status(self.creds[0], self.creds[1], mm2_order_uuid).json()
                                if len(order_info['order']['started_swaps']) == 0:
                                    # cancel mm2 bot order once countertrade complete (if no other trades in progress)
                                    resp = rpclib.cancel_uuid(self.creds[0], self.creds[1], mm2_order_uuid).json()
                                    log_msg = get_time_str()+" (Bot): MM2 order uuid ["+mm2_order_uuid+"] "+base+"/"+rel+" cancelled after countertrade"
                                    self.update_bot_log(mm2_order_uuid, log_msg, str(resp))
                    QCoreApplication.processEvents()
        self.populate_countertrade_table(row_count)

    # Refresh binance countertrade table for bot history json
    def populate_countertrade_table(self, row_count):
        self.bot_binance_orders_table.setSortingEnabled(False)
        self.clear_table(self.bot_binance_orders_table)
        self.bot_mm2_orders_table.setRowCount(row_count)
        row = 0
        for mm2_order_uuid in self.bot_swap_history:
            if 'mm2_base' in self.bot_swap_history[mm2_order_uuid]:
                base = self.bot_swap_history[mm2_order_uuid]['mm2_base']
                rel = self.bot_swap_history[mm2_order_uuid]['mm2_rel']
                time = self.bot_swap_history[mm2_order_uuid]['time']
                if len(self.bot_swap_history[mm2_order_uuid]['mm2_swaps']) > 0:
                    for swap in self.bot_swap_history[mm2_order_uuid]['mm2_swaps']:
                        orderId = '-'
                        symbol = '-'
                        trade_type = '-'
                        amount = '-'
                        status = 'MM2 TRADE COMPLETE'
                        coin = '-'
                        mm2_swap_rel_amount = round(float(self.bot_swap_history[mm2_order_uuid]['mm2_swaps'][swap]['mm2_swap_rel_amount']),8)
                        mm2_swap_base_amount = round(float(self.bot_swap_history[mm2_order_uuid]['mm2_swaps'][swap]['mm2_swap_base_amount']),8)
                        countertrade_row = [time, mm2_order_uuid, swap, base, rel, mm2_swap_rel_amount, mm2_swap_base_amount, orderId, symbol, trade_type, coin, amount, status]
                        self.add_row(row, countertrade_row, self.bot_binance_orders_table)
                        row += 1
                        for orderId in self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"]:
                            mm2_swap_rel_amount = '-'
                            mm2_swap_base_amount = '-'
                            symbol = self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['symbol']
                            trade_type = self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['type']
                            coin = self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['coin']
                            amount = round(float(self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['amount']),8)
                            status = self.bot_swap_history[mm2_order_uuid]["mm2_swaps"][swap]["binance_countertrades"][orderId]['status']
                            countertrade_row = [time, mm2_order_uuid, swap, base, rel, mm2_swap_rel_amount, mm2_swap_base_amount, orderId, symbol, trade_type, coin, amount, status]
                            self.add_row(row, countertrade_row, self.bot_binance_orders_table)
                            row += 1
        self.bot_binance_orders_table.setSortingEnabled(True)
        self.bot_binance_orders_table.resizeColumnsToContents()

    def start_binance_countertrade(self, base, rel, base_amount, rel_amount, mm2_order_uuid, swap):
        # replenish base, liquidate rel
        countertrade_symbols = self.get_binance_countertrade_symbols(base, rel, base_amount, rel_amount)
        selected_rel_symbol = countertrade_symbols[0]
        selected_base_symbol = countertrade_symbols[1]
        if selected_base_symbol != '':
            base_amount = round(float(binance_api.round_to_step(selected_base_symbol, base_amount)), 8)
            rel_amount = round(float(binance_api.round_to_step(selected_rel_symbol, rel_amount)), 8)
            if selected_base_symbol == selected_rel_symbol:                
                # Direct base trade...
                if binance_api.binance_pair_info[selected_base_symbol]['quoteAsset'] == base:
                    resp = binance_api.create_sell_order_at_market(self.creds[5], self.creds[6], selected_base_symbol, base_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_base_symbol, resp['orderId'], "sell", base, base_amount, swap)
                    resp = binance_api.create_buy_order_at_market(self.creds[5], self.creds[6], selected_base_symbol, rel_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_rel_symbol, resp['orderId'], "buy", rel, rel_amount, swap)
                # Direct rel trade...
                elif binance_api.binance_pair_info[selected_base_symbol]['quoteAsset'] == rel:
                    resp = binance_api.create_buy_order_at_market(self.creds[5], self.creds[6], selected_base_symbol, base_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_base_symbol, resp['orderId'], "buy", base, base_amount, swap)
                    resp = binance_api.create_sell_order_at_market(self.creds[5], self.creds[6], selected_base_symbol, rel_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_rel_symbol, resp['orderId'], "sell", rel, rel_amount, swap)
            else:
                # Indirect base trade...
                if binance_api.binance_pair_info[selected_base_symbol]['quoteAsset'] == base:
                    resp = binance_api.create_sell_order_at_market(self.creds[5], self.creds[6], selected_base_symbol, base_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_base_symbol, resp['orderId'], "sell", base, base_amount, swap)
                else:
                    resp = binance_api.create_buy_order_at_market(self.creds[5], self.creds[6], selected_base_symbol, base_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_base_symbol, resp['orderId'], "buy", base, base_amount, swap)
                # Indirect rel trade...
                if binance_api.binance_pair_info[selected_rel_symbol]['quoteAsset'] == rel:
                    resp = binance_api.create_buy_order_at_market(self.creds[5], self.creds[6], selected_rel_symbol, rel_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_rel_symbol, resp['orderId'], "buy", rel, rel_amount, swap)
                else:
                    resp = binance_api.create_sell_order_at_market(self.creds[5], self.creds[6], selected_rel_symbol, rel_amount)
                    if 'orderId' in resp:
                        self.update_bot_swap_history(mm2_order_uuid, selected_rel_symbol, resp['orderId'], "sell", rel, rel_amount, swap)
        self.update_binance_orders_table()

    # get table row values for maker orders
    def prepare_maker_row(self, maker_orders, item):
        role = "Maker"
        base = maker_orders[item]['base']
        base_amount = round(float(maker_orders[item]['available_amount']),8)
        rel = maker_orders[item]['rel']
        rel_amount = round(float(maker_orders[item]['price'])*float(maker_orders[item]['available_amount']),8)
        sell_price = round(float(maker_orders[item]['price']),8)
        timestamp = int(maker_orders[item]['created_at']/1000)
        created_at = datetime.datetime.fromtimestamp(timestamp)
        buy_price = round(float(1/float(sell_price)),8)
        return [created_at, role, rel, rel_amount, buy_price, base, base_amount, sell_price, item]

    # get table row values for taker orders
    def prepare_taker_row(self, taker_orders, item):
        role = "Taker"
        timestamp = int(taker_orders[item]['created_at'])/1000
        created_at = datetime.datetime.fromtimestamp(timestamp)
        base = taker_orders[item]['request']['base']
        rel = taker_orders[item]['request']['rel']
        base_amount = round(float(taker_orders[item]['request']['base_amount']),8)
        rel_amount = round(float(taker_orders[item]['request']['rel_amount']),8)
        buy_price = round(float(taker_orders[item]['request']['rel_amount'])/float(taker_orders[item]['request']['base_amount']),8)
        sell_price = round(float(1/float(buy_price)),8)
        return [created_at, role, base, base_amount, buy_price, rel, rel_amount, sell_price, item]

    def create_mm2_setprice(self):
        # get order params from form fields
        index = self.mm2_sell_coin_combo.currentIndex()
        base = self.mm2_sell_coin_combo.itemText(index)
        index = self.mm2_buy_coin_combo.currentIndex()
        rel = self.mm2_buy_coin_combo.itemText(index)
        basevolume = round(float(self.mm2_buy_amount_spinbox.value()),8)
        relprice = round(float(self.mm2_price_spinbox.value()),8)
        # scan for existing order of pair
        cancel_previous = True
        cancel_trade = False
        orders = rpclib.my_orders(self.creds[0], self.creds[1]).json()
        for order in orders:
            if 'maker_orders' in orders['result']:
                maker_orders = orders['result']['maker_orders']
                msg = ''
                for item in maker_orders:
                    existing_base = maker_orders[item]['base']
                    existing_rel = maker_orders[item]['rel']
                    if base == existing_base and rel == existing_rel:
                        existing_available = maker_orders[item]['available_amount']
                        existing_price = maker_orders[item]['price']
                        existing_timestamp = int(maker_orders[item]['created_at'])/1000
                        existing_created_at = str(datetime.datetime.fromtimestamp(existing_timestamp))
                        msg_title = "Existing order detected!"
                        msg = "Cancel all previous "+base+"/"+rel+" orders?"
                        break
                if msg != '':
                    confirm = QMessageBox.question(self, msg_title, msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                    if confirm == QMessageBox.No:
                        cancel_previous = False
                    elif confirm == QMessageBox.Cancel:
                        cancel_trade = True
        # detect maxvolume trade
        max_vol = round(float(self.mm2_sell_balance_lbl.text().split()[1]),8)
        val = self.mm2_sell_amount_spinbox.value()
        if val == max_vol:
            trade_max = True
        else:
            trade_max = False
        if not cancel_trade:
            # Submit trade
            resp = rpclib.setprice(self.creds[0], self.creds[1], base, rel, basevolume, relprice, trade_max, cancel_previous).json()
            trade_val = round(float(relprice)*float(basevolume),8)
            log_msg = "Sell "+str(basevolume)+" "+base+" for "+str(trade_val)+" "+rel
            if 'error' in resp:
                if resp['error'].find("larger than available") > -1:
                    msg = "Insufficient funds to complete order."
                else:
                    msg = resp
            elif 'result' in resp:
                msg = "Sell order Submitted.\n"
                msg += "Sell "+str(basevolume)+" "+base+"\nfor\n"+str(trade_val)+" "+rel
                self.update_mm2_trades_table()
            else:
                msg = resp
            QMessageBox.information(self, 'Created Setprice Sell Order', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            self.update_trading_log('mm2', log_msg, str(resp))

    def mm2_cancel_bot_order(self):
        cancel = True
        selected_row = self.bot_mm2_orders_table.currentRow()
        if self.bot_mm2_orders_table.item(selected_row,5) is not None:
            if self.bot_mm2_orders_table.item(selected_row,0).text() != '':
                mm2_order_uuid = self.bot_mm2_orders_table.item(selected_row,8).text()
                order_info = rpclib.order_status(self.creds[0], self.creds[1], mm2_order_uuid).json()
                if len(order_info['order']['started_swaps']) != 0:
                    msg = "This order has swaps in progress, are you sure you want to cancel it?"
                    confirm = QMessageBox.question(self, 'Cancel Order', msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                    if confirm == QMessageBox.No:
                        cancel = False
                    elif confirm == QMessageBox.Cancel:
                        cancel = False
                if cancel:
                    resp = rpclib.cancel_uuid(self.creds[0], self.creds[1], mm2_order_uuid).json()
                    msg = ''
                    if 'result' in resp:
                        if resp['result'] == 'success':
                            msg = "Order "+mm2_order_uuid+" cancelled"
                        else:
                            msg = resp
                    else:
                        msg = resp
                    log_msg = "Cancelling mm2 order "+mm2_order_uuid+"..."
                    self.update_trading_log("mm2", log_msg, str(resp))
                    QMessageBox.information(self, 'Order Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        

if __name__ == '__main__':
    
    appctxt = ApplicationContext()
    screen_resolution = appctxt.app.desktop().screenGeometry()
    width, height = screen_resolution.width(), screen_resolution.height()
    print("Screen width: "+str(width))
    print("Screen height: "+str(height))
    window = Ui(appctxt)
    window.resize(width, height)
    exit_code = appctxt.app.exec_()
    rpclib.stop_mm2(window.creds[0], window.creds[1])
    sys.exit(exit_code)
