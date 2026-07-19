import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from Screens.Main import Main
from Screens.theme import THEME_QSS
from Utils.paths import asset_path

__version__ = "1.0"
__authors__ = ["Ahmet Yusuf Başaran ", "Yusufcan Günay"]

logging.basicConfig(format="%(message)s", level=logging.INFO)

if __name__ == "__main__":
    # Sunucu bagimliligi yok: uygulama dogrudan acilir,
    # LAN'daki diger istemciler UDP duyurulariyla listeye duser
    app = QApplication(sys.argv)
    # Koyu tema: tum ekranlar tek global QSS'ten beslenir
    app.setStyleSheet(THEME_QSS)
    app.setWindowIcon(QIcon(asset_path("logo/icon-256.png")))
    # Ekran Cozunurluk degerlerini almak!
    geometry = app.primaryScreen().geometry()
    main_window = Main(geometry.width(), geometry.height())
    # Ana pencereyi göstermek!
    main_window.show()
    sys.exit(app.exec())
