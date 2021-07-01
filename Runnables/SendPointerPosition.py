from PyQt5.QtCore import QRunnable, QCoreApplication

import logging

# import pickle

from Utils.redisconn import redisServerSetup

status, r, p = redisServerSetup()

logging.basicConfig(format="%(message)s", level=logging.INFO)


# 1. Subclass QRunnable
class SendPointerPositionRunnable(QRunnable):
    def __init__(self, id, theIdIamControlling, x, y):
        super().__init__()
        self.id = id
        self.theIdIamControlling = theIdIamControlling
        self.x = x
        self.y = y
        self.setAutoDelete(True)

    def run(self):
        # Mouse Konumunun redis kanalina gonderilmesi
        # "?to=123123123&from=45564564564&posX=123&posY=456" seklinde gonderilir
        r.publish(
            "mouse_positions",
            f"?to={self.theIdIamControlling}&from={self.id}&posX={self.x}&posY={self.y}",
        )
        self.autoDelete()
