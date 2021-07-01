from PyQt5.QtCore import QRunnable

import logging
import pyautogui


logging.basicConfig(format="%(message)s", level=logging.INFO)
# 1. Subclass QRunnable
class MoveMouseCursorRunnable(QRunnable):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.setAutoDelete(True)

    def run(self):
        logging.info(f"Mouse Position Received! (X:{self.x},Y:{self.y})")
        # Mouse Gelen Konuma hareket ettirilir
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(
            self.x,
            self.y,
            duration=0.0,
            logScreenshot=False,
            _pause=False,
        )
        pyautogui.FAILSAFE = True
        self.autoDelete()
