from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
import logging
import logging.handlers

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%d-%b-%y %H:%M:%S')

def update_trading_log(sender, log_msg, log_result=''):
    timestamp = int(time.time())
    time_str = datetime.datetime.fromtimestamp(timestamp)
    prefix = str(time_str)+" ("+sender+"): "
    log_msg = prefix+log_msg
    log_row = QListWidgetItem(log_msg)
    log_row.setForeground(QColor('#00137F'))
    #self.trading_logs_list.addItem(log_row)
    if log_result != '':
        log_row = QListWidgetItem(">>> "+str(log_result))
        log_row.setForeground(QColor('#7F0000'))
        #self.trading_logs_list.addItem(log_row)

def update_bot_log(self, uuid, log_msg, log_result=''):
    log_row = QListWidgetItem(log_msg)
    log_row.setForeground(QColor('#00137F'))
    #self.trading_logs_list.addItem(log_row)
    if log_result != '':
        log_row = QListWidgetItem(">>> "+str(log_result))
        log_row.setForeground(QColor('#7F0000'))
        #self.trading_logs_list.addItem(log_row)

def start_logging_gui(username, config_path):
    print("Init GUI debug log file")
    # File logging
    if not os.path.exists(config_path+"debug"):
        os.makedirs(config_path+"debug")
    gui_debug_log = config_path+'debug/'+username+'_debug_gui.log'
    fh = logging.handlers.RotatingFileHandler(gui_debug_log, mode='a', maxBytes=500000, backupCount=5, encoding=None, delay=False)
    #fh = logging.FileHandler(debug_log)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    print("Storing GUI debug logs in "+gui_debug_log)