from fbs_runtime.application_context.PyQt5 import ApplicationContext
import os
import sys
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


# will try graphing later with these imports
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Point import Point

pg.setConfigOption('background', (64,64,64))
pg.setConfigOption('foreground', (78,155,46))

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

global last_price_update
global price_data
global last_balance_update
global balance_data

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

# TODO: set row count at table population based on num records to insert.
# TODO: more images for activate and wallet page
# TODO: Periodic threaded price/balance updates to cache.
# TODO: Dropdowns in alpha order. Might need lambda function.
# TODO: Detect if in activation loop on activate button press. Ignore or add extar coins if checked.
# Update coins file. TODO: more efficient way if doesnt need to be updated?
if 1 == 0:
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
                        balance_text = balance_info['balance']
                        locked_text = balance_info['locked_by_swaps']
                        available_balance = float(balance_info['balance'])-float(balance_info['locked_by_swaps'])
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
                                                msg = "Insufficient funds to complete order."
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

class activation_thread(QThread):
    trigger = pyqtSignal(str)
    def __init__(self, creds, coins_to_activate):
        QThread.__init__(self)
        self.coins =  coins_to_activate
        self.creds = creds

    def __del__(self):
        self.wait()

    # creds[1] to emit signal for buttton stylesheet change
    def run(self):
        active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        for coin in self.coins:
            if coin[0] not in active_coins:
                r = rpclib.electrum(self.creds[0], self.creds[1], coin[0])
                print(guilib.colorize("Activating "+coin[0]+" with electrum", 'cyan'))
                self.trigger.emit(coin[0])

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

class crosshair_lines(pg.InfiniteLine):
    def __init__(self, *args, **kwargs):
        pg.InfiniteLine.__init__(self, *args, **kwargs)
        self.setCursor(Qt.CrossCursor)

class Ui(QTabWidget):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi(script_path+'/ui/makerbot_gui.ui', self) # Load the .ui file
        self.show() # Show the GUI
        self.setWindowTitle("Komodo Platform's Antara Makerbot")
        self.setWindowIcon(QIcon(':/sml/img/32/color/kmd.png'))
        self.authenticated = False
        self.bot_trading = False
        global gui_coins
        gui_coins = {
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
            "COMMOD":{ 
                "checkbox":self.checkBox_commod, 
                "combo":self.commod_combo, 
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
            "WLC":{ 
                "checkbox":self.checkBox_wlc, 
                "combo":self.wlc_combo, 
            },
            "ZEXO":{ 
                "checkbox":self.checkBox_zexo, 
                "combo":self.zexo_combo, 
            },
        }               
        self.show_login()

    ## COMMON
    def saveFileDialog(self):
        filename = ''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save Trade data to CSV","","All Files (*);;Text Files (*.csv)", options=options)
        return fileName

    def export_table(self):
        # get table data
        table_csv = 'Date, Status, Sell coin, Sell volume, Buy coin, Buy volume, Sell price, UUID\r\n'
        for i in range(self.trades_table.rowCount()):
            row_list = []
            for j in range(self.trades_table.columnCount()):
                try:
                    row_list.append(self.trades_table.item(i,j).text())
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

    def get_cell_val(self, table, column):
        if table.currentRow() != -1:
            return float(table.item(table.currentRow(),column).text())
        else:
            return 0

    def update_combo(self,combo,options,selected):
        combo.clear()
        combo.addItems(options)
        if selected in options:
            for i in range(combo.count()):
                if combo.itemText(i) == selected:
                    combo.setCurrentIndex(i)
        else:
            combo.setCurrentIndex(0)
            selected = combo.itemText(combo.currentIndex())
        return selected

    # Runs whenever activation_thread signals a coin has been activated
    # TODO: use this to update other dropdown comboboxes. Careful with buy/sell tabs!
    def update_active(self):
        self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        existing_coins = []
        for i in range(self.wallet_combo.count()):
            existing_coin = self.wallet_combo.itemText(i)
            existing_coins.append(existing_coin)
        for coin in gui_coins:
            if coin in self.active_coins:
                gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(138, 226, 52)")
                if coin not in existing_coins:
                    self.wallet_combo.addItem(coin)
            else:
                gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(114, 159, 207)")

    ## LOGIN 
    def show_login(self):
        self.stacked_login.setCurrentIndex(0)
        self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        self.username_input.setFocus()
        print("show_login")

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
                        with open(config_path+self.username+"_MM2.json", 'w') as j:
                            j.write(mm2_json_decrypted.decode())
                        self.authenticated = True
                    except:
                        print("decrypting failed")
                        # did not decode, bad password
                        pass
            jsonfile = config_path+self.username+"_MM2.json"
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
                            os.environ['MM_CONF_PATH'] = config_path+self.username+"_MM2.json"
                            try:
                                print("starting mm2")
                                guilib.start_mm2()
                                time.sleep(0.6)
                                version = rpclib.version(self.creds[0], self.creds[1]).json()['result']
                                self.mm2_version_lbl.setText("MarketMaker version: "+version+" ")
                            except:
                                pass
                        with open(config_path+self.username+"_MM2.json", 'w') as j:
                            j.write('')
                        self.show_active()
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
            gui_coins[coin]['checkbox'].show()
            gui_coins[coin]['combo'].show()
            layout.addWidget(gui_coins[coin]['checkbox'], row, 0, 1, 1)
            layout.addWidget(gui_coins[coin]['combo'], row, 1, 1, 1)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/sml/img/32/color/"+coin.lower()+".png"), QIcon.Normal, QIcon.Off)
            gui_coins[coin]['checkbox'].setIcon(icon)
            row += 1

    # ACTIVATE
    def show_active(self):
        print("show_active")
        display_coins_erc20 = []
        display_coins_utxo = []
        display_coins_smartchain = []
        search_txt = self.search_activate.text().lower()
        self.update_active()
        for coin in gui_coins:
            gui_coins[coin]['checkbox'].hide()
            gui_coins[coin]['combo'].hide()
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
            gui_coins[coin]['checkbox'].setText(coin_label_txt+coin_label_api)
            if coin.lower().find(search_txt) > -1 or gui_coins[coin]['checkbox'].text().lower().find(search_txt) > -1 or len(search_txt) == 0:
                if coinslib.coin_activation[coin]['type'] == 'utxo':
                    display_coins_utxo.append(coin)
                elif coinslib.coin_activation[coin]['type'] == 'erc20':
                    display_coins_erc20.append(coin)
                elif coinslib.coin_activation[coin]['type'] == 'smartchain':
                    display_coins_smartchain.append(coin)
            # TODO: lambda sort by coin_api_codes['name']
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
        for coin in gui_coins:
            print("---"+coin+"----")
            print(self.buy_coins)
            print(self.sell_coins)
            combo = gui_coins[coin]['combo']
            checkbox = gui_coins[coin]['checkbox']
            if checkbox.isChecked():
                autoactivate.append(coin)
                if coin not in self.active_coins:
                    coins_to_activate.append([coin,combo])
            print(combo.itemText(combo.currentIndex()))
            if combo.itemText(combo.currentIndex()) == 'Buy':
                self.buy_coins.append(coin)
            elif combo.itemText(combo.currentIndex()) == 'Sell':
                self.sell_coins.append(coin)
            elif combo.itemText(combo.currentIndex()) == 'Buy & sell':
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
        self.activate_thread.trigger.connect(self.update_active)
        self.activate_thread.start()
        self.show_active()

    def show_combo_activated(self, coin):
        gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(138, 226, 52);padding-left:25px;")

    def select_all(self, state, cointype):
        for coin in gui_coins:
            if coinslib.coin_activation[coin]['type'] == cointype:
                gui_coins[coin]['checkbox'].setChecked(state)

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
        for coin in gui_coins:
            include_coin = ['True']
            for apitype in filter_list:
                if gui_coins[coin]['checkbox'].text().find(apitype) != -1:
                    include_coin.append('True')
                else:
                    include_coin.append('False')
            if 'False' not in include_coin:
                gui_coins[coin]['checkbox'].setChecked(True)
            else:
                gui_coins[coin]['checkbox'].setChecked(False)

    ## SHOW ORDERS
    def show_orders(self):
        orders = rpclib.my_orders(self.creds[0], self.creds[1]).json()
        self.orders_table.setSortingEnabled(False)
        self.clear_table(self.orders_table)
        if 'maker_orders' in orders['result']:
            maker_orders = orders['result']['maker_orders']
            row = 0
            for item in maker_orders:
                print(guilib.colorize(maker_orders[item],'blue'))
                role = "Maker"
                base = maker_orders[item]['base']
                base_vol = maker_orders[item]['available_amount']
                rel = maker_orders[item]['rel']
                rel_vol = float(maker_orders[item]['price'])*float(maker_orders[item]['available_amount'])
                sell_price = maker_orders[item]['price']
                buy_price = '-'
                timestamp = int(maker_orders[item]['created_at']/1000)
                created_at = datetime.datetime.fromtimestamp(timestamp)
                market_price = '-'
                margin = '-'
                maker_row = [created_at, role, base, base_vol, rel, rel_vol, buy_price, sell_price, market_price, margin, item]
                col = 0
                for cell_data in maker_row:
                    cell = QTableWidgetItem(str(cell_data))
                    self.orders_table.setItem(row,col,cell)
                    cell.setTextAlignment(Qt.AlignHCenter|Qt.AlignCenter)
                    col += 1
                row += 1
        self.orders_table.setSortingEnabled(True)
        # todo the bit below - need to see an active taker order in action!
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
                sell_price = '-'
                market_price = ''
                margin = ''
                taker_row = [created_at, role, rel, rel_amount, base, base_amount, buy_price, sell_price, market_price, margin, item]
                col = 0
                for cell_data in taker_row:
                    cell = QTableWidgetItem(str(cell_data))
                    self.orders_table.setItem(row,col,cell)
                    cell.setTextAlignment(Qt.AlignHCenter|Qt.AlignCenter)
                    col += 1
                row += 1

    def cancel_order_uuid(self):
        selected_row = self.orders_table.currentRow()
        print(selected_row)
        if self.orders_table.item(selected_row,10) is not None:
            if self.orders_table.item(selected_row,0).text() != '':
                order_uuid = self.orders_table.item(selected_row,10).text()
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
        self.show_orders()

    def cancel_all_orders(self):
        if self.orders_table.item(0,0).text() != '':
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
        self.show_orders()
   
    ## SHOW TRADES
    def show_trades(self):
        swaps_info = rpclib.my_recent_swaps(self.creds[0], self.creds[1], limit=9999, from_uuid='').json()
        row = 0
        self.trades_table.setSortingEnabled(False)
        self.clear_table(self.trades_table)
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
            col = 0
            for cell_data in trade_row:
                cell = QTableWidgetItem(str(cell_data))
                self.trades_table.setItem(row,col,cell)
                cell.setTextAlignment(Qt.AlignHCenter|Qt.AlignCenter)
                col += 1            
            row += 1
            self.trades_table.setSortingEnabled(True)

    ## SHOW ORDERBOOK

    def show_orderbook(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            index = self.orderbook_buy_combo.currentIndex()
            if index != -1:
                base = self.orderbook_buy_combo.itemText(index)
            else:
                base = ''
            index = self.orderbook_sell_combo.currentIndex()
            if index != -1:
                rel = self.orderbook_sell_combo.itemText(index)
            else:
                rel = ''
            active_coins_selection = self.active_coins[:]
            base = self.update_combo(self.orderbook_buy_combo,active_coins_selection,base)
            active_coins_selection.remove(base)
            rel = self.update_combo(self.orderbook_sell_combo,active_coins_selection,rel)
            self.orderbook_table.setHorizontalHeaderLabels(['Buy coin', 'Sell coin', base+' Volume', rel+' price per '+base, 'Market price'])

            pair_book = rpclib.orderbook(self.creds[0], self.creds[1], base, rel).json()
            self.orderbook_table.setSortingEnabled(False)
            self.clear_table(self.orderbook_table)
            print(pair_book)
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
                    col = 0
                    for cell_data in asks_row:
                        cell = QTableWidgetItem(str(cell_data))
                        self.orderbook_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)    
                        col += 1
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
                balance_info = rpclib.my_balance(self.creds[0], self.creds[1], rel).json()
                if 'address' in balance_info:
                    balance_text = balance_info['balance']
                    locked_text = balance_info['locked_by_swaps']
                    available_balance = float(balance_info['balance'])-float(balance_info['locked_by_swaps'])
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

    ## BUY ORDER PAGE - PENDING
    def show_create_buy(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            index = self.create_buy_buy_combo.currentIndex()
            if index != -1:
                base = self.create_buy_buy_combo.itemText(index)
            else:
                base = ''
            index = self.create_buy_sell_combo.currentIndex()
            if index != -1:
                rel = self.create_buy_sell_combo.itemText(index)
            else:
                rel = ''
            active_coins_selection = self.active_coins[:]
            base = self.update_combo(self.create_buy_buy_combo,active_coins_selection,base)
            active_coins_selection.remove(base)
            rel = self.update_combo(self.create_buy_sell_combo,active_coins_selection,rel)
            # Update labels
            self.create_buy_amount_lbl.setText("Buy Amount ("+base+")")
            self.create_buy_price_lbl.setText("Buy Price ("+rel+")")
            self.create_buy_depth_baserel_lbl.setText(rel+"/"+base)
            balance_info = rpclib.my_balance(self.creds[0], self.creds[1], rel).json()
            if 'address' in balance_info:
                balance = round(float(balance_info['balance']),8)
                locked = round(float(balance_info['locked_by_swaps']),8)
                available_balance = balance - locked
                self.create_buy_balance_lbl.setText("Available funds: "+str(available_balance)+" "+rel)
                self.create_buy_locked_lbl.setText("Locked by swaps: "+str(locked)+" "+rel)

            self.buy_depth_table.setHorizontalHeaderLabels(['Price '+base, 'Volume '+rel, 'Value '+base])

            pair_book = rpclib.orderbook(self.creds[0], self.creds[1], rel, base).json()
            self.buy_depth_table.setSortingEnabled(False)
            self.clear_table(self.buy_depth_table)
            if 'error' in pair_book:
                pass
            elif 'asks' in pair_book:
                row = 0
                for item in pair_book['asks']:
                    price = round(float(item['price']), 8)
                    volume = round(float(item['maxvolume']), 8)
                    val = float(item['price'])*float(item['maxvolume'])
                    value = round(val, 8)
                    depth_row = [price, volume, value]
                    col = 0
                    for cell_data in depth_row:
                        cell = QTableWidgetItem(str(cell_data))
                        self.buy_depth_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)
                        col += 1
                    row += 1
            self.buy_depth_table.setSortingEnabled(True)
        pass

    def populate_buy_order_vals(self):
        val = self.get_cell_val(self.buy_depth_table, 0)
        if val == '':
            selected_price = 0
        else:
            selected_price = float(val)
        self.create_buy_price.setValue(selected_price)

    def get_bal_pct(self, bal_lbl, pct):
        bal = float(bal_lbl.text().split()[2])
        return  bal*pct/100

    def create_setprice_buy(self):
        index = self.create_buy_sell_combo.currentIndex()
        rel = self.create_buy_sell_combo.itemText(index)
        index = self.create_buy_buy_combo.currentIndex()
        base = self.create_buy_buy_combo.itemText(index)
        basevolume = self.create_buy_amount.value()
        relprice = self.create_buy_price.value()
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
        max_vol = float(self.create_buy_balance_lbl.text().split()[2])
        val = self.create_buy_amount.value()
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
                msg += "Buy "+str(basevolume)+" "+base+"\nfor\n"+" "+str(trade_val)+" "+rel
            else:
                msg = resp
            QMessageBox.information(self, 'Created Setprice Buy Order', str(msg), QMessageBox.Ok, QMessageBox.Ok)


    ## CREATE ORDER - todo: cleanup references to 'buy' - this is setprice/sell!
    def show_create_sell(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            index = self.create_buy_combo.currentIndex()
            base = self.create_buy_combo.itemText(index)
            index = self.create_sell_combo.currentIndex()
            rel = self.create_sell_combo.itemText(index)
            pair = self.update_create_order_combos(base, rel)
            base = pair[0]
            rel = pair[1]
            self.create_sell_depth_baserel_lbl.setText(base+"/"+rel)
            self.sell_depth_table.setHorizontalHeaderLabels(['Price '+base, 'Volume '+rel, 'Value '+base])
            pair_book = rpclib.orderbook(self.creds[0], self.creds[1], rel, base).json()
            self.sell_depth_table.setSortingEnabled(False)
            self.clear_table(self.sell_depth_table)
            if 'error' in pair_book:
                pass
            elif 'asks' in pair_book:
                row = 0
                for item in pair_book['asks']:
                    price = round(float(item['price']), 8)
                    volume = round(float(item['maxvolume']), 8)
                    val = float(item['price'])*float(item['maxvolume'])
                    value = round(val, 8)
                    depth_row = [price, volume, value]
                    col = 0
                    for cell_data in depth_row:
                        cell = QTableWidgetItem(str(cell_data))
                        self.sell_depth_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)
                        col += 1
                    row += 1
            self.sell_depth_table.setSortingEnabled(True)

    def update_create_order_combos(self, base, rel):
        existing_sell_coins = []
        for i in range(self.create_sell_combo.count()):
            existing_sell_coin = self.create_sell_combo.itemText(i)
            existing_sell_coins.append(existing_sell_coin)
        existing_buy_coins = []
        for i in range(self.create_buy_combo.count()):
            existing_buy_coin = self.create_buy_combo.itemText(i)
            existing_buy_coins.append(existing_buy_coin)
        # add activated if not in combobox if not already there.
        for coin in self.active_coins:
            if coin not in existing_sell_coins:
                self.create_sell_combo.addItem(coin)
            if rel == '':
                self.create_sell_combo.setCurrentIndex(0)
                rel = self.create_sell_combo.itemText(self.create_sell_combo.currentIndex())
            if coin not in existing_buy_coins:
                if coin != rel:
                    self.create_buy_combo.addItem(coin)
                    if base == '':
                        self.create_buy_combo.setCurrentIndex(0)
                        base = self.create_buy_combo.itemText(self.create_buy_combo.currentIndex())
        # eliminate selection duplication
        for i in range(self.create_buy_combo.count()):
            if self.create_buy_combo.itemText(i) == rel:
                self.create_buy_combo.removeItem(i)
                if base == rel:
                    self.create_buy_combo.setCurrentIndex(0)
                    base = self.create_buy_combo.itemText(self.create_buy_combo.currentIndex())
                break
        # Update labels
        self.create_amount_lbl.setText("Sell Amount ("+rel+")")
        self.create_price_lbl.setText("Sell Price ("+base+")")
        balance_info = rpclib.my_balance(self.creds[0], self.creds[1], rel).json()
        if 'address' in balance_info:
            balance = round(float(balance_info['balance']),8)
            locked = round(float(balance_info['locked_by_swaps']),8)
            available_balance = balance - locked
            self.create_order_balance_lbl.setText("Available funds: "+str(available_balance)+" "+rel)
        return base, rel

    def populate_sell_order_vals(self):
        val = self.get_cell_val(self.sell_depth_table, 0)
        if val == '':
            selected_price = 0
        else:
            selected_price = float(val)
        self.create_sell_price.setValue(selected_price)

    def sell_25pct(self):
        self.sell_pct(25)

    def sell_50pct(self):
        self.sell_pct(50)

    def sell_75pct(self):
        self.sell_pct(75)

    def sell_100pct(self):
        # TODO: setup maxvol
        self.sell_pct(100)

    def sell_pct(self, pct):
        if self.create_sell_price.value() == 0:
            price = self.sell_depth_table.item(0,0).text()
        else:
            price = self.create_sell_price.value()
        bal_txt = self.create_order_balance_lbl.text()
        max_vol = float(bal_txt.split()[2])
        val = max_vol*pct/100
        self.create_sell_amount.setValue(val)
    
    def create_setprice(self):
        index = self.create_sell_combo.currentIndex()
        base = self.create_sell_combo.itemText(index)
        index = self.create_buy_combo.currentIndex()
        rel = self.create_buy_combo.itemText(index)
        basevolume = self.create_sell_amount.value()
        relprice = self.create_sell_price.value()
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
                        msg = "Cancel all previous "+base+"/"+rel+" orders?"
                        break
                if msg != '':
                    confirm = QMessageBox.question(self, msg_title, msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                    if confirm == QMessageBox.No:
                        cancel_previous = False
                    elif confirm == QMessageBox.Cancel:
                        cancel_trade = True
        bal_txt = self.create_order_balance_lbl.text()
        max_vol = float(bal_txt.split()[2])
        val = self.create_sell_amount.value()
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
            else:
                msg = resp
            QMessageBox.information(self, 'Created Setprice Order', str(msg), QMessageBox.Ok, QMessageBox.Ok)

    ## PRICES
    def show_prices(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            prices_data = priceslib.get_prices_data(self.creds[0], self.creds[1],self.active_coins)
            print(prices_data)
            self.prices_table.setSortingEnabled(False)
            self.clear_table(self.prices_table)
            row = 0
            for item in prices_data:
                if item in self.active_coins:
                    coin = item
                    try:
                        api_btc_price = str(round(prices_data[item]["average_btc"],8))+" ₿"
                    except:
                        api_btc_price = "-"
                    try:
                        mm2_btc_price = str(round(prices_data[item]["mm2_btc_price"],8))+" ₿"
                    except:
                        mm2_btc_price = "-"
                    try:
                        delta_btc_price = str(round(prices_data[item]["mm2_btc_price"]-prices_data[item]["average_btc"],8))+" ₿"
                    except:
                        delta_btc_price = "-"
                    try:
                        api_kmd_price = round(prices_data[item]["kmd_price"],6)
                    except:
                        api_kmd_price = "-"
                    try:
                        mm2_kmd_price = round(prices_data[item]["mm2_kmd_price"],6)
                    except:
                        mm2_kmd_price = "-"
                    try:
                        delta_kmd_price = round(prices_data[item]["mm2_kmd_price"]-prices_data[item]["kmd_price"],6)
                    except:
                        delta_kmd_price = "-"
                    try:
                        api_usd_price = "$"+str(round(prices_data[item]["average_usd"],4))+" USD"
                    except:
                        api_usd_price = "-"
                    try:
                        mm2_usd_price = "$"+str(round(prices_data[item]["mm2_usd_price"],4))+" USD"
                    except:
                        mm2_usd_price = "-"
                    try:
                        delta_usd_price = "$"+str(round(prices_data[item]["mm2_usd_price"]-prices_data[item]["average_usd"],4))+" USD"
                    except:
                        delta_usd_price = "-"
                    sources = prices_data[item]["sources"]
                    price_row = [coin, api_btc_price, mm2_btc_price, delta_btc_price,
                                 api_kmd_price, mm2_kmd_price, delta_kmd_price,
                                 api_usd_price, mm2_usd_price, delta_usd_price,
                                 sources]
                    col = 0
                    for cell_data in price_row:
                        cell = QTableWidgetItem(str(cell_data))
                        self.prices_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)    
                        col += 1
                    row += 1
        self.prices_table.setSortingEnabled(True)

    ## WALLET
    def show_wallet(self):
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
            self.wallet_coin_img.setText("<html><head/><body><p><img src=\":/lrg/img/400/"+coin.lower()+".png\"/></p></body></html>")
            balance_info = rpclib.my_balance(self.creds[0], self.creds[1], coin).json()
            if 'address' in balance_info:
                addr_text = balance_info['address']
                balance_text = round(float(balance_info['balance']),8)
                locked_text = round(float(balance_info['locked_by_swaps']),8)
                # todo add address explorer links to coinslib
                if coinslib.coin_explorers[coin]['addr_explorer'] != '':
                    self.wallet_address.setText("<a href='"+coinslib.coin_explorers[coin]['addr_explorer']+"/"+addr_text+"'>"+addr_text+"</href>")
                else:
                    self.wallet_address.setText(addr_text)
                self.wallet_balance_lbl.setText(str(coin+" BALANCE"))
                self.wallet_balance.setText(str(balance_text))
                self.wallet_locked_by_swaps.setText("("+str(locked_text)+" locked by swaps)")
                if coinslib.coin_api_codes[coin]['paprika_id'] != '':
                    price = priceslib.get_paprika_price(coinslib.coin_api_codes[coin]['paprika_id']).json()
                    usd_price = float(price['price_usd'])
                    btc_price = float(price['price_btc'])
                elif coinslib.coin_api_codes[coin]['coingecko_id'] != '':
                    price = priceslib.gecko_fiat_prices(coinslib.coin_api_codes[coin]['coingecko_id'], 'usd,btc').json()
                    usd_price = float(price['usd'])
                    btc_price = float(price['btc'])
                else:
                    usd_price = 0
                    btc_price = 0
                print(btc_price)
                if btc_price != 0:
                    self.wallet_usd_value.setText("$"+str(round(balance_text*usd_price,2))+" USD")
                    self.wallet_btc_value.setText(str(round(balance_text*btc_price,6))+" ₿")
                else:
                    self.wallet_usd_value.setText("")
                    self.wallet_btc_value.setText("")

                self.wallet_qr_code.setPixmap(qrcode.make(addr_text, image_factory=QR_image).pixmap())

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
                print(resp)
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
                    balance_info = rpclib.my_balance(self.creds[0], self.creds[1], cointag).json()
                    if 'address' in balance_info:
                        balance_text = balance_info['balance']
                        self.wallet_balance.setText(balance_text)
            else:
                msg = str(resp)
            QMessageBox.information(self, 'Wallet transaction', msg, QMessageBox.Ok, QMessageBox.Ok)
        pass

    ## CONFIG
    def show_config(self):
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
            if os.path.isfile(config_path+self.username+"_MM2.json"):
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
                        self.show_login()

                    else:
                        QMessageBox.information(self, 'Password incorrect!', 'Password incorrect!', QMessageBox.Ok, QMessageBox.Ok)
                        # todo password change option.
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

    def update_logs(self):
        print("update_logs")
        with open(script_path+"/bin/mm2_output.log", 'r') as f:
            log_text = f.read()
            lines = f.readlines()
            self.scrollbar = self.console_logs.verticalScrollBar()
            self.console_logs.setPlainText(log_text)
            self.scrollbar.setValue(10000)
        pass

    ## BINANCE API
    def show_binance_acct(self):
        tickers = self.update_binance_balance_table()
        print(tickers)
        self.update_combo(self.binance_asset_comboBox,tickers,tickers[0])
        ticker_pairs = []
        for ticker in tickers:
            if ticker != "BTC":
                ticker_pairs.append(ticker+"BTC")
        self.update_combo(self.binance_ticker_pair_comboBox,ticker_pairs,ticker_pairs[0])
        self.update_binance_orderbook()
        self.update_orders_table()
        self.update_history_graph()
        addr_text = self.get_binance_deposit_addr()
        self.binance_qr_code.setPixmap(qrcode.make(addr_text, image_factory=QR_image).pixmap())
        self.binance_addr_lbl.setText(addr_text)
        self.binance_addr_coin_lbl.setText("Binance "+tickers[0]+" Address")

    def update_binance_addr(self):
        index = self.binance_asset_comboBox.currentIndex()
        asset = self.binance_asset_comboBox.itemText(index)
        addr_text = self.get_binance_deposit_addr()
        self.update_history_graph()
        if addr_text == 'Address not found - create it at Binance.com':
            self.binance_qr_code.setPixmap(qrcode.make('https://www.binance.com/', image_factory=QR_image).pixmap())
        else:
            self.binance_qr_code.setPixmap(qrcode.make(addr_text, image_factory=QR_image).pixmap())
        self.binance_addr_lbl.setText(addr_text)
        self.binance_addr_coin_lbl.setText("Binance "+asset+" Address")


    def update_history_graph(self):
        index = self.binance_asset_comboBox.currentIndex()
        asset = self.binance_asset_comboBox.itemText(index)
        coin_id = coinslib.coin_api_codes[asset]['paprika_id']
        if coin_id != '':
            history = priceslib.get_paprika_history(coin_id)
            x = []
            x_str = []
            y = []
            mth_ticks = []
            self.xy = {}
            last_month = ''
            for item in history:
                y.append(item['price'])
                dt = dateutil.parser.parse(item['timestamp'])
                x.append(int(datetime.datetime.timestamp(dt)))
                x_str.append(item['timestamp'])
                month = time.ctime(int(datetime.datetime.timestamp(dt))).split(" ")[1]
                if month != last_month:
                    if last_month != '':
                        mth_ticks.append((int(datetime.datetime.timestamp(dt)),month))
                    last_month = month
                self.xy.update({str(int(datetime.datetime.timestamp(dt))):item['price']})

            self.binance_history_graph.setYRange(0,max(y)*1.1, padding=0)
            self.binance_history_graph.setXRange(min(x),max(x), padding=0)
            self.binance_history_graph.clear()


            #self.price_curve = pg.PlotCurveItem(
            price_curve = self.binance_history_graph.plot(
                    x,
                    y, 
                    pen={'color':(78,155,46)},
                    fillLevel=0, brush=(50,50,200,100),
                )
            self.binance_history_graph.addItem(price_curve)
            self.binance_history_graph.setLabel('left', '$USD')
            self.binance_history_graph.setLabel('bottom', '', units=None)
            self.binance_history_graph.showGrid(x=True, y=True, alpha=0.2)
            price_ticks = self.binance_history_graph.getAxis('left')
            price_ticks.enableAutoSIPrefix(enable=False)
            date_ticks = self.binance_history_graph.getAxis('bottom')    
            date_ticks.setTicks([mth_ticks])
            date_ticks.enableAutoSIPrefix(enable=False)
            self.vLine = crosshair_lines(pen={'color':(78,155,46)}, angle=90, movable=False)
            self.vLine.sigPositionChangeFinished.connect(self.getDatePrice)
            self.binance_history_graph.addItem(self.vLine, ignoreBounds=True)
            price = priceslib.get_paprika_price(coin_id).json()
            usd_price = float(price['price_usd'])
            txt='<div style="text-align: center"><span style="color: #FFF;font-size:8pt;">Current USD Price: $'+str(usd_price)+'</span></div>'
            text = pg.TextItem(html=txt, anchor=(0,0), border='w', fill=(0, 0, 255, 100))
            self.binance_history_graph.addItem(text)
            text.setPos(min(x)+(max(x)-min(x))*0.02,max(y))


    def getDatePrice(self):
        min_delta = 999999999999
        xpos = self.vLine.getXPos()
        print(xpos)
        for item in self.xy:
            delta = abs(int(item) - xpos)
            if delta < min_delta:
                min_delta = delta
                ref_time = item
                ref_price = self.xy[str(item)]
        print("time: "+str(datetime.datetime.fromtimestamp(int(ref_time))))
        print("price: "+str(ref_price))

    def getPrice(self, x):
        min_delta = 999999999999
        for item in self.xy:
            delta = abs(int(item) - x)
            if delta < min_delta:
                min_delta = delta
                ref_time = item
                ref_price = self.xy[str(item)]
        print("time: "+str(datetime.datetime.fromtimestamp(int(ref_time))))
        print("price: "+str(ref_price))
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
                    col = 0
                    for cell_data in balance_row:
                        cell = QTableWidgetItem(str(cell_data))
                        self.binance_balances_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)    
                        col += 1
                    row += 1
                self.binance_balances_table.setSortingEnabled(True)
            return tickers

    # TODO: dynamic column header update
    # TODO: Improve available pairs selection
    def update_binance_orderbook(self):
        index = self.binance_ticker_pair_comboBox.currentIndex()
        self.binance_price_spinbox.setValue(0)
        ticker_pair = self.binance_ticker_pair_comboBox.itemText(index)
        depth_limit = 10
        orderbook = binance_api.get_depth(self.creds[5], ticker_pair, depth_limit)
        self.clear_table(self.binance_orderbook_table)
        self.binance_orderbook_table.setSortingEnabled(False)
        self.binance_orderbook_table.setRowCount(depth_limit*2)
        row = 0
        for item in orderbook['bids']:
            price = float(item[0])
            volume = float(item[1])
            balance_row = [ticker_pair, price, volume, 'bid']
            col = 0
            for cell_data in balance_row:
                cell = QTableWidgetItem(str(cell_data))
                self.binance_orderbook_table.setItem(row,col,cell)
                cell.setTextAlignment(Qt.AlignCenter)
                self.binance_orderbook_table.item(row,col).setBackground(QColor(210, 255, 191))
                col += 1
            row += 1
        for item in orderbook['asks']:
            price = float(item[0])
            volume = float(item[1])
            balance_row = [ticker_pair, price, volume, 'ask']
            col = 0
            for cell_data in balance_row:
                cell = QTableWidgetItem(str(cell_data))
                self.binance_orderbook_table.setItem(row,col,cell)
                cell.setTextAlignment(Qt.AlignCenter)
                self.binance_orderbook_table.item(row,col).setBackground(QColor(255, 181, 181))
                col += 1
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

    def get_binance_deposit_addr(self):
        index = self.binance_asset_comboBox.currentIndex()
        asset = self.binance_asset_comboBox.itemText(index)
        resp = binance_api.get_deposit_addr(self.creds[5], self.creds[6], asset)
        if 'address' in resp:
            return resp['address']
        else:
            return 'Address not found - create it at Binance.com'

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
        confirm_msg += str(amount)+' '+asset+' to '+addr+'\n\n'
        confirm_msg += "Check https://www.binance.com/en/fee/schedule for withdrawl fee details\n\n"
        confirm = QMessageBox.question(self, "Confirm withdraw?", confirm_msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
        if confirm == QMessageBox.Yes:
            proceed = True
        else:
            proceed = False
        if proceed:
            resp = binance_api.withdraw(self.creds[5], self.creds[6], asset, addr, amount)
            print(resp.keys())
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
            col = 0
            for cell_data in balance_row:
                cell = QTableWidgetItem(str(cell_data))
                self.binance_orders_table.setItem(row,col,cell)
                cell.setTextAlignment(Qt.AlignCenter)
                col += 1
            row += 1
        self.binance_orders_table.setSortingEnabled(True)

    def binance_cancel_selected_order(self):
        selected_row = self.binance_orders_table.currentRow()
        if self.binance_orders_table.item(selected_row,0) is not None:
            if self.binance_orders_table.item(selected_row,0).text() != '':
                order_id = self.binance_orders_table.item(selected_row,0).text()
                ticker_pair = self.binance_orders_table.item(selected_row,2).text()
                resp = binance_api.delete_order(self.creds[5], self.creds[6], ticker_pair, order_id)
                print(resp)
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
    def show_bot_trades(self):
        if len(self.active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            self.populate_bot_lists()

    def populate_bot_lists(self):
        self.bot_buy_list.clear()
        self.bot_sell_list.clear()
        print(self.buy_coins)
        print(self.sell_coins)
        for buy_coin in self.buy_coins:
            if buy_coin not in self.active_coins:
                buy_coin = buy_coin+ " (inactive)"
            elif buy_coin not in coinslib.binance_coins:
                buy_coin = buy_coin+ " (not on Binance, mm2 only)"
            self.bot_buy_list.addItem(buy_coin)
        for sell_coin in self.sell_coins:
            if sell_coin not in self.active_coins:
                sell_coin = sell_coin+ " (inactive)"
            elif sell_coin not in coinslib.binance_coins:
                sell_coin = sell_coin+ " (not on Binance, mm2 only)"
            self.bot_sell_list.addItem(sell_coin)

    def start_bot_trading(self):
        print(self.bot_trading)
        premium = self.margin_input.value()/100
        self.bot_trade_thread = bot_trading_thread(self.creds, self.sell_coins, self.buy_coins, self.active_coins, premium)
        if self.bot_trading:
            self.bot_trading = False
            self.bot_trade_thread.stop()
        else:
            self.bot_trading = True
            self.bot_trade_thread.trigger.connect(self.update_bot_log)
            self.bot_trade_thread.start()

    def update_bot_log(self, log_msg, log_result):
        self.bot_log_list.addItem(log_msg)
        self.bot_log_list.addItem(">>> "+str(log_result))

    ## TABS
    def prepare_tab(self):
        self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        QCoreApplication.processEvents()
        print(self.active_coins)
        if self.authenticated:
            print("authenticated")
            self.stacked_login.setCurrentIndex(1)
            index = self.currentIndex()
            if self.creds[0] == '':
                QMessageBox.information(self, 'Settings for user "'+self.username+'" not found!', "Settings not found. Please fill in the config form, save your settings and restart Antara Makerbot.", QMessageBox.Ok, QMessageBox.Ok)
                self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))              
            elif index == 0:
                # activate
                print('show_active')
                self.show_active()
            elif index == 1:
                # orders
                print('show_orders')
                self.show_orders()
            elif index == 2:
                # trades
                print('show_trades')
                self.show_trades()
            elif index == 3:
                # order book
                print('show_orderbook')
                self.show_orderbook()
            elif index == 4:
                # create order
                print('show_create_sell')
                self.show_create_sell()
            elif index == 5:
                # create order
                print('show_create_buy')
                self.show_create_buy()
            elif index == 6:
                # wallet
                print('show_prices')
                self.show_prices()
            elif index == 7:
                # wallet
                print('show_wallet')
                self.show_wallet()
            elif index == 8:
                # config
                print('show_config')
                self.show_config()
            elif index == 9:
                # logs
                print('update_logs')
                self.update_logs()
            elif index == 10:
                # logs
                print('binance_acct')
                self.show_binance_acct()
            elif index == 11:
                # logs
                print('bot_trades')
                self.show_bot_trades()
        else:
            print('show_active - login')
            self.stacked_login.setCurrentIndex(0)
            index = self.currentIndex()
            if index != 0:
                QMessageBox.information(self, 'Unauthorised access!', 'You must be logged in to access this tab', QMessageBox.Ok, QMessageBox.Ok)
            self.show_login()

if __name__ == '__main__':
    
    app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
    window = Ui() # Create an instance of our class
    app.exec_() # Start the application
    rpclib.stop_mm2(window.creds[0], window.creds[1])