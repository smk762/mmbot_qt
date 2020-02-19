from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
import datetime

class prices_TableModel(QtCore.QAbstractTableModel):

    def __init__(self, jsondata):
        super(prices_TableModel, self).__init__()
        self._jsondata = jsondata
        self._headers = []
        self._data = []
        if len(self._jsondata) > 0:
            self._headers = list(self._jsondata[0].keys())
            for item in self._jsondata:
                self._data.append(list(item.values()))
        #print(self._data)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        if len(self._data) > 0:
            return len(self._data[0])
        return 0
    
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

class bn_TableModel(QtCore.QAbstractTableModel):
    def __init__(self, jsondata):
        super(bn_TableModel, self).__init__()
        self._jsondata = jsondata
        self._headers = []
        self._data = []
        if len(self._jsondata) > 0:
            self._headers = list(self._jsondata[0].keys())
            for item in self._jsondata:
                self._data.append(list(item.values()))
        #print(self._data)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)
        if role == Qt.ForegroundRole and self._data[index.row()][1] == 0:
            return QtGui.QColor('gray')
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        if len(self._data) > 0:
            return len(self._data[0])
        return 0
    
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

class mm2_TableModel(QtCore.QAbstractTableModel):
    update_sum_vals = pyqtSignal(float,float,float)
    def __init__(self, jsondata=None):
        super(mm2_TableModel, self).__init__()
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
                if val_row[0] != 'TOTAL':
                    self._data.append(val_row)
                else:
                    if val_row[2] != '-':
                        self._usd_sum += val_row[2]
                    if val_row[3] != '-':
                        self._btc_sum += val_row[3]
                    if val_row[4] != '-':
                        self._kmd_sum += val_row[4]
        print(self._data)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            if isinstance(value, float):
                # Render float to 2 dp
                return "{:.8f}".format(value)
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
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._headers[section])

    def update_sum_val_labels(self):
        self.update_sum_vals.emit(self._btc_sum, self._kmd_sum, self._usd_sum)

