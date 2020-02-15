import qrcode
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
# Creates a QR code from a string. Can misbehave if pixmap area size not ideal.
class QR_image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QImage(size, size, QImage.Format_RGB16)
        self._image.fill(Qt.white)

    def pixmap(self):
        return QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            Qt.black)

    def save(self, stream, kind=None):
        pass

class qr_popup():
    def __init__(self, title, qr_text):
        self.title = title
        self.qr_text = qr_text

    def show(self):
        qr_img = qrcode.make(self.qr_text, image_factory=QR_image)
        qr_lbl = QLabel()
        qr_lbl.setText(self.qr_text)
        qr_img_lbl = QLabel()
        qr_img_lbl.setPixmap(qr_img.pixmap())
        msgBox = QMessageBox(QMessageBox.NoIcon, self.title, self.qr_text)
        l = msgBox.layout()
        l.addWidget(qr_img_lbl,0, 0, 1, l.columnCount(), Qt.AlignCenter)
        l.addWidget(qr_lbl,1, 0, 1, l.columnCount(), Qt.AlignCenter)
        msgBox.addButton("Close", QMessageBox.NoRole)
        msgBox.exec()
