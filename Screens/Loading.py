from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import os
import logging


class LoadingScreen(QWidget):
    show_main = pyqtSignal()
    now_available = pyqtSignal()
    request_cancaled = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # self.setFixedSize(QSize(200, 200))
        os.path.dirname(__file__)

        self.setupUi()

    def setupUi(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)
        self.movie = QMovie(f"{os.getcwd()}/assets/spinner.gif")

        generalLayout = QVBoxLayout()

        hlbox1 = QHBoxLayout()
        hlbox2 = QHBoxLayout()
        hlbox3 = QHBoxLayout()
        self.connecting_to_label = QLabel(self)
        hlbox1.addWidget(self.connecting_to_label)
        self.label_animation = QLabel(self)
        self.label_animation.setMovie(self.movie)
        hlbox2.addStretch()
        hlbox2.addWidget(self.label_animation)
        hlbox2.addStretch()

        self.cancel_button = QPushButton("İptal et")
        self.cancel_button.setIcon(QIcon(f"{os.getcwd()}/assets/cancel.png"))
        self.cancel_button.clicked.connect(self.stopAnimation)
        hlbox3.addStretch()
        hlbox3.addWidget(self.cancel_button)
        hlbox3.addStretch()

        generalLayout.addLayout(hlbox1)
        generalLayout.addLayout(hlbox2)
        generalLayout.addLayout(hlbox3)
        self.setLayout(generalLayout)

    def startAnimation(self, ID):
        self.id = ID
        self.connecting_to_label.setText(f"{ID} numaralı ID'den cevap bekleniyor")
        self.show()
        self.movie.start()

    def stopAnimation(self):
        # todo Logs kanalina Kullanicinin istekden vazgectigine dair mesaj yollayalim ki karsi taraf'a giden bildirim ekrani kaybolsun
        # todo  yada isteginden vazgecti mesaji alsin
        self.request_cancaled.emit(self.id)
        # Tekrar musait konumuna al
        self.now_available.emit()
        # Ana ekrani goster
        self.show_main.emit()
        # Animasyonu durdur
        self.movie.stop()
        # Loading Screen i kapat
        self.close()