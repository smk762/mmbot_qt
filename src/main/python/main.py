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
from lib import guilib, rpclib, coinslib, wordlist, enc
import qrcode
import random
from ui import coin_icons
import datetime
import time


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

# Update coins file. TODO: more efficient way if doesnt need to be updated?
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

class activation_thread(QThread):
    def __init__(self, creds, coins_to_activate):
        QThread.__init__(self)
        self.coins =  coins_to_activate
        self.creds = creds

    def __del__(self):
        self.wait()

    def run(self):
        for coin in self.coins:
            r = rpclib.electrum(self.creds[0], self.creds[1], coin)
            print(guilib.colorize("Activating "+coin+" with electrum", 'cyan'))


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

class Ui(QTabWidget):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi(script_path+'/ui/makerbot_gui.ui', self) # Load the .ui file
        self.show() # Show the GUI
        self.setWindowTitle("Komodo Platform's Antara Makerbot")
        self.setWindowIcon(QIcon(':/sml/img/32/color/kmd.png'))
        global gui_coins
        self.authenticated = False
        gui_coins = {
            "BTC": {
                "type":"utxo",
                "checkbox": self.checkBox_btc, 
                "combo": self.btc_combo,
            },
            "ETH": {
                "type":"erc20",
                "checkbox": self.checkBox_eth, 
                "combo": self.eth_combo,
            },
            "KMD": {
                "type":"smartchain",
                "checkbox": self.checkBox_kmd, 
                "combo": self.kmd_combo,
                "icon":":/coins/kmd_400.png"
            },
            "LABS": {
                "type":"smartchain",
                "checkbox": self.checkBox_labs, 
                "combo": self.labs_combo,
                "icon":":/coins/KMD_Labs_Logo_thick_outline_2_32.png"
            },
            "BCH": {
                "type":"utxo",
                "checkbox": self.checkBox_bch, 
                "combo": self.bch_combo,
            },
            "BAT": {
                "type":"erc20",
                "checkbox": self.checkBox_bat, 
                "combo": self.bat_combo,
            },
            "DOGE": {
                "type":"utxo",
                "checkbox": self.checkBox_doge, 
                "combo": self.doge_combo,
            },
            "DGB": {
                "type":"utxo",
                "checkbox": self.checkBox_dgb, 
                "combo": self.dgb_combo,
            },
            "DASH": {
                "type":"utxo",
                "checkbox": self.checkBox_dash, 
                "combo": self.dash_combo,
            },
            "LTC": {
                "type":"utxo",
                "checkbox": self.checkBox_ltc, 
                "combo": self.ltc_combo,
            },
            "ZEC": {
                "type":"utxo",
                "checkbox": self.checkBox_zec, 
                "combo": self.zec_combo,
            },
            "QTUM": {
                "type":"utxo",
                "checkbox": self.checkBox_qtum, 
                "combo": self.qtum_combo,
            },
            "AXE": {
                "type":"utxo",
                "checkbox": self.checkBox_axe, 
                "combo": self.axe_combo,
            },
            "VRSC": {
                "type":"smartchain",
                "checkbox": self.checkBox_vrsc, 
                "combo": self.vrsc_combo,
            },
            "RFOX": {
                "type":"smartchain",
                "checkbox": self.checkBox_rfox, 
                "combo": self.rfox_combo,
            },
            "ZILLA": {
                "type":"smartchain",
                "checkbox": self.checkBox_zilla, 
                "combo": self.zilla_combo,
            },
            "HUSH": {
                "type":"smartchain",
                "checkbox": self.checkBox_hush, 
                "combo": self.hush_combo,
            },
            "OOT": {
                "type":"smartchain",
                "checkbox": self.checkBox_oot, 
                "combo": self.oot_combo,
            },
            "USDC": {
                "type":"erc20",
                "checkbox": self.checkBox_usdc, 
                "combo": self.usdc_combo,
            },
            "AWC": {
                "type":"erc20",
                "checkbox": self.checkBox_awc, 
                "combo": self.awc_combo,
            },
            "TUSD": {
                "type":"erc20",
                "checkbox": self.checkBox_tusd, 
                "combo": self.tusd_combo,
            },
            "PAX": {
                "type":"erc20",
                "checkbox": self.checkBox_pax, 
                "combo": self.pax_combo,
            },
            "RICK": {
                "type":"smartchain",
                "checkbox": self.checkBox_rick, 
                "combo": self.rick_combo,
            },
            "MORTY": {
                "type":"smartchain",
                "checkbox": self.checkBox_morty, 
                "combo": self.morty_combo,
            },
            "DAI": {
                "type":"erc20",
                "checkbox": self.checkBox_dai, 
                "combo": self.dai_combo,
            },
            "RVN": {
                "type":"utxo",
                "checkbox": self.checkBox_rvn, 
                "combo": self.rvn_combo,
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
        timestamp = timestamp = datetime.datetime.timestamp(now)
        filename = self.saveFileDialog()
        if filename != '':
            with open(filename, 'w') as f:
                f.write(table_csv)

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
        if self.password == '' or self.password == '' and not authenticated:
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
            print(self.creds)
            if self.authenticated:            
                if self.username in settings.value('users'):
                    self.username_input.setText('')
                    self.password_input.setText('')
                    self.authenticated = True
                    self.stacked_login.setCurrentIndex(1)
                    if self.creds[0] != '':
                        version = ''
                        stopped = False
                        while version == '':
                            if not stopped:
                                try:
                                    print("stopping mm2 (if running)")
                                    guilib.stop_mm2(self.creds[0], self.creds[1])
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

    # ACTIVATE
    def show_active(self):
        print("show_active")
        active_coins = rpclib.check_active_coins(self.creds[0], self.creds[1])
        search_txt = self.search_activate.text().lower()
        display_coins_erc20 = []
        display_coins_utxo = []
        display_coins_smartchain = []
        if 'gui_coins' in globals():
            for coin in gui_coins:
                gui_coins[coin]['checkbox'].hide()
                gui_coins[coin]['combo'].hide()
                if coin in active_coins:
                    gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(138, 226, 52)")
                else:
                    gui_coins[coin]['combo'].setStyleSheet("background-color: rgb(114, 159, 207)")
                if coin.lower().find(search_txt) > -1 or gui_coins[coin]['checkbox'].text().lower().find(search_txt) > -1 or len(search_txt) == 0:
                    if gui_coins[coin]['type'] == 'utxo':
                        display_coins_utxo.append(coin)
                    elif gui_coins[coin]['type'] == 'erc20':
                        display_coins_erc20.append(coin)
                    elif gui_coins[coin]['type'] == 'smartchain':
                        display_coins_smartchain.append(coin)
            row = 0
            for coin in display_coins_smartchain:
                gui_coins[coin]['checkbox'].show()
                gui_coins[coin]['combo'].show()
                self.smartchains_layout.addWidget(gui_coins[coin]['checkbox'], row, 0, 1, 1)
                self.smartchains_layout.addWidget(gui_coins[coin]['combo'], row, 1, 1, 1)
                icon = QIcon()
                icon.addPixmap(QPixmap(":/sml/img/32/color/"+coin.lower()+".png"), QIcon.Normal, QIcon.Off)
                gui_coins[coin]['checkbox'].setIcon(icon)
                row += 1
            row = 0
            for coin in display_coins_erc20:
                gui_coins[coin]['checkbox'].show()
                gui_coins[coin]['combo'].show()
                self.erc20_layout.addWidget(gui_coins[coin]['checkbox'], row, 0, 1, 1)
                self.erc20_layout.addWidget(gui_coins[coin]['combo'], row, 1, 1, 1)
                icon = QIcon()
                icon.addPixmap(QPixmap(":/sml/img/32/color/"+coin.lower()+".png"), QIcon.Normal, QIcon.Off)
                gui_coins[coin]['checkbox'].setIcon(icon)
                row += 1
            row = 0
            for coin in display_coins_utxo:
                gui_coins[coin]['checkbox'].show()
                gui_coins[coin]['combo'].show()
                self.utxo_layout.addWidget(gui_coins[coin]['checkbox'], row, 0, 1, 1)
                self.utxo_layout.addWidget(gui_coins[coin]['combo'], row, 1, 1, 1)
                icon = QIcon()
                icon.addPixmap(QPixmap(":/sml/img/32/color/"+coin.lower()+".png"), QIcon.Normal, QIcon.Off)
                gui_coins[coin]['checkbox'].setIcon(icon)
                row += 1

    def activate_coins(self):
        coins_to_activate = []
        for coin in gui_coins:
            checkbox = gui_coins[coin]['checkbox']
            combo = gui_coins[coin]['combo']
            if checkbox.isChecked():
                coins_to_activate.append(coin)
        self.activate_thread = activation_thread(self.creds, coins_to_activate)
        self.activate_thread.start()
        self.show_active()

    ## SHOW ORDERS

    def show_orders(self):
        orders = rpclib.my_orders(self.creds[0], self.creds[1]).json()
        row = 0
        row_count = self.orders_table.rowCount()
        self.orders_table.setSortingEnabled(False)
        while row_count > row:
            available = QTableWidgetItem('')
            base = QTableWidgetItem('')
            rel = QTableWidgetItem('')
            price = QTableWidgetItem('')
            created_at = QTableWidgetItem('')
            market_price = QTableWidgetItem('')
            margin = QTableWidgetItem('')
            uuid = QTableWidgetItem('')
            orders_row = [created_at, base, available, rel, price, market_price, margin, uuid]
            col = 0
            for cell in orders_row:
                self.orders_table.setItem(row,col,cell)
                col += 1
            row += 1
        if 'maker_orders' in orders['result']:
            maker_orders = orders['result']['maker_orders']
            row = 0
            for item in maker_orders:
                available = QTableWidgetItem(maker_orders[item]['available_amount'])
                base = QTableWidgetItem(maker_orders[item]['base'])
                rel = QTableWidgetItem(maker_orders[item]['rel'])
                price = QTableWidgetItem(maker_orders[item]['price'])
                timestamp = int(maker_orders[item]['created_at']/1000)
                created_at = QTableWidgetItem(str(datetime.datetime.fromtimestamp(timestamp)))
                market_price = QTableWidgetItem('')
                margin = QTableWidgetItem('')
                uuid = QTableWidgetItem(item)
                maker_row = [created_at, base, available, rel, price, market_price, margin, uuid]
                col = 0
                for cell in maker_row:
                    self.orders_table.setItem(row,col,cell)
                    cell.setTextAlignment(Qt.AlignHCenter|Qt.AlignCenter)
                    col += 1
                row += 1
        self.orders_table.setSortingEnabled(True)
        # todo the bit below
        if 'taker_orders' in orders['result']:
            taker_orders = orders['result']['taker_orders']
            for item in taker_orders:
                print(guilib.colorize(taker_orders[item],'cyan'))
                timestamp = int(maker_orders[item]['request']['created_at'])/1000
                created_at = QTableWidgetItem(str(datetime.datetime.fromtimestamp(timestamp)))
                base = QTableWidgetItem(maker_orders[item]['request']['base'])
                rel = QTableWidgetItem(maker_orders[item]['request']['rel'])
                base_amount = QTableWidgetItem(maker_orders[item]['request']['base_amount'])
                rel_amount = QTableWidgetItem(maker_orders[item]['request']['rel_amount'])
                price = QTableWidgetItem(str(float(rel_amount)/float(base_amount)))
                uuid = QTableWidgetItem(item)
                market_price = QTableWidgetItem('')
                margin = QTableWidgetItem('')
                taker_row = [created_at, base, available, rel, price, market_price, margin, uuid]
                col = 0
                for cell in taker_row:
                    self.orders_table.setItem(row,col,cell)
                    cell.setTextAlignment(Qt.AlignHCenter|Qt.AlignCenter)
                    col += 1
                row += 1

    def cancel_order_uuid(self):
        selected_row = self.orders_table.currentRow()
        print(selected_row)
        if self.orders_table.item(selected_row,7) is not None:
            if self.orders_table.item(selected_row,7).text() != '':
                order_uuid = self.orders_table.item(selected_row,7).text()
                resp = rpclib.cancel_uuid(self.creds[0], self.creds[1], order_uuid).json()
                msg = ''
                if 'result' in resp:
                    if resp['result'] == 'success':
                        msg = "Order "+order_uuid+" cancelled"
                    else:
                        msg = resp
                else:
                    msg = resp
                QMessageBox.information(self, 'Order Cancelled', msg, QMessageBox.Ok, QMessageBox.Ok)
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
        for swap in swaps_info['result']['swaps']:
            for event in swap['events']:
                event_type = event['event']['type']
                if event_type in rpclib.error_events:
                    event_type = 'Failed'
                    break
            status = QTableWidgetItem(event_type)
            uuid = QTableWidgetItem(swap['uuid'])
            my_amount = QTableWidgetItem(swap['my_info']['my_amount'])
            my_coin = QTableWidgetItem(swap['my_info']['my_coin'])
            other_amount = QTableWidgetItem(swap['my_info']['other_amount'])
            other_coin = QTableWidgetItem(swap['my_info']['other_coin'])
            start_time = str(datetime.datetime.fromtimestamp(round(swap['my_info']['started_at']/1000)*1000))
            started_at = QTableWidgetItem(start_time)
            sell_price = QTableWidgetItem(str(float(swap['my_info']['my_amount'])/float(swap['my_info']['other_amount'])))
            trade_row = [started_at, status, other_coin, other_amount, my_coin, my_amount, sell_price, uuid]
            col = 0
            for cell in trade_row:
                self.trades_table.setItem(row,col,cell)
                cell.setTextAlignment(Qt.AlignHCenter|Qt.AlignCenter)
                col += 1            
            row += 1

    ## SHOW ORDERBOOK

    def show_orderbook(self):
        active_coins = rpclib.check_active_coins(self.creds[0], self.creds[1])
        if len(active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            index = self.buy_combo.currentIndex()
            base = self.buy_combo.itemText(index)
            index = self.sell_combo.currentIndex()
            rel = self.sell_combo.itemText(index)
            pair = self.update_orderbook_combos(base, rel, active_coins)
            base = pair[0]
            rel = pair[1]
            pair_book = rpclib.orderbook(self.creds[0], self.creds[1], base, rel).json()
            row = 0
            self.orderbook_table.setSortingEnabled(False)
            row_count = self.orderbook_table.rowCount()
            while row_count > row:
                base = QTableWidgetItem('')
                rel = QTableWidgetItem('')
                price = QTableWidgetItem('')
                volume = QTableWidgetItem('')
                orderbook_row = [base, rel, volume, price]
                col = 0
                for cell in orderbook_row:
                    self.orderbook_table.setItem(row,col,cell)
                    col += 1
                row += 1
            if 'error' in pair_book:
                pass
            elif 'asks' in pair_book:
                row = 0
                for item in pair_book['asks']:
                    base = QTableWidgetItem(pair_book['base'])
                    rel = QTableWidgetItem(pair_book['rel'])
                    price = QTableWidgetItem(str(round(float(item['price']), 8)))
                    volume = QTableWidgetItem(str(round(float(item['maxvolume']), 8)))
                    asks_row = [base, rel, volume, price]
                    col = 0
                    for cell in asks_row:
                        self.orderbook_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)    
                        col += 1
                    row += 1
        self.orderbook_table.setSortingEnabled(True)

    def update_orderbook_combos(self, base, rel, active_coins):
        # check current coins in combobox
        if base == rel:
            base = ''
        existing_buy_coins = []
        for i in range(self.buy_combo.count()):
            existing_buy_coin = self.buy_combo.itemText(i)
            existing_buy_coins.append(existing_buy_coin)
        existing_sell_coins = []
        for i in range(self.sell_combo.count()):
            existing_sell_coin = self.sell_combo.itemText(i)
            existing_sell_coins.append(existing_sell_coin)
        # add activated if not in combobox if not already there.
        for coin in active_coins:
            if coin not in existing_sell_coins:
                self.sell_combo.addItem(coin)
            if coin not in existing_buy_coins:
                if coin != rel:
                    self.buy_combo.addItem(coin)
        # eliminate selection duplication
        for i in range(self.buy_combo.count()):
            if self.buy_combo.itemText(i) == rel:
                self.buy_combo.removeItem(i)
        # set values if empty
        if base == '':
            self.buy_combo.setCurrentIndex(0)
            base = self.buy_combo.itemText(self.buy_combo.currentIndex())
        if rel == '':
            self.sell_combo.setCurrentIndex(1)
            rel = self.sell_combo.itemText(self.sell_combo.currentIndex())
        self.orderbook_table.setHorizontalHeaderLabels(['Sell coin', 'Buy coin', base+' Volume', rel+' price', 'Market price'])
        return base, rel

    def orderbook_buy(self):
        row = 0
        index = self.buy_combo.currentIndex()
        rel = self.buy_combo.itemText(index)
        index = self.sell_combo.currentIndex()
        base = self.sell_combo.itemText(index)
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
                vol, ok = QInputDialog.getDouble(self, 'Enter Volume', 'Enter Volume '+base+' to buy at '+selected_price+' (max. '+str(max_vol)+'): ', QLineEdit.Password)
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
                        msg += str(vol)+" "+base+"\nfor\n"+" "+str(trade_val)+" "+rel
                    else:
                        msg = resp
                    QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)
            else:
                msg = "No order selected!"
                QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)
        else:
            msg = "No order selected!"
            QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)
   
    ## CREATE ORDER - todo: cleanup references to 'buy' - this is setprice/sell!

    def show_create_orders(self):
        active_coins = rpclib.check_active_coins(self.creds[0], self.creds[1])
        if len(active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            index = self.create_buy_combo.currentIndex()
            base = self.create_buy_combo.itemText(index)
            index = self.create_sell_combo.currentIndex()
            rel = self.create_sell_combo.itemText(index)
            pair = self.update_create_order_combos(base, rel, active_coins)
            base = pair[0]
            rel = pair[1]
            self.create_buy_depth_baserel_lbl.setText(rel+"/"+base)
            self.depth_table.setHorizontalHeaderLabels(['Price '+base, 'Volume '+rel, 'Value '+rel])
            pair_book = rpclib.orderbook(self.creds[0], self.creds[1], rel, base).json()
            row = 0
            row_count = self.depth_table.rowCount()
            # todo - investigate wierd tables after sorting then changing pair.
            self.depth_table.setSortingEnabled(False)
            while row_count > row:
                price = QTableWidgetItem('')
                volume = QTableWidgetItem('')
                value = QTableWidgetItem('')
                depth_row = [price, volume, value]
                col = 0
                for cell in depth_row:
                    self.depth_table.setItem(row,col,cell)
                    col += 1
                row += 1
            if 'error' in pair_book:
                pass
            elif 'asks' in pair_book:
                row = 0
                for item in pair_book['asks']:
                    price = QTableWidgetItem(str(round(float(item['price']), 8)))
                    volume = QTableWidgetItem(str(round(float(item['maxvolume']), 8)))
                    val = float(item['price'])*float(item['maxvolume'])
                    value = QTableWidgetItem(str(round(val, 8)))
                    depth_row = [price, volume, value]
                    col = 0
                    for cell in depth_row:
                        self.depth_table.setItem(row,col,cell)
                        cell.setTextAlignment(Qt.AlignCenter)
                        col += 1
                    row += 1
            self.depth_table.setSortingEnabled(True)

    def update_create_order_combos(self, base, rel, active_coins):
        existing_sell_coins = []
        for i in range(self.create_sell_combo.count()):
            existing_sell_coin = self.create_sell_combo.itemText(i)
            existing_sell_coins.append(existing_sell_coin)
        existing_buy_coins = []
        for i in range(self.create_buy_combo.count()):
            existing_buy_coin = self.create_buy_combo.itemText(i)
            existing_buy_coins.append(existing_buy_coin)
        # add activated if not in combobox if not already there.
        for coin in active_coins:
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
        self.create_amount_lbl.setText("Amount ("+rel+")")
        self.create_price_lbl.setText("Price ("+base+")")
        balance_info = rpclib.my_balance(self.creds[0], self.creds[1], rel).json()
        if 'address' in balance_info:
            balance = round(float(balance_info['balance']),8)
            locked = round(float(balance_info['locked_by_swaps']),8)
            available_balance = balance - locked
            self.create_order_balance_lbl.setText("Available funds: "+str(available_balance)+" "+rel)
        return base, rel

    def populate_create_order_vals(self):
        selected_row = self.depth_table.currentRow()
        if self.depth_table.item(selected_row,0).text() == '':
            selected_price = 0
        else:
            selected_price = float(self.depth_table.item(selected_row,0).text())
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
            price = self.depth_table.item(0,0).text()
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

    ## WALLET

    def show_wallet(self):
        active_coins = rpclib.check_active_coins(self.creds[0], self.creds[1])
        if len(active_coins) < 1:
            msg = 'Please activate at least one coin. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            existing_coins = []
            for i in range(self.wallet_combo.count()):
                existing_coin = self.wallet_combo.itemText(i)
                existing_coins.append(existing_coin)
            for coin in active_coins:
                if coin not in existing_coins:
                    self.wallet_combo.addItem(coin)
            index = self.wallet_combo.currentIndex()
            coin = self.wallet_combo.itemText(index)
            self.wallet_coin_img.setText("<html><head/><body><p><img src=\":/lrg/img/400/"+coin.lower()+".png\"/></p></body></html>")
            balance_info = rpclib.my_balance(self.creds[0], self.creds[1], coin).json()
            if 'address' in balance_info:
                addr_text = balance_info['address']
                balance_text = round(float(balance_info['balance']))
                locked_text = round(float(balance_info['locked_by_swaps']),8)
                # todo add address explorer links to coinslib
                if 'addr_explorer' in coinslib.coins[coin]:
                    self.wallet_address.setText("Your address: <a href='"+coinslib.coins[coin]['addr_explorer']+addr_text+"'>"+addr_text+"</href>")
                else:
                    self.wallet_address.setText("Your address: "+addr_text)
                self.wallet_balance.setText(str(balance_text))
                self.wallet_locked_by_swaps.setText("locked by swaps: "+str(locked_text))
                self.wallet_qr_code.setPixmap(qrcode.make(addr_text, image_factory=QR_image).pixmap())

    def send_funds(self):
        index = self.wallet_combo.currentIndex()
        cointag = self.wallet_combo.itemText(index)
        recipient_addr = self.wallet_recipient.text()
        amount = self.wallet_amount.text()
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
                try:
                    msg = "Sent! <a href='"+coinslib.coins[cointag]['tx_explorer']+"/"+txid_str+"'>[Link to block explorer]</href>"
                except:
                    msg = "Sent! TXID: ["+txid_str+"]"
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
                            guilib.stop_mm2(self.creds[0], self.creds[1])
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

    ## TABS

    def prepare_tab(self):
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
                print('show_create_orders')
                self.show_create_orders()
            elif index == 5:
                # wallet
                print('show_wallet')
                self.show_wallet()
            elif index == 6:
                # config
                print('show_config')
                self.show_config()
            elif index == 7:
                # logs
                print('update_logs')
                self.update_logs()
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
    guilib.stop_mm2(window.creds[0], window.creds[1])