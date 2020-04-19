from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import json

class ScrollMessageBox(QMessageBox):
    def __init__(self, json_data, *args, **kwargs):
        QMessageBox.__init__(self, *args, **kwargs)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        scroll.setWidget(self.content)
        lay = QVBoxLayout(self.content)
        json_lines = json.dumps(json_data, indent=4)
        msg_data = QTextEdit(json_lines, self)
        msg_data.setReadOnly(True)
        lay.addWidget(msg_data)
        self.layout().addWidget(scroll, 0, 0, 1, self.layout().columnCount())
        self.setStyleSheet("QScrollArea{min-width:800 px; min-height: 800px}")

class coinComboBox(QComboBox):
    def __init__(self, options=None, selected=None, *args, **kwargs):
        QComboBox.__init__(self, *args, **kwargs)
        self._options = options or {}
        self._selected = selected

    def update(self):
        self.clear()
        self._options.sort()
        print(self._options)
        self.addItems(self._options)
        if selected in self._options:
            for i in range(self.count()):
                if self.itemText(i) == self._selected:
                    self.setCurrentIndex(i)
        elif 'KMD' in self._options:
                for i in range(self.count()):
                    if self.itemText(i) == 'KMD':
                        self.setCurrentIndex(i)
        else:
            self.setCurrentIndex(0)
        return self.itemText(self.currentIndex())

    def selected(self):
        return self.itemText(self.currentIndex())



