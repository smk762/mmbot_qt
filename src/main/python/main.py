#!/usr/bin/env python3
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
from lib import guilib, rpclib, coinslib, wordlist, enc, priceslib, binance_api, botlib
from lib.qrcode import qr_popup
from lib.widgets import ScrollMessageBox
from lib.util import *
from lib.threads import *
from lib.logs import start_logging_gui
from lib.models import *
from lib.auth import check_binance_auth, decrypt_creds, get_creds
from lib import pallete
from lib.bins import *
from ui import resources
import time
import platform
import subprocess
import decimal
import logging
import logging.handlers
from operator import itemgetter 
#from PyQt5.QtWebEngineWidgets import QWebEngineView

home = expanduser("~")

# scaling for high DPI vs SD monitors. Awaiting feedback from other users if any buttons etc are too small.
os.environ["QT_SCALE_FACTOR"] = "1"  
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Setup local settings config ini.
QSettings.setDefaultFormat(QSettings.IniFormat)
QCoreApplication.setOrganizationName("KomodoPlatform")
QCoreApplication.setApplicationName("AntaraMakerbot")
settings = QSettings()
ini_file = settings.fileName()
config_path = settings.fileName().replace("AntaraMakerbot.ini", "")

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

# console logging
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)
handler.setFormatter(formatter)

os.environ['MM_CONF_PATH'] = config_path+"MM2.json"

# Detect existing registered users
if settings.value('users') is None:
    settings.setValue("users", [])

# UI Class
class Ui(QTabWidget):
    def __init__(self, ctx):
        super(Ui, self).__init__() 
        # Load the User interface from file
        uifile = QFile(":/ui/makerbot_gui_dark_v5.ui")        
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
        try:
            self.api_bin = self.ctx.get_resource('mmbot_api')
        except:
            self.api_bin = self.ctx.get_resource('mmbot_api.exe')
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
        #self.webframe_layout = QHBoxLayout()
        #self.webframe.setLayout(self.webframe_layout)
        self.authenticated = False
        self.balances_data = {
            "mm2": {},
            "Binance": {}
        }
        self.mm2_balanceTable_data = []
        # dict for the checkbox and label elements use on the coins activation page. Might be a better way to do this.
        self.gui_coins = {
            "BTC": {
                "checkbox": self.checkBox_btc, 
                "label": self.btc_label,    
            },
            "ETH": {
                "checkbox": self.checkBox_eth, 
                "label": self.eth_label,
            },
            "KMD": {
                "checkbox": self.checkBox_kmd, 
                "label": self.kmd_label,
            },
            "LABS": {
                "checkbox": self.checkBox_labs, 
                "label": self.labs_label,
            },
            "BCH": {
                "checkbox": self.checkBox_bch, 
                "label": self.bch_label,
            },
            "BAT": {
                "checkbox": self.checkBox_bat, 
                "label": self.bat_label,
            },
            "DOGE": {
                "checkbox": self.checkBox_doge, 
                "label": self.doge_label,
            },
            "DGB": {
                "checkbox": self.checkBox_dgb, 
                "label": self.dgb_label,
            },
            "DASH": {
                "checkbox": self.checkBox_dash, 
                "label": self.dash_label,
            },
            "LTC": {
                "checkbox": self.checkBox_ltc, 
                "label": self.ltc_label,
            },
            "ZEC": {
                "checkbox": self.checkBox_zec, 
                "label": self.zec_label,
            },
            "QTUM": {
                "checkbox": self.checkBox_qtum, 
                "label": self.qtum_label,
            },
            "AXE": {
                "checkbox": self.checkBox_axe, 
                "label": self.axe_label,
            },
            "VRSC": {
                "checkbox": self.checkBox_vrsc, 
                "label": self.vrsc_label,
            },
            "RFOX": {
                "checkbox": self.checkBox_rfox, 
                "label": self.rfox_label,
            },
            "ZILLA": {
                "checkbox": self.checkBox_zilla, 
                "label": self.zilla_label,
            },
            "HUSH": {
                "checkbox": self.checkBox_hush, 
                "label": self.hush_label,
            },
            "OOT": {
                "checkbox": self.checkBox_oot, 
                "label": self.oot_label,
            },
            "USDC": {
                "checkbox": self.checkBox_usdc, 
                "label": self.usdc_label,
            },
            "AWC": {
                "checkbox": self.checkBox_awc, 
                "label": self.awc_label,
            },
            "TUSD": {
                "checkbox": self.checkBox_tusd, 
                "label": self.tusd_label,
            },
            "PAX": {
                "checkbox": self.checkBox_pax, 
                "label": self.pax_label,
            },
            "RICK": {
                "checkbox": self.checkBox_rick, 
                "label": self.rick_label,
            },
            "MORTY": {
                "checkbox": self.checkBox_morty, 
                "label": self.morty_label,
            },
            "DAI": {
                "checkbox": self.checkBox_dai, 
                "label": self.dai_label,
            },
            "RVN": {
                "checkbox": self.checkBox_rvn, 
                "label": self.rvn_label,
            },
            "BOTS":{ 
                "checkbox":self.checkBox_bots, 
                "label":self.bots_label, 
            },
            "BTCH":{ 
                "checkbox":self.checkBox_btch, 
                "label":self.btch_label, 
            },
            "CHIPS":{ 
                "checkbox":self.checkBox_chips, 
                "label":self.chips_label, 
            },
            "COQUI":{ 
                "checkbox":self.checkBox_coqui, 
                "label":self.coqui_label, 
            },
            "CRYPTO":{ 
                "checkbox":self.checkBox_crypto, 
                "label":self.crypto_label, 
            },
            "DEX":{ 
                "checkbox":self.checkBox_dex, 
                "label":self.dex_label, 
            },
            "LINK":{ 
                "checkbox":self.checkBox_link, 
                "label":self.link_label, 
            },
            "REVS":{ 
                "checkbox":self.checkBox_revs, 
                "label":self.revs_label, 
            },
            "SUPERNET":{ 
                "checkbox":self.checkBox_supernet, 
                "label":self.supernet_label, 
            },
            "THC":{ 
                "checkbox":self.checkBox_thc, 
                "label":self.thc_label, 
            },
        }
        self.logout_timeout = False
        self.show_login_tab()
        self.datacache_thread = False
        self.activate_thread = False
                
    # once cachedata thred returns data, update balances, logs and tables as periodically.
    # TODO: update this to only act on visible tab
    def update_cachedata(self, prices_dict, balances_dict):
        if self.logout_timeout:
            logger.info("No activity logout in "+str(int(self.logout_timeout - time.time()))+" sec")
            if self.logout_timeout < time.time():

                pending = 0
                if self.mm2_trades_table.rowCount() != 0:
                    for i in range(self.mm2_trades_table.rowCount()):
                        if self.mm2_trades_table.item(i,2) is not None:
                            if self.mm2_trades_table.item(i,2).text() != 'Finished' and self.mm2_trades_table.item(i,2).text() != 'Failed':
                                pending += 1
                if pending == 0:
                    logger.info("Logging out, no activity in last 5 min...")
                    self.logout()
                    QMessageBox.information(self, 'Logout', "Automatically logged out after 5 minutes of inactivity.", QMessageBox.Ok, QMessageBox.Ok)
                else:
                    logger.info("Not auto logging out, order in progress...")
                    self.update_mm2_trade_history_table()                
            else:
                logger.info("Updating cache data from API")
                self.balances_data['mm2'].update(balances_dict['mm2'])
                self.balances_data["Binance"].update(balances_dict["Binance"])
                self.update_mm2_balance_table()
                self.update_mm2_wallet_labels()
                self.update_binance_balance_table()
                self.update_prices_table()
                self.update_mm2_trade_history_table()
                self.update_strategy_history_table()
                self.update_strategies_table()
                self.view_strat_summary()
                self.update_mm2_orders_table()
                self.update_console_logs()
                # TODO: Add gui update functions as req here.

    def start_loop_threads(self):
        # start data caching loop in other thread
        self.datacache_thread = cachedata_thread()
        self.datacache_thread.update_data.connect(self.update_cachedata)
        self.datacache_thread.start()

    ## MM2 management
    def launch_bins(self):
        if self.username in settings.value('users'):
            self.username_input.setText('')
            self.password_input.setText('')
            self.stacked_login.setCurrentIndex(1)
            if self.creds[0] != '':
                kill_mm2()      
                self.launch_mm2()
                kill_api()
                self.launch_api()
                auth_api(self.creds[0], self.creds[1], self.creds[5], self.creds[6], self.username)
                purge_mm2_json(config_path)
                self.show_activation_tab()
                self.stop_all_strats()
                rpclib.cancel_all(self.creds[0], self.creds[1]).json()
                self.authenticated_binance, self.binance_api_err = check_binance_auth(self.creds[5], self.creds[6])
                self.start_loop_threads()
            else:
                self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))

    def launch_api(self):
        i = 0  
        version = ''
        while version == '':
            try:
                start_api(self.api_bin, config_path, self.username)
                version = requests.get('http://127.0.0.1:8000/api_version').json()['version']
                logger.info("Bot version: "+version)
                self.api_version_lbl.setText("Makerbot API version: "+version+" ")
            except Exception as e:
                logger.info('bot not start')
                logger.info(e)
            i += 1
            if i > 10:
                QMessageBox.information(self, 'Error', "Bot API failed to start.\nCheck "+config_path+self.username+"_bot_output.log", QMessageBox.Ok, QMessageBox.Ok)
                sys.exit()

    def launch_mm2(self):
        i = 0
        version = ''
        while version == '':
            try:
                start_mm2(self.mm2_bin, config_path, self.username)
                version = rpclib.version(self.creds[0], self.creds[1]).json()['result']
                logger.info("mm2 version: "+version)
                self.mm2_version_lbl.setText("MarketMaker version: "+version+" ")
            except Exception as e:
                logger.info('mm2 not start')
                logger.info(e)
            i += 1
            if i > 10:
                QMessageBox.information(self, 'Error', "MM2 failed to start.\nCheck logs tab, or "+config_path+self.username+"_mm2_output.log", QMessageBox.Ok, QMessageBox.Ok)
                sys.exit()

    # spinbox operations
    def binance_bid_price_update(self):
        selected_row = self.binance_depth_table_bid.currentRow()
        if selected_row != -1 and self.binance_depth_table_bid.item(selected_row,1) is not None:
            price = self.binance_depth_table_bid.item(selected_row,1).text()
            self.binance_price_spinbox.setValue(float(price))

    def binance_ask_price_update(self):
        selected_row = self.binance_depth_table_ask.currentRow()
        if selected_row != -1 and self.binance_depth_table_ask.item(selected_row,1) is not None:
            price = self.binance_depth_table_ask.item(selected_row,1).text()
            self.binance_price_spinbox.setValue(float(price))

    def update_active(self):
        self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
        for coin in self.gui_coins:
            if coin in self.active_coins:
                self.gui_coins[coin]['label'].setStyleSheet("background-color: rgb(78, 154, 6)")
                self.gui_coins[coin]['label'].setText("ACTIVE")
            else:
                self.gui_coins[coin]['label'].setStyleSheet("background-color: rgb(85, 87, 83)")
                self.gui_coins[coin]['label'].setText("INACTIVE")

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
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            logger.info("MM2 orderbook tab")
            self.update_mm2_orderbook_table()
            self.update_mm2_orders_table()
            self.update_mm2_orderbook_labels()

    def show_binance_trading_tab(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            self.update_binance_orderbook()
            if not self.authenticated_binance:
                msg = self.binance_api_err+"\n"
                self.groupBox_bn_orders.setTitle("Binance API open Orders - "+msg)
                self.groupBox_bn_orderbook.setTitle("Binance API Orderbook - "+msg)
                self.groupBox_bn_balances.setTitle("Binance Balances - "+msg)
            else:
                self.update_binance_orders_table()

    def show_mm2_wallet_tab(self):
        if len(self.active_coins) < 1:
            msg = 'Please activate at least one coin. '
            self.setCurrentWidget(self.findChild(QWidget, 'tab_activate'))
            QMessageBox.information(self, 'Error', msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            if self.wallet_combo.currentIndex() != -1:
                selected = combo_selected(self.wallet_combo)
            else:
                selected = self.wallet_combo.itemText(0)
            update_combo(self.wallet_combo,self.active_coins,selected)
            self.update_mm2_wallet_labels()
            self.update_mm2_balance_table()

    def show_strategies_tab(self):
        self.update_strategies_table()
        self.populate_strategy_lists()

    def show_prices_tab(self):
        self.update_prices_table()

    def show_history_tab(self):
        self.update_mm2_trade_history_table()
        self.update_strategy_history_table()

    def show_config_tab(self):
        # populate credentials and config settings form fields
        if self.creds[0] != '':
            self.rpcpass_text_input.setText(self.creds[1])
            self.seed_text_input.setText(self.creds[2])
            self.netid_input.setValue(self.creds[3])
            self.rpc_ip_text_input.setText(self.creds[4])
            self.binance_key_text_input.setText(self.creds[5])
            self.binance_secret_text_input.setText(self.creds[6])   
            self.timeout_input.setValue(int(self.creds[10]))
            if self.creds[4] == '127.0.0.1':
                self.checkbox_local_only.setChecked(True)
            else:
                self.checkbox_local_only.setChecked(False)

    def show_logs_tab(self):
        self.update_console_logs()

    def update_console_logs(self):
        api_debug_log = config_path+'debug/'+self.username+'_debug_api.log'
        gui_debug_log = config_path+'debug/'+self.username+'_debug_gui.log'
        if self.username != '':
            mm2_output = open(config_path+self.username+"_mm2_output.log",'r')
            with mm2_output as f:
                log_text = f.read()
                self.scrollbar = self.mm2_console_logs.verticalScrollBar()
                self.mm2_console_logs.setPlainText(log_text)
                self.scrollbar.setValue(self.scrollbar.maximum())
            api_output = open(api_debug_log,'r')
            with api_output as f:
                log_text = f.read()
                self.scrollbar = self.api_console_logs.verticalScrollBar()
                self.api_console_logs.setPlainText(log_text)
                self.scrollbar.setValue(self.scrollbar.maximum())
            gui_output = open(gui_debug_log, 'r')
            with gui_output as f:
                log_text = f.read()
                self.scrollbar = self.app_console_logs.verticalScrollBar()
                self.app_console_logs.setPlainText(log_text)
                self.scrollbar.setValue(self.scrollbar.maximum())

    ## LOGIN / ACTIVATE TAB FUNCTIONS
    def login(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        if self.username == '' or self.password == '' and not self.authenticated:
            QMessageBox.information(self, 'Login failed!', 'username and password fields can not be blank!', QMessageBox.Ok, QMessageBox.Ok)        
        else:
            self.authenticated, self.creds = decrypt_creds(self.username, self.password, config_path)
            if self.authenticated:
                logger.info("Launching MM2 and API")
                self.launch_bins()
                logger.info("start_logging_gui")
                start_logging_gui(self.username, config_path)
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

    def logout(self):
        logger.info("Logging out...")
        threads = [self.datacache_thread, self.activate_thread]
        for thread in threads:
            try:
                thread.terminate()
            except:
                pass
        kill_api()
        kill_mm2()
        self.authenticated = False
        self.authenticated_binance = False
        self.logout_timeout = False
        self.username = ''
        self.password = ''
        self.creds = ['','','','','','','','','','','']
        text_inputs = [self.seed_text_input, self.rpcpass_text_input, self.binance_key_text_input, self.binance_secret_text_input,
                       self.import_swaps_input, self.swap_recover_uuid]
        for text_input in text_inputs:
            text_input.setText('')
        tables = [self.mm2_orderbook_table, self.mm2_orders_table, self.binance_balances_table, self.binance_orders_table, 
                  self.wallet_balances_table, self.mm2_tx_table, self.strategies_table, self.strat_summary_table,
                  self.mm2_trades_table, self.strategy_trades_table]
        for table in tables:
            try:
                table.clearContents()
            except Exception as e:
                print(e)
                pass
            try:
                table.clearSpans()
            except Exception as e:
                print(e)
                pass                
        labels = [self.wallet_balance, self.wallet_locked_by_swaps, self.wallet_usd_value, self.wallet_btc_value, 
                  self.orderbook_buy_balance_lbl, self.orderbook_buy_locked_lbl, self.orderbook_sell_balance_lbl,
                  self.orderbook_sell_locked_lbl, self.binance_base_balance_lbl, self.binance_base_locked_lbl,
                  self.binance_quote_balance_lbl, self.binance_quote_locked_lbl, self.binance_addr_coin_lbl,
                  self.wallet_btc_total, self.wallet_usd_total] 
        clear_labels(labels)
        time.sleep(0.2)
        self.show_login_tab()

    def activate_coins(self):
        coins_to_activate = []
        autoactivate = []
        for coin in self.gui_coins:
            label = self.gui_coins[coin]['label']
            checkbox = self.gui_coins[coin]['checkbox']
            # update buy/sell and autoactivate lists.
            if checkbox.isChecked():
                autoactivate.append(coin)
                if coin not in self.active_coins:
                    coins_to_activate.append([coin,label])
            activate_list = {
                "autoactivate":autoactivate,
            }
        with open(config_path+self.username+"_coins.json", 'w') as j:
            j.write(json.dumps(activate_list))
        # Activate selected coins in separate thread
        self.activate_thread = activation_thread(self.creds, coins_to_activate)
        self.activate_thread.activate.connect(self.update_active)
        self.activate_thread.start()
        logger.info("Kickstart coins: "+str(rpclib.coins_needed_for_kick_start(self.creds[0], self.creds[1]).json()))
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
            self.gui_coins[coin]['label'].hide()
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
        else:
            user_autoactivate = []
        row = 0
        for coin in display_coins:
            self.gui_coins[coin]['checkbox'].show()
            self.gui_coins[coin]['label'].show()
            layout.addWidget(self.gui_coins[coin]['checkbox'], row, 0, 1, 1)
            layout.addWidget(self.gui_coins[coin]['label'], row, 1, 1, 1)
            # set checkbox to ticked if in autoactivate list
            if coin in user_autoactivate:
                self.gui_coins[coin]['checkbox'].setChecked(True)
            else:
                self.gui_coins[coin]['checkbox'].setChecked(False)
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
    def update_mm2_orderbook_labels(self):
        baserel = get_base_rel_from_combos(self.orderbook_sell_combo, self.orderbook_buy_combo, self.active_coins[:], 'mm2')
        base = baserel[0]
        rel = baserel[1]
        self.orderbook_buy_amount_lbl.setText(""+rel+" Buy Amount")
        self.orderbook_sell_amount_lbl.setText(""+base+" Sell Amount")
        self.orderbook_price_lbl.setText(""+rel+" Buy Price in "+base)
        self.orderbook_sell_bal_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+base.lower()+".png\"/></p></body></html>")
        self.orderbook_buy_bal_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+rel.lower()+".png\"/></p></body></html>")
        self.orderbook_send_order_btn.setText("Buy "+rel)
        locked_bal = self.get_locked_bal(base)
        self.orderbook_sell_locked_lbl.setText("Locked: "+str(locked_bal[0])+" "+base)
        self.orderbook_sell_balance_lbl.setText("Available: "+str(locked_bal[1])+" "+base)
        locked_bal = self.get_locked_bal(rel)
        self.orderbook_buy_locked_lbl.setText("Locked: "+str(locked_bal[0])+" "+rel)
        self.orderbook_buy_balance_lbl.setText("Available: "+str(locked_bal[1])+" "+rel)

    def get_locked_bal(self, coin):
        try:
            if coin in self.balances_data['mm2']:
                locked_text = round(float(self.balances_data['mm2'][coin]['locked']),8)
                balance = round(float(self.balances_data['mm2'][coin]['total']),8)
            else:
                locked_text = round(float(0),8)
                balance = round(float(0),8)
        except:
                locked_text = '-'
                balance = '-'
        return locked_text, balance

    # Order form button slots
    def mm2_orderbook_get_price(self):
        logger.info('get_price_from_orderbook')        
        selected_row = self.mm2_orderbook_table.currentRow()
        if selected_row != -1 and self.mm2_orderbook_table.item(selected_row,1) is not None:
            if self.mm2_orderbook_table.item(selected_row,3).text() != '':
                #buy_coin = self.mm2_orderbook_table.item(selected_row,0).text()
                sell_coin = self.mm2_orderbook_table.item(selected_row,1).text()
                #volume = self.mm2_orderbook_table.item(selected_row,2).text()
                price = self.mm2_orderbook_table.item(selected_row,3).text()
                #value = self.mm2_orderbook_table.item(selected_row,4).text()
                sell_amount = self.mm2_orderbook_table.item(selected_row,5).text()
                try:
                    available_balance = float(self.balances_data['mm2'][sell_coin]['available'])
                except:
                    available_balance = 0
                if float(sell_amount) > float(available_balance):
                    sell_amount = float(available_balance)
                # set price and buy amount inputs from row selection
                self.orderbook_price_spinbox.setValue(float(price))
                self.orderbook_sell_amount_spinbox.setValue(float(sell_amount))

    def select_mm2_orderbook_row(self, row_list):
        logger.info("MM2 Orderbook row selected: "+str(row_list))
        self.orderbook_price_spinbox.setValue(float(row_list[3]))
        max_buy_amount = float(row_list[2])
        max_sell_amount = float(row_list[5])
        available_sell_amount = float(self.balances_data['mm2'][row_list[1]]['available'])
        if available_sell_amount < max_sell_amount:
            max_sell_amount = available_sell_amount
            max_buy_amount = available_sell_amount/float(row_list[3])
        self.orderbook_buy_amount_spinbox.setValue(max_buy_amount)
        self.orderbook_sell_amount_spinbox.setValue(max_sell_amount)

    def mm2_orderbook_combo_box_switch(self):
        logger.info('combo_box_switch')
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
        rel = update_combo(self.orderbook_buy_combo,active_coins_selection,old_base)
        active_coins_selection.remove(rel)
        base = update_combo(self.orderbook_sell_combo,active_coins_selection,old_rel)
        self.orderbook_price_spinbox.setValue(0)
        self.orderbook_buy_amount_spinbox.setValue(0)
        self.orderbook_sell_amount_spinbox.setValue(0)
        self.show_mm2_orderbook_tab()

    def mm2_orderbook_combo_box_change(self):
        self.orderbook_price_spinbox.setValue(0)
        self.orderbook_buy_amount_spinbox.setValue(0)
        self.orderbook_sell_amount_spinbox.setValue(0)
        self.show_mm2_orderbook_tab()

    def mm2_orderbook_sell_pct(self, val):
        self.orderbook_sell_amount_spinbox.setValue(val)
        if self.orderbook_price_spinbox.value() != 0:
            price = self.orderbook_price_spinbox.value()
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
    def update_mm2_orderbook_amounts(self, sent_by=''):
        if sent_by == '':
            sent_by = self.sender().objectName()
        logger.info("update mm2 values amounts (source: "+sent_by+")")
        orderbook_price_val = self.orderbook_price_spinbox.value()
        orderbook_sell_amount_val = self.orderbook_sell_amount_spinbox.value()
        orderbook_buy_amount_val = self.orderbook_buy_amount_spinbox.value()
        if sent_by == 'orderbook_price_spinbox':
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
        self.update_mm2_orderbook_amounts('orderbook_price_spinbox')

    def mm2_orderbook_buy_amount_changed(self):
        self.update_mm2_orderbook_amounts('orderbook_buy_amount_spinbox')

    def mm2_orderbook_sell_amount_changed(self):
        self.update_mm2_orderbook_amounts('orderbook_sell_amount_spinbox')

    def mm2_orderbook_buy(self):
        rel = combo_selected(self.orderbook_sell_combo)
        base = combo_selected(self.orderbook_buy_combo)
        vol = self.orderbook_buy_amount_spinbox.value()
        price = self.orderbook_price_spinbox.value()
        msg = rpclib.process_mm2_buy(self.creds[0], self.creds[1], base, rel, vol, price)
        QMessageBox.information(self, 'Buy From Orderbook', str(msg), QMessageBox.Ok, QMessageBox.Ok)

    def update_binance_orderbook(self):
        tickers = list(binance_api.base_asset_info.keys())
        # trade comboboxes
        baserel = get_base_rel_from_combos(self.binance_base_combo, self.binance_rel_combo, self.active_coins[:], "Binance")
        base = baserel[0]
        rel = baserel[1]
        try:
            assetinfo = binance_api.base_asset_info[base]
            self.binance_base_amount_spinbox.setSingleStep(float(assetinfo['stepSize']))
            self.binance_base_amount_spinbox.setRange(float(assetinfo['minQty']), float(assetinfo['maxQty']))
        except Exception as e:
            logger.warning("Binance set range and step failed")
            logger.warning("assetinfo: "+str(assetinfo))

        self.binance_price_spinbox.setValue(0)
        balances_data = requests.get('http://127.0.0.1:8000/all_balances').json()
        self.binance_quote_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+rel.lower()+".png\"/></p></body></html>")
        self.binance_base_icon.setText("<html><head/><body><p><img src=\":/64/img/64/"+base.lower()+".png\"/></p></body></html>")
        if not self.authenticated_binance:
            self.binance_quote_balance_lbl.setText('Balance: Invalid API key!')
            self.binance_quote_locked_lbl.setText('Locked: Invalid API key!')
            self.binance_base_balance_lbl.setText('Balance: Invalid API key!')
            self.binance_base_locked_lbl.setText('Locked: Invalid API key!')    
        else:
            # Quote coin icon and balances
            if rel in balances_data["Binance"]:
                locked_text = "Locked: "+str(round(float(balances_data["Binance"][rel]['locked']),8))
                balance = "Balance: "+str(round(float(balances_data["Binance"][rel]['total']),8))
            else:
                locked_text = ""
                balance = "loading balance..."
            self.binance_quote_balance_lbl.setText(balance)
            self.binance_quote_locked_lbl.setText(locked_text)
            # Base coin icon and balances
            if base in balances_data["Binance"]:
                locked_text = "Locked: "+str(round(float(balances_data["Binance"][base]['locked']),8))
                balance = "Balance: "+str(round(float(balances_data["Binance"][base]['total']),8))
            else:
                locked_text = ""
                balance = "loading balance..."
            self.binance_base_balance_lbl.setText(balance)
            self.binance_base_locked_lbl.setText(locked_text)
        self.get_binance_addr(base)
        self.binance_price_lbl.setText("Price ("+rel+" per "+base+")")
        self.binance_base_amount_lbl.setText("Amount ("+base+")")
        self.binance_quote_amount_lbl.setText("Amount ("+rel+")")
        self.binance_sell_btn.setText("Sell "+base)
        self.binance_buy_btn.setText("Buy "+base)
        logger.info("Get Binance bid depth")
        QApplication.processEvents()
        async_request_api_data("table/get_binance_depth/"+base+rel+"/bids", self.binance_depth_table_bid, self.async_populate_binance_orderbook_tbl)
        logger.info("Get Binance ask depth")
        QApplication.processEvents()
        async_request_api_data("table/get_binance_depth/"+base+rel+"/asks", self.binance_depth_table_ask, self.async_populate_binance_orderbook_tbl)

    def mm2_view_order(self):
        cancel = True
        selected_row = self.mm2_orders_table.currentRow()
        if self.mm2_orders_table.item(selected_row,8) is not None:
            mm2_order_uuid = self.mm2_orders_table.item(selected_row,8).text()
            order_info = rpclib.order_status(self.creds[0], self.creds[1], mm2_order_uuid).json()
            result = ScrollMessageBox(order_info)
            result.exec_()

    def mm2_cancel_order(self):
        cancel = True
        selected_row = self.mm2_orders_table.currentRow()
        if self.mm2_orders_table.item(selected_row,7) is not None:
            mm2_order_uuid = self.mm2_orders_table.item(selected_row,7).text()
            if self.mm2_trades_table.item(selected_row,2).text() != 'Finished' and self.mm2_trades_table.item(selected_row ,2).text() != 'Failed':
                msg = "This order has swaps in progress, are you sure you want to cancel it?"
                msg += "\nSwaps in progress: \n"
                for swap in swaps_in_progress:
                    msg += swap+": "+swaps_in_progress[swap]
                confirm = QMessageBox.question(self, 'Cancel Order', msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                if confirm != QMessageBox.Yes:
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
                update_trading_log("mm2", log_msg, str(resp))
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
                    pending += 1
            if pending > 0:
                msg = str(pending)+" order(s) have swaps in progress, are you sure you want to cancel all?"
                confirm = QMessageBox.question(self, 'Confirm Cancel Orders', msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
                if confirm != QMessageBox.Yes:
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
                update_trading_log("mm2", log_msg, str(resp))
        else:
            QMessageBox.information(self, 'Order Cancelled', 'You have no orders!', QMessageBox.Ok, QMessageBox.Ok)
        self.show_mm2_orderbook_tab()
   
    ## Binance Tab
    def binance_combo_box_change(self):
        source = self.sender().objectName()
        print("binance_combobox_change source: "+str(source))
        self.binance_price_spinbox.setValue(0)
        self.binance_base_amount_spinbox.setValue(0)
        self.binance_quote_amount_spinbox.setValue(0)
        self.show_binance_trading_tab()


    def get_binance_addr(self, coin):
        if not self.authenticated_binance:
            self.binance_qr_code_link.hide()
            self.binance_addr_lbl.setText("Invalid API key")
            self.binance_addr_coin_lbl.setText("")
            self.binance_qr_code_link.hide()
        else:
            # start in other thread
            self.thread_addr_request = addr_request_thread(self.creds[5], self.creds[6], coin)
            self.thread_addr_request.resp.connect(self.update_binance_addr)
            self.thread_addr_request.start()

    def update_binance_addr(self, resp, coin):
        if 'address' in resp:
            addr_text = resp['address']
            self.binance_qr_code_link.show()
        else:
            addr_text = 'Address not found - create it at Binance.com'
            self.binance_qr_code_link.hide()
        self.binance_addr_lbl.setText(addr_text)
        self.binance_addr_coin_lbl.setText("Binance "+str(coin)+" Address")

    def show_qr_popup(self):
        coin = self.binance_addr_coin_lbl.text().split()[1]
        addr_txt = self.binance_addr_lbl.text()
        mm2_qr = qr_popup("Binance "+coin+" Address QR Code", addr_txt)
        mm2_qr.show()

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
        logger.info("update binance values amounts (source: "+sent_by+")")
        baseAsset = combo_selected(self.binance_base_combo)
        quoteAsset = combo_selected(self.binance_rel_combo)
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
        baseAsset = combo_selected(self.binance_base_combo)
        quoteAsset = combo_selected(self.binance_rel_combo) 
        symbol = baseAsset+quoteAsset
        logger.info(binance_api.binance_pair_info[symbol])
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
            update_trading_log('Binance', log_msg, str(resp))
        self.update_binance_orders_table()

    def binance_sell(self):
        qty = '{:.8f}'.format(self.binance_base_amount_spinbox.value())
        quote_qty = '{:.8f}'.format(self.binance_quote_amount_spinbox.value())
        price = '{:.8f}'.format(self.binance_price_spinbox.value())
        baseAsset = combo_selected(self.binance_base_combo)
        quoteAsset = combo_selected(self.binance_rel_combo) 
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
            update_trading_log('Binance', log_msg, str(resp))
        self.update_binance_orders_table()

    def binance_withdraw(self):
        coin = combo_selected(self.binance_base_combo) 
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
            update_trading_log("Binance", log_msg, str(resp))
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
            update_trading_log("Binance", log_msg, str(resp))
            time.sleep(0.05)
            self.update_binance_orders_table()
        QMessageBox.information(self, 'Order Cancelled', 'All orders cancelled!', QMessageBox.Ok, QMessageBox.Ok)

    ## WALLET TAB
    def update_mm2_wallet_labels(self):
        index = self.wallet_combo.currentIndex()
        if index != -1:
            coin = self.wallet_combo.itemText(index)
            old_coin = self.wallet_balance.text().split(" ")
            if len(old_coin) > 1:
                if old_coin[1] != coin:
                    self.wallet_recipient.setText('')
                    self.wallet_amount.setValue(0)
                    self.wallet_recipient.setFocus()
            wallet_labels = [self.wallet_balance, self.wallet_locked_by_swaps, self.wallet_btc_value, self.wallet_usd_value, self.wallet_kmd_value]
            clear_labels(wallet_labels)
            self.wallet_amount.setSuffix(" "+coin)
            label_data = requests.get('http://127.0.0.1:8000/labels/mm2_wallet/'+coin).json()
            self.wallet_coin_img.setText("<html><head/><body><p><img src=\":/300/img/300/"+coin.lower()+".png\"/></p></body></html>")
            if label_data['address'] != '':
                if coinslib.coin_explorers[coin]['addr_explorer'] != '':
                    self.wallet_address.setText("<a href='"+coinslib.coin_explorers[coin]['addr_explorer']+"/"+label_data['address']+"'> \
                                                 <span style='text-decoration: underline; color:#eeeeec;'>"+label_data['address']+"</span></href>")
                else:
                    self.wallet_address.setText(label_data['address'])
                self.mm2_qr_code_link.show()
            else:
                self.mm2_qr_code_link.hide()
            try:
                self.wallet_balance.setText(str(round(label_data['total'],8))+" "+coin)
                self.wallet_locked_by_swaps.setText("locked by swaps: "+str(round(label_data['locked'],8))+" "+coin)
            except Exception as e:
                self.wallet_balance.setText("")
                self.wallet_locked_by_swaps.setText("")
            try:
                self.wallet_usd_value.setText("$"+str(round(label_data['usd_val'],2))+" USD")
                self.wallet_btc_value.setText(str(round(label_data['btc_val'],8))+" BTC")
                self.wallet_kmd_value.setText(str(round(label_data['kmd_val'],4))+" KMD")
            except:
                self.wallet_usd_value.setText("")
                self.wallet_btc_value.setText("")
                self.wallet_kmd_value.setText("")
            self.update_mm2_tx_table(coin)

    def show_mm2_qr_popup(self):
        coin = combo_selected(self.wallet_combo)
        addr_txt = self.balances_data["mm2"][coin]["address"]
        mm2_qr = qr_popup("MM2 "+coin+" Address QR Code ", addr_txt)
        mm2_qr.show()

    def update_mm2_balance_sum_labels(self, sum_btc, sum_kmd, sum_usd):
        self.wallet_btc_total.setText(str(round(sum_btc,8))+" BTC")
        self.wallet_kmd_total.setText(str(round(sum_kmd,4))+" KMD")
        self.wallet_usd_total.setText("$"+str(round(sum_usd,4))+" USD")

    def select_wallet_from_table(self, coin):
        update_combo(self.wallet_combo,self.active_coins,coin)
        self.show_mm2_wallet_tab()

    def set_max_withdraw(self):
        coin = combo_selected(self.wallet_combo)
        if coin in self.balances_data["mm2"]:
            balance = self.balances_data["mm2"][coin]["available"]
            self.wallet_amount.setValue(float(balance))

    def set_self_withdraw(self):
        coin = combo_selected(self.wallet_combo)
        if coin in self.balances_data["mm2"]:
            addr_txt = self.balances_data["mm2"][coin]["address"]
            self.wallet_recipient.setText(addr_txt)

    # process withdrawl from wallet tab
    def send_funds(self):
        coin = combo_selected(self.wallet_combo)
        recipient_addr = self.wallet_recipient.text()
        amount = self.wallet_amount.value()
        confirm = QMessageBox.question(self, 'Confirm send?', "Confirm sending "+str(amount)+" "+coin+" to "+recipient_addr+"?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            msg = ''
            if float(amount) == float(self.balances_data["mm2"][coin]["available"]):
                logger.info("withdrawing max "+coin)
                resp = rpclib.withdraw_max(self.creds[0], self.creds[1], coin, recipient_addr).json()
            else:
                logger.info("withdrawing "+str(amount)+" "+coin)
                resp = rpclib.withdraw(self.creds[0], self.creds[1], coin, recipient_addr, amount).json()
            msg = self.process_tx(resp, coin, recipient_addr)
            QMessageBox.information(self, 'Wallet transaction', msg, QMessageBox.Ok, QMessageBox.Ok)
            self.update_mm2_wallet_labels()

    def process_tx(self, resp, coin, recipient_addr):
        if 'error' in resp:
            logger.info(resp['error'])
            if resp['error'].find("Invalid Address!") > -1:
                msg += "Invalid Address"
            elif resp['error'].find("Not sufficient balance!") > -1:
                msg += "Insufficient balance"
            elif resp['error'].find("less than dust amount") > -1:
                msg += "Transaction value too small!"
            else:
                msg = str(resp['error'])
        elif 'tx_hex' in resp:
            resp = rpclib.send_raw_transaction(self.creds[0], self.creds[1], coin, resp['tx_hex']).json()
            if 'tx_hash' in resp:
                txid = resp['tx_hash']
                if recipient_addr.startswith('0x'):
                    txid_str = '0x'+txid
                else:
                    txid_str = txid
                if coinslib.coin_explorers[coin]['tx_explorer'] != '':
                    txid_link = coinslib.coin_explorers[coin]['tx_explorer']+"/"+txid_str
                    msg = "Sent! <br /><a style='color:white !important' href='"+txid_link+"'>"+txid_str+"</a>"
                else:
                    msg = "Sent! <br />TXID: ["+txid_str+"]"
            self.wallet_recipient.setText("")
            self.wallet_amount.setValue(0)
        else:
            msg = str(resp)
        return msg

    ## STRATEGIES TAB
    def populate_strategy_lists(self):
        logger.info('Populating strategy lists')
        self.strat_buy_list.clear()
        self.strat_sell_list.clear()
        self.strat_cex_list.clear()
        prices_data = requests.get('http://127.0.0.1:8000/all_prices').json()
        for coin in self.active_coins:
            if len(prices_data['average'][coin]['btc_sources']) > 0:
                if 'mm2_orderbook' not in prices_data['average'][coin]['btc_sources']:
                    buy_list_item = QListWidgetItem(coin)
                    buy_list_item.setTextAlignment(Qt.AlignHCenter)
                    self.strat_buy_list.addItem(buy_list_item)
                    sell_list_item = QListWidgetItem(coin)
                    sell_list_item.setTextAlignment(Qt.AlignHCenter)
                    self.strat_sell_list.addItem(sell_list_item)
        cex_list = requests.get('http://127.0.0.1:8000/cex/list').json()['cex_list']
        list_item = QListWidgetItem("None")
        list_item.setTextAlignment(Qt.AlignHCenter)
        self.strat_cex_list.addItem(list_item)
        for item in cex_list:
            list_item = QListWidgetItem(item)
            list_item.setTextAlignment(Qt.AlignHCenter)
            if item == 'Binance':
                if self.authenticated_binance:
                    self.strat_cex_list.addItem(list_item)
            else:
                self.strat_cex_list.addItem(list_item)

    def update_strategies_table(self):
        logger.info('Updating strategies table')
        populate_table('', self.strategies_table, self.strategies_msg_lbl, "Highlight a row to view strategy trade summary","","table/bot_strategies")
        row_fg(self.strategies_table, pallete.lt_orange, 10, ['inactive'], 'exclude')
        row_fg(self.strategies_table, pallete.lt_green, 10, ['active'], 'include')
        self.strategies_table.clearSelection()

    def create_strat(self):
        buy_list = []
        for item in self.strat_buy_list.selectedItems():
            buy_list.append(item.text())
        sell_list = []
        for item in self.strat_sell_list.selectedItems():
            sell_list.append(item.text())
        cex_list = []
        for item in self.strat_cex_list.selectedItems():
            cex_list.append(item.text())
        params = 'name='+self.strat_name.text()
        params += '&strategy_type='+combo_selected(self.strat_type_combo)
        params += '&sell_list='+','.join(sell_list)
        params += '&buy_list='+','.join(buy_list)
        params += '&margin='+str(self.strat_margin_spinbox.value())
        params += '&refresh_interval='+str(self.strat_refresh_spinbox.value())
        params += '&balance_pct='+str(self.strat_bal_pct_spinbox.value())
        params += '&cex_list='+','.join(cex_list)
        incompatible_coins = coinslib.validate_selected_coins(cex_list, buy_list, sell_list)
        if len(incompatible_coins) > 0:
            resp = "The selected CEX "+str(cex_items)+" does not support "+str(incompatible_coins)+"!\n Please refine your selection..."
            QMessageBox.information(self, 'CEX Incompatible coins selected!', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        else:
            logger.info('http://127.0.0.1:8000/strategies/create?'+params)
            resp = requests.post('http://127.0.0.1:8000/strategies/create?'+params).json()
            QMessageBox.information(self, 'Create Bot Strategy', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        self.show_strategies_tab()

    def start_strat(self):
        selected_row = self.strategies_table.currentRow()
        if selected_row != -1 and self.strategies_table.item(selected_row,0) is not None:
            strategy_name = self.strategies_table.item(selected_row,0).text()
            resp = requests.post('http://127.0.0.1:8000/strategies/start/'+strategy_name).json()
            QMessageBox.information(self, 'Strategy '+strategy_name+' started', str(resp), QMessageBox.Ok, QMessageBox.Ok)
        else:
            resp = {
                "response": "error",
                "message": "No strategy row selected!"
            }
            QMessageBox.information(self, 'No strategy row selected!', str(resp), QMessageBox.Ok, QMessageBox.Ok)
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
        logger.info("Updating Strategy summary table")
        if selected_row != -1 and self.strategies_table.item(selected_row,0) is not None:
            strategy_name = self.strategies_table.item(selected_row,0).text()
            if self.summary_hide_empty_checkbox.isChecked():
                populate_table('', self.strat_summary_table, "", "", "4|0|EXCLUDE" ,"table/bot_strategy/summary/"+strategy_name)
            else:
                populate_table('', self.strat_summary_table, "", "", "",  "table/bot_strategy/summary/"+strategy_name)
            row_fg(self.strat_summary_table, pallete.lt_green, 4, ['0'], 'exclude')

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
        msg = self.validate_config()
        if msg == '':
            if os.path.isfile(config_path+self.username+"_MM2.enc"):
                confirm = QMessageBox.question(self, 'Confirm overwrite', "Confirm settings overwrite?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if confirm == QMessageBox.Yes:
                    passwd, ok = QInputDialog.getText(self, 'Enter Password', 'Enter your login password: ', QLineEdit.Password)
                    if ok:
                        if passwd == self.password:
                            self.update_creds(passwd)
                            msg_title = 'Settings updated!'
                            msg = "Settings updated. Please login again."
                            self.logout()
                        else:
                            msg_title = 'Password incorrect!'
                            msg = 'Password incorrect!'
                        QMessageBox.information(self, msg_title, msg, QMessageBox.Ok, QMessageBox.Ok)
        else:
            msg_title = 'Validation failed'
            QMessageBox.information(self, msg_title, msg, QMessageBox.Ok, QMessageBox.Ok)

    def validate_config(self):
        msg = ''
        ip_valid = guilib.validate_ip(self.rpc_ip_text_input.text())
        if not ip_valid:
            msg += 'RPC IP is invalid! \n'
        if self.seed_text_input.toPlainText() == '':
            msg += 'No seed phrase input! \n'
        if self.rpcpass_text_input.text() == '':
            msg += 'No RPC password input! \n'
        if self.rpc_ip_text_input.text() == '':
            msg += 'No RPC IP input! \n'
        return msg

    def update_creds(self, passwd):
        data = {}
        data.update({"gui":'Makerbot v0.0.1'})
        data.update({"rpc_password":self.rpcpass_text_input.text()})
        data.update({"netid":int(self.netid_input.text())})
        data.update({"passphrase":self.seed_text_input.toPlainText()})
        data.update({"userhome":home})
        data.update({"rpc_local_only":self.checkbox_local_only.isChecked()})
        data.update({"rpc_allow_ip":self.rpc_ip_text_input.text()})
        data.update({"bn_key":self.binance_key_text_input.text()})
        data.update({"bn_secret":self.binance_secret_text_input.text()})
        data.update({"login_timeout":self.timeout_input.text()})
        data.update({"dbdir":config_path+"DB"})
        # encrypt and store the config / credentials
        enc_data = enc.encrypt_mm2_json(json.dumps(data), passwd)
        with open(config_path+self.username+"_MM2.enc", 'w') as j:
            j.write(bytes.decode(enc_data))

    # Generate wallet seed
    # TODO: add other languages
    def generate_seed(self):
        seed_phrase = get_seed()
        self.seed_text_input.setText(seed_phrase)

    def import_swap_data(self):
        swap_data = json.loads(self.import_swaps_input.toPlainText())
        resp = rpclib.import_swaps(self.creds[0], self.creds[1], swap_data).json()
        QMessageBox.information(self, 'Import Swap Data', str(resp), QMessageBox.Ok, QMessageBox.Ok)

    def recover_swap(self):
        uuid = self.swap_recover_uuid.text()
        resp = rpclib.recover_stuck_swap(self.creds[0], self.creds[1], uuid).json()
        QMessageBox.information(self, 'Recover Stuck Swap', str(resp), QMessageBox.Ok, QMessageBox.Ok)

    def update_mm2_trade_history_table(self):
        if self.mm2_hide_failed_checkbox.isChecked():
            populate_table('', self.mm2_trades_table, self.mm2_trades_msg_lbl, "", "2|Failed|EXCLUDE","table/mm2_history")
        else:
            populate_table('', self.mm2_trades_table, self.mm2_trades_msg_lbl, "", "","table/mm2_history")
        if self.mm2_trades_table.rowCount() > 0:
            row_fg(self.mm2_trades_table, pallete.lt_green, 2, ['Finished'], 'include')
            row_fg(self.mm2_trades_table, pallete.lt_red, 2, ['Failed'], 'include')
            row_fg(self.mm2_trades_table, pallete.lt_orange, 2, ['Failed','Finished'], 'exclude')

    def update_strategy_history_table(self):
        populate_table('', self.strategy_trades_table, self.strategy_trades_msg_lbl, "", "", "table/strategies_history")  
        row_fg(self.strategy_trades_table, pallete.lt_green, 9, ['Complete'], 'include')
        row_fg(self.strategy_trades_table, pallete.lt_orange, 9, ['Complete'], 'exclude')

    # runs each time the tab is changed to populate the items on that tab
    def prepare_tab(self):
        if self.authenticated:
            self.logout_timeout = time.time()+int(self.creds[10])*60
            QApplication.processEvents()
            logger.info("authenticated")
            self.active_coins = guilib.get_active_coins(self.creds[0], self.creds[1])
            self.stacked_login.setCurrentIndex(1)
            index = self.currentIndex()
            if self.creds[0] == '':
                QMessageBox.information(self, 'Settings for user "'+self.username+'" not found!', "Settings not found. Please fill in the config form, save your settings and restart Antara Makerbot.", QMessageBox.Ok, QMessageBox.Ok)
                self.setCurrentWidget(self.findChild(QWidget, 'tab_config'))              
            elif index == 0:
                logger.info('show_activation_tab')
                self.show_activation_tab()
            elif index == 1:
                logger.info('show_mm2_orderbook_tab')
                self.show_mm2_orderbook_tab()
            elif index == 2:
                logger.info('show_binance_tab')
                self.show_binance_trading_tab()
            elif index == 3:
                logger.info('show_mm2_wallet_tab')
                self.show_mm2_wallet_tab()
            elif index == 4:
                logger.info('show_strategies_tab')
                self.show_strategies_tab()
            elif index == 5:
                logger.info('show_prices_tab')
                self.show_prices_tab()
            elif index == 6:
                logger.info('show_history_tab')
                self.show_history_tab()
            elif index == 7:
                logger.info('show_config_tab')
                self.show_config_tab()
            elif index == 8:
                logger.info('show_logs_tab')
                self.show_logs_tab()
        else:
            logger.info('show_activation_tab - login')
            self.stacked_login.setCurrentIndex(0)
            index = self.currentIndex()
            self.show_login_tab()
            if index != 0:
                QMessageBox.information(self, 'Unauthorised access!', 'You must be logged in to access this tab', QMessageBox.Ok, QMessageBox.Ok)

    ## Modelled Table Views ##

    def update_binance_balance_table(self):
        table = self.binance_balances_table
        if self.authenticated_binance:
            r = requests.get("http://127.0.0.1:8000/table/binance_balances")
            if r.status_code == 200:
                if 'table_data' in r.json():
                    # Sort funded and unfunded coins alphabetically
                    balance_items = []
                    non_balance_items = []
                    for item in r.json()['table_data']:
                        if float(item['Balance']) > 0:
                            balance_items.append(item)
                        else:
                            non_balance_items.append(item)
                    balance_data = sorted(balance_items, key=itemgetter('Coin'))
                    non_balance_data = sorted(non_balance_items, key=itemgetter('Coin'))
                    table_data = balance_data+non_balance_data
                    # Activate table model
                    model = bn_balance_TableModel(table_data)
                    table.setModel(model)
                    table.clicked.connect(model.row_selected)    
                    model.update_bn_wallet_signal.connect(self.update_binance_wallet)
                    logger.info("binance_balances_table changed")
                    self.binance_balances_msg_lbl.hide()
        else:
            self.binance_balances_msg_lbl.setText('Invalid API key!')
            self.binance_balances_msg_lbl.show()
    
    def update_binance_wallet(self, coin):
        bn_base_coins = list(binance_api.base_asset_info.keys())
        if coin not in bn_base_coins:
            coin = 'KMD'
        update_combo(self.binance_base_combo,bn_base_coins,coin)
        update_combo(self.binance_rel_combo, binance_api.base_asset_info[coin]['quote_assets'], coin)
        self.get_binance_addr(coin)
        self.update_binance_orderbook()

    def update_mm2_balance_table(self):
            r = requests.get("http://127.0.0.1:8000/table/mm2_balances")
            if r.status_code == 200:
                if 'table_data' in r.json():
                    table_data = sorted(r.json()['table_data'], key=itemgetter('Coin')) 
                    self.mm2_bal_tbl_model = mm2_balance_TableModel(table_data)
                    self.wallet_balances_table.setModel(self.mm2_bal_tbl_model)
                    self.wallet_balances_table.clicked.connect(self.mm2_bal_tbl_model.update_wallet)    
                    self.mm2_bal_tbl_model.update_mm2_wallet_signal.connect(self.select_wallet_from_table)       
                    self.mm2_bal_tbl_model.update_sum_vals.connect(self.update_mm2_balance_sum_labels)   
                    self.mm2_bal_tbl_model.update_sum_val_labels()
                    self.wallet_balances_table.resizeColumnsToContents()
                    logger.info("MM2 Balance Updated")

    def update_mm2_tx_table(self, coin):
        r = requests.get("http://127.0.0.1:8000/table/mm2_tx_history/"+coin)
        if r.status_code == 200:
            if 'table_data' in r.json():
                table_data = sorted(r.json()['table_data'], key=itemgetter('Time'), reverse=True) 
                self.mm2_tx_tbl_model = mm2_tx_TableModel(table_data)
                self.mm2_tx_table.setModel(self.mm2_tx_tbl_model)
                self.mm2_tx_table.resizeColumnsToContents()
                self.mm2_tx_table.doubleClicked.connect(self.mm2_tx_tbl_model.openExplorer)
                logger.info("MM2 tx table updated")

    def update_prices_table(self):
        r = requests.get("http://127.0.0.1:8000/table/prices")
        if r.status_code == 200:
            if 'table_data' in r.json():
                self.prices_model = prices_TableModel(r.json()['table_data'])
                self.prices_table.setModel(self.prices_model)
                self.prices_table.resizeColumnsToContents()
                logger.info("prices_table Updated")

    def update_mm2_orderbook_table(self):
        baserel = get_base_rel_from_combos(self.orderbook_sell_combo, self.orderbook_buy_combo, self.active_coins[:], 'mm2')
        if baserel[0] != '' and baserel[1] != '':
            r = requests.get("http://127.0.0.1:8000/table/mm2_orderbook/"+baserel[1]+"/"+baserel[0])
            if r.status_code == 200:
                logger.info("mm2_orderbook API: "+str(r.json()))
                if 'table_data' in r.json():
                    self.mm2_orderbook_table_model = mm2_orderbook_TableModel(r.json()['table_data'])
                    self.mm2_orderbook_table.setModel(self.mm2_orderbook_table_model)
                    self.mm2_orderbook_table.resizeColumnsToContents()
                    self.mm2_orderbook_table.clicked.connect(self.mm2_orderbook_table_model.select_order_row)    
                    self.mm2_orderbook_table_model.update_mm2_order_inputs_signal.connect(self.select_mm2_orderbook_row) 
                    logger.info("mm2_orderbook API: "+str(r.json()['table_data']))
            else:
                logger.error("mm2_orderbook API: "+str(r.status_code))

    def update_mm2_orders_table(self):
        r = requests.get("http://127.0.0.1:8000/table/mm2_open_orders")
        if r.status_code == 200:
            if 'table_data' in r.json():
                self.mm2_orders_model = mm2_orders_TableModel(r.json()['table_data'])
                self.mm2_orders_table.setModel(self.mm2_orders_model)
                self.mm2_orders_table.resizeColumnsToContents()
                logger.info("mm2_orders_table Updated")

    def update_binance_orders_table(self):
        r = requests.get("http://127.0.0.1:8000/table/binance_open_orders")
        if r.status_code == 200:
            if 'table_data' in r.json():
                self.binance_orders_model = binance_orders_TableModel(r.json()['table_data'])
                self.binance_orders_table.setModel(self.binance_orders_model)
                self.binance_orders_table.resizeColumnsToContents()
                logger.info("mm2_orders_table Updated")

    def async_populate_binance_orderbook_tbl(self, table, resp):
        if resp.status_code == 200:
            if 'table_data' in resp.json():
                self.model = binance_orderbook_TableModel(resp.json()['table_data'])
                table.setModel(self.model)
                table.resizeColumnsToContents()
                logger.info("async table updated: "+str(resp.json()['table_data']))
        QApplication.processEvents()

if __name__ == '__main__':
    appctxt = ApplicationContext()
    screen_resolution = appctxt.app.desktop().screenGeometry()
    width, height = screen_resolution.width(), screen_resolution.height()
    logger.info("Screen width: "+str(width))
    logger.info("Screen height: "+str(height))
    window = Ui(appctxt)
    window.resize(width, height)
    exit_code = appctxt.app.exec_()
    kill_mm2()      
    kill_api()      
    sys.exit(exit_code)