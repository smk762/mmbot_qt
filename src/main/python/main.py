from fbs_runtime.application_context.PyQt5 import ApplicationContext
import os
import sys
import json
from os.path import expanduser
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from lib import guilib, rpclib, coinslib, wordlist
import qrcode
import random
from ui import coin_icons
import datetime

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")
os.environ['MM_COINS_PATH'] = script_path+"/bin/coins"
os.environ['MM_CONF_PATH'] = script_path+"/bin/MM2.json"


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
        global creds
        global gui_coins
        creds = guilib.get_creds()
        if creds[0] != '':
            guilib.stop_mm2(creds[0], creds[1])
            guilib.start_mm2()
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))
            QMessageBox.information(self, 'MM2.json not found!', "Settings not found. Please fill in the config form, save your settings and restart Antara Makerbot.", QMessageBox.Ok, QMessageBox.Ok)

        creds = guilib.get_creds()
        gui_coins = {
            "BTC": {
                "checkbox": self.checkBox_btc, 
                "combo": self.btc_combo,
                "status": self.btc_status,
            },
            "ETH": {
                "checkbox": self.checkBox_eth, 
                "combo": self.eth_combo,
                "status": self.eth_status,
            },
            "KMD": {
                "checkbox": self.checkBox_kmd, 
                "combo": self.kmd_combo,
                "status": self.kmd_status,
            },
            "LABS": {
                "checkbox": self.checkBox_labs, 
                "combo": self.labs_combo,
                "status": self.labs_status,
            },
            "BCH": {
                "checkbox": self.checkBox_bch, 
                "combo": self.bch_combo,
                "status": self.bch_status,
            },
            "BAT": {
                "checkbox": self.checkBox_bat, 
                "combo": self.bat_combo,
                "status": self.bat_status,
            },
            "DOGE": {
                "checkbox": self.checkBox_doge, 
                "combo": self.doge_combo,
                "status": self.doge_status,
            },
            "DASH": {
                "checkbox": self.checkBox_dash, 
                "combo": self.dash_combo,
                "status": self.dash_status,
            },
            "LTC": {
                "checkbox": self.checkBox_ltc, 
                "combo": self.ltc_combo,
                "status": self.ltc_status,
            },
            "ZEC": {
                "checkbox": self.checkBox_zec, 
                "combo": self.zec_combo,
                "status": self.zec_status,
            },
            "RICK": {
                "checkbox": self.checkBox_rick, 
                "combo": self.rick_combo,
                "status": self.rick_status,
            },
            "MORTY": {
                "checkbox": self.checkBox_morty, 
                "combo": self.morty_combo,
                "status": self.morty_status,
            },
            "DAI": {
                "checkbox": self.checkBox_dai, 
                "combo": self.dai_combo,
                "status": self.dai_status,
            },
            "RVN": {
                "checkbox": self.checkBox_rvn, 
                "combo": self.rvn_combo,
                "status": self.rvn_status,
            },
        }

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
        # popup for file to save as
        # write data to file
        # json, csv option?

    ## ACTIVATE

    def show_active(self):
        print("show_active")
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        print(active_coins)
        for coin in gui_coins:
            status = gui_coins[coin]['status']
            if coin in active_coins:
                status.setStyleSheet('color: green')
                status.setText('active')
            else:
                status.setStyleSheet('color: red')
                status.setText('inactive')

    def activate_coins(self):
        activate_dict = {}
        for coin in gui_coins:
            checkbox = gui_coins[coin]['checkbox']
            combo = gui_coins[coin]['combo']
            if checkbox.isChecked():
                QCoreApplication.processEvents()
                activate_dict.update({coin:combo.currentText()})
                r = rpclib.electrum(creds[0], creds[1], coin)
                print(guilib.colorize("Activating "+coin+" with electrum", 'cyan'))
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        self.show_active()

    ## SHOW ORDERS

    def show_orders(self):
        orders = rpclib.my_orders(creds[0], creds[1]).json()
        row = 0
        print(orders)
        if 'maker_orders' in orders['result']:
            maker_orders = orders['result']['maker_orders']
            for item in maker_orders:
                available = QTableWidgetItem(maker_orders[item]['available_amount'])
                base = QTableWidgetItem(maker_orders[item]['base'])
                rel = QTableWidgetItem(maker_orders[item]['rel'])
                price = QTableWidgetItem(maker_orders[item]['price'])
                timestamp = int(maker_orders[item]['created_at'])/1000
                created_at = QTableWidgetItem(str(datetime.datetime.fromtimestamp(timestamp)))
                market_price = QTableWidgetItem('')
                margin = QTableWidgetItem('')
                uuid = QTableWidgetItem(item)
                self.orders_table.setItem(row,0,created_at)
                self.orders_table.setItem(row,1,base)
                self.orders_table.setItem(row,2,available)
                self.orders_table.setItem(row,3,rel)
                self.orders_table.setItem(row,4,price)
                self.orders_table.setItem(row,5,market_price)
                self.orders_table.setItem(row,5,margin)
                self.orders_table.setItem(row,7,uuid)
                row += 1
            row_count = self.orders_table.rowCount()
            while row_count > row:
                available = QTableWidgetItem('')
                base = QTableWidgetItem('')
                rel = QTableWidgetItem('')
                price = QTableWidgetItem('')
                created_at = QTableWidgetItem('')
                market_price = QTableWidgetItem('')
                margin = QTableWidgetItem('')
                uuid = QTableWidgetItem('')
                self.orders_table.setItem(row,0,created_at)
                self.orders_table.setItem(row,1,base)
                self.orders_table.setItem(row,2,available)
                self.orders_table.setItem(row,3,rel)
                self.orders_table.setItem(row,4,price)
                self.orders_table.setItem(row,5,market_price)
                self.orders_table.setItem(row,5,margin)
                self.orders_table.setItem(row,7,uuid)
                row += 1
        if 'taker_orders' in orders['result']:
            taker_orders = orders['result']['taker_orders']
            for item in taker_orders:
                print(taker_orders[item])

    def cancel_order_uuid(self):
        selected_row = self.orders_table.currentRow()
        order_uuid = self.orders_table.item(selected_row,7).text()
        resp = rpclib.cancel_uuid(creds[0], creds[1], order_uuid).json()
        print(resp)
        msg = ''
        if 'result' in resp:
            if resp['result'] == 'success':
                msg = "Order "+order_uuid+" cancelled"
            else:
                msg = resp
        else:
            msg = resp
        try:
           QMessageBox.information(self, 'Order Cancelled', msg, QMessageBox.Ok, QMessageBox.Ok)
        except TypeError:
           QMessageBox.information(self, 'Order Cancelled', 'no orders selected', QMessageBox.Ok, QMessageBox.Ok)
        self.show_orders()

    def cancel_all_orders(self):
        resp = rpclib.cancel_all(creds[0], creds[1]).json()
        print(resp)
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
        self.show_orders()
   
    ## SHOW TRADES

    def show_trades(self):
        swaps_info = rpclib.my_recent_swaps(creds[0], creds[1], limit=9999, from_uuid='').json()
        row = 0
        for swap in swaps_info['result']['swaps']:
            status = ''
            uuid = QTableWidgetItem(swap['uuid'])
            uuid.setTextAlignment(Qt.AlignHCenter)
            my_amount = QTableWidgetItem(swap['my_info']['my_amount'])
            my_amount.setTextAlignment(Qt.AlignHCenter)
            my_coin = QTableWidgetItem(swap['my_info']['my_coin'])
            my_coin.setTextAlignment(Qt.AlignHCenter)
            other_amount = QTableWidgetItem(swap['my_info']['other_amount'])
            other_amount.setTextAlignment(Qt.AlignHCenter)
            other_coin = QTableWidgetItem(swap['my_info']['other_coin'])
            other_coin.setTextAlignment(Qt.AlignHCenter)
            start_time = str(datetime.datetime.fromtimestamp(swap['my_info']['started_at']))
            started_at = QTableWidgetItem(start_time)
            started_at.setTextAlignment(Qt.AlignHCenter)
            sell_price = QTableWidgetItem(str(float(swap['my_info']['my_amount'])/float(swap['my_info']['other_amount'])))
            sell_price.setTextAlignment(Qt.AlignHCenter)
            self.trades_table.setItem(row,0,started_at)
            self.trades_table.setItem(row,2,other_coin)
            self.trades_table.setItem(row,3,other_amount)
            self.trades_table.setItem(row,4,my_coin)
            self.trades_table.setItem(row,5,my_amount)
            self.trades_table.setItem(row,6,sell_price)
            self.trades_table.setItem(row,7,uuid)
            for event in swap['events']:
                event_type = event['event']['type']
                if event_type in rpclib.error_events:
                    event_type = 'Failed'
                    break
            status = QTableWidgetItem(event_type)
            self.trades_table.setItem(row,1,status)
            row += 1

    ## SHOW ORDERBOOK

    def show_orderbook(self):
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        if len(active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            row = 0
            index = self.buy_combo.currentIndex()
            base = self.buy_combo.itemText(index)
            index = self.sell_combo.currentIndex()
            rel = self.sell_combo.itemText(index)
            pair = self.update_orderbook_combos(base, rel, active_coins)
            base = pair[0]
            rel = pair[1]
            pair_book = rpclib.orderbook(creds[0], creds[1], base, rel).json()
            if 'error' in pair_book:
                pass
            elif 'bids' in pair_book:
                for item in pair_book['asks']:
                    base = QTableWidgetItem(pair_book['base'])
                    base.setTextAlignment(Qt.AlignHCenter)
                    rel = QTableWidgetItem(pair_book['rel'])
                    rel.setTextAlignment(Qt.AlignHCenter)
                    price = QTableWidgetItem(str(round(float(item['price']), 8)))
                    price.setTextAlignment(Qt.AlignHCenter)
                    volume = QTableWidgetItem(str(round(float(item['maxvolume']), 8)))
                    volume.setTextAlignment(Qt.AlignHCenter)
                    self.orderbook_table.setItem(row,0,base)
                    self.orderbook_table.setItem(row,1,rel)
                    self.orderbook_table.setItem(row,2,volume)
                    self.orderbook_table.setItem(row,3,price)
                    row += 1
            row_count = self.orderbook_table.rowCount()
            while row_count > row:
                base = QTableWidgetItem('')
                rel = QTableWidgetItem('')
                price = QTableWidgetItem('')
                volume = QTableWidgetItem('')
                self.orderbook_table.setItem(row,0,base)
                self.orderbook_table.setItem(row,1,rel)
                self.orderbook_table.setItem(row,2,volume)
                self.orderbook_table.setItem(row,3,price)
                row += 1

    def update_orderbook_combos(self, base, rel, active_coins, trigger=''):
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
        if self.buy_combo.count() == self.sell_combo.count():
            self.buy_combo.removeItem(0)
        # set values if empty
        if base == '':
            self.buy_combo.setCurrentIndex(0)
            base = self.buy_combo.itemText(self.buy_combo.currentIndex())
        if rel == '':
            self.sell_combo.setCurrentIndex(0)
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
        print(selected_row)
        selected_price = self.orderbook_table.item(selected_row,3).text()
        balance_info = rpclib.my_balance(creds[0], creds[1], rel).json()
        if 'address' in balance_info:
            balance_text = balance_info['balance']
            locked_text = balance_info['locked_by_swaps']
            available_balance = float(balance_info['balance'])-float(balance_info['locked_by_swaps'])
            max_vol = available_balance/float(selected_price)*0.99
        vol, ok = QInputDialog.getDouble(self, 'Enter Volume', 'Enter Volume '+base+' to buy at '+selected_price+' (max. '+str(max_vol)+'): ')
        if ok:
            print(vol)
        resp = rpclib.buy(creds[0], creds[1], base, rel, vol, selected_price).json()
        print(resp)
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
        QMessageBox.information(self, 'Buy From Orderbook', msg, QMessageBox.Ok, QMessageBox.Ok)
   
    ## CREATE ORDER - todo: cleanup references to 'buy' - this is setprice/sell!

    def show_create_orders(self):
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        if len(active_coins) < 2:
            msg = 'Please activate at least two coins. '
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            row = 0
            index = self.create_buy_combo.currentIndex()
            base = self.create_buy_combo.itemText(index)
            index = self.create_sell_combo.currentIndex()
            rel = self.create_sell_combo.itemText(index)
            pair = self.update_create_order_combos(base, rel, active_coins)
            base = pair[0]
            rel = pair[1]            
            self.create_buy_depth_baserel_lbl.setText(base+"/"+rel)
            self.depth_table.setHorizontalHeaderLabels(['Price '+base, 'Amount '+rel, 'Value '+rel])
            pair_book = rpclib.orderbook(creds[0], creds[1], base, rel).json()
            if 'error' in pair_book:
                pass
            elif 'asks' in pair_book:
                for item in pair_book['asks']:
                    price = QTableWidgetItem(str(round(float(item['price']), 8)))
                    price.setTextAlignment(Qt.AlignHCenter)
                    volume = QTableWidgetItem(str(round(float(item['maxvolume']), 8)))
                    volume.setTextAlignment(Qt.AlignHCenter)
                    val = float(item['price'])*float(item['maxvolume'])
                    value = QTableWidgetItem(str(round(val, 8)))
                    value.setTextAlignment(Qt.AlignHCenter)
                    self.depth_table.setItem(row,0,price)
                    self.depth_table.setItem(row,1,volume)
                    self.depth_table.setItem(row,2,value)
                    row += 1
            row_count = self.depth_table.rowCount()
            while row_count > row:
                price = QTableWidgetItem('')
                volume = QTableWidgetItem('')
                value = QTableWidgetItem('')
                self.depth_table.setItem(row,0,price)
                self.depth_table.setItem(row,1,volume)
                self.depth_table.setItem(row,2,value)
                row += 1

  
    def update_create_order_combos(self, base, rel, active_coins):
        # check current coins in combobox
        if base == rel:
            base = ''
        existing_buy_coins = []
        for i in range(self.create_buy_combo.count()):
            existing_buy_coin = self.create_buy_combo.itemText(i)
            existing_buy_coins.append(existing_buy_coin)
        existing_sell_coins = []
        for i in range(self.create_sell_combo.count()):
            existing_sell_coin = self.create_sell_combo.itemText(i)
            existing_sell_coins.append(existing_sell_coin)
        # add activated if not in combobox if not already there.
        for coin in active_coins:
            if coin not in existing_sell_coins:
                self.create_sell_combo.addItem(coin)
            if coin not in existing_buy_coins:
                if coin != rel:
                    self.create_buy_combo.addItem(coin)
        # eliminate selection duplication
        if self.create_buy_combo.count() == self.create_sell_combo.count():
            self.create_buy_combo.removeItem(0)
        # set values if empty
        if base == '':
            self.create_buy_combo.setCurrentIndex(0)
            base = self.create_buy_combo.itemText(self.create_buy_combo.currentIndex())
        if rel == '':
            self.create_sell_combo.setCurrentIndex(0)
            rel = self.create_sell_combo.itemText(self.create_sell_combo.currentIndex())
        balance_info = rpclib.my_balance(creds[0], creds[1], base).json()
        if 'address' in balance_info:
            balance = round(float(balance_info['balance']),8)
            locked = round(float(balance_info['locked_by_swaps']),8)
            available_balance = balance - locked
            self.create_order_balance_lbl.setText("Available funds: "+str(available_balance)+" "+base)
        return base, rel

    def populate_create_order_vals(self):
        selected_row = self.depth_table.currentRow()
        selected_price = float(self.depth_table.item(selected_row,0).text())
        print(selected_price)
        self.create_buy_price.setValue(selected_price)

    def buy_25pct(self):
        self.buy_pct(25)

    def buy_50pct(self):
        self.buy_pct(50)

    def buy_75pct(self):
        self.buy_pct(75)

    def buy_100pct(self):
        self.buy_pct(100)

    def buy_pct(self, pct):
        if self.create_buy_price.value() == 0:
            price = self.depth_table.item(0,0).text()
        else:
            price = self.create_buy_price.value()
        bal_txt = self.create_order_balance_lbl.text()
        max_vol = float(bal_txt.split()[2])
        val = max_vol*pct/100
        self.create_buy_amount.setValue(val)
    
    def create_setprice(self):
        index = self.create_buy_combo.currentIndex()
        base = self.create_buy_combo.itemText(index)
        index = self.create_sell_combo.currentIndex()
        rel = self.create_sell_combo.itemText(index)
        basevolume = self.create_buy_amount.value()
        relprice = self.create_buy_price.value()
        resp = rpclib.setprice(creds[0], creds[1], base, rel, basevolume, relprice).json()
        print(resp)
        if 'error' in resp:
            if resp['error'].find("larger than available") > -1:
                msg = "Insufficient funds to complete order."
            else:
                msg = resp
        elif 'result' in resp:
            trade_val = round(float(relprice)*float(basevolume),8)
            msg = "Order Submitted.\n"
            msg += str(basevolume)+" "+base+"\nfor\n"+" "+str(trade_val)+" "+rel
        else:
            msg = resp
        QMessageBox.information(self, 'Created Setprice Order', msg, QMessageBox.Ok, QMessageBox.Ok)


    ## WALLET

    def show_wallet(self):
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
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
            balance_info = rpclib.my_balance(creds[0], creds[1], coin).json()
            if 'address' in balance_info:
                addr_text = balance_info['address']
                balance_text = round(float(balance_info['balance']))
                locked_text = round(float(balance_info['locked_by_swaps']),8)
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
        print(recipient_addr)
        print(amount)
        resp = rpclib.withdraw(creds[0], creds[1], cointag, recipient_addr, amount).json()
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
            resp = rpclib.send_raw_transaction(creds[0], creds[1], cointag, raw_hex).json()
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
                balance_info = rpclib.my_balance(creds[0], creds[1], coin).json()
                if 'address' in balance_info:
                    balance_text = balance_info['balance']
                    self.wallet_balance.setText(balance_text)
        else:
            print(resp)
            msg = str(resp)
        QMessageBox.information(self, 'Wallet transaction', msg, QMessageBox.Ok, QMessageBox.Ok)
        pass

    ## CONFIG

    def show_config(self):
        pass

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
        binanace_key = self.binance_key_text_input.text()
        binance_secret = self.binance_secret_text_input.text()
        margin = self.trade_premium_input.text()
        netid = self.netid_input.text()
        if passphrase == '':
            msg += 'No seed phrase input! \n'
        if rpc_password == '':
            msg += 'No RPC password input! \n'
        if rpc_ip == '':
            msg += 'No RPC IP input! \n'
        if msg == '':
            overwrite = True
            if os.path.isfile(script_path+"/bin/MM2.json"):
                confirm = QMessageBox.question(self, 'Confirm overwrite', "Existing MM2.json detected. Overwrite?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if not confirm == QMessageBox.Yes:
                    overwrite = False
            if overwrite:
                data = {}
                data.update({"gui":gui})
                data.update({"rpc_password":rpc_password})
                data.update({"netid":int(netid)})
                data.update({"passphrase":passphrase})
                data.update({"userhome":home})
                data.update({"rpc_local_only":local_only})
                data.update({"rpc_allow_ip":rpc_ip})
                print(data)
                with open(script_path+"/bin/MM2.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, 'New MM2.json created', "Settings updated. Please restart Antara Makerbot.", QMessageBox.Ok, QMessageBox.Ok)
                guilib.stop_mm2(creds[0], creds[1])
                print("MM2.json file created!")
        else:
            QMessageBox.information(self, 'Validation failed', msg, QMessageBox.Ok, QMessageBox.Ok)
            pass
    
    def generate_seed(self):
        seed_words_list = []
        while len(seed_words_list) < 24:
            word = random.choice(wordlist.wordlist)
            if word not in seed_words_list:
                seed_words_list.append(word)
        print(seed_words_list)
        seed_phrase = " ".join(seed_words_list)
        print(seed_phrase)
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
        index = self.currentIndex()
        if index == 0:
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

app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = Ui() # Create an instance of our class
app.exec_() # Start the application
guilib.stop_mm2(creds[0], creds[1])
