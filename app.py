import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from Screens.Main import Main
from Screens.theme import THEME_QSS
from Utils.paths import asset_path

logging.basicConfig(format="%(message)s", level=logging.INFO)

if __name__ == "__main__":
    # Sunucu bagimliligi yok: uygulama dogrudan acilir,
    # LAN'daki diger istemciler UDP duyurulariyla listeye duser
    app = QApplication(sys.argv)
    # Koyu tema: tum ekranlar tek global QSS'ten beslenir
    app.setStyleSheet(THEME_QSS)
    app.setWindowIcon(QIcon(asset_path("logo/icon-256.png")))
    # Ekran Cozunurluk degerlerini almak!
    main_window = Main(app.primaryScreen().geometry().width())
    # Ana pencereyi göstermek!
    main_window.show()
    sys.exit(app.exec())
