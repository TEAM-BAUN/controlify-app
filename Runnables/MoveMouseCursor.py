from PyQt5.QtCore import QRunnable, Qt, QThreadPool

import logging
import pyautogui


logging.basicConfig(format="%(message)s", level=logging.INFO)
# 1. Subclass QRunnable
class MoveMouseCursorRunnable(QRunnable):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y

    def run(self):
        # Your long-running task goes here ...
        logging.info(f"Mouse Position Received! (X:{self.x},Y:{self.y})")
        pyautogui.moveTo(
            self.x, self.y, duration=0, tween=pyautogui.linear(0.0), _pause=False
        )
