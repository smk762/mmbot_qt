from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from . import pallete, coinslib
from helpers import *

## Marketmaker Wallet Balances
class mm2_balance_TableModel(QtCore.QAbstractTableModel):
    def __init__(self, jsondata=None):
        super(mm2_balance_TableModel, self).__init__()
        self._jsondata = jsondata or {}
        self._headers = []
        self._data = []
        self._btc_sum = 0
        self._kmd_sum = 0
        self._usd_sum = 0
        if len(self._jsondata) > 0:
            self._headers = list(self._jsondata[0].keys())
            for item in self._jsondata:
                val_row = list(item.values())
                self._data.append(val_row)
                if val_row[2] != '-':
                    self._btc_sum += val_row[2]
                if val_row[3] != '-':
                    self._kmd_sum += val_row[3]
                if val_row[4] != '-':
                    self._usd_sum += val_row[4]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            if self._data[index.row()][2] != '-':
                if index.column() == 1:
                    return "{:.8f}".format(float(value))
                if index.column() == 2:
                    return "{:.8f}".format(float(value))
                if index.column() == 3:
                    return "{:.4f}".format(float(value))
                if index.column() == 4:
                    return "{:.2f}".format(float(value))
            return value
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if role == Qt.ForegroundRole and self._data[index.row()][1] == 0:
            return QtGui.QColor('gray')

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        if len(self._data) > 0:
            return len(self._data[0])
        return 0
    
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

    update_sum_vals = pyqtSignal(float,float,float)
    def update_sum_val_labels(self):
        self.update_sum_vals.emit(self._btc_sum, self._kmd_sum, self._usd_sum)

    update_mm2_wallet_signal = pyqtSignal(str)
    def update_wallet(self, selectedIndexes):
        self._coin = self._data[selectedIndexes.row()][0]
        self.update_mm2_wallet_signal.emit(self._coin)

## Marketmaker Wallet Trasactions
class mm2_tx_TableModel(QtCore.QAbstractTableModel):
    def __init__(self, jsondata):
        super(mm2_tx_TableModel, self).__init__()
        self._data, self._headers = tablize(jsondata)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)
        if role == Qt.ForegroundRole:
            if float(self._data[index.row()][5]) > 0:
                return pallete.lt_green
            if float(self._data[index.row()][5]) < 0:
                return pallete.lt_red
            if index.column() == 8:
                return pallete.lt_blue
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        if len(self._data) > 0:
            return len(self._data[0])
        return 0
    
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if self._headers[section] == 'TXID':
                    return 'TXID (double click to view on block explorer)'
                return str(self._headers[section])

    def openExplorer(self, selectedIndexes):
        if selectedIndexes.column() == 8:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(coinslib.coin_explorers[self._data[selectedIndexes.row()][1]]['tx_explorer']+"/"+self._data[selectedIndexes.row()][8]))

    def copy(self, selectedIndexes):
        logger.info(self._data[selectedIndexes.row()][selectedIndexes.column()])
        return self._data[selectedIndexes.row()][selectedIndexes.column()]
