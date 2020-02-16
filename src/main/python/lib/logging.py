from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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