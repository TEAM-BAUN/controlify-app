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
        # Your long-running task goes here ...
        logging.info(f"Mouse Position is sending! (X:{self.x},Y:{self.y})")
        r.publish(
            "mouse_positions",
            f"?to={self.theIdIamControlling}&from={self.id}&posX={self.x}&posY={self.y}",
        )
        # r.publish(
        #     "logs",
        #     pickle.dumps(
        #         {
        #             "to": f"{self.theIdIamControlling}",
        #             "from": f"{self.id}",
        #             "log_type": "mouse_position",
        #             "mouse_position": f"{self.x}:{self.y}",
        #         }
        #     ),
        # )
        self.autoDelete()
