from PyQt5.QtCore import QObject, pyqtSignal

import logging
import re
from Utils.redisconn import redisServerSetup

logging.basicConfig(format="%(message)s", level=logging.INFO)

status, r, p = redisServerSetup()


pattern = "^\?to=(\d+)&from=(\d+)&posX=(\d+)&posY=(\d+)"


class MousePosListenerWorker(QObject):
    mouse_pointer_pos = pyqtSignal(str, str)

    def __init__(self, id, senderID) -> None:
        super().__init__()
        self.id = id
        self.senderID = senderID
        self.flag = False

    def run(self):
        self.flag = True
        p.subscribe("mouse_positions")
        logging.info("Mouse konumlari dinleniyor...")

        while self.flag:
            log = p.get_message()
            if log:
                mouse_log_details = log["data"].decode("utf-8")
                regex = re.compile(pattern)
                m = regex.match(mouse_log_details)
                id = m.group(1)
                # senderID = m.group(2) Luzumu yok!
                posX = m.group(3)
                posY = m.group(4)
                if self.id == id:
                    self.mouse_pointer_pos.emit(posX, posY)
