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
from lib import guilib, rpclib, coinslib, wordlist, enc, priceslib, binance_api
import qrcode
import random
from ui import coin_icons
import datetime
import time
import dateutil.parser
from zipfile import ZipFile 
import platform
import subprocess

# will try graphing later with these imports
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Point import Point

os.environ["QT_SCALE_FACTOR"] = "1"  # bigness
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

pg.setConfigOption('background', (64,64,64))
pg.setConfigOption('foreground', (78,155,46))

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

# Setup local settings ini.
# Need to test this on alternative Operating systems.
QSettings.setDefaultFormat(QSettings.IniFormat)
QCoreApplication.setOrganizationName("KomodoPlatform")
QCoreApplication.setApplicationName("AntaraMakerbot")
settings = QSettings()
ini_file = settings.fileName()
config_path = settings.fileName().replace("AntaraMakerbot.ini", "")

if settings.value('users') is None:
    settings.setValue("users", [])
print("Existing users: " +str(settings.value('users')))


if not os.path.isfile(config_path+'coins'):
    try:
        print("Downloading latest coins file")
        with open(config_path+"coins", 'w') as f:
            r = requests.get("https://raw.githubusercontent.com/jl777/coins/master/coins")
            if r.status_code == 200:
                f.write(json.dumps(r.json()))
            else:
                print("coins update failed: "+str(r.status_code))
    except:
        pass
os.environ['MM_COINS_PATH'] = config_path+"coins"

# THREADED OPERATIONS

class bot_trading_thread(QThread):
    trigger = pyqtSignal(str, str)
    def __init__(self, creds, sell_coins, buy_coins, active_coins, premium):
        QThread.__init__(self)
        self.creds = creds
        self.sell_coins = sell_coins
        self.buy_coins = buy_coins
        self.active_coins = active_coins
        self.premium = premium

    def __del__(self):
        self.wait()

    def run(self):        
        while True:                
            for base in self.sell_coins:
                if base in self.active_coins:
                    balance_info = rpclib.my_balance(self.creds[0], self.creds[1], base).json()
                    if 'address' in balance_info:
                        address = balance_info['address']
                        balance_text = balance_info['balance']
                        locked_text = balance_info['locked_by_swaps']
                        available_balance = float(balance_info['balance']) - float(balance_info['locked_by_swaps'])
                        for rel in self.buy_coins:
                            if rel in self.active_coins:
                                if base != rel:
                                    if rel in coinslib.binance_coins:
                                        base_btc_price = priceslib.get_btc_price(self.creds[5], base)
                                        rel_btc_price = priceslib.get_btc_price(self.creds[5], rel)
                                        rel_price = base_btc_price/rel_btc_price
                                        trade_price = rel_price+rel_price*self.premium
                                        trade_val = round(float(rel_price)*float(available_balance),8)
                                        timestamp = int(time.time()/1000)*1000
                                        time_str = datetime.datetime.fromtimestamp(timestamp)
                                        prefix = str(time_str)+" (MM2): "
                                        log_msg = prefix+" [Create Order] Sell "+str(available_balance)+" "+base+" for "+str(trade_val)+" "+rel
                                        resp = rpclib.setprice(self.creds[0], self.creds[1], base, rel, available_balance, trade_price, True, True).json()
                                        if 'error' in resp:
                                            if resp['error'].find("larger than available") > -1:
                                                msg = "Insufficient funds to complete "+base+"/"+rel+" order."
                                            else:
                                                msg = resp
                                        elif 'result' in resp:
                                            msg = "New order submitted (previous "+base+"/"+rel+" orders cancelled)."
                                        else:
                                            msg = resp
                                        self.trigger.emit(log_msg, str(msg))
            time.sleep(120)

    def stop(self):
        self.terminate()

class cachedata_thread(QThread):
    trigger = pyqtSignal(dict, dict)
    def __init__(self, creds):
        QThread.__init__(self)
        self.creds = creds

    def __del__(self):
        self.wait()

    def run(self):
        active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        prices_data = priceslib.get_prices_data(self.creds[0], self.creds[1],active_coins)
        balances_data = {}
        for coin in active_coins:
            balances_data[coin] = {}
            balance_info = rpclib.my_balance(self.creds[0], self.creds[1], coin).json()
            if 'address' in balance_info:
                address = balance_info['address']
                balance = round(float(balance_info['balance']),8)
                locked = round(float(balance_info['locked_by_swaps']),8)
                available = balance - locked
                balances_data[coin].update({
                    'address':address,
                    'balance':balance,
                    'locked':locked,
                    'available':available
                })
        self.trigger.emit(prices_data, balances_data)

class activation_thread(QThread):
    trigger = pyqtSignal(str)
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
                self.trigger.emit(coin[0])

# Item Classes

class QR_image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        print(qrcode.image.base.BaseImage)
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

# not used - maybe for graphs if mouse position signalling works
class crosshair_lines(pg.InfiniteLine):
    def __init__(self, *args, **kwargs):
        pg.InfiniteLine.__init__(self, *args, **kwargs)
        self.setCursor(Qt.CrossCursor)

# UI Class

class Ui(QTabWidget):
    def __init__(self, ctx):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uifile = QFile(":/ui/makerbot_gui2.ui")
        uifile.open(QFile.ReadOnly)
        uic.loadUi(uifile, self) # Load the .ui file
        self.ctx = ctx # app context
        self.show() # Show the GUI
        self.mm2_bin = self.ctx.get_resource('mm2')
        self.setWindowTitle("Komodo Platform's Antara Makerbot")
        self.setWindowIcon(QIcon(':/32/img/32/kmd.png'))
        self.authenticated = False
        self.mm2_downloading = False
        self.bot_trading = False
        self.last_price_update = 0
        self.prices_data = {}
        self.balances_data = {}
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

    ## MM2 management
    def start_mm2(self, logfile='mm2_output.log'):
        try:
            mm2_output = open(config_path+self.username+logfile,'w+')
            print(self.mm2_bin)
            subprocess.Popen([self.mm2_bin], stdout=mm2_output, stderr=mm2_output, universal_newlines=True)
            time.sleep(1)
        except Exception as e:
            QMessageBox.information(self, "Progress status", 'No mm2!')
            print(e)

    def update_dl_progressbar(self, value):
        self.dl_progressBar.setValue(value)
        if value == 100:
            QMessageBox.information(self, "Progress status", 'Download complete!')


    ## COMMON
    def saveFileDialog(self):
        filename = ''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save Trade data to CSV","","All Files (*);;Text Files (*.csv)", options=options)
        return fileName

    def add_row(self, row, row_data, table, bgcol=''):
        col = 0
        for cell_data in row_data:
            cell = QTableWidgetItem(str(cell_data))
            table.setItem(row,col,cell)
            cell.setTextAlignment(Qt.AlignCenter)  
            if bgcol != ''  :
                table.item(row,col).setBackground(bgcol)
            col += 1

    def export_table(self):
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

    def update_balance(self, coin):
        print("updating balance in main thread")
        self.balances_data[coin] = {}
        balance_info = rpclib.my_balance(self.creds[0], self.creds[1], coin).json()
        if 'address' in balance_info:
            address = balance_info['address']
            balance = round(float(balance_info['balance']),8)
            locked = round(float(balance_info['locked_by_swaps']),8)
            available = balance - locked
            self.balances_data[coin].update({
                'address':address,
                'balance':balance,
                'locked':locked,
                'available':available
            })

    def get_cell_val(self, table, column):
        if table.currentRow() != -1:
            if table.item(table.currentRow(),column).text() != '':
                return float(table.item(table.currentRow(),column).text())
            else:
                return 0
        else:
            return 0

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

    def update_mm2_orders_tables(self):
        orders = rpclib.my_orders(self.creds[0], self.creds[1]).json()
        self.bot_mm2_orders_table.setSortingEnabled(False)
        self.mm2_orders_table.setSortingEnabled(False)

        self.clear_table(self.bot_mm2_orders_table)
        self.clear_table(self.mm2_orders_table)

        if 'maker_orders' in orders['result']:
            maker_orders = orders['result']['maker_orders']
            bot_row = 0
            mm2_row = 0
            for item in maker_orders:
                print(guilib.colorize(maker_orders[item],'blue'))
                role = "Maker"
                base = maker_orders[item]['base']
                base_amount = maker_orders[item]['available_amount']
                rel = maker_orders[item]['rel']
                rel_amount = float(maker_orders[item]['price'])*float(maker_orders[item]['available_amount'])
                sell_price = maker_orders[item]['price']
                timestamp = int(maker_orders[item]['created_at']/1000)
                created_at = datetime.datetime.fromtimestamp(timestamp)
                buy_price = 1/float(sell_price)

                bot_maker_row = [created_at, role, base+"/"+rel, base_amount, sell_price, item]
                mm2_maker_row = [created_at, role, base, base_amount, rel, rel_amount, buy_price, sell_price, item]

                self.add_row(bot_row, bot_maker_row, self.bot_mm2_orders_table)
                bot_row += 1
                self.add_row(mm2_row, mm2_maker_row, self.mm2_orders_table)
                mm2_row += 1

        if 'taker_orders' in orders['result']:
            taker_orders = orders['result']['taker_orders']
            for item in taker_orders:
                role = "Taker"
                print(guilib.colorize(taker_orders[item],'cyan'))
                timestamp = int(taker_orders[item]['created_at'])/1000
                created_at = datetime.datetime.fromtimestamp(timestamp)
                base = taker_orders[item]['request']['base']
                rel = taker_orders[item]['request']['rel']
                base_amount = taker_orders[item]['request']['base_amount']
                rel_amount = taker_orders[item]['request']['rel_amount']
                buy_price = float(taker_orders[item]['request']['rel_amount'])/float(taker_orders[item]['request']['base_amount'])
                sell_price = 1/float(sell_price)

                bot_taker_row = [created_at, role, rel+"/"+base, base_amount, buy_price, item]
                mm2_taker_row = [created_at, role, rel, rel_amount, base, base_amount, buy_price, sell_price, item]

                self.add_row(bot_row, bot_taker_row, self.bot_mm2_orders_table)
                bot_row += 1
                self.add_row(mm2_row, mm2_taker_row, self.mm2_orders_table)
                mm2_row += 1


        self.bot_mm2_orders_table.setSortingEnabled(True)
        self.mm2_orders_table.setSortingEnabled(True)

    # Thread callbacks
    def update_active(self):
        self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        existing_coins = []
        for i in range(self.wallet_combo.count()):
            existing_coin = self.wallet_combo.itemText(i)
            existing_coins.append(existing_coin)
        for coin in self.gui_coins:
            if coin in self.active_coins:
                self.gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(138, 226, 52)")
                if coin not in existing_coins:
                    self.wallet_combo.addItem(coin)
            else:
                self.gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(114, 159, 207)")

    ## LOGIN 
    def show_login_tab(self):
        self.stacked_login.setCurrentIndex(0)
        self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        self.username_input.setFocus()
        print("show_login_tab")

    def login(self):
        print("logging in...")
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        if self.username == '' or self.password == '' and not self.authenticated:
            QMessageBox.information(self, 'Login failed!', 'username and password fields can not be blank!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            # create .enc if new user
            if not os.path.isfile(config_path+self.username+"_MM2.enc"):
                with open(config_path+self.username+"_MM2.enc", 'w') as f:
                    f.write('')
            # decrypt
            else:
                with open(config_path+self.username+"_MM2.enc", 'r') as f:
                    encrypted_mm2_json = f.read()
                if encrypted_mm2_json != '':
                    print("decrypting")
                    mm2_json_decrypted = enc.decrypt_mm2_json(encrypted_mm2_json, self.password)
                    try:
                        with open(config_path+"MM2.json", 'w') as j:
                            j.write(mm2_json_decrypted.decode())
                        self.authenticated = True
                    except:
                        print("decrypting failed")
                        # did not decode, bad password
                        pass
            jsonfile = config_path+"MM2.json"
            try:
                self.creds = guilib.get_creds(jsonfile)
            except Exception as e:
                print("get_creds failed")
                print(e)
                self.creds = ['','','','','','','','']
                pass
            if self.authenticated:            
                if self.username in settings.value('users'):
                    self.authenticated = True
                    self.username_input.setText('')
                    self.password_input.setText('')
                    self.stacked_login.setCurrentIndex(1)
                    if self.creds[0] != '':
                        version = ''
                        stopped = False
                        while version == '':
                            if not stopped:
                                try:
                                    print("stopping mm2 (if running)")
                                    rpclib.stop_mm2(self.creds[0], self.creds[1])
                                except:
                                    stopped = True
                                    pass
                            os.environ['MM_CONF_PATH'] = config_path+"MM2.json"
                            try:
                                print("starting mm2")
                                self.start_mm2()
                                time.sleep(0.6)
                                version = rpclib.version(self.creds[0], self.creds[1]).json()['result']
                                self.mm2_version_lbl.setText("MarketMaker version: "+version+" ")
                            except:
                                pass
                        with open(config_path+"MM2.json", 'w') as j:
                            j.write('')
                        self.show_activation_tab()
                    else:
                        self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))
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

    def populate_activation_menu(self, display_coins, layout):
        row = 0
        for coin in display_coins:
            self.gui_coins[coin]['checkbox'].show()
            self.gui_coins[coin]['combo'].show()
            layout.addWidget(self.gui_coins[coin]['checkbox'], row, 0, 1, 1)
            layout.addWidget(self.gui_coins[coin]['combo'], row, 1, 1, 1)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/32/img/32/"+coin.lower()+".png"), QIcon.Normal, QIcon.Off)
            self.gui_coins[coin]['checkbox'].setIcon(icon)
            row += 1

    # ACTIVATE
    def show_activation_tab(self):
        print("show_activation_tab")
        display_coins_erc20 = []
        display_coins_utxo = []
        display_coins_smartchain = []
        search_txt = self.search_activate.text().lower()
        self.update_active()
        for coin in self.gui_coins:
            self.gui_coins[coin]['checkbox'].hide()
            self.gui_coins[coin]['combo'].hide()
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

    def activate_coins(self):
        print('Start activate')
        coins_to_activate = []
        autoactivate = []
        self.buy_coins = []
        self.sell_coins = []
        for coin in self.gui_coins:
            combo = self.gui_coins[coin]['combo']
            checkbox = self.gui_coins[coin]['checkbox']
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
            # TODO: use this to reactivte next load
            activate_list = {
                "autoactivate":autoactivate,
                "buy_coins":self.buy_coins,
                "sell_coins":self.sell_coins
            }
        with open(config_path+self.username+"_coins.json", 'w') as j:
            j.write(json.dumps(activate_list))
        # Activate selected coins in separate thread
        self.activate_thread = activation_thread(self.creds, coins_to_activate)
        self.activate_thread.trigger.connect(self.update_active)
        self.activate_thread.start()
        print("Kickstart coins: "+str(rpclib.coins_needed_for_kick_start(self.creds[0], self.creds[1]).json()))
        print("Buy coins: "+str(self.buy_coins))
        print("Sell coins: "+str(self.sell_coins))
        self.show_activation_tab()

    def show_combo_activated(self, coin):
        self.gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(138, 226, 52);padding-left:25px;")

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

    ## SHOW ORDERS
    def mm2_cancel_order(self):
        selected_row = self.mm2_orders_table.currentRow()
        if self.mm2_orders_table.item(selected_row,8) is not None:
            if self.mm2_orders_table.item(selected_row,0).text() != '':
                order_uuid = self.mm2_orders_table.item(selected_row,8).text()
                resp = rpclib.cancel_uuid(self.creds[0], self.creds[1], order_uuid).json()
                msg = ''
                if 'result' in resp:
                    if resp['result'] == 'success':
                        msg = "Order "+order_uuid+" cancelled"
                    else:
                        msg = resp
                else:
                    msg = resp
                QMessageBox.information(self, 'Order Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        self.update_mm2_orders_tables()

    def mm2_cancel_bot_order(self):
        selected_row = self.bot_mm2_orders_table.currentRow()
        if self.bot_mm2_orders_table.item(selected_row,5) is not None:
            if self.bot_mm2_orders_table.item(selected_row,0).text() != '':
                order_uuid = self.bot_mm2_orders_table.item(selected_row,5).text()
                resp = rpclib.cancel_uuid(self.creds[0], self.creds[1], order_uuid).json()
                msg = ''
                if 'result' in resp:
                    if resp['result'] == 'success':
                        msg = "Order "+order_uuid+" cancelled"
                    else:
                        msg = resp
                else:
                    msg = resp
                QMessageBox.information(self, 'Order Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        self.update_mm2_orders_tables()

    def mm2_cancel_all_orders(self):
        if self.bot_mm2_orders_table.item(0,0).text() != '':
            resp = rpclib.cancel_all(self.creds[0], self.creds[1]).json()
            msg = ''
            if 'result' in resp:
                if resp['result'] == 'success':
                    msg = "Order "+order_uuid+" cancelled"
                else:
                    msg = resp
            else:
                msg = resp
            msg = "All your orders have been cancelled"
            QMessageBox.information(self, 'Orders Cancelled', msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Order Cancelled', 'You have no orders!', QMessageBox.Ok, QMessageBox.Ok)
        self.update_mm2_orders_tables()
   
    def show_mm2_trades(self):
        swaps_info = rpclib.my_recent_swaps(self.creds[0], self.creds[1], limit=9999, from_uuid='').json()
        row = 0
        self.mm2_trades_table.setSortingEnabled(False)
        self.clear_table(self.mm2_trades_table)
        for swap in swaps_info['result']['swaps']:
            for event in swap['events']:
                event_type = event['event']['type']
                if event_type in rpclib.error_events:
                    event_type = 'Failed'
                    break
            status = event_type
            role = swap['type']
            uuid = swap['uuid']
            my_amount = swap['my_info']['my_amount']
            my_coin = swap['my_info']['my_coin']
            other_amount = swap['my_info']['other_amount']
            other_coin = swap['my_info']['other_coin']
            started_at = datetime.datetime.fromtimestamp(round(swap['my_info']['started_at']/1000)*1000)
            if swap['type'] == 'Taker':
                buy_price = float(swap['my_info']['my_amount'])/float(swap['my_info']['other_amount'])
                sell_price = '-'
            else:
                buy_price = '-'
                sell_price = float(swap['my_info']['other_amount'])/float(swap['my_info']['my_amount'])
            trade_row = [started_at, role, status, other_coin, other_amount, buy_price, my_coin, my_amount, sell_price, uuid]

            self.add_row(row, trade_row, self.mm2_trades_table)

            row += 1
            self.mm2_trades_table.setSortingEnabled(True)

    ## SHOW ORDERBOOK

    def show_mm2_orderbook_tab(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            if self.orderbook_buy_combo.currentIndex() != -1:
                base = self.orderbook_buy_combo.itemText(self.orderbook_buy_combo.currentIndex())
            else:
                base = ''
            if self.orderbook_sell_combo.currentIndex() != -1:
                rel = self.orderbook_sell_combo.itemText(self.orderbook_sell_combo.currentIndex())
            else:
                rel = ''
            active_coins_selection = self.active_coins[:]

            # populate combo boxes
            base = self.update_combo(self.orderbook_buy_combo,active_coins_selection,base)
            active_coins_selection.remove(base)
            rel = self.update_combo(self.orderbook_sell_combo,active_coins_selection,rel)

            # populate table
            self.orderbook_table.setHorizontalHeaderLabels(['Buy coin', 'Sell coin', base+' Volume', rel+' price per '+base, 'Market price'])
            pair_book = rpclib.orderbook(self.creds[0], self.creds[1], base, rel).json()
            self.orderbook_table.setSortingEnabled(False)
            self.clear_table(self.orderbook_table)
            if 'error' in pair_book:
                pass
            elif 'asks' in pair_book:
                row = 0
                for item in pair_book['asks']:
                    # buying base for rel
                    base = pair_book['base']
                    rel = pair_book['rel']
                    basevolume = round(float(item['maxvolume']), 8)
                    relprice = round(float(item['price']), 8)
                    asks_row = [base, rel, basevolume, relprice]
                    self.add_row(row, asks_row, self.orderbook_table)
                    row += 1
            self.orderbook_table.setSortingEnabled(True)

    def update_orderbook_combos(self, base, rel):
        pass

    def orderbook_buy(self):
        row = 0
        index = self.orderbook_buy_combo.currentIndex()
        base = self.orderbook_buy_combo.itemText(index)
        index = self.orderbook_sell_combo.currentIndex()
        rel = self.orderbook_sell_combo.itemText(index)
        selected_row = self.orderbook_table.currentRow()
        if selected_row != -1:
            selected_price = self.orderbook_table.item(selected_row,3).text()
            if selected_price != '':

                if rel not in self.balances_data:
                    self.update_balance(rel)
                balance_info = self.balances_data[rel]
                if 'address' in balance_info:
                    address = balance_info['address']
                    balance_text = balance_info['balance']
                    locked_text = balance_info['locked']
                    available_balance = balance_info['available']

                    max_vol = available_balance/float(selected_price)*0.99
                vol, ok = QInputDialog.getDouble(self, 'Enter Volume', 'Enter volume '+base+' to buy at '+selected_price+' (max. '+str(max_vol)+'): ', QLineEdit.Password)
                if ok:
                    resp = rpclib.buy(self.creds[0], self.creds[1], base, rel, vol, selected_price).json()
                    if 'error' in resp:
                        if resp['error'].find("larger than available") > -1:
                            msg = "Insufficient funds to complete order."
                        else:
                            msg = resp
                    elif 'result' in resp:
                        trade_val = round(float(selected_price)*float(vol),8)
                        msg = "Order Submitted.\n"
                        msg += "Buying "+str(trade_val)+" "+rel +"\nfor\n"+" "+str(vol)+" "+base
                    else:
                        msg = resp
                    QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            else:
                msg = "No order selected!"
                QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)
        else:
            msg = "No order selected!"
            QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)

    ## PAGE IS HALF DONE, NEEDS SELL BITS POST MERGE
    def show_mm2_trading_tab(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            self.update_mm2_orders_tables()
            self.show_mm2_trades()
            index = self.mm2_buy_buy_combo.currentIndex()
            if index != -1:
                base = self.mm2_buy_buy_combo.itemText(index)
            else:
                base = ''
            index = self.mm2_buy_sell_combo.currentIndex()
            if index != -1:
                rel = self.mm2_buy_sell_combo.itemText(index)
            else:
                rel = ''
            active_coins_selection = self.active_coins[:]
            base = self.update_combo(self.mm2_buy_buy_combo,active_coins_selection,base)
            active_coins_selection.remove(base)
            rel = self.update_combo(self.mm2_buy_sell_combo,active_coins_selection,rel)

            active_coins_selection = self.active_coins[:]
            self.update_combo(self.mm2_sell_sell_combo,active_coins_selection,rel)
            active_coins_selection.remove(rel)
            self.update_combo(self.mm2_sell_buy_combo,active_coins_selection,base)
            # Update labels
            self.mm2_buy_amount_lbl.setText("Amount ("+base+")")
            self.mm2_buy_price_lbl.setText("Price ("+rel+")")
            self.mm2_buy_depth_baserel_lbl.setText(rel+"/"+base)
            self.mm2_buy_bal_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+rel.lower()+".png\"/></p></body></html>")
            self.mm2_sell_amount_lbl.setText("Amount ("+rel+")")
            self.mm2_sell_price_lbl.setText("Price ("+base+")")
            self.mm2_sell_depth_baserel_lbl.setText(base+"/"+rel)
            self.mm2_sell_bal_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+base.lower()+".png\"/></p></body></html>")

            if rel not in self.balances_data:
                self.update_balance(rel)
            balance_info = self.balances_data[rel]
            if 'address' in balance_info:
                address = balance_info['address']
                balance_text = balance_info['balance']
                locked_text = balance_info['locked']
                available_balance = balance_info['available']

                self.mm2_buy_balance_lbl.setText("Available funds: "+str(available_balance)+" "+rel)
                self.mm2_buy_locked_lbl.setText("Locked by swaps: "+str(locked_text)+" "+rel)

            if base not in self.balances_data:
                self.update_balance(base)
            balance_info = self.balances_data[base]
            if 'address' in balance_info:
                address = balance_info['address']
                balance_text = balance_info['balance']
                locked_text = balance_info['locked']
                available_balance = balance_info['available']

                self.mm2_sell_balance_lbl.setText("Available funds: "+str(available_balance)+" "+base)
                self.mm2_sell_locked_lbl.setText("Locked by swaps: "+str(locked_text)+" "+base)

            self.mm2_buy_depth_table.setHorizontalHeaderLabels(['Price '+base, 'Volume '+rel, 'Value '+base])
            self.mm2_sell_depth_table.setHorizontalHeaderLabels(['Price '+rel, 'Volume '+base, 'Value '+rel])

            buy_pair_book = rpclib.orderbook(self.creds[0], self.creds[1], rel, base).json()
            self.mm2_buy_depth_table.setSortingEnabled(False)
            self.clear_table(self.mm2_buy_depth_table)
            if 'error' in buy_pair_book:
                pass
            elif 'asks' in buy_pair_book:
                row = 0
                for item in buy_pair_book['asks']:
                    price = round(float(item['price']), 8)
                    volume = round(float(item['maxvolume']), 8)
                    val = float(item['price'])*float(item['maxvolume'])
                    value = round(val, 8)
                    depth_row = [price, volume, value]
                    self.add_row(row, depth_row, self.mm2_buy_depth_table)
                    row += 1
            self.mm2_buy_depth_table.setSortingEnabled(True)

            sell_pair_book = rpclib.orderbook(self.creds[0], self.creds[1], base, rel).json()
            self.mm2_sell_depth_table.setSortingEnabled(False)
            self.clear_table(self.mm2_sell_depth_table)
            if 'error' in sell_pair_book:
                pass
            elif 'asks' in sell_pair_book:
                row = 0
                for item in sell_pair_book['asks']:
                    price = round(float(item['price']), 8)
                    volume = round(float(item['maxvolume']), 8)
                    val = float(item['price'])*float(item['maxvolume'])
                    value = round(val, 8)
                    depth_row = [price, volume, value]
                    self.add_row(row, depth_row, self.mm2_sell_depth_table)
                    row += 1
            self.mm2_sell_depth_table.setSortingEnabled(True)
        pass

    def combo_box_switch(self):
        index = self.mm2_sell_buy_combo.currentIndex()
        if index != -1:
            base = self.mm2_sell_buy_combo.itemText(index)
        else:
            base = ''
        index = self.mm2_sell_sell_combo.currentIndex()
        if index != -1:
            rel = self.mm2_sell_sell_combo.itemText(index)
        else:
            rel = ''
        active_coins_selection = self.active_coins[:]
        self.update_combo(self.mm2_sell_sell_combo,active_coins_selection,rel)
        active_coins_selection.remove(rel)
        self.update_combo(self.mm2_sell_buy_combo,active_coins_selection,base)
        
        active_coins_selection = self.active_coins[:]
        base = self.update_combo(self.mm2_buy_buy_combo,active_coins_selection,base)
        active_coins_selection.remove(base)
        rel = self.update_combo(self.mm2_buy_sell_combo,active_coins_selection,rel)
        self.show_mm2_trading_tab()

    def populate_buy_order_vals(self):
        val = self.get_cell_val(self.mm2_buy_depth_table, 0)
        if val == '':
            selected_price = 0
        else:
            selected_price = float(val)
        self.mm2_buy_price.setValue(selected_price)

    def populate_sell_order_vals(self):
        val = self.get_cell_val(self.mm2_sell_depth_table, 0)
        if val == '':
            selected_price = 0
        else:
            selected_price = float(val)
        self.mm2_sell_price.setValue(selected_price)

    def get_bal_pct(self, bal_lbl, pct):
        bal = float(bal_lbl.text().split()[2])
        return  bal*pct/100

    def sell_25pct(self):
        val = self.get_bal_pct(self.mm2_sell_balance_lbl, 25)
        self.mm2_sell_amount.setValue(val)

    def sell_50pct(self):
        val = self.get_bal_pct(self.mm2_sell_balance_lbl, 50)
        self.mm2_sell_amount.setValue(val)

    def sell_75pct(self):
        val = self.get_bal_pct(self.mm2_sell_balance_lbl, 75)
        self.mm2_sell_amount.setValue(val)

    def sell_100pct(self):
        val = self.get_bal_pct(self.mm2_sell_balance_lbl, 100)
        self.mm2_sell_amount.setValue(val)

    def buy_25pct(self):
        val = self.get_bal_pct(self.mm2_buy_balance_lbl, 25)
        self.mm2_buy_amount.setValue(val)

    def buy_50pct(self):
        val = self.get_bal_pct(self.mm2_buy_balance_lbl, 50)
        self.mm2_buy_amount.setValue(val)

    def buy_75pct(self):
        val = self.get_bal_pct(self.mm2_buy_balance_lbl, 75)
        self.mm2_buy_amount.setValue(val)

    def buy_100pct(self):
        val = self.get_bal_pct(self.mm2_buy_balance_lbl, 100)
        self.mm2_buy_amount.setValue(val)

    def create_setprice_buy(self): 
        index = self.mm2_buy_sell_combo.currentIndex()
        rel = self.mm2_buy_sell_combo.itemText(index)
        index = self.mm2_buy_buy_combo.currentIndex()
        base = self.mm2_buy_buy_combo.itemText(index)
        basevolume = self.mm2_buy_amount.value()
        relprice = self.mm2_buy_price.value()
        # detect previous
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
                        msg = "Cancel all previous "+rel+"/"+base+" orders?"
                        break
                if msg != '':
                    confirm = QMessageBox.question(self, msg_title, msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                    if confirm == QMessageBox.No:
                        cancel_previous = False
                    elif confirm == QMessageBox.Cancel:
                        cancel_trade = True
        max_vol = float(self.mm2_buy_balance_lbl.text().split()[2])
        val = self.mm2_buy_amount.value()
        if val == max_vol:
            trade_max = True
        else:
            trade_max = False
        if not cancel_trade:
            #resp = rpclib.buy(self.creds[0], self.creds[1], base, rel, basevolume, relprice)
            resp = rpclib.setprice(self.creds[0], self.creds[1], base, rel, basevolume, relprice, trade_max, cancel_previous).json()
            if 'error' in resp:
                if resp['error'].find("larger than available") > -1:
                    msg = "Insufficient funds to complete order."
                else:
                    msg = resp
            elif 'result' in resp:
                trade_val = round(float(relprice)*float(basevolume),8)
                msg = "Order Submitted.\n"
                msg += "Buy "+str(basevolume)+" "+base+"\nfor\n"+" "+str(trade_val)+" "+rel
                self.update_mm2_orders_tables()
                self.show_mm2_trades()
            else:
                msg = resp
            QMessageBox.information(self, 'Created Setprice Buy Order', str(msg), QMessageBox.Ok, QMessageBox.Ok)

    def create_setprice_sell(self): 
        index = self.mm2_sell_sell_combo.currentIndex()
        base = self.mm2_sell_sell_combo.itemText(index)
        index = self.mm2_sell_buy_combo.currentIndex()
        rel = self.mm2_sell_buy_combo.itemText(index)
        basevolume = self.mm2_sell_amount.value()
        relprice = self.mm2_sell_price.value()
        # detect previous
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
                        msg = "Cancel all previous "+rel+"/"+base+" orders?"
                        break
                if msg != '':
                    confirm = QMessageBox.question(self, msg_title, msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                    if confirm == QMessageBox.No:
                        cancel_previous = False
                    elif confirm == QMessageBox.Cancel:
                        cancel_trade = True
        max_vol = float(self.mm2_sell_balance_lbl.text().split()[2])
        val = self.mm2_sell_amount.value()
        if val == max_vol:
            trade_max = True
        else:
            trade_max = False
        if not cancel_trade:
            resp = rpclib.setprice(self.creds[0], self.creds[1], base, rel, basevolume, relprice, trade_max, cancel_previous).json()
            if 'error' in resp:
                if resp['error'].find("larger than available") > -1:
                    msg = "Insufficient funds to complete order."
                else:
                    msg = resp
            elif 'result' in resp:
                trade_val = round(float(relprice)*float(basevolume),8)
                msg = "Order Submitted.\n"
                msg += "Sell "+str(basevolume)+" "+base+"\nfor\n"+" "+str(trade_val)+" "+rel
                self.update_mm2_orders_tables()
                self.show_mm2_trades()
            else:
                msg = resp
            QMessageBox.information(self, 'Created Setprice Sell Order', str(msg), QMessageBox.Ok, QMessageBox.Ok)


    ## PRICES
    def show_prices_tab(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))

    ## WALLET
    def show_mm2_wallet_tab(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:

            self.wallet_recipient.setFocus()
            existing_coins = []
            for i in range(self.wallet_combo.count()):
                existing_coin = self.wallet_combo.itemText(i)
                existing_coins.append(existing_coin)
            for coin in self.active_coins:
                if coin not in existing_coins:
                    self.wallet_combo.addItem(coin)
            index = self.wallet_combo.currentIndex()
            coin = self.wallet_combo.itemText(index)
            self.wallet_coin_img.setText("<html><head/><body><p><img src=\":/300/img/300/"+coin.lower()+".png\"/></p></body></html>")
            if coin not in self.balances_data:
                self.update_balance(coin)
            balance_info = self.balances_data[coin]
            if 'address' in balance_info:
                address = balance_info['address']
                balance_text = balance_info['balance']
                locked_text = balance_info['locked']
                available_balance = balance_info['available']
            if coinslib.coin_explorers[coin]['addr_explorer'] != '':
                self.wallet_address.setText("<a href='"+coinslib.coin_explorers[coin]['addr_explorer']+"/"+address+"'>"+address+"</href>")
            else:
                self.wallet_address.setText(address)
            self.wallet_balance_lbl.setText(str(coin+" BALANCE"))
            self.wallet_balance.setText(str(balance_text))
            self.wallet_locked_by_swaps.setText("("+str(locked_text)+" locked by swaps)")

            if coin in self.prices_data:
                btc_price = self.prices_data[coin]['average_btc']
                usd_price = self.prices_data[coin]['average_usd']
            elif coinslib.coin_api_codes[coin]['paprika_id'] != '':
                price = priceslib.get_paprika_price(coinslib.coin_api_codes[coin]['paprika_id']).json()
                usd_price = float(price['price_usd'])
                btc_price = float(price['price_btc'])
            elif coinslib.coin_api_codes[coin]['coingecko_id'] != '':
                price = priceslib.gecko_fiat_prices(coinslib.coin_api_codes[coin]['coingecko_id'], 'usd,btc').json()
                usd_price = float(price['usd'])
                btc_price = float(price['btc'])
            else:
                usd_price = 'No Data'
                btc_price = 'No Data'
            if btc_price != 'No Data':
                self.wallet_usd_value.setText("$"+str(round(balance_text*usd_price,2))+" USD")
                self.wallet_btc_value.setText(str(round(balance_text*btc_price,6))+" BTC")
            else:
                self.wallet_usd_value.setText("")
                self.wallet_btc_value.setText("")

            self.wallet_qr_code.setPixmap(qrcode.make(address, image_factory=QR_image, box_size=4).pixmap())
<<<<<<< HEAD
=======
            '''
            tx_history = rpclib.my_tx_history(self.creds[0], self.creds[1], coin, 10).json()
            row = 0
            self.clear_table(self.wallet_tx_table)
            self.wallet_tx_table.setSortingEnabled(False)
            rows = len(tx_history['result']['transactions'])
            self.wallet_tx_table.setRowCount(rows)
            for tx in tx_history['result']['transactions']:
                blockheight = tx['block_height']
                timestamp = datetime.datetime.fromtimestamp(int(tx['timestamp']/1000)*1000) 
                my_balance_change = float(tx['my_balance_change'])
                if address != tx['from'][0]:
                    tx_address = tx['from'][0]
                elif address != tx['to'][1]:
                    tx_address = tx['to'][1]
                else:
                    tx_address = tx['to'][0]
                tx_hash = tx['tx_hash']
                tx_row = [timestamp, blockheight, my_balance_change, tx_address, tx_hash]
                self.add_row(row, tx_row, self.wallet_tx_table)
                row += 1
            self.wallet_tx_table.setSortingEnabled(True)
            '''
>>>>>>> 88dd9349fa025172898474553a95e044c783d160

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
                if 'tx_hash' in resp:
                    txid = resp['tx_hash']
                    if recipient_addr.startswith('0x'):
                        txid_str = '0x'+txid
                    else:
                        txid_str = txid
                    if coinslib.coin_explorers[cointag]['tx_explorer'] != '':
                        msg = "Sent! \n<a href='"+coinslib.coin_explorers[cointag]['tx_explorer']+"/"+txid_str+"'>[Link to block explorer]</href>"
                    else:
                        msg = "Sent! \nTXID: ["+txid_str+"]"

                    self.update_balance(cointag)
                    balance_info = self.balances_data[cointag]
                    if 'address' in balance_info:
                        address = balance_info['address']
                        balance_text = balance_info['balance']
                        locked_text = balance_info['locked']
                        available_balance = balance_info['available']
                        self.wallet_balance.setText(str(balance_text))
            else:
                msg = str(resp)
            QMessageBox.information(self, 'Wallet transaction', msg, QMessageBox.Ok, QMessageBox.Ok)
        pass

    ## CONFIG
    def show_config_tab(self):
        if self.creds[0] != '':
            self.rpcpass_text_input.setText(self.creds[1])
            self.seed_text_input.setText(self.creds[2])
            self.netid_input.setValue(self.creds[3])
            self.rpc_ip_text_input.setText(self.creds[4])
            self.binance_key_text_input.setText(self.creds[5])
            self.binance_secret_text_input.setText(self.creds[6])
            self.margin_input.setValue(float(self.creds[7]))
            if self.creds[4] == '127.0.0.1':
                self.checkbox_local_only.setChecked(True)
            else:
                self.checkbox_local_only.setChecked(False)

    def set_localonly(self):
        local_only = self.checkbox_local_only.isChecked()
        if local_only:
            rpc_ip = '127.0.0.1'
            self.rpc_ip_text_input.setReadOnly(True)
            self.rpc_ip_text_input.setText(rpc_ip)
        else:
            self.rpc_ip_text_input.setReadOnly(False)

    def save_config(self):
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
        margin = self.margin_input.text()
        netid = self.netid_input.text()
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
                        enc_data = enc.encrypt_mm2_json(json.dumps(data), passwd)
                        with open(config_path+self.username+"_MM2.enc", 'w') as j:
                            j.write(bytes.decode(enc_data))
                        QMessageBox.information(self, 'Settings file created', "Settings updated. Please login again.", QMessageBox.Ok, QMessageBox.Ok)

                        print("stop_mm2 with old creds")
                        try:
                            rpclib.stop_mm2(self.creds[0], self.creds[1])
                        except Exception as e:
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
    
    def generate_seed(self):
        seed_words_list = []
        while len(seed_words_list) < 24:
            word = random.choice(wordlist.wordlist)
            if word not in seed_words_list:
                seed_words_list.append(word)
        seed_phrase = " ".join(seed_words_list)
        self.seed_text_input.setText(seed_phrase)

    ## LOGS
    def export_logs(self):
        pass

    def show_mm2_logs_tab(self):
        print("show_mm2_logs_tab")
        logfile='mm2_output.log'
        mm2_output = open(config_path+self.username+logfile,'r')
        with mm2_output as f:
            log_text = f.read()
            lines = f.readlines()
            self.scrollbar = self.console_logs.verticalScrollBar()
            self.console_logs.setPlainText(log_text)
            self.scrollbar.setValue(10000)
        pass

    ## BINANCE API
    def show_binance_trading_tab(self):
        tickers = self.update_binance_balance_table()
        print("Binance Tickers: "+str(tickers))
        if tickers is not None:
            self.update_combo(self.binance_asset_comboBox,tickers,tickers[0])
            ticker_pairs = []
            for ticker in tickers:
                if ticker != "BTC":
                    ticker_pairs.append(ticker+"BTC")
            self.update_combo(self.binance_ticker_pair_comboBox,ticker_pairs,ticker_pairs[0])
            self.update_binance_orderbook()
            QCoreApplication.processEvents()
            self.update_orders_table()
            QCoreApplication.processEvents()
            self.update_binance_addr()

    def update_binance_addr(self):
        index = self.binance_asset_comboBox.currentIndex()
        coin = self.binance_asset_comboBox.itemText(index)
        resp = binance_api.get_deposit_addr(self.creds[5], self.creds[6], coin)
        if 'address' in resp:
            addr_text = resp['address']
        else:
            addr_text = 'Address not found - create it at Binance.com'

        self.binance_addr_lbl.setText(addr_text)
        self.binance_addr_coin_lbl.setText("Binance "+str(coin)+" Address")
        QCoreApplication.processEvents()
        self.update_history_graph()

    def show_qr_popup(self):
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
<<<<<<< HEAD
        print("show Binance QR code msgbox")
=======
        print("show msgbox")
>>>>>>> 88dd9349fa025172898474553a95e044c783d160
        msgBox.exec()

    def update_history_graph(self):
        index = self.binance_asset_comboBox.currentIndex()
        coin = self.binance_asset_comboBox.itemText(index)
        index = self.history_quote_combobox.currentIndex()
        quote = self.history_quote_combobox.itemText(index).lower()
        if self.history_1yr_btn.isChecked():
            since = 'year_ago'
        elif self.history_6mth_btn.isChecked():
            since = '6_month_ago'
        elif self.history_3mth_btn.isChecked():
            since = '3_month_ago'
        elif self.history_1mth_btn.isChecked():
            since = 'month_ago'
        elif self.history_1wk_btn.isChecked():
            since = 'week_ago'
        elif self.history_24hr_btn.isChecked():
            since = 'day_ago'
        coin_id = coinslib.coin_api_codes[coin]['paprika_id']
        if coin_id != '':
            history = priceslib.get_paprika_history(coin_id, since, quote)
            x = []
            x_str = []
            y = []
            time_ticks = []
            val_ticks = []
            self.xy = {}
            last_time = ''
            for item in history:
                y.append(item['price'])
                dt = dateutil.parser.parse(item['timestamp'])
                x.append(int(datetime.datetime.timestamp(dt)))
                x_str.append(item['timestamp'])
                if since in ['year_ago']:
                    month = time.ctime(int(datetime.datetime.timestamp(dt))).split(" ")[1]
                    if month != last_time:
                        if last_time != '':
                            time_ticks.append((int(datetime.datetime.timestamp(dt)),month))
                        last_time = month
                elif since in ['6_month_ago']:
                    time_components = (time.ctime(int(datetime.datetime.timestamp(dt))).split(" "))
                    if time_components[2] in ['15']:
                        time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[2]+" "+time_components[1]))
                    elif time_components[3] in ['1']:
                        time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[3]+" "+time_components[1]))
                elif since in ['3_month_ago']:
                    time_components = (time.ctime(int(datetime.datetime.timestamp(dt))).split(" "))
                    if time_components[2] in ['15', '22']:
                        if time_components[2] != last_time:
                            time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[2]+" "+time_components[1]))
                            last_time = time_components[2]
                    if time_components[3] in ['1', '8']:
                        if time_components[3] != last_time:
                            time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[3]+" "+time_components[1]))
                            last_time = time_components[3]                            
                elif since in ['month_ago']:
                    time_components = (time.ctime(int(datetime.datetime.timestamp(dt))).split(" "))
                    if time_components[2] in ['10', '13', '16', '19', '22', '25', '28']:
                        if time_components[2] != last_time:
                            time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[2]+" "+time_components[1]))
                            last_time = time_components[2]
                    elif time_components[3] in ['1', '4', '7']:
                        if time_components[3] != last_time:
                            time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[3]+" "+time_components[1]))
                            last_time = time_components[3]
                elif since in ['week_ago']:
                    time_components = (time.ctime(int(datetime.datetime.timestamp(dt))).split(" "))
                    if time_components[0] != last_time:
                        time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[0]+" "+time_components[2]+" "+time_components[1]))
                        last_time = time_components[0]
                elif since in ['day_ago']:
                    time_components = (time.ctime(int(datetime.datetime.timestamp(dt))).split(" "))
                    hour_components = time_components[3].split(":")
                    if int(hour_components[0])%2 == 0:
                        if hour_components[0] != last_time:
                            time_ticks.append((int(datetime.datetime.timestamp(dt)),time_components[3]))
                            last_time = hour_components[0]

                self.xy.update({str(int(datetime.datetime.timestamp(dt))):item['price']})

            self.binance_history_graph.setYRange(0,max(y)*1.1, padding=0)
            self.binance_history_graph.setXRange(min(x),max(x), padding=0)
            self.binance_history_graph.clear()
            price_curve = self.binance_history_graph.plot(
                    x,
                    y, 
                    pen={'color':(78,155,46)},
                    fillLevel=0, brush=(50,50,200,100),
                )
            self.binance_history_graph.addItem(price_curve)
            if quote == 'usd':
                self.binance_history_graph.setLabel('left', '$USD')
            else:
                self.binance_history_graph.setLabel('left', 'BTC')
            self.binance_history_graph.setLabel('bottom', '', units=None)
            self.binance_history_graph.showGrid(x=True, y=True, alpha=0.2)
            price_ticks = self.binance_history_graph.getAxis('left')
            date_ticks = self.binance_history_graph.getAxis('bottom')    
            date_ticks.setTicks([time_ticks])
            date_ticks.enableAutoSIPrefix(enable=False)
            #self.vLine = crosshair_lines(pen={'color':(78,155,46)}, angle=90, movable=False)
            #self.vLine.sigPositionChangeFinished.connect(self.getDatePrice)
            #self.binance_history_graph.addItem(self.vLine, ignoreBounds=True)
            self.binance_history_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+coin.lower()+".png\"/></p></body></html>")

            if coin in self.prices_data:
                btc_price = self.prices_data[coin]['average_btc']
                usd_price = self.prices_data[coin]['average_usd']
            elif coinslib.coin_api_codes[coin]['paprika_id'] != '':
                price = priceslib.get_paprika_price(coinslib.coin_api_codes[coin]['paprika_id']).json()
                usd_price = float(price['price_usd'])
                btc_price = float(price['price_btc'])
            elif coinslib.coin_api_codes[coin]['coingecko_id'] != '':
                price = priceslib.gecko_fiat_prices(coinslib.coin_api_codes[coin]['coingecko_id'], 'usd,btc').json()
                usd_price = float(price['usd'])
                btc_price = float(price['btc'])
            else:
                usd_price = 'No Data'
                btc_price = 'No Data'
            if quote == 'usd':
                txt='<div style="text-align: center"><span style="color: #FFF;font-size:10pt;">Current USD Price: $'+str(usd_price)+'</span></div>'
            else:
                txt='<div style="text-align: center"><span style="color: #FFF;font-size:10pt;">Current BTC Price: $'+str(btc_price)+'</span></div>'
            text = pg.TextItem(html=txt, anchor=(0,0), border='w', fill=(0, 0, 255, 100))
            self.binance_history_graph.addItem(text)
            text.setPos(min(x)+(max(x)-min(x))*0.02,max(y))

    def getDatePrice(self):
        min_delta = 999999999999
        xpos = self.vLine.getXPos()
        for item in self.xy:
            delta = abs(int(item) - xpos)
            if delta < min_delta:
                min_delta = delta
                ref_time = item
                ref_price = self.xy[str(item)]

    def getPrice(self, x):
        min_delta = 999999999999
        for item in self.xy:
            delta = abs(int(item) - x)
            if delta < min_delta:
                min_delta = delta
                ref_time = item
                ref_price = self.xy[str(item)]
        return ref_price


    def update_binance_balance_table(self):
        acct_info = binance_api.get_account_info(self.creds[5], self.creds[6])
        if 'msg' in acct_info:
            QMessageBox.information(self, 'Binance API key error!', str(acct_info['msg']), QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))
        else:
            tickers = []
            if 'balances' in acct_info:
                self.clear_table(self.binance_balances_table)
                self.binance_balances_table.setSortingEnabled(False)
                rows = len(acct_info['balances'])
                self.binance_balances_table.setRowCount(rows)
                row = 0
                for item in acct_info['balances']:
                    coin = item['asset']
                    available = float(item['free'])
                    locked = float(item['locked'])
                    balance = locked + available
                    if balance > 0 or coin in coinslib.binance_coins:
                        tickers.append(coin)
                    balance_row = [coin, balance, available, locked]
                    self.add_row(row, balance_row, self.binance_balances_table)
                    row += 1
                self.binance_balances_table.setSortingEnabled(True)
            return tickers

    def update_binance_orderbook(self):
        index = self.binance_ticker_pair_comboBox.currentIndex()
        self.binance_price_spinbox.setValue(0)
        ticker_pair = self.binance_ticker_pair_comboBox.itemText(index)
        depth_limit = 20
        orderbook = binance_api.get_depth(self.creds[5], ticker_pair, depth_limit)
        self.clear_table(self.binance_orderbook_table)
        self.binance_orderbook_table.setSortingEnabled(False)
        self.binance_orderbook_table.setRowCount(26)
        row = 0
        for item in orderbook['bids']:
            price = float(item[0])
            volume = float(item[1])
            balance_row = [ticker_pair, price, volume, 'bid']
            self.add_row(row, balance_row, self.binance_orderbook_table, QColor(255, 181, 181))
            if row == 12: 
                break
            row += 1

        for item in orderbook['asks']:
            price = float(item[0])
            volume = float(item[1])
            balance_row = [ticker_pair, price, volume, 'ask']
            self.add_row(row, balance_row, self.binance_orderbook_table, QColor(218, 255, 127))
            if row == 25: 
                break
            row += 1
        self.binance_orderbook_table.setSortingEnabled(True)
        self.binance_orderbook_table.sortItems(1)
        base = ticker_pair.replace("BTC","")
        self.binance_sell_btn.setText("Sell "+base)
        self.binance_buy_btn.setText("Buy "+base)

    def update_binance_price_val(self):
        selected_row = self.binance_orderbook_table.currentRow()
        price = self.binance_orderbook_table.item(selected_row,1).text()
        order_type = self.binance_orderbook_table.item(selected_row,3).text()
        self.binance_price_spinbox.setValue(float(price))

    def binance_buy(self):
        qty = '{:.8f}'.format(self.binance_qty_spinbox.value())
        price = '{:.8f}'.format(self.binance_price_spinbox.value())
        index = self.binance_ticker_pair_comboBox.currentIndex()
        ticker_pair = self.binance_ticker_pair_comboBox.itemText(index)
        resp = binance_api.create_buy_order(self.creds[5], self.creds[6], ticker_pair, qty, price)
        if 'orderId' in resp:
            msg = "Order submitted!"
            QMessageBox.information(self, 'Sell Order Sent', msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Sell Order Failed', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.update_orders_table()

    def binance_sell(self):
        qty = '{:.8f}'.format(self.binance_qty_spinbox.value())
        price = '{:.8f}'.format(self.binance_price_spinbox.value())
        index = self.binance_ticker_pair_comboBox.currentIndex()
        ticker_pair = self.binance_ticker_pair_comboBox.itemText(index)
        resp = binance_api.create_sell_order(self.creds[5], self.creds[6], ticker_pair, qty, price)
        if 'orderId' in resp:
            msg = "Order submitted!"
            QMessageBox.information(self, 'Sell Order Sent', msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Sell Order Failed', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.update_orders_table()


    def binance_withdraw(self):
        index = self.binance_asset_comboBox.currentIndex()
        asset = self.binance_asset_comboBox.itemText(index)
        addr = self.binance_withdraw_addr_lineEdit.text()
        amount = self.binance_withdraw_amount_spinbox.value()
        msg = ''
        '''
        # This API method is returning error 500
        resp = binance_api.asset_detail(self.creds[5], self.creds[6])
        min_withdraw = resp['asset_detail'][asset]['minWithdrawAmount']
        fee = resp['asset_detail'][asset]['withdrawFee']
        status = resp['asset_detail'][asset]['withdrawStatus']
        proceed = True
        if amount < float(min_withdraw):
            msg += "Withdraw amount is less than Binance minimum!"
            proceed = False
        if not status:
            msg += "Withdrawl of "+asset+" is currently suspended on Binance!"
            proceed = False
        if not proceed:
            QMessageBox.information(self, 'Binance Withdraw', str(msg), QMessageBox.Ok, QMessageBox.Ok)

        else:
        '''
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

    def update_orders_table(self):
        open_orders = binance_api.get_open_orders(self.creds[5], self.creds[6])
        if 'msg' in open_orders:
            QMessageBox.information(self, 'Binance API key error!', str(open_orders['msg']), QMessageBox.Ok, QMessageBox.Ok)
        self.clear_table(self.binance_orders_table)
        self.binance_orders_table.setSortingEnabled(False)
        self.binance_orders_table.setRowCount(len(open_orders))
        row = 0
        for item in open_orders:
            order_id = item['orderId']
            side = item['side']
            symbol = item['symbol']
            price = item['price']
            qty = item['origQty']
            filled = item['executedQty']
            time = datetime.datetime.fromtimestamp(int(item['time']/1000))
            balance_row = [order_id, side, symbol, price, qty, filled, time]
            self.add_row(row, balance_row, self.binance_orders_table)
            row += 1
        self.binance_orders_table.setSortingEnabled(True)

    def binance_cancel_selected_order(self):
        selected_row = self.binance_orders_table.currentRow()
        if self.binance_orders_table.item(selected_row,0) is not None:
            if self.binance_orders_table.item(selected_row,0).text() != '':
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
                QMessageBox.information(self, 'Order Cancelled', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            QMessageBox.information(self, 'Order Cancelled', 'No orders selected!', QMessageBox.Ok, QMessageBox.Ok)        
        self.update_orders_table()

    def binance_cancel_all_orders(self):
        open_orders = binance_api.get_open_orders(self.creds[5], self.creds[6])
        order_ids = []
        for item in open_orders:
            order_ids.append([item['orderId'],item['symbol']])
        for order_id in order_ids:
            binance_api.delete_order(self.creds[5], self.creds[6], order_id[1], order_id[0])
            time.sleep(0.05)
            self.update_orders_table()
        QMessageBox.information(self, 'Order Cancelled', 'All orders cancelled!', QMessageBox.Ok, QMessageBox.Ok)


    ## BOT TRADES
    def show_bot_trading_tab(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            self.populate_bot_lists()

    def populate_bot_lists(self):
        self.bot_buy_list.clear()
        self.bot_sell_list.clear()
        for buy_coin in self.buy_coins:
            if buy_coin not in self.active_coins:
                buy_coin = buy_coin+ " (inactive)"
            elif buy_coin not in coinslib.binance_coins:
                buy_coin = buy_coin+ " (not on Binance)"
            self.bot_buy_list.addItem(buy_coin)
        for sell_coin in self.sell_coins:
            if sell_coin not in self.active_coins:
                sell_coin = sell_coin+ " (inactive)"
            elif sell_coin not in coinslib.binance_coins:
                sell_coin = sell_coin+ " (not on Binance)"
            self.bot_sell_list.addItem(sell_coin)

    def stop_bot_trading(self):
        print("stopping bot")
        self.bot_trade_thread.stop()
        self.bot_status_lbl.setText("STOPPED")
        self.bot_status_lbl.setStyleSheet("color: rgb(164, 0, 0);\nbackground-color: rgb(177, 179, 186);")
        timestamp = int(time.time()/1000)*1000
        time_str = datetime.datetime.fromtimestamp(timestamp)
        self.bot_log_list.addItem(str(time_str)+" Bot stopped")
        resp = QMessageBox.information(self, 'Cancel orders?', 'Cancel all orders?\nAlternatively, you can cancel individually\nby selecting orders from the open orders table. ', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.mm2_cancel_all_orders()

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
            premium = self.margin_input.value()/100
            self.bot_trade_thread = bot_trading_thread(self.creds, self.sell_coins, self.buy_coins, self.active_coins, premium)
            self.bot_trade_thread.trigger.connect(self.update_bot_log)
            self.bot_trade_thread.start()
            self.bot_status_lbl.setText("ACTIVE")
            self.bot_status_lbl.setStyleSheet('color: #043409;\nbackground-color: rgb(166, 215, 166);')
            timestamp = int(time.time()/1000)*1000
            time_str = datetime.datetime.fromtimestamp(timestamp)
            self.bot_log_list.addItem(str(time_str)+" Bot started")
        else:
            msg = 'Please activate at least one sell coin and at least one different buy coin (Binance compatible). '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))

    def update_bot_log(self, log_msg, log_result):
        self.bot_log_list.addItem(log_msg)
        self.bot_log_list.addItem(">>> "+str(log_result))
        self.update_mm2_orders_tables()

    ## TABS
    def update_cachedata(self, prices_dict, balaces_dict):
        print("updating cache data from thread")
        self.prices_data = prices_dict
        self.balances_data = balaces_dict
        self.prices_table.setSortingEnabled(False)
        self.clear_table(self.prices_table)
        row = 0
        for item in self.prices_data:
            if item in self.active_coins:
                coin = item
                try:
                    api_btc_price = str(round(self.prices_data[item]["average_btc"],8))+" ₿"
                except:
                    api_btc_price = "-"
                try:
                    mm2_btc_price = str(round(self.prices_data[item]["mm2_btc_price"],8))+" ₿"
                except:
                    mm2_btc_price = "-"
                try:
                    delta_btc_price = str(round(self.prices_data[item]["mm2_btc_price"]-self.prices_data[item]["average_btc"],8))+" ₿"
                except:
                    delta_btc_price = "-"
                try:
                    api_kmd_price = round(self.prices_data[item]["kmd_price"],6)
                except:
                    api_kmd_price = "-"
                try:
                    mm2_kmd_price = round(self.prices_data[item]["mm2_kmd_price"],6)
                except:
                    mm2_kmd_price = "-"
                try:
                    delta_kmd_price = round(self.prices_data[item]["mm2_kmd_price"]-self.prices_data[item]["kmd_price"],6)
                except:
                    delta_kmd_price = "-"
                try:
                    api_usd_price = "$"+str(round(self.prices_data[item]["average_usd"],4))+" USD"
                except:
                    api_usd_price = "-"
                try:
                    mm2_usd_price = "$"+str(round(self.prices_data[item]["mm2_usd_price"],4))+" USD"
                except:
                    mm2_usd_price = "-"
                try:
                    delta_usd_price = "$"+str(round(self.prices_data[item]["mm2_usd_price"]-self.prices_data[item]["average_usd"],4))+" USD"
                except:
                    delta_usd_price = "-"
                sources = self.prices_data[item]["sources"]
                price_row = [coin, api_btc_price, mm2_btc_price, delta_btc_price,
                             api_kmd_price, mm2_kmd_price, delta_kmd_price,
                             api_usd_price, mm2_usd_price, delta_usd_price,
                             sources]
                self.add_row(row, price_row, self.prices_table)
                row += 1
        



    def prepare_tab(self):
        try:
            self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
            if self.last_price_update < int(time.time()) - 120:
                self.last_price_update = int(time.time())
                self.datacache_thread = cachedata_thread(self.creds)
                self.datacache_thread.trigger.connect(self.update_cachedata)
                self.datacache_thread.start()
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
                # prices
                print('show_prices_tab')
                self.show_prices_tab()
            elif index == 3:
                # wallet
                print('show_mm2_wallet_tab')
                self.show_mm2_wallet_tab()
            elif index == 4:
                # mm trade
                print('makerbot_trade')
                self.show_mm2_trading_tab()
            elif index == 5:
                # binance acct
                print('binance_acct')
                self.show_binance_trading_tab()
            elif index == 6:
                # bot trade
                print('bot_trades')
                self.show_bot_trading_tab()
            elif index == 7:
                # config
                print('show_config_tab')
                self.show_config_tab()
            elif index == 8:
                # logs
                print('show_mm2_logs_tab')
                self.show_mm2_logs_tab()
        else:
            print('show_activation_tab - login')
            self.stacked_login.setCurrentIndex(0)
            index = self.currentIndex()
            if index != 0:
                QMessageBox.information(self, 'Unauthorised access!', 'You must be logged in to access this tab', QMessageBox.Ok, QMessageBox.Ok)
            self.show_login_tab()

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
