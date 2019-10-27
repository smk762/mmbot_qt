import os
import sys 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from ui import ui_main


class makerbot_app(QMainWindow, ui_main.Ui_Dialog):
    def __init__(self, parent=None):
        super(makerbot_app, self).__init__(parent)
        self.setupUi(self)

@pyqtSlot()
def on_click(self):
    print(self)
    print('PyQt5 button click')

def main():
    appcontext = ApplicationContext()       # 1. Instantiate ApplicationContext
    app = QApplication(sys.argv)
    form = makerbot_app()
    form.show()
    app.exec_()
    exit_code = appcontext.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()