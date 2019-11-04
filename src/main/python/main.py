from fbs_runtime.application_context.PyQt5 import ApplicationContext
import os
import sys
from os.path import expanduser
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from lib import guilib, rpclib, coinslib
import qrcode

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

class QR_image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        self.border = border
        print(border)
        self.width = width
        print(width)
        self.box_size = box_size
        print(box_size)
        size = (width + border * 2) * box_size
        print(size)
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
        uic.loadUi('ui/gui_template.ui', self) # Load the .ui file
        self.show() # Show the GUI
        global creds
        global coins
        creds = guilib.get_creds()
        if creds[0] != '':
            guilib.stop_mm2(creds[0], creds[1])
            guilib.start_mm2()
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
        else:
            self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))
        creds = guilib.get_creds()
        coins = {
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

    def update_logs(self):
        print("update_logs")
        with open(script_path+"/bin/mm2_output.log", 'r') as f:
            log_text = f.read()
            lines = f.readlines()
            self.scrollbar = self.console_logs.verticalScrollBar()
            self.console_logs.setPlainText(log_text)
            self.scrollbar.setValue(10000)
        pass
    def export_logs(self):
        pass

    def show_active(self):
        print("show_active")
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        print(active_coins)
        for coin in coins:
            status = coins[coin]['status']
            if coin in active_coins:
                status.setStyleSheet('color: green')
                status.setText('active')
            else:
                status.setStyleSheet('color: red')
                status.setText('inactive')

    def activate_coins(self):
        activate_dict = {}
        for coin in coins:
            checkbox = coins[coin]['checkbox']
            combo = coins[coin]['combo']
            if checkbox.isChecked():
                QCoreApplication.processEvents()
                activate_dict.update({coin:combo.currentText()})
                r = rpclib.electrum(creds[0], creds[1], coin)
                print(guilib.colorize("Activating "+coin+" with electrum", 'cyan'))
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        self.show_active()

    def show_balances(self):
        balance_info = {}
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        row = 0
        for coin in active_coins:
            balance_info[coin] = rpclib.my_balance(creds[0], creds[1], coin).json()
            addr = QTableWidgetItem(balance_info[coin]['address'])
            cointag = QTableWidgetItem(coin)
            balance = QTableWidgetItem(balance_info[coin]['balance'])
            locked_by_swaps = QTableWidgetItem(balance_info[coin]['locked_by_swaps'])
            self.table_balances.setItem(row,0,cointag)
            self.table_balances.setItem(row,1,addr)
            self.table_balances.setItem(row,2,balance)
            row += 1
    def show_orders(self):
        pass
    def show_trades(self):
        pass
    def show_orderbook(self):
        pass

    def show_wallet(self):
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
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
        addr_text = balance_info['address']
        balance_text = balance_info['balance']
        locked_text = balance_info['locked_by_swaps']
        self.wallet_address.setText(addr_text)
        self.wallet_balance.setText(balance_text)
        self.wallet_qr_code.setPixmap(qrcode.make(addr_text, image_factory=QR_image).pixmap())

    def show_config(self):
        pass

    def prepare_tab(self):
        QCoreApplication.processEvents()
        index = self.currentIndex()
        if index == 0:
            # activate
            self.show_active()
        elif index == 1:
            # balances
            self.show_balances()
        elif index == 2:
            # orders
            self.show_orders()
        elif index == 3:
            # trades
            self.show_trades()
        elif index == 4:
            # order book
            self.show_orderbook()
        elif index == 5:
            # wallet
            self.show_wallet()
        elif index == 6:
            # config
            self.show_config()
        elif index == 7:
            # logs
            self.update_logs()

app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = Ui() # Create an instance of our class
app.exec_() # Start the application
