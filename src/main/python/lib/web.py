
'''
def clearLayout(layout):
  while layout.count():
    child = layout.takeAt(0)
    child.widget().deleteLater()

class Web(QWebEngineView):

    def load(self, url):
        self.setUrl(QUrl(url))

    def load_html(self, html):
        self.setHtml(html)

    def adjustTitle(self):
        self.setWindowTitle(self.title())

    def disableJS(self):

        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, False)
'''

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