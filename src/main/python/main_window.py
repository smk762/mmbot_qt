from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Ui(QTabWidget):
    def __init__(self, ctx):
        super(Ui, self).__init__() 
        # Load the User interface from file
        uifile = QFile(":/ui/makerbot_gui_dark_v4c_nograph.ui")
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
            self.bot_api = self.ctx.get_resource('mmbot_api')
        except:
            self.bot_api = self.ctx.get_resource('mmbot_api.exe')
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
        self.create_login_tab()

    def create_login_tab():
        

    def create_wallet_tab():
        pass