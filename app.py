from PyQt5.QtWidgets import QApplication
import sys
import logging
from Utils.redisconn import redisServerSetup
from Screens.Main import Main

__version__ = "0.1"
__authors__ = ["Ahmet Yusuf Başaran ", "Yusufcan Günay"]

logging.basicConfig(format="%(message)s", level=logging.INFO)

if __name__ == "__main__":
    status, r, p = redisServerSetup()
    if status:
        app = QApplication(sys.argv)
        # Ekran Cozunurluk degerlerini almak!
        screen_resolution = app.desktop().screenGeometry()
        width, height = screen_resolution.width(), screen_resolution.height()
        main_window = Main(width, height)
        main_window.show()
        sys.exit(app.exec())
    else:
        logging.info("Server'a bağlanılamıyor...")