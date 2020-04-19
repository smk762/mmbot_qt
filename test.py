import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, jsondata):
        super(TableModel, self).__init__()
        self._jsondata = jsondata
        self._headers = []
        self._data = []
        if len(self._jsondata) > 0:
            self._headers = list(self._jsondata[0].keys())
            for item in self._jsondata:
                self._data.append(list(item.values()))

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])
    
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.table = QtWidgets.QTableView()

        data = [
    {
      "Coin": "BTC",
      "Balance": "0.2157428900",
      "Available": "0.1216791600",
      "Locked": "0.0940637300"
    },
    {
      "Coin": "LTC",
      "Balance": "1.1000000000",
      "Available": "1.1000000000",
      "Locked": 0
    },
    {
      "Coin": "ETH",
      "Balance": "0.0008740000",
      "Available": "0.0008740000",
      "Locked": 0
    },
    {
      "Coin": "NEO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BNB",
      "Balance": "17.6413468900",
      "Available": "17.6413468900",
      "Locked": 0
    },
    {
      "Coin": "QTUM",
      "Balance": "8.6004294600",
      "Available": "8.6004294600",
      "Locked": 0
    },
    {
      "Coin": "EOS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SNT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BNT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GAS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "USDT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "HSR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "OAX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DNT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MCO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ICN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ZRX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "OMG",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WTC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "YOYO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LRC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TRX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SNGLS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "STRAT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BQX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "FUN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "KNC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CDT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XVG",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "IOTA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SNM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LINK",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CVC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TNT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "REP",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MDA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MTL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SALT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NULS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SUB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "STX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MTH",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ADX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ETC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ENG",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ZEC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "AST",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GNT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DGD",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BAT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DASH",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "POWR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BTG",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "REQ",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XMR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "EVX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VIB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ENJ",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VEN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ARK",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XRP",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MOD",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "STORJ",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "KMD",
      "Balance": "7991.8253585500",
      "Available": "1288.0653585500",
      "Locked": "6703.7600000000"
    },
    {
      "Coin": "RCN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "EDO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DATA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DLT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MANA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "PPT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "RDN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GXS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "AMB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ARN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCPT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CND",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GVT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "POE",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BTS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "FUEL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XZC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "QSP",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LSK",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCD",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TNB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ADA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LEND",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XLM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CMT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WAVES",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WABI",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GTO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ICX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "OST",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ELF",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "AION",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WINGS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BRD",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NEBL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NAV",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VIBE",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LUN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TRIG",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "APPC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CHAT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "RLC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "INS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "PIVX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "IOST",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "STEEM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NANO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "AE",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VIA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BLZ",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SYS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "RPX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NCASH",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "POA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ONT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ZIL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "STORM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XEM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WAN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WPR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "QLC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GRS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CLOAK",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LOOM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TUSD",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ZEN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SKY",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "THETA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "IOTX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "QKC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "AGI",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NXS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "SC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NPXS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "KEY",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NAS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MFT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DENT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ARDR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "HOT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VET",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DOCK",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "POLY",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VTHO",
      "Balance": "1.2947040000",
      "Available": "1.2947040000",
      "Locked": 0
    },
    {
      "Coin": "ONG",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "PHX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "HC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "GO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "PAX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "RVN",
      "Balance": "1552.0000000000",
      "Available": "1552.0000000000",
      "Locked": 0
    },
    {
      "Coin": "DCR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "USDC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MITH",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCHABC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCHSV",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "REN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BTT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "USDS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "FET",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TFUEL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CELR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "MATIC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ATOM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "PHB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ONE",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "FTM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BTCB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "USDSB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CHZ",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "COS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ALGO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ERD",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DOGE",
      "Balance": "0.1195693700",
      "Available": "0.1195693700",
      "Locked": 0
    },
    {
      "Coin": "BGBP",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DUSK",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ANKR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WIN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TUSDB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "COCOS",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "PERL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TOMO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BUSD",
      "Balance": "235.2394000000",
      "Available": "235.2394000000",
      "Locked": 0
    },
    {
      "Coin": "BAND",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BEAM",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "HBAR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XTZ",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NGN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "NKN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "EUR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "KAVA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "RUB",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ARPA",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TRY",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "CTXC",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BCH",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TROY",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "VITE",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "FTT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "OGN",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "DREP",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BULL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "BEAR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ETHBULL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "ETHBEAR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XRPBULL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "XRPBEAR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "EOSBULL",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "EOSBEAR",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "TCT",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "WRX",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    },
    {
      "Coin": "LTO",
      "Balance": 0,
      "Available": 0,
      "Locked": 0
    }
  ]
        self.model = TableModel(data)
        self.table.setModel(self.model)

        self.setCentralWidget(self.table)


app=QtWidgets.QApplication(sys.argv)
window=MainWindow()
window.show()
app.exec_()
