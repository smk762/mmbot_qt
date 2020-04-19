from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class mm2_balances_table(QTableWidget):
    def __init__(self, active_coins, balance_data, prices_data):
        QTableWidget.__init__(self)
        self.active_coins = active_coins
        self.balance_data = balance_data
        self.prices_data = prices_data

    def update(self, active_coins, balance_data):
        self.clearContents()
        self.setSortingEnabled(False)
        self.setRowCount(len(self.active_coins))
        r = request.get("http://127.0.0.1:8000/table/mm2_balances")
        if r.status_code == 200:
            if 'table_data' in r.json():
                table_data = r.json()['table_data']
                row = 0
                for row_data in table_data:
                    self.add_row(row, row_data)
                    row += 1
        self.setSortingEnabled(True)

    def add_row(self, row, row_data):
        col = 0
        for cell_data in row_data:
            cell = QTableWidgetItem(str(cell_data))
            cell.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
            self.setItem(row,col,cell)
            col += 1

class mm2_wallet(coin, add_graph=False)
    self.wallet_recipient.setText('')
    self.wallet_amount.setValue(0)
    self.wallet_recipient.setFocus()
    if self.wallet_combo.currentIndex() != -1:
        selected = self.wallet_combo.itemText(self.wallet_combo.currentIndex())
    else:
        selected = self.wallet_combo.itemText(0)
    self.update_combo(self.wallet_combo,self.active_coins,selected)
    self.update_mm2_wallet_labels()
    self.update_mm2_balance_table()
    if selected == '':
        selected = self.wallet_combo.itemText(self.wallet_combo.currentIndex())
    '''
    tv_url = coinslib.coin_graph[selected]['url']
    tv_symbol = coinslib.coin_graph[selected]['symbol']
    tv_title = coinslib.coin_graph[selected]['title']

    if tv_url == '':
        tv_url = 'https://www.tradingview.com/symbols/NASDAQ-TSLA/'
        tv_symbol = 'NASDAQ:TSLA'
        tv_title = 'TESLA CHART'
    

    html = '<!DOCTYPE html>'
    html += '<html>'
    html += '<head>'
    html += '<title></title>'
    html += '</head>'
    html += '<body style="background:#333; margin:auto">'

    html += '<!-- TradingView Widget BEGIN --> \
            <div class="tradingview-widget-container"> \
              <div id="tradingview_41435"></div> \
              <div class="tradingview-widget-copyright"><a href="'+tv_url+'" rel="noopener" target="_blank"><span class="blue-text">'+tv_symbol+'</span></a> by TradingView</div> \
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script> \
              <script type="text/javascript"> \
              new TradingView.widget( \
              { \
              "width": 1400, \
              "height": 260, \
              "symbol": "'+tv_symbol+'", \
              "interval": "240", \
              "timezone": "Etc/UTC", \
              "theme": "Dark", \
              "style": "3", \
              "locale": "en", \
              "toolbar_bg": "#f1f3f6", \
              "enable_publishing": false, \
              "allow_symbol_change": true, \
              "container_id": "tradingview_41435" \
            } \
              ); \
              </script> \
            </div> \
            <!-- TradingView Widget END -->' 

    html += '</body>'
    html += '</html>'

    web = Web()
    #web.load("https://www.tradingview.com/chart/?symbol=BINANCE%3AKMDBTC")
    web.load_html(html) 
    
    clearLayout(self.webframe_layout)
    self.webframe_layout.addWidget(web)
'''