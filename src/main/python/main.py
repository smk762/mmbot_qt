from fbs_runtime.application_context.PyQt5 import ApplicationContext
import os
import sys
from os.path import expanduser
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from lib import guilib, rpclib, coinslib

cwd = os.getcwd()
script_path = sys.path[0]
home = expanduser("~")

class Ui(QTabWidget):
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('ui/gui_template.ui', self) # Load the .ui file
        self.show() # Show the GUI
        creds = guilib.get_creds()
        if creds[0] != '':
            guilib.stop_mm2(creds[0], creds[1])
            guilib.start_mm2()
        else:
            self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))
        global coins

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
        creds = guilib.get_creds()
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
        creds = guilib.get_creds()
        for coin in coins:
            checkbox = coins[coin]['checkbox']
            combo = coins[coin]['combo']
            if checkbox.isChecked():
                activate_dict.update({coin:combo.currentText()})
        guilib.activate_selected_coins(creds[0], creds[1], list(activate_dict.keys()))
        active_coins = rpclib.check_active_coins(creds[0], creds[1])
        for coin in coins:
            status = coins[coin]['status']
            if coin in active_coins:
                status.setStyleSheet('color: green')
                status.setText('active')
            else:
                status.setStyleSheet('color: red')
                status.setText('inactive')

app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = Ui() # Create an instance of our class
app.exec_() # Start the application
