from PyQt5.QtCore import QRunnable, QCoreApplication
import logging
import pyautogui

logging.basicConfig(format="%(message)s", level=logging.INFO)

# 1. Subclass QRunnable
class MouseLeftClickRunnable(QRunnable):
    def __init__(self):
        super().__init__()
        self.setAutoDelete(True)

    def run(self):
        # Mouse Sag tik'in gerceklesmesi
        logging.info("Left Click received!")
        pyautogui.leftClick()
        self.autoDelete()
