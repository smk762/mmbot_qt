import os
import sys
import os
import sys
import json
import time
import requests
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from os.path import expanduser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from lib import guilib, rpclib
from shutil import copyfile

cwd = os.getcwd()
script_path = sys.path[0]
mm2_path = script_path+"/bin"
conf_path = script_path+"/conf"
log_path = script_path+"/log"
home = expanduser("~")

for x in [mm2_path, conf_path, log_path]:
    if not os.path.exists(x):
        os.makedirs(x)

while True:
    tries = 0
    try:
        tries += 1
        with open(cwd+"/MM2.json") as j:
            mm2json = json.load(j)
        gui = mm2json['gui']
        netid = mm2json['netid']
        passphrase = mm2json['passphrase']
        userpass = mm2json['rpc_password']
        rpc_password = mm2json['rpc_password']
        local_ip = "http://127.0.0.1:7783"
        break
    except FileNotFoundError:
        copyfile(conf_path+"/MM2_example.json", cwd+"/MM2.json")
        print("Copying MM2.json template "+conf_path+"/MM2_example.json to "+cwd+"/MM2.json...")
        pass
    time.sleep(3)
    if tries > 3:
        print("MM2.json not found, failing and exit...")
        sys.exit()

while True:
    tries = 0
    try:
        tries += 1
        with open(cwd+"/coins") as j:
            coins_json = json.load(j)
        break
    except FileNotFoundError:
        url = 'https://raw.githubusercontent.com/jl777/coins/master/coins'
        coins_json = requests.get(url)
        data = coins_json.json()
        with open(cwd+'/coins', 'w') as f:
            json.dump(data, f)
        print("Getting coins file from "+url+"...")
        pass
    time.sleep(3)
    if tries > 3:
        print("'coins' file not found, failing and exit...")
        sys.exit()


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
        self.status_MM2 = QtWidgets.QLabel(Dialog)
        self.status_MM2.setGeometry(QtCore.QRect(847, 20, 271, 51))
        self.status_MM2.setObjectName("status_MM2")
        running = rpclib.check_mm2_status(local_ip, userpass)
        if not running:
            self.btn_startMM2 = QtWidgets.QCommandLinkButton(Dialog)
            self.btn_startMM2.setGeometry(QtCore.QRect(390, 390, 303, 48))
            self.btn_startMM2.setObjectName("btn_startMM2")
            self.btn_startMM2.clicked.connect(self.start_mm2)
            # TODO make red by default
            mm2_state = "offline"
        else:
            # TODO make green
            mm2_state = "online"
            Dialog.removeWidget(self.btn_startMM2)

        self.retranslateUi(Dialog, mm2_state)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog, mm2_state):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "KomodoPlatform\'s Antara Makerbot"))
        self.btn_startMM2.setText(_translate("Dialog", "Start MarketMaker2"))
        self.status_MM2.setToolTip(_translate("Dialog", "Shows if MM2 is running"))
        self.status_MM2.setText("MM2 status: "+mm2_state)


    @pyqtSlot()
    def start_mm2(self, logfile='mm2_output.log'):
        print('Starting MM2...')
        print(mm2_path+'/mm2')
        if os.path.isfile(mm2_path+'/mm2'):
            mm2_output = open(log_path+"/"+logfile,'w+')
            subprocess.Popen([mm2_path+"/mm2"], stdout=mm2_output, stderr=mm2_output, universal_newlines=True)
            print(colorize("Marketmaker 2 starting. Use 'tail -f "+log_path+"/"+logfile+"' for mm2 console messages. ",'green'))
            self.status_MM2.setText("MM2 status: online")
            self.btn_startMM2.deleteLater()
            self.btn_startMM2 = None
            time.sleep(1)
        else:
            print(colorize("\nmm2 binary not found!", 'red'))
            print(colorize("See https://developers.komodoplatform.com/basic-docs/atomicdex/atomicdex-setup/get-started-atomicdex.html for install instructions.", 'orange'))
            print(colorize("Exiting...\n", 'blue'))
            sys.exit()
