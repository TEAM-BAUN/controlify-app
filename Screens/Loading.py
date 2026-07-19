from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QMovie
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from Utils.paths import asset_path


class LoadingScreen(QWidget):
    # Iptal edilen bekleyisin hedef ID'sini tasir
    canceled = Signal(str)

    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.CustomizeWindowHint
        )
        self.movie = QMovie(asset_path("spinner.gif"))

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
        self.cancel_button.setIcon(QIcon(asset_path("cancel.png")))
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
        # Karsi tarafa vazgectigimizi baglantiyi kapatarak bildiririz;
        # durum sifirlama ve ana ekrana donus Main tarafinda yapilir
        self.canceled.emit(self.id)
        self.movie.stop()
        self.close()
