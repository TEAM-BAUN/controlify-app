import logging
import random
import pyautogui

from PyQt5.QtCore import QObject,pyqtSignal

logging.basicConfig(format="%(message)s", level=logging.INFO)

# 1. Subclass QRunnable
class MouseRightClick(QObject):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        # Your long-running task goes here ...
        logging.info(f"Right Click received!")
        pyautogui.rightClick()
        self.finished.emit()
