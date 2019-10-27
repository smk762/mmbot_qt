import os
import sys
import os
import sys
import json
import time
import requests
import subprocess
from os.path import expanduser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot

cwd = os.getcwd()
script_path = sys.path[0]
mm2_path = script_path+"/bin"
home = expanduser("~")

def colorize(string, color):
        colors = {
                'black':'\033[30m',
                'red':'\033[31m',
                'green':'\033[32m',
                'orange':'\033[33m',
                'blue':'\033[34m',
                'purple':'\033[35m',
                'cyan':'\033[36m',
                'lightgrey':'\033[37m',
                'darkgrey':'\033[90m',
                'lightred':'\033[91m',
                'lightgreen':'\033[92m',
                'yellow':'\033[93m',
                'lightblue':'\033[94m',
                'pink':'\033[95m',
                'lightcyan':'\033[96m',
        }
        if color not in colors:
                return str(string)
        else:
                return colors[color] + str(string) + '\033[0m'


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1132, 867)
        self.btn_startMM2 = QtWidgets.QCommandLinkButton(Dialog)
        self.btn_startMM2.setGeometry(QtCore.QRect(390, 390, 303, 48))
        self.btn_startMM2.setObjectName("btn_startMM2")
        self.btn_startMM2.clicked.connect(self.start_mm2)
        self.status_MM2 = QtWidgets.QTextEdit(Dialog)
        self.status_MM2.setGeometry(QtCore.QRect(847, 20, 271, 51))
        self.status_MM2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.status_MM2.setAutoFillBackground(True)
        self.status_MM2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.status_MM2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.status_MM2.setUndoRedoEnabled(False)
        self.status_MM2.setLineWrapColumnOrWidth(0)
        self.status_MM2.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.status_MM2.setObjectName("status_MM2")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "KomodoPlatform\'s Antara Makerbot"))
        self.btn_startMM2.setText(_translate("Dialog", "Start MarketMaker2"))
        self.status_MM2.setToolTip(_translate("Dialog", "Shows if MM2 is running"))
        self.status_MM2.setPlaceholderText(_translate("Dialog", "MM2 status:"))

    @pyqtSlot()
    def start_mm2(self, logfile='mm2_output.log'):
        print('Starting MM2...')
        print(mm2_path+'/mm2')
        if os.path.isfile(mm2_path+'/mm2'):
            mm2_output = open(logfile,'w+')
            subprocess.Popen([mm2_path+"/mm2"], stdout=mm2_output, stderr=mm2_output, universal_newlines=True)
            msg = "Marketmaker 2 starting. Use 'tail -f "+logfile+"' for mm2 console messages. "
            time.sleep(1)
        else:
            print(colorize("\nmm2 binary not found!", 'red'))
            print(colorize("See https://developers.komodoplatform.com/basic-docs/atomicdex/atomicdex-setup/get-started-atomicdex.html for install instructions.", 'orange'))
            print(colorize("Exiting...\n", 'blue'))
            sys.exit()        