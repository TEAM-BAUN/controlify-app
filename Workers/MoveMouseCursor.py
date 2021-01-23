from PyQt5.QtCore import QObject, pyqtSignal

import logging
import pyautogui


logging.basicConfig(format="%(message)s", level=logging.INFO)
# 1. Subclass QRunnable
class MoveMouseCursor(QObject):
    finished = pyqtSignal()

    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y

    def run(self):
        # Your long-running task goes here ...
        logging.info(f"Mouse Position Received! (X:{self.x},Y:{self.y})")
        pyautogui.moveTo(self.x, self.y, duration=0.01, tween="linear")
        # pyautogui.moveTo(self.x, self.y, duration=0.25, _pause=True)
        self.finished.emit()
