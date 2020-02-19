from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

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
    def __init__(self, jsondata=None):
        super(mm2_TableModel, self).__init__()
        self.jsondata = jsondata or {}
        self.headers = []
        self.data = []
        if len(self.jsondata) > 0:
            self.headers = list(self.jsondata[0].keys())
            for item in self.jsondata:
                self.data.append(list(item.values()))
        print(self.data)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self.data[index.row()][index.column()]
            return str(value)

    def rowCount(self, index):
        return len(self.data)

    def columnCount(self, index):
        if len(self.data) > 0:
            return len(self.data[0])
        return 0
    
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.headers[section])
