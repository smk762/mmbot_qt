
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